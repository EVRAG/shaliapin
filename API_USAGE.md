# Использование API

## Эндпоинты

### POST /api/messages/create

Создать новое сообщение. Принимает имя, пол, настроение и текст сообщения. Отправляет на модерацию в OpenAI и сохраняет в базу данных.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/messages/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Иван",
    "gender": "Мужской",
    "mood": "Хорошее",
    "message_text": "Эх, как же хорошо жить легко!"
  }'
```

**Ответ (200 OK):**
```json
{
  "id": 1,
  "name": "Иван",
  "gender": "Мужской",
  "mood": "Хорошее",
  "message_text": "Эх, как же хорошо жить легко!",
  "status": "ok",
  "openai_response": {
    "response": "...",
    "status": "ok"
  }
}
```

**Поля запроса:**
- `name` (обязательное) - имя пользователя
- `gender` (опциональное) - пол
- `mood` (опциональное) - настроение
- `message_text` (обязательное) - текст сообщения

---

### GET /api/messages

Получить последние 5 сообщений со статусом 'ok' из очереди.

**Запрос:**
```bash
curl http://localhost:8000/api/messages
```

**Ответ (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Иван",
    "gender": "Мужской",
    "mood": "Хорошее",
    "message_text": "Текст сообщения",
    "openai_response": "{\"response\": \"...\", \"status\": \"ok\"}",
    "status": "ok",
    "created_at": "2024-01-01 12:00:00",
    "is_fetched": false,
    "fetched_at": null
  },
  ...
]
```

**Примечание:** Сообщения НЕ помечаются как забранные и остаются в очереди. Возвращает массив из последних 5 сообщений, отсортированных по дате (новые первыми).

---

### POST /api/queue/reset

Сбросить очередь - пометить все сообщения как незабранные.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/queue/reset
```

**Ответ (200 OK):**
```json
{
  "message": "Очередь сброшена. Помечено сообщений: 5",
  "reset_count": 5
}
```

---

### GET /api/health

Проверка здоровья API.

**Запрос:**
```bash
curl http://localhost:8000/api/health
```

**Ответ (200 OK):**
```json
{
  "status": "ok"
}
```

---

## Пример использования в Python

```python
import requests

# Создать сообщение
response = requests.post(
    "http://localhost:8000/api/messages/create",
    json={
        "name": "Иван",
        "gender": "Мужской",
        "mood": "Хорошее",
        "message_text": "Эх, как же хорошо жить легко!"
    }
)
if response.status_code == 200:
    result = response.json()
    print(f"Сообщение создано: {result['message_text']}")
    print(f"Статус: {result['status']}")

# Получить последние 5 сообщений
response = requests.get("http://localhost:8000/api/messages")
if response.status_code == 200:
    messages = response.json()
    print(f"Получено сообщений: {len(messages)}")
    for msg in messages:
        print(f"- {msg['name']}: {msg['message_text']}")

# Сбросить очередь
response = requests.post("http://localhost:8000/api/queue/reset")
if response.status_code == 200:
    result = response.json()
    print(f"Сброшено сообщений: {result['reset_count']}")
```

