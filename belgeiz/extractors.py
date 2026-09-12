from __future__ import annotations

import io
import os
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from PIL import Image, ImageOps

from .chunking import chunk_page
from .config import Settings
from .models import DocumentResult


SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ProgressCallback = Callable[[int, int, str], None]


@lru_cache(maxsize=2)
def _load_easyocr_reader(model_dir: str):
    """Ağır OCR modelini süreç boyunca tek kez yükler."""

    try:
        import easyocr
        import torch
    except ImportError as exc:  # pragma: no cover - kurulum hatası yolu
        raise RuntimeError(
            "EasyOCR kurulu değil. setup.ps1 veya setup.sh çalıştırın."
        ) from exc
    # Tüm çekirdekleri kullanmak masaüstünü kilitleyebiliyor; dengeli bir üst sınır.
    torch.set_num_threads(max(1, min(4, (os.cpu_count() or 2) // 2)))
    return easyocr.Reader(
        ["tr", "en"],
        gpu=False,
        verbose=False,
        model_storage_directory=model_dir,
        user_network_directory=str(Path(model_dir) / "user_network"),
    )


class OCREngine(Protocol):
    def extract(self, image: Image.Image) -> tuple[str, float]: ...


class EasyOCREngine:
    """Ağır modeli yalnızca ilk OCR isteğinde yükler."""

    def __init__(self, max_image_side: int = 1_400) -> None:
        self._reader = None
        self.max_image_side = max_image_side

    def _get_reader(self):
        if self._reader is None:
            model_dir = Path(
                os.getenv("BELGEIZ_OCR_MODEL_DIR", str(Path.cwd() / ".easyocr"))
            ).resolve()
            model_dir.mkdir(parents=True, exist_ok=True)
            try:
                self._reader = _load_easyocr_reader(str(model_dir))
            except Exception as exc:
                raise RuntimeError(
                    "OCR modeli hazırlanamadı. İlk kullanımda internet bağlantısı gerekir; "
                    "model daha sonra .easyocr dizininden çevrimdışı kullanılır."
                ) from exc
        return self._reader

    def extract(self, image: Image.Image) -> tuple[str, float]:
        import numpy as np

        prepared = ImageOps.exif_transpose(image).convert("L")
        prepared = ImageOps.autocontrast(prepared)
        max_side = self.max_image_side
        if max(prepared.size) > max_side:
            prepared.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        results = self._get_reader().readtext(
            np.asarray(prepared),
            decoder="greedy",
            beamWidth=1,
            detail=1,
            paragraph=False,
            canvas_size=max_side,
            mag_ratio=1.0,
        )
        if not results:
            return "", 0.0
        # EasyOCR çoğunlukla okuma sırasını korur; koordinatlarla bunu sabitliyoruz.
        ordered = sorted(results, key=lambda item: (item[0][0][1], item[0][0][0]))
        text = "\n".join(str(item[1]).strip() for item in ordered if str(item[1]).strip())
        confidence = sum(float(item[2]) for item in ordered) / len(ordered)
        return text, confidence


class DocumentExtractor:
    def __init__(
        self,
        settings: Settings | None = None,
        ocr_engine: OCREngine | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.ocr_engine = ocr_engine or EasyOCREngine(self.settings.ocr_max_image_side)

    def extract_bytes(
        self,
        filename: str,
        data: bytes,
        progress: ProgressCallback | None = None,
    ) -> DocumentResult:
        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError("Yalnızca PDF, JPG, JPEG ve PNG dosyaları desteklenir.")
        if not data:
            raise ValueError("Dosya boş.")
        if len(data) > self.settings.max_file_mb * 1024 * 1024:
            raise ValueError(
                f"Dosya {self.settings.max_file_mb} MB sınırını aşıyor."
            )
        if extension == ".pdf":
            return self._extract_pdf(filename, data, progress)
        return self._extract_image(filename, data, progress)

    def _extract_image(
        self, filename: str, data: bytes, progress: ProgressCallback | None = None
    ) -> DocumentResult:
        try:
            with Image.open(io.BytesIO(data)) as opened:
                if opened.width * opened.height > 40_000_000:
                    raise ValueError("Görüntü 40 megapiksel güvenlik sınırını aşıyor.")
                image = opened.copy()
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Görüntü dosyası açılamadı veya bozuk.") from exc
        if progress:
            progress(0, 1, "OCR modeli hazırlanıyor")
        text, confidence = self.ocr_engine.extract(image)
        if progress:
            progress(1, 1, "Görüntü okundu")
        warnings: list[str] = []
        if not text.strip():
            warnings.append("Görüntüde okunabilir metin bulunamadı.")
        elif confidence < 0.45:
            warnings.append(
                f"OCR güveni düşük ({confidence:.0%}); kaynak görüntüyü kontrol edin."
            )
        return DocumentResult(
            document_name=filename,
            page_count=1,
            chunks=chunk_page(
                text,
                filename,
                page=1,
                extraction_method=f"ocr:{confidence:.2f}",
                max_words=self.settings.max_chunk_words,
                overlap_words=self.settings.chunk_overlap_words,
            ),
            warnings=warnings,
        )

    def _extract_pdf(
        self, filename: str, data: bytes, progress: ProgressCallback | None = None
    ) -> DocumentResult:
        try:
            import pymupdf
        except ImportError as exc:  # pragma: no cover - kurulum hatası yolu
            raise RuntimeError("PyMuPDF kurulu değil; kurulum betiğini çalıştırın.") from exc

        try:
            document = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise ValueError("PDF açılamadı; dosya bozuk veya şifreli olabilir.") from exc

        if document.needs_pass:
            document.close()
            raise ValueError("Şifreli PDF dosyaları MVP kapsamında desteklenmiyor.")
        if document.page_count > self.settings.max_pdf_pages:
            document.close()
            raise ValueError(
                f"PDF {self.settings.max_pdf_pages} sayfa sınırını aşıyor."
            )

        page_count = document.page_count
        chunks = []
        warnings: list[str] = []
        try:
            for page_index, page in enumerate(document, start=1):
                text = page.get_text("text", sort=True).strip()
                method = "pdf-text"
                if self._needs_ocr(text):
                    if self.settings.ocr_enabled:
                        if progress:
                            progress(
                                page_index - 1,
                                page_count,
                                f"Sayfa {page_index}: OCR yapılıyor",
                            )
                        scale = self.settings.ocr_render_scale
                        pixmap = page.get_pixmap(
                            matrix=pymupdf.Matrix(scale, scale), alpha=False
                        )
                        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                        text, confidence = self.ocr_engine.extract(image)
                        method = f"pdf-ocr:{confidence:.2f}"
                    else:
                        confidence = 0.0
                        warnings.append(
                            f"Sayfa {page_index}: taranmış görünüyor; OCR kapalı olduğu için atlandı."
                        )
                    if self.settings.ocr_enabled and confidence < 0.45:
                        warnings.append(
                            f"Sayfa {page_index}: OCR güveni düşük ({confidence:.0%})."
                        )
                if not text.strip():
                    warnings.append(f"Sayfa {page_index}: okunabilir metin bulunamadı.")
                    if progress:
                        progress(
                            page_index,
                            page_count,
                            f"Sayfa {page_index}/{page_count} tamamlandı",
                        )
                    continue
                chunks.extend(
                    chunk_page(
                        text,
                        filename,
                        page_index,
                        method,
                        self.settings.max_chunk_words,
                        self.settings.chunk_overlap_words,
                    )
                )
                if progress:
                    progress(
                        page_index,
                        page_count,
                        f"Sayfa {page_index}/{page_count} tamamlandı",
                    )
        finally:
            document.close()
        return DocumentResult(filename, page_count, chunks, warnings)

    def _needs_ocr(self, text: str) -> bool:
        stripped = "".join(text.split())
        if len(stripped) < self.settings.ocr_min_text_chars:
            return True
        alphanumeric = sum(character.isalnum() for character in stripped)
        return alphanumeric / max(1, len(stripped)) < 0.45
