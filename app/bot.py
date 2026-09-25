"""Telegram command handlers and bot startup."""

import asyncio
import logging
import time

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.ai import analyze_news
from app.config import settings
from app.news import fetch_news
from app.scheduler import start_scheduler

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я бот мировых новостей и их влияния на крипторынок.\n"
        "Используй /today для AI-дайджеста.\n"
        "Используй /chatid, чтобы узнать ID этого чата."
    )

async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None or update.message is None:
        return
    await update.message.reply_text(
        f"ID этого чата: {update.effective_chat.id}\n\n"
        "Добавь это значение в TELEGRAM_CHAT_ID в файле .env."
    )

async def send_digest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text("Собираю новости и готовлю AI-анализ... 🤖📰")
    try:
        started = time.monotonic()
        news = await asyncio.to_thread(fetch_news, limit=20)
        logger.info("Digest RSS stage: %.1fs, %d articles", time.monotonic() - started, len(news))
        started = time.monotonic()
        digest = await asyncio.to_thread(analyze_news, news)
        logger.info("Digest AI stage: %.1fs", time.monotonic() - started)
    except Exception:
        logger.exception("Digest generation failed")
        await update.message.reply_text(
            "Не удалось подготовить дайджест. Подробности доступны в журнале сервера."
        )
        return

    for offset in range(0, len(digest), 4000):
        await update.message.reply_text(digest[offset:offset + 4000])

async def post_init(application: Application) -> None:
    start_scheduler(application)

def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured. Create .env and add your bot token.")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chatid", chatid))
    application.add_handler(CommandHandler("today", send_digest))
    logger.info("Telegram bot is running")
    application.run_polling()

if __name__ == "__main__":
    main()
