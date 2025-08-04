# 🚀 Руководство по деплою CryptoAlphaPro Signal Bot

## 📋 Предварительные требования

### 1. GitHub репозиторий
- Создайте репозиторий на GitHub
- Добавьте remote origin
- Настройте GitHub Secrets

### 2. Сервер для деплоя
- Ubuntu 20.04+ или CentOS 8+
- Docker и Docker Compose
- Минимум 4GB RAM, 2 CPU cores
- 50GB свободного места

### 3. API ключи
- Telegram Bot Token
- CryptoPanic API Key
- Dune Analytics API Key
- Twitter Bearer Token

## 🐳 Docker деплой

### Локальный запуск
```bash
# Клонирование
git clone https://github.com/YOUR_USERNAME/cryptoalpha-pro-signal-bot.git
cd cryptoalpha-pro-signal-bot

# Настройка окружения
cp env.example .env
# Отредактируйте .env файл

# Запуск
docker-compose up -d

# Проверка статуса
docker-compose ps
docker-compose logs -f cryptoalpha-bot
```

### Продакшен деплой
```bash
# На сервере
git clone https://github.com/YOUR_USERNAME/cryptoalpha-pro-signal-bot.git
cd cryptoalpha-pro-signal-bot

# Настройка
cp env.example .env
nano .env  # Настройте переменные

# Запуск
docker-compose -f docker-compose.yml up -d

# Мониторинг
docker-compose logs -f
```

## 🔧 Настройка мониторинга

### Grafana дашборд
1. Откройте http://your-server:3000
2. Логин: admin / admin123
3. Импортируйте дашборды из monitoring/grafana/

### Prometheus метрики
1. Откройте http://your-server:9090
2. Проверьте targets и метрики

## 📱 Telegram бот

### Команды
- `/start` - Инициализация
- `/startbot` - Запуск мониторинга
- `/stopbot` - Остановка мониторинга
- `/status` - Статус бота
- `/signals` - Генерация сигналов
- `/help` - Справка

## 🔒 Безопасность

### Переменные окружения
- Никогда не коммитьте .env файл
- Используйте GitHub Secrets
- Ротация API ключей

### Сетевая безопасность
- Настройте firewall
- Используйте SSL/TLS
- Ограничьте доступ к портам

## 📊 Производительность

### Мониторинг
- CPU: <80%
- RAM: <4GB
- Disk: <50GB
- Network: <100Mbps

### Оптимизация
- Настройте кэширование Redis
- Оптимизируйте запросы к БД
- Мониторьте API лимиты

## 🆘 Устранение неполадок

### Логи
```bash
# Логи бота
docker-compose logs cryptoalpha-bot

# Логи всех сервисов
docker-compose logs

# Логи в реальном времени
docker-compose logs -f
```

### Перезапуск
```bash
# Перезапуск бота
docker-compose restart cryptoalpha-bot

# Перезапуск всех сервисов
docker-compose restart
```

### Обновление
```bash
# Обновление кода
git pull origin main

# Пересборка и перезапуск
docker-compose down
docker-compose up -d --build
```

## 📞 Поддержка

- GitHub Issues: [Создать issue](https://github.com/YOUR_USERNAME/cryptoalpha-pro-signal-bot/issues)
- Telegram: [@cryptoalpha_support](https://t.me/cryptoalpha_support)
- Email: support@cryptoalpha.pro

---

**Удачного трейдинга! 🚀**
