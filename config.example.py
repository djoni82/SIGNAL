# 📝 Пример конфигурации для UnifiedSignalBot
# Скопируйте этот файл как config.py и заполните своими API ключами

TELEGRAM_CONFIG = {
    'bot_token': 'ВАШ_TELEGRAM_BOT_TOKEN',  # Получите у @BotFather
    'chat_id': 'ВАШ_CHAT_ID',               # ID вашего чата
    'admin_chat_id': 'АДМИНСКИЙ_CHAT_ID',   # ID админского чата
    'enable_telegram': True,
    'send_signals': True,
    'send_status': True,
    'send_errors': True,
}

EXCHANGE_KEYS = {
    'binance': {
        'key': 'ВАШ_BINANCE_API_KEY',       # API ключ Binance
        'secret': 'ВАШ_BINANCE_SECRET'      # Секрет Binance
    },
    'bybit': {
        'key': 'ВАШ_BYBIT_API_KEY',         # API ключ Bybit
        'secret': 'ВАШ_BYBIT_SECRET'        # Секрет Bybit
    },
    'okx': {
        'key': 'ВАШ_OKX_API_KEY',           # API ключ OKX
        'secret': 'ВАШ_OKX_SECRET',         # Секрет OKX
        'passphrase': 'ВАШ_OKX_PASSPHRASE'  # Пароль OKX
    }
}

EXTERNAL_APIS = {
    'dune': {
        'api_key': 'ВАШ_DUNE_API_KEY',      # API ключ Dune Analytics
        'base_url': 'https://api.dune.com/api/v1',
        'query_id': 'ВАШ_QUERY_ID'          # ID запроса Dune
    },
    'crypto_panic': {
        'api_key': 'ВАШ_CRYPTOPANIC_API_KEY', # API ключ CryptoPanic
        'base_url': 'https://cryptopanic.com/api/v1'
    },
    'coingecko': {
        'base_url': 'https://api.coingecko.com/api/v3'
    }
}

