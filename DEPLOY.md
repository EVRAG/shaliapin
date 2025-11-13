# Деплой на VPS

Подробная инструкция по развертыванию проекта на VPS сервере.

## Требования

- VPS с Ubuntu 20.04+ или Debian 11+
- Минимум 1GB RAM, 10GB диска
- Root доступ или пользователь с sudo правами
- Доменное имя (для HTTPS)

## Шаг 1: Подготовка сервера

### 1.1 Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Установка Docker и Docker Compose

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перелогиньтесь или выполните:
newgrp docker
```

### 1.3 Установка Nginx (для reverse proxy и SSL)

```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

### 1.4 Настройка firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## Шаг 2: Развертывание приложения

### 2.1 Клонирование проекта

```bash
cd /opt
sudo git clone <your-repo-url> shalapin-bot
cd shalapin-bot
```

Или загрузите проект через `scp`:

```bash
# С вашего локального компьютера
scp -r /path/to/Shalapin_bot user@your-server:/opt/shalapin-bot
```

### 2.2 Создание .env файла

```bash
cd /opt/shalapin-bot
sudo nano .env
```

Заполните файл:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_PATH=/app/data/messages.db
API_HOST=0.0.0.0
API_PORT=8000
```

### 2.3 Создание директории для данных

```bash
sudo mkdir -p /opt/shalapin-bot/data
sudo chown -R $USER:$USER /opt/shalapin-bot
```

### 2.4 Запуск приложения

```bash
cd /opt/shalapin-bot
docker-compose -f docker-compose.prod.yml up -d --build
```

Проверьте статус:

```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## Шаг 3: Настройка Nginx и SSL

### 3.1 Создание конфигурации Nginx

```bash
sudo nano /etc/nginx/sites-available/shalapin-bot
```

Вставьте конфигурацию (замените `your-domain.com` на ваш домен):

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Логи
    access_log /var/log/nginx/shalapin-bot-access.log;
    error_log /var/log/nginx/shalapin-bot-error.log;

    # Проксирование на frontend контейнер
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 3.2 Активация конфигурации

```bash
sudo ln -s /etc/nginx/sites-available/shalapin-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3.3 Получение SSL сертификата

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot автоматически обновит конфигурацию Nginx для HTTPS.

### 3.4 Автоматическое обновление сертификата

Certbot создаст cron задачу автоматически. Проверить можно:

```bash
sudo certbot renew --dry-run
```

## Шаг 4: Настройка автозапуска (Systemd)

### 4.1 Создание systemd service

```bash
sudo nano /etc/systemd/system/shalapin-bot.service
```

Вставьте:

```ini
[Unit]
Description=Shalapin Bot Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/shalapin-bot
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

### 4.2 Активация сервиса

```bash
sudo systemctl daemon-reload
sudo systemctl enable shalapin-bot.service
sudo systemctl start shalapin-bot.service
```

Проверка:

```bash
sudo systemctl status shalapin-bot.service
```

## Шаг 5: Настройка бэкапов

### 5.1 Создание скрипта бэкапа

```bash
chmod +x /opt/shalapin-bot/scripts/backup.sh
```

### 5.2 Настройка cron для автоматических бэкапов

```bash
crontab -e
```

Добавьте строку для ежедневного бэкапа в 3:00:

```
0 3 * * * /opt/shalapin-bot/scripts/backup.sh
```

## Шаг 6: Мониторинг и логи

### Просмотр логов

```bash
# Логи всех сервисов
docker-compose -f docker-compose.prod.yml logs -f

# Логи только backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Логи только frontend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Логи Nginx
sudo tail -f /var/log/nginx/shalapin-bot-access.log
sudo tail -f /var/log/nginx/shalapin-bot-error.log
```

### Проверка здоровья

```bash
# Health check API
curl http://localhost:8000/api/health

# Проверка через домен
curl https://your-domain.com/api/health
```

## Обновление приложения

Используйте скрипт обновления:

```bash
cd /opt/shalapin-bot
./scripts/update.sh
```

Или вручную:

```bash
cd /opt/shalapin-bot
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

## Полезные команды

### Перезапуск сервисов

```bash
docker-compose -f docker-compose.prod.yml restart
```

### Остановка

```bash
docker-compose -f docker-compose.prod.yml down
```

### Полная остановка и удаление

```bash
docker-compose -f docker-compose.prod.yml down -v
```

### Просмотр использования ресурсов

```bash
docker stats
```

### Очистка неиспользуемых образов

```bash
docker system prune -a
```

## Безопасность

1. **Firewall**: Убедитесь, что UFW включен и настроен правильно
2. **SSH**: Используйте ключи вместо паролей, отключите root логин
3. **Docker**: Не запускайте контейнеры от root
4. **SSL**: Всегда используйте HTTPS
5. **Бэкапы**: Настройте регулярные бэкапы базы данных
6. **Обновления**: Регулярно обновляйте систему и Docker образы

## Устранение проблем

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
docker-compose -f docker-compose.prod.yml logs

# Проверьте .env файл
cat .env

# Проверьте порты
sudo netstat -tulpn | grep -E '80|443|8000|8080'
```

### Проблема: Nginx не проксирует запросы

```bash
# Проверьте конфигурацию
sudo nginx -t

# Проверьте, что контейнеры запущены
docker-compose -f docker-compose.prod.yml ps

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/shalapin-bot-error.log
```

### Проблема: SSL сертификат не обновляется

```bash
# Проверьте статус certbot
sudo certbot certificates

# Обновите вручную
sudo certbot renew
```

## Поддержка

При возникновении проблем проверьте:
1. Логи Docker: `docker-compose logs -f`
2. Логи Nginx: `/var/log/nginx/`
3. Статус systemd: `sudo systemctl status shalapin-bot`
4. Статус контейнеров: `docker-compose ps`

