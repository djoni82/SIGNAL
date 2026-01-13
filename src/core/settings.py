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
    okx_key: str = ""    # Legacy name
    bingx_key: str = ""
    bingx_secret: str = ""

    # External APIs
    gemini_api_key: str = "YOUR_GEMINI_API_KEY"
    
    # Ultra Mode Settings (Real ML + Smart Money)
    use_ultra_mode: bool = True  # Set to True to enable Ultra Mode
    ultra_min_confidence: float = 0.40  # Temporarily lowered to test signal delivery
    ultra_shadow_mode: bool = True  # Test mode: generate signals but don't send to Telegram
    
    # Smart Money API Keys (optional, for advanced features)
    coinglass_api_key: str = ""  # https://www.coinglass.com/
    hyblock_api_key: str = ""    # https://app.hyblock.capital/
    
    # ML Model Path
    ml_model_path: str = "models/"
    
    dune_api_key: str = 'ВАШ_DUNE_API_KEY'
    dune_query_id: str = 'ВАШ_QUERY_ID'
    cryptopanic_api_key: str = 'ВАШ_CRYPTOPANIC_API_KEY'

    # Trading Config
    trading_pairs: List[str] = [
        # Top 100 by 24h Volume (Binance)
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'PEPE/USDT',
        'DOGE/USDT', 'BNB/USDT', 'ZEC/USDT', 'BONK/USDT', 'SUI/USDT',
        'WIF/USDT', 'BCH/USDT', 'TRX/USDT', 'VIRTUAL/USDT', 'ADA/USDT',
        'ENA/USDT', 'FET/USDT', 'PENGU/USDT', 'AVAX/USDT', 'LINK/USDT',
        'SHIB/USDT', 'LTC/USDT', 'UNI/USDT', 'NEAR/USDT', 'TAO/USDT',
        'HBAR/USDT', 'RENDER/USDT', 'FLOKI/USDT', 'WLD/USDT', 'PNUT/USDT',
        'PUMP/USDT', 'FIL/USDT', 'AAVE/USDT', 'OG/USDT', 'NEIRO/USDT',
        'XLM/USDT', 'DOT/USDT', 'ICP/USDT', 'BOME/USDT', 'ARB/USDT',
        'APT/USDT', 'TON/USDT', 'TIA/USDT', 'ACT/USDT', 'SEI/USDT',
        'LUNC/USDT', 'STX/USDT', 'DASH/USDT', 'AIXBT/USDT', 'ZEN/USDT',
        'STRK/USDT', 'CVX/USDT', 'ARKM/USDT', 'CHZ/USDT', 'POL/USDT',
        'ETC/USDT', 'BTTC/USDT', 'GALA/USDT', 'ORCA/USDT', 'CRV/USDT',
        'OP/USDT', 'BIO/USDT', 'ETHFI/USDT', 'ONDO/USDT', 'LUNA/USDT',
        'LDO/USDT', 'INJ/USDT', 'EIGEN/USDT', 'LPT/USDT', 'CAKE/USDT',
        'XEC/USDT', 'PEOPLE/USDT', 'KAITO/USDT', 'ATOM/USDT', 'MATIC/USDT',
        'SAND/USDT', 'MANA/USDT', 'AXS/USDT', 'IMX/USDT', 'LRC/USDT',
        'SNX/USDT', 'COMP/USDT', 'MKR/USDT', 'GRT/USDT', 'RUNE/USDT',
        'FTT/USDT', 'CRO/USDT', 'OKB/USDT', 'OCEAN/USDT', 'AGIX/USDT'
    ]
    timeframes: List[str] = ['15m', '1h', '4h']
    primary_timeframe: str = '1h'
    update_frequency: int = 300
    min_confidence: float = 0.8  # Restored to 0.8 for 90 pairs
    signal_cooldown_minutes: int = 60
    
    # Risk Management
    initial_capital: float = 1000.0
    max_position_size_pct: float = 0.1
    trade_in_crisis: bool = False
    
    # Production Optimizations
    arbitrage_min_spread_pct: float = 2.0
    arbitrage_commission_pct: float = 0.2
    arbitrage_min_net_profit: float = 0.5
    arbitrage_max_sanity_spread: float = 50.0

    class Config:
        env_file = ".env"

settings = Settings()
