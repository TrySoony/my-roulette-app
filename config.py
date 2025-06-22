"""
Конфигурация для Telegram-бота рулетки подарков
"""
import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Основные настройки
    bot_token: str
    admin_id: int
    max_attempts: int = 2
    debug: bool = False
    
    # Настройки сервера
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 8000))
    
    # URL для вебхука
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Пути к файлам
    user_data_file: str = "user_data.json"
    
    # Настройки безопасности
    allowed_hosts: list = ["*"]
    cors_origins: list = ["*"]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

# Создаем глобальный экземпляр настроек
config = Settings()

# Проверяем обязательные настройки
if not config.bot_token:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения")

if not config.admin_id:
    raise ValueError("ADMIN_ID не установлен в переменных окружения") 