#!/bin/bash
# auto_retrain_scheduler.sh
# Автоматическое переобучение моделей каждую неделю

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  SignalPro Ultra - Auto Retraining"
echo "  Started: $(date)"
echo "=========================================="

# Активируем виртуальное окружение
source .venv/bin/activate

# Запускаем переобучение
python train_models.py >> logs/retraining.log 2>> logs/retraining_error.log

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Retraining successful at $(date)" >> logs/retraining.log
    
    # Перезапускаем бота если он работает
    if [ -f bot.pid ] && ps -p $(cat bot.pid) > /dev/null 2>&1; then
        echo "🔄 Restarting bot with new models..." >> logs/retraining.log
        kill -HUP $(cat bot.pid) || true
        sleep 5
        ./start_bot_24_7.sh
    fi
else
    echo "❌ Retraining failed at $(date) with code $EXIT_CODE" >> logs/retraining_error.log
fi

echo "=========================================="
echo "  Finished: $(date)"
echo "=========================================="
