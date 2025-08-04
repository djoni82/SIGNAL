#!/usr/bin/env python3
"""
Configuration - Конфигурация для CryptoAlphaPro Bot
"""

# Telegram настройки
TELEGRAM_CONFIG = {
    'bot_token': '8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg',
    'chat_id': '5333574230',
    'admin_chat_id': '5333574230',  # Админский чат для управления ботом
    'enable_telegram': True,  # Включить/выключить Telegram
    'send_signals': True,  # Отправлять сигналы
    'send_status': True,  # Отправлять статус
    'send_errors': True,  # Отправлять ошибки
}

# API ключи для бирж
EXCHANGE_KEYS = {
    'binance': {
        'key': 'UGPsFwnP6Sirw5V1aL3xeOwMr7wzWm1eigxDNb2wrJRs3fWP3QDnOjIwVCeipczV',
        'secret': 'jmA0MyvImfAvMu3KdJ32AkdajzIK2YE1U236KcpiTQRL9ItkM6aqil1jh73XEfPe'
    },
    'bybit': {
        'key': 'mWoHS9ONHT2EzePncI',
        'secret': 'b3rUJND24b9OPlmmwKo4Qv6E0ipqYUHTXr9x'
    },
    'okx': {
        'key': 'a7f94985-9865-495f-a3f9-e681ab17492d',
        'secret': '5BE33E5B1802F25F08D28D902EB71970',
        'passphrase': 'Baks1982.'
    }
}

# Внешние API ключи
EXTERNAL_APIS = {
    'dune': {
        'api_key': 'IpFMlwUDxk9AhUdfgF6vVfvKcldTfF2ay',
        'query_id': 5341077,
        'base_url': 'https://api.dune.com/api/v1'
    },
    'crypto_panic': {
        'api_key': '875f9eb195992389523bcf015c95f315245e395e',
        'base_url': 'https://cryptopanic.com/api/developer/v2'
    },
    'twitter': {
        'api_key': 'your_twitter_api_key_here',
        'api_secret': 'your_twitter_api_secret_here',
        'bearer_token': 'your_twitter_bearer_token_here',
        'app_id': '31291794'
    },
    'coingecko': {
        'api_key': 'CG-your-api-key-here',
        'base_url': 'https://api.coingecko.com/api/v3'
    }
}

# Торговые настройки
TRADING_CONFIG = {
    'pairs': [
        # Топ криптовалюты
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT',
        'SOL/USDT', 'DOGE/USDT', 'TRX/USDT', 'MATIC/USDT', 'LTC/USDT',
        'DOT/USDT', 'SHIB/USDT', 'AVAX/USDT', 'ATOM/USDT', 'UNI/USDT',
        'LINK/USDT', 'BCH/USDT', 'XLM/USDT', 'ICP/USDT', 'FIL/USDT',
        'ETC/USDT', 'HBAR/USDT', 'VET/USDT', 'ALGO/USDT', 'NEAR/USDT',
        
        # DeFi токены
        'AAVE/USDT', 'MKR/USDT', 'COMP/USDT', 'YFI/USDT', 'SNX/USDT',
        'CRV/USDT', 'SUSHI/USDT', '1INCH/USDT', 'BAL/USDT', 'ZRX/USDT',
        'LRC/USDT', 'REN/USDT', 'BAND/USDT', 'ALPHA/USDT', 'GRT/USDT',
        
        # Layer 2 и альткоины
        'FTM/USDT', 'ONE/USDT', 'EGLD/USDT', 'FLOW/USDT', 'KSM/USDT',
        'THETA/USDT', 'SAND/USDT', 'MANA/USDT', 'GALA/USDT', 'AXS/USDT',
        'ENJ/USDT', 'CHZ/USDT', 'BAT/USDT', 'ZIL/USDT', 'HOT/USDT',
        
        # Privacy coins
        'XMR/USDT', 'ZEC/USDT', 'DASH/USDT',
        
        # Старые альткоины
        'NEO/USDT', 'QTUM/USDT', 'IOTA/USDT', 'XTZ/USDT', 'EOS/USDT',
        'WAVES/USDT', 'DCR/USDT', 'RVN/USDT', 'ZEN/USDT', 'OMG/USDT',
        
        # Новые проекты
        'JUP/USDT', 'PYTH/USDT', 'JTO/USDT', 'WIF/USDT', 'BONK/USDT',
        'BOME/USDT', 'PEPE/USDT', 'FLOKI/USDT', 'WEN/USDT',
        
        # Дополнительные пары
        'STORJ/USDT', 'ANKR/USDT', 'CTSI/USDT', 'AR/USDT', 'RLC/USDT',
        'SKL/USDT', 'OCEAN/USDT', 'AUDIO/USDT', 'HIVE/USDT', 'STEEM/USDT',
        
        # Мемкоины и популярные
        'CAT/USDT', 'POPCAT/USDT', 'MYRO/USDT', 'SLERF/USDT', 'BOOK/USDT',
        
        # Дополнительные альткоины до 100
        'RNDR/USDT', 'GRT/USDT', 'IMX/USDT', 'LPT/USDT', 'ENS/USDT',
        'APE/USDT', 'GMT/USDT', 'GST/USDT', 'STEPN/USDT', 'ANC/USDT',
        'LUNA/USDT', 'UST/USDT', 'MIRROR/USDT', 'RUNE/USDT', 'THOR/USDT',
        'CAKE/USDT', 'AUTO/USDT', 'BAKE/USDT', 'BNX/USDT', 'TLM/USDT',
        'SLP/USDT', 'PYR/USDT', 'GHST/USDT', 'QUICK/USDT', 'DYDX/USDT'
    ],
    'timeframes': ['15m', '1h', '4h', '1d'],
    'update_frequency': 300,  # 5 минут
    'min_confidence': 0.8,  # 80% для Best Alpha Only
    'top_signals': 5
}

# Анализ настройки
ANALYSIS_CONFIG = {
    'min_confidence': 0.8,  # 80% для Best Alpha Only
    'min_risk_reward': 2.0,  # 2.0 для качественных сигналов
    'max_signals_per_cycle': 5
} 