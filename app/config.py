from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    timezone: str = os.getenv("TIMEZONE", "Europe/Amsterdam")

settings = Settings()
