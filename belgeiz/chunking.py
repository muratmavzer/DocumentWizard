from __future__ import annotations

import hashlib
import re

from .models import SourceChunk


_SPACE_RE = re.compile(r"[ \t\f\v]+")
_BLANK_RE = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """OCR/PDF çıktısını normalize ederken satır ve tablo yapısını korur."""

    lines = [_SPACE_RE.sub(" ", line).strip() for line in text.replace("\r", "\n").split("\n")]
    return _BLANK_RE.sub("\n\n", "\n".join(lines)).strip()


def _windows(words: list[str], size: int, overlap: int) -> list[str]:
    if not words:
        return []
    step = max(1, size - overlap)
    result: list[str] = []
    for start in range(0, len(words), step):
        window = words[start : start + size]
        if not window:
            break
        result.append(" ".join(window))
        if start + size >= len(words):
            break
    return result


def chunk_page(
    text: str,
    document_name: str,
    page: int,
    extraction_method: str,
    max_words: int = 180,
    overlap_words: int = 30,
) -> list[SourceChunk]:
    """Bir sayfayı, sayfa sınırlarını aşmadan örtüşen parçalara böler."""

    normalized = clean_text(text)
    if not normalized:
        return []

    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    assembled: list[str] = []
    buffer: list[str] = []
    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) > max_words:
            if buffer:
                assembled.append("\n\n".join(buffer))
                buffer = []
            assembled.extend(_windows(words, max_words, overlap_words))
            continue
        if sum(len(p.split()) for p in buffer) + len(words) > max_words and buffer:
            assembled.append("\n\n".join(buffer))
            previous_words = assembled[-1].split()[-overlap_words:]
            buffer = [" ".join(previous_words)] if previous_words else []
        buffer.append(paragraph)
    if buffer:
        assembled.append("\n\n".join(buffer))

    chunks: list[SourceChunk] = []
    for index, body in enumerate(assembled, start=1):
        digest = hashlib.sha1(
            f"{document_name}|{page}|{index}|{body}".encode("utf-8")
        ).hexdigest()[:10]
        chunks.append(
            SourceChunk(
                id=f"src-{digest}",
                document_name=document_name,
                page=page,
                text=body,
                extraction_method=extraction_method,
            )
        )
    return chunks

