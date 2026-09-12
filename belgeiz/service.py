from __future__ import annotations

from .config import Settings
from .extractors import DocumentExtractor, ProgressCallback
from .models import DocumentResult, SourceChunk
from .qa import GroundedQA, OllamaResponder, OpenAIResponder
from .retrieval import HybridRetriever


class BelgeIzService:
    """Arayüzden bağımsız uygulama servisi; test ve başka istemcilere açıktır."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.extractor = DocumentExtractor(self.settings)
        self.documents: list[DocumentResult] = []
        self.chunks: list[SourceChunk] = []

    def add_document(
        self,
        filename: str,
        data: bytes,
        progress: ProgressCallback | None = None,
    ) -> DocumentResult:
        result = self.extractor.extract_bytes(filename, data, progress)
        self.documents.append(result)
        self.chunks.extend(result.chunks)
        return result

    def remove_document(self, index: int) -> DocumentResult:
        if index < 0 or index >= len(self.documents):
            raise IndexError("Belge bulunamadı.")
        removed = self.documents.pop(index)
        self.chunks = [
            chunk for document in self.documents for chunk in document.chunks
        ]
        return removed

    def create_qa(
        self,
        api_key: str = "",
        model: str | None = None,
        provider: str = "openai",
        ollama_url: str | None = None,
    ) -> GroundedQA:
        if not self.chunks:
            raise ValueError("Önce en az bir okunabilir belge yükleyin.")
        if provider == "ollama":
            responder = OllamaResponder(
                model or self.settings.ollama_model,
                ollama_url or self.settings.ollama_url,
            )
        elif provider == "openai":
            responder = OpenAIResponder(api_key, model or self.settings.model)
        else:
            raise ValueError("Bilinmeyen model sağlayıcısı.")
        return GroundedQA(HybridRetriever(self.chunks), responder, self.settings)
