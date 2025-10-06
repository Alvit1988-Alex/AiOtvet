"""Database helpers for synchronous SQLAlchemy usage."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


_SETTINGS = get_settings()

_ENGINE = create_engine(
    _SETTINGS.database_url,
    connect_args={"check_same_thread": False} if _SETTINGS.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide transactional scope."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
