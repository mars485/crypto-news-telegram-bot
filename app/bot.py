from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.ai import analyze_news
from app.config import settings
from app.news import fetch_news
from app.scheduler import start_scheduler


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
        news = fetch_news(limit=20)
        digest = analyze_news(news)
    except Exception as exc:
        await update.message.reply_text(
            f"Не удалось подготовить дайджест.\n\nОшибка: {exc}"
        )
        return

    for start in range(0, len(digest), 4000):
        await update.message.reply_text(digest[start:start + 4000])


async def post_init(application: Application) -> None:
    start_scheduler(application)


def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured. "
            "Create .env and add your bot token."
        )

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chatid", chatid))
    application.add_handler(CommandHandler("today", send_digest))

    print("Telegram bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
