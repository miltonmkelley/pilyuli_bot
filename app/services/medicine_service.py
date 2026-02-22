"""Service layer for medicine and schedule management."""

from __future__ import annotations

from datetime import datetime, timezone

from app.db import get_db


async def ensure_user(telegram_id: int) -> int:
    """Register user if not exists. Return internal user id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]

        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute(
            "INSERT INTO users (telegram_id, created_at) VALUES (?, ?)",
            (telegram_id, now),
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore[return-value]
    finally:
        await db.close()


async def add_medicine(
    telegram_id: int,
    name: str,
    dosage: str,
    times: list[str],
) -> int:
    """Add a medicine with schedule times. Return medicine id."""
    user_id = await ensure_user(telegram_id)

    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute(
            "INSERT INTO medicines (user_id, name, dosage, created_at) VALUES (?, ?, ?, ?)",
            (user_id, name, dosage, now),
        )
        medicine_id: int = cursor.lastrowid  # type: ignore[assignment]

        for t in times:
            await db.execute(
                "INSERT INTO schedules (medicine_id, time) VALUES (?, ?)",
                (medicine_id, t),
            )

        await db.commit()
        return medicine_id
    finally:
        await db.close()


async def get_user_medicines(telegram_id: int) -> list[dict]:
    """Get all medicines for a user with their schedules."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT m.id, m.name, m.dosage
            FROM medicines m
            JOIN users u ON m.user_id = u.id
            WHERE u.telegram_id = ?
            ORDER BY m.name
            """,
            (telegram_id,),
        )
        medicines = []
        for row in await cursor.fetchall():
            med = {"id": row[0], "name": row[1], "dosage": row[2]}
            sch_cursor = await db.execute(
                "SELECT time FROM schedules WHERE medicine_id = ? ORDER BY time",
                (med["id"],),
            )
            med["times"] = [r[0] for r in await sch_cursor.fetchall()]
            medicines.append(med)
        return medicines
    finally:
        await db.close()


async def delete_medicine(medicine_id: int) -> bool:
    """Delete a medicine, its schedules, and future (scheduled) doses.

    Returns True if the medicine was found and deleted.
    """
    db = await get_db()
    try:
        # Check medicine exists
        cursor = await db.execute(
            "SELECT id FROM medicines WHERE id = ?", (medicine_id,)
        )
        if not await cursor.fetchone():
            return False

        # Delete future doses (keep taken/missed for history)
        await db.execute(
            "DELETE FROM doses WHERE medicine_id = ? AND status = 'scheduled'",
            (medicine_id,),
        )
        # Delete schedules
        await db.execute(
            "DELETE FROM schedules WHERE medicine_id = ?", (medicine_id,)
        )
        # Delete medicine
        await db.execute(
            "DELETE FROM medicines WHERE id = ?", (medicine_id,)
        )
        await db.commit()
        return True
    finally:
        await db.close()
