#!/bin/bash

echo "🚀 Настройка Vercel для CryptoAlphaPro Signal Bot"
echo "=" * 60

echo "📋 Проверка файлов..."
if [ -f "index.html" ]; then
    echo "✅ index.html найден"
else
    echo "❌ index.html не найден"
    exit 1
fi

if [ -f "vercel.json" ]; then
    echo "✅ vercel.json найден"
else
    echo "❌ vercel.json не найден"
    exit 1
fi

if [ -f "package.json" ]; then
    echo "✅ package.json найден"
else
    echo "❌ package.json не найден"
    exit 1
fi

echo ""
echo "🔧 Инструкции по настройке Vercel:"
echo ""
echo "1. Откройте https://vercel.com/dashboard"
echo "2. Нажмите 'Add New...' → 'Project'"
echo "3. Найдите репозиторий 'djoni82/SIGNAL'"
echo "4. Если нет в списке, нажмите 'Import Git Repository'"
echo "5. Введите: https://github.com/djoni82/SIGNAL"
echo "6. Настройте проект:"
echo "   - Project Name: cryptoalpha-signal-bot"
echo "   - Framework Preset: Other"
echo "   - Root Directory: ./ (оставьте пустым)"
echo "   - Build Command: оставьте пустым"
echo "   - Output Directory: оставьте пустым"
echo "   - Install Command: оставьте пустым"
echo "7. Нажмите 'Deploy'"
echo ""
echo "🎯 Ожидаемый результат:"
echo "- Сайт: https://cryptoalpha-signal-bot.vercel.app"
echo "- Landing page с информацией о боте"
echo "- Telegram Bot: @cryptoalpha_bot"
echo ""
echo "📱 Telegram данные:"
echo "- Token: 8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg"
echo "- Chat ID: 5333574230"
echo ""
echo "🔗 Полезные ссылки:"
echo "- GitHub: https://github.com/djoni82/SIGNAL"
echo "- Actions: https://github.com/djoni82/SIGNAL/actions"
echo ""
echo "🎉 После настройки Vercel будет работать!" 