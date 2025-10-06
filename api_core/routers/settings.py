"""Settings endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, require_role, get_settings_dep
from ..models import Setting, OperatorRole
from ..schemas import SettingsSchema, UpdateSettingsRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsSchema)
def read_settings(
    db: Session = Depends(get_db),
    settings=Depends(get_settings_dep),
    _: str = Depends(require_role(OperatorRole.OPERATOR)),
):
    overrides = {setting.key: setting.value for setting in db.query(Setting).all()}
    return SettingsSchema(
        llm_provider=overrides.get("llm_provider", settings.llm_provider),
        model=overrides.get("model", settings.llm_model),
        temperature=float(overrides.get("temperature", settings.temperature)),
        max_tokens=int(overrides.get("max_tokens", settings.max_tokens)),
        confidence_threshold=float(
            overrides.get("confidence_threshold", settings.confidence_threshold)
        ),
        lm_studio_url=overrides.get("lm_studio_url", settings.lm_studio_url),
        openai_key=overrides.get("openai_key", settings.openai_key),
    )


@router.put("", response_model=SettingsSchema)
def update_settings(
    payload: UpdateSettingsRequest,
    db: Session = Depends(get_db),
    settings=Depends(get_settings_dep),
    _: str = Depends(require_role(OperatorRole.ADMIN)),
):
    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setting = db.get(Setting, key)
        if setting:
            setting.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))
    db.commit()
    return read_settings(db=db, settings=settings)
