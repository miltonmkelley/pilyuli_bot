"""Bot and Dispatcher factory."""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.handlers import add_medicine, callbacks, start, today
from app.handlers import settings as settings_handler


def create_bot() -> Bot:
    """Create a Bot instance."""
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """Create a Dispatcher and register all handler routers."""
    dp = Dispatcher()
    dp.include_routers(
        start.router,
        add_medicine.router,
        today.router,
        settings_handler.router,
        callbacks.router,
    )
    return dp
