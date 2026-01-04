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
        'key': 'NEdNOs4i396D0Xb6Qp2n885jNKrT8FVZsTnQbheIzvPHfhsZCsmasL3CXVTXXiQ6',
        'secret': 'nCnO0x0QZwJkXj8VFabDKP3klf4Ebzt4yJgiglDdvjAuiIFx9IdvVvsxk3zuNBCQ'
    },
    'bybit': {
        'key': 'dbO1Q0HOsiPXS9rQa8',
        'secret': 'zEULSUmCXhOkAhP8KLJqyqnFaxvO59ATTFTc'
    },
    'okx': {
        'key': '3f6b8393-36bd-48fa-9051-061954be1882',
        'secret': '559B87BC72A45922FEE6A0874E3B3D07',
        'passphrase': 'Tims1982@'
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
        'api_key': 'SwRphJeF987vGpn0mXedNKPbZ',
        'api_secret': 'Ubjkw6EWqRHrHmUEpF0hX9xjkXoaVyzTHc4H21O8x1gcX2ve3y',
        'bearer_token': 'AAAAAAAAAAAAAAAAAAAAAJJ53QEAAAAAD0rBYGg55mJ%2BDVOw9L%2Bf6g23g%2FY%3Dp29zmZyMQqGjC3s1TLbFXS6sRWGQ0LF28NT44Fyg8Hd5nTdUcQ',
        'app_id': '31291794'
    },
    'coingecko': {
        'api_key': 'CG-TyedrrKDMCFt9McbTZCXN3mi',
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
