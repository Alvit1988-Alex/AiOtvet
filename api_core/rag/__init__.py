"""Helpers to wire RAG components."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..adapters import build_default_registry
from ..adapters.llm_base import LlmAdapter
from .ingest import DocumentIngestor
from .retriever import Retriever
from .vectorstore import VectorStore


_vector_store = VectorStore()
_adapters = build_default_registry()


def get_vector_store() -> VectorStore:
    return _vector_store


def get_ingestor(db: Session) -> DocumentIngestor:
    adapter = _adapters.get("openai")
    return DocumentIngestor(db, _vector_store, adapter)


def get_retriever(db: Session) -> Retriever:
    return Retriever(db, _vector_store)
