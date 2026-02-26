"""Handler for the /settings command — configure notification preferences."""

from __future__ import annotations

import re

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

    max_reminders = State()
    interval = State()


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
            text=(
                f"⚙️ Текущие настройки уведомлений:\n\n"
                f"🔔 Макс. напоминаний: {current['max_reminders']}\n"
                f"⏱ Интервал: {current['reminder_interval_minutes']} мин.\n\n"
                f"Хотите изменить? Введите максимальное кол-во напоминаний (1–10).\n"
                f"Для отмены отправьте /cancel"
            )
        )
    await state.set_state(EditSettings.max_reminders)


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
                text="❌ Настройка отменена.", 
                reply_markup=main_menu_kb()
            )
    else:
        if message.bot:
            await send_single_message(
                bot=message.bot,
                chat_id=message.chat.id,
                text="Нечего отменять."
            )


@router.message(EditSettings.max_reminders)
async def process_max_reminders(message: Message, state: FSMContext) -> None:
    """Receive max reminders count."""
    try:
        await message.delete()
    except Exception:
        pass

    text = (message.text or "").strip()

    if not text.isdigit() or not (1 <= int(text) <= 10):
        if message.bot:
            await send_single_message(
                bot=message.bot,
                chat_id=message.chat.id,
                text="Введите число от 1 до 10:"
            )
        return

    await state.update_data(max_reminders=int(text))
    await state.set_state(EditSettings.interval)
    if message.bot:
        await send_single_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text="⏱ Введите интервал между напоминаниями в минутах (1–60):"
        )


@router.message(EditSettings.interval)
async def process_interval(message: Message, state: FSMContext) -> None:
    """Receive reminder interval and save settings."""
    try:
        await message.delete()
    except Exception:
        pass

    text = (message.text or "").strip()

    if not text.isdigit() or not (1 <= int(text) <= 60):
        if message.bot:
            await send_single_message(
                bot=message.bot,
                chat_id=message.chat.id,
                text="Введите число от 1 до 60:"
            )
        return

    if not message.from_user:
        return

    data = await state.get_data()
    max_r = data["max_reminders"]
    interval = int(text)

    await update_settings(message.from_user.id, max_r, interval)
    await state.clear()
    if message.bot:
        await send_single_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text=(
                f"✅ Настройки сохранены!\n\n"
                f"🔔 Макс. напоминаний: {max_r}\n"
                f"⏱ Интервал: {interval} мин."
            ),
            reply_markup=main_menu_kb(),
        )
