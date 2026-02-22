"""Handler for the /today command — display today's dose status."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytz
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.keyboards import history_kb
from app.services.dose_service import get_dose_history, get_today_doses

router = Router()

STATUS_ICONS = {"taken": "✅", "missed": "❌", "scheduled": "⏳"}


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


async def format_history(telegram_id: int, period: str) -> str:
    """Build history text for yesterday or last week."""
    tz = pytz.timezone(settings.timezone)
    now = datetime.now(tz)

    if period == "yesterday":
        day = now - timedelta(days=1)
        start = end = day.strftime("%Y-%m-%d")
        title = f"📅 Вчера ({start}):"
    else:  # week
        end_date = now - timedelta(days=1)
        start_date = now - timedelta(days=7)
        start = start_date.strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d")
        title = f"📅 За неделю ({start} — {end}):"

    doses = await get_dose_history(telegram_id, start, end)

    if not doses:
        return f"{title}\n\nНет записей за этот период."

    # Group by date
    by_date: dict[str, list[dict]] = {}
    for d in doses:
        date_part = d["scheduled_datetime"].split(" ")[0]
        by_date.setdefault(date_part, []).append(d)

    lines = [title, ""]
    for date_str in sorted(by_date.keys(), reverse=True):
        lines.append(f"📆 {date_str}")
        for d in sorted(by_date[date_str], key=lambda x: x["scheduled_datetime"]):
            time_part = d["scheduled_datetime"].split(" ")[1] if " " in d["scheduled_datetime"] else ""
            icon = STATUS_ICONS.get(d["status"], "⏳")
            suffix = ""
            if d["status"] == "taken" and d.get("taken_at"):
                taken_time = d["taken_at"].split(" ")[1] if " " in d["taken_at"] else d["taken_at"]
                suffix = f" (в {taken_time})"
            elif d["status"] == "missed":
                suffix = " (пропущено)"
            lines.append(f"  {icon} {d['medicine_name']} — {time_part}{suffix}")
        lines.append("")

    return "\n".join(lines).strip()


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    """Show today's doses for the user."""
    if not message.from_user:
        return

    text = await _format_today(message.from_user.id)
    await message.answer(text, reply_markup=history_kb())
