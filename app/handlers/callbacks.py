"""Callback query handlers for dose inline buttons and menu navigation."""

from __future__ import annotations

from datetime import datetime

import pytz
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.config import settings
from app.keyboards import main_menu_kb
from app.services.dose_service import mark_taken, snooze


router = Router()


# ── Menu navigation callbacks ──────────────────────────────────────


@router.callback_query(F.data == "menu:add")
async def on_menu_add(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle '💊 Добавить' button — start add-medicine FSM."""
    from app.handlers.add_medicine import AddMedicine

    await callback.answer()
    await state.set_state(AddMedicine.name)
    await callback.message.answer("💊 Введите название лекарства:")  # type: ignore[union-attr]


@router.callback_query(F.data == "menu:today")
async def on_menu_today(callback: CallbackQuery) -> None:
    """Handle '📋 Сегодня' button — show today's schedule."""
    from app.handlers.today import _format_today

    if not callback.from_user:
        return

    await callback.answer()
    text = await _format_today(callback.from_user.id)
    await callback.message.answer(text, reply_markup=main_menu_kb())  # type: ignore[union-attr]


@router.callback_query(F.data == "menu:settings")
async def on_menu_settings(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle '⚙️ Настройки' button — show settings."""
    from app.handlers.settings import EditSettings
    from app.services.settings_service import get_settings_by_telegram_id

    if not callback.from_user:
        return

    await callback.answer()
    current = await get_settings_by_telegram_id(callback.from_user.id)
    await callback.message.answer(  # type: ignore[union-attr]
        f"⚙️ Текущие настройки уведомлений:\n\n"
        f"🔔 Макс. напоминаний: {current['max_reminders']}\n"
        f"⏱ Интервал: {current['reminder_interval_minutes']} мин.\n\n"
        f"Хотите изменить? Введите максимальное кол-во напоминаний (1–10).\n"
        f"Для отмены отправьте /cancel"
    )
    await state.set_state(EditSettings.max_reminders)


# ── Dose action callbacks ──────────────────────────────────────────


@router.callback_query(F.data.startswith("dose_taken:"))
async def on_dose_taken(callback: CallbackQuery) -> None:
    """Handle the 'Taken' button press."""
    if not callback.data:
        return

    dose_id = int(callback.data.split(":")[1])
    tz = pytz.timezone(settings.timezone)
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    success = await mark_taken(dose_id, now_str)

    if success:
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"✅ Отмечено как принятое в {now_str}"
        )
    else:
        await callback.answer("⚠️ Этот приём уже обработан.", show_alert=True)


@router.callback_query(F.data.startswith("dose_snooze:"))
async def on_dose_snooze(callback: CallbackQuery) -> None:
    """Handle the 'Snooze' button press."""
    if not callback.data:
        return

    dose_id = int(callback.data.split(":")[1])
    success = await snooze(dose_id)

    if success:
        await callback.message.edit_text(  # type: ignore[union-attr]
            "⏰ Напоминание отложено на 10 минут"
        )
    else:
        await callback.answer("⚠️ Этот приём уже обработан.", show_alert=True)
