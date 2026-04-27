"""Handler for the /settings command — configure notification preferences."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.keyboards import main_menu_kb
from app.services.settings_service import get_settings_by_telegram_id, update_settings
from app.services.message_service import send_single_message

router = Router()


class EditSettings(StatesGroup):
    """FSM states for editing notification settings."""

    interval = State()


def _settings_text(interval: int) -> str:
    return (
        f"⚙️ Настройки уведомлений:\n\n"
        f"⏱ Интервал повторных уведомлений: {interval} мин.\n\n"
        f"Введите новый интервал в минутах (1–120):\n"
        f"Для отмены отправьте /cancel"
    )


@router.message(Command("settings"))
async def cmd_settings(message: Message, state: FSMContext) -> None:
    """Show current settings and offer to change them."""
    if not message.from_user:
        return

    try:
        await message.delete()
    except Exception:
        pass

    current = await get_settings_by_telegram_id(message.from_user.id)
    if message.bot:
        await send_single_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text=_settings_text(current["reminder_interval_minutes"]),
        )
    await state.set_state(EditSettings.interval)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Cancel settings editing."""
    try:
        await message.delete()
    except Exception:
        pass

    current_state = await state.get_state()
    if current_state:
        await state.clear()
        if message.bot:
            await send_single_message(
                bot=message.bot,
                chat_id=message.chat.id,
                text="❌ Отменено.",
                reply_markup=main_menu_kb()
            )
    else:
        if message.bot:
            await send_single_message(
                bot=message.bot,
                chat_id=message.chat.id,
                text="Нечего отменять."
            )


@router.message(EditSettings.interval)
async def process_interval(message: Message, state: FSMContext) -> None:
    """Receive reminder interval and save settings."""
    try:
        await message.delete()
    except Exception:
        pass

    text = (message.text or "").strip()

    if not text.isdigit() or not (1 <= int(text) <= 120):
        if message.bot:
            await send_single_message(
                bot=message.bot,
                chat_id=message.chat.id,
                text="Введите число от 1 до 120:"
            )
        return

    if not message.from_user:
        return

    interval = int(text)
    await update_settings(message.from_user.id, interval)
    await state.clear()
    if message.bot:
        await send_single_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text=(
                f"✅ Настройки сохранены!\n\n"
                f"⏱ Интервал повторных уведомлений: {interval} мин."
            ),
            reply_markup=main_menu_kb(),
        )
