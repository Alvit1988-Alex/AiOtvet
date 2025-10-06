"""Background task for embedding documents."""
from __future__ import annotations

import asyncio


async def process_queue() -> None:  # pragma: no cover - worker runtime
    while True:
        await asyncio.sleep(5)
