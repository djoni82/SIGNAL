# src/strategies/advanced_features.py
"""
Advanced Feature Engineering - продвинутые математические фичи.
Включает: Hurst Exponent, DFA, Fractals, Statistical Moments.
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Инженер сложных фич для ML моделей.
    Эти фичи дают преимущество над базовыми TA индикаторами.
    """
    
    def create_advanced_features(self, data: pd.DataFrame) -> Dict:
        """
        Генерирует продвинутые фичи из OHLCV данных.
        """
        features = {}
        
        if len(data) < 100:
            logger.warning("Not enough data for advanced features")
            return features
        
        close = data['close'].values
        returns = pd.Series(close).pct_change().dropna().values
        
        # === 1. FRACTAL DIMENSION (HURST EXPONENT) ===
        # Показывает персистентность тренда
        # 0-0.5: Mean Reverting, 0.5: Random Walk, 0.5-1: Trending
        features['hurst_exponent'] = self._calculate_hurst(returns)
        
        # === 2. DFA (DETRENDED FLUCTUATION ANALYSIS) ===
        # Измеряет long-range correlations
        features['dfa_alpha'] = self._calculate_dfa(close)
        
        # === 3. STATISTICAL MOMENTS ===
        # Skewness: асимметрия распределения
        # Kurtosis: "толщина хвостов" (риск экстремальных движений)
        features['returns_skew'] = float(stats.skew(returns))
        features['returns_kurtosis'] = float(stats.kurtosis(returns))
        
        # === 4. VOLATILITY REGIME DETECTION ===
        features['volatility_regime'] = self._detect_volatility_regime(returns)
        features['volatility_percentile'] = self._volatility_percentile(returns)
        
        # === 5. MOMENTUM PERSISTENCE ===
        # Как долго текущий тренд сохраняется
        features['momentum_persistence'] = self._momentum_persistence(close)
        
        # === 6. ENTROPY (СЛОЖНОСТЬ ЦЕНОВОГО РЯДА) ===
        features['price_entropy'] = self._calculate_entropy(returns)
        
        return features

    def _calculate_hurst(self, series, lags_range=(2, 100)):
        """
        Hurst Exponent через R/S analysis.
        """
        try:
            if len(series) < lags_range[1]:
                return 0.5
            
            lags = range(lags_range[0], min(lags_range[1], len(series) // 2))
            tau = []
            
            for lag in lags:
                # Standard deviation of differences
                std_dev = np.std(series[lag:] - series[:-lag])
                if std_dev > 0:
                    tau.append(std_dev)
                else:
                    tau.append(1e-10)
            
            if not tau or len(tau) < 2:
                return 0.5
                
            # Log-log regression
            poly = np.polyfit(np.log(list(lags)[:len(tau)]), np.log(tau), 1)
            hurst = float(poly[0] * 2.0)
            
            # Clamp between 0 and 1
            return np.clip(hurst, 0.0, 1.0)
            
        except Exception as e:
            logger.debug(f"Hurst calculation error: {e}")
            return 0.5

    def _calculate_dfa(self, series, window_sizes=None):
        """
        Detrended Fluctuation Analysis (упрощенная версия).
        """
        try:
            n = len(series)
            if n < 100:
                return 1.0
            
            # Profile (cumulative sum of deviations from mean)
            y = np.cumsum(series - np.mean(series))
            
            # Window sizes (scales)
            if window_sizes is None:
                window_sizes = np.logspace(np.log10(10), np.log10(n // 4), 15).astype(int)
            
            fluct = []
            for scale in window_sizes:
                if scale >= len(y):
                    continue
                    
                # Local trend
                reshaped = y[:len(y) - len(y) % scale].reshape(-1, scale)
                local_trend = np.mean(reshaped, axis=1)
                
                # Fluctuation
                rms = np.sqrt(np.mean((reshaped - local_trend[:, None]) ** 2))
                fluct.append(rms)
            
            if len(fluct) < 2:
                return 1.0
            
            # Power law: F(n) ~ n^alpha
            valid_scales = window_sizes[:len(fluct)]
            coeff = np.polyfit(np.log(valid_scales), np.log(fluct), 1)
            return float(np.clip(coeff[0], 0.0, 2.0))
            
        except Exception as e:
            logger.debug(f"DFA calculation error: {e}")
            return 1.0

    def _detect_volatility_regime(self, returns, window=20):
        """
        Классификация режима волатильности.
        """
        try:
            if len(returns) < window * 5:
                return 0.5  # NORMAL
            
            vol_short = np.std(returns[-window:])
            vol_long = np.std(returns[-window * 5:])
            
            ratio = vol_short / vol_long if vol_long > 0 else 1.0
            
            if ratio > 1.5:
                return 1.0  # SPIKE (high volatility)
            elif ratio < 0.5:
                return 0.0  # LOW (compressed volatility)
            else:
                return 0.5  # NORMAL
                
        except:
            return 0.5

    def _volatility_percentile(self, returns, window=100):
        """
        Текущая волатильность относительно исторической (percentile).
        """
        try:
            if len(returns) < window:
                return 0.5
            
            current_vol = np.std(returns[-20:])
            hist_vols = [np.std(returns[i:i + 20]) for i in range(len(returns) - 20)]
            
            if not hist_vols:
                return 0.5
            
            percentile = np.sum(np.array(hist_vols) < current_vol) / len(hist_vols)
            return float(percentile)
            
        except:
            return 0.5

    def _momentum_persistence(self, prices, window=20):
        """
        Как долго цена движется в одном направлении.
        """
        try:
            if len(prices) < window:
                return 0.0
            
            recent_returns = np.diff(prices[-window:])
            same_direction = (recent_returns > 0).sum() / len(recent_returns)
            
            # 1.0 = все движения в одну сторону, 0.5 = случайность
            return float(abs(same_direction - 0.5) * 2)
            
        except:
            return 0.0

    def _calculate_entropy(self, returns, bins=20):
        """
        Shannon Entropy - мера непредсказуемости.
        Высокая энтропия = хаос, низкая = структура.
        """
        try:
            if len(returns) < 50:
                return 0.5
            
            hist, _ = np.histogram(returns, bins=bins)
            hist = hist / np.sum(hist)  # Normalize to probability
            
            # Remove zeros
            hist = hist[hist > 0]
            
            entropy = -np.sum(hist * np.log2(hist))
            
            # Normalize to 0-1 (max entropy for uniform distribution = log2(bins))
            max_entropy = np.log2(bins)
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.5
            
            return float(normalized_entropy)
            
        except:
            return 0.5
