"""Daily Telegram digest scheduler."""

from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from app.config import settings


async def daily_digest_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send the daily digest to the configured chat."""
    from app.ai import analyze_news, telegram_digest_parts
    from app.news import fetch_news

    if not settings.telegram_chat_id:
        return

    try:
        news = fetch_news(limit=20)
        image_item = next((item for item in news if item.image_url), None)
        if image_item:
            try:
                await context.bot.send_photo(
                    chat_id=settings.telegram_chat_id,
                    photo=image_item.image_url,
                    caption="🌍 📰 <b>МИРОВЫЕ НОВОСТИ • CRYPTO</b> 📈 🚀",
                    parse_mode="HTML",
                )
            except Exception:
                import logging
                logging.getLogger(__name__).warning("RSS illustration could not be sent", exc_info=True)
        digest = analyze_news(news)
        if not digest:
            digest = "За последние сутки подходящих новостей не найдено."

        for text, parse_mode in telegram_digest_parts(digest):
            await context.bot.send_message(
                chat_id=settings.telegram_chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
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
