"""Главный файл приложения"""
import uvicorn
from config import settings
from api import app


if __name__ == "__main__":
    # Запускаем FastAPI сервер
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )

