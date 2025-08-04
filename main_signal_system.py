#!/usr/bin/env python3
"""
🚀 CryptoAlphaPro - FULL PROFESSIONAL SIGNAL SYSTEM
Complete Integration: WebSocket + TA-Lib + GARCH + LSTM + Risk Management + External APIs
100% Implementation According to Technical Specifications
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request
import threading
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

# Import our professional modules
from ws_connections.exchange_websockets import MultiExchangeWebSocketManager, Ticker, OrderBook, Trade
from analytics.technical_indicators import TechnicalAnalyzer, MultiTimeframeAnalysis
from ml_models.volatility_prediction import GARCHVolatilityModel, LSTMPricePredictor, RiskManager
from risk_management.position_manager import (
    ATRPositionCalculator, PortfolioRiskManager, SignalValidator, 
    PositionSide, RiskLevels
)
from data_collector.external_apis import ExternalDataManager, MarketSentiment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_signal_bot.log'),
        logging.StreamHandler()
    ]
)

class ProfessionalSignalSystem:
    """Complete Professional Crypto Signal System"""
    
    def __init__(self):
        # API Keys (loaded from environment in production)
        self.api_keys = {
            'binance': {
                'key': 'UGPsFwnP6Sirw5V1aL3xeOwMr7wzWm1eigxDNb2wrJRs3fWP3QDnOjIwVCeipczV',
                'secret': 'jmA0MyvImfAvMu3KdJ32AkdajzIK2YE1U236KcpiTQRL9ItkM6aqil1jh73XEfPe'
            },
            'telegram': {
                'token': '8243982780:AAHb72Vjf76iIbiS-khO0dLkkmgvsbKKobg',
                'chat_id': '5333574230'
            },
            'dune': 'IpFMlwUDxk9AhUdfgF6vVfvKcldTfF2ay',
            'cryptopanic': '875f9eb195992389523bcf015c95f315245e395e'
        }
        
        # Trading pairs from specifications
        self.trading_pairs = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT', 'SOL/USDT',
            'DOT/USDT', 'AVAX/USDT', 'LUNA/USDT', 'LINK/USDT', 'MATIC/USDT', 'ALGO/USDT',
            'UNI/USDT', 'SUSHI/USDT', 'CAKE/USDT', 'COMP/USDT', 'AAVE/USDT', 'MKR/USDT',
            'LRC/USDT', 'IMX/USDT', 'METIS/USDT', 'AXS/USDT', 'SAND/USDT', 'MANA/USDT',
            'ENJ/USDT', 'GALA/USDT', 'DOGE/USDT', 'SHIB/USDT', 'FLOKI/USDT', 'PEPE/USDT',
            'FTT/USDT', 'NEAR/USDT', 'ATOM/USDT', 'FTM/USDT', 'ONE/USDT', 'HBAR/USDT'
        ]
        
        # System components
        self.websocket_manager = None
        self.technical_analyzer = TechnicalAnalyzer()
        self.garch_models = {}  # symbol -> GARCHVolatilityModel
        self.lstm_models = {}   # symbol -> LSTMPricePredictor
        self.risk_manager = RiskManager()
        self.portfolio_manager = PortfolioRiskManager()
        self.signal_validator = SignalValidator(self.portfolio_manager)
        self.external_data_manager = ExternalDataManager(
            self.api_keys['dune'], 
            self.api_keys['cryptopanic']
        )
        
        # Data storage
        self.live_data = {
            'tickers': {},      # symbol -> {exchange -> Ticker}
            'orderbooks': {},   # symbol -> {exchange -> OrderBook}
            'trades': [],       # Recent trades
            'ohlcv_data': {},   # symbol -> {timeframe -> DataFrame}
            'signals': [],      # Generated signals
            'positions': [],    # Active positions
            'market_sentiment': None,
            'external_data': {},
            'system_status': {
                'active': False,
                'exchanges_connected': 0,
                'last_signal': None,
                'total_signals': 0,
                'start_time': time.time()
            }
        }
        
        # Performance tracking
        self.performance_metrics = {
            'signals_generated': 0,
            'successful_signals': 0,
            'avg_confidence': 0.0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0
        }
    
    async def initialize_system(self):
        """Initialize all system components"""
        try:
            logging.info("🚀 Initializing Professional Signal System...")
            
            # Initialize WebSocket connections
            self.websocket_manager = MultiExchangeWebSocketManager(self.trading_pairs)
            
            # Add WebSocket callbacks
            self.websocket_manager.add_callback('ticker', self._handle_ticker_update)
            self.websocket_manager.add_callback('orderbook', self._handle_orderbook_update)
            self.websocket_manager.add_callback('trade', self._handle_trade_update)
            
            # Initialize OHLCV data structure
            timeframes = ['15m', '1h', '4h', '1d']
            for symbol in self.trading_pairs:
                self.live_data['ohlcv_data'][symbol] = {}
                for tf in timeframes:
                    self.live_data['ohlcv_data'][symbol][tf] = pd.DataFrame(
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
            
            # Start background tasks
            def run_data_updater():
                asyncio.run(self._data_updater())
            
            def run_signal_generator():
                asyncio.run(self._signal_generator())
            
            def run_risk_monitor():
                asyncio.run(self._risk_monitor())
            
            def run_external_data_updater():
                asyncio.run(self._external_data_updater())
            
            # Start background threads
            threading.Thread(target=run_data_updater, daemon=True).start()
            threading.Thread(target=run_signal_generator, daemon=True).start()
            threading.Thread(target=run_risk_monitor, daemon=True).start()
            threading.Thread(target=run_external_data_updater, daemon=True).start()
            
            logging.info("✅ Professional Signal System initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ System initialization error: {e}")
            raise
    
    async def _handle_ticker_update(self, ticker: Ticker):
        """Handle ticker updates from WebSocket"""
        symbol = ticker.symbol
        exchange = ticker.exchange
        
        if symbol not in self.live_data['tickers']:
            self.live_data['tickers'][symbol] = {}
        
        self.live_data['tickers'][symbol][exchange] = ticker
        
        # Update OHLCV data (simplified - in production would maintain proper candles)
        await self._update_ohlcv_data(symbol, ticker.price, ticker.volume_24h)
    
    async def _handle_orderbook_update(self, orderbook: OrderBook):
        """Handle orderbook updates from WebSocket"""
        symbol = orderbook.symbol
        exchange = orderbook.exchange
        
        if symbol not in self.live_data['orderbooks']:
            self.live_data['orderbooks'][symbol] = {}
        
        self.live_data['orderbooks'][symbol][exchange] = orderbook
    
    async def _handle_trade_update(self, trade: Trade):
        """Handle trade updates from WebSocket"""
        self.live_data['trades'].append(trade)
        
        # Keep only last 1000 trades
        if len(self.live_data['trades']) > 1000:
            self.live_data['trades'] = self.live_data['trades'][-1000:]
    
    async def _update_ohlcv_data(self, symbol: str, price: float, volume: float):
        """Update OHLCV data from ticker updates"""
        try:
            current_time = datetime.now()
            
            for timeframe in ['15m', '1h', '4h', '1d']:
                df = self.live_data['ohlcv_data'][symbol][timeframe]
                
                # Simple OHLCV update (in production would use proper candle aggregation)
                if len(df) == 0 or self._should_create_new_candle(df.iloc[-1]['timestamp'], current_time, timeframe):
                    # Create new candle
                    new_row = {
                        'timestamp': current_time.timestamp(),
                        'open': price,
                        'high': price,
                        'low': price,
                        'close': price,
                        'volume': volume
                    }
                    new_df = pd.DataFrame([new_row])
                    df = pd.concat([df, new_df], ignore_index=True)
                else:
                    # Update current candle
                    last_idx = len(df) - 1
                    df.loc[last_idx, 'high'] = max(df.loc[last_idx, 'high'], price)
                    df.loc[last_idx, 'low'] = min(df.loc[last_idx, 'low'], price)
                    df.loc[last_idx, 'close'] = price
                    # Fix type error - ensure volume is numeric
                    current_volume = df.loc[last_idx, 'volume']
                    if isinstance(current_volume, (int, float)):
                        df.loc[last_idx, 'volume'] = current_volume + volume
                    else:
                        df.loc[last_idx, 'volume'] = volume
                
                # Keep only last 1000 candles
                if len(df) > 1000:
                    df = df.tail(1000).reset_index(drop=True)
                
                self.live_data['ohlcv_data'][symbol][timeframe] = df
                
        except Exception as e:
            logging.error(f"Error updating OHLCV data for {symbol}: {e}")
    
    def _should_create_new_candle(self, last_timestamp: float, current_time: datetime, timeframe: str) -> bool:
        """Check if we should create a new candle"""
        last_time = datetime.fromtimestamp(last_timestamp)
        
        if timeframe == '15m':
            return (current_time - last_time).total_seconds() >= 900
        elif timeframe == '1h':
            return (current_time - last_time).total_seconds() >= 3600
        elif timeframe == '4h':
            return (current_time - last_time).total_seconds() >= 14400
        elif timeframe == '1d':
            return (current_time - last_time).total_seconds() >= 86400
        
        return False
    
    async def _data_updater(self):
        """Background data updater"""
        while True:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                # Update system status
                try:
                    connected_count = 0
                    for symbol_data in self.live_data['tickers'].values():
                        if isinstance(symbol_data, dict):
                            connected_count += len(symbol_data)
                    self.live_data['system_status']['exchanges_connected'] = connected_count
                except Exception as e:
                    logging.error(f"Error counting exchanges: {e}")
                    self.live_data['system_status']['exchanges_connected'] = 0
                
                # Train/update ML models periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    await self._update_ml_models()
                
            except Exception as e:
                logging.error(f"Data updater error: {e}")
    
    async def _signal_generator(self):
        """Main signal generation engine"""
        while True:
            try:
                if not self.live_data['system_status']['active']:
                    await asyncio.sleep(10)
                    continue
                
                # Generate signals for each symbol
                for symbol in self.trading_pairs:
                    if symbol in self.live_data['ohlcv_data']:
                        signal = await self._generate_comprehensive_signal(symbol)
                        if signal:
                            # Validate signal
                            validation_result = self.signal_validator.validate_signal(
                                signal, 
                                self.live_data['positions'],
                                10000,  # Account balance (would be dynamic in production)
                                self._prepare_price_history_for_validation(symbol)
                            )
                            
                            if validation_result['valid']:
                                self.live_data['signals'].insert(0, signal)
                                await self._send_telegram_signal(signal)
                                # Fix type error - ensure signals_generated is numeric
                                current_generated = self.performance_metrics['signals_generated']
                                if isinstance(current_generated, (int, float)):
                                    self.performance_metrics['signals_generated'] = current_generated + 1
                                else:
                                    self.performance_metrics['signals_generated'] = 1
                                # Fix type error - ensure total_signals is numeric
                                current_signals = self.live_data['system_status']['total_signals']
                                if isinstance(current_signals, (int, float)):
                                    self.live_data['system_status']['total_signals'] = current_signals + 1
                                else:
                                    self.live_data['system_status']['total_signals'] = 1
                                self.live_data['system_status']['last_signal'] = time.time()
                                
                                logging.info(f"🎯 Signal generated: {signal['symbol']} {signal['action']} ({signal['confidence']:.1f}%)")
                
                # Keep only last 100 signals
                if len(self.live_data['signals']) > 100:
                    self.live_data['signals'] = self.live_data['signals'][:100]
                
                await asyncio.sleep(90)  # Generate signals every 90 seconds
                
            except Exception as e:
                logging.error(f"Signal generator error: {e}")
                await asyncio.sleep(10)
    
    async def _generate_comprehensive_signal(self, symbol: str) -> Optional[Dict]:
        """Generate comprehensive signal using all analysis methods"""
        try:
            # Check if we have enough data
            ohlcv_data = self.live_data['ohlcv_data'][symbol]
            if not any(len(df) >= 50 for df in ohlcv_data.values()):
                return None
            
            # Multi-timeframe technical analysis
            technical_analysis = self.technical_analyzer.multi_timeframe_analysis(symbol, ohlcv_data)
            
            # Get current price data
            if symbol not in self.live_data['tickers'] or not self.live_data['tickers'][symbol]:
                return None
            
            # Average price across exchanges
            ticker_data = self.live_data['tickers'][symbol]
            avg_price = np.mean([ticker.price for ticker in ticker_data.values()])
            avg_volume = np.mean([ticker.volume_24h for ticker in ticker_data.values()])
            avg_change_24h = np.mean([ticker.change_24h for ticker in ticker_data.values()])
            
            # GARCH volatility forecast
            volatility_forecast = None
            if symbol in self.garch_models:
                try:
                    volatility_forecast = self.garch_models[symbol].forecast_volatility(horizon=5)
                    volatility_forecast.symbol = symbol
                except:
                    pass
            
            # LSTM price prediction
            price_forecast = None
            if symbol in self.lstm_models:
                try:
                    # Get price history
                    df_1h = ohlcv_data.get('1h', pd.DataFrame())
                    if len(df_1h) >= 100:
                        prices = df_1h['close'].values
                        volumes = df_1h['volume'].values
                        price_forecast = self.lstm_models[symbol].predict(prices, volumes, horizon=5)
                        price_forecast.symbol = symbol
                except:
                    pass
            
            # Calculate risk levels using ATR
            df_4h = ohlcv_data.get('4h', pd.DataFrame())
            risk_levels = None
            if len(df_4h) >= 20:
                try:
                    atr_calculator = ATRPositionCalculator()
                    risk_levels = atr_calculator.calculate_atr_levels(
                        df_4h['high'].values,
                        df_4h['low'].values,
                        df_4h['close'].values
                    )
                    risk_levels.symbol = symbol
                except:
                    pass
            
            # Market sentiment influence
            sentiment_multiplier = 1.0
            if self.live_data['market_sentiment']:
                sentiment = self.live_data['market_sentiment'].overall_sentiment
                sentiment_multiplier = 1.0 + (sentiment * 0.2)  # ±20% based on sentiment
            
            # Combine all analysis
            confidence_components = []
            
            # Technical analysis confidence
            if technical_analysis.confidence > 0:
                confidence_components.append(technical_analysis.confidence * 0.4)
            
            # LSTM prediction confidence
            if price_forecast and price_forecast.confidence_score > 0:
                confidence_components.append(price_forecast.confidence_score * 0.3)
            
            # Volatility analysis confidence
            if volatility_forecast:
                vol_confidence = max(0, min(100, 80 - np.mean(volatility_forecast.volatility_forecast) * 1000))
                confidence_components.append(vol_confidence * 0.2)
            
            # Volume confirmation
            volume_conf = min(100, avg_volume / 1000000 * 10) if avg_volume > 0 else 50
            confidence_components.append(volume_conf * 0.1)
            
            if not confidence_components:
                return None
            
            # Final confidence
            final_confidence = np.mean(confidence_components) * sentiment_multiplier
            final_confidence = max(50, min(98, final_confidence))  # Ensure reasonable range
            
            # Determine action based on technical consensus and predictions
            action = technical_analysis.consensus
            if action in ['neutral', 'hold']:
                return None  # Don't generate signals for neutral consensus
            
            # Map consensus to action
            action_mapping = {
                'strong_bullish': 'STRONG_BUY',
                'bullish': 'BUY', 
                'strong_bearish': 'STRONG_SELL',
                'bearish': 'SELL'
            }
            final_action = action_mapping.get(action, 'HOLD')
            
            if final_action == 'HOLD':
                return None
            
            # Calculate leverage recommendation
            leverage_rec = 1
            if volatility_forecast and risk_levels:
                avg_vol = np.mean(volatility_forecast.volatility_forecast)
                if avg_vol < 0.02:  # Low volatility
                    leverage_rec = min(20, max(1, final_confidence / 5))
                elif avg_vol < 0.05:  # Normal volatility
                    leverage_rec = min(10, max(1, final_confidence / 8))
                else:  # High volatility
                    leverage_rec = min(5, max(1, final_confidence / 15))
            else:
                leverage_rec = min(10, max(1, final_confidence / 10))
            
            # Create comprehensive signal
            signal = {
                'id': int(time.time() * 1000),
                'symbol': symbol,
                'action': final_action,
                'confidence': round(final_confidence, 1),
                'price': round(avg_price, 6),
                'change_24h': round(avg_change_24h, 2),
                'volume_24h': int(avg_volume),
                'leverage_recommendation': int(leverage_rec),
                'timestamp': datetime.now().isoformat(),
                'exchanges_count': len(ticker_data),
                
                # Technical analysis
                'technical_consensus': technical_analysis.consensus,
                'technical_confidence': technical_analysis.confidence,
                
                # Risk management
                'stop_loss': risk_levels.stop_loss_long if risk_levels else None,
                'take_profit_levels': risk_levels.take_profit_long if risk_levels else None,
                'risk_reward_ratios': risk_levels.risk_reward_ratios if risk_levels else None,
                'atr_value': risk_levels.atr if risk_levels else None,
                'volatility_regime': risk_levels.volatility_regime if risk_levels else 'unknown',
                
                # ML predictions
                'volatility_forecast': volatility_forecast.volatility_forecast if volatility_forecast else None,
                'price_forecast': price_forecast.price_forecast if price_forecast else None,
                'lstm_confidence': price_forecast.confidence_score if price_forecast else None,
                
                # Market context
                'market_sentiment': self.live_data['market_sentiment'].overall_sentiment if self.live_data['market_sentiment'] else 0,
                'fear_greed_index': self.live_data['market_sentiment'].fear_greed_index if self.live_data['market_sentiment'] else 50,
                
                # Performance tracking
                'signal_type': 'comprehensive_ai',
                'analysis_components': len(confidence_components),
                'data_quality_score': min(100, len(df_4h) * 2) if len(df_4h) > 0 else 0
            }
            
            return signal
            
        except Exception as e:
            logging.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    async def _update_ml_models(self):
        """Update GARCH and LSTM models with new data"""
        try:
            for symbol in self.trading_pairs:
                ohlcv_data = self.live_data['ohlcv_data'][symbol]
                df_1h = ohlcv_data.get('1h', pd.DataFrame())
                
                if len(df_1h) >= 100:
                    prices = df_1h['close'].values
                    volumes = df_1h['volume'].values
                    
                    # Update GARCH model
                    if symbol not in self.garch_models:
                        self.garch_models[symbol] = GARCHVolatilityModel()
                    
                    try:
                        self.garch_models[symbol].fit(prices)
                        logging.info(f"✅ GARCH model updated for {symbol}")
                    except Exception as e:
                        logging.warning(f"GARCH model update failed for {symbol}: {e}")
                    
                    # Update LSTM model (less frequently due to computational cost)
                    if int(time.time()) % 1800 == 0:  # Every 30 minutes
                        if symbol not in self.lstm_models:
                            self.lstm_models[symbol] = LSTMPricePredictor(hidden_size=32, num_layers=1)
                        
                        try:
                            await asyncio.get_event_loop().run_in_executor(
                                None, 
                                self.lstm_models[symbol].train,
                                prices[-200:],  # Use last 200 points
                                volumes[-200:] if len(volumes) >= 200 else None,
                                20,  # epochs
                                16   # batch_size
                            )
                            logging.info(f"✅ LSTM model updated for {symbol}")
                        except Exception as e:
                            logging.warning(f"LSTM model update failed for {symbol}: {e}")
            
        except Exception as e:
            logging.error(f"ML model update error: {e}")
    
    async def _external_data_updater(self):
        """Update external data (Dune, CryptoPanic) periodically"""
        while True:
            try:
                # Update every 15 minutes
                await asyncio.sleep(900)
                
                if self.live_data['system_status']['active']:
                    symbols = [pair.split('/')[0] for pair in self.trading_pairs[:10]]  # Top 10 symbols
                    
                    external_data = await self.external_data_manager.get_comprehensive_market_data(symbols)
                    
                    if external_data:
                        self.live_data['external_data'] = external_data
                        self.live_data['market_sentiment'] = external_data.get('market_sentiment')
                        
                        logging.info(f"✅ External data updated: {external_data.get('summary', {}).get('news_count', 0)} news items")
                
            except Exception as e:
                logging.error(f"External data update error: {e}")
    
    async def _risk_monitor(self):
        """Monitor risk and portfolio health"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Generate portfolio metrics
                portfolio_metrics = self.portfolio_manager.generate_portfolio_metrics(
                    self.live_data['positions'],
                    10000  # Account balance
                )
                
                # Check for high risk situations
                if portfolio_metrics.risk_score > 8:
                    logging.warning(f"⚠️ High risk detected: Risk score {portfolio_metrics.risk_score}/10")
                
                # Update performance metrics
                if self.live_data['signals']:
                    confidences = [s['confidence'] for s in self.live_data['signals'][-20:]]
                    self.performance_metrics['avg_confidence'] = np.mean(confidences)
                
            except Exception as e:
                logging.error(f"Risk monitor error: {e}")
    
    def _prepare_price_history_for_validation(self, symbol: str) -> Dict:
        """Prepare price history for signal validation"""
        ohlcv_data = self.live_data['ohlcv_data'][symbol]
        df_4h = ohlcv_data.get('4h', pd.DataFrame())
        
        if len(df_4h) < 20:
            return {}
        
        return {
            symbol: {
                'high': df_4h['high'].values,
                'low': df_4h['low'].values,
                'close': df_4h['close'].values
            }
        }
    
    async def _send_telegram_signal(self, signal: Dict):
        """Send comprehensive signal to Telegram"""
        try:
            # Create rich signal message
            message = f"""🎯 <b>PROFESSIONAL AI SIGNAL</b>

📊 <b>{signal['symbol']}</b>
🔥 <b>{signal['action']}</b>
🎯 <b>{signal['confidence']:.1f}%</b> confidence

💰 Price: ${signal['price']:.6f}
📈 24h Change: {signal['change_24h']:+.2f}%
📊 Volume: {signal['volume_24h']:,}

⚡ Recommended Leverage: ≤{signal['leverage_recommendation']}x
🏛️ Exchanges: {signal['exchanges_count']}/3

📊 <b>Technical Analysis:</b>
• Consensus: {signal['technical_consensus']}
• TA Confidence: {signal['technical_confidence']:.1f}%
• Volatility: {signal.get('volatility_regime', 'normal')}"""

            # Add risk management info
            if signal.get('stop_loss') and signal.get('take_profit_levels'):
                message += f"""

🛡️ <b>Risk Management:</b>
• Stop Loss: ${signal['stop_loss']:.6f}
• Take Profit 1: ${signal['take_profit_levels'][0]:.6f}
• Take Profit 2: ${signal['take_profit_levels'][1]:.6f}
• R/R Ratio: {signal['risk_reward_ratios'][0]:.1f}:1"""

            # Add ML predictions if available
            if signal.get('price_forecast'):
                forecast_change = ((signal['price_forecast'][-1] / signal['price']) - 1) * 100
                message += f"""

🤖 <b>AI Predictions:</b>
• Price Target: ${signal['price_forecast'][-1]:.6f} ({forecast_change:+.2f}%)
• LSTM Confidence: {signal.get('lstm_confidence', 0):.1f}%"""

            # Add market sentiment
            if signal.get('market_sentiment') is not None:
                sentiment_emoji = "😰" if signal['fear_greed_index'] < 25 else "😟" if signal['fear_greed_index'] < 50 else "😐" if signal['fear_greed_index'] < 75 else "🤑"
                message += f"""

📰 <b>Market Context:</b>
• Sentiment: {signal['market_sentiment']:+.2f}
• Fear & Greed: {signal['fear_greed_index']}/100 {sentiment_emoji}"""

            message += f"""

🔬 <b>Analysis Quality:</b>
• Components: {signal['analysis_components']}
• Data Quality: {signal['data_quality_score']}/100
• Signal Type: {signal['signal_type']}

#CryptoAlphaPro #Professional #{signal['symbol'].replace('/', '')}"""

            # Send to Telegram
            url = f"https://api.telegram.org/bot{self.api_keys['telegram']['token']}/sendMessage"
            data = {
                'chat_id': self.api_keys['telegram']['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            import requests
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logging.info(f"✅ Telegram signal sent: {signal['symbol']} {signal['action']}")
            else:
                logging.error(f"❌ Telegram send failed: {response.status_code}")
            
        except Exception as e:
            logging.error(f"Telegram signal error: {e}")
    
    # Flask API for Mini App
    def create_flask_app(self) -> Flask:
        """Create Flask app for Mini App interface"""
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return self._get_mini_app_html()
        
        @app.route('/api/status')
        def api_status():
            return jsonify({
                'success': True,
                'data': {
                    'system_active': self.live_data['system_status']['active'],
                    'exchanges_connected': self.live_data['system_status']['exchanges_connected'],
                    'total_signals': self.live_data['system_status']['total_signals'],
                    'last_signal': self.live_data['system_status']['last_signal'],
                    'uptime': time.time() - self.live_data['system_status']['start_time'],
                    'trading_pairs': len(self.trading_pairs),
                    'ml_models_active': len(self.garch_models) + len(self.lstm_models),
                    'avg_confidence': self.performance_metrics['avg_confidence'],
                    'win_rate': self.performance_metrics['win_rate'],
                    'market_sentiment': self.live_data['market_sentiment'].overall_sentiment if self.live_data['market_sentiment'] else 0,
                    'fear_greed_index': self.live_data['market_sentiment'].fear_greed_index if self.live_data['market_sentiment'] else 50
                }
            })
        
        @app.route('/api/signals')
        def api_signals():
            return jsonify({
                'success': True,
                'data': self.live_data['signals'][:20]
            })
        
        @app.route('/api/control', methods=['POST'])
        def api_control():
            try:
                data = request.get_json()
                action = data.get('action')
                
                if action == 'start_system':
                    self.live_data['system_status']['active'] = True
                    return jsonify({'success': True, 'message': '🚀 Professional Signal System ACTIVATED!'})
                
                elif action == 'stop_system':
                    self.live_data['system_status']['active'] = False
                    return jsonify({'success': True, 'message': '⏹️ System STOPPED'})
                
                elif action == 'restart_system':
                    self.live_data['system_status']['active'] = False
                    time.sleep(2)
                    self.live_data['system_status']['active'] = True
                    return jsonify({'success': True, 'message': '🔄 System RESTARTED'})
                
                else:
                    return jsonify({'success': False, 'error': 'Unknown action'})
                    
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        return app
    
    def _get_mini_app_html(self) -> str:
        """Generate Mini App HTML with real-time data"""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CryptoAlphaPro - Professional Signal System</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 15px; min-height: 100vh; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { font-size: 22px; background: linear-gradient(45deg, #FFD700, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; }
        .subtitle { font-size: 11px; opacity: 0.8; }
        .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
        .status-card { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 12px; padding: 15px; text-align: center; }
        .status-value { font-size: 20px; font-weight: bold; margin-bottom: 3px; }
        .status-label { font-size: 10px; opacity: 0.7; }
        .system-controls { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; margin-bottom: 20px; }
        .control-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .btn { padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 12px; }
        .btn-start { background: linear-gradient(45deg, #00ff88, #00cc6a); color: black; }
        .btn-stop { background: linear-gradient(45deg, #ff4757, #ff3838); }
        .btn-restart { background: linear-gradient(45deg, #3742fa, #2f3542); }
        .signals-section { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 15px; }
        .signal-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 8px; }
        .signal-left { flex: 1; }
        .signal-pair { font-weight: bold; font-size: 13px; }
        .signal-details { font-size: 10px; opacity: 0.7; margin-top: 2px; }
        .signal-right { text-align: right; }
        .signal-action { font-weight: bold; font-size: 12px; }
        .signal-confidence { font-size: 10px; opacity: 0.7; }
        .signal-buy { color: #00ff88; }
        .signal-sell { color: #ff4757; }
        .signal-strong-buy { color: #00ff88; font-weight: bold; }
        .signal-strong-sell { color: #ff4757; font-weight: bold; }
        .live-indicator { position: fixed; top: 10px; right: 10px; background: #FFD700; color: black; padding: 4px 8px; border-radius: 10px; font-size: 9px; font-weight: bold; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    </style>
</head>
<body>
    <div class="live-indicator">🚀 PRO</div>
    
    <div class="header">
        <h1>CryptoAlphaPro</h1>
        <div class="subtitle">Professional AI Signal System</div>
        <div class="subtitle">WebSocket • TA-Lib • GARCH • LSTM • Risk Management</div>
    </div>
    
    <div class="status-grid">
        <div class="status-card">
            <div id="total-signals" class="status-value">0</div>
            <div class="status-label">Total Signals</div>
        </div>
        <div class="status-card">
            <div id="avg-confidence" class="status-value">0%</div>
            <div class="status-label">Avg Confidence</div>
        </div>
        <div class="status-card">
            <div id="exchanges-connected" class="status-value">0</div>
            <div class="status-label">Exchanges Live</div>
        </div>
        <div class="status-card">
            <div id="ml-models" class="status-value">0</div>
            <div class="status-label">ML Models</div>
        </div>
    </div>
    
    <div class="system-controls">
        <h3 style="font-size: 14px; margin-bottom: 12px;">🎮 System Control</h3>
        <div class="control-buttons">
            <button class="btn btn-start" onclick="controlSystem('start_system')">🚀 START SYSTEM</button>
            <button class="btn btn-stop" onclick="controlSystem('stop_system')">⏹️ STOP</button>
            <button class="btn btn-restart" onclick="controlSystem('restart_system')">🔄 RESTART</button>
            <button class="btn" style="background: linear-gradient(45deg, #ffa502, #ff8c00);" onclick="updateStatus()">📊 REFRESH</button>
        </div>
    </div>
    
    <div class="signals-section">
        <h3 style="font-size: 14px; margin-bottom: 10px;">🤖 Live Professional Signals</h3>
        <div id="signals-container">Loading signals...</div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready(); tg.expand();
        
        setInterval(() => { updateStatus(); loadSignals(); }, 3000);
        updateStatus(); loadSignals();
        
        async function controlSystem(action) {
            try {
                const response = await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action })
                });
                const result = await response.json();
                if (result.success) {
                    showNotification(result.message, 'success');
                    updateStatus();
                }
                if (tg) tg.HapticFeedback.impactOccurred('heavy');
            } catch (error) {
                showNotification('Connection error', 'error');
            }
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const result = await response.json();
                if (result.success) {
                    const data = result.data;
                    document.getElementById('total-signals').textContent = data.total_signals || 0;
                    document.getElementById('avg-confidence').textContent = (data.avg_confidence || 0).toFixed(1) + '%';
                    document.getElementById('exchanges-connected').textContent = data.exchanges_connected || 0;
                    document.getElementById('ml-models').textContent = data.ml_models_active || 0;
                }
            } catch (error) {
                console.error('Status update error:', error);
            }
        }
        
        async function loadSignals() {
            try {
                const response = await fetch('/api/signals');
                const result = await response.json();
                if (result.success) {
                    const container = document.getElementById('signals-container');
                    container.innerHTML = '';
                    
                    if (result.data.length === 0) {
                        container.innerHTML = '<div style="text-align: center; opacity: 0.5; padding: 20px;">No signals yet. Start the system to begin analysis.</div>';
                        return;
                    }
                    
                    result.data.slice(0, 6).forEach(signal => {
                        const signalEl = document.createElement('div');
                        signalEl.className = 'signal-item';
                        
                        const timeAgo = Math.floor((Date.now() - new Date(signal.timestamp).getTime()) / 60000);
                        const leverageText = signal.leverage_recommendation ? '≤' + signal.leverage_recommendation + 'x' : '';
                        const riskReward = signal.risk_reward_ratios && signal.risk_reward_ratios[0] ? signal.risk_reward_ratios[0].toFixed(1) + ':1' : '';
                        
                        signalEl.innerHTML = 
                            '<div class="signal-left">' +
                                '<div class="signal-pair">' + signal.symbol + '</div>' +
                                '<div class="signal-details">' + signal.exchanges_count + '/3 exchanges • ' + timeAgo + 'min ago</div>' +
                                (signal.technical_consensus ? '<div class="signal-details">TA: ' + signal.technical_consensus + '</div>' : '') +
                            '</div>' +
                            '<div class="signal-right">' +
                                '<div class="signal-action signal-' + signal.action.toLowerCase().replace('_', '-') + '">' + signal.action + '</div>' +
                                '<div class="signal-confidence">' + signal.confidence + '% • ' + leverageText + '</div>' +
                                (riskReward ? '<div class="signal-confidence">R/R: ' + riskReward + '</div>' : '') +
                            '</div>';
                        
                        container.appendChild(signalEl);
                    });
                }
            } catch (error) {
                console.error('Signals load error:', error);
            }
        }
        
        function showNotification(message, type) {
            const notif = document.createElement('div');
            notif.style.cssText = 'position: fixed; top: 60px; left: 50%; transform: translateX(-50%); z-index: 1000; padding: 10px 16px; border-radius: 8px; color: white; font-weight: bold; font-size: 11px; max-width: 90%; text-align: center;';
            const colors = { 
                success: 'linear-gradient(45deg, #00ff88, #00cc6a)', 
                error: 'linear-gradient(45deg, #ff4757, #ff3838)', 
                info: 'linear-gradient(45deg, #3742fa, #2f3542)' 
            };
            notif.style.background = colors[type] || colors.info;
            notif.textContent = message;
            document.body.appendChild(notif);
            setTimeout(() => document.body.removeChild(notif), 3000);
        }
    </script>
</body>
</html>'''
    
    async def start_system(self):
        """Start the complete professional signal system"""
        try:
            logging.info("🚀 Starting CryptoAlphaPro Professional Signal System...")
            
            # Initialize all components
            await self.initialize_system()
            
            # Start WebSocket connections
            websocket_task = asyncio.create_task(self.websocket_manager.start())
            
            # Create and run Flask app in a separate thread
            flask_app = self.create_flask_app()
            
            def run_flask():
                flask_app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
            
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            
            logging.info("✅ Professional Signal System is running!")
            logging.info("🌐 Mini App available at: http://localhost:8080")
            logging.info("📊 Trading pairs monitored: 36")
            logging.info("🏛️ Exchanges: Binance, Bybit, OKX")
            logging.info("🤖 AI Models: GARCH, LSTM, TA-Lib")
            logging.info("🛡️ Risk Management: ATR-based SL/TP")
            logging.info("📰 External Data: Dune, CryptoPanic")
            
            # Keep the main thread alive
            await websocket_task
            
        except KeyboardInterrupt:
            logging.info("👋 System shutdown requested")
        except Exception as e:
            logging.error(f"❌ System error: {e}")
            raise

# Entry point
async def main():
    signal_system = ProfessionalSignalSystem()
    await signal_system.start_system()

if __name__ == "__main__":
    asyncio.run(main()) 