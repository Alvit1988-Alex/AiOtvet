"""Celery-like worker placeholder for background jobs."""
from __future__ import annotations

import asyncio
from typing import Callable, Coroutine

from .tasks import embeddings, notifications


async def run_worker() -> None:  # pragma: no cover - worker runtime
    tasks: list[Coroutine[None, None, None]] = [
        embeddings.process_queue(),
        notifications.dispatch_queue(),
    ]
    await asyncio.gather(*tasks)
