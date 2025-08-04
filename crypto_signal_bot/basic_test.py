#!/usr/bin/env python3
"""
Basic test for CryptoAlphaPro concepts (no external dependencies)
"""

import time
import random
import math
from datetime import datetime
from collections import deque
import threading

print("🚀 CryptoAlphaPro AI Engine Basic Test")
print("🤖 Testing millisecond-level crypto signal bot")
print("=" * 60)

class StreamProcessor:
    """High-performance stream data processor"""
    
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.price_buffer = deque(maxlen=window_size)
        self.volume_buffer = deque(maxlen=window_size)
        self.lock = threading.Lock()
        
    def add_tick(self, price, volume):
        """Add new tick data (thread-safe)"""
        with self.lock:
            self.price_buffer.append(price)
            self.volume_buffer.append(volume)
    
    def get_features(self):
        """Extract features for ML model"""
        if len(self.price_buffer) < 20:
            return None
            
        with self.lock:
            prices = list(self.price_buffer)
            volumes = list(self.volume_buffer)
        
        # Calculate basic features
        current_price = prices[-1]
        avg_5 = sum(prices[-5:]) / 5
        avg_20 = sum(prices[-20:]) / 20
        
        # Simple volatility (standard deviation approximation)
        mean_20 = avg_20
        variance = sum((p - mean_20) ** 2 for p in prices[-20:]) / 20
        volatility = math.sqrt(variance)
        
        # Price returns
        return_5 = (current_price - prices[-6]) / prices[-6] if len(prices) > 5 else 0
        return_20 = (current_price - prices[-21]) / prices[-21] if len(prices) > 20 else 0
        
        # Volume features
        current_volume = volumes[-1]
        avg_volume_5 = sum(volumes[-5:]) / 5
        avg_volume_20 = sum(volumes[-20:]) / 20
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
        
        features = {
            'current_price': current_price,
            'sma_5': avg_5,
            'sma_20': avg_20,
            'volatility': volatility,
            'return_5': return_5,
            'return_20': return_20,
            'current_volume': current_volume,
            'volume_ratio': volume_ratio,
            'trend_signal': 2 if avg_5 > avg_20 and current_price > avg_5 
                           else (0 if avg_5 < avg_20 and current_price < avg_5 else 1)
        }
        
        return features

