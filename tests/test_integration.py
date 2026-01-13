# tests/test_integration.py
"""
Integration tests for full signal generation pipeline
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_full_signal_pipeline(sample_ohlcv_data):
    """Test complete signal generation from data to signal"""
    from src.strategies.signal_generator_ultra import UltraSignalGenerator
    
    # Mock exchange
    mock_exchange = Mock()
    mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])
    
    generator = UltraSignalGenerator(mock_exchange)
    
    # Prepare multi-timeframe data
    multi_tf_data = {
        '1h': sample_ohlcv_data,
        '4h': sample_ohlcv_data,
        '15m': sample_ohlcv_data
    }
    
    # Generate signal
    signal = await generator.analyze_symbol(
        symbol='BTC/USDT',
        multi_tf_data=multi_tf_data,
        target_timeframe='1h'
    )
    
    # Signal might be None if confidence is low (which is expected without trained models)
    # But the function should not crash
    assert signal is None or hasattr(signal, 'confidence')

@pytest.mark.asyncio
async def test_ml_prediction_integration(sample_features):
    """Test ML prediction in pipeline context"""
    from src.strategies.ml_engine_real import RealMLEngine
    
    engine = RealMLEngine()
    prob = engine.predict_probability(sample_features)
    
    # Should return neutral 0.5 without training
    assert prob == 0.5

@pytest.mark.asyncio  
async def test_smart_money_integration():
    """Test Smart Money integration with signal generator"""
    from src.strategies.smart_money_analyzer import SmartMoneyAnalyzer
    
    analyzer = SmartMoneyAnalyzer()
    
    result = await analyzer.analyze_smart_money_context(
        'BTC/USDT', 50000.0, 'BUY'
    )
    
    assert 'smart_money_boost' in result
    await analyzer.close()
