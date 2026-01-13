#!/bin/bash
# Auto-Start Setup Script for SignalPro Bot
# This script configures the bot to automatically start on system boot/login

set -e

echo "🚀 Setting up SignalPro Bot Auto-Start..."

# Create LaunchAgent plist
PLIST_PATH="$HOME/Library/LaunchAgents/com.signalpro.bot.plist"
SIGNAL_DIR="/Users/zhakhongirkuliboev/SIGNAL"

# Ensure LaunchAgents directory exists
mkdir -p "$HOME/Library/LaunchAgents"

# Create the plist file
cat > "$PLIST_PATH" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.signalpro.bot</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /Users/zhakhongirkuliboev/SIGNAL && ./persistent_bot.sh > watchdog.log 2>&1</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/zhakhongirkuliboev/SIGNAL/launchd.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/zhakhongirkuliboev/SIGNAL/launchd_error.log</string>
    
    <key>WorkingDirectory</key>
    <string>/Users/zhakhongirkuliboev/SIGNAL</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
    </dict>
    
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

echo "✅ Created LaunchAgent plist at: $PLIST_PATH"

# Unload existing agent if running
launchctl unload "$PLIST_PATH" 2>/dev/null || true

# Load the new agent
launchctl load "$PLIST_PATH"

echo "✅ LaunchAgent loaded successfully"

# Start the bot immediately
launchctl start com.signalpro.bot

echo ""
echo "🎉 Auto-start configured successfully!"
echo ""
echo "The bot will now:"
echo "  • Start automatically when you log in"
echo "  • Restart automatically if it crashes"
echo "  • Survive system reboots"
echo ""
echo "To check status:"
echo "  launchctl list | grep signalpro"
echo ""
echo "To stop auto-start:"
echo "  launchctl unload ~/Library/LaunchAgents/com.signalpro.bot.plist"
echo ""
echo "To re-enable auto-start:"
echo "  launchctl load ~/Library/LaunchAgents/com.signalpro.bot.plist"
