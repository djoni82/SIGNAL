#!/bin/bash
# Setup script for CryptoAlphaPro API keys

echo "🔑 Setting up CryptoAlphaPro with your API keys..."

# Create .env file with real API keys
cat > .env << 'ENVEOF'
# CryptoAlphaPro Production API Keys
# ======================
# DATABASES
# ======================
TIMESCALE_PASSWORD=crypto_alpha_pro_2024
POSTGRES_PASSWORD=crypto_alpha_pro_2024
REDIS_PASSWORD=crypto_alpha_pro_2024
RABBITMQ_PASSWORD=crypto_alpha_pro_2024
GRAFANA_ADMIN_PASSWORD=crypto_alpha_admin_2024

# ======================
# CRYPTOCURRENCY EXCHANGES
# ======================

# Binance API
BINANCE_API_KEY=UGPsFwnP6Sirw5V1aL3xeOwMr7wzWm1eigxDNb2wrJRs3fWP3QDnOjIwVCeipczV
BINANCE_SECRET=jmA0MyvImfAvMu3KdJ32AkdajzIK2YE1U236KcpiTQRL9ItkM6aqil1jh73XEfPe

# Bybit API
BYBIT_API_KEY=mWoHS9ONHT2EzePncI
BYBIT_SECRET=b3rUJND24b9OPlmmwKo4Qv6E0ipqYUHTXr9x

# OKX API
OKX_API_KEY=a7f94985-9865-495f-a3f9-e681ab17492d
OKX_SECRET=5BE33E5B1802F25F08D28D902EB71970
OKX_PASSPHRASE=Baks1982.

# ======================
# TELEGRAM BOT
# ======================
TELEGRAM_BOT_TOKEN=8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
TELEGRAM_ADMIN_CHAT_ID=YOUR_ADMIN_CHAT_ID

# ======================
# EXTERNAL DATA APIS
# ======================

# Dune Analytics API
DUNE_API_KEY=IpFMlwUDxk9AhUdfgF6vVfvKcldTfF2ay
DUNE_QUERY_ID=5341077

# CryptoPanic News API
CRYPTOPANIC_API_KEY=875f9eb195992389523bcf015c95f315245e395e

# ======================
# ADDITIONAL CONFIGURATION
# ======================

# Trading Settings (NEW: UP TO 50X LEVERAGE)
MAX_LEVERAGE=50
MIN_LEVERAGE=1
DEFAULT_LEVERAGE=5
RISK_TOLERANCE=medium

# Performance Settings
MAX_PROCESSING_TIME_MS=10
CONFIDENCE_THRESHOLD=0.75
SIGNAL_COOLDOWN_SECONDS=30

# ======================
# SECURITY
# ======================
JWT_SECRET_KEY=crypto_alpha_pro_jwt_secret_2024_ultra_secure_key_256_bit
ENCRYPTION_KEY=crypto_alpha_pro_encryption_key_32_byte
ENVEOF

echo "✅ .env file created with your API keys"
echo "⚡ Maximum leverage set to 50x"
echo "🚀 CryptoAlphaPro ready for high-leverage trading!"

# Make the file readable only by owner for security
chmod 600 .env

echo "🔒 .env file secured (600 permissions)"
echo ""
echo "Next steps:"
echo "1. Get your Telegram Chat ID: Send a message to @AlphaSignalProK_bot"
echo "2. Visit: https://api.telegram.org/bot8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg/getUpdates"
echo "3. Update TELEGRAM_CHAT_ID in .env with your chat ID"
echo "4. Run: docker-compose up -d"
