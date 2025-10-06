"""Knowledge retrieval orchestrator."""
from __future__ import annotations

from typing import Iterable, List

from sqlalchemy.orm import Session

from ..adapters.llm_base import ChatMessage
from ..models import KnowledgeChunk
from .vectorstore import VectorStore


class Retriever:
    """Retrieve relevant chunks using the vector store."""

    def __init__(self, db: Session, vector_store: VectorStore) -> None:
        self.db = db
        self.vector_store = vector_store

    def retrieve(self, query: str, k: int = 5) -> List[dict]:
        if not query:
            return []
        embedding = self._embed_query(query)
        chunk_ids = self.vector_store.similarity_search(embedding, k=k)
        if not chunk_ids:
            return []
        chunks = self.db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(chunk_ids)).all()
        return [
            {"id": chunk.id, "text": chunk.chunk_text, "document_id": chunk.document_id}
            for chunk in chunks
        ]

    def _embed_query(self, text: str) -> List[float]:
        tokens = text.split()
        if not tokens:
            return [0.0]
        avg = sum(len(token) for token in tokens) / len(tokens)
        return [avg, float(len(tokens))]
