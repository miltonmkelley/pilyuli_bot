"""Inline keyboards for bot interactions."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    """Main menu inline keyboard with quick access buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💊 Добавить", callback_data="menu:add"),
                InlineKeyboardButton(text="📋 Сегодня", callback_data="menu:today"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
            ],
        ]
    )


def dose_reminder_kb(dose_id: int) -> InlineKeyboardMarkup:
    """Create an inline keyboard for a dose reminder.

    Buttons: ✅ Принял / ⏰ Отложить (10 мин)
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принял",
                    callback_data=f"dose_taken:{dose_id}",
                ),
                InlineKeyboardButton(
                    text="⏰ Отложить",
                    callback_data=f"dose_snooze:{dose_id}",
                ),
            ]
        ]
    )

