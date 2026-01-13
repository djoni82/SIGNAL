# tests/conftest.py
"""
Pytest configuration and fixtures
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@pytest.fixture
def sample_ohlcv_data():
    """Генерирует sample OHLCV данные для тестов"""
    dates = pd.date_range(end=datetime.now(), periods=200, freq='1H')
    np.random.seed(42)
    
    close_prices = 50000 + np.cumsum(np.random.randn(200) * 100)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.randn(200) * 50,
        'high': close_prices + abs(np.random.randn(200) * 100),
        'low': close_prices - abs(np.random.randn(200) * 100),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 200)
    })
    
    return df.set_index('timestamp')

@pytest.fixture
def sample_features():
    """Sample ML features"""
    return {
        'hurst_exponent': 0.6,
        'dfa_alpha': 1.2,
        'returns_skew': 0.15,
        'returns_kurtosis': 3.5,
        'volatility_regime': 0.5,
        'price_entropy': 0.7,
        'sma_20': 50000,
        'sma_50': 49500,
        'rsi': 55.0,
        'atr': 500.0,
        'volume_ratio': 1.3
    }
