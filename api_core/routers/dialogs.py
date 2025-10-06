"""Dialog related API endpoints."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..adapters.llm_base import ChatMessage
from ..deps import get_db, require_role, get_current_operator, get_settings_dep
from ..models import DialogStatus, DialogMode, MessageSender, Operator, OperatorRole
from ..rag import get_retriever
from ..schemas import DialogDetail, DialogListItem, MessageSchema
from ..services.dialog_service import DialogService
from ..services.llm_router import LlmRouter
from ..state import build_confidence, get_adapter_registry, get_notifier

router = APIRouter(prefix="/api/dialogs", tags=["dialogs"])

SYSTEM_PROMPT = (
    "You are AiOtvet assistant. Respond based on company knowledge."
)


class ReplyRequest(BaseModel):
    text: str


class AssignRequest(BaseModel):
    operator_id: int


class TakeoverRequest(BaseModel):
    by_operator_id: Optional[int] = None


class PaginationQuery(BaseModel):
    before_id: Optional[int] = None
    limit: int = 50


def get_dialog_service(
    db: Session = Depends(get_db),
    settings=Depends(get_settings_dep),
) -> DialogService:
    confidence = build_confidence(settings.confidence_threshold)
    return DialogService(db, get_notifier(), confidence)


def get_llm_router(
    db: Session = Depends(get_db),
    settings=Depends(get_settings_dep),
) -> LlmRouter:
    confidence = build_confidence(settings.confidence_threshold)
    retriever = get_retriever(db)
    return LlmRouter(settings=settings, retriever=retriever, confidence=confidence, adapters=get_adapter_registry())


class BotMessageRequest(BaseModel):
    tg_user_id: int
    message: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@router.post("", response_model=MessageSchema)
def ingest_user_message(
    payload: BotMessageRequest,
    service: DialogService = Depends(get_dialog_service),
    router_dep: LlmRouter = Depends(get_llm_router),
):
    user = service.ensure_user(
        payload.tg_user_id,
        {
            "username": payload.username,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
        },
    )
    dialog = service.create_or_get_active_dialog(user)
    message = service.handle_user_message(dialog, payload.message)
    history = [
        ChatMessage(
            role="assistant" if m.sender in {MessageSender.BOT, MessageSender.OPERATOR} else "user",
            content=m.text,
        )
        for m in dialog.messages
    ]
    if dialog.mode == DialogMode.AUTO:
        result = router_dep.generate_reply(history, SYSTEM_PROMPT)
        bot_message = service.handle_bot_reply(dialog, result.text, result.confidence, result.provider)
        return MessageSchema.from_orm(bot_message)
    return MessageSchema.from_orm(message)


@router.get("", response_model=List[DialogListItem])
def list_dialogs(
    status: DialogStatus | None = None,
    service: DialogService = Depends(get_dialog_service),
    _: Operator = Depends(require_role(OperatorRole.OPERATOR)),
):
    dialogs = service.list_dialogs(status=status)
    return dialogs


@router.get("/{dialog_id}", response_model=DialogDetail)
def dialog_details(
    dialog_id: int,
    service: DialogService = Depends(get_dialog_service),
    _: Operator = Depends(require_role(OperatorRole.OPERATOR)),
):
    try:
        dialog = service.get_dialog(dialog_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DialogDetail(dialog=dialog, messages=[MessageSchema.from_orm(m) for m in dialog.messages])


@router.post("/{dialog_id}/reply", response_model=MessageSchema)
def reply_dialog(
    dialog_id: int,
    payload: ReplyRequest,
    service: DialogService = Depends(get_dialog_service),
    operator: Operator = Depends(get_current_operator),
):
    try:
        dialog = service.get_dialog(dialog_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    message = service.handle_operator_reply(dialog, operator, payload.text)
    return MessageSchema.from_orm(message)


@router.post("/{dialog_id}/assign")
def assign_dialog(
    dialog_id: int,
    payload: AssignRequest,
    service: DialogService = Depends(get_dialog_service),
    _: Operator = Depends(require_role(OperatorRole.LEAD)),
    db: Session = Depends(get_db),
):
    try:
        dialog = service.get_dialog(dialog_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    operator = db.get(Operator, payload.operator_id)
    if operator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")
    service.assign_operator(dialog, operator)
    return {"status": "ok"}


@router.post("/{dialog_id}/takeover")
def takeover_dialog(
    dialog_id: int,
    payload: TakeoverRequest,
    service: DialogService = Depends(get_dialog_service),
    operator: Operator = Depends(get_current_operator),
):
    try:
        dialog = service.get_dialog(dialog_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    service.takeover(dialog, operator)
    return {"status": "ok"}


@router.post("/{dialog_id}/handoff")
def handoff_dialog(
    dialog_id: int,
    service: DialogService = Depends(get_dialog_service),
    _: Operator = Depends(require_role(OperatorRole.OPERATOR)),
):
    try:
        dialog = service.get_dialog(dialog_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    service.handoff_to_auto(dialog)
    return {"status": "ok"}


@router.get("/{dialog_id}/messages", response_model=List[MessageSchema])
def paginate_messages(
    dialog_id: int,
    before_id: int | None = None,
    limit: int = 50,
    service: DialogService = Depends(get_dialog_service),
    _: Operator = Depends(require_role(OperatorRole.OPERATOR)),
):
    try:
        dialog = service.get_dialog(dialog_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    messages = service.paginate_messages(dialog, limit=limit, before_id=before_id)
    return [MessageSchema.from_orm(message) for message in messages]
