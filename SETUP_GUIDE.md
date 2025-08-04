# 🚀 CryptoAlphaPro - Setup Guide

## 📋 Что было создано

Профессиональный крипто-сигнальный бот с полной архитектурой согласно техническому заданию:

### 🏗️ Архитектура системы
- **Главное приложение**: `src/main.py` - точка входа со всеми компонентами
- **Конфигурация**: `src/config/config_manager.py` - управление настройками
- **Сбор данных**: `src/data_collector/data_manager.py` - сбор данных с бирж
- **Аналитика**: `src/analytics/signal_generator.py` - генерация сигналов
- **ML модели**: `src/prediction/ml_predictor.py` - LSTM и GARCH модели
- **Риск-менеджмент**: `src/risk_management/risk_manager.py` - управление рисками
- **Telegram бот**: `src/telegram_bot/bot.py` - отправка сигналов
- **Арбитраж**: `src/arbitrage/arbitrage_manager.py` - поиск арбитражных возможностей
- **Мониторинг**: `src/monitoring/prometheus_metrics.py` - метрики системы

### 🛠️ Технологии
- **Python 3.11+** с asyncio
- **ML**: PyTorch (LSTM), GARCH, XGBoost, Random Forest
- **ТА**: TA-Lib для технических индикаторов
- **Базы данных**: TimescaleDB, PostgreSQL, Redis
- **Очереди**: RabbitMQ + Celery
- **Мониторинг**: Prometheus + Grafana
- **Биржи**: Binance, Bybit, OKX (через CCXT)
- **Telegram**: python-telegram-bot

## 🚀 Установка

### 1. Системные требования
```bash
# macOS
brew install python@3.11 ta-lib postgresql redis rabbitmq

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip
sudo apt-get install libta-lib-dev postgresql redis-server rabbitmq-server

# TimescaleDB
sudo apt-get install postgresql-15-timescaledb
```

### 2. Создание окружения
```bash
# Клонирование проекта
git clone https://github.com/djoni82/SIGNAL.git crypto_signal_bot
cd crypto_signal_bot

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка баз данных

#### PostgreSQL и TimescaleDB
```bash
# Создание пользователя и базы данных
sudo -u postgres createuser -P crypto_user
sudo -u postgres createdb -O crypto_user crypto_timeseries
sudo -u postgres createdb -O crypto_user crypto_metadata

# Подключение к TimescaleDB
sudo -u postgres psql crypto_timeseries
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
\q
```

#### Redis
```bash
# Настройка Redis с паролем
echo "requirepass your_redis_password" >> /etc/redis/redis.conf
sudo systemctl restart redis
```

#### RabbitMQ
```bash
# Создание пользователя RabbitMQ
sudo rabbitmqctl add_user crypto_user your_password
sudo rabbitmqctl set_user_tags crypto_user administrator
sudo rabbitmqctl set_permissions -p / crypto_user ".*" ".*" ".*"
```

### 4. Переменные окружения

Создайте файл `.env`:
```bash
# Базы данных
TIMESCALE_PASSWORD=your_timescale_password
POSTGRES_PASSWORD=your_postgres_password
REDIS_PASSWORD=your_redis_password
RABBITMQ_PASSWORD=your_rabbitmq_password

# Биржи
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
BYBIT_API_KEY=your_bybit_api_key
BYBIT_SECRET=your_bybit_secret
OKX_API_KEY=your_okx_api_key
OKX_SECRET=your_okx_secret
OKX_PASSPHRASE=your_okx_passphrase

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
TELEGRAM_ADMIN_CHAT_ID=your_admin_chat_id

# Внешние API (опционально)
DUNE_API_KEY=your_dune_api_key
CRYPTOPANIC_API_KEY=your_cryptopanic_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Мониторинг
GRAFANA_ADMIN_PASSWORD=admin_password
```

### 5. Конфигурация

Отредактируйте `config/config.yaml` для настройки:
- Торговых пар
- Таймфреймов
- Параметров риск-менеджмента
- Настроек ML моделей

## 🏃‍♂️ Запуск

### Вариант 1: Docker (рекомендуется)
```bash
# Запуск всей инфраструктуры
docker-compose up -d

# Просмотр логов
docker-compose logs -f crypto_signal_bot

