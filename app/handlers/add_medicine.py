"""Handler for the /add command — FSM flow to add a medicine."""

from __future__ import annotations

import re
from datetime import datetime

import pytz
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.config import settings
from app.keyboards import main_menu_kb
from app.services.dose_service import generate_daily_doses
from app.services.medicine_service import add_medicine

router = Router()

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class AddMedicine(StatesGroup):
    """FSM states for adding a medicine."""

    name = State()
    dosage = State()
    times = State()


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    """Start the add-medicine flow."""
    await state.set_state(AddMedicine.name)
    await message.answer("💊 Введите название лекарства:")


@router.message(AddMedicine.name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Receive medicine name, ask for dosage."""
    if not message.text or not message.text.strip():
        await message.answer("Название не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(AddMedicine.dosage)
    await message.answer(
        "💉 Введите дозировку (например, «1 таблетка» или «5 мл»):"
    )


@router.message(AddMedicine.dosage)
async def process_dosage(message: Message, state: FSMContext) -> None:
    """Receive dosage, ask for schedule times."""
    dosage = (message.text or "").strip()
    await state.update_data(dosage=dosage)
    await state.set_state(AddMedicine.times)
    await message.answer(
        "🕐 Введите время приёма в формате ЧЧ:ММ.\n"
        "Несколько значений через запятую (например: 08:00, 14:00, 22:00):"
    )


@router.message(AddMedicine.times)
async def process_times(message: Message, state: FSMContext) -> None:
    """Receive schedule times, validate, and save medicine."""
    if not message.text:
        await message.answer("Пожалуйста, введите время:")
        return

    raw_times = [t.strip() for t in message.text.split(",")]
    valid_times: list[str] = []
    invalid: list[str] = []

    for t in raw_times:
        if TIME_RE.match(t):
            valid_times.append(t)
        else:
            invalid.append(t)

    if invalid:
        await message.answer(
            f"❌ Неверный формат времени: {', '.join(invalid)}\n"
            "Используйте формат ЧЧ:ММ (например, 08:00, 14:30):"
        )
        return

    if not valid_times:
        await message.answer("Нужно указать хотя бы одно время:")
        return

    data = await state.get_data()
    if not message.from_user:
        return

    await add_medicine(
        telegram_id=message.from_user.id,
        name=data["name"],
        dosage=data["dosage"],
        times=valid_times,
    )

    # Generate doses for today immediately so /today works right away
    tz = pytz.timezone(settings.timezone)
    today = datetime.now(tz).strftime("%Y-%m-%d")
    await generate_daily_doses(today)

    times_str = ", ".join(valid_times)
    await state.clear()
    await message.answer(
        f"✅ Лекарство «{data['name']}» добавлено!\n"
        f"Дозировка: {data['dosage']}\n"
        f"Время приёма: {times_str}",
        reply_markup=main_menu_kb(),
    )

