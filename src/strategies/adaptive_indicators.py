import pandas as pd
import numpy as np
from typing import Dict, Tuple
from src.strategies.models import MarketRegime

class ImprovedAdaptiveIndicatorEngine:
    
    def calculate_adaptive_indicators(self, data: pd.DataFrame, regime: MarketRegime) -> Dict:
        indicators = {}
        
        # Basic Indicators
        indicators['rsi'] = self._calculate_rsi(data['close'])
        indicators['ema_12'] = data['close'].ewm(span=12, adjust=False).mean()
        indicators['ema_26'] = data['close'].ewm(span=26, adjust=False).mean()
        indicators['ema_50'] = data['close'].ewm(span=50, adjust=False).mean()
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2.0 if regime.volatility != 'high' else 2.5
        sma = data['close'].rolling(window=bb_period).mean()
        std = data['close'].rolling(window=bb_period).std()
        indicators['bb_upper'] = sma + (std * bb_std)
        indicators['bb_lower'] = sma - (std * bb_std)
        indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / sma
        
        # ATR for risk management
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        indicators['atr'] = pd.Series(true_range).rolling(14).mean()
        
        # MACD
        indicators['macd'] = indicators['ema_12'] - indicators['ema_26']
        indicators['macd_signal'] = indicators['macd'].ewm(span=9, adjust=False).mean()
        indicators['macd_hist'] = indicators['macd'] - indicators['macd_signal']

        # Cross indicators
        indicators['ema_cross'] = indicators['ema_12'] > indicators['ema_26']
        
        # OBV for Feature Engine
        indicators['obv'] = (np.sign(data['close'].diff()) * data['volume']).fillna(0).cumsum()

        # ADX for Risk Management
        indicators['adx'] = self._calculate_adx(data)

        return indicators

    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculates Average Directional Index (ADX)"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = abs(minus_dm)
        
        tr1 = pd.Series(high - low)
        tr2 = pd.Series(abs(high - close.shift(1)))
        tr3 = pd.Series(abs(low - close.shift(1)))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10))
        adx = dx.rolling(window=period).mean()
        
        return adx

    def calculate_adaptive_rsi(self, data: pd.DataFrame, regime: MarketRegime) -> Tuple[pd.Series, int, int]:
        rsi = self._calculate_rsi(data['close'])
        
        # Adaptive Levels based on Regime
        if regime.trend == 'bullish':
            oversold = 40
            overbought = 80
        elif regime.trend == 'bearish':
            oversold = 20
            overbought = 60
        else:
            oversold = 30
            overbought = 70
            
        return rsi, oversold, overbought

    def _calculate_atr_direct(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return pd.Series(true_range).rolling(period).mean()

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
