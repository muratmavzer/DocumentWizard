from __future__ import annotations

import math
import re
from collections import Counter
from difflib import SequenceMatcher

from .models import SearchHit, SourceChunk


_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "document", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "page", "the", "this", "to", "what",
    "when", "where", "which", "who", "why", "with", "about",
    "acaba", "adı", "ait", "belge", "belgede", "belgelerde", "bu", "da", "de", "diye",
    "hangi", "hakkında", "ile", "için", "ise", "kaç", "ki", "kim", "mı", "mi", "mu",
    "mü", "nasıl", "ne", "neden", "nerede", "olan", "olarak", "sayfa", "şu", "ve", "veya",
}


def normalize(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").casefold()


def tokenize(text: str, *, remove_stopwords: bool = False) -> list[str]:
    tokens = _TOKEN_RE.findall(normalize(text))
    if remove_stopwords:
        return [token for token in tokens if token not in _STOPWORDS and len(token) > 1]
    return tokens


class HybridRetriever:
    """Dil bağımsız BM25 + kapsama + yazım/çekim toleranslı eşleme."""

    def __init__(self, chunks: list[SourceChunk]) -> None:
        if not chunks:
            raise ValueError("Arama dizini için en az bir metin parçası gerekir.")
        self.chunks = chunks
        self.documents = [tokenize(chunk.text) for chunk in chunks]
        self.counters = [Counter(tokens) for tokens in self.documents]
        self.avg_length = sum(map(len, self.documents)) / len(self.documents)
        self.document_frequency: Counter[str] = Counter()
        for tokens in self.documents:
            self.document_frequency.update(set(tokens))

    def search(self, query: str, top_k: int = 5) -> list[SearchHit]:
        query_tokens = tokenize(query, remove_stopwords=True)
        if not query_tokens:
            query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scored: list[SearchHit] = []
        for chunk, tokens, counts in zip(self.chunks, self.documents, self.counters):
            bm25 = self._bm25(query_tokens, tokens, counts)
            coverage = sum(1 for token in set(query_tokens) if token in counts) / len(
                set(query_tokens)
            )
            fuzzy = self._fuzzy_coverage(query_tokens, set(tokens))
            scaled_bm25 = bm25 / (bm25 + 3.0) if bm25 > 0 else 0.0
            score = min(1.0, 0.40 * scaled_bm25 + 0.40 * coverage + 0.20 * fuzzy)
            scored.append(SearchHit(chunk, round(score, 4)))
        return sorted(scored, key=lambda hit: hit.score, reverse=True)[:top_k]

    def _bm25(
        self, query: list[str], document: list[str], counts: Counter[str]
    ) -> float:
        score = 0.0
        total_docs = len(self.documents)
        k1, b = 1.5, 0.75
        length_factor = 1 - b + b * len(document) / max(1.0, self.avg_length)
        for token in query:
            frequency = counts[token]
            if not frequency:
                continue
            df = self.document_frequency[token]
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            score += idf * frequency * (k1 + 1) / (frequency + k1 * length_factor)
        return score

    @staticmethod
    def _fuzzy_coverage(query: list[str], document_tokens: set[str]) -> float:
        if not document_tokens:
            return 0.0
        matches = 0.0
        # En fazla 1200 eşleşme: kötü niyetli/aşırı uzun OCR çıktısında maliyeti sınırlar.
        candidates = list(document_tokens)[:1200]
        for query_token in set(query):
            best = 0.0
            for token in candidates:
                if min(len(query_token), len(token)) < 4:
                    continue
                if query_token.startswith(token[:4]) or token.startswith(query_token[:4]):
                    best = max(best, SequenceMatcher(None, query_token, token).ratio())
            matches += best if best >= 0.72 else 0.0
        return matches / len(set(query))

