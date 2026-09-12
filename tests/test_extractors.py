import io

import pytest
from PIL import Image

from belgeiz.config import Settings
from belgeiz.extractors import DocumentExtractor


class StubOCR:
    def __init__(self, text="Toplam tutar 1.275,50 TL'dir.", confidence=0.92):
        self.text = text
        self.confidence = confidence
        self.calls = 0

    def extract(self, image):
        self.calls += 1
        assert image.width > 0
        return self.text, self.confidence


def _png_bytes():
    image = Image.new("RGB", (320, 160), "white")
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def test_image_routes_through_bilingual_ocr_contract():
    ocr = StubOCR("İstanbul office has 48 çalışan.")
    result = DocumentExtractor(Settings(), ocr).extract_bytes("scan.png", _png_bytes())

    assert ocr.calls == 1
    assert result.page_count == 1
    assert result.chunks[0].text == "İstanbul office has 48 çalışan."
    assert result.chunks[0].extraction_method == "ocr:0.92"


def test_low_ocr_confidence_is_reported():
    result = DocumentExtractor(Settings(), StubOCR(confidence=0.30)).extract_bytes(
        "scan.jpg", _png_bytes()
    )
    assert "OCR güveni düşük" in result.warnings[0]


def test_unsupported_and_oversized_files_are_rejected():
    extractor = DocumentExtractor(Settings(max_file_mb=1), StubOCR())
    with pytest.raises(ValueError, match="Yalnızca"):
        extractor.extract_bytes("notes.txt", b"hello")
    with pytest.raises(ValueError, match="sınırını"):
        extractor.extract_bytes("huge.png", b"x" * (1024 * 1024 + 1))


def test_text_pdf_extracts_page_and_table_like_rows():
    pymupdf = pytest.importorskip("pymupdf")
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text(
        (72, 72),
        "Quarterly Report\nProduct   Units   Revenue\nAtlas     24      120000 USD\nProject owner: Deniz Kaya",
    )
    data = pdf.tobytes()
    pdf.close()

    ocr = StubOCR()
    result = DocumentExtractor(Settings(), ocr).extract_bytes("table.pdf", data)
    assert result.page_count == 1
    assert "120000 USD" in result.chunks[0].text
    assert result.chunks[0].page == 1
    assert ocr.calls == 0


def test_scanned_pdf_page_falls_back_to_ocr():
    pymupdf = pytest.importorskip("pymupdf")
    pdf = pymupdf.open()
    pdf.new_page()
    data = pdf.tobytes()
    pdf.close()

    ocr = StubOCR("Tarama içindeki teslim tarihi 18 Ekim 2026'dır.")
    result = DocumentExtractor(Settings(), ocr).extract_bytes("scanned.pdf", data)

    assert ocr.calls == 1
    assert result.chunks[0].page == 1
    assert result.chunks[0].extraction_method == "pdf-ocr:0.92"
    assert "18 Ekim 2026" in result.chunks[0].text


def test_short_but_meaningful_pdf_text_does_not_trigger_ocr():
    extractor = DocumentExtractor(Settings(ocr_min_text_chars=8), StubOCR())
    assert extractor._needs_ocr("Toplam: 42 TL") is False
    assert extractor._needs_ocr("  1  ") is True


def test_pdf_reports_page_level_progress():
    pymupdf = pytest.importorskip("pymupdf")
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text(
        (72, 72), "Bu sayfa OCR gerektirmeden hizli okunacak metin icerir."
    )
    data = pdf.tobytes()
    pdf.close()
    events = []

    DocumentExtractor(Settings(), StubOCR()).extract_bytes(
        "progress.pdf", data, progress=lambda *args: events.append(args)
    )

    assert events[-1] == (1, 1, "Sayfa 1/1 tamamlandı")
