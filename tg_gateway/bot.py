"""Aiogram bot entry point for the customer facing bot."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.types import Message

from .handlers import user


def create_bot(token: str) -> Dispatcher:
    bot = Bot(token)
    dp = Dispatcher()

    @dp.message()
    async def handle_message(message: Message) -> None:  # pragma: no cover - requires Telegram
        await user.handle_incoming(message)

    return dp
