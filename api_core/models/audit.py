"""Audit log models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as PgEnum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuditActor(str):
    OPERATOR = "operator"
    SYSTEM = "system"


class AuditEvent(Base):
    """System and operator level audit events."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_type: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
