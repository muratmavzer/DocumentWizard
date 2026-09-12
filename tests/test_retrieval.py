from belgeiz.models import SourceChunk
from belgeiz.retrieval import HybridRetriever, normalize, tokenize


CHUNKS = [
    SourceChunk("tr-1", "sozlesme.pdf", 1, "Sözleşmenin toplam bedeli 125.000 Türk lirasıdır."),
    SourceChunk("en-1", "report.pdf", 4, "The renewable energy project started in March 2025."),
    SourceChunk("tr-2", "rapor.pdf", 2, "İstanbul ofisinde toplam 48 çalışan bulunmaktadır."),
]


def test_turkish_case_normalization():
    assert normalize("İSTANBUL IŞIK") == "istanbul ışık"
    assert "istanbul" in tokenize("İstanbul'daki")


def test_retriever_finds_turkish_amount():
    hits = HybridRetriever(CHUNKS).search("Sözleşme bedeli ne kadar?", top_k=2)
    assert hits[0].chunk.id == "tr-1"
    assert hits[0].score >= 0.18


def test_retriever_finds_english_date():
    hits = HybridRetriever(CHUNKS).search("When did the energy project start?")
    assert hits[0].chunk.id == "en-1"
    assert hits[0].score >= 0.18


def test_out_of_document_query_stays_below_gate():
    hits = HybridRetriever(CHUNKS).search("Şirketin CEO'sunun doğum tarihi nedir?")
    assert hits[0].score < 0.18

