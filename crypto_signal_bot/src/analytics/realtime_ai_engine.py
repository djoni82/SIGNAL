"""
Real-time AI Engine for CryptoAlphaPro
Millisecond-level market analysis with ML predictions and news sentiment
"""

import asyncio
import numpy as np
import pandas as pd
import talib
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from collections import deque
import threading
from queue import Queue, Empty
import aiohttp
import re
from textblob import TextBlob
import hashlib


@dataclass
class MarketSignal:
    """Market signal data structure"""
    symbol: str
    exchange: str
    timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: List[float]
    leverage: float
    reason: str
    indicators: Dict[str, Any]
    ml_score: float
    news_sentiment: float
    volume_profile: Dict[str, float]
    risk_score: float
    execution_time_ms: float


class StreamProcessor:
    """High-performance stream data processor"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.price_buffer = deque(maxlen=window_size)
        self.volume_buffer = deque(maxlen=window_size)
        self.timestamp_buffer = deque(maxlen=window_size)
        self.lock = threading.Lock()
        
    def add_tick(self, price: float, volume: float, timestamp: datetime):
        """Add new tick data (thread-safe)"""
        with self.lock:
            self.price_buffer.append(price)
            self.volume_buffer.append(volume)
            self.timestamp_buffer.append(timestamp)
    
    def get_features(self) -> Optional[np.ndarray]:
        """Extract features for ML model"""
        if len(self.price_buffer) < 20:
            return None
            
        with self.lock:
            prices = np.array(list(self.price_buffer))
            volumes = np.array(list(self.volume_buffer))
        
        try:
            features = []
            
            # Price features
            features.extend([
                prices[-1],  # Current price
                np.mean(prices[-5:]),  # 5-tick average
                np.mean(prices[-20:]),  # 20-tick average
                np.std(prices[-20:]),  # 20-tick volatility
                (prices[-1] - prices[-5]) / prices[-5],  # 5-tick return
                (prices[-1] - prices[-20]) / prices[-20],  # 20-tick return
            ])
            
            # Volume features
            features.extend([
                volumes[-1],  # Current volume
                np.mean(volumes[-5:]),  # 5-tick volume average
                np.mean(volumes[-20:]),  # 20-tick volume average
                volumes[-1] / np.mean(volumes[-20:]) if np.mean(volumes[-20:]) > 0 else 1,  # Volume ratio
            ])
            
            # Technical indicators (if enough data)
            if len(prices) >= 14:
                rsi = talib.RSI(prices, timeperiod=14)[-1]
                features.append(rsi if not np.isnan(rsi) else 50)
            else:
                features.append(50)
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"❌ Error extracting features: {e}")
            return None


class NewsAnalyzer:
    """Real-time news sentiment analyzer"""
    
    def __init__(self):
        self.sentiment_cache = {}
        self.crypto_keywords = {
            'BTC': ['bitcoin', 'btc', 'satoshi'],
            'ETH': ['ethereum', 'eth', 'ether', 'vitalik'],
            'BNB': ['binance', 'bnb', 'cz'],
        }
        
    async def analyze_news(self, news_items: List[Dict]) -> Dict[str, float]:
        """Analyze news sentiment for different symbols"""
        sentiment_scores = {}
        
        for item in news_items:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            text = f"{title} {content}"
            
            # Extract sentiment
            blob = TextBlob(text)
            base_sentiment = blob.sentiment.polarity
            
            # Apply crypto-specific adjustments
            adjusted_sentiment = self._adjust_crypto_sentiment(text, base_sentiment)
            
            # Map to symbols
            affected_symbols = self._extract_symbols(text)
            
            for symbol in affected_symbols:
                if symbol not in sentiment_scores:
                    sentiment_scores[symbol] = []
                sentiment_scores[symbol].append(adjusted_sentiment)
        
        # Average sentiments
        final_scores = {}
        for symbol, scores in sentiment_scores.items():
            final_scores[symbol] = np.mean(scores)
            
        return final_scores
    
    def _adjust_crypto_sentiment(self, text: str, base_sentiment: float) -> float:
        """Adjust sentiment based on crypto-specific context"""
        bullish_words = ['moon', 'rocket', 'bull', 'pump', 'hodl', 'buy', 'bullish', 'adoption', 'institutional']
        bearish_words = ['crash', 'dump', 'bear', 'sell', 'bearish', 'regulation', 'ban', 'hack', 'scam']
        
        bullish_count = sum(1 for word in bullish_words if word in text)
        bearish_count = sum(1 for word in bearish_words if word in text)
        
        # Adjust based on crypto-specific words
        adjustment = (bullish_count - bearish_count) * 0.1
        adjusted = base_sentiment + adjustment
        
        return max(-1, min(1, adjusted))
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract cryptocurrency symbols from text"""
        symbols = []
        for symbol, keywords in self.crypto_keywords.items():
            if any(keyword in text for keyword in keywords):
                symbols.append(symbol)
        return symbols if symbols else ['BTC']  # Default to BTC


