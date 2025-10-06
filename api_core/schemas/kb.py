"""Schemas for knowledge base endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


class KnowledgeChunkSchema(BaseModel):
    id: int
    document_id: int
    chunk_text: str
    meta: dict | None

    class Config:
        orm_mode = True


class KnowledgeDocumentSchema(BaseModel):
    id: int
    title: str
    tags: str | None
    source_type: str
    updated_at: datetime

    class Config:
        orm_mode = True


class SearchResult(BaseModel):
    document: KnowledgeDocumentSchema
    chunk: KnowledgeChunkSchema
    score: float
