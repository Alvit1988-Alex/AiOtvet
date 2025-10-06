"""Application configuration settings using Pydantic."""
from __future__ import annotations

from functools import lru_cache
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = Field("AiOtvet Core API", description="Human readable service name")
    debug: bool = Field(False, description="Toggle debug features")

    database_url: str = Field(
        "sqlite:///./app.db",
        env="DATABASE_URL",
        description="SQLAlchemy connection string",
    )

    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    llm_provider: str = Field("openai", env="LLM_PROVIDER")
    llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL")
    embed_model: str = Field("text-embedding-3-small", env="EMBED_MODEL")
    temperature: float = Field(0.3, env="TEMPERATURE")
    max_tokens: int = Field(1024, env="MAX_TOKENS")
    confidence_threshold: float = Field(0.65, env="CONFIDENCE_THRESHOLD")

    openai_key: str | None = Field(None, env="OPENAI_API_KEY")
    lm_studio_url: str | None = Field("http://localhost:1234/v1", env="LM_STUDIO_URL")

    web_origin: str = Field("http://localhost:3000", env="WEB_ORIGIN")
    jwt_secret: str = Field("change_me", env="JWT_SECRET")
    jwt_exp_minutes: int = Field(60, env="JWT_EXP_MINUTES")

    sentry_dsn: str | None = Field(None, env="SENTRY_DSN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("confidence_threshold")
    def validate_confidence(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
