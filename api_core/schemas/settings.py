"""Settings API schema."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SettingsSchema(BaseModel):
    llm_provider: str = Field(...)
    model: str = Field(...)
    temperature: float = Field(...)
    max_tokens: int = Field(...)
    confidence_threshold: float = Field(...)
    lm_studio_url: str | None = Field(default=None)
    openai_key: str | None = Field(default=None)


class UpdateSettingsRequest(BaseModel):
    llm_provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    confidence_threshold: float | None = None
    lm_studio_url: str | None = None
    openai_key: str | None = None
