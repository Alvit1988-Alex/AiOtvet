import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:  # pragma: no cover - environment guard
    import sqlalchemy  # noqa: F401
except ImportError:  # pragma: no cover - skip when dependency missing
    pytest.exit("sqlalchemy not available", returncode=0)

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from api_core.db import _ENGINE, SessionLocal
from api_core.models.base import Base


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_ENGINE)
    yield
    Base.metadata.drop_all(bind=_ENGINE)


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
