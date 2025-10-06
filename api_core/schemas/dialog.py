"""Pydantic schemas for dialog endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from ..models import DialogMode, DialogStatus, MessageSender, OperatorRole


class UserSchema(BaseModel):
    id: int
    tg_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None

    class Config:
        orm_mode = True


class OperatorSchema(BaseModel):
    id: int
    email: str
    role: OperatorRole

    class Config:
        orm_mode = True


class DialogListItem(BaseModel):
    id: int
    user: UserSchema
    status: DialogStatus
    mode: DialogMode
    assigned_operator: OperatorSchema | None
    last_message_at: datetime
    unread_count: int = 0

    class Config:
        orm_mode = True


class MessageSchema(BaseModel):
    id: int
    dialog_id: int
    sender: MessageSender
    text: str
    payload: dict | None
    llm_provider: str | None
    confidence: float | None
    created_at: datetime

    class Config:
        orm_mode = True


class DialogDetail(BaseModel):
    dialog: DialogListItem
    messages: List[MessageSchema]
