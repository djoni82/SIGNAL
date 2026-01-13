#!/bin/bash
# setup_auto_retraining.sh
# Настройка автоматического переобучения для macOS (launchd)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔧 Настройка автоматического переобучения моделей..."

# Создаем директорию для логов
mkdir -p logs

# Делаем скрипт исполняемым
chmod +x auto_retrain_scheduler.sh

# Создаем launchd plist для еженедельного запуска
cat > ~/Library/LaunchAgents/com.signalpro.retrain.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.signalpro.retrain</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_DIR/auto_retrain_scheduler.sh</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/retraining.log</string>
    
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/retraining_error.log</string>
    
    <!-- Запуск каждое воскресенье в 03:00 -->
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

# Загружаем в launchd
launchctl unload ~/Library/LaunchAgents/com.signalpro.retrain.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.signalpro.retrain.plist

echo ""
echo "✅ Автоматическое переобучение настроено!"
echo ""
echo "📅 Расписание: Каждое воскресенье в 03:00"
echo "📋 Логи: $SCRIPT_DIR/logs/retraining.log"
echo ""
echo "🔧 Управление:"
echo "   Статус:      launchctl list | grep signalpro.retrain"
echo "   Остановить:  launchctl unload ~/Library/LaunchAgents/com.signalpro.retrain.plist"
echo "   Запустить:   launchctl load ~/Library/LaunchAgents/com.signalpro.retrain.plist"
echo "   Тест сейчас: ./auto_retrain_scheduler.sh"
echo ""