class MLPredictor:
    """Lightweight ML predictor for real-time inference"""
    
    def __init__(self):
        self.models = {}
        self.feature_scalers = {}
        self.prediction_cache = {}
        
    def load_model(self, symbol: str, model_path: str = None):
        """Load or initialize model for symbol"""
        if model_path:
            try:
                self.models[symbol] = torch.load(model_path, map_location='cpu')
                logger.info(f"📊 Loaded ML model for {symbol}")
            except Exception as e:
                logger.error(f"❌ Failed to load model for {symbol}: {e}")
                self._init_default_model(symbol)
        else:
            self._init_default_model(symbol)
    
    def _init_default_model(self, symbol: str):
        """Initialize simple neural network"""
        class SimplePredictor(nn.Module):
            def __init__(self, input_size=11):
                super().__init__()
                self.layers = nn.Sequential(
                    nn.Linear(input_size, 32),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(32, 16),
                    nn.ReLU(),
                    nn.Linear(16, 3)  # BUY, SELL, HOLD
                )
            
            def forward(self, x):
                return torch.softmax(self.layers(x), dim=-1)
        
        self.models[symbol] = SimplePredictor()
        self.models[symbol].eval()
        logger.info(f"🤖 Initialized default model for {symbol}")
    
    def predict(self, symbol: str, features: np.ndarray) -> Tuple[int, float]:
        """Make prediction (0=SELL, 1=HOLD, 2=BUY)"""
        if symbol not in self.models:
            self.load_model(symbol)
        
        try:
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features).unsqueeze(0)
                output = self.models[symbol](features_tensor)
                probabilities = output.numpy()[0]
                
                prediction = np.argmax(probabilities)
                confidence = probabilities[prediction]
                
                return prediction, float(confidence)
                
        except Exception as e:
            logger.error(f"❌ ML prediction error for {symbol}: {e}")
            return 1, 0.5  # Default to HOLD with low confidence


