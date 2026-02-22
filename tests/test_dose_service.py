"""Tests for dose_service — generation, state transitions, missed logic."""

from __future__ import annotations

import pytest

import app.db as db_module
from app.db import get_db


async def _reset_db() -> None:
    """Drop all tables and recreate the schema."""
    db = await get_db()
    try:
        await db.execute("DROP TABLE IF EXISTS user_settings")
        await db.execute("DROP TABLE IF EXISTS doses")
        await db.execute("DROP TABLE IF EXISTS schedules")
        await db.execute("DROP TABLE IF EXISTS medicines")
        await db.execute("DROP TABLE IF EXISTS users")
        await db.executescript(db_module.SCHEMA)
        await db.commit()
    finally:
        await db.close()


async def _seed_data() -> None:
    """Reset DB, then seed test data."""
    await _reset_db()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO users (telegram_id, created_at) VALUES (?, ?)",
            (12345, "2025-01-01T00:00:00"),
        )
        await db.execute(
            "INSERT INTO medicines (user_id, name, dosage, created_at) VALUES (?, ?, ?, ?)",
            (1, "TestMed", "1 tab", "2025-01-01T00:00:00"),
        )
        await db.execute(
            "INSERT INTO schedules (medicine_id, time) VALUES (?, ?)",
            (1, "08:00"),
        )
        await db.execute(
            "INSERT INTO schedules (medicine_id, time) VALUES (?, ?)",
            (1, "20:00"),
        )
        await db.commit()
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_generate_daily_doses():
    await _seed_data()
    from app.services.dose_service import generate_daily_doses

    created = await generate_daily_doses("2025-06-15")
    assert created == 2

    created2 = await generate_daily_doses("2025-06-15")
    assert created2 == 0


@pytest.mark.asyncio
async def test_mark_taken():
    await _seed_data()
    from app.services.dose_service import generate_daily_doses, mark_taken

    await generate_daily_doses("2025-06-15")

    success = await mark_taken(1, "2025-06-15 08:03")
    assert success is True

    success2 = await mark_taken(1, "2025-06-15 08:05")
    assert success2 is False


@pytest.mark.asyncio
async def test_snooze():
    await _seed_data()
    from app.services.dose_service import generate_daily_doses, snooze

    await generate_daily_doses("2025-06-15")

    success = await snooze(1)
    assert success is True

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT scheduled_datetime, reminder_sent FROM doses WHERE id = 1"
        )
        row = await cursor.fetchone()
        assert row[0] == "2025-06-15 08:10"
        assert row[1] == 0
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_process_missed():
    await _seed_data()
    from app.services.dose_service import generate_daily_doses, process_missed_doses

    await generate_daily_doses("2025-06-15")

    count = await process_missed_doses("2025-06-15 09:59")
    assert count == 0

    count = await process_missed_doses("2025-06-15 10:01")
    assert count == 1


@pytest.mark.asyncio
async def test_forbidden_transition_missed_to_taken():
    await _seed_data()
    from app.services.dose_service import (
        generate_daily_doses,
        mark_taken,
        process_missed_doses,
    )

    await generate_daily_doses("2025-06-15")
    await process_missed_doses("2025-06-15 10:01")

    success = await mark_taken(1, "2025-06-15 10:05")
    assert success is False


@pytest.mark.asyncio
async def test_get_due_reminders():
    await _seed_data()
    from app.services.dose_service import generate_daily_doses, get_due_reminders

    await generate_daily_doses("2025-06-15")

    due = await get_due_reminders("2025-06-15 07:59")
    assert len(due) == 0

    due = await get_due_reminders("2025-06-15 08:00")
    assert len(due) == 1
    assert due[0]["medicine_name"] == "TestMed"
    assert due[0]["telegram_id"] == 12345


@pytest.mark.asyncio
async def test_get_today_doses():
    await _seed_data()
    from app.services.dose_service import generate_daily_doses, get_today_doses

    await generate_daily_doses("2025-06-15")

    doses = await get_today_doses(12345, "2025-06-15")
    assert len(doses) == 2
    assert doses[0]["scheduled_datetime"] == "2025-06-15 08:00"
    assert doses[1]["scheduled_datetime"] == "2025-06-15 20:00"
