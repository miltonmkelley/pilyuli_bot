"""Application entrypoint: init DB, start scheduler, run bot polling."""

from __future__ import annotations

import asyncio
import logging

from app.bot import create_bot, create_dispatcher
from app.db import init_db
from app.scheduler import setup_scheduler
from app.services.dose_service import generate_daily_doses

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Initialize all components and start the bot."""
    logger.info("Initializing database...")
    await init_db()

    bot = create_bot()
    dp = create_dispatcher()

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    # Generate doses for today on startup (in case bot was down at 00:01)
    from datetime import datetime

    import pytz

    from app.config import settings

    tz = pytz.timezone(settings.timezone)
    today = datetime.now(tz).strftime("%Y-%m-%d")
    created = await generate_daily_doses(today)
    if created:
        logger.info("Generated %d doses for today on startup", created)

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
