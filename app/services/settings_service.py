"""Service layer for user notification settings."""

from __future__ import annotations

from app.db import get_db

# Defaults
DEFAULT_MAX_REMINDERS = 3
DEFAULT_REMINDER_INTERVAL = 5  # minutes


async def get_user_settings(user_id: int) -> dict:
    """Get notification settings for a user (by internal user_id).

    Returns defaults if no custom settings exist.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT max_reminders, reminder_interval_minutes FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row:
            return {
                "max_reminders": row[0],
                "reminder_interval_minutes": row[1],
            }
        return {
            "max_reminders": DEFAULT_MAX_REMINDERS,
            "reminder_interval_minutes": DEFAULT_REMINDER_INTERVAL,
        }
    finally:
        await db.close()


async def get_settings_by_telegram_id(telegram_id: int) -> dict:
    """Get notification settings for a user by telegram_id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT us.max_reminders, us.reminder_interval_minutes
            FROM user_settings us
            JOIN users u ON us.user_id = u.id
            WHERE u.telegram_id = ?
            """,
            (telegram_id,),
        )
        row = await cursor.fetchone()
        if row:
            return {
                "max_reminders": row[0],
                "reminder_interval_minutes": row[1],
            }
        return {
            "max_reminders": DEFAULT_MAX_REMINDERS,
            "reminder_interval_minutes": DEFAULT_REMINDER_INTERVAL,
        }
    finally:
        await db.close()


async def update_settings(
    telegram_id: int,
    max_reminders: int,
    reminder_interval_minutes: int,
) -> None:
    """Update (or create) notification settings for a user."""
    db = await get_db()
    try:
        # Get internal user_id
        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return
        user_id = row[0]

        await db.execute(
            """
            INSERT INTO user_settings (user_id, max_reminders, reminder_interval_minutes)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                max_reminders = excluded.max_reminders,
                reminder_interval_minutes = excluded.reminder_interval_minutes
            """,
            (user_id, max_reminders, reminder_interval_minutes),
        )
        await db.commit()
    finally:
        await db.close()
