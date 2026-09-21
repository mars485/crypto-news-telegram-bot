from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.news import fetch_news


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я бот мировых новостей и их влияния на крипторынок.\n"
        "Используй /today, чтобы получить последние новости."
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    await update.message.reply_text("Собираю последние новости... 📰")

    news = fetch_news(limit=10)

    if not news:
        await update.message.reply_text(
            "Не удалось получить новости. Попробуй ещё раз позже."
        )
        return

    lines = ["📰 Последние новости\n"]

    for index, item in enumerate(news, start=1):
        lines.append(
            f"{index}. {item.title}\n"
            f"Источник: {item.source}\n"
            f"{item.url}\n"
        )

    message = "\n".join(lines)

    # Telegram has a message limit of about 4096 characters.
    await update.message.reply_text(message[:4000])


def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured. "
            "Create .env and add your bot token."
        )

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today))

    print("Telegram bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
