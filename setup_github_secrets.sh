#!/bin/bash

# Скрипт для настройки GitHub Actions Secrets
# Требует установленный GitHub CLI (gh)

echo "🔑 Настройка GitHub Actions Secrets для CryptoAlphaPro Signal Bot"
echo "=" * 70

# Проверяем, установлен ли GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI не установлен. Установите его:"
    echo "   macOS: brew install gh"
    echo "   Ubuntu: sudo apt install gh"
    echo "   Windows: winget install GitHub.cli"
    exit 1
fi

# Проверяем авторизацию
if ! gh auth status &> /dev/null; then
    echo "❌ Не авторизован в GitHub CLI. Выполните: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI готов к работе"

# Основные API ключи
echo ""
echo "🔐 Настройка основных API ключей..."

# Telegram
gh secret set TELEGRAM_TOKEN --body "8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg" --repo djoni82/SIGNAL
echo "✅ TELEGRAM_TOKEN добавлен"

gh secret set TELEGRAM_CHAT_ID --body "5333574230" --repo djoni82/SIGNAL
echo "✅ TELEGRAM_CHAT_ID добавлен"

# CryptoPanic (бесплатный API)
gh secret set CRYPTOPANIC_TOKEN --body "free" --repo djoni82/SIGNAL
echo "✅ CRYPTOPANIC_TOKEN добавлен"

# Dune Analytics (заглушка)
gh secret set DUNE_API_KEY --body "your_dune_api_key_here" --repo djoni82/SIGNAL
echo "✅ DUNE_API_KEY добавлен (заглушка)"

# Twitter (заглушка)
gh secret set TWITTER_BEARER_TOKEN --body "your_twitter_bearer_token" --repo djoni82/SIGNAL
echo "✅ TWITTER_BEARER_TOKEN добавлен (заглушка)"

# Docker ключи
echo ""
echo "🐳 Настройка Docker ключей..."

gh secret set DOCKER_USERNAME --body "your_docker_username" --repo djoni82/SIGNAL
echo "✅ DOCKER_USERNAME добавлен (заглушка)"

gh secret set DOCKER_PASSWORD --body "your_docker_password" --repo djoni82/SIGNAL
echo "✅ DOCKER_PASSWORD добавлен (заглушка)"

# База данных
echo ""
echo "🗄️ Настройка базы данных..."

gh secret set POSTGRES_PASSWORD --body "cryptoalpha123" --repo djoni82/SIGNAL
echo "✅ POSTGRES_PASSWORD добавлен"

gh secret set POSTGRES_DB --body "cryptoalpha" --repo djoni82/SIGNAL
echo "✅ POSTGRES_DB добавлен"

gh secret set POSTGRES_USER --body "cryptoalpha" --repo djoni82/SIGNAL
echo "✅ POSTGRES_USER добавлен"

# Мониторинг
echo ""
echo "📊 Настройка мониторинга..."

gh secret set GRAFANA_PASSWORD --body "admin123" --repo djoni82/SIGNAL
echo "✅ GRAFANA_PASSWORD добавлен"

gh secret set PROMETHEUS_ENABLED --body "true" --repo djoni82/SIGNAL
echo "✅ PROMETHEUS_ENABLED добавлен"

# Безопасность
echo ""
echo "🔒 Настройка безопасности..."

gh secret set ENCRYPTION_KEY --body "cryptoalpha_encryption_key_32_chars" --repo djoni82/SIGNAL
echo "✅ ENCRYPTION_KEY добавлен"

gh secret set JWT_SECRET --body "cryptoalpha_jwt_secret_key_2024" --repo djoni82/SIGNAL
echo "✅ JWT_SECRET добавлен"

# Конфигурация бота
echo ""
echo "⚙️ Настройка конфигурации бота..."

gh secret set BOT_MODE --body "production" --repo djoni82/SIGNAL
echo "✅ BOT_MODE добавлен"

gh secret set LOG_LEVEL --body "INFO" --repo djoni82/SIGNAL
echo "✅ LOG_LEVEL добавлен"

gh secret set MAX_LEVERAGE --body "50" --repo djoni82/SIGNAL
echo "✅ MAX_LEVERAGE добавлен"

gh secret set MIN_LEVERAGE --body "1" --repo djoni82/SIGNAL
echo "✅ MIN_LEVERAGE добавлен"

# Дополнительные настройки
echo ""
echo "🔧 Дополнительные настройки..."

gh secret set MONITORING_INTERVAL --body "300" --repo djoni82/SIGNAL
echo "✅ MONITORING_INTERVAL добавлен"

gh secret set SIGNAL_GENERATION_INTERVAL --body "60" --repo djoni82/SIGNAL
echo "✅ SIGNAL_GENERATION_INTERVAL добавлен"

gh secret set DEFAULT_SL_PERCENT --body "2.0" --repo djoni82/SIGNAL
echo "✅ DEFAULT_SL_PERCENT добавлен"

gh secret set DEFAULT_TP_PERCENT --body "6.0" --repo djoni82/SIGNAL
echo "✅ DEFAULT_TP_PERCENT добавлен"

echo ""
echo "🎉 Все GitHub Actions Secrets настроены!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Замените заглушки на реальные ключи:"
echo "   - DUNE_API_KEY"
echo "   - TWITTER_BEARER_TOKEN"
echo "   - DOCKER_USERNAME"
echo "   - DOCKER_PASSWORD"
echo ""
echo "2. Проверьте настройки:"
echo "   https://github.com/djoni82/SIGNAL/settings/secrets/actions"
echo ""
echo "3. Запустите CI/CD pipeline:"
echo "   git push origin main"
echo ""
echo "🔗 Полезные ссылки:"
echo "• GitHub Secrets: https://github.com/djoni82/SIGNAL/settings/secrets/actions"
echo "• Actions: https://github.com/djoni82/SIGNAL/actions"
echo "• Issues: https://github.com/djoni82/SIGNAL/issues"
echo ""
echo "✅ Проект готов к автоматическому деплою!" 