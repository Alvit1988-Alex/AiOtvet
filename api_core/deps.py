"""FastAPI dependency definitions."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .db import SessionLocal
from .models import Operator, OperatorRole
from .services import auth as auth_service


security_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for the request."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_settings_dep() -> Settings:
    """FastAPI dependency returning the settings instance."""

    return get_settings()


def get_current_operator(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> Operator:
    """Resolve current operator from a JWT token."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = auth_service.decode_token(credentials.credentials, settings.jwt_secret)
    except auth_service.InvalidTokenError as exc:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    operator_id = payload.get("sub")
    if operator_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    operator = db.get(Operator, int(operator_id))
    if operator is None or not operator.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Operator disabled")
    return operator


def require_role(required: OperatorRole):
    """Dependency factory enforcing a minimal role."""

    def dependency(operator: Operator = Depends(get_current_operator)) -> Operator:
        if operator.role == OperatorRole.ADMIN:
            return operator
        if operator.role == OperatorRole.LEAD and required in {OperatorRole.OPERATOR, OperatorRole.LEAD}:
            return operator
        if operator.role == OperatorRole.OPERATOR and required == OperatorRole.OPERATOR:
            return operator
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    return dependency
