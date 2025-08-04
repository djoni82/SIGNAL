#!/usr/bin/env python3
"""
Интеграционные тесты для CryptoAlphaPro Signal Bot
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'crypto_signal_bot'))

from full_featured_bot import FullFeaturedSignalGenerator, NewsAnalyzer, OnChainAnalyzer, TwitterAnalyzer

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.fixture
    async def signal_generator(self):
        """Фикстура для создания генератора сигналов"""
        generator = FullFeaturedSignalGenerator()
        await generator.initialize()
        yield generator
        await generator.shutdown()
    
    @pytest.mark.asyncio
    async def test_full_signal_generation_workflow(self, signal_generator):
        """Тест полного процесса генерации сигнала"""
        
        # Мокаем все внешние API
        with patch.object(signal_generator.data_collector, 'get_symbol_data', return_value={
            'price': 50000.0,
            'change_24h': 2.5,
            'volume': 1000000.0,
            'price_volatility': 0.01,
            'exchanges_count': 3
        }), \
        patch.object(signal_generator.news_analyzer, 'get_news_sentiment', return_value={
            'sentiment_percentage': 65,
            'positive_news': 3,
            'negative_news': 1,
            'neutral_news': 1
        }), \
        patch.object(signal_generator.onchain_analyzer, 'get_onchain_data', return_value={
            'onchain_sentiment': 0.7,
            'active_addresses': 1000000
        }), \
        patch.object(signal_generator.twitter_analyzer, 'get_twitter_sentiment', return_value={
            'sentiment_percentage': 70,
            'tweet_count': 1000
        }), \
        patch.object(signal_generator.telegram_controller, 'send_message', return_value=True):
            
            # Генерируем сигнал
            signal = await signal_generator.generate_signal_for_symbol('BTC/USDT')
            
            # Проверяем результат
            assert signal is not None
            assert signal['symbol'] == 'BTC/USDT'
            assert signal['signal'] in ['STRONG_BUY', 'BUY', 'SELL', 'STRONG_SELL']
            assert 1.0 <= signal['leverage'] <= 50.0
            assert signal['confidence'] > 0
            assert 'news_sentiment' in signal
            assert 'onchain_sentiment' in signal
            assert 'twitter_sentiment' in signal
    
    @pytest.mark.asyncio
    async def test_multiple_signals_generation(self, signal_generator):
        """Тест генерации множественных сигналов"""
        
        # Мокаем данные для нескольких пар
        mock_data = {
            'BTC/USDT': {
                'price': 50000.0,
                'change_24h': 2.5,
                'volume': 1000000.0,
                'price_volatility': 0.01,
                'exchanges_count': 3
            },
            'ETH/USDT': {
                'price': 3000.0,
                'change_24h': 1.5,
                'volume': 500000.0,
                'price_volatility': 0.02,
                'exchanges_count': 2
            }
        }
        
        with patch.object(signal_generator.data_collector, 'get_symbol_data', 
                         side_effect=lambda symbol: mock_data.get(symbol)), \
        patch.object(signal_generator.news_analyzer, 'get_news_sentiment', return_value={
            'sentiment_percentage': 60
        }), \
        patch.object(signal_generator.onchain_analyzer, 'get_onchain_data', return_value={
            'onchain_sentiment': 0.6
        }), \
        patch.object(signal_generator.twitter_analyzer, 'get_twitter_sentiment', return_value={
            'sentiment_percentage': 65
        }), \
        patch.object(signal_generator.telegram_controller, 'send_message', return_value=True):
            
            pairs = ['BTC/USDT', 'ETH/USDT']
            signals = await signal_generator.generate_signals_for_pairs(pairs)
            
            assert len(signals) > 0
            assert signal_generator.stats['pairs_processed'] == 2
            assert signal_generator.stats['signals_generated'] > 0
    
    @pytest.mark.asyncio
    async def test_ai_analysis_with_all_factors(self, signal_generator):
        """Тест AI анализа со всеми факторами"""
        
        # Тестовые данные
        market_data = {
            'price': 50000.0,
            'change_24h': 3.0,
            'volume': 1000000.0,
            'price_volatility': 0.01,
            'exchanges_count': 3
        }
        
        news_data = {
            'sentiment_percentage': 75,
            'positive_news': 4,
            'negative_news': 1
        }
        
        onchain_data = {
            'onchain_sentiment': 0.8,
            'active_addresses': 1200000
        }
        
        twitter_data = {
            'sentiment_percentage': 80,
            'tweet_count': 1500
        }
        
        # Выполняем анализ
        analysis = signal_generator.analyze_market_data(
            market_data, news_data, onchain_data, twitter_data
        )
        
        # Проверяем результат
        assert analysis is not None
        assert 'signal' in analysis
        assert 'confidence' in analysis
        assert 'trend_strength' in analysis
        assert 'volatility' in analysis
        assert 'exchanges_count' in analysis
        assert 'news_sentiment' in analysis
        assert 'onchain_sentiment' in analysis
        assert 'twitter_sentiment' in analysis
        
        # Проверяем логику
        assert 0.1 <= analysis['confidence'] <= 0.95
        assert analysis['signal'] in ['STRONG_BUY', 'BUY', 'NEUTRAL', 'SELL', 'STRONG_SELL']
    
    def test_risk_calculation_with_leverage(self, signal_generator):
        """Тест расчета рисков с плечом"""
        
        # Тестовые данные
        price = 50000.0
        signal = 'STRONG_BUY'
        confidence = 0.8
        
        news_data = {'sentiment_percentage': 75}
        onchain_data = {'onchain_sentiment': 0.8}
        twitter_data = {'sentiment_percentage': 80}
        
        # Рассчитываем риски
        risk_params = signal_generator.calculate_risk_params(
            price, signal, confidence, news_data, onchain_data, twitter_data
        )
        
        # Проверяем результат
        assert risk_params is not None
        assert 'stop_loss' in risk_params
        assert 'take_profit' in risk_params
        assert 'leverage' in risk_params
        assert 'sl_percent' in risk_params
        assert 'tp_percent' in risk_params
        
        # Проверяем логику плеча
        assert 1.0 <= risk_params['leverage'] <= 50.0
        
        # Проверяем SL/TP для LONG позиции
        assert risk_params['stop_loss'] < price
        assert risk_params['take_profit'] > price
    
    def test_risk_calculation_short_position(self, signal_generator):
        """Тест расчета рисков для SHORT позиции"""
        
        # Тестовые данные для SHORT
        price = 50000.0
        signal = 'STRONG_SELL'
        confidence = 0.8
        
        news_data = {'sentiment_percentage': 25}
        onchain_data = {'onchain_sentiment': 0.2}
        twitter_data = {'sentiment_percentage': 20}
        
        # Рассчитываем риски
        risk_params = signal_generator.calculate_risk_params(
            price, signal, confidence, news_data, onchain_data, twitter_data
        )
        
        # Проверяем SL/TP для SHORT позиции
        assert risk_params['stop_loss'] > price
        assert risk_params['take_profit'] < price
    
    def test_price_formatting(self, signal_generator):
        """Тест форматирования цен"""
        
        # Тест разных цен
        assert signal_generator.format_price(50000.0) == "$50,000.00"
        assert signal_generator.format_price(0.12345678) == "$0.12345678"
        assert signal_generator.format_price(0.001) == "$0.00100000"
        assert signal_generator.format_price(None) == "N/A"
        assert signal_generator.format_price(0) == "$0.00"
    
    def test_signal_classification(self, signal_generator):
        """Тест классификации сигналов"""
        
        # Тест STRONG_BUY
        signal = signal_generator._classify_signal(0.8, 3.0)
        assert signal == 'STRONG_BUY'
        
        # Тест BUY
        signal = signal_generator._classify_signal(0.6, 1.0)
        assert signal == 'BUY'
        
        # Тест NEUTRAL
        signal = signal_generator._classify_signal(0.4, 0.3)
        assert signal == 'NEUTRAL'
        
        # Тест SELL
        signal = signal_generator._classify_signal(0.2, -1.0)
        assert signal == 'SELL'
        
        # Тест STRONG_SELL
        signal = signal_generator._classify_signal(0.1, -3.0)
        assert signal == 'STRONG_SELL'
    
    @pytest.mark.asyncio
    async def test_news_analyzer(self):
        """Тест анализатора новостей"""
        analyzer = NewsAnalyzer()
        
        # Мокаем API запрос
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'results': [
                {'vote': 'positive'},
                {'vote': 'positive'},
                {'vote': 'negative'},
                {'vote': 'neutral'}
            ]
        })
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await analyzer.get_news_sentiment('BTC/USDT')
            
            assert result is not None
            assert 'sentiment_percentage' in result
            assert 'positive_news' in result
            assert 'negative_news' in result
            assert 'neutral_news' in result
            assert result['positive_news'] == 2
            assert result['negative_news'] == 1
            assert result['neutral_news'] == 1
    
    @pytest.mark.asyncio
    async def test_onchain_analyzer(self):
        """Тест анализатора on-chain данных"""
        analyzer = OnChainAnalyzer()
        
        result = await analyzer.get_onchain_data('BTC/USDT')
        
        assert result is not None
        assert 'onchain_sentiment' in result
        assert 'active_addresses' in result
        assert 0 <= result['onchain_sentiment'] <= 1
    
    @pytest.mark.asyncio
    async def test_twitter_analyzer(self):
        """Тест анализатора Twitter"""
        analyzer = TwitterAnalyzer()
        
        result = await analyzer.get_twitter_sentiment('BTC/USDT')
        
        assert result is not None
        assert 'sentiment_percentage' in result
        assert 'tweet_count' in result
        assert 0 <= result['sentiment_percentage'] <= 100
    
    def test_telegram_message_formatting(self, signal_generator):
        """Тест форматирования Telegram сообщений"""
        
        # Тестовые данные сигнала
        signal_data = {
            'symbol': 'BTC/USDT',
            'signal': 'STRONG_BUY',
            'price': 50000.0,
            'change_24h': 3.0,
            'confidence': 0.8,
            'stop_loss': 49000.0,
            'take_profit': 53000.0,
            'leverage': 15.0,
            'exchanges_count': 3,
            'news_sentiment': 75,
            'onchain_sentiment': 0.8,
            'twitter_sentiment': 80
        }
        
        # Форматируем сообщение
        message = signal_generator.format_signal_message(signal_data)
        
        # Проверяем содержимое
        assert 'STRONG_BUY BTC/USDT' in message
        assert '$50,000.00' in message
        assert '3.00%' in message
        assert '80%' in message
        assert '15.0x' in message
        assert '3' in message  # exchanges_count
        assert '$49,000.00' in message  # stop_loss
        assert '$53,000.00' in message  # take_profit
        assert 'CryptoAlphaPro Full Featured v3.0' in message

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 