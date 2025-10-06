"""Knowledge base routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_operator, require_role
from ..models import KnowledgeChunk, KnowledgeDocument, OperatorRole
from ..rag import get_ingestor, get_retriever, get_vector_store
from ..schemas import KnowledgeChunkSchema, KnowledgeDocumentSchema, SearchResult

router = APIRouter(prefix="/api/kb", tags=["knowledge_base"])


@router.post("/upload", response_model=KnowledgeDocumentSchema)
def upload_document(
    tags: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    operator=Depends(require_role(OperatorRole.OPERATOR)),
):
    ingestor = get_ingestor(db)
    result = ingestor.ingest(file, tags=tags, operator_id=operator.id)
    return KnowledgeDocumentSchema.from_orm(result.document)


@router.get("/search", response_model=List[SearchResult])
def search_documents(
    q: str,
    k: int = 5,
    db: Session = Depends(get_db),
):
    retriever = get_retriever(db)
    results = retriever.retrieve(q, k=k)
    search_results: list[SearchResult] = []
    for item in results:
        chunk = db.get(KnowledgeChunk, item["id"])
        if not chunk:
            continue
        document = db.get(KnowledgeDocument, chunk.document_id)
        if not document:
            continue
        search_results.append(
            SearchResult(
                document=KnowledgeDocumentSchema.from_orm(document),
                chunk=KnowledgeChunkSchema.from_orm(chunk),
                score=1.0,
            )
        )
    return search_results


@router.post("/reindex/{document_id}")
def reindex_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_role(OperatorRole.LEAD)),
):
    document = db.get(KnowledgeDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    vector_store = get_vector_store()
    for chunk in document.chunks:
        if chunk.embedding:
            vector_store.upsert(chunk.id, chunk.embedding)
    return {"status": "ok"}
