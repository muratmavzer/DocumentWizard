from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SourceChunk:
    """Arama ve atıf için kullanılabilen, sayfa kökeni korunmuş metin parçası."""

    id: str
    document_name: str
    page: int
    text: str
    extraction_method: str = "text"

    @property
    def label(self) -> str:
        return f"{self.document_name} · sayfa {self.page}"


@dataclass(slots=True)
class DocumentResult:
    document_name: str
    page_count: int
    chunks: list[SourceChunk] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SearchHit:
    chunk: SourceChunk
    score: float


@dataclass(frozen=True, slots=True)
class Citation:
    chunk_id: str
    document_name: str
    page: int
    text: str

    @classmethod
    def from_chunk(cls, chunk: SourceChunk) -> "Citation":
        return cls(chunk.id, chunk.document_name, chunk.page, chunk.text)


@dataclass(slots=True)
class Answer:
    text: str
    grounded: bool
    citations: list[Citation] = field(default_factory=list)
    retrieval_score: float = 0.0
    reason: str | None = None
    evidence_mode: str = "retrieval"
