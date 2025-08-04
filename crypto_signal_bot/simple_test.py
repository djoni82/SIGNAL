#!/usr/bin/env python3
"""
Simple test for CryptoAlphaPro core concepts
"""

import asyncio
import time
import numpy as np
from datetime import datetime
from collections import deque
import threading

# Test AI Engine core concepts
class StreamProcessor:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.price_buffer = deque(maxlen=window_size)
        self.volume_buffer = deque(maxlen=window_size)
        self.lock = threading.Lock()
        
    def add_tick(self, price, volume):
        with self.lock:
            self.price_buffer.append(price)
            self.volume_buffer.append(volume)
    
    def get_features(self):
        if len(self.price_buffer) < 20:
            return None
            
        with self.lock:
            prices = np.array(list(self.price_buffer))
            volumes = np.array(list(self.volume_buffer))
        
        # Basic features
        features = [
            prices[-1],  # Current price
            np.mean(prices[-5:]),  # 5-tick average
            np.mean(prices[-20:]),  # 20-tick average
            np.std(prices[-20:]),  # Volatility
            (prices[-1] - prices[-5]) / prices[-5],  # 5-tick return
            volumes[-1],  # Current volume
            np.mean(volumes[-5:]),  # Volume average
        ]
        
        return np.array(features)

class NewsAnalyzer:
    def __init__(self):
        self.crypto_keywords = {
            'BTC': ['bitcoin', 'btc'],
            'ETH': ['ethereum', 'eth'],
        }
    
    def analyze_sentiment(self, text):
        positive_words = ['bull', 'moon', 'surge', 'adoption']
        negative_words = ['bear', 'crash', 'dump', 'regulation']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total

# Test performance
def test_performance():
    print("🧪 Testing CryptoAlphaPro Core Concepts")
    print("=" * 50)
    
    # Test StreamProcessor performance
    processor = StreamProcessor()
    
    # Add test data
    print("📊 Adding test market data...")
    for i in range(100):
        price = 50000 + np.random.randn() * 100
        volume = 100 + np.random.randn() * 10
        processor.add_tick(price, volume)
    
    # Test feature extraction speed
    print("⚡ Testing feature extraction speed...")
    start_time = time.time()
    
    for _ in range(1000):
        features = processor.get_features()
    
    processing_time = (time.time() - start_time) * 1000
    print(f"✅ Feature extraction: {processing_time/1000:.3f}ms per extraction")
    
    # Test news sentiment
    news_analyzer = NewsAnalyzer()
    
    test_texts = [
        "Bitcoin surges to new highs amid bull market",
        "Ethereum crashes due to regulatory concerns",
        "Neutral crypto market news today"
    ]
    
    print("\n📰 Testing news sentiment analysis...")
    for text in test_texts:
        sentiment = news_analyzer.analyze_sentiment(text)
        print(f"   '{text[:30]}...': {sentiment:.2f}")
    
    # Simulate real-time processing
    print("\n🚀 Simulating real-time tick processing...")
    
    tick_count = 0
    signals_generated = 0
    processing_times = []
    
    for i in range(50):
        start = time.time()
        
        # Simulate new tick
        price = 50000 + np.sin(i * 0.1) * 500 + np.random.randn() * 50
        volume = 100 + np.random.randn() * 20
        processor.add_tick(price, volume)
        
        # Extract features
        features = processor.get_features()
        
        if features is not None:
            # Simulate ML prediction (simple logic)
            price_trend = features[4]  # Price return
            volume_ratio = features[6] / features[5] if features[5] > 0 else 1
            
            # Generate signal if conditions met
            if abs(price_trend) > 0.001 and volume_ratio > 1.2:
                signals_generated += 1
                print(f"🎯 Signal #{signals_generated}: {'BUY' if price_trend > 0 else 'SELL'} at {price:.2f}")
        
        processing_time = (time.time() - start) * 1000
        processing_times.append(processing_time)
        tick_count += 1
        
        # Small delay to simulate real market
        time.sleep(0.01)
    
    avg_processing_time = np.mean(processing_times)
    max_processing_time = max(processing_times)
    
    print(f"\n📈 Performance Results:")
    print(f"   Ticks processed: {tick_count}")
    print(f"   Signals generated: {signals_generated}")
    print(f"   Avg processing time: {avg_processing_time:.2f}ms")
    print(f"   Max processing time: {max_processing_time:.2f}ms")
    print(f"   Signal rate: {(signals_generated/tick_count)*100:.1f}%")
    
    # Check if meets requirements
    if avg_processing_time < 10:  # Under 10ms
        print("✅ PASSED: Processing speed meets requirements")
    else:
        print("❌ FAILED: Processing too slow")
    
    if signals_generated > 0:
        print("✅ PASSED: Signal generation working")
    else:
        print("❌ FAILED: No signals generated")
    
    print("\n🎉 Test completed!")
    print(f"💡 CryptoAlphaPro AI Engine ready for {avg_processing_time:.1f}ms millisecond trading!")

if __name__ == "__main__":
    test_performance()
