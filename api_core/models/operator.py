"""Operator model for internal staff accounts."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as PgEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class OperatorRole(str, Enum):
    """Role describing operator permissions."""

    OPERATOR = "operator"
    LEAD = "lead"
    ADMIN = "admin"


class Operator(Base):
    """Staff member able to work with dialogs."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[OperatorRole] = mapped_column(PgEnum(OperatorRole))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dialogs: Mapped[list["Dialog"]] = relationship("Dialog", back_populates="assigned_operator")
