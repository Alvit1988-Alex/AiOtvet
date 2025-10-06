"""Declarative base setup for SQLAlchemy models."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


def _camel_to_snake(name: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


class Base(DeclarativeBase):
    """Base class adding automatic table naming and timestamps."""

    metadata = MetaData()

    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore[misc]
        return _camel_to_snake(cls.__name__)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON serialisable representation of the model."""

        data: dict[str, Any] = {}
        for column in self.__table__.columns:  # type: ignore[attr-defined]
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                data[column.name] = value.isoformat()
            else:
                data[column.name] = value
        return data
