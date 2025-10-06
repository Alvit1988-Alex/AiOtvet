"""Document ingestion utilities for the RAG pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..adapters.llm_base import LlmAdapter
from ..models import KnowledgeChunk, KnowledgeDocument
from .vectorstore import VectorStore


@dataclass
class IngestResult:
    document: KnowledgeDocument
    chunks: List[KnowledgeChunk]


class DocumentIngestor:
    """Handle upload, chunking and embedding."""

    def __init__(self, db: Session, vector_store: VectorStore, adapter: LlmAdapter) -> None:
        self.db = db
        self.vector_store = vector_store
        self.adapter = adapter

    def ingest(self, file: UploadFile, tags: str | None, operator_id: int | None) -> IngestResult:
        content = file.file.read().decode("utf-8")
        document = KnowledgeDocument(
            title=file.filename,
            tags=tags,
            source_type=Path(file.filename).suffix.lstrip("."),
            updated_by=operator_id,
        )
        self.db.add(document)
        self.db.flush()

        chunks = self._chunk_text(content)
        embeddings = self.adapter.embed(chunks, model="text-embedding-3-small")
        chunk_models: list[KnowledgeChunk] = []
        for idx, text in enumerate(chunks):
            chunk = KnowledgeChunk(document_id=document.id, chunk_text=text, embedding=embeddings[idx], meta={})
            self.db.add(chunk)
            self.db.flush()
            self.vector_store.upsert(chunk.id, embeddings[idx])
            chunk_models.append(chunk)
        return IngestResult(document=document, chunks=chunk_models)

    def _chunk_text(self, text: str, max_len: int = 500) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks: list[str] = []
        current: list[str] = []
        for word in words:
            current.append(word)
            if sum(len(w) + 1 for w in current) > max_len:
                chunks.append(" ".join(current))
                current = []
        if current:
            chunks.append(" ".join(current))
        return chunks