# Остановка
docker-compose down
```

### Вариант 2: Ручной запуск
```bash
# Активация окружения
source venv/bin/activate

# Запуск основных сервисов
sudo systemctl start postgresql redis rabbitmq-server

# Запуск бота
python src/main.py
```

### Вариант 3: Разработка
```bash
# Установка зависимостей для разработки
pip install pytest pytest-asyncio black flake8

# Запуск тестов
pytest tests/

# Форматирование кода
black src/

# Проверка стиля
flake8 src/
```

## 📊 Мониторинг

После запуска доступны:
- **Prometheus метрики**: http://localhost:9090
- **Grafana дашборд**: http://localhost:3000 (admin:admin)
- **RabbitMQ управление**: http://localhost:15672

## 🤖 Telegram команды

После настройки бота доступны команды:
- `/start` - Приветствие
- `/help` - Список команд
- `/status` - Статус системы
- `/signals` - Последние сигналы
- `/stats` - Статистика
- `/config` - Конфигурация

## 🎯 Основные функции

### Генерация сигналов
Система анализирует:
- **Технические индикаторы**: RSI, MACD, EMA, ATR, Bollinger Bands
- **Мультитаймфреймный анализ**: 15m, 1h, 4h, 1d
- **Объемы и волатильность**
- **ML предсказания**: LSTM + GARCH модели

### Риск-менеджмент
- Динамический расчет плеча на основе волатильности
- ATR-based стоп-лоссы и тейк-профиты
- Контроль концентрации портфеля
- Автоматическое хеджирование

### Арбитраж
- Мониторинг спредов между биржами
- Триангульный арбитраж
- Автоматическое исполнение сделок

## 🔧 Настройка для продакшена

### AWS EC2 развертывание
```bash
# Рекомендуемая конфигурация
# Instance: c5.4xlarge (16 vCPU, 32GB RAM)
# Storage: 100GB+ SSD

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Клонирование и запуск
git clone https://github.com/djoni82/SIGNAL.git
cd SIGNAL
cp .env.example .env
# Настройка переменных окружения
docker-compose -f docker-compose.prod.yml up -d
```

### Безопасность
```bash
# Настройка файрвола
sudo ufw allow 22    # SSH
sudo ufw allow 443   # HTTPS
sudo ufw allow 3000  # Grafana (только для админов)
sudo ufw enable

# SSL сертификаты
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

## 📈 Производительность

### Целевые метрики
- **Время генерации сигнала**: <250мс
- **Задержка данных**: <100мс
- **Точность прогнозов**: >72%
- **Uptime**: 99.9%

### Оптимизация
- Используйте SSD для баз данных
- Настройте connection pooling
- Включите Redis clustering для высоких нагрузок
- Используйте CDN для статических ресурсов

## 🐛 Диагностика проблем

### Общие проблемы
```bash
# Проверка подключений к базам данных
docker-compose exec timescaledb pg_isready

# Проверка Redis
redis-cli ping

# Проверка логов
docker-compose logs crypto_signal_bot | tail -100

# Проверка метрик
curl http://localhost:9090/metrics
```

### Отладка
- Установите `log_level: DEBUG` в конфигурации
- Используйте `pytest -v` для детального тестирования
- Мониторьте использование памяти и CPU

## 🔄 Обновления

```bash
# Обновление кода
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt --upgrade

# Перезапуск сервисов
docker-compose restart
```

## 📚 Документация

### API Reference
- Все модули имеют подробную документацию в docstrings
- Используйте `help(module_name)` в Python консоли

### Конфигурация
- `config/config.yaml` - основные настройки
- `docker-compose.yml` - настройки контейнеров
- `.env` - переменные окружения

## ⚠️ Дисклеймер

**ВНИМАНИЕ**: Это программное обеспечение предназначено для образовательных и исследовательских целей.

- **Не является финансовым советом**
- **Торговля криптовалютами связана с высокими рисками**
- **Используйте на свой страх и риск**
- **Всегда проводите собственный анализ**

## 🆘 Поддержка

- **Issues**: [GitHub Issues](https://github.com/djoni82/SIGNAL/issues)
- **Discussions**: [GitHub Discussions](https://github.com/djoni82/SIGNAL/discussions)
- **Email**: support@cryptoalphapro.com

---

**Made with ❤️ for the crypto community**

*Happy Trading! 🚀* 