TRADING_CONFIG = {
    'pairs': [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
        'XRP/USDT', 'DOT/USDT', 'DOGE/USDT', 'AVAX/USDT', 'MATIC/USDT',
        'LINK/USDT', 'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'ATOM/USDT',
        'NEAR/USDT', 'FTM/USDT', 'ALGO/USDT', 'VET/USDT', 'ICP/USDT',
        'FIL/USDT', 'TRX/USDT', 'ETC/USDT', 'XLM/USDT', 'HBAR/USDT',
        'APT/USDT', 'OP/USDT', 'ARB/USDT', 'MKR/USDT', 'AAVE/USDT',
        'SNX/USDT', 'COMP/USDT', 'CRV/USDT', 'DYDX/USDT', 'JUP/USDT',
        'QUICK/USDT', 'DASH/USDT', 'ZEC/USDT', 'XMR/USDT', 'EOS/USDT',
        'IOTA/USDT', 'NEO/USDT', 'WAVES/USDT', 'XTZ/USDT', 'ZIL/USDT',
        'ONE/USDT', 'HOT/USDT', 'BAT/USDT', 'MANA/USDT', 'SAND/USDT',
        'ENJ/USDT', 'CHZ/USDT', 'ANKR/USDT', 'COTI/USDT', 'DENT/USDT',
        'WIN/USDT', 'CAKE/USDT', 'BAKE/USDT', 'SUSHI/USDT', '1INCH/USDT',
        'ALPHA/USDT', 'AUDIO/USDT', 'BAND/USDT', 'BICO/USDT', 'BLZ/USDT',
        'BNT/USDT', 'BOND/USDT', 'C98/USDT', 'CELO/USDT', 'CHR/USDT',
        'CLV/USDT', 'COCOS/USDT', 'CTSI/USDT', 'CTXC/USDT', 'CVP/USDT',
        'DATA/USDT', 'DEGO/USDT', 'DUSK/USDT', 'EGLD/USDT', 'ELF/USDT',
        'ERN/USDT', 'FIDA/USDT', 'FLOW/USDT', 'FORTH/USDT', 'FRONT/USDT',
        'FTT/USDT', 'GALA/USDT', 'GTC/USDT', 'HBAR/USDT', 'HIVE/USDT',
        'HOT/USDT', 'ICP/USDT', 'IDEX/USDT', 'ILV/USDT', 'IMX/USDT',
        'INJ/USDT', 'IOTX/USDT', 'JASMY/USDT', 'KAVA/USDT', 'KDA/USDT',
        'KEEP/USDT', 'KLAY/USDT', 'KNC/USDT', 'KSM/USDT', 'LDO/USDT',
        'LINA/USDT', 'LIT/USDT', 'LOKA/USDT', 'LPT/USDT', 'LQTY/USDT',
        'LRC/USDT', 'LTO/USDT', 'LUNA/USDT', 'MASK/USDT', 'MBOX/USDT',
        'MC/USDT', 'MINA/USDT', 'MKR/USDT', 'MLN/USDT', 'MOB/USDT',
        'MTL/USDT', 'MULTI/USDT', 'NEO/USDT', 'NKN/USDT', 'NMR/USDT',
        'OCEAN/USDT', 'OGN/USDT', 'OM/USDT', 'OMG/USDT', 'ONE/USDT',
        'ONG/USDT', 'ONT/USDT', 'ORN/USDT', 'OXT/USDT', 'PAXG/USDT',
        'PEOPLE/USDT', 'PERP/USDT', 'PHA/USDT', 'POLS/USDT', 'POLY/USDT',
        'POND/USDT', 'POWR/USDT', 'PUNDIX/USDT', 'PYR/USDT', 'QI/USDT',
        'QNT/USDT', 'QTUM/USDT', 'RAD/USDT', 'RARE/USDT', 'RAY/USDT',
        'REEF/USDT', 'REN/USDT', 'REP/USDT', 'REQ/USDT', 'RLC/USDT',
        'ROSE/USDT', 'RSR/USDT', 'RUNE/USDT', 'RVN/USDT', 'SAND/USDT',
        'SCRT/USDT', 'SFP/USDT', 'SHIB/USDT', 'SKL/USDT', 'SLP/USDT',
        'SNT/USDT', 'SNX/USDT', 'SOL/USDT', 'SPELL/USDT', 'SRM/USDT',
        'STARL/USDT', 'STMX/USDT', 'STORJ/USDT', 'STPT/USDT', 'STRAX/USDT',
        'STX/USDT', 'SUPER/USDT', 'SUSHI/USDT', 'SWEAT/USDT', 'SXP/USDT',
        'SYN/USDT', 'SYS/USDT', 'T/USDT', 'TFUEL/USDT', 'THETA/USDT',
        'TLM/USDT', 'TOKE/USDT', 'TOMO/USDT', 'TORN/USDT', 'TRB/USDT',
        'TRIBE/USDT', 'TRU/USDT', 'TRX/USDT', 'TVK/USDT', 'TWT/USDT',
        'UMA/USDT', 'UNFI/USDT', 'UNI/USDT', 'USDC/USDT', 'USDP/USDT',
        'USDT/USDT', 'UTK/USDT', 'VET/USDT', 'VGX/USDT', 'VTHO/USDT',
        'WAVES/USDT', 'WAXP/USDT', 'WBTC/USDT', 'WOO/USDT', 'XEC/USDT',
        'XEM/USDT', 'XLM/USDT', 'XMR/USDT', 'XRP/USDT', 'XTZ/USDT',
        'XVG/USDT', 'XVS/USDT', 'YFI/USDT', 'YGG/USDT', 'ZEC/USDT',
        'ZEN/USDT', 'ZIL/USDT', 'ZRX/USDT'
    ],
    'timeframes': ['15m', '1h', '4h'],      # Таймфреймы для обычных сигналов
    'update_frequency': 300,                # Частота обновления (5 минут)
    'min_confidence': 0.8,                  # Минимальная уверенность (80%)
    'top_signals': 5                        # Количество лучших сигналов
}

# Настройки скальпинга
SCALPING_CONFIG = {
    'enabled': True,                        # Включить скальпинг
    'pairs': TRADING_CONFIG['pairs'][:20],  # Первые 20 пар для скальпинга
    'timeframes': ['1m', '5m', '15m'],      # Таймфреймы для скальпинга
    'frequency': 60,                        # Частота обновления (1 минута)
    'min_confidence': 0.6                   # Минимальная уверенность (60%)
}

# Настройки логирования
LOGGING_CONFIG = {
    'level': 'INFO',                        # Уровень логирования
    'file': 'bot_logs.txt',                 # Файл логов
    'max_size': 10 * 1024 * 1024,          # Максимальный размер файла (10MB)
    'backup_count': 5                       # Количество резервных файлов
}

# Настройки безопасности
SECURITY_CONFIG = {
    'rate_limit': 100,                      # Лимит запросов в минуту
    'timeout': 30,                          # Таймаут запросов (секунды)
    'retry_attempts': 3,                    # Количество попыток повтора
    'retry_delay': 5                        # Задержка между попытками (секунды)
} 