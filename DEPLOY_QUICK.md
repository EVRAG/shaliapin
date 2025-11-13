# Быстрый деплой на VPS

Краткая инструкция для опытных пользователей.

## Предварительные требования

- Ubuntu/Debian VPS
- Доменное имя
- Root/sudo доступ

## Команды для быстрого деплоя

```bash
# 1. Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo usermod -aG docker $USER && newgrp docker
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 2. Установка Nginx и Certbot
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
sudo ufw allow 22,80,443/tcp && sudo ufw enable

# 3. Клонирование/загрузка проекта
cd /opt
sudo git clone <your-repo> shalapin-bot
# или загрузите через scp
cd shalapin-bot

# 4. Создание .env
sudo nano .env
# Заполните: OPENAI_API_KEY=...

# 5. Настройка прав
sudo mkdir -p data backups
sudo chown -R $USER:$USER /opt/shalapin-bot

# 6. Запуск
docker-compose -f docker-compose.prod.yml up -d --build

# 7. Настройка Nginx
sudo cp nginx-proxy.conf.example /etc/nginx/sites-available/shalapin-bot
sudo nano /etc/nginx/sites-available/shalapin-bot  # Замените your-domain.com
sudo ln -s /etc/nginx/sites-available/shalapin-bot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 8. SSL сертификат
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 9. Systemd автозапуск
sudo cp systemd/shalapin-bot.service.example /etc/systemd/system/shalapin-bot.service
sudo nano /etc/systemd/system/shalapin-bot.service  # Замените your-username
sudo systemctl daemon-reload
sudo systemctl enable shalapin-bot.service
sudo systemctl start shalapin-bot.service

# 10. Настройка бэкапов
crontab -e
# Добавьте: 0 3 * * * /opt/shalapin-bot/scripts/backup.sh
```

## Проверка

```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f

# Health check
curl https://your-domain.com/api/health
```

## Обновление

```bash
cd /opt/shalapin-bot
./scripts/update.sh
```

Подробная инструкция: [DEPLOY.md](DEPLOY.md)

