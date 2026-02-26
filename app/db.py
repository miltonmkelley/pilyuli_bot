"""Database initialization and connection helper for SQLite."""

from __future__ import annotations

import os

import aiosqlite

DB_PATH = os.getenv("DB_PATH", "pill_bot.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    last_message_id INTEGER
);

CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    dosage TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

CREATE TABLE IF NOT EXISTS doses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    schedule_id INTEGER,
    scheduled_datetime TEXT NOT NULL,
    status TEXT NOT NULL,
    taken_at TEXT,
    reminder_sent INTEGER DEFAULT 0,
    reminder_count INTEGER DEFAULT 0,
    next_reminder_at TEXT,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id),
    FOREIGN KEY (schedule_id) REFERENCES schedules(id)
);

CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    max_reminders INTEGER NOT NULL DEFAULT 3,
    reminder_interval_minutes INTEGER NOT NULL DEFAULT 5,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


async def init_db(db_path: str = DB_PATH) -> None:
    """Create tables if they don't exist."""
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        
        # Миграция: добавляем last_message_id, если его нет
        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_message_id INTEGER")
        except aiosqlite.OperationalError:
            # Колонка уже существует
            pass
            
        await db.commit()


async def get_db(db_path: str = DB_PATH) -> aiosqlite.Connection:
    """Open a database connection.

    Caller is responsible for closing it (or use as async context manager).
    """
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def get_last_message_id(telegram_id: int, db_path: str = DB_PATH) -> int | None:
    """Get the ID of the last message sent to the user by the bot."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT last_message_id FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0] is not None:
                return int(row[0])
            return None


async def set_last_message_id(telegram_id: int, message_id: int, db_path: str = DB_PATH) -> None:
    """Save the ID of the last message sent to the user by the bot."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE users SET last_message_id = ? WHERE telegram_id = ?",
            (message_id, telegram_id),
        )
        await db.commit()

