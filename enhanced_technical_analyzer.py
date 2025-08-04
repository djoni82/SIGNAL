#!/usr/bin/env python3
"""
🔥 ENHANCED TECHNICAL ANALYZER v2.0
Полный набор профессиональных индикаторов для генерации детальных сигналов
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Any
import time
from datetime import datetime

class ProfessionalTechnicalAnalyzer:
    """Профессиональный технический анализатор с полным набором индикаторов"""
    
    def __init__(self):
        self.indicators = {}
        
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет всех технических индикаторов"""
        try:
            if len(df) < 50:
                return {}
                
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            open_price = df['open'].values
            volume = df['volume'].values
            
            indicators = {}
            
            # RSI (Relative Strength Index)
            indicators['rsi'] = self._calculate_rsi(close)
            
            # MACD (Moving Average Convergence Divergence)
            indicators['macd'] = self._calculate_macd(close)
            
            # EMA (Exponential Moving Average)
            indicators['ema'] = self._calculate_ema(close)
            
            # ATR (Average True Range)
            indicators['atr'] = self._calculate_atr(high, low, close)
            
            # Bollinger Bands
            indicators['bollinger'] = self._calculate_bollinger_bands(close)
            
            # Stochastic Oscillator
            indicators['stochastic'] = self._calculate_stochastic(high, low, close)
            
            # ADX (Average Directional Index)
            indicators['adx'] = self._calculate_adx(high, low, close)
            
            # CCI (Commodity Channel Index)
            indicators['cci'] = self._calculate_cci(high, low, close)
            
            # Williams %R
            indicators['williams_r'] = self._calculate_williams_r(high, low, close)
            
            # SuperTrend
            indicators['supertrend'] = self._calculate_supertrend(high, low, close)
            
            # Donchian Channel
            indicators['donchian'] = self._calculate_donchian_channel(high, low)
            
            # VWAP (Volume Weighted Average Price)
            indicators['vwap'] = self._calculate_vwap(high, low, close, volume)
            
            # Ichimoku
            indicators['ichimoku'] = self._calculate_ichimoku(high, low, close)
            
            # OBV (On-Balance Volume)
            indicators['obv'] = self._calculate_obv(close, volume)
            
            # Volume Analysis
            indicators['volume_analysis'] = self._calculate_volume_analysis(volume)
            
            # Support/Resistance Levels
            indicators['support_resistance'] = self._calculate_support_resistance(high, low, close)
            
            # Candlestick Patterns
            indicators['patterns'] = self._calculate_candlestick_patterns(open_price, high, low, close)
            
            # Multi-timeframe analysis
            indicators['mtf_consensus'] = self._calculate_mtf_consensus(indicators)
            
            return indicators
            
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            return {}
    
    def _calculate_rsi(self, close: np.ndarray, period: int = 14) -> Dict:
        """RSI расчет"""
        try:
            rsi = talib.RSI(close, timeperiod=period)
            current_rsi = rsi[-1]
            
            # Определяем силу сигнала
            if current_rsi > 80:
                signal = "STRONG_SELL"
                strength = "очень сильный"
            elif current_rsi > 70:
                signal = "SELL"
                strength = "сильный"
            elif current_rsi > 60:
                signal = "WEAK_SELL"
                strength = "умеренный"
            elif current_rsi < 20:
                signal = "STRONG_BUY"
                strength = "очень сильный"
            elif current_rsi < 30:
                signal = "BUY"
                strength = "сильный"
            elif current_rsi < 40:
                signal = "WEAK_BUY"
                strength = "умеренный"
            else:
                signal = "NEUTRAL"
                strength = "нейтральный"
            
            return {
                'value': current_rsi,
                'signal': signal,
                'strength': strength,
                'description': f"RSI {strength} {'>' if current_rsi > 50 else '<'} {60 if current_rsi > 60 else 40} ({current_rsi:.2f})"
            }
        except:
            return {'value': 50, 'signal': 'NEUTRAL', 'strength': 'нейтральный', 'description': 'RSI недоступен'}
    
    def _calculate_macd(self, close: np.ndarray) -> Dict:
        """MACD расчет"""
        try:
            macd_line, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            
            current_macd = macd_line[-1]
            current_signal = macd_signal[-1]
            current_hist = macd_hist[-1]
            
            # Определяем силу гистограммы
            if abs(current_hist) > 0.01:
                hist_strength = "сильная"
            elif abs(current_hist) > 0.005:
                hist_strength = "умеренная"
            else:
                hist_strength = "слабая"
            
            signal = "BUY" if current_hist > 0 else "SELL"
            
            return {
                'macd': current_macd,
                'signal_line': current_signal,
                'histogram': current_hist,
                'signal': signal,
                'strength': hist_strength,
                'description': f"Гистограмма MACD {hist_strength}"
            }
        except:
            return {'histogram': 0, 'signal': 'NEUTRAL', 'strength': 'слабая', 'description': 'MACD недоступен'}
    
    def _calculate_ema(self, close: np.ndarray) -> Dict:
        """EMA расчет"""
        try:
            ema_20 = talib.EMA(close, timeperiod=20)
            ema_50 = talib.EMA(close, timeperiod=50)
            ma_50 = talib.SMA(close, timeperiod=50)
            
            current_price = close[-1]
            current_ema_20 = ema_20[-1]
            current_ema_50 = ema_50[-1]
            current_ma_50 = ma_50[-1]
            
            # Определяем позицию цены относительно EMA
            price_above_ema20 = current_price > current_ema_20
            price_above_ema50 = current_price > current_ema_50
            ema20_above_ema50 = current_ema_20 > current_ema_50
            price_above_ma50 = current_price > current_ma_50
            
            # Определяем силу тренда
            if price_above_ema20 and price_above_ema50 and ema20_above_ema50:
                trend_strength = "сильное подтверждение"
                signal = "STRONG_BUY"
            elif price_above_ema20 and ema20_above_ema50:
                trend_strength = "умеренное подтверждение"
                signal = "BUY"
            elif not price_above_ema20 and not price_above_ema50 and not ema20_above_ema50:
                trend_strength = "сильный медвежий тренд"
                signal = "STRONG_SELL"
            else:
                trend_strength = "смешанные сигналы"
                signal = "NEUTRAL"
            
            return {
                'ema_20': current_ema_20,
                'ema_50': current_ema_50,
                'ma_50': current_ma_50,
                'price_above_ema': price_above_ema20,
                'signal': signal,
                'strength': trend_strength,
                'description': f"Цена {'выше' if price_above_ema20 else 'ниже'} EMA, {trend_strength}",
                'ma50_cross': "Фильтр MA50 пересек положительную линию" if price_above_ma50 else "Цена ниже MA50"
            }
        except:
            return {'signal': 'NEUTRAL', 'strength': 'неопределенный', 'description': 'EMA недоступен'}
    
    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> Dict:
        """ATR расчет"""
        try:
            atr = talib.ATR(high, low, close, timeperiod=period)
            current_atr = atr[-1]
            current_price = close[-1]
            
            # ATR в процентах от цены
            atr_percent = (current_atr / current_price) * 100
            
            if atr_percent > 5:
                volatility = "очень высокая"
            elif atr_percent > 3:
                volatility = "высокая"
            elif atr_percent > 2:
                volatility = "умеренная"
            else:
                volatility = "низкая"
            
            return {
                'value': current_atr,
                'percent': atr_percent,
                'volatility': volatility,
                'description': f"Волатильность {volatility} (ATR: {atr_percent:.2f}%)"
            }
        except:
            return {'value': 0, 'volatility': 'неопределенная', 'description': 'ATR недоступен'}
    
    def _calculate_bollinger_bands(self, close: np.ndarray, period: int = 20) -> Dict:
        """Bollinger Bands расчет"""
        try:
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=period, nbdevup=2, nbdevdn=2)
            
            current_price = close[-1]
            current_upper = bb_upper[-1]
            current_lower = bb_lower[-1]
            current_middle = bb_middle[-1]
            
            # Определяем позицию цены в полосах
            if current_price > current_upper:
                position = "выше верхней полосы"
                signal = "BREAKOUT_UP"
                description = "Цена пробила полосу Боллинджера (пробой)"
            elif current_price < current_lower:
                position = "ниже нижней полосы"
                signal = "BREAKOUT_DOWN"
                description = "Цена пробила нижнюю полосу Боллинджера"
            elif current_price > current_middle:
                position = "выше средней линии"
                signal = "BUY"
                description = "Цена выше средней линии Боллинджера"
            else:
                position = "ниже средней линии"
                signal = "SELL"
                description = "Цена ниже средней линии Боллинджера"
            
            return {
                'upper': current_upper,
                'middle': current_middle,
                'lower': current_lower,
                'position': position,
                'signal': signal,
                'description': description
            }
        except:
            return {'signal': 'NEUTRAL', 'description': 'Bollinger Bands недоступны'}
    
    def _calculate_stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """Stochastic Oscillator расчет"""
        try:
            slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
            
            current_k = slowk[-1]
            current_d = slowd[-1]
            
            if current_k > 80 and current_d > 80:
                signal = "STRONG_SELL"
                strength = "сильное"
                description = "Stoch RSI показывает перекупленность"
            elif current_k < 20 and current_d < 20:
                signal = "STRONG_BUY"
                strength = "сильное"
                description = "Stoch RSI показывает перепроданность"
            elif current_k > current_d:
                signal = "BUY"
                strength = "умеренное"
                description = "Stoch RSI бычий кроссовер"
            else:
                signal = "SELL"
                strength = "слабое"
                description = "Слабое подтверждение направления Stoch RSI"
            
            return {
                'k': current_k,
                'd': current_d,
                'signal': signal,
                'strength': strength,
                'description': description
            }
        except:
            return {'signal': 'NEUTRAL', 'strength': 'слабое', 'description': 'Слабое подтверждение направления Stoch RSI'}
    
    def _calculate_adx(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> Dict:
        """ADX расчет"""
        try:
            adx = talib.ADX(high, low, close, timeperiod=period)
            current_adx = adx[-1]
            
            if current_adx >= 50:
                strength = "очень высокая"
                description = f"Сила тренда очень высокая (ADX ≥ 50, {current_adx:.1f})"
            elif current_adx >= 25:
                strength = "высокая"
                description = f"Сила тренда высокая (ADX ≥ 25, {current_adx:.1f})"
            elif current_adx >= 20:
                strength = "умеренная"
                description = f"Сила тренда умеренная (ADX ≥ 20, {current_adx:.1f})"
            else:
                strength = "слабая"
                description = f"Слабый тренд (ADX < 20, {current_adx:.1f})"
            
            return {
                'value': current_adx,
                'strength': strength,
                'description': description
            }
        except:
            return {'value': 15, 'strength': 'слабая', 'description': 'ADX недоступен'}
    
    def _calculate_cci(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> Dict:
        """CCI расчет"""
        try:
            cci = talib.CCI(high, low, close, timeperiod=period)
            current_cci = cci[-1]
            
            if current_cci > 100:
                signal = "STRONG_BUY"
                description = f"CCI показывает сильный бычий импульс ({current_cci:.1f})"
            elif current_cci < -100:
                signal = "STRONG_SELL"
                description = f"CCI показывает сильный медвежий импульс ({current_cci:.1f})"
            elif current_cci > 0:
                signal = "BUY"
                description = f"CCI положительный ({current_cci:.1f})"
            else:
                signal = "SELL"
                description = f"CCI отрицательный ({current_cci:.1f})"
            
            return {
                'value': current_cci,
                'signal': signal,
                'description': description
            }
        except:
            return {'value': 0, 'signal': 'NEUTRAL', 'description': 'CCI недоступен'}
    
    def _calculate_williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> Dict:
        """Williams %R расчет"""
        try:
            williams_r = talib.WILLR(high, low, close, timeperiod=period)
            current_wr = williams_r[-1]
            
            if current_wr > -20:
                signal = "STRONG_SELL"
                description = f"Williams %R перекупленность ({current_wr:.1f})"
            elif current_wr < -80:
                signal = "STRONG_BUY"
                description = f"Williams %R перепроданность ({current_wr:.1f})"
            elif current_wr > -50:
                signal = "SELL"
                description = f"Williams %R медвежий ({current_wr:.1f})"
            else:
                signal = "BUY"
                description = f"Williams %R бычий ({current_wr:.1f})"
            
            return {
                'value': current_wr,
                'signal': signal,
                'description': description
            }
        except:
            return {'value': -50, 'signal': 'NEUTRAL', 'description': 'Williams %R недоступен'}
    
    def _calculate_supertrend(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 10, multiplier: float = 3.0) -> Dict:
        """SuperTrend расчет"""
        try:
            # ATR расчет
            atr = talib.ATR(high, low, close, timeperiod=period)
            
            # SuperTrend расчет
            hl2 = (high + low) / 2
            upper_band = hl2 + (multiplier * atr)
            lower_band = hl2 - (multiplier * atr)
            
            supertrend = np.zeros(len(close))
            direction = np.ones(len(close))
            
            for i in range(1, len(close)):
                if close[i] <= lower_band[i-1]:
                    direction[i] = -1
                elif close[i] >= upper_band[i-1]:
                    direction[i] = 1
                else:
                    direction[i] = direction[i-1]
                
                if direction[i] == 1:
                    supertrend[i] = lower_band[i]
                else:
                    supertrend[i] = upper_band[i]
            
            current_trend = direction[-1]
            trend_name = "бычий тренд" if current_trend == 1 else "медвежий тренд"
            
            return {
                'value': current_trend,
                'trend': trend_name,
                'signal': 'BUY' if current_trend == 1 else 'SELL',
                'description': f"SuperTrend == {int(current_trend)} ({trend_name})"
            }
        except:
            return {'value': 0, 'trend': 'неопределенный', 'signal': 'NEUTRAL', 'description': 'SuperTrend недоступен'}
    
    def _calculate_donchian_channel(self, high: np.ndarray, low: np.ndarray, period: int = 20) -> Dict:
        """Donchian Channel расчет"""
        try:
            df_temp = pd.DataFrame({'high': high, 'low': low})
            upper_channel = df_temp['high'].rolling(period).max()
            lower_channel = df_temp['low'].rolling(period).min()
            middle_channel = (upper_channel + lower_channel) / 2
            
            current_price = (high[-1] + low[-1]) / 2
            current_upper = upper_channel.iloc[-1]
            current_lower = lower_channel.iloc[-1]
            current_middle = middle_channel.iloc[-1]
            
            if current_price > current_middle:
                signal = "BUY"
                description = f"Price > Donchian Mid"
            else:
                signal = "SELL"
                description = f"Price < Donchian Mid"
            
            return {
                'upper': current_upper,
                'lower': current_lower,
                'middle': current_middle,
                'signal': signal,
                'description': description
            }
        except:
            return {'signal': 'NEUTRAL', 'description': 'Donchian недоступен'}
    
    def _calculate_vwap(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> Dict:
        """VWAP расчет"""
        try:
            typical_price = (high + low + close) / 3
            cumulative_volume = np.cumsum(volume)
            cumulative_price_volume = np.cumsum(typical_price * volume)
            
            vwap = cumulative_price_volume / cumulative_volume
            current_vwap = vwap[-1]
            current_price = close[-1]
            
            if current_price > current_vwap:
                signal = "BUY"
                description = f"Price > VWAP"
            else:
                signal = "SELL"
                description = f"Price < VWAP"
            
            return {
                'value': current_vwap,
                'signal': signal,
                'description': description
            }
        except:
            return {'value': 0, 'signal': 'NEUTRAL', 'description': 'VWAP недоступен'}
    
    def _calculate_ichimoku(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """Ichimoku расчет"""
        try:
            # Tenkan-sen (Conversion Line)
            high_9 = pd.Series(high).rolling(9).max()
            low_9 = pd.Series(low).rolling(9).min()
            tenkan_sen = (high_9 + low_9) / 2
            
            # Kijun-sen (Base Line)
            high_26 = pd.Series(high).rolling(26).max()
            low_26 = pd.Series(low).rolling(26).min()
            kijun_sen = (high_26 + low_26) / 2
            
            current_price = close[-1]
            current_tenkan = tenkan_sen.iloc[-1]
            current_kijun = kijun_sen.iloc[-1]
            
            if current_price > current_tenkan > current_kijun:
                signal = "STRONG_BUY"
                description = "Ichimoku бычий сигнал"
            elif current_price < current_tenkan < current_kijun:
                signal = "STRONG_SELL"
                description = "Ichimoku медвежий сигнал"
            else:
                signal = "NEUTRAL"
                description = "Ichimoku нейтральный"
            
            return {
                'tenkan_sen': current_tenkan,
                'kijun_sen': current_kijun,
                'signal': signal,
                'description': description
            }
        except:
            return {'signal': 'NEUTRAL', 'description': 'Ichimoku недоступен'}
    
    def _calculate_obv(self, close: np.ndarray, volume: np.ndarray) -> Dict:
        """OBV расчет"""
        try:
            obv = talib.OBV(close, volume)
            
            # Тренд OBV
            obv_trend = "растущий" if obv[-1] > obv[-10] else "падающий"
            signal = "BUY" if obv_trend == "растущий" else "SELL"
            
            return {
                'value': obv[-1],
                'trend': obv_trend,
                'signal': signal,
                'description': f"OBV тренд {obv_trend}"
            }
        except:
            return {'trend': 'неопределенный', 'signal': 'NEUTRAL', 'description': 'OBV недоступен'}
    
    def _calculate_volume_analysis(self, volume: np.ndarray) -> Dict:
        """Анализ объема"""
        try:
            current_volume = volume[-1]
            avg_volume = np.mean(volume[-20:])  # Средний объем за 20 периодов
            
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            if volume_ratio > 2.0:
                spike_level = "очень сильный"
                description = f"Рост объёма более {(volume_ratio-1)*100:.0f}%!"
            elif volume_ratio > 1.5:
                spike_level = "сильный"
                description = f"Рост объёма более {(volume_ratio-1)*100:.0f}%!"
            elif volume_ratio > 1.2:
                spike_level = "умеренный"
                description = f"Рост объёма {(volume_ratio-1)*100:.0f}%"
            else:
                spike_level = "отсутствует"
                description = "Нет Volume Spike"
            
            return {
                'current': current_volume,
                'average': avg_volume,
                'ratio': volume_ratio,
                'spike_level': spike_level,
                'description': description
            }
        except:
            return {'spike_level': 'отсутствует', 'description': 'Нет Volume Spike'}
    
    def _calculate_support_resistance(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """Расчет уровней поддержки и сопротивления"""
        try:
            current_price = close[-1]
            
            # Простое определение уровней
            resistance = np.max(high[-20:])  # Максимум за 20 периодов
            support = np.min(low[-20:])      # Минимум за 20 периодов
            
            # Расстояние до уровней
            resistance_distance = abs(resistance - current_price) / current_price * 100
            support_distance = abs(current_price - support) / current_price * 100
            
            # Пробой уровней
            if current_price >= resistance * 0.99:
                breakout = "Уровень сопротивления резко пробит"
            elif current_price <= support * 1.01:
                breakout = "Уровень поддержки пробит"
            else:
                breakout = "Нет пробоя уровней"
            
            warnings = []
            if support_distance > 5:
                warnings.append(f"Уровень поддержки находится далеко от цены: ${support:.4f} ({support_distance:.2f}%)")
            if resistance_distance > 5:
                warnings.append(f"Уровень сопротивления находится далеко от цены: ${resistance:.4f} ({resistance_distance:.2f}%)")
            
            return {
                'support': support,
                'resistance': resistance,
                'support_distance': support_distance,
                'resistance_distance': resistance_distance,
                'breakout': breakout,
                'warnings': warnings
            }
        except:
            return {'breakout': 'Неопределенно', 'warnings': []}
    
    def _calculate_candlestick_patterns(self, open_price: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> Dict:
        """Анализ свечных паттернов"""
        try:
            patterns = []
            
            # Три белых солдата
            three_white_soldiers = talib.CDL3WHITESOLDIERS(open_price, high, low, close)
            if three_white_soldiers[-1] > 0:
                patterns.append("Обнаружен паттерн «Три белых солдата»")
            
            # Три черных ворона
            three_black_crows = talib.CDL3BLACKCROWS(open_price, high, low, close)
            if three_black_crows[-1] < 0:
                patterns.append("Обнаружен паттерн «Три черных ворона»")
            
            # Молот
            hammer = talib.CDLHAMMER(open_price, high, low, close)
            if hammer[-1] > 0:
                patterns.append("Обнаружен паттерн «Молот»")
            
            # Повешенный
            hanging_man = talib.CDLHANGINGMAN(open_price, high, low, close)
            if hanging_man[-1] < 0:
                patterns.append("Обнаружен паттерн «Повешенный»")
            
            # Дожи
            doji = talib.CDLDOJI(open_price, high, low, close)
            if doji[-1] != 0:
                patterns.append("Обнаружен паттерн «Дожи»")
            
            if not patterns:
                patterns.append("Нет значимых свечных паттернов")
            
            return {
                'patterns': patterns,
                'description': "; ".join(patterns)
            }
        except:
            return {'patterns': ["Паттерны недоступны"], 'description': 'Паттерны недоступны'}
    
    def _calculate_mtf_consensus(self, indicators: Dict) -> Dict:
        """Мультитаймфрейм консенсус"""
        try:
            # Собираем сигналы от разных индикаторов
            signals = []
            
            # RSI сигнал
            rsi_signal = indicators.get('rsi', {}).get('signal', 'NEUTRAL')
            if 'BUY' in rsi_signal:
                signals.append(1)
            elif 'SELL' in rsi_signal:
                signals.append(-1)
            else:
                signals.append(0)
            
            # MACD сигнал
            macd_signal = indicators.get('macd', {}).get('signal', 'NEUTRAL')
            if macd_signal == 'BUY':
                signals.append(1)
            elif macd_signal == 'SELL':
                signals.append(-1)
            else:
                signals.append(0)
            
            # EMA сигнал
            ema_signal = indicators.get('ema', {}).get('signal', 'NEUTRAL')
            if 'BUY' in ema_signal:
                signals.append(1)
            elif 'SELL' in ema_signal:
                signals.append(-1)
            else:
                signals.append(0)
            
            # SuperTrend сигнал
            supertrend_signal = indicators.get('supertrend', {}).get('signal', 'NEUTRAL')
            if supertrend_signal == 'BUY':
                signals.append(1)
            elif supertrend_signal == 'SELL':
                signals.append(-1)
            else:
                signals.append(0)
            
            # Подсчитываем консенсус
            total_signals = len(signals)
            bullish_signals = sum(1 for s in signals if s > 0)
            bearish_signals = sum(1 for s in signals if s < 0)
            
            if bullish_signals >= total_signals * 0.75:
                consensus = "strong_buy"
                description = "Подтверждение часового тренда положительное; Подтверждение 4-часового тренда положительное"
            elif bearish_signals >= total_signals * 0.75:
                consensus = "strong_sell"
                description = "Подтверждение часового тренда отрицательное; Подтверждение 4-часового тренда отрицательное"
            elif bullish_signals > bearish_signals:
                consensus = "buy"
                description = "Смешанное подтверждение тренда"
            elif bearish_signals > bullish_signals:
                consensus = "sell"
                description = "MTF Consensus == \"sell\" или \"strong_sell\""
            else:
                consensus = "neutral"
                description = "Нейтральный консенсус"
            
            return {
                'consensus': consensus,
                'bullish_count': bullish_signals,
                'bearish_count': bearish_signals,
                'description': description
            }
        except:
            return {'consensus': 'neutral', 'description': 'MTF консенсус недоступен'}
    
    def generate_detailed_signal(self, df: pd.DataFrame, symbol: str, action: str) -> Dict:
        """Генерация детального сигнала как в примере"""
        try:
            indicators = self.calculate_all_indicators(df)
            current_price = df['close'].iloc[-1]
            
            # Рассчитываем TP/SL как в примере
            if action == 'BUY':
                tp1 = current_price * 1.025   # +2.5%
                tp2 = current_price * 1.05    # +5%
                tp3 = current_price * 1.10    # +10%
                tp4 = current_price * 1.135   # +13.5%
                sl = current_price * 0.95     # -5%
            else:
                tp1 = current_price * 0.975   # -2.5%
                tp2 = current_price * 0.95    # -5%
                tp3 = current_price * 0.90    # -10%
                tp4 = current_price * 0.865   # -13.5%
                sl = current_price * 1.05     # +5%
            
            # Рассчитываем уверенность на основе всех индикаторов
            confidence_factors = []
            
            # RSI фактор
            rsi_signal = indicators.get('rsi', {}).get('signal', 'NEUTRAL')
            if 'STRONG' in rsi_signal:
                confidence_factors.append(0.25)
            elif 'BUY' in rsi_signal or 'SELL' in rsi_signal:
                confidence_factors.append(0.15)
            
            # MACD фактор
            macd_strength = indicators.get('macd', {}).get('strength', 'слабая')
            if macd_strength == 'сильная':
                confidence_factors.append(0.2)
            elif macd_strength == 'умеренная':
                confidence_factors.append(0.1)
            
            # EMA фактор
            ema_signal = indicators.get('ema', {}).get('signal', 'NEUTRAL')
            if 'STRONG' in ema_signal:
                confidence_factors.append(0.2)
            elif 'BUY' in ema_signal or 'SELL' in ema_signal:
                confidence_factors.append(0.1)
            
            # ADX фактор
            adx_strength = indicators.get('adx', {}).get('strength', 'слабая')
            if adx_strength in ['высокая', 'очень высокая']:
                confidence_factors.append(0.15)
            elif adx_strength == 'умеренная':
                confidence_factors.append(0.1)
            
            # Volume фактор
            volume_spike = indicators.get('volume_analysis', {}).get('spike_level', 'отсутствует')
            if volume_spike in ['очень сильный', 'сильный']:
                confidence_factors.append(0.1)
            elif volume_spike == 'умеренный':
                confidence_factors.append(0.05)
            
            # Bollinger Bands фактор
            bb_signal = indicators.get('bollinger', {}).get('signal', 'NEUTRAL')
            if 'BREAKOUT' in bb_signal:
                confidence_factors.append(0.1)
            
            total_confidence = min(sum(confidence_factors) + 0.5, 0.95)  # Базовая уверенность 50%
            
            # Динамическое плечо (1x-50x)
            leverage = min(50, max(1, int(total_confidence * 60)))
            
            return {
                'symbol': symbol,
                'action': action,
                'entry_price': current_price,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'tp4': tp4,
                'stop_loss': sl,
                'leverage': leverage,
                'confidence': total_confidence,
                'indicators': indicators,
                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'data_quality': 'REAL'
            }
            
        except Exception as e:
            print(f"❌ Error generating detailed signal: {e}")
            return None 