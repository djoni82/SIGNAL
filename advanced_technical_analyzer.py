#!/usr/bin/env python3
"""
Advanced Technical Analyzer - Расширенный технический анализ с паттернами
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

class AdvancedTechnicalAnalyzer:
    """Расширенный технический анализатор с паттернами и мультитаймфреймовым анализом"""
    
    def __init__(self):
        self.patterns = {}
        self.support_resistance_levels = {}
    
    def analyze_candlestick_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Анализирует паттерны свечей
        
        Args:
            df: DataFrame с данными OHLCV
            
        Returns:
            Словарь с найденными паттернами
        """
        patterns = {}
        
        if len(df) < 3:
            return patterns
        
        # Получаем последние свечи
        current = df.iloc[-1]
        prev1 = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        # Три белых солдата (Three White Soldiers)
        if (self._is_bullish_candle(current) and 
            self._is_bullish_candle(prev1) and 
            self._is_bullish_candle(prev2) and
            current['close'] > prev1['close'] > prev2['close']):
            patterns['bullish_three_white_soldiers'] = True
        
        # Три черных ворона (Three Black Crows)
        if (self._is_bearish_candle(current) and 
            self._is_bearish_candle(prev1) and 
            self._is_bearish_candle(prev2) and
            current['close'] < prev1['close'] < prev2['close']):
            patterns['bearish_three_black_crows'] = True
        
        # Доджи (Doji)
        if self._is_doji(current):
            patterns['doji'] = True
        
        # Молот (Hammer)
        if self._is_hammer(current):
            patterns['hammer'] = True
        
        # Повешенный (Hanging Man)
        if self._is_hanging_man(current):
            patterns['hanging_man'] = True
        
        # Утренняя звезда (Morning Star)
        if len(df) >= 3:
            if (self._is_bearish_candle(prev2) and 
                self._is_doji(prev1) and 
                self._is_bullish_candle(current)):
                patterns['morning_star'] = True
        
        # Вечерняя звезда (Evening Star)
        if len(df) >= 3:
            if (self._is_bullish_candle(prev2) and 
                self._is_doji(prev1) and 
                self._is_bearish_candle(current)):
                patterns['evening_star'] = True
        
        return patterns
    
    def _is_bullish_candle(self, candle: pd.Series) -> bool:
        """Проверяет, является ли свеча бычьей"""
        return candle['close'] > candle['open']
    
    def _is_bearish_candle(self, candle: pd.Series) -> bool:
        """Проверяет, является ли свеча медвежьей"""
        return candle['close'] < candle['open']
    
    def _is_doji(self, candle: pd.Series) -> bool:
        """Проверяет, является ли свеча доджи"""
        body_size = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        return body_size <= total_range * 0.1  # Тело не более 10% от общего диапазона
    
    def _is_hammer(self, candle: pd.Series) -> bool:
        """Проверяет, является ли свеча молотом"""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (lower_shadow > body_size * 2 and 
                upper_shadow < body_size * 0.5)
    
    def _is_hanging_man(self, candle: pd.Series) -> bool:
        """Проверяет, является ли свеча повешенным"""
        return self._is_hammer(candle)  # Та же форма, но в верхней части тренда
    
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """
        Рассчитывает уровни поддержки и сопротивления
        
        Args:
            df: DataFrame с данными OHLCV
            window: Окно для поиска экстремумов
            
        Returns:
            Словарь с уровнями поддержки и сопротивления
        """
        if len(df) < window:
            return {'support': 0, 'resistance': 0}
        
        # Находим локальные минимумы и максимумы
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        # Текущая цена
        current_price = df['close'].iloc[-1]
        
        # Находим ближайшие уровни
        resistance_levels = []
        support_levels = []
        
        for i in range(len(df) - window, len(df)):
            if df['high'].iloc[i] == highs.iloc[i]:
                resistance_levels.append(df['high'].iloc[i])
            if df['low'].iloc[i] == lows.iloc[i]:
                support_levels.append(df['low'].iloc[i])
        
        # Фильтруем уровни
        resistance_levels = [r for r in resistance_levels if r > current_price]
        support_levels = [s for s in support_levels if s < current_price]
        
        # Берем ближайшие уровни
        resistance = min(resistance_levels) if resistance_levels else current_price * 1.05
        support = max(support_levels) if support_levels else current_price * 0.95
        
        return {
            'support': support,
            'resistance': resistance
        }
    
    def analyze_multiple_timeframes(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Анализирует данные на нескольких таймфреймах
        
        Args:
            data_dict: Словарь с данными по таймфреймам
            
        Returns:
            Словарь с анализом по таймфреймам
        """
        mtf_analysis = {'timeframes': {}}
        
        for timeframe, df in data_dict.items():
            if len(df) < 20:
                continue
            
            # Рассчитываем индикаторы для каждого таймфрейма
            analysis = self._analyze_single_timeframe(df)
            mtf_analysis['timeframes'][timeframe] = analysis
        
        # Определяем общий тренд
        mtf_analysis['overall_trend'] = self._determine_overall_trend(mtf_analysis['timeframes'])
        
        return mtf_analysis
    
    def _analyze_single_timeframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Анализирует один таймфрейм"""
        analysis = {}
        
        # RSI
        analysis['rsi'] = self._calculate_rsi(df['close'])
        
        # EMA
        analysis['ema'] = {
            'ema_8': self._calculate_ema(df['close'], 8),
            'ema_21': self._calculate_ema(df['close'], 21)
        }
        
        # MACD
        macd_data = self._calculate_macd(df['close'])
        analysis['macd'] = macd_data
        
        # Bollinger Bands
        bb_data = self._calculate_bollinger_bands(df['close'])
        analysis['bollinger'] = bb_data
        
        # ADX
        adx_data = self._calculate_adx(df)
        analysis['adx'] = adx_data
        
        # Volume
        analysis['volume'] = self._analyze_volume(df)
        
        # Паттерны
        analysis['patterns'] = self.analyze_candlestick_patterns(df)
        
        # Определяем тренд
        analysis['trend'] = self._determine_trend(analysis)
        
        return analysis
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Рассчитывает RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Рассчитывает EMA"""
        return prices.ewm(span=period).mean().iloc[-1]
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Рассчитывает MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.iloc[-1],
            'signal': signal_line.iloc[-1],
            'histogram': histogram.iloc[-1]
        }
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """Рассчитывает Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        current_price = prices.iloc[-1]
        position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
        
        return {
            'upper': upper_band.iloc[-1],
            'middle': sma.iloc[-1],
            'lower': lower_band.iloc[-1],
            'position': position
        }
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Dict[str, float]:
        """Рассчитывает ADX"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothing
        tr_smooth = tr.rolling(window=period).mean()
        plus_di = (pd.Series(plus_dm).rolling(window=period).mean() / tr_smooth) * 100
        minus_di = (pd.Series(minus_dm).rolling(window=period).mean() / tr_smooth) * 100
        
        # ADX
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': adx.iloc[-1],
            'plus_di': plus_di.iloc[-1],
            'minus_di': minus_di.iloc[-1]
        }
    
    def _analyze_volume(self, df: pd.DataFrame, period: int = 20) -> Dict[str, float]:
        """Анализирует объем"""
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].rolling(window=period).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        return {
            'current': current_volume,
            'average': avg_volume,
            'ratio': volume_ratio
        }
    
    def _determine_trend(self, analysis: Dict[str, Any]) -> str:
        """Определяет тренд на основе анализа"""
        bullish_signals = 0
        bearish_signals = 0
        
        # RSI
        if 'rsi' in analysis:
            rsi = analysis['rsi']
            if rsi > 60:
                bullish_signals += 1
            elif rsi < 40:
                bearish_signals += 1
        
        # EMA
        if 'ema' in analysis:
            ema_data = analysis['ema']
            if ema_data['ema_8'] > ema_data['ema_21']:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # MACD
        if 'macd' in analysis:
            macd_data = analysis['macd']
            if macd_data['histogram'] > 0:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # ADX
        if 'adx' in analysis:
            adx_data = analysis['adx']
            if adx_data['adx'] >= 25:
                if adx_data['plus_di'] > adx_data['minus_di']:
                    bullish_signals += 1
                else:
                    bearish_signals += 1
        
        # Определяем тренд
        if bullish_signals > bearish_signals:
            return 'bullish'
        elif bearish_signals > bullish_signals:
            return 'bearish'
        else:
            return 'neutral'
    
    def _determine_overall_trend(self, timeframes: Dict[str, Any]) -> str:
        """Определяет общий тренд по всем таймфреймам"""
        bullish_count = 0
        bearish_count = 0
        
        for tf_data in timeframes.values():
            trend = tf_data.get('trend', 'neutral')
            if trend == 'bullish':
                bullish_count += 1
            elif trend == 'bearish':
                bearish_count += 1
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral' 