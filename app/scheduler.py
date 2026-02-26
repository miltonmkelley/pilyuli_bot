"""APScheduler setup: daily dose generation, reminders, auto-miss."""

from __future__ import annotations

import logging
from datetime import datetime

import pytz
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.keyboards import dose_reminder_kb
from app.services.dose_service import (
    generate_daily_doses,
    get_due_reminders,
    mark_reminder_sent,
    process_missed_doses,
)
from app.services.message_service import send_single_message

logger = logging.getLogger(__name__)


async def _generate_daily(tz_name: str) -> None:
    """Job: generate doses for today."""
    try:
        tz = pytz.timezone(tz_name)
        today = datetime.now(tz).strftime("%Y-%m-%d")
        created = await generate_daily_doses(today)
        logger.info("Generated %d doses for %s", created, today)
    except Exception:
        logger.exception("Error generating daily doses")


async def _process_reminders(bot: Bot, tz_name: str) -> None:
    """Job: send due reminders."""
    try:
        tz = pytz.timezone(tz_name)
        now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

        # Mark missed doses FIRST so they don't trigger reminders
        await process_missed_doses(now_str)

        due = await get_due_reminders(now_str)

        for dose in due:
            time_part = dose["scheduled_datetime"].split(" ")[1]
            dosage = f" ({dose['dosage']})" if dose["dosage"] else ""
            count = dose["reminder_count"] + 1
            max_r = dose["max_reminders"]
            count_label = f"  (напоминание {count}/{max_r})" if max_r > 1 else ""
            text = f"💊 Время принять: {dose['medicine_name']}{dosage}\n🕐 {time_part}{count_label}"

            try:
                await send_single_message(
                    bot=bot,
                    chat_id=dose["telegram_id"],
                    text=text,
                    reply_markup=dose_reminder_kb(dose["dose_id"]),
                )
                await mark_reminder_sent(dose["dose_id"], dose["interval_minutes"])
            except Exception:
                logger.exception(
                    "Failed to send reminder for dose %d", dose["dose_id"]
                )
    except Exception:
        logger.exception("Error processing reminders")


async def _process_missed(tz_name: str) -> None:
    """Job: mark overdue doses as missed."""
    try:
        tz = pytz.timezone(tz_name)
        now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
        count = await process_missed_doses(now_str)
        if count:
            logger.info("Marked %d doses as missed", count)
    except Exception:
        logger.exception("Error processing missed doses")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Create and configure the scheduler with all periodic jobs."""
    tz = pytz.timezone(settings.timezone)
    scheduler = AsyncIOScheduler(timezone=tz)

    # Generate daily doses at 00:01
    scheduler.add_job(
        _generate_daily,
        "cron",
        hour=0,
        minute=1,
        args=[settings.timezone],
        id="generate_daily_doses",
        replace_existing=True,
    )

    # Process due reminders every 60 seconds
    scheduler.add_job(
        _process_reminders,
        "interval",
        seconds=60,
        args=[bot, settings.timezone],
        id="process_reminders",
        replace_existing=True,
    )

    # Process missed doses every 60 seconds
    scheduler.add_job(
        _process_missed,
        "interval",
        seconds=60,
        args=[settings.timezone],
        id="process_missed",
        replace_existing=True,
    )

    return scheduler
