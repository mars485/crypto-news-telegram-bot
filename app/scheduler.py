"""Daily Telegram digest scheduler."""

from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from app.config import settings


async def daily_digest_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send the daily digest to the configured chat."""
    from app.ai import analyze_news
    from app.news import fetch_news

    if not settings.telegram_chat_id:
        return

    try:
        news = fetch_news(limit=20)
        digest = analyze_news(news)
        if not digest:
            digest = "За последние сутки подходящих новостей не найдено."

        for start in range(0, len(digest), 4000):
            await context.bot.send_message(
                chat_id=settings.telegram_chat_id,
                text=digest[start:start + 4000],
            )
    except Exception as exc:
        await context.bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=f"Не удалось подготовить ежедневный дайджест.\n\nОшибка: {exc}",
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
