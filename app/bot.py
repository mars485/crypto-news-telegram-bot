from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я бот мировых новостей и их влияния на крипторынок.\n"
        "Команда /today будет добавлена на следующем этапе."
    )


def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured. "
            "Create .env and add your bot token."
        )

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))

    print("Telegram bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
