"""Background notification dispatcher."""
from __future__ import annotations

import asyncio


async def dispatch_queue() -> None:  # pragma: no cover - worker runtime
    while True:
        await asyncio.sleep(5)
