import asyncio
import logging
import sys
from typing import Optional
import ccxt
import ccxt.async_support as ccxt_async

from src.core.settings import settings
from src.core.logging import setup_logging
from src.services.notifier import Notifier
from src.services.telegram import TelegramBot
from src.services.api_server import run_api
import threading
from src.strategies.models import EnhancedSignal
from src.services.portfolio_service import PortfolioService
from src.strategies.signal_generator import SignalGenerator

# Setup Logging
setup_logging(json_logs=False, log_level="INFO")
logger = logging.getLogger(__name__)

# Silence noisy third-party loggers
for logger_name in ['websockets', 'websockets.client', 'websockets.server', 'ccxt', 'ccxt.async_support', 'urllib3']:
    logging.getLogger(logger_name).setLevel(logging.WARNING)
    logging.getLogger(logger_name).propagate = False

class Bot:
    def __init__(self):
        self.settings = settings
        self.notifier = Notifier()
        self.exchange_connector = None
        self.signal_generator = None
        self.exchanges = {}
        self.primary_exchange = None
        self.is_active = True # Controlled by Telegram
        # Production Optimizations
        self.symbol_whitelist = {}  # exchange_name -> set of symbols
        self.last_signal_time = {}  # symbol -> datetime
        self.last_update_time = {}  # symbol -> timestamp (for dynamic frequency)
        self.api_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent API calls
        self.notifier.telegram.set_control_callback(self.control_callback)
        
        # Top 20 pairs by liquidity (update every 60s)
        self.TOP_PAIRS = {
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'BNB/USDT',
            'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 'DOT/USDT',
            'MATIC/USDT', 'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'NEAR/USDT',
            'ATOM/USDT', 'FIL/USDT', 'APT/USDT', 'ARB/USDT', 'OP/USDT'
        }

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
                self.exchanges['binance'] = ccxt_async.binance({
                    'apiKey': settings.binance_key,
                    'secret': settings.binance_secret,
                    'enableRateLimit': True,
                    'options': {'defaultType': 'future'}
                })
                logger.info("Initialized Binance")
            except Exception as e:
                logger.error(f"Failed to init Binance: {e}")

        # Bybit
        if settings.bybit_key and settings.bybit_key != 'ВАШ_BYBIT_API_KEY':
            try:
                self.exchanges['bybit'] = ccxt_async.bybit({
                    'apiKey': settings.bybit_key,
                    'secret': settings.bybit_secret,
                    'enableRateLimit': True,
                    'options': {'defaultType': 'linear'}
                })
                logger.info("Initialized Bybit")
            except Exception as e:
                logger.error(f"Failed to init Bybit: {e}")

        # BingX
        if settings.bingx_key:
            try:
                self.exchanges['bingx'] = ccxt_async.bingx({
                    'apiKey': settings.bingx_key,
                    'secret': settings.bingx_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'swap',
                        'adjustForTimeDifference': True,
                        'fetchCurrencies': False
                    }
                })
                logger.info("Initialized BingX")
            except Exception as e:
                logger.error(f"Failed to init BingX: {e}")

        # Load Markets & Build Whitelist
        for name, exchange in list(self.exchanges.items()):
            try:
                logger.info(f"Loading markets for {name}...")
                try:
                    await exchange.load_markets()
                    # Filter only relevant markets
                    m_type = exchange.options.get('defaultType', 'spot')
                    if name in ['bingx', 'bybit']: m_type = 'swap' # Both mostly used as swap
                    
                    target_types = {m_type}
                    if m_type in ['future', 'swap']:
                         target_types.add('swap')
                         
                    whitelist = set()
                    for symbol in exchange.symbols:
                        market = exchange.market(symbol)
                        # Check type AND 'linear' for Bybit
                        is_linear = market.get('linear', True) if name == 'bybit' else True 
                        
                        if name == 'bybit' and not is_linear:
                            continue

                        if market['type'] in target_types and market['active']:
                            # Normalize symbol for storage (strip :USDT, 1000 prefix, etc)
                            # This ensures our check "if symbol in whitelist" works for standard names
                            clean_symbol = symbol.split(':')[0]
                            whitelist.add(symbol) # Add raw for trading
                            
                            # Also add normalized variations to ensure "BTC/USDT" checks pass
                            # even if the raw symbol is "BTC/USDT:USDT"
                            if clean_symbol != symbol:
                                whitelist.add(clean_symbol)
                            
                            # Add slash-less version
                            whitelist.add(symbol.replace('/', '').split(':')[0])
                            
                    self.symbol_whitelist[name] = whitelist
                    logger.info(f"Loaded {len(whitelist)} {m_type} markets for {name}")
                    
                    # Fallback if empty (e.g. API Error)
                    if not whitelist:
                        logger.warning(f"⚠️ Whitelist empty for {name}. Usage fallback to settings.trading_pairs.")
                        self.symbol_whitelist[name] = set(self.settings.trading_pairs)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Initial load_markets failed for {name}: {e}. Using settings fallback.")
                    # Fallback to user settings to prevent complete stall
                    self.symbol_whitelist[name] = set(self.settings.trading_pairs)
            except Exception as e:
                logger.error(f"Critical error in gateway setup for {name}: {e}")

        if not self.exchanges:
            logger.error("No exchanges initialized! Check .env")
            return

        # Use Binance as primary for TA, or first available
        self.primary_exchange = self.exchanges.get('binance') or list(self.exchanges.values())[0]
        self.exchange_connector = self.primary_exchange # Backwards compatibility

        # Signal Generator (Legacy or Ultra Mode)
        if self.settings.use_ultra_mode:
            logger.info("🚀 Initializing Ultra Mode (Real ML + Smart Money)...")
            from src.strategies.signal_generator_ultra import UltraSignalGenerator
            from src.strategies.binance_ws import BinanceWSClient
            
            # Smart Symbol Resolution: Find the actual symbols used by Binance
            binance_symbols = []
            for s in self.settings.trading_pairs:
                m_symbol, _ = self.find_matching_symbol('binance', s)
                if m_symbol:
                    binance_symbols.append(m_symbol)
                else:
                    binance_symbols.append(s)
            
            # Start WS Client with RESOLVED symbols
            self.ws_client = BinanceWSClient(binance_symbols)
            asyncio.create_task(self.ws_client.start())
            
            self.signal_generator = UltraSignalGenerator(self.primary_exchange, ws_client=self.ws_client)
            logger.info(f"   Min Confidence: {self.settings.ultra_min_confidence:.0%}")
            logger.info("   ML Models: XGBoost + LightGBM + CatBoost")
            logger.info("   Smart Money: Liquidity + Funding Analysis (WebSocket)")
        else:
            logger.info("📊 Initializing Legacy Mode (TA + Heuristic ML)...")
            from src.strategies.signal_generator import SignalGenerator
            self.signal_generator = SignalGenerator(self.primary_exchange)
            logger.info(f"   Min Confidence: {self.settings.min_confidence:.0%}")
        
        # Portfolio Service
        self.portfolio_service = PortfolioService(self.exchanges)
        logger.info(f"Bot Initialized. Active Exchanges: {list(self.exchanges.keys())}")
        self.is_running = True

    def find_matching_symbol(self, exchange_name: str, target_symbol: str) -> tuple[Optional[str], float]:
        """
        Smart matching that handles:
        1. Base/Quote variations (BTC/USDT vs BTCUSDT)
        2. Contract prefixes (1000PEPE vs PEPE)
        3. Exchange-specific suffixes (:USDT)
        """
        # Safety: normalize name
        if not exchange_name:
            return None, 1.0
            
        name = exchange_name.lower()
        whitelist = self.symbol_whitelist.get(name, set())
        
        # 1. Exact Match (Multiplier 1.0)
        if target_symbol in whitelist:
            return target_symbol, 1.0
            
        # 2. Suffix Match (:USDT or similar CCXT formats)
        base_part = target_symbol.split(':')[0] if ':' in target_symbol else target_symbol
        if base_part in whitelist:
            return base_part, 1.0

        # 3. Fuzzy Match for Futures (1000x, 1000000x prefixes)
        base = target_symbol.split('/')[0].upper()
        quote = target_symbol.split('/')[1].upper() if '/' in target_symbol else "USDT"
        
        for s in whitelist:
            # 3a. Preferred Derivatives Match (Linear Perpetuals first)
            # Most CCXT linear perps end with :USDT or are just the base/quote
            if s.endswith(":USDT") and s.startswith(f"{base}/{quote}"):
                return s, 1.0
            
        for s in whitelist:
            # 3a. Preferred Derivatives Match (Linear Perpetuals first)
            # Most CCXT linear perps end with :USDT or are just the base/quote
            if s.endswith(":USDT") and s.startswith(f"{base}/{quote}"):
                return s, 1.0
            
            # Simple format but must not be a quarterly (no dashes/dates)
            if s == f"{base}/{quote}" or s == f"{base}{quote}":
                return s, 1.0
                
            # 3b. Prefixes (1000x, 1000000x)
            for multiplier in [1000, 1000000]:
                prefix = str(multiplier)
                if s.startswith(f"{prefix}{base}"):
                    # Precise match check, excluding dated contracts
                    remaining = s[len(prefix)+len(base):]
                    if (not remaining or remaining.startswith('/') or remaining.startswith(':')) and '-' not in s:
                        return s, float(multiplier)
        
        # Fallback: robust fuzzy check for ANY matching pair
        target_clean = f"{base}{quote}"
        for s in whitelist:
             # Remove common suffixes/separators for comparison
             s_clean = s.split(':')[0].replace('/', '').replace('-', '')
             
             # Check if it's the 1000x version
             if s_clean == target_clean or \
                s_clean == f"1000{target_clean}" or \
                s_clean == f"1000000{target_clean}":
                 return s, 1.0

        return None, 1.0

    async def run_loop(self):
        """Main operational loop with dynamic frequency and rate limiting"""
        logger.info("Main loop started. Scanning for signals...")
        import time
        
        while self.is_running:
            try:
                if not self.is_active:
                    await asyncio.sleep(10)
                    continue

                # Enhanced WS Health Check (Ultra Mode)
                if self.settings.use_ultra_mode and hasattr(self, 'ws_client'):
                    if not self.ws_client.is_connected():
                        logger.warning("⚠️ WebSocket disconnected or stale. Reconnecting...")
                        try:
                            await self.ws_client.restart()
                            logger.info("✅ WebSocket reconnected successfully")
                        except Exception as e:
                            logger.error(f"Failed to restart WebSocket: {e}")
                            await asyncio.sleep(5)

                for symbol in self.settings.trading_pairs:
                    if not self.is_active: break
                    
                    # Dynamic Update Frequency
                    now = time.time()
                    update_interval = 60 if symbol in self.TOP_PAIRS else 300  # 1m vs 5m
                    
                    if symbol in self.last_update_time:
                        elapsed = now - self.last_update_time[symbol]
                        if elapsed < update_interval:
                            continue  # Skip this symbol for now
                    
                    self.last_update_time[symbol] = now

                    # Whitelist Check: Find matched symbol for primary exchange
                    primary_name = None
                    for n, ex in self.exchanges.items():
                        if ex == self.primary_exchange:
                            primary_name = n
                            break
                    
                    m_symbol, m_factor = self.find_matching_symbol(primary_name, symbol)
                    
                    if not m_symbol:
                        logger.debug(f"Skipping {symbol} - No match found on {primary_name}")
                        continue

                    effective_symbol = m_symbol

                    # 1. Arbitrage Check (Pre-scan)
                    spread_pct = await self._check_arbitrage(symbol)

                    # 2. Ultra Mode Analysis (with Rate Limiting)
                    if self.settings.use_ultra_mode and self.signal_generator:
                        try:
                            # Rate-limited signal generation
                            async with self.api_semaphore:
                                signal = await self.signal_generator.generate_signal(
                                    symbol=m_symbol, 
                                    timeframe=self.settings.primary_timeframe,
                                    arbitrage_spread=spread_pct
                                )
                            if signal:
                                # Cooldown Check
                                from typing import Dict, List, Optional
                                from datetime import datetime
                                now = datetime.now()
                                if symbol not in self.last_signal_time or (now - self.last_signal_time[symbol]).total_seconds() > self.settings.signal_cooldown_minutes * 60:
                                    
                                    # Send/Log Signal
                                    if getattr(self.settings, 'ultra_shadow_mode', False):
                                        logger.info(f"[SHADOW] Signal for {symbol}: {signal.direction} (Conf: {signal.confidence:.2f})")
                                    else:
                                        await self.notifier.send_signal(signal)
                                    
                                    self.last_signal_time[symbol] = now
                                else:
                                    logger.debug(f"Signal for {symbol} suppressed by cooldown.")

                        except Exception as e:
                            logger.error(f"Ultra mode error for {symbol}: {e}")


                    await asyncio.sleep(0.5)  # Small delay between symbols

                # Dynamic sleep: shorter for active monitoring
                logger.debug(f"Loop iteration complete. Next cycle in 30s")
                await asyncio.sleep(30)  # Check every 30s, but symbols update per their interval

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await self.notifier.send(f"⚠️ Bot Critical Error: {str(e)}")
                await asyncio.sleep(60)

    async def _check_arbitrage(self, symbol):
        """Fetches prices from all exchanges and checks for spreads correctly"""
        MIN_SPREAD_PCT = self.settings.arbitrage_min_spread_pct
        COMMISSION_PCT = self.settings.arbitrage_commission_pct
        
        prices = {}
        matched_symbols = {}

        for name, exchange in self.exchanges.items():
            m_symbol, m_factor = self.find_matching_symbol(name, symbol)
            if not m_symbol:
                continue

            try:
                ticker = await exchange.fetch_ticker(m_symbol)
                if ticker and 'last' in ticker:
                    # IMPORTANT: Normalize price by dividing by multiplier factor
                    prices[name] = ticker['last'] / m_factor
                    matched_symbols[name] = f"{m_symbol} (x{m_factor})" if m_factor > 1 else m_symbol
            except ccxt.RateLimitExceeded as e:
                logger.warning(f"Rate limit hit on {name} for {symbol}. Sleeping 60s.")
                await asyncio.sleep(60)
            except ccxt.ExchangeError as e:
                logger.warning(f"Exchange error on {name} for {symbol}: {e}")
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} from {name}: {e}")

        if len(prices) > 1:
            min_price = min(prices.values())
            max_price = max(prices.values())
            spread_pct = ((max_price - min_price) / min_price) * 100

            if spread_pct > MIN_SPREAD_PCT:
                # Extra sanity check for "unreal" spreads
                if spread_pct > 50.0:
                    logger.warning(f"⚠️ Extreme spread detected ({spread_pct:.2f}%). Potential matching error. Symbols: {matched_symbols}")
                    return

                net_profit = spread_pct - COMMISSION_PCT
                if net_profit > 0.5:
                    logger.info(f"⚡ Arbitrage found for {symbol}: {spread_pct:.2f}% (Net: {net_profit:.2f}%)")
                    await self.notifier.send_signal(
                        f"⚡ <b>Arbitrage Opportunity!</b>\n"
                        f"Pair: {symbol}\n"
                        f"Spread: {spread_pct:.2f}%\n"
                        f"Net Profit: {net_profit:.2f}%\n\n"
                        f"Prices:\n" + "\n".join([f"• {k}: ${v:.6f}" for k, v in prices.items()])
                    )
            
            return spread_pct
        return 0.0

    async def _fetch_data(self, symbol):
        data = {}
        try:
            for tf in self.settings.timeframes:
                try:
                    ohlcv = await self.primary_exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
                    if ohlcv:
                         import pandas as pd
                         df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                         df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                         df.set_index('timestamp', inplace=True)
                         data[tf] = df
                except ccxt.RateLimitExceeded as e:
                    logger.warning(f"Rate limit hit for {symbol} on {tf}. Sleeping 60s.")
                    await asyncio.sleep(60)
                    return None
                except ccxt.ExchangeError as e:
                    logger.error(f"Exchange error for {symbol} on {tf}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
        return data

    def _format_signal(self, signal: EnhancedSignal) -> str:
        """Format signal for Telegram with professional Russian styling"""
        
        # Direction emoji and text
        if "BUY" in signal.direction or signal.direction == "STRONG_BUY":
            direction_emoji = "🟢"
            direction_text = "СИГНАЛ: ПОКУПКА" if signal.direction == "BUY" else "СИГНАЛ: СИЛЬНАЯ ПОКУПКА"
        else:
            direction_emoji = "🔴"
            direction_text = "СИГНАЛ: ПРОДАЖА" if signal.direction == "SELL" else "СИГНАЛ: СИЛЬНАЯ ПРОДАЖА"
        
        # Format take-profit levels
        tp_lines = []
        for i, tp in enumerate(signal.take_profit, 1):
            tp_lines.append(f"🎯 TP{i}: ${tp:.6f}")
        tp_text = "\n".join(tp_lines)
        
        # Extract rationale details
        regime = signal.rationale.get('regime', 'neutral')
        volatility = signal.rationale.get('volatility', 'medium')
        ta_score = signal.rationale.get('ta_score', signal.confidence)
        ml_prob = signal.rationale.get('ml_probability', 0.5)
        
        # Regime translation
        regime_ru = {
            'bullish': 'бычий',
            'bearish': 'медвежий', 
            'neutral': 'нейтральный',
            'sideways': 'боковой'
        }.get(regime, regime)
        
        # Volatility translation  
        vol_ru = {
            'low': 'низкая',
            'medium': 'средняя',
            'high': 'высокая'
        }.get(volatility, volatility)
        
        # Build message
        message = (
            f"{direction_emoji} <b>{direction_text}</b>\n\n"
            f"<b>Символ:</b> {signal.symbol} 📊\n"
            f"💰 <b>Цена входа:</b> ${signal.entry_price:.6f}\n\n"
            f"{tp_text}\n\n"
            f"🛑 <b>Стоп-лосс:</b> ${signal.stop_loss:.6f}\n"
            f"📊 <b>Размер позиции:</b> {signal.position_size_pct:.1f}%\n"
            f"📈 <b>Уровень успеха:</b> {signal.confidence * 100:.0f}%\n"
        )
        
        # Smart Money Metrics (Ultra Mode only usually)
        sm_metrics = signal.rationale.get('smart_money', {}).get('metrics', {})
        if sm_metrics:
            message += "\n🧠 <b>Smart Money Context:</b>\n"
            funding = sm_metrics.get('funding_rate', 0)
            ls_ratio = sm_metrics.get('ls_ratio', 1.0)
            liq_ratio = sm_metrics.get('liq_ratio', 1.0)
            
            message += f"• Funding Rate: <code>{funding * 100:.4f}%</code> {'🔥' if abs(funding) > 0.02 else ''}\n"
            message += f"• Long/Short Ratio: <code>{ls_ratio:.2f}</code> {'👥' if ls_ratio > 1.2 or ls_ratio < 0.8 else ''}\n"
            message += f"• Liq Ratio: <code>{liq_ratio:.2f}</code> {'💧' if liq_ratio > 2.0 or liq_ratio < 0.5 else ''}\n"
            
        message += f"\n🕐 <b>Время:</b> {signal.valid_until.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Add rationale
        message += f"🔍 <b>Почему сигнал на {'длинную' if 'BUY' in signal.direction else 'короткую'} позицию?</b>\n\n"
        message += "<b>Подробности сделки</b> 👇\n\n"
        
        # Technical details
        indicators = signal.rationale.get('indicators', {})
        reasons = []
        
        if isinstance(indicators, dict):
            # RSI logic
            rsi = indicators.get('rsi')
            # Extract scalar if it's a Series
            if hasattr(rsi, 'iloc'): rsi = rsi.iloc[-1] if len(rsi) > 0 else None
            
            if rsi is not None:
                if rsi < 30:
                    reasons.append(f"• RSI слабый &lt; 30 ({rsi:.1f})")
                elif rsi > 70:
                    reasons.append(f"• RSI сильный &gt; 70 ({rsi:.1f})")
                    
            # MACD logic
            macd_hist = indicators.get('macd_hist', 0)
            if hasattr(macd_hist, 'iloc'): macd_hist = macd_hist.iloc[-1] if len(macd_hist) > 0 else 0
            
            if macd_hist > 0:
                reasons.append("• Гистограмма MACD сильная")
            elif macd_hist < 0:
                reasons.append("• Гистограмма MACD слабая")
                
            # ADX logic
            adx = indicators.get('adx')
            if hasattr(adx, 'iloc'): adx = adx.iloc[-1] if len(adx) > 0 else None
            
            if adx is not None and adx > 25:
                reasons.append(f"• Сила тренда очень высокая (ADX ≥ 25, {adx:.1f})")
        
        # Add generic reasons if we don't have specific indicators
        if not reasons:
            reasons = [
                f"• Режим рынка: {regime_ru}",
                f"• Волатильность: {vol_ru}",
                f"• TA Score: {ta_score:.2f}",
                f"• ML вероятность: {ml_prob:.2f}"
            ]
        
        message += "\n".join(reasons)
        message += f"\n\n⚡ <b>Таймфрейм:</b> {signal.timeframe}\n"
        message += f"📊 <b>R/R соотношение:</b> 1:{signal.risk_reward:.1f}"
        
        return message


    async def cleanup(self):
        await self.notifier.close()
        for name, exchange in getattr(self, 'exchanges', {}).items():
            await exchange.close()

async def main():
    bot = Bot()
    try:
        await bot.initialize()

        # Use the Telegram instance from Notifier
        telegram_bot = bot.notifier.telegram

        # Run everything
        logger.info("Launching bot components...")

        await asyncio.gather(
            bot.run_loop(),
            telegram_bot.start_polling(),
            run_api(bot)
        )

    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
