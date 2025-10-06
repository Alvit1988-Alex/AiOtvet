"""Entry point for the FastAPI application."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import _ENGINE  # noqa: PLC2701
from .models.base import Base
from .routers import dialogs, kb, operators, settings as settings_router
from .ws import notifications


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(operators.router)
    app.include_router(dialogs.router)
    app.include_router(kb.router)
    app.include_router(settings_router.router)
    app.include_router(notifications.router)

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=_ENGINE)

    return app


app = create_app()
