from __future__ import annotations

from io import BytesIO

from sqlalchemy.orm import Session

from api_core.adapters import build_default_registry
from api_core.adapters.llm_base import ChatMessage
from api_core.config import get_settings
from api_core.models import (
    Dialog,
    DialogStatus,
    KnowledgeChunk,
    KnowledgeDocument,
    Message,
    MessageSender,
    Operator,
    OperatorRole,
    User,
)
from api_core.rag.ingest import DocumentIngestor
from api_core.rag.retriever import Retriever
from api_core.rag.vectorstore import VectorStore
from api_core.services import auth as auth_service
from api_core.services.confidence import ConfidenceEvaluator
from api_core.services.dialog_service import DialogService
from api_core.services.llm_router import LlmRouter
from api_core.state import get_notifier


def create_operator(db: Session, email: str, role: OperatorRole = OperatorRole.ADMIN) -> Operator:
    operator = Operator(
        email=email,
        role=role,
        password_hash=auth_service.hash_password("secret"),
        is_active=True,
    )
    db.add(operator)
    db.commit()
    db.refresh(operator)
    return operator


def test_authentication_and_listing(db_session: Session) -> None:
    create_operator(db_session, "admin@example.com")
    operator = auth_service.authenticate_operator(db_session, "admin@example.com", "secret")
    assert operator.email == "admin@example.com"

    user = User(tg_user_id=123, username="user")
    db_session.add(user)
    db_session.flush()
    dialog = Dialog(user_id=user.id)
    db_session.add(dialog)
    db_session.flush()
    message = Message(dialog_id=dialog.id, sender=MessageSender.USER, text="Hello")
    db_session.add(message)
    db_session.commit()

    service = DialogService(db_session, get_notifier(), ConfidenceEvaluator(0.5))
    dialogs = service.list_dialogs()
    assert dialogs[0].id == dialog.id


def test_dialog_reply_flow(db_session: Session) -> None:
    operator = create_operator(db_session, "operator@example.com", role=OperatorRole.OPERATOR)
    service = DialogService(db_session, get_notifier(), ConfidenceEvaluator(0.65))

    user = User(tg_user_id=555, username="alice")
    db_session.add(user)
    db_session.flush()
    dialog = Dialog(user_id=user.id)
    db_session.add(dialog)
    db_session.commit()

    message = service.handle_operator_reply(dialog, operator, "We will help you")
    assert dialog.status == DialogStatus.WAITING_USER
    assert message.sender == MessageSender.OPERATOR


def test_kb_ingest_and_retrieve(db_session: Session) -> None:
    operator = create_operator(db_session, "kb@example.com", role=OperatorRole.OPERATOR)
    adapter_registry = build_default_registry()
    vector_store = VectorStore()
    ingestor = DocumentIngestor(db_session, vector_store, adapter_registry.get("openai"))
    upload = type("Upload", (), {"file": BytesIO(b"Support hours 9-18"), "filename": "doc.md"})()
    result = ingestor.ingest(upload, tags="support", operator_id=operator.id)
    assert result.document.title == "doc.md"

    retriever = Retriever(db_session, vector_store)
    results = retriever.retrieve("support", k=5)
    assert results


def test_dialog_service_confidence(db_session: Session) -> None:
    confidence = ConfidenceEvaluator(threshold=0.5)
    service = DialogService(db_session, get_notifier(), confidence)
    user = User(tg_user_id=1)
    db_session.add(user)
    db_session.flush()
    dialog = Dialog(user_id=user.id)
    db_session.add(dialog)
    db_session.commit()

    message = service.handle_bot_reply(dialog, "Answer with detail", 0.2, provider="openai")
    assert dialog.status == DialogStatus.WAITING_OPERATOR
    assert message.sender == MessageSender.BOT


def test_llm_router_uses_rag(db_session: Session) -> None:
    settings = get_settings()
    vector_store = VectorStore()
    retriever = Retriever(db_session, vector_store)
    router = LlmRouter(
        settings=settings,
        retriever=retriever,
        confidence=ConfidenceEvaluator(settings.confidence_threshold),
        adapters=build_default_registry(),
    )

    document = KnowledgeDocument(title="Card", tags="info", source_type="md")
    db_session.add(document)
    db_session.flush()
    chunk = KnowledgeChunk(document_id=document.id, chunk_text="Our price is 100", embedding=[1.0, 1.0])
    db_session.add(chunk)
    db_session.commit()
    vector_store.upsert(chunk.id, [1.0, 1.0])

    result = router.generate_reply(
        [ChatMessage(role="user", content="What is the price?")],
        system_prompt="system",
    )
    assert "Echo" in result.text
    assert result.citations


def test_auto_dialog_flow_with_router(db_session: Session) -> None:
    settings = get_settings()
    vector_store = VectorStore()
    retriever = Retriever(db_session, vector_store)
    router = LlmRouter(
        settings=settings,
        retriever=retriever,
        confidence=ConfidenceEvaluator(settings.confidence_threshold),
        adapters=build_default_registry(),
    )
    service = DialogService(db_session, get_notifier(), ConfidenceEvaluator(settings.confidence_threshold))

    user = User(tg_user_id=321)
    db_session.add(user)
    db_session.flush()
    dialog = Dialog(user_id=user.id)
    db_session.add(dialog)
    db_session.commit()

    service.handle_user_message(dialog, "Hello")
    history = [ChatMessage(role="user", content=m.text) for m in dialog.messages]
    result = router.generate_reply(history, "system")
    bot_message = service.handle_bot_reply(dialog, result.text, result.confidence, result.provider)
    assert bot_message.sender == MessageSender.BOT
    assert dialog.status in {DialogStatus.WAITING_OPERATOR, DialogStatus.WAITING_USER}
