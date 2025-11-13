#!/bin/bash

# Скрипт для резервного копирования базы данных

BACKUP_DIR="/opt/shalapin-bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/messages_$DATE.db"
SOURCE_DB="/opt/shalapin-bot/data/messages.db"

# Создаем директорию для бэкапов если её нет
mkdir -p "$BACKUP_DIR"

# Проверяем существование базы данных
if [ ! -f "$SOURCE_DB" ]; then
    echo "Ошибка: База данных не найдена: $SOURCE_DB"
    exit 1
fi

# Копируем базу данных
cp "$SOURCE_DB" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Бэкап создан успешно: $BACKUP_FILE"
    
    # Сжимаем бэкап
    gzip "$BACKUP_FILE"
    echo "Бэкап сжат: $BACKUP_FILE.gz"
    
    # Удаляем старые бэкапы (оставляем последние 30 дней)
    find "$BACKUP_DIR" -name "messages_*.db.gz" -mtime +30 -delete
    echo "Старые бэкапы удалены (старше 30 дней)"
else
    echo "Ошибка при создании бэкапа"
    exit 1
fi

