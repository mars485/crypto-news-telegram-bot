from app.config import settings

def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    print("Telegram bot configuration loaded.")

if __name__ == "__main__":
    main()
