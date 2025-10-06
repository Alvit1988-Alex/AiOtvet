"""Admin Telegram bot placeholder."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.types import Message


def create_bot(token: str) -> Dispatcher:
    bot = Bot(token)
    dp = Dispatcher()

    @dp.message()
    async def handle_admin(message: Message) -> None:  # pragma: no cover - Telegram integration
        await message.answer("Admin bot online")

    return dp
