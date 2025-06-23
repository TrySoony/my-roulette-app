from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Настройки сервера
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Настройки базы данных
    database_url: str
    
    # Настройки CORS
    cors_origins: List[str] = ["*"]
    
    # Настройки безопасности
    admin_token: str
    
    # Настройки Telegram
    bot_token: str  # Для верификации запросов от бота
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Settings() 