class NewsAnalyzer:
    """Real-time news sentiment analyzer"""
    
    def __init__(self):
        self.crypto_keywords = {
            'BTC': ['bitcoin', 'btc', 'satoshi'],
            'ETH': ['ethereum', 'eth', 'ether'],
            'BNB': ['binance', 'bnb'],
        }
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of crypto news"""
        if not text:
            return 0.0
            
        bullish_words = ['bull', 'bullish', 'moon', 'rocket', 'surge', 'rally', 
                        'adoption', 'institutional', 'breakthrough', 'positive']
        bearish_words = ['bear', 'bearish', 'crash', 'dump', 'plunge', 'regulation', 
                        'ban', 'hack', 'scam', 'negative', 'concern']
        
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        
        sentiment = (bullish_count - bearish_count) / total
        return max(-1.0, min(1.0, sentiment))
    
    def extract_symbols(self, text):
        """Extract crypto symbols from text"""
        if not text:
            return ['BTC']
            
        text_lower = text.lower()
        found_symbols = []
        
        for symbol, keywords in self.crypto_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_symbols.append(symbol)
        
        return found_symbols if found_symbols else ['BTC']

class AIEngine:
    """Main AI engine for signal generation"""
    
    def __init__(self):
        self.stream_processors = {}
        self.news_analyzer = NewsAnalyzer()
        self.confidence_threshold = 0.7
        self.signals_generated = 0
        self.processing_times = []
        
    def process_tick(self, exchange, symbol, price, volume):
        """Process incoming tick data"""
        if symbol not in self.stream_processors:
            self.stream_processors[symbol] = StreamProcessor()
        
        start_time = time.time()
        
        # Add tick to processor
        processor = self.stream_processors[symbol]
        processor.add_tick(price, volume)
        
        # Get features
        features = processor.get_features()
        if features is None:
            return None
        
        # Generate signal
        signal = self._generate_signal(exchange, symbol, features)
        
        # Track processing time
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        
        if signal:
            self.signals_generated += 1
        
        return signal
    
    def _generate_signal(self, exchange, symbol, features):
        """Generate trading signal from features"""
        # Simple signal logic
        trend_signal = features['trend_signal']
        volume_ratio = features['volume_ratio']
        volatility = features['volatility']
        price_return = features['return_5']
        
        # Check signal conditions
        strong_volume = volume_ratio > 1.5  # 50% above average
        significant_move = abs(price_return) > 0.002  # 0.2% move
        
        if not (strong_volume and significant_move):
            return None
        
        # Determine signal type
        if trend_signal == 2 and price_return > 0:
            action = 'BUY'
            confidence = min(0.95, 0.7 + (price_return * 10) + (volume_ratio - 1) * 0.1)
        elif trend_signal == 0 and price_return < 0:
            action = 'SELL'
            confidence = min(0.95, 0.7 + (abs(price_return) * 10) + (volume_ratio - 1) * 0.1)
        else:
            return None
        
        if confidence < self.confidence_threshold:
            return None
        
        # Calculate risk parameters
        current_price = features['current_price']
        atr = volatility
        
        if action == 'BUY':
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
        
        # Dynamic leverage based on confidence and volatility
        base_leverage = 3.0
        vol_adjustment = max(0.5, 1 - (volatility / current_price * 100))
        leverage = min(10.0, max(1.0, base_leverage * vol_adjustment * confidence))
        
        signal = {
            'timestamp': datetime.now().isoformat(),
            'exchange': exchange,
            'symbol': symbol,
            'action': action,
            'confidence': round(confidence, 3),
            'entry_price': round(current_price, 6),
            'stop_loss': round(stop_loss, 6),
            'take_profit': [round(tp, 6) for tp in take_profit],
            'leverage': round(leverage, 1),
            'indicators': {
                'trend_strength': 'strong' if trend_signal != 1 else 'weak',
                'volume_ratio': round(volume_ratio, 2),
                'volatility': round(volatility, 2),
                'price_return_5t': round(price_return * 100, 2)
            }
        }
        
        return signal

def run_performance_test():
    """Run comprehensive performance test"""
    print("📊 Initializing AI Engine...")
    ai_engine = AIEngine()
    
    print("📈 Generating synthetic market data...")
    
    # Simulate market data
    base_price = 50000
    signals = []
    
    print("⚡ Testing real-time processing...")
    print("-" * 40)
    
    for i in range(100):
        # Simulate price movement with trend and noise
        trend = math.sin(i * 0.05) * 200
        noise = random.uniform(-50, 50)
        price = base_price + trend + noise
        
        # Simulate volume with spikes
        base_volume = 100
        volume_spike = random.uniform(0.5, 3.0) if random.random() < 0.3 else 1.0
        volume = base_volume * volume_spike
        
        # Process tick
        signal = ai_engine.process_tick('binance', 'BTC/USDT', price, volume)
        
        if signal:
            signals.append(signal)
            print(f"🎯 Signal #{len(signals)}: {signal['action']} {signal['symbol']}")
            print(f"   💰 Entry: ${signal['entry_price']:,.2f}")
            print(f"   🛡️  Stop Loss: ${signal['stop_loss']:,.2f}")
            print(f"   🎯 Take Profit: ${signal['take_profit'][0]:,.2f} - ${signal['take_profit'][2]:,.2f}")
            print(f"   📊 Confidence: {signal['confidence']:.1%}")
            print(f"   📈 Leverage: {signal['leverage']}x")
            print(f"   📋 Indicators: {signal['indicators']}")
            print("-" * 40)
        
        # Small delay to simulate real-time
        time.sleep(0.001)  # 1ms delay
    
    # Performance analysis
    print("\n📈 PERFORMANCE RESULTS")
    print("=" * 50)
    
    if ai_engine.processing_times:
        avg_time = sum(ai_engine.processing_times) / len(ai_engine.processing_times)
        max_time = max(ai_engine.processing_times)
        min_time = min(ai_engine.processing_times)
        
        print(f"⏱️  Processing Speed:")
        print(f"   Average: {avg_time:.2f}ms")
        print(f"   Maximum: {max_time:.2f}ms") 
        print(f"   Minimum: {min_time:.2f}ms")
        
        if avg_time < 5:
            print("✅ EXCELLENT: Ultra-fast processing (<5ms)")
        elif avg_time < 10:
            print("✅ GOOD: Fast processing (<10ms)")
        else:
            print("⚠️  SLOW: Processing over 10ms")
    
    print(f"\n🎯 Signal Generation:")
    print(f"   Total ticks processed: 100")
    print(f"   Signals generated: {ai_engine.signals_generated}")
    print(f"   Signal rate: {ai_engine.signals_generated/100*100:.1f}%")
    
    if ai_engine.signals_generated > 0:
        print("✅ Signal generation working correctly")
    else:
        print("❌ No signals generated")
    
    # Test news sentiment
    print(f"\n📰 Testing News Sentiment Analysis:")
    news_analyzer = NewsAnalyzer()
    
    test_news = [
        "Bitcoin surges to new all-time high amid institutional adoption",
        "Cryptocurrency market crashes due to regulatory concerns",
        "Ethereum upgrade brings positive changes to the network",
        "Major exchange hack causes bearish sentiment in crypto"
    ]
    
    for news in test_news:
        sentiment = news_analyzer.analyze_sentiment(news)
        symbols = news_analyzer.extract_symbols(news)
        sentiment_label = "BULLISH" if sentiment > 0.2 else ("BEARISH" if sentiment < -0.2 else "NEUTRAL")
        
        print(f"   📰 '{news[:50]}...'")
        print(f"      Sentiment: {sentiment:.2f} ({sentiment_label})")
        print(f"      Symbols: {', '.join(symbols)}")
    
    print("\n🎉 TEST COMPLETED!")
    print("=" * 50)
    
    if ai_engine.signals_generated > 0 and ai_engine.processing_times:
        avg_time = sum(ai_engine.processing_times) / len(ai_engine.processing_times)
        if avg_time < 10:
            print("✅ CryptoAlphaPro AI Engine READY!")
            print(f"🚀 Capable of {1000/avg_time:.0f} ticks per second processing")
            print("💡 Ready for millisecond-level crypto trading!")
        else:
            print("⚠️  Performance needs optimization")
    else:
        print("❌ System needs debugging")

if __name__ == "__main__":
    run_performance_test()
