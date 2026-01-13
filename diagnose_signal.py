import asyncio
import logging
from src.core.settings import settings
from src.strategies.signal_generator_ultra import UltraSignalGenerator
import ccxt.async_support as ccxt

# Setup basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("Diagnostic")

async def test_signal_generation():
    print("--- DIAGNOSTIC START ---")
    
    # Mock settings for test
    settings.use_ultra_mode = True
    settings.ultra_shadow_mode = False
    
    print(f"Testing Symbol: BTC/USDT")
    print(f"Timeframe: {settings.primary_timeframe}")
    
    try:
        # Initializing with None for exchange_connector might work if it's only used for some fallbacks
        # If it crashes inside, I'll need to mock it.
        class MockConnector:
             async def fetch_ohlcv(self, *args, **kwargs): return [] 
             async def fetch_ohlcv_df(self, *args, **kwargs):
                 import pandas as pd
                 import numpy as np
                 # Return valid DF structure for ML
                 return pd.DataFrame({
                     'open': np.random.rand(200)*100,
                     'high': np.random.rand(200)*100,
                     'low': np.random.rand(200)*100,
                     'close': np.random.rand(200)*100,
                     'volume': np.random.rand(200)*1000
                 })
             
        generator = UltraSignalGenerator(exchange_connector=MockConnector(), ws_client=None)
        
        # Manually trigger signal generation
        # spread=0.0 means no arbitrage advantage, neutral ground
        print("Running generate_signal(BTC/USDT)...")
        signal = await generator.generate_signal(
            symbol="BTC/USDT", 
            timeframe=settings.primary_timeframe, 
            arbitrage_spread=0.0
        )
        
        if signal:
            print("\n✅ SIGNAL GENERATED!")
            print(f"Direction: {signal.direction}")
            print(f"Confidence: {signal.confidence}")
            print(f"Price: {signal.entry_price}")
            print(f"Rationale: {signal.rationale}")
        else:
            print("\n❌ NO SIGNAL GENERATED")
            print("Likely filtered by logic (ADX, Confidence, etc). Check logs above.")

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during generation: {e}")
        import traceback
        traceback.print_exc()

    print("--- DIAGNOSTIC END ---")

if __name__ == "__main__":
    asyncio.run(test_signal_generation())
