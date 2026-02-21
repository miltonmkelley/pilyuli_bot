"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    bot_token: str
    timezone: str

    @classmethod
    def from_env(cls) -> Settings:
        """Create settings from environment variables.

        Raises:
            ValueError: If BOT_TOKEN is missing.
        """
        bot_token = os.getenv("BOT_TOKEN", "")
        if not bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")

        timezone = os.getenv("TIMEZONE", "Europe/Moscow")
        return cls(bot_token=bot_token, timezone=timezone)


settings = Settings.from_env()
