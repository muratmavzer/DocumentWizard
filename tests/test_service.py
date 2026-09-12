import pytest

from belgeiz.config import Settings
from belgeiz.models import DocumentResult, SourceChunk
from belgeiz.qa import GroundedQA
from belgeiz.service import BelgeIzService


class StubExtractor:
    def extract_bytes(self, filename, data, progress=None):
        assert data == b"content"
        if progress:
            progress(1, 1, "tamam")
        chunk = SourceChunk("src-1", filename, 1, "Proje kodu ALFA-42")
        return DocumentResult(filename, 1, [chunk], [])


def test_service_adds_document_and_chunks():
    service = BelgeIzService(Settings())
    service.extractor = StubExtractor()

    result = service.add_document("brief.pdf", b"content")

    assert service.documents == [result]
    assert service.chunks[0].id == "src-1"


def test_service_removes_document_and_rebuilds_active_chunks():
    first_chunk = SourceChunk("same-id", "ilk.pdf", 1, "İlk belge")
    second_chunk = SourceChunk("same-id", "ikinci.pdf", 1, "İkinci belge")
    service = BelgeIzService(Settings())
    service.documents = [
        DocumentResult("ilk.pdf", 1, [first_chunk]),
        DocumentResult("ikinci.pdf", 1, [second_chunk]),
    ]
    service.chunks = [first_chunk, second_chunk]

    removed = service.remove_document(0)

    assert removed.document_name == "ilk.pdf"
    assert [document.document_name for document in service.documents] == ["ikinci.pdf"]
    assert service.chunks == [second_chunk]


def test_service_rejects_unknown_document_index():
    service = BelgeIzService(Settings())
    with pytest.raises(IndexError, match="bulunamadı"):
        service.remove_document(0)


def test_service_requires_readable_document_before_qa():
    service = BelgeIzService(Settings())
    with pytest.raises(ValueError, match="Önce"):
        service.create_qa("fake-key")


def test_service_builds_qa_with_configured_model(monkeypatch):
    service = BelgeIzService(Settings(model="default-model"))
    service.chunks = [SourceChunk("src-1", "a.pdf", 1, "Teslim tarihi 1 Ekim")]
    captured = {}

    class FakeResponder:
        def __init__(self, api_key, model):
            captured.update(api_key=api_key, model=model)

        def __call__(self, question, context):
            return {"grounded": False, "answer": "", "citation_ids": []}

    monkeypatch.setattr("belgeiz.service.OpenAIResponder", FakeResponder)
    qa = service.create_qa("fake-key", "override-model")

    assert isinstance(qa, GroundedQA)
    assert captured == {"api_key": "fake-key", "model": "override-model"}


def test_service_builds_local_ollama_qa(monkeypatch):
    service = BelgeIzService(Settings(ollama_model="qwen3:1.7b"))
    service.chunks = [SourceChunk("src-1", "a.pdf", 1, "Proje kodu ALFA-42")]
    captured = {}

    class FakeOllama:
        def __init__(self, model, base_url):
            captured.update(model=model, base_url=base_url)

    monkeypatch.setattr("belgeiz.service.OllamaResponder", FakeOllama)
    qa = service.create_qa(
        provider="ollama",
        model="qwen3:4b-instruct",
        ollama_url="http://localhost:11434",
    )

    assert isinstance(qa, GroundedQA)
    assert captured == {
        "model": "qwen3:4b-instruct",
        "base_url": "http://localhost:11434",
    }
