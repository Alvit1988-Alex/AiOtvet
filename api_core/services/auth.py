"""Authentication utilities for operators."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import Operator, OperatorRole


class InvalidTokenError(RuntimeError):
    """Raised when decoding of a token fails."""


PBKDF_ITERATIONS = 390000


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Return a salted PBKDF2 hash."""

    salt = salt or hashlib.sha256(password.encode("utf-8")).digest()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF_ITERATIONS)
    return _b64encode(salt) + ":" + _b64encode(dk)


def verify_password(password: str, stored: str) -> bool:
    """Check whether password matches stored hash."""

    salt_b64, hash_b64 = stored.split(":", 1)
    salt = _b64decode(salt_b64)
    expected = _b64decode(hash_b64)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF_ITERATIONS)
    return hmac.compare_digest(candidate, expected)


def create_token(payload: Dict[str, Any], secret: str, expires_minutes: int = 60) -> str:
    """Create a HS256 signed token."""

    header = {"alg": "HS256", "typ": "JWT"}
    payload = payload.copy()
    payload["exp"] = int((datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)).timestamp())

    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), f"{header_b64}.{payload_b64}".encode("utf-8"), hashlib.sha256)
    signature_b64 = _b64encode(signature.digest())
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_token(token: str, secret: str) -> Dict[str, Any]:
    """Decode a HS256 signed token."""

    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise InvalidTokenError("Malformed token") from exc

    signature = hmac.new(secret.encode("utf-8"), f"{header_b64}.{payload_b64}".encode("utf-8"), hashlib.sha256)
    if not hmac.compare_digest(signature.digest(), _b64decode(signature_b64)):
        raise InvalidTokenError("Signature mismatch")

    payload = json.loads(_b64decode(payload_b64))
    exp = payload.get("exp")
    if exp is not None and datetime.now(tz=timezone.utc).timestamp() > exp:
        raise InvalidTokenError("Token expired")
    return payload


def authenticate_operator(db: Session, email: str, password: str) -> Operator:
    """Validate operator credentials."""

    operator = db.query(Operator).filter(Operator.email == email).first()
    if not operator or not operator.password_hash or not verify_password(password, operator.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not operator.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator inactive")
    return operator


def ensure_admin(operator: Operator) -> None:
    """Helper raising if operator lacks admin rights."""

    if operator.role != OperatorRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privilege required")
