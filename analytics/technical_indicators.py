#!/usr/bin/env python3
"""
🚀 Professional Technical Analysis System
TA-Lib Integration: RSI, MACD, EMA, ATR, Bollinger Bands, Volume Analysis
Multi-timeframe analysis with trend detection
"""
import talib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

@dataclass
class TechnicalSignal:
    indicator: str
    signal: str  # 'buy', 'sell', 'hold'
    strength: float  # 0-100
    value: float
    timestamp: float

@dataclass
class MultiTimeframeAnalysis:
    symbol: str
    timeframes: Dict[str, Dict]  # '15m': {signals, trend, strength}
    consensus: str  # 'strong_bullish', 'bullish', 'neutral', 'bearish', 'strong_bearish'
    confidence: float  # 0-100
    timestamp: float

class TechnicalAnalyzer:
    """Professional Technical Analysis Engine"""
    
    def __init__(self):
        self.timeframes = ['15m', '1h', '4h', '1d']
        self.indicators_config = {
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'ema': {'periods': [8, 21, 50, 200]},
            'atr': {'period': 14},
            'bb': {'period': 20, 'std': 2},
            'stoch': {'k_period': 14, 'd_period': 3},
            'adx': {'period': 14},
            'cci': {'period': 20},
            'williams_r': {'period': 14}
        }
    
    def calculate_rsi(self, close_prices: np.array, period: int = 14) -> Dict:
        """Calculate RSI with signal generation"""
        rsi = talib.RSI(close_prices, timeperiod=period)
        current_rsi = rsi[-1]
        prev_rsi = rsi[-2] if len(rsi) > 1 else current_rsi
        
        # Generate signal
        if current_rsi > 70:
            signal = 'sell'
            strength = min(100, (current_rsi - 70) * 3.33)
        elif current_rsi < 30:
            signal = 'buy' 
            strength = min(100, (30 - current_rsi) * 3.33)
        else:
            signal = 'hold'
            strength = 50
        
        # Divergence detection
        divergence = None
        if len(close_prices) > 20:
            price_trend = close_prices[-1] - close_prices[-10]
            rsi_trend = rsi[-1] - rsi[-10]
            if price_trend > 0 and rsi_trend < 0:
                divergence = 'bearish'
            elif price_trend < 0 and rsi_trend > 0:
                divergence = 'bullish'
        
        return {
            'value': current_rsi,
            'signal': signal,
            'strength': strength,
            'overbought': current_rsi > 70,
            'oversold': current_rsi < 30,
            'divergence': divergence,
            'trend': 'up' if current_rsi > prev_rsi else 'down'
        }
    
    def calculate_macd(self, close_prices: np.array, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD with histogram and signals"""
        macd_line, macd_signal, macd_histogram = talib.MACD(close_prices, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        
        current_macd = macd_line[-1]
        current_signal = macd_signal[-1]
        current_histogram = macd_histogram[-1]
        prev_histogram = macd_histogram[-2] if len(macd_histogram) > 1 else 0
        
        # Signal generation
        if current_macd > current_signal and current_histogram > 0:
            signal = 'buy'
            strength = min(100, abs(current_histogram) * 1000)
        elif current_macd < current_signal and current_histogram < 0:
            signal = 'sell'
            strength = min(100, abs(current_histogram) * 1000)
        else:
            signal = 'hold'
            strength = 50
        
        # Crossover detection
        crossover = None
        if len(macd_histogram) > 2:
            if prev_histogram <= 0 and current_histogram > 0:
                crossover = 'bullish'
            elif prev_histogram >= 0 and current_histogram < 0:
                crossover = 'bearish'
        
        return {
            'macd': current_macd,
            'signal_line': current_signal,
            'histogram': current_histogram,
            'signal': signal,
            'strength': strength,
            'crossover': crossover,
            'above_zero': current_macd > 0
        }
    
    def calculate_ema_system(self, close_prices: np.array, periods: List[int] = [8, 21, 50, 200]) -> Dict:
        """Calculate EMA system with trend analysis"""
        emas = {}
        for period in periods:
            emas[f'ema_{period}'] = talib.EMA(close_prices, timeperiod=period)[-1]
        
        current_price = close_prices[-1]
        
        # Trend analysis
        trend_score = 0
        if current_price > emas['ema_8']:
            trend_score += 25
        if emas['ema_8'] > emas['ema_21']:
            trend_score += 25
        if emas['ema_21'] > emas['ema_50']:
            trend_score += 25
        if emas['ema_50'] > emas['ema_200']:
            trend_score += 25
        
        # Signal generation
        if trend_score >= 75:
            signal = 'buy'
            strength = trend_score
        elif trend_score <= 25:
            signal = 'sell'
            strength = 100 - trend_score
        else:
            signal = 'hold'
            strength = 50
        
        return {
            **emas,
            'trend_score': trend_score,
            'signal': signal,
            'strength': strength,
            'trend': 'bullish' if trend_score > 50 else 'bearish',
            'golden_cross': emas['ema_50'] > emas['ema_200'] and emas['ema_8'] > emas['ema_21'],
            'death_cross': emas['ema_50'] < emas['ema_200'] and emas['ema_8'] < emas['ema_21']
        }
    
    def calculate_atr(self, high_prices: np.array, low_prices: np.array, close_prices: np.array, period: int = 14) -> Dict:
        """Calculate ATR for volatility and stop loss levels"""
        atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=period)
        current_atr = atr[-1]
        current_price = close_prices[-1]
        
        # Stop loss and take profit levels
        atr_multiplier_sl = 1.5  # Conservative stop loss
        atr_multiplier_tp = [2.0, 3.0, 4.0]  # Multiple take profit levels
        
        stop_loss_long = current_price - (current_atr * atr_multiplier_sl)
        stop_loss_short = current_price + (current_atr * atr_multiplier_sl)
        
        take_profit_long = [current_price + (current_atr * mult) for mult in atr_multiplier_tp]
        take_profit_short = [current_price - (current_atr * mult) for mult in atr_multiplier_tp]
        
        # Volatility assessment
        avg_atr = np.mean(atr[-10:])  # 10-period average
        volatility = 'high' if current_atr > avg_atr * 1.2 else 'low' if current_atr < avg_atr * 0.8 else 'normal'
        
        return {
            'atr': current_atr,
            'atr_percent': (current_atr / current_price) * 100,
            'volatility': volatility,
            'stop_loss_long': stop_loss_long,
            'stop_loss_short': stop_loss_short,
            'take_profit_long': take_profit_long,
            'take_profit_short': take_profit_short,
            'position_size_factor': 1.0 / (current_atr / current_price)  # For position sizing
        }
    
    def calculate_bollinger_bands(self, close_prices: np.array, period: int = 20, std: float = 2.0) -> Dict:
        """Calculate Bollinger Bands with squeeze detection"""
        upper_band, middle_band, lower_band = talib.BBANDS(close_prices, timeperiod=period, nbdevup=std, nbdevdn=std)
        
        current_price = close_prices[-1]
        current_upper = upper_band[-1]
        current_middle = middle_band[-1]
        current_lower = lower_band[-1]
        
        # Band position
        band_position = (current_price - current_lower) / (current_upper - current_lower)
        
        # Signal generation
        if current_price > current_upper:
            signal = 'sell'
            strength = min(100, (current_price - current_upper) / current_upper * 100 * 10)
        elif current_price < current_lower:
            signal = 'buy'
            strength = min(100, (current_lower - current_price) / current_lower * 100 * 10)
        else:
            signal = 'hold'
            strength = 50
        
        # Squeeze detection (bands contracting)
        band_width = (current_upper - current_lower) / current_middle
        avg_width = np.mean([(upper_band[i] - lower_band[i]) / middle_band[i] for i in range(-10, 0)])
        squeeze = band_width < avg_width * 0.8
        
        return {
            'upper_band': current_upper,
            'middle_band': current_middle,
            'lower_band': current_lower,
            'band_position': band_position,
            'signal': signal,
            'strength': strength,
            'squeeze': squeeze,
            'expanding': band_width > avg_width * 1.2
        }
    
    def calculate_stochastic(self, high_prices: np.array, low_prices: np.array, close_prices: np.array) -> Dict:
        """Calculate Stochastic Oscillator"""
        k_percent, d_percent = talib.STOCH(high_prices, low_prices, close_prices)
        
        current_k = k_percent[-1]
        current_d = d_percent[-1]
        
        # Signal generation
        if current_k > 80 and current_d > 80:
            signal = 'sell'
            strength = min(100, (current_k - 80) * 5)
        elif current_k < 20 and current_d < 20:
            signal = 'buy'
            strength = min(100, (20 - current_k) * 5)
        else:
            signal = 'hold'
            strength = 50
        
        return {
            'k_percent': current_k,
            'd_percent': current_d,
            'signal': signal,
            'strength': strength,
            'overbought': current_k > 80,
            'oversold': current_k < 20
        }
    
    def calculate_adx(self, high_prices: np.array, low_prices: np.array, close_prices: np.array, period: int = 14) -> Dict:
        """Calculate ADX for trend strength"""
        adx = talib.ADX(high_prices, low_prices, close_prices, timeperiod=period)
        plus_di = talib.PLUS_DI(high_prices, low_prices, close_prices, timeperiod=period)
        minus_di = talib.MINUS_DI(high_prices, low_prices, close_prices, timeperiod=period)
        
        current_adx = adx[-1]
        current_plus_di = plus_di[-1]
        current_minus_di = minus_di[-1]
        
        # Trend strength
        if current_adx > 25:
            trend_strength = 'strong'
        elif current_adx > 20:
            trend_strength = 'moderate'
        else:
            trend_strength = 'weak'
        
        # Direction
        if current_plus_di > current_minus_di:
            direction = 'bullish'
            signal = 'buy' if current_adx > 25 else 'hold'
        else:
            direction = 'bearish'
            signal = 'sell' if current_adx > 25 else 'hold'
        
        return {
            'adx': current_adx,
            'plus_di': current_plus_di,
            'minus_di': current_minus_di,
            'trend_strength': trend_strength,
            'direction': direction,
            'signal': signal,
            'strength': min(100, current_adx * 2)
        }
    
    def calculate_volume_analysis(self, close_prices: np.array, volume: np.array) -> Dict:
        """Advanced volume analysis"""
        # On Balance Volume
        obv = talib.OBV(close_prices, volume)
        current_obv = obv[-1]
        prev_obv = obv[-2] if len(obv) > 1 else current_obv
        
        # Volume Rate of Change
        volume_roc = talib.ROC(volume, timeperiod=10)
        current_volume_roc = volume_roc[-1]
        
        # Average volume
        avg_volume = np.mean(volume[-20:])
        current_volume = volume[-1]
        volume_ratio = current_volume / avg_volume
        
        # Signal generation
        price_change = close_prices[-1] - close_prices[-2] if len(close_prices) > 1 else 0
        
        if price_change > 0 and volume_ratio > 1.5:
            signal = 'buy'
            strength = min(100, volume_ratio * 30)
        elif price_change < 0 and volume_ratio > 1.5:
            signal = 'sell'
            strength = min(100, volume_ratio * 30)
        else:
            signal = 'hold'
            strength = 50
        
        return {
            'obv': current_obv,
            'obv_trend': 'up' if current_obv > prev_obv else 'down',
            'volume_roc': current_volume_roc,
            'volume_ratio': volume_ratio,
            'signal': signal,
            'strength': strength,
            'high_volume': volume_ratio > 2.0,
            'accumulation': price_change > 0 and current_obv > prev_obv,
            'distribution': price_change < 0 and current_obv < prev_obv
        }
    
    def comprehensive_analysis(self, data: pd.DataFrame) -> Dict:
        """Complete technical analysis of a symbol"""
        high_prices = data['high'].values
        low_prices = data['low'].values
        close_prices = data['close'].values
        volume = data['volume'].values if 'volume' in data.columns else np.ones(len(close_prices))
        
        # Calculate all indicators
        analysis = {
            'rsi': self.calculate_rsi(close_prices),
            'macd': self.calculate_macd(close_prices),
            'ema': self.calculate_ema_system(close_prices),
            'atr': self.calculate_atr(high_prices, low_prices, close_prices),
            'bb': self.calculate_bollinger_bands(close_prices),
            'stoch': self.calculate_stochastic(high_prices, low_prices, close_prices),
            'adx': self.calculate_adx(high_prices, low_prices, close_prices),
            'volume': self.calculate_volume_analysis(close_prices, volume)
        }
        
        # Generate consensus
        signals = []
        strengths = []
        
        for indicator, data in analysis.items():
            if 'signal' in data and 'strength' in data:
                signals.append(data['signal'])
                weight = 1.0
                if indicator in ['ema', 'adx']:  # Give more weight to trend indicators
                    weight = 1.5
                strengths.append(data['strength'] * weight)
        
        # Calculate consensus
        buy_signals = sum(1 for s in signals if s == 'buy')
        sell_signals = sum(1 for s in signals if s == 'sell')
        total_signals = len(signals)
        
        avg_strength = np.mean(strengths) if strengths else 50
        
        if buy_signals > sell_signals * 1.5:
            consensus = 'bullish'
            confidence = min(100, (buy_signals / total_signals) * 100 + (avg_strength - 50))
        elif sell_signals > buy_signals * 1.5:
            consensus = 'bearish'
            confidence = min(100, (sell_signals / total_signals) * 100 + (avg_strength - 50))
        else:
            consensus = 'neutral'
            confidence = 50
        
        # Enhanced consensus with strength
        if confidence > 80:
            consensus = f"strong_{consensus}"
        
        return {
            'analysis': analysis,
            'consensus': consensus,
            'confidence': confidence,
            'signals_summary': {
                'buy': buy_signals,
                'sell': sell_signals,
                'hold': total_signals - buy_signals - sell_signals,
                'total': total_signals
            },
            'timestamp': datetime.now().timestamp()
        }
    
    def multi_timeframe_analysis(self, symbol: str, data_dict: Dict[str, pd.DataFrame]) -> MultiTimeframeAnalysis:
        """Analyze multiple timeframes and generate consensus"""
        timeframe_results = {}
        
        for timeframe, data in data_dict.items():
            if len(data) > 50:  # Ensure enough data
                analysis = self.comprehensive_analysis(data)
                timeframe_results[timeframe] = {
                    'consensus': analysis['consensus'],
                    'confidence': analysis['confidence'],
                    'signals': analysis['signals_summary'],
                    'key_levels': {
                        'stop_loss': analysis['analysis']['atr']['stop_loss_long'],
                        'take_profit': analysis['analysis']['atr']['take_profit_long'],
                        'support': analysis['analysis']['bb']['lower_band'],
                        'resistance': analysis['analysis']['bb']['upper_band']
                    }
                }
        
        # Generate overall consensus
        consensus_scores = []
        confidence_weights = []
        
        timeframe_weight = {'15m': 1.0, '1h': 1.5, '4h': 2.0, '1d': 2.5}
        
        for tf, result in timeframe_results.items():
            weight = timeframe_weight.get(tf, 1.0)
            
            if 'strong_bullish' in result['consensus']:
                consensus_scores.append(2 * weight)
            elif 'bullish' in result['consensus']:
                consensus_scores.append(1 * weight)
            elif 'bearish' in result['consensus']:
                consensus_scores.append(-1 * weight)
            elif 'strong_bearish' in result['consensus']:
                consensus_scores.append(-2 * weight)
            else:
                consensus_scores.append(0)
            
            confidence_weights.append(result['confidence'] * weight)
        
        overall_score = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0
        overall_confidence = sum(confidence_weights) / len(confidence_weights) if confidence_weights else 50
        
        # Determine final consensus
        if overall_score > 1.5:
            final_consensus = 'strong_bullish'
        elif overall_score > 0.5:
            final_consensus = 'bullish'
        elif overall_score < -1.5:
            final_consensus = 'strong_bearish'
        elif overall_score < -0.5:
            final_consensus = 'bearish'
        else:
            final_consensus = 'neutral'
        
        return MultiTimeframeAnalysis(
            symbol=symbol,
            timeframes=timeframe_results,
            consensus=final_consensus,
            confidence=min(100, max(0, overall_confidence)),
            timestamp=datetime.now().timestamp()
        )

def detect_chart_patterns(data: pd.DataFrame) -> Dict:
    """Detect common chart patterns"""
    high_prices = data['high'].values
    low_prices = data['low'].values
    close_prices = data['close'].values
    
    patterns = {}
    
    # Double Top/Bottom detection (simplified)
    if len(close_prices) > 20:
        recent_highs = []
        recent_lows = []
        
        for i in range(10, len(close_prices) - 10):
            if all(high_prices[i] > high_prices[j] for j in range(i-5, i+6) if j != i):
                recent_highs.append((i, high_prices[i]))
            if all(low_prices[i] < low_prices[j] for j in range(i-5, i+6) if j != i):
                recent_lows.append((i, low_prices[i]))
        
        # Double top
        if len(recent_highs) >= 2:
            last_two_highs = recent_highs[-2:]
            if abs(last_two_highs[0][1] - last_two_highs[1][1]) / last_two_highs[0][1] < 0.02:
                patterns['double_top'] = True
        
        # Double bottom
        if len(recent_lows) >= 2:
            last_two_lows = recent_lows[-2:]
            if abs(last_two_lows[0][1] - last_two_lows[1][1]) / last_two_lows[0][1] < 0.02:
                patterns['double_bottom'] = True
    
    # Head and Shoulders (simplified)
    if len(recent_highs) >= 3:
        last_three = recent_highs[-3:]
        if (last_three[1][1] > last_three[0][1] and 
            last_three[1][1] > last_three[2][1] and
            abs(last_three[0][1] - last_three[2][1]) / last_three[0][1] < 0.05):
            patterns['head_and_shoulders'] = True
    
    return patterns

# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
    data = pd.DataFrame({
        'datetime': dates,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    analyzer = TechnicalAnalyzer()
    result = analyzer.comprehensive_analysis(data)
    
    print(f"📊 Technical Analysis Result:")
    print(f"Consensus: {result['consensus']}")
    print(f"Confidence: {result['confidence']:.1f}%")
    print(f"RSI: {result['analysis']['rsi']['value']:.1f} ({result['analysis']['rsi']['signal']})")
    print(f"MACD: {result['analysis']['macd']['signal']} (Histogram: {result['analysis']['macd']['histogram']:.4f})")
    print(f"EMA Trend: {result['analysis']['ema']['trend']} (Score: {result['analysis']['ema']['trend_score']})") 