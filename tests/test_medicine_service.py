"""Tests for medicine_service — user registration, add medicine, retrieval."""

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


@pytest.mark.asyncio
async def test_ensure_user_creates_new():
    await _reset_db()
    from app.services.medicine_service import ensure_user

    user_id = await ensure_user(99999)
    assert isinstance(user_id, int)

    user_id2 = await ensure_user(99999)
    assert user_id2 == user_id


@pytest.mark.asyncio
async def test_add_medicine_with_schedules():
    await _reset_db()
    from app.services.medicine_service import add_medicine, get_user_medicines

    med_id = await add_medicine(
        telegram_id=99999,
        name="Aspirin",
        dosage="500mg",
        times=["08:00", "20:00"],
    )
    assert isinstance(med_id, int)

    medicines = await get_user_medicines(99999)
    assert len(medicines) == 1
    assert medicines[0]["name"] == "Aspirin"
    assert medicines[0]["dosage"] == "500mg"
    assert medicines[0]["times"] == ["08:00", "20:00"]


@pytest.mark.asyncio
async def test_multiple_medicines():
    await _reset_db()
    from app.services.medicine_service import add_medicine, get_user_medicines

    await add_medicine(99999, "Med A", "1 tab", ["08:00"])
    await add_medicine(99999, "Med B", "2 tab", ["09:00", "21:00"])

    medicines = await get_user_medicines(99999)
    assert len(medicines) == 2
    names = {m["name"] for m in medicines}
    assert names == {"Med A", "Med B"}


@pytest.mark.asyncio
async def test_delete_medicine():
    await _reset_db()
    from app.services.dose_service import generate_daily_doses
    from app.services.medicine_service import (
        add_medicine,
        delete_medicine,
        get_user_medicines,
    )

    med_id = await add_medicine(99999, "ToDelete", "1 tab", ["10:00"])
    await generate_daily_doses("2025-06-15")

    # Verify medicine and doses exist
    medicines = await get_user_medicines(99999)
    assert len(medicines) == 1

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT COUNT(*) FROM doses WHERE medicine_id = ?", (med_id,)
        )
        assert (await cur.fetchone())[0] == 1
    finally:
        await db.close()

    # Delete medicine
    result = await delete_medicine(med_id)
    assert result is True

    # Verify everything is gone
    medicines = await get_user_medicines(99999)
    assert len(medicines) == 0

    db = await get_db()
    try:
        cur = await db.execute(
            "SELECT COUNT(*) FROM doses WHERE medicine_id = ?", (med_id,)
        )
        assert (await cur.fetchone())[0] == 0
        cur = await db.execute(
            "SELECT COUNT(*) FROM schedules WHERE medicine_id = ?", (med_id,)
        )
        assert (await cur.fetchone())[0] == 0
    finally:
        await db.close()

    # Delete non-existent returns False
    result = await delete_medicine(99999)
    assert result is False
