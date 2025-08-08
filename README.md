# 🚨 UnifiedSignalBot - SignalPro + ScalpingPro

Профессиональный криптовалютный сигнальный бот, объединяющий обычные сигналы и скальпинг в одной системе.

## 🎯 Особенности

### 📊 SignalPro (Обычные сигналы)
- **Таймфреймы**: 15m, 1h, 4h
- **Минимальная уверенность**: 80%
- **Частота обновления**: 5 минут
- **Плечо**: 1x-50x в зависимости от уверенности
- **Формат**: Профессиональные сигналы с детальным анализом

### ⚡ ScalpingPro (Скальпинг)
- **Таймфреймы**: 1m, 5m, 15m
- **Минимальная уверенность**: 60%
- **Частота обновления**: 1 минута
- **Быстрые сигналы** для краткосрочной торговли

## 🔧 Технические индикаторы

- **RSI** (14 периодов) - перекупленность/перепроданность
- **MACD** - трендовые сигналы
- **EMA** (12, 20, 26, 50) - скользящие средние
- **Bollinger Bands** - волатильность и пробои
- **ADX** - сила тренда
- **Volume Ratio** - анализ объема
- **Stochastic Oscillator** - моментум
- **Candlestick Patterns** - свечные паттерны

## 🚀 Логика плеча

| Уверенность | Плечо | Префикс | Описание |
|-------------|-------|---------|----------|
| 96-97% | 50x | STRONG_ | Максимальная уверенность |
| 95%+ | 40x | STRONG_ | Очень высокая уверенность |
| 90%+ | 25x | - | Высокая уверенность |
| 80%+ | 15x | - | Обычная уверенность |

## 📱 Telegram интеграция

### Команды управления:
- `/start` - запуск бота
- `/stop` - остановка бота
- `/status` - статус работы
- `/stats` - статистика
- `/help` - справка

### Формат сигналов:
```
🚨 СИГНАЛ НА ДЛИННУЮ ПОЗИЦИЮ 🚀

Пара: BTC/USDT
Действие: BUY
Цена входа: $43,245.67

🎯 Take Profit:
TP1: $44,090.58
TP2: $45,407.95
TP3: $47,570.24
TP4: $49,732.52

🛑 Stop Loss: $41,085.40

📊 Уровень успеха: 87%
🕒 Время: 05.08.2025 12:35

🔎 Почему сигнал на длинную позицию ❓

Подробности сделки 👇

• RSI сильный > 70 (87.37) - перекупленность
• Смешанный EMA тренд
• Цена ниже MA50
• Сила тренда очень высокая (ADX ≥ 30, 31.1)
• Рост объёма более 163%!
• Обнаружен паттерн «Три черных ворона»
• Подтверждение часового тренда отрицательное
• Подтверждение 4-часового тренда отрицательное
```

## 🛠️ Установка и настройка

### 1. Клонирование репозитория
```bash
git clone https://github.com/djoni82/SIGNAL.git
cd SIGNAL
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка конфигурации
Создайте файл `config.py` с вашими API ключами:

```python
TELEGRAM_CONFIG = {
    'bot_token': 'ВАШ_TELEGRAM_BOT_TOKEN',
    'chat_id': 'ВАШ_CHAT_ID',
    'admin_chat_id': 'АДМИНСКИЙ_CHAT_ID',
    'enable_telegram': True,
    'send_signals': True,
    'send_status': True,
    'send_errors': True,
}

EXCHANGE_KEYS = {
    'binance': {
        'key': 'ВАШ_BINANCE_API_KEY',
        'secret': 'ВАШ_BINANCE_SECRET'
    },
    'bybit': {
        'key': 'ВАШ_BYBIT_API_KEY',
        'secret': 'ВАШ_BYBIT_SECRET'
    },
    'okx': {
        'key': 'ВАШ_OKX_API_KEY',
        'secret': 'ВАШ_OKX_SECRET',
        'passphrase': 'ВАШ_OKX_PASSPHRASE'
    }
}

EXTERNAL_APIS = {
    'dune': {
        'api_key': 'ВАШ_DUNE_API_KEY',
        'base_url': 'https://api.dune.com/api/v1',
        'query_id': 'ВАШ_QUERY_ID'
    },
    'crypto_panic': {
        'api_key': 'ВАШ_CRYPTOPANIC_API_KEY',
        'base_url': 'https://cryptopanic.com/api/v1'
    },
    'coingecko': {
        'base_url': 'https://api.coingecko.com/api/v3'
    }
}

TRADING_CONFIG = {
    'pairs': [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
        'XRP/USDT', 'DOT/USDT', 'DOGE/USDT', 'AVAX/USDT', 'MATIC/USDT',
        # ... добавьте нужные пары
    ],
    'timeframes': ['15m', '1h', '4h'],
    'update_frequency': 300,  # 5 минут
    'min_confidence': 0.8,    # 80%
    'top_signals': 5
}
```

### 4. Запуск бота
```bash
python unified_signal_bot.py
```

## 🐳 Docker развертывание

### Создание Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "unified_signal_bot.py"]
```

### Сборка и запуск
```bash
docker build -t unified-signal-bot .
docker run -d --name signal-bot unified-signal-bot
```

## 📊 Мониторинг

Бот ведет подробную статистику:
- ⏱️ Время работы
- 🔄 Количество циклов анализа
- 📊 Сигналов сгенерировано/отправлено
- ❌ Количество ошибок
- 🎯 Успешность сигналов

## 🔒 Безопасность

- API ключи хранятся в отдельном файле config.py
- Telegram доступ только для авторизованных пользователей
- Rate limit защита для всех API вызовов
- Graceful shutdown при получении сигналов завершения

## 📈 Статистика использования

- **200+ торговых пар** для анализа
- **3 биржи** (Binance, Bybit, OKX)
- **5 таймфреймов** (1m, 5m, 15m, 1h, 4h)
- **Реальные данные** через ccxt API
- **On-chain анализ** через Dune Analytics

## 🚀 Roadmap

- [ ] Machine Learning предсказания
- [ ] Multi-exchange arbitrage
- [ ] Portfolio management
- [ ] Mobile app
- [ ] Web dashboard

## 📞 Поддержка

- **GitHub Issues**: для технических вопросов
- **Telegram**: @CryptoAlphaProSupport

## 📜 Лицензия

MIT License - можете использовать в коммерческих целях.

---

**⚡ UnifiedSignalBot - Профессиональные торговые сигналы для профессиональных трейдеров ⚡** 