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
        self.is_active = True # Controlled by Telegram
        
        # Link control callback
        self.notifier.telegram.set_control_callback(self.control_callback)

    def control_callback(self, action: str):
        if action == 'start':
            self.is_active = True
            logger.info("Bot resumed via Telegram.")
        elif action == 'stop':
            self.is_active = False
            logger.info("Bot paused via Telegram.")

    async def initialize(self):
        logger.info("Initializing Bot...")
        self.exchanges = {}
        
        # Binance
        if settings.binance_key:
            try:
                self.exchanges['binance'] = ccxt.binance({
                    'apiKey': settings.binance_key,
                    'secret': settings.binance_secret,
                    'enableRateLimit': True,
                })
                logger.info("Initialized Binance")
            except Exception as e:
                logger.error(f"Failed to init Binance: {e}")

        # Bybit
        if settings.bybit_key and settings.bybit_key != 'ВАШ_BYBIT_API_KEY':
            try:
                self.exchanges['bybit'] = ccxt.bybit({
                    'apiKey': settings.bybit_key,
                    'secret': settings.bybit_secret,
                    'enableRateLimit': True,
                })
                logger.info("Initialized Bybit")
            except Exception as e:
                logger.error(f"Failed to init Bybit: {e}")

        # BingX
        if settings.bingx_key:
            try:
                self.exchanges['bingx'] = ccxt.bingx({
                    'apiKey': settings.bingx_key,
                    'secret': settings.bingx_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'swap',  # Обычно для фьючерсов
                    }
                })
                logger.info("Initialized BingX")
            except Exception as e:
                logger.error(f"Failed to init BingX: {e}")

        # Load Markets to verify connection
        for name, exchange in list(self.exchanges.items()):
            try:
                logger.info(f"Loading markets for {name}...")
                await exchange.load_markets()
            except Exception as e:
                logger.error(f"Failed to load markets for {name}: {e}")
                # Remove failed exchange
                await exchange.close()
                del self.exchanges[name]

        if not self.exchanges:
            logger.error("No exchanges initialized! Check .env")
            return

        # Use Binance as primary for TA, or first available
        self.primary_exchange = self.exchanges.get('binance') or list(self.exchanges.values())[0]
        self.exchange_connector = self.primary_exchange # Backwards compatibility
        
        self.signal_generator = SignalGenerator(self.primary_exchange)
        logger.info(f"Bot Initialized. Active Exchanges: {list(self.exchanges.keys())}")

    async def run_loop(self):
        logger.info(f"Starting analysis loop for {len(settings.trading_pairs)} pairs...")
        
        while True:
            if not self.is_active:
                await asyncio.sleep(5)
                continue

            try:
                for symbol in settings.trading_pairs:
                    if not self.is_active: break 

                    logger.info(f"Analyzing {symbol}...")
                    
                    # 1. Arbitrage Check (Multi-Exchange)
                    await self._check_arbitrage(symbol)

                    # 2. Main Strategy Analysis (Primary Exchange)
                    multi_tf_data = await self._fetch_data(symbol)
                    
                    if not multi_tf_data:
                        continue
                        
                    signal: EnhancedSignal = await self.signal_generator.analyze_symbol(symbol, multi_tf_data)
                    
                    if signal:
                        logger.info(f"Signal found for {symbol}: {signal.direction}")
                        formatted_msg = self._format_signal(signal)
                        await self.notifier.send_signal(formatted_msg)
                    
                    await asyncio.sleep(1) 
                
                logger.info(f"Loop finished. Sleeping for {settings.update_frequency}s")
                await asyncio.sleep(settings.update_frequency)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await self.notifier.send(f"⚠️ Bot Critical Error: {str(e)}")
                await asyncio.sleep(60)

    async def _check_arbitrage(self, symbol):
        """Fetches prices from all exchanges and checks for spreads"""
        prices = {}
        
        for name, exchange in self.exchanges.items():
            try:
                ticker = await exchange.fetch_ticker(symbol)
                if ticker and 'last' in ticker:
                    prices[name] = ticker['last']
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} from {name}: {e}")
        
        if len(prices) > 1:
            min_price = min(prices.values())
            max_price = max(prices.values())
            spread_pct = ((max_price - min_price) / min_price) * 100
            
            log_msg = f"Prices for {symbol}: {prices} | Spread: {spread_pct:.2f}%"
            logger.info(log_msg)
            
            if spread_pct > 1.0: # 1% Arbitrage threshold
                await self.notifier.send_signal(f"⚡ <b>Arbitrage Opportunity!</b>\n{symbol}\nSpread: {spread_pct:.2f}%\n{prices}")

    async def _fetch_data(self, symbol):
        data = {}
        try:
            for tf in settings.timeframes:
                ohlcv = await self.primary_exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
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
        for name, exchange in getattr(self, 'exchanges', {}).items():
            await exchange.close()

async def main():
    bot = Bot()
    try:
        await bot.initialize()
        
        await asyncio.gather(
            bot.run_loop(),
            bot.notifier.telegram.start_polling()
        )
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
