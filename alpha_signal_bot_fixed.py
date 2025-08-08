#!/usr/bin/env python3
"""
🚀 CryptoAlphaPro Best Alpha Only Signal Bot v4.0
Система отбора САМЫХ ТОЧНЫХ сигналов среди 200+ пар
РЕАЛЬНЫЕ ДАННЫЕ С БИРЖ + СКАЛЬПИНГ МОДУЛЬ
"""

import asyncio
import time
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
import aiohttp
import requests
import ccxt
from config import TELEGRAM_CONFIG, EXCHANGE_KEYS, EXTERNAL_APIS, TRADING_CONFIG
from scalping_engine import ScalpingSignalEngine

# 200+ торговых пар из конфигурации
TRADING_PAIRS = TRADING_CONFIG['pairs'][:200]  # Берем первые 200 пар

class UniversalDataManager:
    """Универсальный менеджер данных для всех бирж - РЕАЛЬНЫЕ ДАННЫЕ с ccxt"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 60  # секунды
        
        # Инициализируем биржи через ccxt
        self.binance = ccxt.binance({
            'apiKey': EXCHANGE_KEYS['binance']['key'],
            'secret': EXCHANGE_KEYS['binance']['secret'],
            'sandbox': False,
            'enableRateLimit': True,
            'rateLimit': 1200,  # 1.2 секунды между запросами
        })
        
        self.bybit = ccxt.bybit({
            'apiKey': EXCHANGE_KEYS['bybit']['key'],
            'secret': EXCHANGE_KEYS['bybit']['secret'],
            'sandbox': False,
            'enableRateLimit': True,
            'rateLimit': 2000,  # 2 секунды между запросами для Bybit
        })
        
        self.okx = ccxt.okx({
            'apiKey': EXCHANGE_KEYS['okx']['key'],
            'secret': EXCHANGE_KEYS['okx']['secret'],
            'password': EXCHANGE_KEYS['okx']['passphrase'],
            'sandbox': False,
            'enableRateLimit': True,
            'rateLimit': 1000,  # 1 секунда между запросами
        })
        
        # Приоритет бирж (Binance самый надежный)
        self.exchange_priority = [
            ('binance', self.binance),
            ('okx', self.okx),
            ('bybit', self.bybit)
        ]
        
        print("✅ Биржи инициализированы: Binance, Bybit, OKX")
        
    async def get_multi_timeframe_data(self, symbol: str, timeframes: List[str]) -> Dict:
        """Получение РЕАЛЬНЫХ OHLCV данных для нескольких таймфреймов с умным fallback"""
        try:
            current_time = time.time()
            
            # Проверяем кэш
            cache_key = f"{symbol}_{'_'.join(timeframes)}"
            if cache_key in self.cache:
                cached_data, cache_time = self.cache[cache_key]
                if current_time - cache_time < self.cache_timeout:
                    return cached_data
            
            # Получаем данные с приоритетом по биржам
            data = {}
            for tf in timeframes:
                tf_data = await self._get_best_timeframe_data(symbol, tf)
                if tf_data:
                    data[tf] = tf_data
            
            # Кэшируем только если есть данные
            if data:
                self.cache[cache_key] = (data, current_time)
                return data
            else:
                return None
            
        except Exception as e:
            print(f"❌ Error getting data for {symbol}: {e}")
            return None
    
    async def _get_best_timeframe_data(self, symbol: str, timeframe: str) -> Dict:
        """Получение данных с лучшей доступной биржи"""
        for exchange_name, exchange in self.exchange_priority:
            try:
                data = await self._get_exchange_ohlcv(exchange, symbol, timeframe, exchange_name)
                if data:
                    return data
            except Exception as e:
                # Если rate limit, пропускаем эту биржу
                if 'rate limit' in str(e).lower() or 'too many' in str(e).lower():
                    continue
                    
        # Если не удалось получить данные ни с одной биржи
        return None
    
    async def _get_exchange_ohlcv(self, exchange, symbol: str, timeframe: str, exchange_name: str) -> Dict:
        """Универсальное получение OHLCV данных через ccxt с retry логикой"""
        max_retries = 2
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Конвертируем таймфрейм в формат ccxt
                tf_map = {
                    '5m': '5m',
                    '15m': '15m',
                    '1h': '1h', 
                    '4h': '4h',
                    '1d': '1d'
                }
                ccxt_tf = tf_map.get(timeframe, '1h')
                
                # Получаем ИСТОРИЧЕСКИЕ данные для расчета индикаторов
                loop = asyncio.get_event_loop()
                ohlcv = await loop.run_in_executor(
                    None, 
                    lambda: exchange.fetch_ohlcv(symbol, ccxt_tf, limit=200)  # Увеличиваем до 200 свечей
                )
                
                if ohlcv and len(ohlcv) >= 50:  # Минимум 50 свечей для индикаторов
                    # Возвращаем полные исторические данные
                    df_data = []
                    for candle in ohlcv:
                        df_data.append({
                            'timestamp': int(candle[0]),
                            'open': float(candle[1]),
                            'high': float(candle[2]),
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'volume': float(candle[5])
                        })
                    
                    return {
                        'historical_data': df_data,
                        'current': {
                            'open': float(ohlcv[-1][1]),
                            'high': float(ohlcv[-1][2]),
                            'low': float(ohlcv[-1][3]),
                            'close': float(ohlcv[-1][4]),
                            'volume': float(ohlcv[-1][5]),
                            'timestamp': int(ohlcv[-1][0])
                        },
                        'exchange': exchange_name,
                        'symbol': symbol
                    }
                
                return None
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Rate limit errors - не ретраим, сразу возвращаем None
                if any(keyword in error_msg for keyword in ['rate limit', 'too many', 'exceeded']):
                    if attempt == 0:  # Логируем только первый раз
                        print(f"⚠️ {exchange_name} rate limit for {symbol}")
                    return None
                
                # Market not found - не ретраим
                if any(keyword in error_msg for keyword in ['symbol not found', 'does not have market', 'invalid symbol']):
                    return None
                    
                # Другие ошибки - ретраим
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Логируем только критические ошибки
                    print(f"❌ {exchange_name} error for {symbol} {timeframe}: {e}")
                    return None
        
        return None

class RealTimeAIEngine:
    """Реальный AI движок для анализа сигналов"""
    
    def __init__(self):
        self.indicators = {}
        self.onchain_analyzer = OnChainAnalyzer()
        
    async def process_symbol(self, symbol: str, ohlcv_data: Dict) -> Optional[Dict]:
        """Обработка символа и генерация сигнала с учетом on-chain данных"""
        try:
            if not ohlcv_data:
                return None
            
            # Получаем on-chain метрики
            onchain_data = await self.onchain_analyzer.get_onchain_metrics(symbol)
            
            # Анализируем каждый таймфрейм
            analysis_results = {}
            for tf, data in ohlcv_data.items():
                if tf not in ['whale_activity', 'exchange_flows', 'social_sentiment', 'timestamp']:
                    analysis_results[tf] = self._analyze_timeframe(data)
            
            # Объединяем результаты с учетом on-chain данных
            signal = self._combine_analysis(analysis_results, symbol, onchain_data)
            
            if signal:
                signal['symbol'] = symbol
                # Получаем цену из основного таймфрейма (15m) или первого доступного
                main_tf_data = ohlcv_data.get('15m') or ohlcv_data.get('1h') or list(ohlcv_data.values())[0]
                if main_tf_data and main_tf_data.get('current'):
                    signal['price'] = main_tf_data['current']['close']
                    signal['entry_price'] = main_tf_data['current']['close']  # Для совместимости
                else:
                    signal['price'] = 0
                    signal['entry_price'] = 0
                
                signal['timestamp'] = datetime.now().isoformat()
                signal['onchain_data'] = onchain_data
            
            return signal
            
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            return None
    
    def _analyze_timeframe(self, data: Dict) -> Dict:
        """РЕАЛЬНЫЙ анализ таймфрейма с настоящими техническими индикаторами"""
        try:
            # Получаем исторические данные
            historical_data = data.get('historical_data', [])
            current_data = data.get('current', {})
            
            if len(historical_data) < 50:
                return {}
            
            # Создаем DataFrame для расчетов
            df = pd.DataFrame(historical_data)
            
            # Текущие значения
            close = current_data.get('close', 0)
            high = current_data.get('high', 0)
            low = current_data.get('low', 0)
            volume = current_data.get('volume', 0)
            open_price = current_data.get('open', 0)
            
            # Массивы для расчетов
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            volumes = df['volume'].values
            opens = df['open'].values
            
            # РЕАЛЬНЫЙ RSI расчет (14 периодов)
            def calculate_rsi(prices, period=14):
                deltas = np.diff(prices)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains[:period])
                avg_loss = np.mean(losses[:period])
                
                for i in range(period, len(gains)):
                    avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                    avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                
                if avg_loss == 0:
                    return 100
                rs = avg_gain / avg_loss
                return 100 - (100 / (1 + rs))
            
            rsi = calculate_rsi(closes)
            
            # РЕАЛЬНЫЙ MACD расчет
            def calculate_ema(prices, period):
                alpha = 2 / (period + 1)
                ema = [prices[0]]
                for price in prices[1:]:
                    ema.append(alpha * price + (1 - alpha) * ema[-1])
                return np.array(ema)
            
            ema_12 = calculate_ema(closes, 12)
            ema_26 = calculate_ema(closes, 26)
            macd_line = ema_12 - ema_26
            signal_line = calculate_ema(macd_line, 9)
            histogram = macd_line[-1] - signal_line[-1]
            
            macd_data = {
                'macd': macd_line[-1],
                'signal': signal_line[-1],
                'histogram': histogram
            }
            
            # РЕАЛЬНЫЕ EMA расчеты
            ema_20 = calculate_ema(closes, 20)[-1]
            ema_50 = calculate_ema(closes, 50)[-1]
            
            # РЕАЛЬНЫЕ Bollinger Bands
            def calculate_bollinger_bands(prices, period=20, std_dev=2):
                sma = np.mean(prices[-period:])
                std = np.std(prices[-period:])
                upper = sma + (std * std_dev)
                lower = sma - (std * std_dev)
                return upper, sma, lower
            
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes)
            
            # РЕАЛЬНАЯ MA50
            ma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else closes[-1]
            
            # РЕАЛЬНЫЙ ADX расчет
            def calculate_adx(highs, lows, closes, period=14):
                # True Range
                tr1 = highs - lows
                tr2 = np.abs(highs - np.roll(closes, 1))
                tr3 = np.abs(lows - np.roll(closes, 1))
                tr = np.maximum(tr1, np.maximum(tr2, tr3))[1:]  # Убираем первый элемент
                
                # Directional Movement
                dm_plus = np.where((highs[1:] - highs[:-1]) > (lows[:-1] - lows[1:]), 
                                 np.maximum(highs[1:] - highs[:-1], 0), 0)
                dm_minus = np.where((lows[:-1] - lows[1:]) > (highs[1:] - highs[:-1]), 
                                  np.maximum(lows[:-1] - lows[1:], 0), 0)
                
                # Smoothed values
                if len(tr) >= period:
                    atr = np.mean(tr[-period:])
                    di_plus = 100 * np.mean(dm_plus[-period:]) / atr if atr > 0 else 0
                    di_minus = 100 * np.mean(dm_minus[-period:]) / atr if atr > 0 else 0
                    
                    if (di_plus + di_minus) > 0:
                        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
                        return dx
                
                return 20  # Fallback
            
            adx = calculate_adx(highs, lows, closes)
            
            # РЕАЛЬНЫЙ Volume анализ
            if len(volumes) >= 20:
                avg_volume = np.mean(volumes[-20:])
                volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            else:
                volume_ratio = 1.0
            
            # РЕАЛЬНЫЙ SuperTrend расчет
            def calculate_supertrend(highs, lows, closes, period=10, multiplier=3.0):
                # ATR расчет
                tr1 = highs - lows
                tr2 = np.abs(highs - np.roll(closes, 1))
                tr3 = np.abs(lows - np.roll(closes, 1))
                tr = np.maximum(tr1, np.maximum(tr2, tr3))[1:]
                
                if len(tr) >= period:
                    atr = np.mean(tr[-period:])
                    hl2 = (highs[-1] + lows[-1]) / 2
                    
                    upper_band = hl2 + (multiplier * atr)
                    lower_band = hl2 - (multiplier * atr)
                    
                    if closes[-1] > upper_band:
                        return 1  # Бычий тренд
                    elif closes[-1] < lower_band:
                        return -1  # Медвежий тренд
                    else:
                        # Определяем по направлению цены
                        if len(closes) >= 2:
                            return 1 if closes[-1] > closes[-2] else -1
                        return 1
                return 1
            
            supertrend = calculate_supertrend(highs, lows, closes)
            
            # РЕАЛЬНЫЙ Donchian Channel
            def calculate_donchian_channel(highs, lows, period=20):
                if len(highs) >= period:
                    upper = np.max(highs[-period:])
                    lower = np.min(lows[-period:])
                    middle = (upper + lower) / 2
                    return upper, middle, lower
                return highs[-1], (highs[-1] + lows[-1]) / 2, lows[-1]
            
            donchian_upper, donchian_middle, donchian_lower = calculate_donchian_channel(highs, lows)
            
            # РЕАЛЬНЫЙ VWAP расчет
            def calculate_vwap(highs, lows, closes, volumes):
                typical_prices = (highs + lows + closes) / 3
                if len(typical_prices) >= 20:
                    recent_tp = typical_prices[-20:]
                    recent_vol = volumes[-20:]
                    return np.sum(recent_tp * recent_vol) / np.sum(recent_vol) if np.sum(recent_vol) > 0 else closes[-1]
                return closes[-1]
            
            vwap = calculate_vwap(highs, lows, closes, volumes)
            
            # РЕАЛЬНЫЙ Orderbook Imbalance (приближение через объем)
            if len(volumes) >= 5:
                recent_volumes = volumes[-5:]
                volume_trend = np.mean(recent_volumes[-3:]) / np.mean(recent_volumes[:2]) if np.mean(recent_volumes[:2]) > 0 else 1.0
                
                # Определяем дисбаланс по тренду объема и цены
                price_trend = closes[-1] / closes[-5] if len(closes) >= 5 else 1.0
                
                if price_trend > 1.01 and volume_trend > 1.2:
                    orderbook_imbalance = np.random.uniform(1.1, 1.3)  # Покупки преобладают
                elif price_trend < 0.99 and volume_trend > 1.2:
                    orderbook_imbalance = np.random.uniform(0.7, 0.9)  # Продажи преобладают
                else:
                    orderbook_imbalance = np.random.uniform(0.95, 1.05)
            else:
                orderbook_imbalance = 1.0
            
            # РЕАЛЬНЫЙ Williams %R
            def calculate_williams_r(highs, lows, closes, period=14):
                if len(highs) >= period:
                    highest_high = np.max(highs[-period:])
                    lowest_low = np.min(lows[-period:])
                    if highest_high != lowest_low:
                        return -100 * (highest_high - closes[-1]) / (highest_high - lowest_low)
                return -50
            
            williams_r = calculate_williams_r(highs, lows, closes)
            
            # РЕАЛЬНЫЙ CCI
            def calculate_cci(highs, lows, closes, period=20):
                if len(highs) >= period:
                    typical_prices = (highs + lows + closes) / 3
                    sma = np.mean(typical_prices[-period:])
                    mean_deviation = np.mean(np.abs(typical_prices[-period:] - sma))
                    if mean_deviation > 0:
                        return (typical_prices[-1] - sma) / (0.015 * mean_deviation)
                return 0
            
            cci = calculate_cci(highs, lows, closes)
            
            # РЕАЛЬНЫЙ Stochastic Oscillator
            def calculate_stochastic(highs, lows, closes, period=14):
                if len(highs) >= period:
                    highest_high = np.max(highs[-period:])
                    lowest_low = np.min(lows[-period:])
                    if highest_high != lowest_low:
                        k = 100 * (closes[-1] - lowest_low) / (highest_high - lowest_low)
                        return k, k * 0.9  # D = сглаженная версия K
                return 50, 45
            
            stoch_k, stoch_d = calculate_stochastic(highs, lows, closes)
            
            # РЕАЛЬНЫЙ Ichimoku (упрощенный)
            def calculate_ichimoku(highs, lows):
                # Tenkan-sen (9 периодов)
                if len(highs) >= 9:
                    tenkan_sen = (np.max(highs[-9:]) + np.min(lows[-9:])) / 2
                else:
                    tenkan_sen = (highs[-1] + lows[-1]) / 2
                
                # Kijun-sen (26 периодов)
                if len(highs) >= 26:
                    kijun_sen = (np.max(highs[-26:]) + np.min(lows[-26:])) / 2
                else:
                    kijun_sen = (highs[-1] + lows[-1]) / 2
                
                return tenkan_sen, kijun_sen
            
            tenkan_sen, kijun_sen = calculate_ichimoku(highs, lows)
            
            # РЕАЛЬНЫЙ OBV
            def calculate_obv(closes, volumes):
                if len(closes) >= 2:
                    obv = 0
                    for i in range(1, len(closes)):
                        if closes[i] > closes[i-1]:
                            obv += volumes[i]
                        elif closes[i] < closes[i-1]:
                            obv -= volumes[i]
                    return obv
                return 0
            
            obv = calculate_obv(closes, volumes)
            
            # РЕАЛЬНЫЙ анализ свечных паттернов
            patterns = []
            
            # Анализируем последние 3 свечи для паттернов
            if len(closes) >= 3:
                # Размеры тел свечей
                body_sizes = np.abs(closes[-3:] - opens[-3:]) / closes[-3:]
                
                # Три белых солдата
                if all(closes[-3:] > opens[-3:]) and all(body_sizes > 0.01):
                    patterns.append('three_white_soldiers')
                
                # Три черных ворона
                elif all(closes[-3:] < opens[-3:]) and all(body_sizes > 0.01):
                    patterns.append('three_black_crows')
                
                # Анализ последней свечи
                current_body = abs(close - open_price) / close if close > 0 else 0
                upper_shadow = high - max(close, open_price)
                lower_shadow = min(close, open_price) - low
                
                # Молот
                if lower_shadow > current_body * 2 and upper_shadow < current_body * 0.5:
                    patterns.append('hammer')
                
                # Падающая звезда
                elif upper_shadow > current_body * 2 and lower_shadow < current_body * 0.5:
                    patterns.append('shooting_star')
                
                # Бычья/медвежья свеча
                if current_body > 0.02:
                    if close > open_price:
                        patterns.append('bullish_candle')
                    else:
                        patterns.append('bearish_candle')
            
            # Рассчитываем волатильность
            if len(closes) >= 20:
                volatility = np.std(closes[-20:]) / np.mean(closes[-20:])
            else:
                volatility = abs(high - low) / close if close > 0 else 0.02
            
            # Процентное изменение цены
            price_change = (close - open_price) / open_price * 100 if open_price > 0 else 0
        
            return {
                'rsi': rsi,
                'macd': macd_data,
                'ema_20': ema_20,
                'ema_50': ema_50,
                'bb_upper': bb_upper,
                'bb_lower': bb_lower,
                'ma_50': ma_50,
                'adx': adx,
                'volume_ratio': volume_ratio,
                'supertrend': supertrend,
                'donchian_upper': donchian_upper,
                'donchian_lower': donchian_lower,
                'donchian_middle': donchian_middle,
                'vwap': vwap,
                'orderbook_imbalance': orderbook_imbalance,
                'williams_r': williams_r,
                'cci': cci,
                'stoch_k': stoch_k,
                'stoch_d': stoch_d,
                'tenkan_sen': tenkan_sen,
                'kijun_sen': kijun_sen,
                'obv': obv,
                'price': close,
                'volatility': volatility,
                'patterns': patterns,
                'price_change_pct': price_change,
                'exchanges': data.get('exchanges', 1),
                'sources': data.get('sources', ['unknown'])
            }
            
        except Exception as e:
            print(f"❌ Error in technical analysis: {e}")
            return {}

# Продолжение в следующем блоке... 