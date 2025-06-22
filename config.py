"""
Конфигурация для Telegram-бота рулетки подарков
"""
import os
import re
from typing import Optional
from dataclasses import dataclass

@dataclass
class Config:
    """Конфигурация бота"""
    bot_token: str
    admin_id: int
    webapp_url: str
    max_attempts: int = 2
    debug: bool = False

    @staticmethod
    def from_env():
        """Создает конфигурацию из переменных окружения"""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")

        admin_id = os.getenv("ADMIN_ID")
        if not admin_id:
            raise ValueError("ADMIN_ID environment variable is required")
        admin_id = int(admin_id)

        webapp_url = os.getenv("WEBAPP_URL", "https://my-roulette-app-4.onrender.com")
        if not webapp_url.startswith("https://"):
            raise ValueError("WEBAPP_URL must start with https://")

        max_attempts = int(os.getenv("MAX_ATTEMPTS", "2"))
        debug = os.getenv("DEBUG", "false").lower() == "true"

        return Config(
            bot_token=bot_token,
            admin_id=admin_id,
            webapp_url=webapp_url,
            max_attempts=max_attempts,
            debug=debug
        )

# Создаем конфигурацию из переменных окружения
config = Config.from_env() 