"""Dialog and message related ORM models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as PgEnum, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class DialogStatus(str, Enum):
    """Possible dialog processing states."""

    AUTO = "auto"
    WAITING_OPERATOR = "waiting_operator"
    WAITING_USER = "waiting_user"


class DialogMode(str, Enum):
    """Mode describing who is in control of the dialog."""

    AUTO = "auto"
    HUMAN = "human"


class MessageSender(str, Enum):
    """Participants capable of sending messages."""

    USER = "user"
    BOT = "bot"
    OPERATOR = "operator"


class Dialog(Base):
    """High-level conversation metadata."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    assigned_operator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("operator.id"), nullable=True
    )
    status: Mapped[DialogStatus] = mapped_column(
        PgEnum(DialogStatus), default=DialogStatus.AUTO, index=True
    )
    mode: Mapped[DialogMode] = mapped_column(
        PgEnum(DialogMode), default=DialogMode.AUTO, index=True
    )
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="dialogs")
    assigned_operator: Mapped[Optional["Operator"]] = relationship("Operator")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="dialog", order_by="Message.created_at"
    )


Index("ix_dialog_status_last_message", Dialog.status, Dialog.last_message_at)


class Message(Base):
    """Individual message belonging to a dialog."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dialog_id: Mapped[int] = mapped_column(ForeignKey("dialog.id"), index=True)
    sender: Mapped[MessageSender] = mapped_column(PgEnum(MessageSender), index=True)
    text: Mapped[str] = mapped_column(String)
    payload: Mapped[dict | None] = mapped_column(JSON, default=dict)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    dialog: Mapped[Dialog] = relationship("Dialog", back_populates="messages")


Index("ix_message_dialog_created", Message.dialog_id, Message.created_at)
