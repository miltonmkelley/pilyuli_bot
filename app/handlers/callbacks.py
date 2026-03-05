"""Callback query handlers for dose buttons and menu (inline + reply keyboard)."""

from __future__ import annotations

from datetime import datetime

import pytz
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.keyboards import main_menu_kb, schedule_menu_kb, history_kb
from app.services.dose_service import mark_taken, snooze
from app.services.message_service import send_single_message

router = Router()


# ── Reply keyboard text button handlers ────────────────────────────


@router.message(F.text == "📋 Расписание")
async def on_reply_schedule(message: Message) -> None:
    """Handle reply keyboard '📋 Расписание' button — show add/delete sub-menu."""
    try:
        await message.delete()
    except Exception:
        pass
    if message.bot:
        await send_single_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text="📋 Управление расписанием:", 
            reply_markup=schedule_menu_kb()
        )


@router.message(F.text == "📋 Сегодня")
async def on_reply_today(message: Message) -> None:
    """Handle reply keyboard '📋 Сегодня' button."""
    from app.handlers.today import _format_today

    if not message.from_user:
        return

    try:
        await message.delete()
    except Exception:
        pass

    text, doses = await _format_today(message.from_user.id)
    if message.bot:
        from app.keyboards import today_kb, back_to_main_kb
        reply_markup = today_kb(doses) if doses else back_to_main_kb()
        await send_single_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text=text, 
            reply_markup=reply_markup
        )


@router.message(F.text == "⚙️ Настройки")
async def on_reply_settings(message: Message, state: FSMContext) -> None:
    """Handle reply keyboard '⚙️ Настройки' button."""
    from app.handlers.settings import EditSettings
    from app.services.settings_service import get_settings_by_telegram_id

    if not message.from_user:
        return

    try:
        await message.delete()
    except Exception:
        pass

    current = await get_settings_by_telegram_id(message.from_user.id)
    from app.keyboards import back_to_main_kb
    if message.bot:
        await send_single_message(
            bot=message.bot,
            chat_id=message.chat.id,
            text=(
                f"⚙️ Текущие настройки уведомлений:\n\n"
                f"🔔 Макс. напоминаний: {current['max_reminders']}\n"
                f"⏱ Интервал: {current['reminder_interval_minutes']} мин.\n\n"
                f"Хотите изменить? Введите максимальное кол-во напоминаний (1–10).\n"
                f"Для отмены отправьте /cancel или вернитесь в главное меню."
            ),
            reply_markup=back_to_main_kb()
        )
    await state.set_state(EditSettings.max_reminders)


# ── Schedule sub-menu callbacks ───────────────────────────────────


