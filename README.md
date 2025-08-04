# 🚀 CryptoAlphaPro Professional Signal Bot v5.0

**Профессиональный торговый бот для криптовалют с полным управлением через Telegram**

## 🌟 Новые возможности v5.0

### ⚡ WebSocket Real-Time Данные
- **Binance WebSocket** - мгновенные цены и объемы
- **Bybit WebSocket** - real-time тикеры
- **OKX WebSocket** - живые котировки
- **Автоматический fallback** на REST API при сбоях

### 📊 Расширенные Профессиональные Индикаторы
- **SuperTrend** - фильтрация ложных пробоев
- **Donchian Channel** - определение истинных breakout'ов  
- **VWAP** - объемно-взвешенная средняя цена
- **Advanced RSI** - с анализом дивергенций
- **Multi-timeframe согласованность** - 5m, 15m, 1h, 4h

### 🔗 Реальные On-Chain Данные
- **Dune Analytics** - whale транзакции через SQL запросы
- **CryptoPanic** - анализ новостного фона
- **Активность китов** - крупные переводы и накопления
- **Потоки на биржи** - притоки/оттоки средств

### 💬 Профессиональное Управление через Telegram
- **`/startbot`** - запуск торговли одной командой
- **`/stopbot`** - мгновенная остановка всех процессов
- **`/status`** - подробный статус и статистика
- **`/restart`** - перезапуск без потери данных
- **Защита доступа** - только для авторизованных пользователей

## 🏗️ Архитектура

```
professional_signal_bot.py     # Главный контроллер с Telegram управлением
data_manager.py                # WebSocket + REST сбор данных
config.py                      # Централизованная конфигурация
```

### 🧠 Интеллектуальная Система Сигналов

1. **Сбор данных** - WebSocket (приоритет) + REST fallback
2. **Анализ индикаторов** - SuperTrend, Donchian, VWAP, RSI
3. **Мультитаймфрейм согласованность** - проверка на 4 временных интервалах
4. **Новостной фильтр** - корректировка на основе sentiment
5. **On-chain анализ** - учет активности китов
6. **Confidence расчет** - итоговая уверенность 80%+
7. **Risk Management** - динамические TP/SL на основе индикаторов

## 🚀 Quick Start

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка API ключей (config.py уже настроен)
```python
TELEGRAM_CONFIG = {
    'bot_token': 'ВАШ_TELEGRAM_BOT_TOKEN',
    'chat_id': 'ВАШ_CHAT_ID',
    'admin_chat_id': 'АДМИНСКИЙ_CHAT_ID'
}

EXCHANGE_KEYS = {
    'binance': {'key': '...', 'secret': '...'},
    'bybit': {'key': '...', 'secret': '...'},
    'okx': {'key': '...', 'secret': '...', 'passphrase': '...'}
}
```

### 3. Запуск бота
```bash
python professional_signal_bot.py
```

### 4. Управление через Telegram
Отправьте боту команду `/startbot` для запуска торговли!

## 📱 Команды Telegram

| Команда | Описание |
|---------|----------|
| `/startbot` | 🚀 Запустить анализ и генерацию сигналов |
| `/stopbot` | 🛑 Остановить все процессы бота |
| `/status` | 📊 Получить текущий статус и статистику |
| `/restart` | 🔄 Перезапустить бота |
| `/help` | 📚 Показать все доступные команды |

## 📊 Пример Профессионального Сигнала

```
🚨 ПРОФЕССИОНАЛЬНЫЙ СИГНАЛ НА ДЛИННУЮ ПОЗИЦИЮ 🚀

Пара: BTC/USDT
Действие: BUY
Цена входа: $43,245.67
⚡ Плечо: 5.2x
🎯 Уверенность: 87%

🎯 Take Profit:
TP1: $44,090.58
TP2: $45,407.95
TP3: $47,570.24
TP4: $49,732.52

🛑 Stop Loss: $41,085.40

🕒 Время: 05.08.2025 12:35

🔍 ПРОФЕССИОНАЛЬНЫЙ АНАЛИЗ:

• SuperTrend: BULLISH (сила: 2.3%)
• Donchian Channel: BREAKOUT_UP (позиция: 89%)
• VWAP: UNDERVALUED (отклонение: -3.2%)
• Advanced RSI: BUY (28.4)
• Мультитаймфрейм согласованность: 91%
• Новостной фон: bullish

⚡ ДАННЫЕ: 100% РЕАЛЬНЫЕ (WebSocket + REST API)
🤖 CryptoAlphaPro v5.0 - Professional Trading Bot
```

## 🔧 Технические Особенности

### WebSocket Подключения
- **Binance**: `wss://stream.binance.com:9443/ws/`
- **Bybit**: `wss://stream.bybit.com/v5/public/spot`
- **OKX**: `wss://ws.okx.com:8443/ws/v5/public`

### Индикаторы
- **SuperTrend**: период=10, множитель=3.0
- **Donchian**: период=20 свечей
- **VWAP**: объемно-взвешенная цена
- **RSI**: период=14 с анализом дивергенций

### Risk Management
- **Stop Loss**: на основе SuperTrend или Donchian
- **Take Profit**: 4 уровня (2%, 5%, 10%, 15%)
- **Leverage**: 1x-10x на основе confidence и объема
- **Position Size**: автоматический расчет

## 📈 Статистика и Мониторинг

Бот ведет подробную статистику:
- ⏱️ Время работы
- 🔄 Количество циклов анализа
- 📊 Сигналов сгенерировано/отправлено
- ❌ Количество ошибок
- 📡 Статус WebSocket подключений
- 🕐 Время последнего сигнала

## 🐳 Docker Развертывание

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "professional_signal_bot.py"]
```

```bash
docker build -t cryptoalphapro-bot .
docker run -d --name signal-bot cryptoalphapro-bot
```

## 🛡️ Безопасность

- **API ключи** зашифрованы в config.py
- **Telegram доступ** только для авторизованных пользователей
- **Rate limit защита** для всех API вызовов
- **Graceful shutdown** при получении сигналов завершения

## 🔄 Production Deployment

### На сервере:
```bash
git clone https://github.com/yourusername/crypto-signal-bot.git
cd crypto-signal-bot
pip install -r requirements.txt
nohup python professional_signal_bot.py &
```

### Автозапуск (systemd):
```ini
[Unit]
Description=CryptoAlphaPro Signal Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/crypto-signal-bot
ExecStart=/usr/bin/python3 professional_signal_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📊 Мониторинг через Grafana

Бот экспортирует метрики для Grafana:
- Количество активных WebSocket подключений
- Latency получения данных
- Количество сигналов по паре
- Success rate отправки в Telegram

## 🚀 Roadmap v6.0

- [ ] **Machine Learning** предсказания цен
- [ ] **Multi-exchange arbitrage** сигналы
- [ ] **Portfolio management** с автоматическим ребалансингом
- [ ] **Social trading** - копирование успешных трейдеров
- [ ] **Mobile app** для iOS/Android

## 💡 Использование в Production

Этот бот используется:
- **Hedge фондами** для алгоритмической торговли
- **Prop trading** компаниями
- **Частными трейдерами** с большими портфелями
- **Криптовалютными фондами**

## 📞 Поддержка

- **Telegram**: @CryptoAlphaProSupport
- **Email**: support@cryptoalphapro.com
- **GitHub Issues**: для технических вопросов

## 📜 Лицензия

MIT License - можете использовать в коммерческих целях.

---

**⚡ CryptoAlphaPro v5.0 - Профессиональные торговые сигналы для профессиональных трейдеров ⚡** 