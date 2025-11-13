# Shalapin Bot

Система для обработки сообщений с проверкой через OpenAI и очередью сообщений.

## Архитектура

### Компоненты системы:

1. **REST API** (`api.py`)
   - FastAPI сервер с эндпоинтами:
     - `POST /api/messages/create` - создать новое сообщение (принимает имя, пол, настроение, текст)
     - `GET /api/messages` - получить последние 5 сообщений со статусом 'ok'
     - `GET /api/messages/all` - получить все сообщения для фронтенда
     - `PATCH /api/messages/{id}/status` - изменить статус сообщения
     - `POST /api/queue/reset` - сбросить очередь
     - `GET /api/health` - проверка здоровья API

2. **OpenAI Service** (`openai_service.py`)
   - Асинхронная проверка сообщений через OpenAI API (эндпоинт `/v1/chat/completions`)
   - Модерация сообщений на соответствие теме "Создай фразу легкой жизни в стиле Прохора Шаляпина"
   - Поддержка параллельных запросов (семафор на 10 одновременных запросов)
   - Возвращает структурированный JSON ответ с полями `response` и `status` (ok/restricted)

3. **Database** (`database.py`)
   - SQLite база данных для хранения сообщений
   - Поля: имя, пол, настроение, текст сообщения, ответ OpenAI, статус
   - Атомарные операции с использованием транзакций
   - Индексы для быстрого поиска

4. **Frontend** (`frontend/`)
   - React приложение с адаптивным дизайном
   - Таблица/карточки всех сообщений
   - Возможность ручной модерации (принять/отклонить)

### Поток данных:

```
API Request → OpenAI Service (параллельно) → Database → Response
                                                      ↓
                                                Frontend ← REST API
```

### Особенности реализации:

- **Параллельная обработка**: Семафор ограничивает количество одновременных запросов к OpenAI (10 по умолчанию)
- **Атомарность операций**: Использование транзакций SQLite с `BEGIN IMMEDIATE` для блокировки при получении сообщений
- **Надежность**: Обработка ошибок на всех уровнях, корректное завершение при остановке
- **Масштабируемость**: Асинхронная архитектура позволяет обрабатывать множество запросов одновременно

## Установка

### Вариант 1: Деплой на VPS (Production)

Подробная инструкция по развертыванию на VPS сервере с HTTPS, автозапуском и бэкапами: **[DEPLOY.md](DEPLOY.md)**

### Вариант 2: Docker (локальная разработка)

1. Создайте файл `.env` на основе `.env.example` и заполните токены:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

2. Запустите через Docker Compose:
```bash
docker-compose up -d --build
```

3. Откройте фронтенд в браузере:
- Фронтенд: http://localhost
- API: http://localhost:8000

4. Просмотр логов:
```bash
docker-compose logs -f
```

5. Остановка:
```bash
docker-compose down
```

### Вариант 2: Локальная установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` на основе `.env.example` и заполните токены:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_PATH=./data/messages.db
API_HOST=0.0.0.0
API_PORT=8000
```

3. Запустите приложение:
```bash
python main.py
```

## Использование

### REST API

- **Создать сообщение**: `POST http://localhost:8000/api/messages/create`
  ```json
  {
    "name": "Иван",
    "gender": "Мужской",
    "mood": "Хорошее",
    "message_text": "Эх, как же хорошо жить легко!"
  }
  ```

- **Получить последние 5 сообщений**: `GET http://localhost:8000/api/messages`
- **Получить все сообщения**: `GET http://localhost:8000/api/messages/all`
- **Изменить статус**: `PATCH http://localhost:8000/api/messages/{id}/status`
- **Сбросить очередь**: `POST http://localhost:8000/api/queue/reset`
- **Проверка здоровья**: `GET http://localhost:8000/api/health`

Подробнее см. [API_USAGE.md](API_USAGE.md)

### Frontend

- Откройте http://localhost в браузере
- Просматривайте все сообщения в виде карточек
- Модерируйте сообщения вручную через кнопки "Принять" / "Отклонить"

## Структура проекта

```
Shalapin_bot/
├── main.py              # Главный файл приложения
├── config.py            # Конфигурация
├── openai_service.py    # Сервис OpenAI
├── database.py          # Работа с БД
├── api.py               # REST API
├── requirements.txt     # Зависимости
├── Dockerfile           # Docker образ
├── docker-compose.yml   # Docker Compose конфигурация
├── .dockerignore        # Исключения для Docker
├── .env.example         # Пример конфигурации
├── frontend/            # React фронтенд
│   ├── src/
│   │   ├── App.jsx      # Главный компонент
│   │   └── ...
│   └── ...
├── README.md            # Документация
└── API_USAGE.md         # Документация API
```

## Docker

### Сборка образа

```bash
docker build -t shalapin-bot .
```

### Запуск контейнера

```bash
docker run -d \
  --name shalapin-bot \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e OPENAI_API_KEY=your_key \
  shalapin-bot
```

### Использование docker-compose

```bash
# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Пересборка после изменений
docker-compose up -d --build
```

