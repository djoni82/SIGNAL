# src/strategies/feature_engine.py
import pandas as pd
import numpy as np
import talib
from scipy import stats
from typing import Dict
from src.strategies.models import MarketRegime

class SmartFeatureEngineer:
    def __init__(self, max_features: int = 50):
        self.max_features = max_features
        # feature_importance logic can be added here

    def create_features(self, data: pd.DataFrame, regime: MarketRegime, indicators: Dict) -> Dict:
        features = {}
        features.update(self._create_price_features(data, indicators))
        features.update(self._create_volume_features(data, indicators))
        features.update(self._create_structure_features(data))
        features.update(self._create_statistical_features(data))
        features.update(self._create_context_features(data, regime))
        features.update(self._create_pattern_features(data))
        return features
    
    def _create_price_features(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        features = {}
        current_price = data['close'].iloc[-1]

        # Price position in BB
        if 'bb_upper' in indicators and 'bb_lower' in indicators:
            bb_upper = indicators['bb_upper'].iloc[-1]
            bb_lower = indicators['bb_lower'].iloc[-1]
            if bb_upper != bb_lower:
                features['bb_position'] = (current_price - bb_lower) / (bb_upper - bb_lower)
                features['bb_squeeze'] = indicators.get('bb_width', pd.Series([0])).iloc[-1] < 0.1
        
        # RSI divergence (Original logic)
        rsi = indicators.get('rsi', pd.Series(50, index=data.index))
        price_change = data['close'].pct_change(5).iloc[-1]
        rsi_change = rsi.diff(5).iloc[-1]
        
        if not pd.isna(price_change) and not pd.isna(rsi_change):
            features['rsi_divergence'] = 1 if (price_change > 0 and rsi_change < 0) or \
                                            (price_change < 0 and rsi_change > 0) else 0
        
        # Candlestick body ratio
        body = abs(data['close'].iloc[-1] - data['open'].iloc[-1])
        wick = data['high'].iloc[-1] - data['low'].iloc[-1]
        features['candle_body_ratio'] = body / (wick + 1e-10)
        
        return features
    
    def _create_volume_features(self, data: pd.DataFrame, indicators: Dict) -> Dict:
        features = {}
        
        # Volume spikes
        volume_ma = data['volume'].rolling(20).mean()
        current_volume = data['volume'].iloc[-1]
        features['volume_ratio'] = current_volume / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1
        
        # Volume-price correlation
        corr_window = min(20, len(data))
        volume_corr = data['close'].tail(corr_window).corr(data['volume'].tail(corr_window))
        features['volume_price_corr'] = volume_corr if not pd.isna(volume_corr) else 0
        
        # OBV momentum (Original logic)
        if 'obv' in indicators:
            obv = indicators['obv']
            # Anti-division by zero
            obv_past = obv.iloc[-5] if len(obv) > 5 else obv.iloc[-1]
            denominator = abs(obv_past) + 1e-10
            features['obv_momentum'] = (obv.iloc[-1] - obv_past) / denominator
            
        return features
    
    def _create_structure_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        pivot_high = data['high'].rolling(10).max().iloc[-1]
        pivot_low = data['low'].rolling(10).min().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        features['dist_to_resistance'] = (pivot_high - current_price) / current_price
        features['dist_to_support'] = (current_price - pivot_low) / current_price
        
        # Higher highs / Lower lows
        highs_5 = data['high'].rolling(5).max()
        lows_5 = data['low'].rolling(5).min()
        
        features['higher_high'] = 1 if len(highs_5) >= 2 and highs_5.iloc[-1] > highs_5.iloc[-2] else 0
        features['lower_low'] = 1 if len(lows_5) >= 2 and lows_5.iloc[-1] < lows_5.iloc[-2] else 0
        
        return features
    
    def _create_statistical_features(self, data: pd.DataFrame) -> Dict:
        returns = data['close'].pct_change().dropna()
        if len(returns) < 10: return {}
        
        features = {
            'returns_skew': float(returns.skew()),
            'returns_kurtosis': float(returns.kurtosis()),
            'volatility_20d': float(returns.std() * np.sqrt(365)),
            'sharpe_20d': float(returns.mean() / returns.std() * np.sqrt(365)) if returns.std() > 0 else 0,
            'var_95': float(np.percentile(returns, 5))
        }
        return features
    
    def _create_context_features(self, data: pd.DataFrame, regime: MarketRegime) -> Dict:
        features = {}
        if not data.empty:
            last_time = data.index[-1]
            features['hour_sin'] = np.sin(2 * np.pi * last_time.hour / 24)
            features['hour_cos'] = np.cos(2 * np.pi * last_time.hour / 24)
            features['day_of_week'] = last_time.dayofweek / 6
            features['is_weekend'] = 1 if last_time.dayofweek >= 5 else 0
            
            features['asian_session'] = 1 if 0 <= last_time.hour < 8 else 0
            features['us_session'] = 1 if 13 <= last_time.hour < 21 else 0
            features['euro_session'] = 1 if 7 <= last_time.hour < 16 else 0
        
        regime_mapping = {'bullish': 1, 'bearish': -1, 'neutral': 0,
                          'accumulation': 1, 'distribution': -1, 'markup': 2, 'markdown': -2}
        
        features['regime_trend'] = regime_mapping.get(regime.trend, 0)
        features['regime_phase'] = regime_mapping.get(regime.phase, 0)
        features['regime_strength'] = regime.strength / 100
        features['crisis_mode'] = 1 if regime.crisis_mode else 0
        
        return features
    
    def _create_pattern_features(self, data: pd.DataFrame) -> Dict:
        features = {}
        # Using talib for pattern recognition
        try:
            open_ = data['open'].values
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            
            features['pattern_doji'] = 1 if talib.CDLDOJI(open_, high, low, close)[-1] != 0 else 0
            features['pattern_hammer'] = 1 if talib.CDLHAMMER(open_, high, low, close)[-1] != 0 else 0
            features['pattern_engulfing'] = 1 if talib.CDLENGULFING(open_, high, low, close)[-1] != 0 else 0
            features['pattern_morning_star'] = 1 if talib.CDLMORNINGSTAR(open_, high, low, close)[-1] != 0 else 0
            features['pattern_evening_star'] = 1 if talib.CDLEVENINGSTAR(open_, high, low, close)[-1] != 0 else 0
        except Exception as e:
            # Fallback if talib fails or data too short
            features['pattern_error'] = 1
            
        return features
