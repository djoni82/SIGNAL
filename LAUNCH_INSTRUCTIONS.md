# 🚀 Инструкция по запуску CryptoAlphaPro Signal Bot

## 📋 **Быстрый старт (5 минут)**

### **1. Настройка GitHub Actions Secrets**

Выберите один из способов:

#### **🔗 Способ 1: Прямые ссылки (рекомендуется)**
Откройте [QUICK_SETUP.md](QUICK_SETUP.md) и используйте прямые ссылки для добавления ключей.

#### **⚡ Способ 2: Автоматический скрипт**
```bash
# Клонируйте репозиторий
git clone https://github.com/djoni82/SIGNAL.git
cd SIGNAL

# Запустите скрипт настройки
./setup_github_secrets.sh
```

#### **📝 Способ 3: Ручная настройка**
Перейдите в [GitHub Secrets](https://github.com/djoni82/SIGNAL/settings/secrets/actions) и добавьте ключи из [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md).

### **2. Запуск проекта**

После настройки всех ключей:

```bash
# Сделайте push в main ветку
git push origin main
```

### **3. Проверка работы**

1. Перейдите в [Actions](https://github.com/djoni82/SIGNAL/actions)
2. Проверьте, что CI/CD pipeline запустился
3. Дождитесь успешного завершения всех шагов

## 🔧 **Локальный запуск (для разработки)**

### **1. Установка зависимостей**

```bash
# Клонируйте репозиторий
git clone https://github.com/djoni82/SIGNAL.git
cd SIGNAL

# Установите зависимости
pip install -r requirements.txt
```

### **2. Настройка переменных окружения**

Создайте файл `.env`:

```bash
# Основные настройки
TELEGRAM_TOKEN=8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg
TELEGRAM_CHAT_ID=5333574230
CRYPTOPANIC_TOKEN=free

# База данных
POSTGRES_PASSWORD=cryptoalpha123
POSTGRES_DB=cryptoalpha
POSTGRES_USER=cryptoalpha

# Мониторинг
GRAFANA_PASSWORD=admin123
PROMETHEUS_ENABLED=true

# Безопасность
ENCRYPTION_KEY=cryptoalpha_encryption_key_32_chars
JWT_SECRET=cryptoalpha_jwt_secret_key_2024

# Конфигурация бота
BOT_MODE=production
LOG_LEVEL=INFO
MAX_LEVERAGE=50
MIN_LEVERAGE=1
```

### **3. Запуск бота**

```bash
# Основной бот
python full_featured_bot.py

# Или простой бот
python enhanced_signal_bot.py

# Или тестовый бот
python test_simple.py
```

## 🐳 **Docker запуск**

### **1. Сборка и запуск**

```bash
# Сборка образа
docker build -t cryptoalpha-signal-bot .

# Запуск контейнера
docker run -d --name signal-bot cryptoalpha-signal-bot

# Или с docker-compose
docker-compose up -d
```

### **2. Проверка логов**

```bash
# Просмотр логов
docker logs signal-bot

# Следить за логами в реальном времени
docker logs -f signal-bot
```

## 📱 **Telegram команды**

После запуска бота используйте команды:

- `/startbot` - Запустить бота
- `/stopbot` - Остановить бота
- `/status` - Статус бота
- `/signals` - Последние сигналы
- `/pairs` - Список пар
- `/addpair BTCUSDT` - Добавить пару
- `/help` - Справка

## 🔍 **Мониторинг**

### **1. Grafana Dashboard**
- URL: `http://localhost:3000`
- Логин: `admin`
- Пароль: `admin123`

### **2. Prometheus Metrics**
- URL: `http://localhost:9090`

### **3. Логи приложения**
```bash
# Просмотр логов
tail -f logs/signal_bot.log

# Поиск ошибок
grep "ERROR" logs/signal_bot.log
```

## 🚨 **Устранение неполадок**

### **Проблема: Бот не запускается**
```bash
# Проверьте логи
docker logs signal-bot

# Проверьте переменные окружения
echo $TELEGRAM_TOKEN

# Перезапустите контейнер
docker restart signal-bot
```

### **Проблема: Нет сигналов**
```bash
# Проверьте API ключи
python test_simple.py

# Проверьте настройки фильтров
# Уменьшите min_confidence в конфигурации
```

### **Проблема: Ошибки подключения**
```bash
# Проверьте сеть
ping api.binance.com

# Проверьте DNS
nslookup api.binance.com

# Перезапустите Docker
docker system prune -a
```

## 📊 **Производительность**

### **Рекомендуемые настройки сервера:**
- **CPU:** 2+ ядра
- **RAM:** 4+ GB
- **Диск:** 20+ GB SSD
- **Сеть:** Стабильное интернет-соединение

### **Оптимизация:**
```bash
# Увеличьте лимиты Docker
docker run --memory=2g --cpus=2 cryptoalpha-signal-bot

# Настройте логирование
export LOG_LEVEL=WARNING
```

## 🔗 **Полезные ссылки**

- **GitHub Repository:** https://github.com/djoni82/SIGNAL
- **GitHub Actions:** https://github.com/djoni82/SIGNAL/actions
- **GitHub Secrets:** https://github.com/djoni82/SIGNAL/settings/secrets/actions
- **Issues:** https://github.com/djoni82/SIGNAL/issues
- **Telegram Bot:** @your_bot_username

## 📞 **Поддержка**

Если возникли проблемы:

1. Проверьте [Issues](https://github.com/djoni82/SIGNAL/issues)
2. Создайте новый Issue с подробным описанием
3. Приложите логи и скриншоты
4. Укажите версию Python и ОС

## ✅ **Чек-лист запуска**

- [ ] GitHub Actions Secrets настроены
- [ ] CI/CD pipeline прошел успешно
- [ ] Telegram бот отвечает на команды
- [ ] Сигналы генерируются
- [ ] Мониторинг работает
- [ ] Логи не содержат ошибок

---

**🎉 Поздравляем! Ваш CryptoAlphaPro Signal Bot готов к работе!** 🚀 