# tests/test_smart_money.py
"""
Tests for Smart Money Analyzer
"""
import pytest
from src.strategies.smart_money_analyzer import SmartMoneyAnalyzer

class TestSmartMoneyAnalyzer:
    """Tests for Smart Money analysis"""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test analyzer initializes"""
        analyzer = SmartMoneyAnalyzer()
        assert analyzer is not None
    
    @pytest.mark.asyncio
    async def test_get_liquidity_data(self):
        """Test liquidity data retrieval"""
        analyzer = SmartMoneyAnalyzer()
        liq_data = await analyzer.get_liquidity_data('BTC/USDT')
        
        assert 'short_liq_price' in liq_data
        assert 'long_liq_price' in liq_data
        assert 'liquidity_gap' in liq_data
    
    @pytest.mark.asyncio
    async def test_get_funding_metrics(self):
        """Test funding rate retrieval"""
        analyzer = SmartMoneyAnalyzer()
        funding = await analyzer.get_funding_metrics('BTC/USDT')
        
        assert 'current_funding' in funding
        assert 'funding_trend' in funding
    
    @pytest.mark.asyncio
    async def test_analyze_context_buy(self):
        """Test Smart Money context for BUY"""
        analyzer = SmartMoneyAnalyzer()
        
        result = await analyzer.analyze_smart_money_context(
            symbol='BTC/USDT',
            current_price=64000.0,
            direction='BUY'
        )
        
        assert 'smart_money_boost' in result
        assert 'rationale' in result
        assert 'metrics' in result
        
        # Boost should be capped
        assert -0.10 <= result['smart_money_boost'] <= 0.30
    
    @pytest.mark.asyncio
    async def test_analyze_context_sell(self):
        """Test Smart Money context for SELL"""
        analyzer = SmartMoneyAnalyzer()
        
        result = await analyzer.analyze_smart_money_context(
            symbol='ETH/USDT',
            current_price=3500.0,
            direction='SELL'
        )
        
        assert isinstance(result['smart_money_boost'], float)
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test session cleanup"""
        analyzer = SmartMoneyAnalyzer()
        await analyzer._ensure_session()
        await analyzer.close()
        
        if analyzer.session:
            assert analyzer.session.closed
