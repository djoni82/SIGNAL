# 🔑 Руководство по API ключам для CryptoAlphaPro

## Обязательные API ключи для работы бота:

### 🏦 **Криптобиржи** (минимум 1, рекомендуется все 3)

#### 1. **Binance API**
- Регистрация: https://www.binance.com/en/binance-api
- Переход: Профиль → API Management → Create API
- Права: Spot Trading (чтение), Futures Trading (чтение)
- Ключи: `BINANCE_API_KEY`, `BINANCE_SECRET`

#### 2. **Bybit API** 
- Регистрация: https://www.bybit.com/app/user/api-management
- Права: Contract Trading (чтение), Spot Trading (чтение)
- Ключи: `BYBIT_API_KEY`, `BYBIT_SECRET`

#### 3. **OKX API**
- Регистрация: https://www.okx.com/account/my-api
- Права: Trading (чтение), Spot Trading
- Ключи: `OKX_API_KEY`, `OKX_SECRET`, `OKX_PASSPHRASE`

### 📱 **Telegram Bot**
- Создание: https://t.me/BotFather
- Команды: `/newbot` → название → username
- Получение Chat ID: отправьте сообщение боту, затем:
  ```
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
  ```
- Ключи: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### 📊 **Данные и аналитика**

#### 1. **Dune Analytics** (On-chain данные)
- Регистрация: https://dune.com/api
- План: Premium ($390/мес) или Enterprise
- Ключ: `DUNE_API_KEY`

#### 2. **CryptoPanic** (Новости)
- Регистрация: https://cryptopanic.com/developers/api/
- План: Free (500 запросов/день) или Pro ($29/мес)
- Ключ: `CRYPTOPANIC_API_KEY`

#### 3. **Twitter API v2** (Социальные сигналы)
- Регистрация: https://developer.twitter.com/en/portal/dashboard
- План: Basic ($100/мес) или Pro ($5000/мес)
- Ключи: `TWITTER_BEARER_TOKEN`, `TWITTER_API_KEY`, `TWITTER_API_SECRET`

### 🔐 **Базы данных**
```env
TIMESCALE_PASSWORD=secure_password_123
POSTGRES_PASSWORD=secure_password_456
REDIS_PASSWORD=secure_password_789
RABBITMQ_PASSWORD=secure_password_000
GRAFANA_ADMIN_PASSWORD=admin_password_321
```

## 💰 **Приблизительная стоимость API ключей в месяц:**

| Сервис | Free план | Paid план | Рекомендуемый |
|--------|-----------|-----------|---------------|
| Binance | ✅ Да (лимиты) | - | Free |
| Bybit | ✅ Да (лимиты) | - | Free |
| OKX | ✅ Да (лимиты) | - | Free |
| Telegram | ✅ Бесплатно | - | Free |
| Dune Analytics | ❌ Нет | $390/мес | Premium |
| CryptoPanic | ✅ 500 req/день | $29/мес | Pro |
| Twitter API | ❌ Нет | $100/мес | Basic |

**Общая стоимость: ~$519/месяц** для полного функционала

## 🎯 **Минимальная конфигурация для тестов:**

Для начального тестирования можно использовать:
- 1 биржа (Binance) - **Бесплатно**
- Telegram Bot - **Бесплатно** 
- CryptoPanic Free - **Бесплатно**
- Mock данные для остального

## 📝 **Создание .env файла:**

```bash
# Скопируйте этот шаблон в файл .env
cp API_KEYS_GUIDE.md .env

# Затем отредактируйте .env и вставьте ваши ключи:
nano .env
```

## ⚠️ **Безопасность:**
- Никогда не коммитьте .env файл в Git
- Используйте разные ключи для разработки и продакшена
- Регулярно обновляйте пароли (каждые 90 дней)
- Ограничьте права API ключей до минимально необходимых 