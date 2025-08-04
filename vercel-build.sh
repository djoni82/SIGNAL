#!/bin/bash

# Простой скрипт сборки для Vercel
echo "🚀 Building CryptoAlphaPro Signal Bot..."

# Проверяем наличие основных файлов
if [ -f "index.html" ]; then
    echo "✅ index.html found"
else
    echo "❌ index.html not found"
    exit 1
fi

if [ -f "package.json" ]; then
    echo "✅ package.json found"
else
    echo "❌ package.json not found"
    exit 1
fi

echo "🎉 Build completed successfully!"
echo "📱 Telegram Bot: @cryptoalpha_bot"
echo "🔗 Repository: https://github.com/djoni82/SIGNAL" 