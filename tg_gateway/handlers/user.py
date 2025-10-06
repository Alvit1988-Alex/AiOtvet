"""User bot handlers interacting with the core API."""
from __future__ import annotations

from aiogram.types import Message

from ..utils.api_client import ApiClient

_client = ApiClient()


async def handle_incoming(message: Message) -> None:  # pragma: no cover - Telegram integration
    dialog = await _client.ensure_dialog(message.from_user.id, message.text or "")
    await message.answer(dialog["reply"])  # type: ignore[index]
