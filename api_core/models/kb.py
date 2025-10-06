"""Knowledge base models used by the RAG subsystem."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class KnowledgeDocument(Base):
    """Uploaded knowledge base document."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    tags: Mapped[str | None] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(32))
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("operator.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    """Chunked passage from a document."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_document.id"))
    chunk_text: Mapped[str] = mapped_column(String)
    embedding: Mapped[list[float] | None] = mapped_column(JSON)
    meta: Mapped[dict | None] = mapped_column(JSON)

    document: Mapped[KnowledgeDocument] = relationship("KnowledgeDocument", back_populates="chunks")
