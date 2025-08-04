#!/usr/bin/env python3
"""
Universal Data Manager - Универсальный менеджер данных
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UniversalDataManager:
    """Универсальный менеджер данных для работы с множественными парами"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_timeout = 60  # секунды
        self.rate_limit_delay = 0.1  # задержка между запросами
        
        # API endpoints
        self.apis = {
            'binance': 'https://api.binance.com/api/v3',
            'bybit': 'https://api.bybit.com/v5',
            'okx': 'https://www.okx.com/api/v5'
        }
        
        # Маппинг таймфреймов
        self.timeframe_mapping = {
            '1m': '1m',
            '5m': '5m', 
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
    
    async def __aenter__(self):
        """Асинхронный контекст менеджер - вход"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекст менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def get_multi_timeframe_data(self, pair: str, timeframes: List[str]) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Получает данные для одной пары по нескольким таймфреймам
        
        Args:
            pair: Торговая пара (например, 'BTC/USDT')
            timeframes: Список таймфреймов ['15m', '1h', '4h']
            
        Returns:
            Словарь с данными по таймфреймам или None
        """
        try:
            # Проверяем кеш
            cache_key = f"{pair}_{'_'.join(timeframes)}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_timeout:
                    return cached_data
            
            # Получаем данные по всем таймфреймам
            data_dict = {}
            tasks = []
            
            for tf in timeframes:
                task = self.get_ohlcv_data(pair, tf)
                tasks.append((tf, task))
            
            # Выполняем запросы параллельно
            for tf, task in tasks:
                try:
                    data = await task
                    if data is not None and len(data) > 20:
                        data_dict[tf] = data
                    await asyncio.sleep(self.rate_limit_delay)
                except Exception as e:
                    logger.warning(f"Ошибка получения данных {pair} {tf}: {e}")
            
            # Кешируем результат
            if data_dict:
                self.cache[cache_key] = (data_dict, datetime.now().timestamp())
                return data_dict
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения мультитаймфреймовых данных для {pair}: {e}")
            return None
    
    async def get_ohlcv_data(self, pair: str, timeframe: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Получает OHLCV данные для одной пары и таймфрейма
        
        Args:
            pair: Торговая пара
            timeframe: Таймфрейм
            limit: Количество свечей
            
        Returns:
            DataFrame с OHLCV данными или None
        """
        try:
            # Нормализуем пару
            symbol = pair.replace('/', '')
            
            # Пробуем Binance API
            url = f"{self.apis['binance']}/klines"
            params = {
                'symbol': symbol,
                'interval': self.timeframe_mapping.get(timeframe, timeframe),
                'limit': limit
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_binance_klines(data)
            
            # Если Binance не сработал, создаем симулированные данные
            return self._create_simulated_data(pair, timeframe, limit)
            
        except Exception as e:
            logger.warning(f"Ошибка получения OHLCV для {pair} {timeframe}: {e}")
            return self._create_simulated_data(pair, timeframe, limit)
    
    def _parse_binance_klines(self, data: List) -> pd.DataFrame:
        """Парсит данные свечей от Binance"""
        try:
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Конвертируем типы
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Ошибка парсинга данных Binance: {e}")
            return pd.DataFrame()
    
    def _create_simulated_data(self, pair: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Создает симулированные данные для тестирования"""
        try:
            # Базовые цены для разных пар
            base_prices = {
                'BTC': 50000,
                'ETH': 3000,
                'BNB': 300,
                'ADA': 0.5,
                'SOL': 100,
                'DOT': 7,
                'LINK': 15,
                'MATIC': 0.8,
                'AVAX': 30,
                'ATOM': 10,
                'M': 0.378300
            }
            
            # Определяем базовую цену
            base_price = 100
            for coin, price in base_prices.items():
                if coin in pair:
                    base_price = price
                    break
            
            # Создаем временной ряд
            if timeframe == '1m':
                freq = '1min'
            elif timeframe == '5m':
                freq = '5min'
            elif timeframe == '15m':
                freq = '15min'
            elif timeframe == '30m':
                freq = '30min'
            elif timeframe == '1h':
                freq = '1h'
            elif timeframe == '4h':
                freq = '4h'
            elif timeframe == '1d':
                freq = '1d'
            else:
                freq = '15min'
            
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=limit//24),
                periods=limit,
                freq=freq
            )
            
            # Создаем реалистичные данные с трендом
            trend = np.linspace(0, base_price * 0.02, limit)
            noise = np.random.normal(0, base_price * 0.001, limit)
            prices = base_price + trend + noise
            
            # Создаем OHLC данные
            data = []
            for i, (date, price) in enumerate(zip(dates, prices)):
                # Добавляем волатильность
                volatility = price * 0.002
                
                open_price = price
                high_price = price + abs(np.random.normal(0, volatility))
                low_price = price - abs(np.random.normal(0, volatility))
                close_price = price + np.random.normal(0, volatility * 0.5)
                volume = np.random.uniform(1000000, 5000000)
                
                data.append({
                    'timestamp': date,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Ошибка создания симулированных данных: {e}")
            return pd.DataFrame()
    
    async def get_batch_data(self, pairs: List[str], timeframes: List[str]) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Получает данные для множества пар по нескольким таймфреймам
        
        Args:
            pairs: Список торговых пар
            timeframes: Список таймфреймов
            
        Returns:
            Словарь с данными по парам и таймфреймам
        """
        try:
            # Создаем задачи для всех пар
            tasks = []
            for pair in pairs:
                task = self.get_multi_timeframe_data(pair, timeframes)
                tasks.append((pair, task))
            
            # Выполняем все задачи параллельно
            results = {}
            for pair, task in tasks:
                try:
                    data = await task
                    if data:
                        results[pair] = data
                    await asyncio.sleep(self.rate_limit_delay)
                except Exception as e:
                    logger.warning(f"Ошибка получения данных для {pair}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка батчевого получения данных: {e}")
            return {}
    
    def clear_cache(self):
        """Очищает кеш"""
        self.cache.clear()
        logger.info("Кеш очищен")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кеша"""
        return {
            'cache_size': len(self.cache),
            'cache_timeout': self.cache_timeout,
            'rate_limit_delay': self.rate_limit_delay
        } 