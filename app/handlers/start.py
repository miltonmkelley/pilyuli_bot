"""Handler for the /start command."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
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


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    """Handle /menu command: clear states and show menu."""
    if not message.from_user:
        return

    try:
        await message.delete()
    except Exception:
        pass

    await state.clear()
    
    if message.bot:
        from app.keyboards import main_menu_kb
        await send_single_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text="🏠 Главное меню:",
            reply_markup=main_menu_kb(),
        )
