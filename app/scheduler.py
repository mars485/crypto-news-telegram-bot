"""Daily Telegram digest scheduler."""

import asyncio
import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from app.config import settings


async def daily_digest_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send the daily digest to the configured chat."""
    from app.edition import build_edition
    from app.news import fetch_news
    from app.publishing import publish_edition

    if not settings.telegram_chat_id:
        return

    try:
        news = await asyncio.to_thread(fetch_news, limit=20)
        edition = await asyncio.to_thread(build_edition, news)
        await publish_edition(context.bot, settings.telegram_chat_id, edition)
    except Exception:
        logging.getLogger(__name__).exception("Scheduled edition failed")
        await context.bot.send_message(
            chat_id=settings.telegram_chat_id,
            text="Не удалось подготовить ежедневный дайджест. Подробности в журнале сервера.",
        )


def start_scheduler(application: Application) -> None:
    """Schedule the digest every day at 08:00 in the configured timezone."""
    if not settings.telegram_chat_id:
        print("Daily scheduler is disabled: TELEGRAM_CHAT_ID is not configured.")
        return

    if application.job_queue is None:
        raise RuntimeError(
            "JobQueue is unavailable. Install python-telegram-bot with the "
            "job-queue extra."
        )

    tz = ZoneInfo(settings.timezone)
    application.job_queue.run_daily(
        daily_digest_job,
        time=time(hour=8, minute=0, tzinfo=tz),
        name="daily-crypto-news-digest",
    )
    print(f"Daily digest scheduled for 08:00 ({settings.timezone}).")