@router.callback_query(F.data == "sched:add")
async def on_sched_add(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle schedule sub-menu '💊 Добавить' button."""
    from app.handlers.add_medicine import AddMedicine

    await callback.answer()
    await state.set_state(AddMedicine.name)
    if callback.message and callback.message.bot:
        await send_single_message(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            text="💊 Введите название лекарства:"
        )


@router.callback_query(F.data == "sched:delete")
async def on_sched_delete(callback: CallbackQuery) -> None:
    """Handle schedule sub-menu '🗑 Удалить' — show medicine list."""
    from app.keyboards import delete_medicine_kb
    from app.services.medicine_service import get_user_medicines

    if not callback.from_user:
        return

    await callback.answer()
    medicines = await get_user_medicines(callback.from_user.id)

    if not medicines:
        await callback.message.edit_text("📭 У вас нет добавленных лекарств.")  # type: ignore[union-attr]
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        "🗑 Выберите лекарство для удаления:",
        reply_markup=delete_medicine_kb(medicines),
    )


@router.callback_query(F.data == "sched:back")
async def on_sched_back(callback: CallbackQuery) -> None:
    """Handle '↩️ Назад' — return to schedule sub-menu."""
    await callback.answer()
    await callback.message.edit_text(  # type: ignore[union-attr]
        "📋 Управление расписанием:", reply_markup=schedule_menu_kb()
    )


@router.callback_query(F.data.startswith("delete_med:"))
async def on_delete_medicine(callback: CallbackQuery) -> None:
    """Handle medicine deletion."""
    from app.services.medicine_service import delete_medicine

    if not callback.data:
        return

    medicine_id = int(callback.data.split(":")[1])
    success = await delete_medicine(medicine_id)

    if success:
        from app.keyboards import schedule_menu_kb
        await callback.message.edit_text(
            "✅ Лекарство удалено из расписания.", 
            reply_markup=schedule_menu_kb()
        )
    else:
        await callback.answer("⚠️ Лекарство не найдено.", show_alert=True)


# ── History callbacks ─────────────────────────────────────────────


@router.callback_query(F.data.startswith("history:"))
async def on_history(callback: CallbackQuery) -> None:
    """Handle history buttons (yesterday, week)."""
    from app.handlers.today import format_history

    if not callback.from_user or not callback.data:
        return

    period = callback.data.split(":")[1]  # yesterday or week
    await callback.answer()
    text = await format_history(callback.from_user.id, period)
    if callback.message and callback.message.bot:
        from app.keyboards import back_to_main_kb
        await send_single_message(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=back_to_main_kb()
        )


# ── Inline menu navigation callbacks ──────────────────────────────


@router.callback_query(F.data == "menu:schedule")
async def on_menu_schedule(callback: CallbackQuery) -> None:
    """Handle inline '📋 Расписание' button."""
    await callback.answer()
    if callback.message and callback.message.bot:
        await send_single_message(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            text="📋 Управление расписанием:", 
            reply_markup=schedule_menu_kb()
        )


@router.callback_query(F.data == "menu:today")
async def on_menu_today(callback: CallbackQuery) -> None:
    """Handle inline '📋 Сегодня' button."""
    from app.handlers.today import _format_today

    if not callback.from_user:
        return

    await callback.answer()
    text, doses = await _format_today(callback.from_user.id)
    if callback.message and callback.message.bot:
        from app.keyboards import today_kb, back_to_main_kb
        reply_markup = today_kb(doses) if doses else back_to_main_kb()
        await send_single_message(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            text=text, 
            reply_markup=reply_markup
        )


@router.callback_query(F.data == "menu:history")
async def on_menu_history(callback: CallbackQuery) -> None:
    """Handle inline '📅 История' button."""
    await callback.answer()
    if callback.message and callback.message.bot:
        from app.keyboards import history_kb
        await callback.message.edit_text(  # type: ignore[union-attr]
            "📅 Выберите период для просмотра истории:",
            reply_markup=history_kb()
        )


@router.callback_query(F.data == "menu:main")
async def on_menu_main(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle inline '🏠 Главное меню' button."""
    await callback.answer()
    await state.clear()
    if callback.message and callback.message.bot:
        await send_single_message(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            text="🏠 Главное меню:", 
            reply_markup=main_menu_kb()
        )


@router.callback_query(F.data == "menu:settings")
async def on_menu_settings(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle inline '⚙️ Настройки' button."""
    from app.handlers.settings import EditSettings
    from app.services.settings_service import get_settings_by_telegram_id

    if not callback.from_user:
        return

    await callback.answer()
    current = await get_settings_by_telegram_id(callback.from_user.id)
    from app.keyboards import back_to_main_kb
    if callback.message and callback.message.bot:
        await send_single_message(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            text=(
                f"⚙️ Текущие настройки уведомлений:\n\n"
                f"🔔 Макс. напоминаний: {current['max_reminders']}\n"
                f"⏱ Интервал: {current['reminder_interval_minutes']} мин.\n\n"
                f"Хотите изменить? Введите максимальное кол-во напоминаний (1–10).\n"
                f"Для отмены отправьте /cancel или вернитесь в главное меню."
            ),
            reply_markup=back_to_main_kb()
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
    if not callback.data or not callback.from_user:
        return

    from app.services.settings_service import get_settings_by_telegram_id

    dose_id = int(callback.data.split(":")[1])
    user_settings = await get_settings_by_telegram_id(callback.from_user.id)
    interval = user_settings["reminder_interval_minutes"]

    success, used_interval = await snooze(dose_id, interval)

    if success:
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"⏰ Напоминание отложено на {used_interval} мин."
        )
    else:
        await callback.answer("⚠️ Этот приём уже обработан.", show_alert=True)


@router.callback_query(F.data.startswith("dose_skip:"))
async def on_dose_skip(callback: CallbackQuery) -> None:
    """Handle the 'Skip / Not today' button press."""
    if not callback.data:
        return

    from app.services.dose_service import mark_skipped
    dose_id = int(callback.data.split(":")[1])
    
    success = await mark_skipped(dose_id)

    if success:
        await callback.message.edit_text(  # type: ignore[union-attr]
            "❌ Отмечено как пропущенное."
        )
    else:
        await callback.answer("⚠️ Этот приём уже обработан.", show_alert=True)


# ── Today View Editing callbacks ───────────────────────────────────

@router.callback_query(F.data.startswith("today_edit:"))
async def on_today_edit(callback: CallbackQuery) -> None:
    """Handle clicking on a specific dose in the Today view."""
    if not callback.data:
        return

    from app.services.dose_service import get_dose_by_id
    from app.keyboards import edit_today_dose_kb

    dose_id = int(callback.data.split(":")[1])
    dose = await get_dose_by_id(dose_id)
    
    if not dose:
        await callback.answer("⚠️ Приём не найден.", show_alert=True)
        return

    await callback.answer()
    
    time_part = dose["scheduled_datetime"].split(" ")[1] if " " in dose["scheduled_datetime"] else dose["scheduled_datetime"]
    text = f"💊 Управление приёмом:\n\nЛекарство: {dose['medicine_name']} ({dose['dosage'] or '—'})\nВремя: {time_part}\nСтатус: "
    
    if dose["status"] == "taken":
        text += "✅ Принято"
    elif dose["status"] == "missed":
        text += "❌ Пропущено"
    elif dose["status"] == "skipped":
        text += "❌ Не сегодня"
    else:
        text += "⏳ В ожидании"

    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        reply_markup=edit_today_dose_kb(dose_id, dose["status"])
    )


@router.callback_query(F.data == "today_back")
async def on_today_back(callback: CallbackQuery) -> None:
    """Return to the full Today view from the single dose edit view."""
    from app.handlers.today import _format_today
    if not callback.from_user:
        return

    await callback.answer()
    text, doses = await _format_today(callback.from_user.id)
    
    if callback.message:
        from app.keyboards import today_kb, back_to_main_kb
        reply_markup = today_kb(doses) if doses else back_to_main_kb()
        await callback.message.edit_text(text, reply_markup=reply_markup)  # type: ignore[union-attr]


@router.callback_query(F.data.startswith("today_action_"))
async def on_today_action(callback: CallbackQuery) -> None:
    """Handle taking action on a dose from the Today view editor."""
    if not callback.data:
        return

    from app.services.dose_service import mark_taken, mark_skipped, unmark_dose

    action_parts = callback.data.split(":")
    action_type = action_parts[0]
    dose_id = int(action_parts[1])

    success = False
    if action_type == "today_action_taken":
        tz = pytz.timezone(settings.timezone)
        now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
        success = await mark_taken(dose_id, now_str)
    elif action_type == "today_action_skip":
        success = await mark_skipped(dose_id)
    elif action_type == "today_action_reset":
        success = await unmark_dose(dose_id)

    if success:
        await on_today_back(callback)
    else:
        await callback.answer("⚠️ Не удалось обновить статус приёма.", show_alert=True)
