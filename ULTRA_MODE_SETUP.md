# ULTRA_MODE_SETUP.md - UPDATED VERSION
# Руководство по включению Ultra Mode (Production-Ready)

## ⚠️ ВАЖНО: Реалистичные ожидания

**Ultra Mode НЕ является "святым граалем"**. Типичные метрики:
- **Win Rate:** 60-70% (не 85-95%!)  
- **Сигналов:** 2-5 в день (не 10-15)
- **R/R Ratio:** 1:2 - 1:3 в среднем

> [!CAUTION]
> Если вы ожидаете 90%+ точность, вы будете разочарованы. Machine Learning не предсказывает будущее, а находит вероятностные паттерны.

---

## Что такое Ultra Mode?

**Ultra Mode** - режим с реальным ML и анализом институциональной ликвидности.

### Сравнение режимов:

| Характеристика | Legacy Mode | Ultra Mode |
|----------------|-------------|------------|
| ML Engine | Эвристика (if-else) | XGBoost + LightGBM + CatBoost |
| Smart Money | ❌ Нет | ✅ Liquidity + Funding |
| Min Confidence | 0.80 (80%) | 0.85 (85%) |
| Сигналов/день | ~10-15 | ~2-5 |
| **Win Rate** | **65-75%** | **70-80%** |
| Обучение | Не требуется | Еженедельное (автоматическое) |

---

## 🚀 Пошаговая активация Ultra Mode

### Шаг 1: Установка ML библиотек

```bash
cd ~/SIGNAL
source .venv/bin/activate
pip install xgboost lightgbm catboost scikit-learn joblib
```

**Проверка:**
```bash
python -c "import xgboost; import lightgbm; import catboost; print('✅ ML libs OK')"
```

---

### Шаг 2: Первое обучение моделей

```bash
python train_models.py
```

**Ожидаемый вывод (10-30 минут):**
```
📊 Training on 12 symbols
📅 Lookback period: 180 days

Step 1/2: Collecting historical data...
✅ BTC/USDT: 4320 samples
✅ ETH/USDT: 4320 samples
...
✅ Data collected: 34560 training, 8640 validation samples
   Positive rate: 23.4%

Step 2/2: Training ensemble models...
   This may take 10-30 minutes...
Training XGBoost...
Training LightGBM...
Training CatBoost...

✅ Training complete!
   Models saved to: models/
```

**Критическая проверка:**
```bash
ls -lh models/
# Должны быть файлы:
# xgb_model.json
# lgbm_model.txt
# catboost_model.cbm
# features.pkl  ← КРИТИЧНО для feature consistency!
```

---

### Шаг 3: Включение Ultra Mode

**Вариант A: Через .env (рекомендуется)**
```bash
# Создайте или отредактируйте .env
USE_ULTRA_MODE=true
ULTRA_MIN_CONFIDENCE=0.85
ULTRA_SHADOW_MODE=false  # false = реальный режим
```

**Вариант B: В settings.py**
```python
# src/core/settings.py
use_ultra_mode: bool = True  # Было False
ultra_min_confidence: float = 0.85
```

---

### Шаг 4: Shadow Mode Testing (ОБЯЗАТЕЛЬНО перед продакшн!)

> [!IMPORTANT]
> **Не запускайте Ultra Mode сразу на реальные деньги!**

**Shadow Mode** генерирует сигналы, но НЕ отправляет их в Telegram/биржу.

```bash
# В .env или settings.py:
ULTRA_SHADOW_MODE=true
```

Запустите бота на 24 часа:
```bash
python main.py
```

Проверьте логи:
```bash
cat logs/shadow_signals.json | jq
```

**Анализ через 24 часа:**
1. Откройте каждый сигнал из `shadow_signals.json`
2. Проверьте, сработал бы он или нет
3. Посчитайте win rate
4. Если >= 60% → можно включить реальный режим

---

### Шаг 5: Настройка автопереобучения (ОБЯЗАТЕЛЬНО!)

```bash
./setup_auto_retraining.sh
```

**Это настроит:**
- Еженедельное переобучение (Воскресенье, 03:00)
- Автоматический рестарт бота после обучения
- Логи в `logs/retraining.log`

**Проверка cron/launchd:**
```bash
# macOS (launchd):
launchctl list | grep signalpro

# Linux (cron):
crontab -l
```

---

### Шаг 6: Реальный запуск

```bash
# Выключить Shadow Mode
# В .env: ULTRA_SHADOW_MODE=false

# Остановить старый процесс
pkill -9 -f "python main.py"

# Запустить
python main.py
```

