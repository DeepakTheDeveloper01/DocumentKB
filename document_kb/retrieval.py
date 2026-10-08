from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from .document_loader import DocumentChunk

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+")
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "or", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "to", "of", "in",
    "on", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "up", "down",
    "out", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just", "as",
    "also", "not", "this", "that", "these", "those", "it", "its", "from",
    "they", "them", "their", "we", "our", "you", "your", "i", "me", "my",
    "he", "him", "his", "she", "her", "what", "which", "who", "whom",
    "see", "section", "using", "use", "used", "step", "run", "running",
    "available", "include", "includes", "including", "support", "supports", "based",
    "new", "one", "two", "three", "first", "second", "third",
}


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOPWORDS and len(t) > 1]


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    matched_terms: List[str]


class RetrievalEngine:
    def __init__(self, chunks: List[DocumentChunk]):
        self.chunks = chunks
        self._chunks_tf: List[Counter] = []
        self._chunks_len: List[int] = []
        self._doc_freq: Counter = Counter()
        self._section_index: Dict[str, List[int]] = defaultdict(list)
        self._keyword_index: Dict[str, List[int]] = defaultdict(list)
        self._build_indexes()

    def _build_indexes(self) -> None:
        N = len(self.chunks)
        for idx, chunk in enumerate(self.chunks):
            tokens = _tokenize(chunk.text + " " + chunk.section_title + " " + chunk.doc_title)
            tf = Counter(tokens)
            self._chunks_tf.append(tf)
            self._chunks_len.append(len(tokens))
            for token in tf:
                self._doc_freq[token] += 1
            if chunk.section_number:
                self._section_index[chunk.section_number].append(idx)
            for kw in chunk.keywords:
                self._keyword_index[kw.lower()].append(idx)
        self._avg_len = sum(self._chunks_len) / max(1, N)
        self._N = N

    def _bm25_score(self, query_tokens: List[str], chunk_idx: int, k1: float = 1.5, b: float = 0.75) -> tuple[float, List[str]]:
        score = 0.0
        matched: List[str] = []
        tf = self._chunks_tf[chunk_idx]
        dlen = self._chunks_len[chunk_idx]
        seen = set()
        for qt in query_tokens:
            if qt not in tf:
                continue
            if qt not in seen:
                seen.add(qt)
                matched.append(qt)
            f = tf[qt]
            df = self._doc_freq[qt]
            idf = math.log(1 + (self._N - df + 0.5) / (df + 0.5))
            denom = f + k1 * (1 - b + b * dlen / self._avg_len)
            score += idf * (f * (k1 + 1) / denom)
        return score, matched

    def _keyword_boost(self, query_text: str, chunk_idx: int) -> float:
        q_tokens = set(_tokenize(query_text))
        boost = 0.0
        chunk = self.chunks[chunk_idx]
        for kw in chunk.keywords:
            if kw.lower() in q_tokens:
                boost += 0.6
        q_words = set(q_tokens)
        s_tokens = set(_tokenize(chunk.section_title))
        d_tokens = set(_tokenize(chunk.doc_title))
        inter_s = len(q_words & s_tokens)
        if inter_s:
            boost += 0.4 * inter_s
        inter_d = len(q_words & d_tokens)
        if inter_d:
            boost += 0.3 * inter_d
        return boost

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        context_hints: Optional[List[str]] = None,
        avoid_sections: Optional[List[str]] = None,
    ) -> List[RetrievalResult]:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        boost_idxs: set = set()
        for kw in _tokenize(query):
            if kw in self._keyword_index:
                boost_idxs.update(self._keyword_index[kw])
        if context_hints:
            for hint in context_hints:
                h_tokens = _tokenize(hint)
                q_tokens.extend(h_tokens)
                for tok in h_tokens:
                    if tok in self._keyword_index:
                        boost_idxs.update(self._keyword_index[tok])

        candidates = set(range(len(self.chunks))) | boost_idxs

        if avoid_sections:
            removed = set()
            for bad in avoid_sections:
                for idx in list(self._section_index.get(bad, [])):
                    removed.add(idx)
            candidates -= removed

        scored: List[tuple[float, int, List[str]]] = []
        for idx in candidates:
            score, matched = self._bm25_score(q_tokens, idx)
            score += self._keyword_boost(query, idx)
            if idx in boost_idxs:
                score += 0.25
            if score <= 0.0 and not matched:
                continue
            scored.append((score, idx, matched))

        scored.sort(key=lambda x: x[0], reverse=True)

        dedupe: set = set()
        results: List[RetrievalResult] = []
        for score, idx, matched in scored:
            chunk = self.chunks[idx]
            key = (chunk.doc_path, chunk.section_number)
            if key in dedupe and len(results) >= top_k:
                continue
            dedupe.add(key)
            results.append(RetrievalResult(chunk=chunk, score=score, matched_terms=matched))
            if len(results) >= top_k + 2:
                break

        return results[:top_k]
