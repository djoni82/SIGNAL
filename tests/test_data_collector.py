#!/usr/bin/env python3
"""
Тесты для Universal Data Collector
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'crypto_signal_bot'))

from universal_data_collector import UniversalDataCollector

class TestUniversalDataCollector:
    """Тесты для UniversalDataCollector"""
    
    @pytest.fixture
    async def collector(self):
        """Фикстура для создания коллектора"""
        collector = UniversalDataCollector()
        await collector.__aenter__()
        yield collector
        await collector.__aexit__(None, None, None)
    
    def test_format_symbol(self):
        """Тест форматирования символов"""
        collector = UniversalDataCollector()
        
        # Тест для OKX
        assert collector.format_symbol('BTC/USDT', 'okx') == 'BTC-USDT'
        
        # Тест для других бирж
        assert collector.format_symbol('BTC/USDT', 'binance') == 'BTCUSDT'
        assert collector.format_symbol('ETH/USDT', 'bybit') == 'ETHUSDT'
    
    @pytest.mark.asyncio
    async def test_get_binance_data_success(self, collector):
        """Тест успешного получения данных с Binance"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'lastPrice': '50000.00',
            'priceChangePercent': '2.5',
            'volume': '1000000',
            'highPrice': '51000.00',
            'lowPrice': '49000.00',
            'bidPrice': '49999.00',
            'askPrice': '50001.00'
        })
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await collector.get_binance_data('BTC/USDT')
            
            assert result is not None
            assert result['price'] == 50000.0
            assert result['change_24h'] == 2.5
            assert result['volume'] == 1000000.0
            assert result['exchange'] == 'binance'
    
    @pytest.mark.asyncio
    async def test_get_binance_data_error(self, collector):
        """Тест обработки ошибки Binance API"""
        mock_response = Mock()
        mock_response.status = 404
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await collector.get_binance_data('BTC/USDT')
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_bybit_data_success(self, collector):
        """Тест успешного получения данных с Bybit"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'result': {
                'list': [{
                    'lastPrice': '50000.00',
                    'price24hPcnt': '0.025',
                    'volume24h': '1000000',
                    'highPrice24h': '51000.00',
                    'lowPrice24h': '49000.00',
                    'bid1Price': '49999.00',
                    'ask1Price': '50001.00'
                }]
            }
        })
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await collector.get_bybit_data('BTC/USDT')
            
            assert result is not None
            assert result['price'] == 50000.0
            assert result['change_24h'] == 2.5
            assert result['volume'] == 1000000.0
            assert result['exchange'] == 'bybit'
    
    @pytest.mark.asyncio
    async def test_get_okx_data_success(self, collector):
        """Тест успешного получения данных с OKX"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'data': [{
                'last': '50000.00',
                'change24h': '0.025',
                'vol24h': '1000000',
                'high24h': '51000.00',
                'low24h': '49000.00',
                'bidPx': '49999.00',
                'askPx': '50001.00'
            }]
        })
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await collector.get_okx_data('BTC/USDT')
            
            assert result is not None
            assert result['price'] == 50000.0
            assert result['change_24h'] == 2.5
            assert result['volume'] == 1000000.0
            assert result['exchange'] == 'okx'
    
    def test_validate_data_valid(self):
        """Тест валидации корректных данных"""
        collector = UniversalDataCollector()
        
        valid_data = {
            'price': 50000.0,
            'change_24h': 2.5,
            'volume': 1000000.0
        }
        
        assert collector.validate_data(valid_data, 'BTC/USDT') is True
    
    def test_validate_data_invalid_price(self):
        """Тест валидации некорректной цены"""
        collector = UniversalDataCollector()
        
        invalid_data = {
            'price': 1000000.0,  # Слишком высокая цена для BTC
            'change_24h': 2.5,
            'volume': 1000000.0
        }
        
        assert collector.validate_data(invalid_data, 'BTC/USDT') is False
    
    def test_validate_data_invalid_change(self):
        """Тест валидации некорректного изменения цены"""
        collector = UniversalDataCollector()
        
        invalid_data = {
            'price': 50000.0,
            'change_24h': 150.0,  # Слишком большое изменение
            'volume': 1000000.0
        }
        
        assert collector.validate_data(invalid_data, 'BTC/USDT') is False
    
    def test_calculate_aggregated_data(self):
        """Тест расчета агрегированных данных"""
        collector = UniversalDataCollector()
        
        exchange_data = {
            'binance': {
                'price': 50000.0,
                'change_24h': 2.5,
                'volume': 1000000.0
            },
            'bybit': {
                'price': 50010.0,
                'change_24h': 2.6,
                'volume': 1001000.0
            }
        }
        
        result = collector.calculate_aggregated_data(exchange_data)
        
        assert result is not None
        assert 'price' in result
        assert 'change_24h' in result
        assert 'volume' in result
        assert result['exchanges_count'] == 2
    
    @pytest.mark.asyncio
    async def test_get_symbol_data_success(self, collector):
        """Тест получения данных по символу"""
        # Мокаем все методы получения данных
        with patch.object(collector, 'get_binance_data', return_value={
            'price': 50000.0, 'change_24h': 2.5, 'volume': 1000000.0
        }), \
        patch.object(collector, 'get_bybit_data', return_value={
            'price': 50010.0, 'change_24h': 2.6, 'volume': 1001000.0
        }), \
        patch.object(collector, 'get_okx_data', return_value=None):
            
            result = await collector.get_symbol_data('BTC/USDT')
            
            assert result is not None
            assert result['symbol'] == 'BTC/USDT'
            assert result['exchanges_count'] == 2
    
    @pytest.mark.asyncio
    async def test_get_multiple_symbols_data(self, collector):
        """Тест получения данных по нескольким символам"""
        with patch.object(collector, 'get_symbol_data', return_value={
            'symbol': 'BTC/USDT',
            'price': 50000.0,
            'exchanges_count': 2
        }):
            
            symbols = ['BTC/USDT', 'ETH/USDT']
            result = await collector.get_multiple_symbols_data(symbols)
            
            assert len(result) == 2
            assert 'BTC/USDT' in result
            assert 'ETH/USDT' in result
    
    def test_get_available_pairs(self):
        """Тест получения списка доступных пар"""
        collector = UniversalDataCollector()
        pairs = collector.get_available_pairs()
        
        assert isinstance(pairs, list)
        assert len(pairs) > 0
        assert 'BTC/USDT' in pairs
        assert 'ETH/USDT' in pairs
    
    def test_add_custom_pair(self):
        """Тест добавления кастомной пары"""
        collector = UniversalDataCollector()
        
        # Успешное добавление
        assert collector.add_custom_pair('NEWCOIN/USDT') is True
        
        # Неуспешное добавление (неверный формат)
        assert collector.add_custom_pair('INVALID') is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 