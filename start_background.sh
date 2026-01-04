#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 Starting SignalPro Bot in background..."
nohup ./run.sh > bot.log 2>&1 &
PID=$!
echo "✅ Bot started! PID: $PID"
echo "📄 Logs are being written to: bot.log"
echo "To stop the bot, run: kill $PID"
echo "To watch logs, run: tail -f bot.log"
