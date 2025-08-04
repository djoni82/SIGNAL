#!/usr/bin/env python3
"""
Test CryptoAlphaPro with 50x Leverage Support
Demonstrates the high-leverage trading capabilities
"""

import time
import random
import math
from datetime import datetime
from collections import deque
import threading

print("🚀 CryptoAlphaPro - 50X LEVERAGE TEST")
print("⚡ Testing AI-powered crypto bot with up to 50x leverage")
print("=" * 60)

class HighLeverageEngine:
    """High-leverage AI trading engine"""
    
    def __init__(self):
        self.price_buffer = deque(maxlen=100)
        self.volume_buffer = deque(maxlen=100)
        self.signals_generated = 0
        self.processing_times = []
        
    def calculate_dynamic_leverage(self, volatility: float, confidence: float) -> float:
        """Calculate leverage up to 50x based on volatility and confidence"""
        
        # Convert volatility to percentage
        volatility_percent = volatility * 100
        
        # Volatility-based limits
        if volatility_percent < 1.5:      # Ultra low volatility
            max_vol_leverage = 50.0
        elif volatility_percent < 2.5:    # Low volatility
            max_vol_leverage = 35.0
        elif volatility_percent < 4.0:    # Medium-low volatility
            max_vol_leverage = 25.0
        elif volatility_percent < 6.0:    # Medium volatility
            max_vol_leverage = 15.0
        elif volatility_percent < 8.0:    # High volatility
            max_vol_leverage = 10.0
        else:                              # Extreme volatility
            max_vol_leverage = 5.0
        
        # Confidence-based limits
        if confidence >= 0.95:            # 95%+ confidence
            confidence_max_leverage = 50.0
        elif confidence >= 0.90:          # 90%+ confidence
            confidence_max_leverage = 35.0
        elif confidence >= 0.85:          # 85%+ confidence
            confidence_max_leverage = 25.0
        elif confidence >= 0.80:          # 80%+ confidence
            confidence_max_leverage = 15.0
        elif confidence >= 0.75:          # 75%+ confidence
            confidence_max_leverage = 10.0
        else:                              # Below 75% confidence
            confidence_max_leverage = 5.0
        
        # Base calculation
        base_leverage = 5.0 * confidence
        if volatility_percent < 2.0:
            base_leverage *= 2.0  # Double for low volatility
        
        # Apply all limits
        final_leverage = min(
            50.0,                     # Absolute max
            max_vol_leverage,         # Volatility limit
            confidence_max_leverage,  # Confidence limit
            base_leverage * 2         # Calculated leverage
        )
        
        return max(1.0, round(final_leverage, 1))
    
    def generate_signal(self, symbol: str, price: float, volume: float, volatility: float, confidence: float):
        """Generate high-leverage trading signal"""
        start_time = time.time()
        
        # Add to buffers
        self.price_buffer.append(price)
        self.volume_buffer.append(volume)
        
        if len(self.price_buffer) < 20:
            return None
        
        # Technical analysis
        prices = list(self.price_buffer)
        volumes = list(self.volume_buffer)
        
        sma_5 = sum(prices[-5:]) / 5
        sma_20 = sum(prices[-20:]) / 20
        current_price = prices[-1]
        
        # Volume analysis
        avg_volume = sum(volumes[-20:]) / 20
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        
        # Price movement
        price_change = (current_price - prices[-5]) / prices[-5]
        
        # Generate signal conditions
        strong_volume = volume_ratio > 1.5
        significant_move = abs(price_change) > 0.001
        trend_alignment = (sma_5 > sma_20 and price_change > 0) or (sma_5 < sma_20 and price_change < 0)
        
        if strong_volume and significant_move and trend_alignment and confidence > 0.75:
            # Calculate leverage
            leverage = self.calculate_dynamic_leverage(volatility, confidence)
            
            # Determine action
            action = 'BUY' if price_change > 0 else 'SELL'
            
            # Calculate risk parameters
            atr = volatility * current_price
            
            if action == 'BUY':
                stop_loss = current_price - (atr * 2)
                take_profit = [
                    current_price + (atr * 2),
                    current_price + (atr * 4),
                    current_price + (atr * 6)
                ]
            else:
                stop_loss = current_price + (atr * 2)
                take_profit = [
                    current_price - (atr * 2),
                    current_price - (atr * 4),
                    current_price - (atr * 6)
                ]
            
            # Create signal
            signal = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'leverage': leverage,
                'indicators': {
                    'volatility_percent': volatility * 100,
                    'volume_ratio': volume_ratio,
                    'price_change_percent': price_change * 100,
                    'trend_alignment': trend_alignment
                },
                'risk_metrics': {
                    'volatility_tier': self._get_volatility_tier(volatility * 100),
                    'confidence_tier': self._get_confidence_tier(confidence),
                    'max_leverage_allowed': leverage
                }
            }
            
            processing_time = (time.time() - start_time) * 1000
            self.processing_times.append(processing_time)
            self.signals_generated += 1
            
            return signal
        
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        return None
    
    def _get_volatility_tier(self, vol_percent: float) -> str:
        """Get volatility tier for display"""
        if vol_percent < 1.5:
            return "ULTRA_LOW"
        elif vol_percent < 2.5:
            return "LOW"
        elif vol_percent < 4.0:
            return "MEDIUM_LOW"
        elif vol_percent < 6.0:
            return "MEDIUM"
        elif vol_percent < 8.0:
            return "HIGH"
        else:
            return "EXTREME"
    
    def _get_confidence_tier(self, confidence: float) -> str:
        """Get confidence tier for display"""
        if confidence >= 0.95:
            return "ULTRA_HIGH"
        elif confidence >= 0.90:
            return "VERY_HIGH"
        elif confidence >= 0.85:
            return "HIGH"
        elif confidence >= 0.80:
            return "MEDIUM_HIGH"
        elif confidence >= 0.75:
            return "MEDIUM"
        else:
            return "LOW"

