import requests
import time
from typing import Dict

class DataValidator:
    """Система валидации данных - РАСШИРЕННАЯ ВЕРСИЯ"""
    
    # ПРАВИЛЬНЫЕ ДИАПАЗОНЫ ДЛЯ КАЖДОЙ ПАРЫ
    VALID_RANGES = {
        'BTC/USDT': {'price': (10000, 200000), 'volume': (1000000, 10000000000)},
        'ETH/USDT': {'price': (1000, 20000), 'volume': (500000, 5000000000)},
        'BNB/USDT': {'price': (200, 700), 'volume': (500000, 2000000000)},
        'ADA/USDT': {'price': (0.3, 3.0), 'volume': (10000000, 500000000)},
        'XRP/USDT': {'price': (0.4, 2.0), 'volume': (50000000, 2000000000)},
        'SOL/USDT': {'price': (20, 300), 'volume': (50000000, 3000000000)},
        'DOT/USDT': {'price': (3, 20), 'volume': (10000000, 500000000)},
        'AVAX/USDT': {'price': (10, 100), 'volume': (20000000, 800000000)},
        'LINK/USDT': {'price': (5, 30), 'volume': (30000000, 800000000)},
        'MATIC/USDT': {'price': (0.5, 3.0), 'volume': (50000000, 1500000000)},
        'UNI/USDT': {'price': (3, 50), 'volume': (20000000, 1000000000)},
        'LTC/USDT': {'price': (50, 1000), 'volume': (10000000, 500000000)}
    }
    
    @staticmethod
    def validate_price(price: float, symbol: str) -> bool:
        """Проверка реалистичности цены"""
        if price <= 0:
            return False
        
        if symbol in DataValidator.VALID_RANGES:
            ranges = DataValidator.VALID_RANGES[symbol]
            return ranges['price'][0] <= price <= ranges['price'][1]
        
        return True
    
    @staticmethod
    def validate_volume(volume: float, symbol: str) -> bool:
        """Проверка реалистичности объема"""
        if volume <= 0:
            return False
        
        if symbol in DataValidator.VALID_RANGES:
            ranges = DataValidator.VALID_RANGES[symbol]
            return ranges['volume'][0] <= volume <= ranges['volume'][1]
        
        return True
    
    @staticmethod
    def validate_24h_change(change: float) -> bool:
        """Проверка реалистичности 24h изменения"""
        return -50.0 <= change <= 100.0
    
    @staticmethod
    def validate_market_data(symbol: str, price: float, volume: float, change: float) -> bool:
        """Комплексная валидация рыночных данных"""
        return (
            DataValidator.validate_price(price, symbol) and
            DataValidator.validate_volume(volume, symbol) and
            DataValidator.validate_24h_change(change)
        ) 

class DataFallback:
    """Система резервных источников данных"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 минут
    
    def get_coingecko_data(self, symbol: str) -> Dict:
        """Резервный источник - CoinGecko"""
        try:
            # Конвертируем символ для CoinGecko
            coin_id = symbol.split('/')[0].lower()
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    coin_data = data[coin_id]
                    return {
                        'price': float(coin_data['usd']),
                        'change_24h': float(coin_data.get('usd_24h_change', 0)),
                        'volume': float(coin_data.get('usd_24h_vol', 0)),
                        'source': 'coingecko'
                    }
        except Exception as e:
            print(f"❌ CoinGecko error for {symbol}: {e}")
        return {}
    
    def get_cached_data(self, symbol: str) -> Dict:
        """Получение кэшированных данных"""
        if symbol in self.cache:
            cache_time, data = self.cache[symbol]
            if time.time() - cache_time < self.cache_timeout:
                return data
        return {}
    
    def cache_data(self, symbol: str, data: Dict):
        """Кэширование данных"""
        self.cache[symbol] = (time.time(), data)
    
    def get_reliable_data(self, symbol: str, primary_data: Dict) -> Dict:
        """Получение надежных данных с резервированием"""
        # Проверяем основные данные
        if primary_data and self.validate_primary_data(symbol, primary_data):
            self.cache_data(symbol, primary_data)
            return primary_data
        
        # Проверяем кэш
        cached_data = self.get_cached_data(symbol)
        if cached_data:
            print(f"📦 Используем кэшированные данные для {symbol}")
            return cached_data
        
        # Используем резервный источник
        fallback_data = self.get_coingecko_data(symbol)
        if fallback_data:
            print(f"🔄 Используем резервный источник для {symbol}")
            self.cache_data(symbol, fallback_data)
            return fallback_data
        
        return {}
    
    def validate_primary_data(self, symbol: str, data: Dict) -> bool:
        """Валидация основных данных"""
        if not data:
            return False
        
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        change = data.get('change_24h', 0)
        
        return DataValidator.validate_market_data(symbol, price, volume, change) 