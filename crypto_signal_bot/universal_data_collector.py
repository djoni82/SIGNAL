#!/usr/bin/env python3
"""
Universal Data Collector for CryptoAlphaPro
Поддержка Binance, Bybit, OKX + любые пары
"""

import requests
import asyncio
import aiohttp
import pandas as pd
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("universal_data_collector")

class UniversalDataCollector:
    """Универсальный сборщик данных с поддержкой всех бирж"""
    
    def __init__(self):
        self.session = None
        self.exchanges = {
            'binance': {
                'base_url': 'https://api.binance.com/api/v3',
                'ticker_url': '/ticker/24hr',
                'klines_url': '/klines'
            },
            'bybit': {
                'base_url': 'https://api.bybit.com/v5/market',
                'ticker_url': '/tickers',
                'klines_url': '/kline'
            },
            'okx': {
                'base_url': 'https://www.okx.com/api/v5/market',
                'ticker_url': '/tickers',
                'klines_url': '/candles'
            }
        }
        
        # Кэш для данных
        self.data_cache = {}
        self.cache_timeout = 30  # секунды
        
    async def __aenter__(self):
        """Асинхронный вход"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный выход"""
        if self.session:
            await self.session.close()
    
    def format_symbol(self, symbol: str, exchange: str) -> str:
        """Форматирование символа для разных бирж"""
        if exchange == 'okx':
            return symbol.replace('/', '-')  # BTC-USDT
        else:
            return symbol.replace('/', '')   # BTCUSDT
    
    async def get_binance_data(self, symbol: str) -> Optional[Dict]:
        """Получение данных с Binance"""
        try:
            formatted_symbol = self.format_symbol(symbol, 'binance')
            url = f"{self.exchanges['binance']['base_url']}{self.exchanges['binance']['ticker_url']}"
            params = {'symbol': formatted_symbol}
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'price': float(data['lastPrice']),
                        'change_24h': float(data['priceChangePercent']),
                        'volume': float(data['volume']),
                        'high_24h': float(data['highPrice']),
                        'low_24h': float(data['lowPrice']),
                        'bid': float(data['bidPrice']),
                        'ask': float(data['askPrice']),
                        'exchange': 'binance'
                    }
                else:
                    logger.warning(f"Binance API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Binance error for {symbol}: {e}")
        return None
    
    async def get_bybit_data(self, symbol: str) -> Optional[Dict]:
        """Получение данных с Bybit"""
        try:
            formatted_symbol = self.format_symbol(symbol, 'bybit')
            url = f"{self.exchanges['bybit']['base_url']}{self.exchanges['bybit']['ticker_url']}"
            params = {'category': 'spot', 'symbol': formatted_symbol}
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('result', {}).get('list'):
                        ticker = data['result']['list'][0]
                        
                        return {
                            'price': float(ticker['lastPrice']),
                            'change_24h': float(ticker['price24hPcnt']) * 100,
                            'volume': float(ticker['volume24h']),
                            'high_24h': float(ticker['highPrice24h']),
                            'low_24h': float(ticker['lowPrice24h']),
                            'bid': float(ticker['bid1Price']),
                            'ask': float(ticker['ask1Price']),
                            'exchange': 'bybit'
                        }
                else:
                    logger.warning(f"Bybit API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Bybit error for {symbol}: {e}")
        return None
    
    async def get_okx_data(self, symbol: str) -> Optional[Dict]:
        """Получение данных с OKX"""
        try:
            formatted_symbol = self.format_symbol(symbol, 'okx')
            url = f"{self.exchanges['okx']['base_url']}{self.exchanges['okx']['ticker_url']}"
            params = {'instType': 'SPOT', 'instId': formatted_symbol}
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('data'):
                        ticker = data['data'][0]
                        
                        return {
                            'price': float(ticker['last']),
                            'change_24h': float(ticker.get('change24h', 0)) * 100,
                            'volume': float(ticker['vol24h']),
                            'high_24h': float(ticker['high24h']),
                            'low_24h': float(ticker['low24h']),
                            'bid': float(ticker['bidPx']),
                            'ask': float(ticker['askPx']),
                            'exchange': 'okx'
                        }
                else:
                    logger.warning(f"OKX API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"OKX error for {symbol}: {e}")
        return None
    
    async def get_all_exchange_data(self, symbol: str) -> Dict[str, Any]:
        """Получение данных со всех бирж"""
        tasks = [
            self.get_binance_data(symbol),
            self.get_bybit_data(symbol),
            self.get_okx_data(symbol)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        exchange_data = {}
        for i, result in enumerate(results):
            if isinstance(result, dict):
                exchange_name = ['binance', 'bybit', 'okx'][i]
                exchange_data[exchange_name] = result
        
        return exchange_data
    
    def validate_data(self, data: Dict, symbol: str) -> bool:
        """Валидация данных"""
        if not data:
            return False
        
        # Проверка цен
        price_limits = {
            'BTC/USDT': {'min': 10000, 'max': 200000},
            'ETH/USDT': {'min': 1000, 'max': 10000},
            'SOL/USDT': {'min': 10, 'max': 500},
            'ADA/USDT': {'min': 0.1, 'max': 10},
            'XRP/USDT': {'min': 0.1, 'max': 10},
            'BNB/USDT': {'min': 100, 'max': 1000},
            'DOT/USDT': {'min': 1, 'max': 100},
            'AVAX/USDT': {'min': 10, 'max': 500},
            'LINK/USDT': {'min': 1, 'max': 100},
            'MATIC/USDT': {'min': 0.1, 'max': 10},
            'UNI/USDT': {'min': 1, 'max': 100},
            'LTC/USDT': {'min': 50, 'max': 1000}
        }
        
        # Универсальная проверка для новых пар
        if symbol not in price_limits:
            # Для новых пар используем более широкие лимиты
            price = data.get('price', 0)
            if price <= 0 or price > 1000000:  # Максимум $1M
                return False
        else:
            limits = price_limits[symbol]
            price = data.get('price', 0)
            if not (limits['min'] <= price <= limits['max']):
                return False
        
        # Проверка изменения цены
        change = data.get('change_24h', 0)
        if not (-50 <= change <= 100):  # От -50% до +100%
            return False
        
        return True
    
    def calculate_aggregated_data(self, exchange_data: Dict) -> Dict:
        """Расчет агрегированных данных"""
        if not exchange_data:
            return {}
        
        prices = [data['price'] for data in exchange_data.values()]
        changes = [data['change_24h'] for data in exchange_data.values()]
        volumes = [data['volume'] for data in exchange_data.values()]
        
        # Медианные значения (более устойчивы к выбросам)
        import statistics
        avg_price = statistics.median(prices)
        avg_change = statistics.median(changes)
        avg_volume = statistics.median(volumes)
        
        # Волатильность между биржами
        price_volatility = statistics.stdev(prices) / avg_price if len(prices) > 1 else 0
        
        return {
            'price': avg_price,
            'change_24h': avg_change,
            'volume': avg_volume,
            'price_volatility': price_volatility,
            'exchanges_count': len(exchange_data),
            'exchange_data': exchange_data
        }
    
    async def get_symbol_data(self, symbol: str, use_cache: bool = True) -> Optional[Dict]:
        """Получение данных по символу со всех бирж"""
        
        # Проверка кэша
        if use_cache and symbol in self.data_cache:
            cache_time, cache_data = self.data_cache[symbol]
            if time.time() - cache_time < self.cache_timeout:
                return cache_data
        
        # Получение данных со всех бирж
        exchange_data = await self.get_all_exchange_data(symbol)
        
        if not exchange_data:
            logger.warning(f"No data received for {symbol}")
            return None
        
        # Валидация данных
        valid_data = {}
        for exchange, data in exchange_data.items():
            if self.validate_data(data, symbol):
                valid_data[exchange] = data
            else:
                logger.warning(f"Invalid data from {exchange} for {symbol}")
        
        if not valid_data:
            logger.warning(f"No valid data for {symbol}")
            return None
        
        # Расчет агрегированных данных
        aggregated = self.calculate_aggregated_data(valid_data)
        aggregated['symbol'] = symbol
        aggregated['timestamp'] = datetime.now().isoformat()
        
        # Сохранение в кэш
        if use_cache:
            self.data_cache[symbol] = (time.time(), aggregated)
        
        return aggregated
    
    async def get_multiple_symbols_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Получение данных по нескольким символам"""
        tasks = [self.get_symbol_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data = {}
        for i, result in enumerate(results):
            if isinstance(result, dict):
                data[symbols[i]] = result
            else:
                logger.error(f"Error getting data for {symbols[i]}: {result}")
        
        return data
    
    def get_available_pairs(self) -> List[str]:
        """Получение списка доступных пар (заглушка)"""
        # В реальности можно получить с API бирж
        return [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT', 'SOL/USDT',
            'DOT/USDT', 'AVAX/USDT', 'LINK/USDT', 'MATIC/USDT', 'UNI/USDT', 'LTC/USDT',
            'DOGE/USDT', 'TON/USDT', 'PEPE/USDT', 'FLOKI/USDT', 'SHIB/USDT', 'BONK/USDT'
        ]
    
    def add_custom_pair(self, symbol: str) -> bool:
        """Добавление кастомной пары"""
        try:
            # Проверка формата
            if '/' not in symbol:
                logger.error(f"Invalid symbol format: {symbol}")
                return False
            
            # Добавляем в список доступных пар
            available = self.get_available_pairs()
            if symbol not in available:
                available.append(symbol)
                logger.info(f"Added custom pair: {symbol}")
            
            return True
        except Exception as e:
            logger.error(f"Error adding custom pair {symbol}: {e}")
            return False

# Тестовая функция
async def test_universal_collector():
    """Тест универсального коллектора"""
    print("🚀 Testing Universal Data Collector")
    print("=" * 50)
    
    async with UniversalDataCollector() as collector:
        # Тестовые пары
        test_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'DOGE/USDT']
        
        for symbol in test_pairs:
            print(f"\n🔍 Testing {symbol}...")
            
            data = await collector.get_symbol_data(symbol)
            if data:
                print(f"✅ {symbol}: ${data['price']:.2f} ({data['change_24h']:.2f}%)")
                print(f"   Exchanges: {data['exchanges_count']}")
                print(f"   Volatility: {data['price_volatility']:.4f}")
            else:
                print(f"❌ No data for {symbol}")
        
        # Тест множественных пар
        print(f"\n📊 Testing multiple symbols...")
        all_data = await collector.get_multiple_symbols_data(test_pairs)
        print(f"✅ Got data for {len(all_data)} symbols")

if __name__ == "__main__":
    asyncio.run(test_universal_collector()) 