class RealtimeAIEngine:
    """Main AI engine for real-time market analysis"""
    
    def __init__(self, config, data_manager, risk_manager):
        self.config = config
        self.data_manager = data_manager
        self.risk_manager = risk_manager
        
        # Components
        self.stream_processors = {}
        self.news_analyzer = NewsAnalyzer()
        self.ml_predictor = MLPredictor()
        
        # Processing queues
        self.tick_queue = Queue(maxsize=10000)
        self.news_queue = Queue(maxsize=1000)
        self.signal_queue = Queue(maxsize=500)
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.running = False
        
        # Performance tracking
        self.processing_times = deque(maxlen=1000)
        self.signals_generated = 0
        
        # Configuration
        self.target_pairs = config.get_trading_pairs()
        self.confidence_threshold = config.get('signals.confidence_threshold', 0.7)
        
    async def start(self):
        """Start the AI engine"""
        self.running = True
        logger.info("🚀 Starting Real-time AI Engine...")
        
        # Initialize stream processors
        for pair in self.target_pairs:
            self.stream_processors[pair] = StreamProcessor()
            self.ml_predictor.load_model(pair.split('/')[0])
        
        # Start processing tasks
        tasks = [
            asyncio.create_task(self._tick_processor(), name="tick_processor"),
            asyncio.create_task(self._news_processor(), name="news_processor"),
            asyncio.create_task(self._signal_generator(), name="signal_generator"),
            asyncio.create_task(self._performance_monitor(), name="performance_monitor"),
        ]
        
        logger.success("✅ Real-time AI Engine started")
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"❌ AI Engine error: {e}")
        finally:
            self.running = False
    
    async def process_tick(self, exchange: str, symbol: str, price: float, volume: float, timestamp: datetime):
        """Process incoming tick data"""
        try:
            if not self.running or symbol not in self.stream_processors:
                return
            
            # Add to stream processor
            self.stream_processors[symbol].add_tick(price, volume, timestamp)
            
            # Queue for analysis
            if not self.tick_queue.full():
                self.tick_queue.put({
                    'exchange': exchange,
                    'symbol': symbol,
                    'price': price,
                    'volume': volume,
                    'timestamp': timestamp
                })
            
        except Exception as e:
            logger.error(f"❌ Error processing tick: {e}")
    
    async def process_news(self, news_items: List[Dict]):
        """Process news items"""
        try:
            if not self.running or not news_items:
                return
            
            if not self.news_queue.full():
                self.news_queue.put(news_items)
                
        except Exception as e:
            logger.error(f"❌ Error processing news: {e}")
    
    async def _tick_processor(self):
        """Process tick data queue"""
        while self.running:
            try:
                tick_data = self.tick_queue.get(timeout=0.1)
                await self._analyze_tick(tick_data)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Tick processor error: {e}")
                await asyncio.sleep(0.01)
    
    async def _analyze_tick(self, tick_data: Dict):
        """Analyze individual tick for signals"""
        start_time = time.time()
        
        try:
            symbol = tick_data['symbol']
            exchange = tick_data['exchange']
            
            # Get features from stream processor
            processor = self.stream_processors.get(symbol)
            if not processor:
                return
            
            features = processor.get_features()
            if features is None:
                return
            
            # ML prediction
            base_symbol = symbol.split('/')[0]
            ml_prediction, ml_confidence = self.ml_predictor.predict(base_symbol, features)
            
            # Technical analysis
            technical_signal = self._technical_analysis(processor)
            
            # Volume profile analysis
            volume_signal = self._volume_analysis(processor)
            
            # Combine signals
            combined_signal = self._combine_signals(
                ml_prediction, ml_confidence,
                technical_signal, volume_signal
            )
            
            if combined_signal['confidence'] >= self.confidence_threshold:
                # Create market signal
                signal = await self._create_market_signal(
                    symbol, exchange, tick_data, combined_signal
                )
                
                # Queue signal for execution
                if signal and not self.signal_queue.full():
                    self.signal_queue.put(signal)
                    self.signals_generated += 1
            
            # Track processing time
            processing_time = (time.time() - start_time) * 1000
            self.processing_times.append(processing_time)
            
            if processing_time > 10:  # Log if over 10ms
                logger.warning(f"⚠️  Slow tick processing: {processing_time:.2f}ms for {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Tick analysis error: {e}")
    
    def _technical_analysis(self, processor: StreamProcessor) -> Dict[str, Any]:
        """Fast technical analysis"""
        try:
            with processor.lock:
                prices = np.array(list(processor.price_buffer))
                volumes = np.array(list(processor.volume_buffer))
            
            if len(prices) < 20:
                return {'signal': 1, 'strength': 0.5}  # HOLD
            
            # Fast moving averages
            sma_5 = np.mean(prices[-5:])
            sma_20 = np.mean(prices[-20:])
            current_price = prices[-1]
            
            # Simple trend detection
            trend_signal = 2 if sma_5 > sma_20 and current_price > sma_5 else (0 if sma_5 < sma_20 and current_price < sma_5 else 1)
            
            # Volatility check
            volatility = np.std(prices[-20:]) / np.mean(prices[-20:])
            
            # Volume confirmation
            recent_volume = np.mean(volumes[-5:])
            avg_volume = np.mean(volumes[-20:])
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Calculate strength
            strength = min(0.9, abs(sma_5 - sma_20) / sma_20 + (volume_ratio - 1) * 0.1)
            
            return {
                'signal': trend_signal,
                'strength': strength,
                'volatility': volatility,
                'volume_ratio': volume_ratio
            }
            
        except Exception as e:
            logger.error(f"❌ Technical analysis error: {e}")
            return {'signal': 1, 'strength': 0.5}
    
    def _volume_analysis(self, processor: StreamProcessor) -> Dict[str, Any]:
        """Volume profile analysis"""
        try:
            with processor.lock:
                volumes = np.array(list(processor.volume_buffer))
                prices = np.array(list(processor.price_buffer))
            
            if len(volumes) < 10:
                return {'signal': 1, 'strength': 0.5}
            
            # Volume trend
            recent_vol = np.mean(volumes[-5:])
            avg_vol = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
            
            vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
            
            # Volume breakout detection
            if vol_ratio > 2.0:  # High volume breakout
                price_change = (prices[-1] - prices[-5]) / prices[-5]
                signal = 2 if price_change > 0 else 0  # BUY or SELL based on price direction
                strength = min(0.9, vol_ratio / 3)
            else:
                signal = 1  # HOLD
                strength = 0.5
            
            return {
                'signal': signal,
                'strength': strength,
                'volume_ratio': vol_ratio
            }
            
        except Exception as e:
            logger.error(f"❌ Volume analysis error: {e}")
            return {'signal': 1, 'strength': 0.5}
    
    def _combine_signals(self, ml_pred: int, ml_conf: float, 
                        tech_signal: Dict, vol_signal: Dict) -> Dict[str, Any]:
        """Combine different signals into final decision"""
        try:
            # Weight the signals
            ml_weight = 0.4
            tech_weight = 0.4
            vol_weight = 0.2
            
            # Convert to standardized format (0=SELL, 1=HOLD, 2=BUY)
            signals = [ml_pred, tech_signal['signal'], vol_signal['signal']]
            weights = [ml_weight * ml_conf, tech_weight * tech_signal['strength'], vol_weight * vol_signal['strength']]
            
            # Weighted average
            weighted_sum = sum(s * w for s, w in zip(signals, weights))
            total_weight = sum(weights)
            
            if total_weight == 0:
                return {'signal': 1, 'confidence': 0.5}  # HOLD
            
            weighted_avg = weighted_sum / total_weight
            
            # Determine final signal
            if weighted_avg > 1.6:
                final_signal = 2  # BUY
                confidence = min(0.95, (weighted_avg - 1.6) / 0.4 + 0.7)
            elif weighted_avg < 0.4:
                final_signal = 0  # SELL
                confidence = min(0.95, (0.4 - weighted_avg) / 0.4 + 0.7)
            else:
                final_signal = 1  # HOLD
                confidence = 0.5
            
            return {
                'signal': final_signal,
                'confidence': confidence,
                'components': {
                    'ml': {'prediction': ml_pred, 'confidence': ml_conf},
                    'technical': tech_signal,
                    'volume': vol_signal
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Signal combination error: {e}")
            return {'signal': 1, 'confidence': 0.5}
    
    async def _create_market_signal(self, symbol: str, exchange: str, 
                                  tick_data: Dict, combined_signal: Dict) -> Optional[MarketSignal]:
        """Create market signal object"""
        try:
            signal_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
            signal_type = signal_map[combined_signal['signal']]
            
            if signal_type == 'HOLD':
                return None
            
            current_price = tick_data['price']
            
            # Calculate risk parameters
            processor = self.stream_processors[symbol]
            with processor.lock:
                prices = np.array(list(processor.price_buffer))
            
            volatility = np.std(prices[-20:]) / np.mean(prices[-20:]) if len(prices) >= 20 else 0.02
            
            # ATR approximation
            atr = volatility * current_price
            
            # Stop loss and take profit
            if signal_type == 'BUY':
                stop_loss = current_price - (atr * 2)
                take_profit = [
                    current_price + (atr * 2),
                    current_price + (atr * 4),
                    current_price + (atr * 6)
                ]
            else:  # SELL
                stop_loss = current_price + (atr * 2)
                take_profit = [
                    current_price - (atr * 2),
                    current_price - (atr * 4),
                    current_price - (atr * 6)
                ]
            
            # Calculate leverage
            leverage = self._calculate_dynamic_leverage(volatility, combined_signal['confidence'])
            
            # Risk score
            risk_score = min(1.0, volatility * 10 + (1 - combined_signal['confidence']))
            
            # Processing time
            processing_time = self.processing_times[-1] if self.processing_times else 0
            
            return MarketSignal(
                symbol=symbol,
                exchange=exchange,
                timestamp=tick_data['timestamp'],
                signal_type=signal_type,
                confidence=combined_signal['confidence'],
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                leverage=leverage,
                reason=f"AI Combo: ML={combined_signal['components']['ml']['confidence']:.2f}, Tech={combined_signal['components']['technical']['strength']:.2f}",
                indicators=combined_signal['components'],
                ml_score=combined_signal['components']['ml']['confidence'],
                news_sentiment=0.0,  # Will be updated by news processor
                volume_profile={'ratio': combined_signal['components']['volume']['volume_ratio']},
                risk_score=risk_score,
                execution_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating market signal: {e}")
            return None
    
    def _calculate_dynamic_leverage(self, volatility: float, confidence: float) -> float:
        """Calculate dynamic leverage based on volatility and confidence (UP TO 50X)"""
        
        # Get configuration for high leverage controls
        max_leverage = 50.0  # Maximum 50x leverage
        base_leverage = 5.0  # Base leverage
        
        # Calculate volatility percentage
        volatility_percent = volatility * 100  # Convert to percentage
        
        # Volatility-based leverage limits
        if volatility_percent < 2.0:  # Low volatility
            max_vol_leverage = 50.0
        elif volatility_percent < 5.0:  # Medium volatility  
            max_vol_leverage = 25.0
        else:  # High volatility (>5%)
            max_vol_leverage = 10.0
        
        # Confidence-based leverage calculation
        if confidence >= 0.95:  # 95%+ confidence
            confidence_multiplier = 10.0  # Can use up to 50x
        elif confidence >= 0.85:  # 85%+ confidence
            confidence_multiplier = 5.0   # Up to 25x
        elif confidence >= 0.75:  # 75%+ confidence
            confidence_multiplier = 2.0   # Up to 10x
        else:  # Below 75% confidence
            confidence_multiplier = 1.0   # Conservative leverage
        
        # Calculate leverage components
        # 1. Base leverage adjusted by confidence
        base_adjusted = base_leverage * confidence_multiplier
        
        # 2. Volatility adjustment (reduce leverage for high volatility)
        vol_adjustment = max(0.1, 1 - (volatility_percent / 10))  # Reduce for high vol
        
        # 3. Final leverage calculation
        calculated_leverage = base_adjusted * vol_adjustment
        
        # Apply all limits
        final_leverage = min(
            max_leverage,           # Absolute maximum (50x)
            max_vol_leverage,       # Volatility-based limit
            calculated_leverage     # Calculated leverage
        )
        
        # Ensure minimum leverage
        final_leverage = max(1.0, final_leverage)
        
        # Round to 1 decimal place
        return round(final_leverage, 1)
    
    async def _news_processor(self):
        """Process news sentiment"""
        while self.running:
            try:
                news_items = self.news_queue.get(timeout=1.0)
                sentiment_scores = await self.news_analyzer.analyze_news(news_items)
                
                # Update signals with news sentiment
                self._update_signals_with_news(sentiment_scores)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"❌ News processor error: {e}")
                await asyncio.sleep(1)
    
    def _update_signals_with_news(self, sentiment_scores: Dict[str, float]):
        """Update existing signals with news sentiment"""
        # This would update signals in the queue or cache
        # For now, just log the sentiment
        for symbol, sentiment in sentiment_scores.items():
            logger.info(f"📰 News sentiment for {symbol}: {sentiment:.2f}")
    
    async def _signal_generator(self):
        """Generate and broadcast signals"""
        while self.running:
            try:
                signal = self.signal_queue.get(timeout=0.1)
                
                # Convert to standard format
                signal_dict = {
                    'symbol': signal.symbol,
                    'exchange': signal.exchange,
                    'action': signal.signal_type,
                    'confidence': signal.confidence,
                    'entry_price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'leverage': signal.leverage,
                    'timestamp': signal.timestamp.isoformat(),
                    'indicators': {
                        'ml_score': signal.ml_score,
                        'risk_score': signal.risk_score,
                        'execution_time_ms': signal.execution_time_ms,
                        'reason': signal.reason
                    }
                }
                
                # Broadcast signal (to Telegram, database, etc.)
                await self._broadcast_signal(signal_dict)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Signal generator error: {e}")
                await asyncio.sleep(0.01)
    
    async def _broadcast_signal(self, signal: Dict):
        """Broadcast signal to all subscribers"""
        try:
            logger.success(f"🎯 AI Signal: {signal['action']} {signal['symbol']} @ {signal['entry_price']:.6f} "
                          f"(Confidence: {signal['confidence']:.2f}, Risk: {signal['indicators']['risk_score']:.2f})")
            
            # Store in database
            if hasattr(self.data_manager, 'db_manager'):
                await self.data_manager.db_manager.insert_trade_signal(signal)
            
            # Cache in Redis
            if hasattr(self.data_manager, 'redis_manager'):
                await self.data_manager.redis_manager.cache_signal(signal)
            
            # TODO: Send to Telegram bot
            # TODO: Trigger risk management checks
            
        except Exception as e:
            logger.error(f"❌ Error broadcasting signal: {e}")
    
    async def _performance_monitor(self):
        """Monitor AI engine performance"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                if self.processing_times:
                    avg_time = np.mean(list(self.processing_times))
                    max_time = max(self.processing_times)
                    
                    logger.info(f"🔬 AI Engine Stats: "
                              f"Avg: {avg_time:.2f}ms, "
                              f"Max: {max_time:.2f}ms, "
                              f"Signals: {self.signals_generated}")
                    
                    if avg_time > 5:  # Warn if average over 5ms
                        logger.warning(f"⚠️  AI Engine performance degraded: {avg_time:.2f}ms average")
                
            except Exception as e:
                logger.error(f"❌ Performance monitor error: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.processing_times:
            return {}
        
        times = list(self.processing_times)
        return {
            'avg_processing_time_ms': np.mean(times),
            'max_processing_time_ms': max(times),
            'min_processing_time_ms': min(times),
            'p95_processing_time_ms': np.percentile(times, 95),
            'signals_generated': self.signals_generated,
            'queue_sizes': {
                'tick_queue': self.tick_queue.qsize(),
                'news_queue': self.news_queue.qsize(),
                'signal_queue': self.signal_queue.qsize()
            }
        }
    
    async def shutdown(self):
        """Shutdown AI engine"""
        logger.info("🛑 Shutting down AI Engine...")
        self.running = False
        self.executor.shutdown(wait=True)
        logger.success("✅ AI Engine shutdown completed") 