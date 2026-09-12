from __future__ import annotations

import os
from dataclasses import dataclass


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "hayir", "hayır", "no", "off"}


@dataclass(frozen=True, slots=True)
class Settings:
    model: str = "gpt-5.4-mini"
    ollama_model: str = "qwen3:4b-instruct"
    ollama_url: str = "http://127.0.0.1:11434"
    retrieval_threshold: float = 0.18
    max_file_mb: int = 20
    max_pdf_pages: int = 100
    max_context_chars: int = 16_000
    max_chunk_words: int = 180
    chunk_overlap_words: int = 30
    top_k: int = 8
    ocr_enabled: bool = True
    ocr_render_scale: float = 1.20
    ocr_max_image_side: int = 1_400
    ocr_min_text_chars: int = 8

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            model=os.getenv("BELGEIZ_MODEL", defaults.model),
            ollama_model=os.getenv("BELGEIZ_OLLAMA_MODEL", defaults.ollama_model),
            ollama_url=os.getenv("BELGEIZ_OLLAMA_URL", defaults.ollama_url),
            retrieval_threshold=_env_float(
                "BELGEIZ_RETRIEVAL_THRESHOLD", defaults.retrieval_threshold
            ),
            max_file_mb=_env_int("BELGEIZ_MAX_FILE_MB", defaults.max_file_mb),
            max_pdf_pages=_env_int("BELGEIZ_MAX_PDF_PAGES", defaults.max_pdf_pages),
            max_context_chars=_env_int(
                "BELGEIZ_MAX_CONTEXT_CHARS", defaults.max_context_chars
            ),
            ocr_enabled=_env_bool("BELGEIZ_OCR_ENABLED", defaults.ocr_enabled),
            ocr_render_scale=_env_float(
                "BELGEIZ_OCR_RENDER_SCALE", defaults.ocr_render_scale
            ),
            ocr_max_image_side=_env_int(
                "BELGEIZ_OCR_MAX_IMAGE_SIDE", defaults.ocr_max_image_side
            ),
            ocr_min_text_chars=_env_int(
                "BELGEIZ_OCR_MIN_TEXT_CHARS", defaults.ocr_min_text_chars
            ),
        )
