"""Simple vector store implementation using cosine similarity."""
from __future__ import annotations

from math import sqrt
from typing import Iterable, List


class VectorStore:
    """Stores embeddings in memory for the MVP."""

    def __init__(self) -> None:
        self._vectors: dict[int, List[float]] = {}

    def upsert(self, chunk_id: int, embedding: List[float]) -> None:
        self._vectors[chunk_id] = embedding

    def delete(self, chunk_id: int) -> None:
        self._vectors.pop(chunk_id, None)

    def similarity_search(self, query_vector: List[float], k: int = 5) -> List[int]:
        scores: list[tuple[int, float]] = []
        for chunk_id, vector in self._vectors.items():
            score = self._cosine(query_vector, vector)
            scores.append((chunk_id, score))
        scores.sort(key=lambda item: item[1], reverse=True)
        return [chunk_id for chunk_id, _ in scores[:k]]

    @staticmethod
    def _cosine(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sqrt(sum(a * a for a in vec_a))
        norm_b = sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
