# tests/test_advanced_features.py
"""
Tests for Advanced Feature Engineering
"""
import pytest
import numpy as np
from src.strategies.advanced_features import AdvancedFeatureEngineer

class TestAdvancedFeatures:
    """Tests for advanced feature calculation"""
    
    def test_create_features(self, sample_ohlcv_data):
        """Test feature generation from OHLCV data"""
        engineer = AdvancedFeatureEngineer()
        features = engineer.create_advanced_features(sample_ohlcv_data)
        
        assert 'hurst_exponent' in features
        assert 'dfa_alpha' in features
        assert 'returns_skew' in features
        assert 'returns_kurtosis' in features
        assert 'volatility_regime' in features
    
    def test_hurst_exponent_range(self, sample_ohlcv_data):
        """Hurst should be between 0 and 1"""
        engineer = AdvancedFeatureEngineer()
        returns = sample_ohlcv_data['close'].pct_change().dropna().values
        hurst = engineer._calculate_hurst(returns)
        
        assert 0.0 <= hurst <= 1.0
    
    def test_dfa_calculation(self, sample_ohlcv_data):
        """DFA should return reasonable values"""
        engineer = AdvancedFeatureEngineer()
        close = sample_ohlcv_data['close'].values
        dfa = engineer._calculate_dfa(close)
        
        assert 0.0 <= dfa <= 2.0
    
    def test_volatility_regime_detection(self, sample_ohlcv_data):
        """Volatility regime should classify correctly"""
        engineer = AdvancedFeatureEngineer()
        returns = sample_ohlcv_data['close'].pct_change().dropna().values
        regime = engineer._detect_volatility_regime(returns)
        
        assert regime in [0.0, 0.5, 1.0]  # LOW, NORMAL, SPIKE
    
    def test_entropy_calculation(self, sample_ohlcv_data):
        """Entropy should be normalized"""
        engineer = AdvancedFeatureEngineer()
        returns = sample_ohlcv_data['close'].pct_change().dropna().values
        entropy = engineer._calculate_entropy(returns)
        
        assert 0.0 <= entropy <= 1.0
    
    def test_insufficient_data(self):
        """Should handle insufficient data gracefully"""
        engineer = AdvancedFeatureEngineer()
        import pandas as pd
        
        # Only 10 rows
        small_df = pd.DataFrame({
            'close': np.random.randn(10) + 100,
            'high': np.random.randn(10) + 101,
            'low': np.random.randn(10) + 99,
            'volume': np.random.randint(1000, 2000, 10)
        })
        
        features = engineer.create_advanced_features(small_df)
        assert isinstance(features, dict)
