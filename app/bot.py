"""Telegram command handlers and bot startup."""

import asyncio
import logging
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
)

from app.edition import build_edition
from app.publishing import publish_edition
from app.config import settings
from app.news import fetch_news
from app.scheduler import start_scheduler

logger = logging.getLogger(__name__)


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📰 Получить дайджест", callback_data="digest")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
    ])


def count_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1️⃣ 1 новость", callback_data="digest:1"),
            InlineKeyboardButton("5️⃣ 5 новостей", callback_data="digest:5"),
            InlineKeyboardButton("🔟 10 новостей", callback_data="digest:10"),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu")],
    ])


HELP_TEXT = (
    "Доступные действия:\n"
    "📰 Получить дайджест — выбор 1, 5 или 10 новостей с AI-анализом.\n"
    "ℹ️ Помощь — это меню.\n\n"
    "Команды: /start, /menu, /today, /chatid."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "Привет! 👋\n\nЯ бот мировых новостей и их влияния на крипторынок.\n"
        "Выбери действие:",
        reply_markup=main_menu(),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None:
        await update.message.reply_text("Главное меню:", reply_markup=main_menu())


async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None or update.message is None:
        return
    await update.message.reply_text(
        f"ID этого чата: {update.effective_chat.id}\n\n"
        "Добавь это значение в TELEGRAM_CHAT_ID в файле .env.",
        reply_markup=main_menu(),
    )


async def send_digest(update: Update, context: ContextTypes.DEFAULT_TYPE, count: int = 5) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    # Prevent overlapping paid OpenAI requests from repeated button presses.
    active = context.application.bot_data.setdefault("active_digests", set())
    if chat_id in active:
        await context.bot.send_message(chat_id, "Дайджест уже готовится. Подожди завершения.")
        return
    active.add(chat_id)
    try:
        await context.bot.send_message(chat_id, "Собираю новости и готовлю AI-анализ... 🤖📰")
        started = time.monotonic()
        news = await asyncio.to_thread(fetch_news, limit=20)
        logger.info("Digest RSS stage: %.1fs, %d articles", time.monotonic() - started, len(news))
        started = time.monotonic()
        edition = await asyncio.to_thread(build_edition, news, count)
        logger.info("Edition AI stage: %.1fs", time.monotonic() - started)
        await publish_edition(context.bot, chat_id, edition)
        await context.bot.send_message(chat_id, "Готово. Выбери действие:", reply_markup=main_menu())
    except Exception:
        logger.exception("Digest generation or delivery failed")
        await context.bot.send_message(
            chat_id,
            "Не удалось подготовить или отправить дайджест. Подробности в журнале сервера.",
            reply_markup=main_menu(),
        )
    finally:
        active.discard(chat_id)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    if query.data == "digest" and update.effective_chat is not None:
        await context.bot.send_message(
            update.effective_chat.id, "📰 <b>Сколько новостей подготовить?</b>",
            parse_mode="HTML", reply_markup=count_menu(),
        )
    elif query.data in ("digest:1", "digest:5", "digest:10"):
        await send_digest(update, context, int(query.data.split(":")[1]))
    elif query.data == "menu" and update.effective_chat is not None:
        await context.bot.send_message(
            update.effective_chat.id, "Главное меню:", reply_markup=main_menu(),
        )
    elif query.data == "help" and update.effective_chat is not None:
        await context.bot.send_message(
            update.effective_chat.id, HELP_TEXT, reply_markup=main_menu()
        )


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
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("chatid", chatid))
    application.add_handler(CommandHandler("today", send_digest))
    application.add_handler(CallbackQueryHandler(handle_button))
    logger.info("Telegram bot is running")
    application.run_polling()


if __name__ == "__main__":
    main()
