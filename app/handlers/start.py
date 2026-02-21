"""Handler for the /start command."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards import main_menu_kb
from app.services.medicine_service import ensure_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Register user and send greeting."""
    if not message.from_user:
        return

    await ensure_user(message.from_user.id)

    await message.answer(
        "👋 Привет! Я бот-напоминалка о лекарствах.\n\n"
        "Доступные команды:\n"
        "/add — добавить лекарство\n"
        "/today — расписание на сегодня\n"
        "/settings — настройки уведомлений",
        reply_markup=main_menu_kb(),
    )
