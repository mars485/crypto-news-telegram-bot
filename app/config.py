from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    telegram_chat_id: int = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
    timezone: str = os.getenv("TIMEZONE", "Europe/Amsterdam")


settings = Settings()
