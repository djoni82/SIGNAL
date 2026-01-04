import asyncio
import logging
import sys
import ccxt.base.errors
import ccxt.async_support as ccxt

from src.core.settings import settings
from src.core.logging import setup_logging
from src.services.notifier import Notifier
from src.strategies.signal_generator import SignalGenerator
from src.strategies.models import EnhancedSignal

# Setup Logging
setup_logging(json_logs=False, log_level="INFO")
logger = logging.getLogger(__name__)

class Bot:
    def __init__(self):
        self.notifier = Notifier()
        self.exchange_connector = None 
        self.signal_generator = None
        
    async def initialize(self):
        logger.info("Initializing Bot...")
        
        # Initialize CCXT exchange (using Binance as default example)
        # In a real scenario, you might want to load this from settings dynamically
        self.exchange_connector = ccxt.binance({
            'apiKey': settings.binance_key,
            'secret': settings.binance_secret,
            'enableRateLimit': True,
        })
        
        # Initialize Signal Generator with exchange connector
        self.signal_generator = SignalGenerator(self.exchange_connector)
        logger.info("Bot Initialized.")

    async def run_loop(self):
        logger.info(f"Starting analysis loop for {len(settings.trading_pairs)} pairs...")
        
        while True:
            try:
                for symbol in settings.trading_pairs:
                    logger.info(f"Analyzing {symbol}...")
                    
                    # Fetch Data (Simplified fetch for refactor demonstration)
                    # Ideally this should be in a separate DataManager class
                    multi_tf_data = await self._fetch_data(symbol)
                    
                    if not multi_tf_data:
                        continue
                        
                    signal: EnhancedSignal = await self.signal_generator.analyze_symbol(symbol, multi_tf_data)
                    
                    if signal:
                        logger.info(f"Signal found for {symbol}: {signal.direction}")
                        formatted_msg = self._format_signal(signal)
                        await self.notifier.send_signal(formatted_msg)
                    
                    await asyncio.sleep(1) # Small delay between pairs
                
                logger.info(f"Loop finished. Sleeping for {settings.update_frequency}s")
                await asyncio.sleep(settings.update_frequency)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await self.notifier.send(f"⚠️ Bot Critical Error: {str(e)}")
                await asyncio.sleep(60)

    async def _fetch_data(self, symbol):
        data = {}
        try:
            for tf in settings.timeframes:
                ohlcv = await self.exchange_connector.fetch_ohlcv(symbol, timeframe=tf, limit=100)
                if ohlcv:
                     import pandas as pd
                     df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                     df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                     df.set_index('timestamp', inplace=True)
                     data[tf] = df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
        return data

    def _format_signal(self, signal: EnhancedSignal) -> str:
        emoji = "🟢" if "BUY" in signal.direction else "🔴"
        return (
            f"{emoji} <b>SIGNAL: {signal.direction}</b>\n\n"
            f"Symbol: {signal.symbol}\n"
            f"Entry: {signal.entry_price}\n"
            f"Confidence: {signal.confidence:.2f}\n"
            f"Stop Loss: {signal.stop_loss:.4f}\n"
            f"Take Profit: {[f'{tp:.4f}' for tp in signal.take_profit]}\n"
            f"Rationale: {signal.rationale}"
        )

    async def cleanup(self):
        await self.notifier.close()
        if self.exchange_connector:
            await self.exchange_connector.close()

async def main():
    bot = Bot()
    try:
        await bot.initialize()
        await bot.run_loop()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
