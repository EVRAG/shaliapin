#!/bin/bash

# Скрипт для обновления приложения

set -e

PROJECT_DIR="/opt/shalapin-bot"
cd "$PROJECT_DIR"

echo "=== Обновление Shalapin Bot ==="

# Создаем бэкап перед обновлением
echo "Создание бэкапа..."
./scripts/backup.sh

# Обновляем код (если используется git)
if [ -d ".git" ]; then
    echo "Обновление кода из git..."
    git pull
fi

# Пересобираем и перезапускаем контейнеры
echo "Пересборка контейнеров..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Ждем запуска
echo "Ожидание запуска сервисов..."
sleep 10

# Проверяем статус
echo "Проверка статуса..."
docker-compose -f docker-compose.prod.yml ps

# Проверяем health check
echo "Проверка health check..."
sleep 5
curl -f http://localhost:8000/api/health || echo "ВНИМАНИЕ: Health check не прошел!"

echo "=== Обновление завершено ==="

