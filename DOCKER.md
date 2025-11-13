# Docker инструкции

## Быстрый старт

1. Создайте файл `.env` с вашими токенами:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

2. Запустите через Docker Compose:
```bash
docker-compose up -d
```

3. Проверьте логи:
```bash
docker-compose logs -f
```

## Команды Docker Compose

### Запуск
```bash
docker-compose up -d
```

### Остановка
```bash
docker-compose down
```

### Просмотр логов
```bash
docker-compose logs -f
```

### Пересборка после изменений кода
```bash
docker-compose up -d --build
```

### Перезапуск
```bash
docker-compose restart
```

### Просмотр статуса
```bash
docker-compose ps
```

## Использование Docker напрямую

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
  --env-file .env \
  shalapin-bot
```

### Остановка контейнера
```bash
docker stop shalapin-bot
docker rm shalapin-bot
```

### Просмотр логов
```bash
docker logs -f shalapin-bot
```

## Персистентность данных

База данных SQLite сохраняется в директории `./data` на хосте, которая монтируется в контейнер. Это означает, что данные сохраняются даже после перезапуска контейнера.

## Проблемы и решения

### Проблема: Контейнер не запускается
- Проверьте, что файл `.env` существует и содержит все необходимые переменные
- Проверьте логи: `docker-compose logs`

### Проблема: Порт 8000 уже занят
- Измените порт в `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Используйте другой порт на хосте
```

### Проблема: База данных не сохраняется
- Убедитесь, что директория `./data` существует и имеет правильные права доступа
- Проверьте, что volume правильно смонтирован: `docker-compose ps`

