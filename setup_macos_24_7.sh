#!/bin/bash
# macOS-совместимый скрипт для запуска бота 24/7
# (systemd не работает на macOS, используем launchd)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Настройка SignalPro для работы 24/7 на macOS..."

# Убиваем старые процессы
pkill -9 -f "python main.py"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Создаем plist файл для launchd (macOS аналог systemd)
cat > ~/Library/LaunchAgents/com.signalpro.bot.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.signalpro.bot</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/zhakhongirkuliboev/SIGNAL/.venv/bin/python</string>
        <string>/Users/zhakhongirkuliboev/SIGNAL/main.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/zhakhongirkuliboev/SIGNAL</string>
    
    <key>StandardOutPath</key>
    <string>/Users/zhakhongirkuliboev/SIGNAL/bot.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/zhakhongirkuliboev/SIGNAL/bot_error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ Создан файл launchd: ~/Library/LaunchAgents/com.signalpro.bot.plist"

# Загружаем service
launchctl unload ~/Library/LaunchAgents/com.signalpro.bot.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.signalpro.bot.plist

echo ""
echo "✅ Бот запущен в фоне и будет автоматически запускаться при загрузке macOS!"
echo ""
echo "📋 Команды управления:"
echo "   Статус:      launchctl list | grep signalpro"
echo "   Остановить:  launchctl unload ~/Library/LaunchAgents/com.signalpro.bot.plist"
echo "   Запустить:   launchctl load ~/Library/LaunchAgents/com.signalpro.bot.plist"
echo "   Логи:        tail -f ~/SIGNAL/bot.log"
echo "   Ошибки:      tail -f ~/SIGNAL/bot_error.log"
