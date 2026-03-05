"""Inline and reply keyboards for bot interactions."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def persistent_menu_kb() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard always visible at the bottom of the chat."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Расписание"),
                KeyboardButton(text="📋 Сегодня"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def schedule_menu_kb() -> InlineKeyboardMarkup:
    """Sub-menu for schedule management: add / delete."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💊 Добавить", callback_data="sched:add"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data="sched:delete"),
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ],
        ]
    )


def main_menu_kb() -> InlineKeyboardMarkup:
    """Main menu inline keyboard with quick access buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Расписание", callback_data="menu:schedule"),
                InlineKeyboardButton(text="📋 Сегодня", callback_data="menu:today"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
            ],
        ]
    )


def delete_medicine_kb(medicines: list[dict]) -> InlineKeyboardMarkup:
    """Inline keyboard listing medicines for deletion."""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🗑 {med['name']} ({med['dosage'] or '—'})",
                callback_data=f"delete_med:{med['id']}",
            )
        ]
        for med in medicines
    ]
    buttons.append(
        [
            InlineKeyboardButton(text="↩️ Назад", callback_data="sched:back"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def history_kb() -> InlineKeyboardMarkup:
    """Inline keyboard for history navigation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Вчера", callback_data="history:yesterday"),
                InlineKeyboardButton(text="📅 Неделя", callback_data="history:week"),
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ],
        ]
    )


def dose_reminder_kb(dose_id: int) -> InlineKeyboardMarkup:
    """Create an inline keyboard for a dose reminder.

    Buttons: ✅ Принял / ⏰ Отложить
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принял",
                    callback_data=f"dose_taken:{dose_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Не сегодня",
                    callback_data=f"dose_skip:{dose_id}",
                ),
                InlineKeyboardButton(
                    text="⏰ Отложить",
                    callback_data=f"dose_snooze:{dose_id}",
                ),
            ]
        ]
    )

def back_to_main_kb() -> InlineKeyboardMarkup:
    """Inline keyboard with only the main menu button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ]
        ]
    )
