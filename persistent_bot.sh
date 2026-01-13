#!/bin/bash
# persistent_bot.sh - Script to keep SignalPro running 24/7

echo "🚀 Starting SignalPro Watchdog..."
echo "Logs will be available in bot.log"

while true; do
    echo "[$(date)] Starting main.py..."
    # Run the bot and wait for it to finish
    ./.venv/bin/python main.py >> bot.log 2>&1
    
    EXIT_CODE=$?
    echo "[$(date)] Bot exited with code $EXIT_CODE. Restarting in 10 seconds..."
    sleep 10
done