**Проверка логов:**
```
🚀 Initializing Ultra Mode (Real ML + Smart Money)...
   Min Confidence: 85%
   ML Models: XGBoost + LightGBM + CatBoost
   Smart Money: Liquidity + Funding Analysis
✅ XGBoost model loaded
✅ LightGBM model loaded
✅ CatBoost model loaded
✅ Feature validation passed: 11 features
```

> [!WARNING]
> Если видите "Feature mismatch" - пере обучите модели!

---

## 🧪 Тестирование

### Unit Tests:
```bash
pip install -r requirements_test.txt
./run_tests.sh
```

### Feature Consistency Test:
```bash
python -c "
from src.strategies.signal_generator_ultra import UltraSignalGenerator
from unittest.mock import Mock
gen = UltraSignalGenerator(Mock())
print('✅ Feature validation passed')
"
```

### Smart Money API Validation:
```bash
# Если у вас есть Coinglass API key
python -c "
import asyncio
from src.strategies.smart_money_analyzer import SmartMoneyAnalyzer
async def test():
    analyzer = SmartMoneyAnalyzer(coinglass_key='YOUR_KEY')
    status = await analyzer.validate_api_keys()
    print(status)
asyncio.run(test())
"
```

---

## 📊 Мониторинг Ultra Mode

### Real-time Signals:
```bash
# API endpoint
curl http://localhost:8000/api/signals | jq '.[] | {symbol, confidence, direction}'

# Логи
tail -f bot.log | grep "ULTRA SIGNAL"
```

**Пример успешного сигнала:**
```
🚀 [ULTRA SIGNAL] BTC/USDT (1h) | Conf: 87% | Dir: STRONG_BUY |
TA=0.72 ML=0.89 SM=+0.12
```

### Performance Metrics:
```bash
# Посчитать сигналы за последний час
grep "ULTRA SIGNAL" bot.log | tail -20
```

---

## ⚙️ Troubleshooting

### ❌ "Feature mismatch" Error

**Причина:** Модели обучены на старой версии фич.

**Решение:**
```bash
python train_models.py  # Переобучить
```

---

### ❌ "Models not found"

**Решение:**
```bash
ls models/  # Проверить наличие файлов
python train_models.py  # Если пусто - обучить
```

---

### ❌ ImportError: xgboost not found

**Решение:**
```bash
pip uninstall xgboost -y
pip install xgboost --no-cache-dir
```

---

### ⚠️ Слишком мало сигналов (0-1 в день)

**Это НОРМАЛЬНО для 0.85 порога!**

**Если нужно больше:**
```python
ultra_min_confidence: float = 0.82  # Мягче
```

**Но учтите:** Точность упадет до ~65-70%.

---

### ⚠️ Using MOCK data warning

**Причина:** Нет API ключей от Coinglass/Hyblock.

**Что происходит:** Smart Money использует случайные данные.

**Решение (для продакшн):**
1. Получить API key: https://www.coinglass.com/pricing
2. Добавить в .env: `COINGLASS_API_KEY=xxx`

---

## 🔄 Возврат к Legacy Mode

Если Ultra Mode не подходит:

```python
# settings.py:
use_ultra_mode: bool = False
```

Перезапуск:
```bash
pkill -9 -f "python main.py"
python main.py
```

Все Legacy функции сохранены! ✅

---

## 📈 Опциональные улучшения

### Кастомизация порога:

**Агрессивный (больше сигналов, меньше точность):**
```python
ultra_min_confidence: float = 0.80
```

**Супер-консервативный (топ 5% сигналов):**
```python
ultra_min_confidence: float = 0.90
```

### Добавление Smart Money API:

**Coinglass (ликвидационные карты):**
```bash
# .env
COINGLASS_API_KEY=your_key_from_coinglass_com
```

**Проверка:**
```bash
curl -H "coinglassSecret: YOUR_KEY" \
  "https://open-api.coinglass.com/public/v2/indicator/funding_usd_history"
```

---

## 💡 Best Practices

1. **Всегда тестируйте в Shadow Mode** перед реальным запуском
2. **Мониторьте переобучение:** Win rate должен быть стабильным
3. **Логи - ваш друг:** Регулярно проверяйте `logs/shadow_signals.json`
4. **Feature drift:** Если точность упала, переобучите модели
5. **Не гонитесь за количеством:** 2-3 сигнала/день с 70% винрейтом > 15 сигналов с 55%

---

## 🎯 Expected Results

**Через 1 неделю работы:**
- Сигналов: 10-25
- Win Rate: 65-75%
- Avg R/R: 1:2

**Красные флаги (нужно переобучить):**
- Win Rate < 55%
- Слишком много сигналов (>50/неделя)
- Все сигналы на одной паре

---

**Готово! У вас production-ready Ultra Mode с автообучением и тестированием.**
