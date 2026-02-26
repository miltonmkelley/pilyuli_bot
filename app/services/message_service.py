"""Centralized message sending service to maintain a single active bot message."""

from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, Message, ReplyKeyboardMarkup

from app.db import get_last_message_id, set_last_message_id

logger = logging.getLogger(__name__)


async def send_single_message(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    **kwargs: Any,
) -> Message:
    """
    Send a message to a user, replacing the previous one if it exists.
    This maintains the 'single message' interface in the chat.
    """
    # 1. Get the last known message ID
    last_message_id = await get_last_message_id(chat_id)

    # 2. Try to delete it (so the new message appears at the bottom with standard notification)
    if last_message_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
        except Exception as e:
            # Message might be already deleted or too old to delete
            logger.debug("Could not delete old message %s: %s", last_message_id, e)

    # 3. Send the new message
    new_message = await bot.send_message(
        chat_id=chat_id, text=text, reply_markup=reply_markup, **kwargs
    )

    # 4. Save the new message ID
    await set_last_message_id(chat_id, new_message.message_id)

    return new_message
