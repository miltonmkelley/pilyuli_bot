"""Handler for the /start command."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards import main_menu_kb, persistent_menu_kb
from app.services.medicine_service import ensure_user
from app.services.message_service import send_single_message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Register user and send greeting."""
    if not message.from_user:
        return

    await ensure_user(message.from_user.id)
    
    # Delete user's command message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    # Send persistent reply keyboard (always visible at bottom)
    await send_single_message(
        bot=message.bot,
        chat_id=message.chat.id,
        text="👋 Привет! Я бот-напоминалка о лекарствах.\n\n"
             "Используй кнопки внизу для быстрого доступа 👇",
        reply_markup=persistent_menu_kb(),
    )
