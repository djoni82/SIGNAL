#!/bin/bash

# Скрипт для настройки GitHub репозитория CryptoAlphaPro Signal Bot

echo "🚀 Настройка GitHub репозитория для CryptoAlphaPro Signal Bot v3.0"
echo "=" * 60

# Проверяем, что мы в правильной директории
if [ ! -f "README.md" ]; then
    echo "❌ Ошибка: README.md не найден. Убедитесь, что вы в корневой директории проекта."
    exit 1
fi

# Инициализируем Git репозиторий
echo "📁 Инициализация Git репозитория..."
git init

# Добавляем все файлы
echo "📝 Добавление файлов в Git..."
git add .

# Создаем первый коммит
echo "💾 Создание первого коммита..."
git commit -m "🚀 Initial commit: CryptoAlphaPro Signal Bot v3.0

✨ Features:
- Multi-exchange data collection (Binance, Bybit, OKX)
- AI-powered signal generation
- News sentiment analysis (CryptoPanic)
- On-chain data analysis (Dune Analytics)
- Twitter sentiment analysis
- Dynamic leverage calculation (1x-50x)
- Telegram bot integration
- Universal pair support
- Comprehensive testing suite
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Monitoring with Prometheus & Grafana

📊 Technical Stack:
- Python 3.11+
- AsyncIO for high performance
- PostgreSQL + Redis
- Docker + Docker Compose
- GitHub Actions for automation
- Comprehensive test coverage

🎯 Ready for production deployment!"

# Создаем ветку develop
echo "🌿 Создание ветки develop..."
git checkout -b develop

# Создаем ветку main
echo "🌿 Создание ветки main..."
git checkout -b main

echo ""
echo "✅ Git репозиторий настроен!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Создайте репозиторий на GitHub:"
echo "   https://github.com/new"
echo ""
echo "2. Добавьте remote origin:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/cryptoalpha-pro-signal-bot.git"
echo ""
echo "3. Отправьте код на GitHub:"
echo "   git push -u origin main"
echo "   git push -u origin develop"
echo ""
echo "4. Настройте GitHub Secrets:"
echo "   - DOCKER_USERNAME"
echo "   - DOCKER_PASSWORD"
echo "   - TELEGRAM_TOKEN"
echo "   - TELEGRAM_CHAT_ID"
echo "   - CRYPTOPANIC_TOKEN"
echo "   - DUNE_API_KEY"
echo "   - TWITTER_BEARER_TOKEN"
echo ""
echo "5. Запустите CI/CD pipeline:"
echo "   - Push в main запустит production деплой"
echo "   - Push в develop запустит staging деплой"
echo ""
echo "🎉 Проект готов к автоматическому деплою!"

# Создаем файл с инструкциями по деплою
cat > DEPLOYMENT_GUIDE.md << 'EOF'
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
EOF

echo "📖 Создан файл DEPLOYMENT_GUIDE.md с подробными инструкциями"
echo ""
echo "🎯 Проект полностью готов к деплою!" 