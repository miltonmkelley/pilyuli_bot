"""Handler for the /today command — display today's dose status."""

from __future__ import annotations

from datetime import datetime

import pytz
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.keyboards import main_menu_kb
from app.services.dose_service import get_today_doses

router = Router()


def _format_dose(dose: dict) -> str:
    """Format a single dose line for display."""
    status = dose["status"]
    name = dose["medicine_name"]
    dt = dose["scheduled_datetime"]

    # Extract time HH:MM from scheduled_datetime
    time_part = dt.split(" ")[1] if " " in dt else dt

    if status == "taken":
        taken_at = dose.get("taken_at", "")
        taken_time = ""
        if taken_at and " " in taken_at:
            taken_time = taken_at.split(" ")[1]
        elif taken_at:
            taken_time = taken_at
        return f"✅ {name} — {time_part} (принято в {taken_time})"
    elif status == "missed":
        return f"❌ {name} — {time_part} (пропущено)"
    else:  # scheduled
        return f"⏳ {name} — {time_part} (ожидается)"


async def _format_today(telegram_id: int) -> str:
    """Build the today's schedule text for a user. Reusable by callbacks."""
    tz = pytz.timezone(settings.timezone)
    today = datetime.now(tz).strftime("%Y-%m-%d")
    doses = await get_today_doses(telegram_id, today)

    if not doses:
        return (
            "📅 На сегодня нет запланированных приёмов.\n"
            "Добавьте лекарство командой /add"
        )

    lines = [_format_dose(d) for d in doses]
    return "📅 Сегодня:\n\n" + "\n".join(lines)


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    """Show today's doses for the user."""
    if not message.from_user:
        return

    text = await _format_today(message.from_user.id)
    await message.answer(text, reply_markup=main_menu_kb())
