#!/bin/bash
# Скрипт для запуска бота 24/7 в фоновом режиме

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Убиваем старые процессы
pkill -9 -f "python main.py"
pkill -9 -f "uvicorn"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

echo "Запуск SignalPro в фоновом режиме..."

# Активируем виртуальное окружение и запускаем бота в фоне с nohup
nohup .venv/bin/python main.py > bot.log 2> bot_error.log &

# Сохраняем PID
echo $! > bot.pid

echo "Бот запущен! PID: $(cat bot.pid)"
echo "Логи: tail -f bot.log"
echo "Ошибки: tail -f bot_error.log"
echo "Остановить: kill \$(cat bot.pid)"