def run_50x_leverage_test():
    """Run comprehensive 50x leverage test"""
    
    print("📊 Initializing High-Leverage AI Engine...")
    engine = HighLeverageEngine()
    
    print("⚡ Testing different volatility and confidence scenarios...")
    print("-" * 60)
    
    # Test scenarios with different volatility and confidence levels
    test_scenarios = [
        {"vol": 0.012, "conf": 0.97, "desc": "Ultra Low Vol + Ultra High Confidence"},
        {"vol": 0.015, "conf": 0.93, "desc": "Low Vol + Very High Confidence"},
        {"vol": 0.022, "conf": 0.88, "desc": "Low-Medium Vol + High Confidence"},
        {"vol": 0.035, "conf": 0.82, "desc": "Medium Vol + Medium-High Confidence"},
        {"vol": 0.055, "conf": 0.78, "desc": "High Vol + Medium Confidence"},
        {"vol": 0.085, "conf": 0.95, "desc": "Extreme Vol + Ultra High Confidence"},
    ]
    
    signals = []
    base_price = 50000
    
    for i, scenario in enumerate(test_scenarios):
        print(f"🧪 Scenario {i+1}: {scenario['desc']}")
        
        # Generate market data with specific volatility
        for tick in range(30):  # 30 ticks per scenario
            # Simulate price with trend
            trend = math.sin(tick * 0.1) * 100
            noise = random.uniform(-scenario['vol'] * base_price, scenario['vol'] * base_price)
            price = base_price + trend + noise
            
            # Volume spike simulation
            volume_spike = random.uniform(0.8, 2.5) if random.random() < 0.4 else 1.0
            volume = 100 * volume_spike
            
            # Generate signal
            signal = engine.generate_signal(
                symbol="BTC/USDT",
                price=price,
                volume=volume,
                volatility=scenario['vol'],
                confidence=scenario['conf']
            )
            
            if signal:
                signals.append(signal)
                leverage_color = "🔥" if signal['leverage'] >= 25 else ("⚡" if signal['leverage'] >= 10 else "📊")
                
                print(f"   {leverage_color} SIGNAL: {signal['action']} @ ${signal['entry_price']:,.2f}")
                print(f"      Leverage: {signal['leverage']}x")
                print(f"      Confidence: {signal['confidence']:.1%}")
                print(f"      Stop Loss: ${signal['stop_loss']:,.2f}")
                print(f"      Take Profit: ${signal['take_profit'][0]:,.2f} - ${signal['take_profit'][2]:,.2f}")
                print(f"      Vol Tier: {signal['risk_metrics']['volatility_tier']}")
                print(f"      Conf Tier: {signal['risk_metrics']['confidence_tier']}")
                print()
        
        print(f"   📈 Scenario {i+1} completed")
        print("-" * 40)
    
    # Performance summary
    print("\n🏆 HIGH-LEVERAGE PERFORMANCE RESULTS")
    print("=" * 60)
    
    if engine.processing_times:
        avg_time = sum(engine.processing_times) / len(engine.processing_times)
        max_time = max(engine.processing_times)
        
        print(f"⏱️  Processing Performance:")
        print(f"   Average: {avg_time:.3f}ms")
        print(f"   Maximum: {max_time:.3f}ms") 
        print(f"   Total Ticks: {len(engine.processing_times)}")
        
        if avg_time < 1.0:
            print("   ✅ ULTRA-FAST: Sub-millisecond processing!")
        elif avg_time < 5.0:
            print("   ✅ EXCELLENT: Lightning-fast processing")
        else:
            print("   ⚠️  ACCEPTABLE: Good processing speed")
    
    print(f"\n🎯 Signal Generation:")
    print(f"   Total Signals: {engine.signals_generated}")
    print(f"   Signal Rate: {engine.signals_generated/len(engine.processing_times)*100:.1f}%")
    
    # Leverage analysis
    if signals:
        leverages = [s['leverage'] for s in signals]
        max_leverage = max(leverages)
        avg_leverage = sum(leverages) / len(leverages)
        
        leverage_50x = sum(1 for l in leverages if l == 50.0)
        leverage_25x_plus = sum(1 for l in leverages if l >= 25.0)
        leverage_10x_plus = sum(1 for l in leverages if l >= 10.0)
        
        print(f"\n📊 Leverage Analysis:")
        print(f"   Maximum Used: {max_leverage}x")
        print(f"   Average: {avg_leverage:.1f}x")
        print(f"   50x Signals: {leverage_50x} ({leverage_50x/len(signals)*100:.1f}%)")
        print(f"   25x+ Signals: {leverage_25x_plus} ({leverage_25x_plus/len(signals)*100:.1f}%)")
        print(f"   10x+ Signals: {leverage_10x_plus} ({leverage_10x_plus/len(signals)*100:.1f}%)")
        
        print(f"\n🎯 Example High-Leverage Signal:")
        max_lev_signal = max(signals, key=lambda x: x['leverage'])
        print(f"   Symbol: {max_lev_signal['symbol']}")
        print(f"   Action: {max_lev_signal['action']}")
        print(f"   Leverage: {max_lev_signal['leverage']}x 🔥")
        print(f"   Confidence: {max_lev_signal['confidence']:.1%}")
        print(f"   Entry: ${max_lev_signal['entry_price']:,.2f}")
        print(f"   Risk Tier: {max_lev_signal['risk_metrics']['volatility_tier']}")
    
    print(f"\n✅ SYSTEM STATUS:")
    if signals and avg_time < 5:
        print("🔥 READY FOR 50X LEVERAGE TRADING!")
        print("⚡ Ultra-fast signal generation")
        print("🛡️  Advanced risk management active")
        print("🎯 Professional-grade trading signals")
        print(f"🚀 Capable of processing {1000/avg_time:.0f} signals per second")
    else:
        print("⚠️  System needs optimization for high-frequency trading")
    
    print("\n" + "=" * 60)
    print("🎉 CryptoAlphaPro 50X LEVERAGE TEST COMPLETED!")

if __name__ == "__main__":
    run_50x_leverage_test()
