# 🚀 Инструкция по деплою UnifiedSignalBot

## 📋 Предварительные требования

- Docker и Docker Compose
- Git
- Python 3.11+
- Доступ к серверу (VPS/Cloud)

## 🐳 Docker деплой

### 1. Клонирование репозитория
```bash
git clone https://github.com/djoni82/SIGNAL.git
cd SIGNAL
```

### 2. Настройка конфигурации
Создайте файл `config.py` с вашими API ключами (см. README.md)

### 3. Запуск через Docker Compose
```bash
# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 4. Проверка статуса
```bash
# Статус контейнеров
docker-compose ps

# Логи бота
docker logs unified-signal-bot
```

## 🐳 Ручной Docker деплой

### 1. Сборка образа
```bash
docker build -t unified-signal-bot .
```

### 2. Запуск контейнера
```bash
docker run -d \
  --name unified-signal-bot \
  --restart unless-stopped \
  -v $(pwd)/config.py:/app/config.py:ro \
  -v $(pwd)/logs:/app/logs \
  unified-signal-bot
```

### 3. Управление контейнером
```bash
# Остановка
docker stop unified-signal-bot

# Перезапуск
docker restart unified-signal-bot

# Удаление
docker rm -f unified-signal-bot
```

## 🚀 Production деплой

### 1. Настройка сервера
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Клонирование и настройка
```bash
# Создание директории
sudo mkdir -p /opt/unified-signal-bot
cd /opt/unified-signal-bot

# Клонирование репозитория
sudo git clone https://github.com/djoni82/SIGNAL.git .

# Настройка прав доступа
sudo chown -R $USER:$USER /opt/unified-signal-bot
```

### 3. Настройка конфигурации
```bash
# Создание config.py
nano config.py
# Вставьте ваши API ключи
```

### 4. Запуск в production
```bash
# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

## 🔄 Автоматический деплой через GitHub Actions

### 1. Настройка секретов в GitHub
Перейдите в Settings → Secrets and variables → Actions и добавьте:

- `DOCKER_USERNAME` - ваш Docker Hub логин
- `DOCKER_PASSWORD` - ваш Docker Hub пароль
- `HOST` - IP адрес вашего сервера
- `USERNAME` - пользователь сервера
- `KEY` - приватный SSH ключ

### 2. Автоматический деплой
При каждом push в main ветку:
1. Запускаются тесты
2. Собирается Docker образ
3. Образ загружается в Docker Hub
4. Автоматически деплоится на сервер

## 📊 Мониторинг

### 1. Логи
```bash
# Docker Compose логи
docker-compose logs -f unified-signal-bot

# Системные логи
journalctl -u docker.service -f
```

### 2. Статистика
```bash
# Использование ресурсов
docker stats unified-signal-bot

# Размер образов
docker images
```

### 3. Telegram команды
- `/status` - статус бота
- `/stats` - статистика
- `/restart` - перезапуск

## 🔧 Troubleshooting

### Проблема: Бот не запускается
```bash
# Проверка логов
docker-compose logs unified-signal-bot

# Проверка конфигурации
python -c "import config; print('Config OK')"
```

### Проблема: Нет сигналов
```bash
# Проверка API ключей
docker exec unified-signal-bot python -c "import config; print('API keys loaded')"

# Проверка подключения к биржам
docker exec unified-signal-bot python -c "import ccxt; print('CCXT OK')"
```

### Проблема: Telegram не работает
```bash
# Проверка Telegram токена
curl "https://api.telegram.org/bot/YOUR_BOT_TOKEN/getMe"
```

## 🔒 Безопасность

### 1. Firewall
```bash
# Открытие только необходимых портов
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. SSL сертификаты
```bash
# Установка Certbot
sudo apt install certbot

# Получение сертификата
sudo certbot certonly --standalone -d your-domain.com
```

### 3. Резервное копирование
```bash
# Создание бэкапа
tar -czf backup-$(date +%Y%m%d).tar.gz config.py logs/

# Автоматическое резервное копирование (cron)
0 2 * * * tar -czf /backups/backup-$(date +\%Y\%m\%d).tar.gz /opt/unified-signal-bot/config.py /opt/unified-signal-bot/logs/
```

## 📈 Масштабирование

### 1. Горизонтальное масштабирование
```bash
# Запуск нескольких экземпляров
docker-compose up -d --scale unified-signal-bot=3
```

### 2. Load Balancer
```bash
# Настройка Nginx
sudo apt install nginx
sudo nano /etc/nginx/sites-available/unified-signal-bot
```

### 3. Мониторинг через Prometheus/Grafana
```bash
# Добавление метрик
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

---

**🚀 UnifiedSignalBot готов к production деплою!** 