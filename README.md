# 🚀 CryptoAlphaPro Signal Bot

**Продвинутый AI-бот для генерации торговых сигналов на криптовалютном рынке**

[![GitHub Actions](https://github.com/djoni82/SIGNAL/workflows/CI/CD/badge.svg)](https://github.com/djoni82/SIGNAL/actions)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://hub.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 **Особенности**

- 🤖 **AI-анализ** - Машинное обучение для прогнозирования цен
- 📊 **Мульти-биржа** - Поддержка Binance, Bybit, OKX
- 📰 **Новостной анализ** - Интеграция с CryptoPanic
- 🔗 **On-chain данные** - Анализ блокчейн метрик
- 🐦 **Социальные сети** - Twitter sentiment анализ
- 📱 **Telegram бот** - Удобное управление через чат
- 🐳 **Docker готов** - Простое развертывание
- 📈 **Мониторинг** - Grafana + Prometheus
- 🔒 **Безопасность** - Шифрование и JWT токены

## ⚡ **Быстрый старт**

### **1. Настройка GitHub Actions Secrets**

Выберите удобный способ:

- 🔗 **[Прямые ссылки](QUICK_SETUP.md)** (рекомендуется)
- ⚡ **[Автоматический скрипт](setup_github_secrets.sh)**
- 📝 **[Ручная настройка](GITHUB_ACTIONS_SETUP.md)**

### **2. Запуск**

```bash
# Клонируйте репозиторий
git clone https://github.com/djoni82/SIGNAL.git
cd SIGNAL

# Настройте секреты (см. выше)
# Сделайте push для запуска CI/CD
git push origin main
```

### **3. Проверка**

- Перейдите в [Actions](https://github.com/djoni82/SIGNAL/actions)
- Дождитесь успешного завершения pipeline
- Найдите бота в Telegram: `@your_bot_username`

## 📱 **Telegram команды**

| Команда | Описание |
|---------|----------|
| `/startbot` | Запустить бота |
| `/stopbot` | Остановить бота |
| `/status` | Статус бота |
| `/signals` | Последние сигналы |
| `/pairs` | Список пар |
| `/addpair BTCUSDT` | Добавить пару |
| `/help` | Справка |

## 🏗️ **Архитектура**

```
📁 crypto_signal_bot_pro/
├── 🤖 analytics/           # AI анализ и индикаторы
├── 📊 data_collector/      # Сбор данных с бирж
├── 🛡️ risk_management/     # Управление рисками
├── 📱 telegram_bot/        # Telegram интерфейс
├── 🛠️ utils/              # Утилиты и хелперы
├── 🐳 Dockerfile           # Docker конфигурация
├── 🔄 docker-compose.yml   # Оркестрация сервисов
└── 📋 requirements.txt     # Зависимости Python
```

## 🔧 **Технологии**

- **Python 3.8+** - Основной язык
- **TensorFlow/Keras** - Машинное обучение
- **Pandas/NumPy** - Анализ данных
- **Telegram Bot API** - Мессенджер интеграция
- **Docker** - Контейнеризация
- **PostgreSQL** - База данных
- **Grafana** - Визуализация
- **Prometheus** - Мониторинг

## 📊 **Возможности**

### **AI Анализ**
- LSTM нейросети для прогнозирования
- Технические индикаторы (RSI, MACD, Bollinger)
- Анализ паттернов и трендов
- Мультитаймфреймовый анализ

### **Риск-менеджмент**
- Динамическое плечо (1x-50x)
- Stop-loss и Take-profit
- Позиционный sizing
- Максимальная просадка

### **Интеграции**
- **Биржи:** Binance, Bybit, OKX
- **Новости:** CryptoPanic API
- **On-chain:** Dune Analytics
- **Соцсети:** Twitter API

## 🚀 **Развертывание**

### **Локальный запуск**
```bash
pip install -r requirements.txt
python full_featured_bot.py
```

### **Docker**
```bash
docker build -t cryptoalpha-signal-bot .
docker run -d --name signal-bot cryptoalpha-signal-bot
```

### **Docker Compose**
```bash
docker-compose up -d
```

## 📈 **Мониторинг**

- **Grafana:** http://localhost:3000 (admin/admin123)
- **Prometheus:** http://localhost:9090
- **Логи:** `docker logs signal-bot`

## 🔒 **Безопасность**

- ✅ Шифрование API ключей
- ✅ JWT токены для аутентификации
- ✅ Rate limiting
- ✅ Валидация входных данных
- ✅ Логирование безопасности

## 📋 **Требования**

- **Python:** 3.8+
- **RAM:** 4+ GB
- **CPU:** 2+ ядра
- **Диск:** 20+ GB
- **Сеть:** Стабильное интернет-соединение

## 🤝 **Вклад в проект**

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 **Лицензия**

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## ⚠️ **Отказ от ответственности**

Этот бот предназначен только для образовательных целей. Торговля криптовалютами связана с высокими рисками. Авторы не несут ответственности за финансовые потери.

## 📞 **Поддержка**

- 📧 **Email:** support@cryptoalpha.com
- 💬 **Telegram:** @cryptoalpha_support
- 🐛 **Issues:** [GitHub Issues](https://github.com/djoni82/SIGNAL/issues)
- 📖 **Документация:** [Wiki](https://github.com/djoni82/SIGNAL/wiki)

## 🌟 **Благодарности**

- [Binance API](https://binance-docs.github.io/apidocs/) за данные
- [CryptoPanic](https://cryptopanic.com/) за новости
- [Dune Analytics](https://dune.com/) за on-chain данные
- [Telegram Bot API](https://core.telegram.org/bots/api) за мессенджер

---

**⭐ Если проект вам понравился, поставьте звездочку!**

**🚀 Готов к запуску в продакшене!** 