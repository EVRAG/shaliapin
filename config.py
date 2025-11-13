"""Конфигурация приложения"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Настройки приложения"""
    # OpenAI
    openai_api_key: str
    
    # Database
    database_path: str = "./data/messages.db"
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Создаем директорию для БД если её нет
settings = Settings()
db_path = Path(settings.database_path)
if db_path.parent != Path('.'):
    db_path.parent.mkdir(parents=True, exist_ok=True)

