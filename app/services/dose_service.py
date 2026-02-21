"""Service layer for dose management: generation, reminders, state transitions."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.db import get_db


async def generate_daily_doses(date_str: str) -> int:
    """Generate dose entries for a given date (YYYY-MM-DD).

    Creates one dose per schedule entry, skips if already exists.
    Returns the number of doses created.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, medicine_id, time FROM schedules"
        )
        schedules = await cursor.fetchall()

        created = 0
        for sch in schedules:
            schedule_id = sch[0]
            medicine_id = sch[1]
            time_str = sch[2]
            scheduled_dt = f"{date_str} {time_str}"

            # Check for duplicate
            dup = await db.execute(
                """
                SELECT id FROM doses
                WHERE medicine_id = ? AND scheduled_datetime = ?
                """,
                (medicine_id, scheduled_dt),
            )
            if await dup.fetchone():
                continue

            await db.execute(
                """
                INSERT INTO doses (medicine_id, scheduled_datetime, status, reminder_sent, reminder_count, next_reminder_at)
                VALUES (?, ?, 'scheduled', 0, 0, ?)
                """,
                (medicine_id, scheduled_dt, scheduled_dt),
            )
            created += 1

        await db.commit()
        return created
    finally:
        await db.close()


async def get_due_reminders(now_str: str) -> list[dict[str, Any]]:
    """Find doses that are due for a reminder.

    Uses next_reminder_at to determine when to send the next reminder.
    Respects per-user max_reminders setting.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT d.id, d.medicine_id, d.scheduled_datetime,
                   m.name, m.dosage, u.telegram_id,
                   d.reminder_count,
                   COALESCE(us.max_reminders, 3) as max_reminders,
                   COALESCE(us.reminder_interval_minutes, 5) as interval_min
            FROM doses d
            JOIN medicines m ON d.medicine_id = m.id
            JOIN users u ON m.user_id = u.id
            LEFT JOIN user_settings us ON us.user_id = u.id
            WHERE d.status = 'scheduled'
              AND COALESCE(d.next_reminder_at, d.scheduled_datetime) <= ?
              AND d.reminder_count < COALESCE(us.max_reminders, 3)
            """,
            (now_str,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "dose_id": r[0],
                "medicine_id": r[1],
                "scheduled_datetime": r[2],
                "medicine_name": r[3],
                "dosage": r[4],
                "telegram_id": r[5],
                "reminder_count": r[6],
                "max_reminders": r[7],
                "interval_minutes": r[8],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def mark_reminder_sent(dose_id: int, interval_minutes: int) -> None:
    """Increment reminder_count and schedule next reminder."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT next_reminder_at, scheduled_datetime FROM doses WHERE id = ?",
            (dose_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return

        current_time = row[0] or row[1]
        current_dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M")
        next_dt = current_dt + timedelta(minutes=interval_minutes)
        next_str = next_dt.strftime("%Y-%m-%d %H:%M")

        await db.execute(
            """
            UPDATE doses
            SET reminder_count = reminder_count + 1,
                next_reminder_at = ?
            WHERE id = ?
            """,
            (next_str, dose_id),
        )
        await db.commit()
    finally:
        await db.close()


async def mark_taken(dose_id: int, taken_at: str) -> bool:
    """Mark a dose as taken. Returns False if state transition is forbidden."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT status FROM doses WHERE id = ?", (dose_id,)
        )
        row = await cursor.fetchone()
        if not row or row[0] != "scheduled":
            return False

        await db.execute(
            "UPDATE doses SET status = 'taken', taken_at = ? WHERE id = ?",
            (taken_at, dose_id),
        )
        await db.commit()
        return True
    finally:
        await db.close()


async def snooze(dose_id: int) -> bool:
    """Snooze a dose by 10 minutes. Returns False if state transition is forbidden."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT status, scheduled_datetime FROM doses WHERE id = ?",
            (dose_id,),
        )
        row = await cursor.fetchone()
        if not row or row[0] != "scheduled":
            return False

        old_dt = datetime.strptime(row[1], "%Y-%m-%d %H:%M")
        new_dt = old_dt + timedelta(minutes=10)
        new_dt_str = new_dt.strftime("%Y-%m-%d %H:%M")

        await db.execute(
            """
            UPDATE doses
            SET scheduled_datetime = ?, reminder_sent = 0,
                reminder_count = 0, next_reminder_at = ?
            WHERE id = ?
            """,
            (new_dt_str, new_dt_str, dose_id),
        )
        await db.commit()
        return True
    finally:
        await db.close()


async def process_missed_doses(now_str: str) -> int:
    """Mark doses as missed if 2 hours have passed since scheduled time.

    Returns the number of doses marked as missed.
    """
    now = datetime.strptime(now_str, "%Y-%m-%d %H:%M")
    cutoff = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

    db = await get_db()
    try:
        cursor = await db.execute(
            """
            UPDATE doses
            SET status = 'missed'
            WHERE status = 'scheduled'
              AND scheduled_datetime <= ?
            """,
            (cutoff,),
        )
        await db.commit()
        return cursor.rowcount
    finally:
        await db.close()


async def get_today_doses(telegram_id: int, date_str: str) -> list[dict[str, Any]]:
    """Get all doses for a user on a given date, sorted by scheduled time."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT d.id, m.name, m.dosage, d.scheduled_datetime,
                   d.status, d.taken_at
            FROM doses d
            JOIN medicines m ON d.medicine_id = m.id
            JOIN users u ON m.user_id = u.id
            WHERE u.telegram_id = ?
              AND d.scheduled_datetime LIKE ?
            ORDER BY d.scheduled_datetime
            """,
            (telegram_id, f"{date_str}%"),
        )
        rows = await cursor.fetchall()
        return [
            {
                "dose_id": r[0],
                "medicine_name": r[1],
                "dosage": r[2],
                "scheduled_datetime": r[3],
                "status": r[4],
                "taken_at": r[5],
            }
            for r in rows
        ]
    finally:
        await db.close()
