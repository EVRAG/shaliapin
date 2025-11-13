"""REST API для другого сервиса"""
import json
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db
from openai_service import openai_service


class ResetQueueResponse(BaseModel):
    """Ответ на сброс очереди"""
    message: str
    reset_count: int


class UpdateStatusRequest(BaseModel):
    """Запрос на обновление статуса"""
    status: str  # 'ok' или 'restricted'


class CreateMessageRequest(BaseModel):
    """Запрос на создание сообщения"""
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    mood: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Инициализация базы данных
    await db.init_db()
    
    yield


app = FastAPI(
    title="Shalapin Bot API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/messages")
async def get_messages() -> list[Dict[str, Any]]:
    """
    Получить последние 5 сообщений со статусом 'ok' из очереди.
    
    Сообщения НЕ помечаются как забранные и остаются в очереди.
    Возвращает список из последних 5 сообщений, отсортированных по дате создания (новые первыми).
    """
    messages = await db.get_latest_messages(limit=5)
    return messages


@app.post("/api/queue/reset")
async def reset_queue() -> ResetQueueResponse:
    """
    Сбросить очередь - пометить все сообщения как незабранные.
    
    Это позволяет другому сервису снова получить доступ ко всем сообщениям.
    """
    reset_count = await db.reset_queue()
    
    return ResetQueueResponse(
        message=f"Очередь сброшена. Помечено сообщений: {reset_count}",
        reset_count=reset_count
    )


@app.get("/api/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "ok"}


@app.post("/api/messages/create")
async def create_message(request: CreateMessageRequest) -> Dict[str, Any]:
    """
    Создать новое сообщение.
    
    Принимает имя, пол, настроение и текст сообщения.
    Отправляет на модерацию в OpenAI и сохраняет в базу данных.
    """
    previous_messages = await db.get_last_approved_messages(limit=3)
    
    # Проверяем сообщение через OpenAI
    result = await openai_service.check_message(
        name=request.name,
        age=request.age,
        gender=request.gender,
        mood=request.mood,
        previous_messages=previous_messages
    )
    
    # Сохраняем в базу данных
    message_id = await db.add_message(
        name=request.name,
        age=request.age,
        gender=request.gender,
        mood=request.mood,
        message_text=result.get('response', ''),
        openai_response=json.dumps(result, ensure_ascii=False),
        status=result['status']
    )
    
    return {
        "id": message_id,
        "name": request.name,
        "age": request.age,
        "gender": request.gender,
        "mood": request.mood,
        "message_text": result.get('response', ''),
        "status": result['status'],
        "openai_response": result
    }


@app.get("/api/messages/all")
async def get_all_messages() -> list[Dict[str, Any]]:
    """
    Получить все сообщения для фронтенда.
    """
    messages = await db.get_all_messages()
    return messages


@app.patch("/api/messages/{message_id}/status")
async def update_message_status(message_id: int, request: UpdateStatusRequest) -> Dict[str, Any]:
    """
    Обновить статус сообщения.
    
    Это позволяет вручную изменить статус модерации сообщения.
    """
    if request.status not in ['ok', 'restricted']:
        raise HTTPException(status_code=400, detail="Status must be 'ok' or 'restricted'")
    
    success = await db.update_message_status(message_id, request.status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {"message": "Status updated successfully", "message_id": message_id, "status": request.status}

