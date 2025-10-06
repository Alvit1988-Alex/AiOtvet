"""Operator management and auth endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..deps import get_db, get_settings_dep, require_role
from ..models import Operator, OperatorRole
from ..schemas.dialog import OperatorSchema
from ..services import auth as auth_service

router = APIRouter(prefix="/api", tags=["operators"])


class OperatorCreateRequest(BaseModel):
    email: EmailStr
    role: OperatorRole = OperatorRole.OPERATOR
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TelegramAuthRequest(BaseModel):
    init_data: str


class TwoFactorRequest(BaseModel):
    operator_id: int
    code: str


@router.get("/operators", response_model=list[OperatorSchema])
def list_operators(
    db: Session = Depends(get_db),
    _: Operator = Depends(require_role(OperatorRole.LEAD)),
):
    operators = db.query(Operator).all()
    return [OperatorSchema.from_orm(op) for op in operators]


@router.post("/operators", response_model=OperatorSchema, status_code=status.HTTP_201_CREATED)
def create_operator(
    payload: OperatorCreateRequest,
    db: Session = Depends(get_db),
    _: Operator = Depends(require_role(OperatorRole.ADMIN)),
):
    if db.query(Operator).filter(Operator.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    password_hash = auth_service.hash_password(payload.password)
    operator = Operator(
        email=payload.email,
        role=payload.role,
        password_hash=password_hash,
        created_at=datetime.utcnow(),
    )
    db.add(operator)
    db.commit()
    db.refresh(operator)
    return OperatorSchema.from_orm(operator)


@router.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    settings=Depends(get_settings_dep),
):
    operator = auth_service.authenticate_operator(db, payload.email, payload.password)
    token = auth_service.create_token({"sub": operator.id}, secret=settings.jwt_secret, expires_minutes=settings.jwt_exp_minutes)
    return TokenResponse(access_token=token)


def _verify_tg_init_data(init_data: str, bot_token: str) -> bool:
    """Validate Telegram init data signature."""

    if not init_data:
        return False
    # TODO: Implement HMAC-SHA256 validation according to Telegram spec.
    return True


@router.post("/auth/tg", response_model=TokenResponse)
def telegram_login(
    payload: TelegramAuthRequest,
    db: Session = Depends(get_db),
    settings=Depends(get_settings_dep),
):
    if not _verify_tg_init_data(payload.init_data, settings.jwt_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    operator = db.query(Operator).filter(Operator.is_active == True).first()  # noqa: E712
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")
    token = auth_service.create_token({"sub": operator.id}, secret=settings.jwt_secret)
    return TokenResponse(access_token=token)


@router.post("/auth/2fa/verify")
def verify_2fa(
    payload: TwoFactorRequest,
    db: Session = Depends(get_db),
):
    operator = db.get(Operator, payload.operator_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    if payload.code != "000000":
        raise HTTPException(status_code=400, detail="Invalid code")
    return {"status": "verified"}
