from pydantic_settings import BaseSettings
from typing import Dict, List, Optional

class Settings(BaseSettings):
    # Telegram Config
    telegram_bot_token: str = 'ВАШ_TELEGRAM_BOT_TOKEN'
    telegram_chat_id: str = 'ВАШ_CHAT_ID'
    telegram_admin_chat_id: str = 'АДМИНСКИЙ_CHAT_ID'
    enable_telegram: bool = True
    send_signals: bool = True
    send_status: bool = True
    send_errors: bool = True

    # Exchange Keys
    binance_key: str = 'ВАШ_BINANCE_API_KEY'
    binance_secret: str = 'ВАШ_BINANCE_SECRET'
    bybit_key: str = 'ВАШ_BYBIT_API_KEY'
    bybit_secret: str = 'ВАШ_BYBIT_SECRET'
    okx_key: str = 'ВАШ_OKX_API_KEY'
    okx_secret: str = 'ВАШ_OKX_SECRET'
    okx_passphrase: str = 'ВАШ_OKX_PASSPHRASE'

    # External APIs
    dune_api_key: str = 'ВАШ_DUNE_API_KEY'
    dune_query_id: str = 'ВАШ_QUERY_ID'
    cryptopanic_api_key: str = 'ВАШ_CRYPTOPANIC_API_KEY'

    # Trading Config
    trading_pairs: List[str] = [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
        'XRP/USDT', 'DOT/USDT', 'DOGE/USDT', 'AVAX/USDT', 'MATIC/USDT'
    ]
    timeframes: List[str] = ['15m', '1h', '4h']
    primary_timeframe: str = '1h'
    update_frequency: int = 300
    min_confidence: float = 0.8
    signal_cooldown_minutes: int = 60
    
    # Risk Management
    initial_capital: float = 1000.0
    max_position_size_pct: float = 0.1
    trade_in_crisis: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
