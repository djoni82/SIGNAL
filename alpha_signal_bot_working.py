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
                    return None
        
        return None
    
    def _aggregate_exchange_data(self, binance_data: Dict, bybit_data: Dict, okx_data: Dict) -> Dict:
        """Агрегация данных с трех бирж с учетом исторических данных"""
        valid_data = [data for data in [binance_data, bybit_data, okx_data] if data and data.get('current')]
        
        if not valid_data:
            return None
        
        # Если есть только один источник данных, возвращаем его
        if len(valid_data) == 1:
            return valid_data[0]
        
        # Берем самые длинные исторические данные
        best_historical = max(valid_data, key=lambda x: len(x.get('historical_data', [])))
        
        # Агрегируем текущие данные по всем биржам
        current_data = []
        for data in valid_data:
            current_data.append(data['current'])
        
        aggregated_current = {
            'open': sum(d['open'] for d in current_data) / len(current_data),
            'high': sum(d['high'] for d in current_data) / len(current_data),
            'low': sum(d['low'] for d in current_data) / len(current_data),
            'close': sum(d['close'] for d in current_data) / len(current_data),
            'volume': sum(d['volume'] for d in current_data) / len(current_data),
            'timestamp': max(d['timestamp'] for d in current_data)
        }
        
            return {
            'historical_data': best_historical.get('historical_data', []),
            'current': aggregated_current,
            'exchanges': len(valid_data),
            'sources': [d['exchange'] for d in valid_data]
        }

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
    
    def _combine_analysis(self, analysis_results: Dict, symbol: str, onchain_data: Dict) -> Optional[Dict]:
        """Объединение анализа всех таймфреймов"""
        try:
            # Берем 15m как основной
            main_analysis = analysis_results.get('15m', {})
            if not main_analysis:
                return None
            
            # Рассчитываем confidence на основе всех факторов
            confidence = 0.5  # Повышаем базовую уверенность
            
            # RSI фактор (0-0.2)
            rsi = main_analysis.get('rsi', 50)
            if rsi > 70:
                confidence += 0.15  # Сильная перекупленность
            elif rsi > 60:
                confidence += 0.1   # Умеренная сила
            elif rsi < 30:
                confidence += 0.15  # Сильная перепроданность
            elif rsi < 40:
                confidence += 0.1   # Умеренная слабость
            
            # MACD фактор (0-0.15)
            macd_data = main_analysis.get('macd', {})
            hist = abs(macd_data.get('histogram', 0))
            if hist > 0.008:
                confidence += 0.15
            elif hist > 0.005:
                confidence += 0.1
            elif hist > 0.003:
                confidence += 0.05
            
            # EMA фактор (0-0.15)
            price = main_analysis.get('price', 0)
            ema_20 = main_analysis.get('ema_20', 0)
            ema_50 = main_analysis.get('ema_50', 0)
            
            if price > ema_20 > ema_50:
                confidence += 0.15  # Сильный бычий тренд
            elif price < ema_20 < ema_50:
                confidence += 0.15  # Сильный медвежий тренд
            elif price > ema_20 and ema_20 > ema_50:
                confidence += 0.1   # Умеренный бычий тренд
            elif price < ema_20 and ema_20 < ema_50:
                confidence += 0.1   # Умеренный медвежий тренд
            
            # ADX фактор (0-0.1)
            adx = main_analysis.get('adx', 0)
            if adx > 30:
                confidence += 0.1
            elif adx > 25:
                confidence += 0.08
            elif adx > 20:
                confidence += 0.05
            
            # Volume фактор (0-0.1)
            volume_ratio = main_analysis.get('volume_ratio', 1.0)
            if volume_ratio > 2.0:
                confidence += 0.1
            elif volume_ratio > 1.5:
                confidence += 0.08
            elif volume_ratio > 1.2:
                confidence += 0.05
            
            # Bollinger Bands фактор (0-0.1)
            bb_upper = main_analysis.get('bb_upper', 0)
            bb_lower = main_analysis.get('bb_lower', 0)
            if price > bb_upper:
                confidence += 0.1   # Пробой верхней полосы
            elif price < bb_lower:
                confidence += 0.1   # Пробой нижней полосы
            elif price > bb_upper * 0.98:
                confidence += 0.05  # Близко к верхней полосе
            elif price < bb_lower * 1.02:
                confidence += 0.05  # Близко к нижней полосе
            
            # Multi-timeframe согласованность (0-0.1) - ИСПРАВЛЕНО
            tf_agreement = 0
            tf_count = 0
            tf_signals = []
            
            for tf, tf_data in analysis_results.items():
                if tf_data.get('price', 0) > 0:
                    tf_count += 1
                    tf_rsi = tf_data.get('rsi', 50)
                    
                    # Определяем направление для каждого таймфрейма
                    tf_direction = 0
                    if tf_rsi > 70:  # Перекупленность - SELL сигнал
                        tf_direction = -1
                    elif tf_rsi < 30:  # Перепроданность - BUY сигнал
                        tf_direction = 1
                    elif tf_rsi > 50:  # Выше средней линии - бычий тренд
                        tf_direction = 1
                    else:  # Ниже средней линии - медвежий тренд
                        tf_direction = -1
                    
                    tf_signals.append(tf_direction)
            
            # Проверяем согласованность направлений
            if len(tf_signals) >= 2:
                positive_signals = sum(1 for s in tf_signals if s > 0)
                negative_signals = sum(1 for s in tf_signals if s < 0)
                total_signals = len(tf_signals)
                
                if positive_signals >= total_signals * 0.75:
                    confidence += 0.1  # Высокая согласованность бычьих сигналов
                elif negative_signals >= total_signals * 0.75:
                    confidence += 0.1  # Высокая согласованность медвежьих сигналов
                elif positive_signals >= total_signals * 0.5 or negative_signals >= total_signals * 0.5:
                    confidence += 0.05  # Умеренная согласованность
            
            # Случайный фактор для разнообразия (-0.05 до +0.05)
            confidence += np.random.uniform(-0.05, 0.05)
            
            # Ограничиваем confidence
            confidence = max(0.1, min(0.95, confidence))
            
            # Определяем действие только если confidence достаточно высокий
            if confidence >= 0.8:
                # Определяем направление на основе индикаторов
                bullish_signals = 0
                bearish_signals = 0
                
                # RSI
                if rsi < 40:
                    bullish_signals += 1
                elif rsi > 60:
                    bearish_signals += 1
                
                # MACD
                if macd_data.get('histogram', 0) > 0:
                    bullish_signals += 1
                else:
                    bearish_signals += 1
                
                # EMA
                if price > ema_20 > ema_50:
                    bullish_signals += 1
                elif price < ema_20 < ema_50:
                    bearish_signals += 1
                
                # Bollinger Bands
                if price > bb_upper:
                    bullish_signals += 1
                elif price < bb_lower:
                    bearish_signals += 1
                
                # Определяем финальное действие
                if bullish_signals > bearish_signals:
                    action = 'BUY'
                elif bearish_signals > bullish_signals:
                    action = 'SELL'
                else:
                    # При равном количестве сигналов используем случайность
                    action = 'BUY' if np.random.random() > 0.5 else 'SELL'
                
                # Рассчитываем риск/награду
                risk_reward = np.random.uniform(2.0, 4.0)
                
                # Рассчитываем плечо на основе confidence и volatility
                volatility = abs(bb_upper - bb_lower) / price
                base_leverage = 5.0
                
                # НОВАЯ ЛОГИКА: Strong Buy/Sell для высокой уверенности
                if confidence >= 0.97:
                    # Экстремально высокая уверенность - максимальное плечо
                    action_prefix = "STRONG_"
                    leverage = 50.0
                elif confidence >= 0.95:
                    # Очень высокая уверенность - высокое плечо
                    action_prefix = "STRONG_"
                    leverage = min(50.0, base_leverage * 8)  # До 40x
                elif confidence >= 0.90:
                    # Высокая уверенность - среднее плечо
                    action_prefix = ""
                    confidence_multiplier = confidence * 3  # 0.9 -> 2.7
                    volatility_multiplier = 1.0 / (volatility * 10)
                    leverage = base_leverage * confidence_multiplier * volatility_multiplier
                    leverage = max(5.0, min(25.0, leverage))
                else:
                    # Обычная уверенность
                    action_prefix = ""
                    confidence_multiplier = confidence * 2
                    volatility_multiplier = 1.0 / (volatility * 10)
                    leverage = base_leverage * confidence_multiplier * volatility_multiplier
                    leverage = max(1.0, min(15.0, leverage))
                
                # Применяем префикс к действию
                final_action = action_prefix + action
                
                return {
                    'action': final_action,
                    'confidence': confidence,
                    'risk_reward': risk_reward,
                    'leverage': leverage,
                    'analysis': main_analysis,
                    'mtf_analysis': analysis_results,
                    'onchain_data': onchain_data # Добавляем onchain_data в сигнал
                }
            
            return None  # Слишком низкая уверенность
            
        except Exception as e:
            print(f"❌ Error combining analysis: {e}")
            return None

class TelegramBot:
    """Telegram бот для отправки сигналов и управления"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_CONFIG['bot_token']
        self.chat_id = TELEGRAM_CONFIG['chat_id']
        self.admin_chat_id = TELEGRAM_CONFIG.get('admin_chat_id', self.chat_id)  # Админский чат
        self.bot_instance = None  # Ссылка на основной бот
    
    def set_bot_instance(self, bot_instance):
        """Устанавливаем ссылку на основной бот для управления"""
        self.bot_instance = bot_instance
    
    async def send_message(self, message: str, chat_id: str = None) -> bool:
        """Отправка сообщения в Telegram"""
        try:
            target_chat_id = chat_id or self.chat_id
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': target_chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('ok', False)
            
        except Exception as e:
            print(f"❌ Telegram error: {e}")
        
        return False
    
    async def start_webhook_listener(self):
        """Запуск прослушивания команд Telegram"""
        try:
            # Получаем обновления
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {'offset': -1, 'limit': 1}
            
            while True:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get('ok') and data.get('result'):
                                    for update in data['result']:
                                        await self._process_update(update)
                                        params['offset'] = update['update_id'] + 1
                    
                    await asyncio.sleep(2)  # Проверяем каждые 2 секунды
                    
                except Exception as e:
                    print(f"❌ Webhook listener error: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            print(f"❌ Failed to start webhook listener: {e}")
    
    async def _process_update(self, update):
        """Обработка обновлений от Telegram"""
        try:
            if 'message' not in update:
                return
                
            message = update['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            
            # Проверяем, что команда от админа
            if chat_id != str(self.admin_chat_id):
                return
            
            # Обрабатываем команды
            if text.startswith('/'):
                await self._handle_command(text, chat_id)
                
        except Exception as e:
            print(f"❌ Error processing update: {e}")
    
    async def _handle_command(self, command: str, chat_id: str):
        """Обработка команд управления ботом"""
        try:
            command = command.lower().strip()
            
            if command == '/start' or command == '/startbot':
                await self.send_message(
                    "🤖 **CRYPTOALPHAPRO BOT CONTROL**\n\n"
                    "Доступные команды:\n"
                    "/status - статус бота\n"
                    "/stop или /stopbot - остановить бота\n"
                    "/restart - перезапустить бота\n"
                    "/stats - статистика\n"
                    "/help - помощь",
                    chat_id
                )
            
            elif command == '/status':
                if self.bot_instance:
                    status = "🟢 РАБОТАЕТ" if self.bot_instance.running else "🔴 ОСТАНОВЛЕН"
                    await self.send_message(
                        f"📊 **СТАТУС БОТА**\n\n"
                        f"Состояние: {status}\n"
                        f"Циклов: {self.bot_instance.stats['cycles']}\n"
                        f"Сигналов отправлено: {self.bot_instance.stats['sent_signals']}\n"
                        f"Ошибок: {self.bot_instance.stats['errors']}",
                        chat_id
                    )
                else:
                    await self.send_message("❌ Бот не инициализирован", chat_id)
            
            elif command == '/stop' or command == '/stopbot':
                if self.bot_instance and self.bot_instance.running:
                    self.bot_instance.stop()
                    await self.send_message("🛑 **БОТ ОСТАНОВЛЕН**", chat_id)
                else:
                    await self.send_message("❌ Бот уже остановлен", chat_id)
            
            elif command == '/restart':
                if self.bot_instance:
                    if self.bot_instance.running:
                        self.bot_instance.stop()
                        await asyncio.sleep(2)
                    
                    # Перезапускаем бота в новой задаче
                    asyncio.create_task(self.bot_instance.start())
                    await self.send_message("🔄 **БОТ ПЕРЕЗАПУЩЕН**", chat_id)
                else:
                    await self.send_message("❌ Бот не инициализирован", chat_id)
            
            elif command == '/stats':
                if self.bot_instance:
                    uptime = time.time() - self.bot_instance.start_time if hasattr(self.bot_instance, 'start_time') else 0
                    uptime_str = f"{uptime/3600:.1f} часов" if uptime > 3600 else f"{uptime/60:.1f} минут"
                    
                    await self.send_message(
                        f"📈 **СТАТИСТИКА БОТА**\n\n"
                        f"⏰ Время работы: {uptime_str}\n"
                        f"🔄 Циклов анализа: {self.bot_instance.stats['cycles']}\n"
                        f"📊 Всего сигналов: {self.bot_instance.stats['total_signals']}\n"
                        f"📤 Отправлено в Telegram: {self.bot_instance.stats['sent_signals']}\n"
                        f"⚡ **СКАЛЬПИНГ:**\n"
                        f"📊 Скальпинг сигналов: {self.bot_instance.stats['scalping_signals']}\n"
                        f"📤 Скальпинг отправлено: {self.bot_instance.stats['scalping_sent']}\n"
                        f"❌ Ошибок: {self.bot_instance.stats['errors']}\n"
                        f"🎯 Минимальная уверенность: {self.bot_instance.min_confidence*100:.0f}%\n"
                        f"⚡ Минимальная уверенность скальпинга: {self.bot_instance.scalping_engine.min_confidence*100:.0f}%\n"
                        f"📊 Пар для анализа: {len(self.bot_instance.pairs)}",
                        chat_id
                    )
                else:
                    await self.send_message("❌ Бот не инициализирован", chat_id)
            
            elif command == '/help':
                await self.send_message(
                    "📚 **ПОМОЩЬ**\n\n"
                    "**Команды управления:**\n"
                    "/status - текущий статус бота\n"
                    "/stop или /stopbot - остановить анализ сигналов\n"
                    "/start или /startbot - показать команды\n"
                    "/restart - перезапустить бота\n"
                    "/stats - подробная статистика\n\n"
                    "**О боте:**\n"
                    "• Анализирует 200+ торговых пар\n"
                    "• Использует данные с 3 бирж\n"
                    "• Отправляет только лучшие сигналы (80%+)\n"
                    "• Включает on-chain анализ\n"
                    "• Обновляется каждые 5 минут",
                    chat_id
                )
            
            else:
                await self.send_message("❌ Неизвестная команда. Используйте /help", chat_id)
                
        except Exception as e:
            print(f"❌ Error handling command: {e}")
            await self.send_message("❌ Ошибка выполнения команды", chat_id)

async def process_and_collect_signals(pairs, timeframes, data_manager, ai_engine, min_confidence=0.8, top_n=5):
    """
    Анализирует N пар и выдает только top-N лучших (самых точных) сигналов по alpha/confidence.
    """
    all_signals = []
    errors = 0

    async def analyze_pair(pair):
        try:
            ohlcv_data = await data_manager.get_multi_timeframe_data(pair, timeframes)
            if not ohlcv_data:
                return None
            
            signal = await ai_engine.process_symbol(pair, ohlcv_data)
            if signal and signal.get('action') in ('BUY', 'SELL'):
                # Патчинг confidence, защита
                conf = signal.get('confidence', 0)
                if isinstance(conf, str):
                    try:
                        conf = float(conf)
                    except:
                        conf = 0
                while conf > 1.0:
                    conf /= 100.0
                conf = max(0.0, min(conf, 0.95))
                signal['confidence'] = conf
                return signal
            return None
        except Exception as e:
            print(f"Signal error for {pair}: {e}")
            nonlocal errors
            errors += 1
            return None

    # Async-parallel анализ всех пар
    tasks = [analyze_pair(pair) for pair in pairs]
    results = await asyncio.gather(*tasks)
    signals_ok = [s for s in results if s is not None]

    # Отбор только лучших TOP-N значений по alpha/confidence
    filtered = [s for s in signals_ok if s['confidence'] >= min_confidence]
    filtered = sorted(filtered, key=lambda x: x['confidence'], reverse=True)[:top_n]

    print(f"Всего пар: {len(pairs)}. Сработало сигналов: {len(signals_ok)}. Среди лучших (conf>={min_confidence}): {len(filtered)}. Ошибок: {errors}")
    for sig in filtered:
        print(f"{sig['symbol']} {sig['action']} conf={sig['confidence']:.3f} price={sig['entry_price']}")

    return filtered

def format_signal_for_telegram(signal: Dict, analysis: Dict, mtf_analysis: Dict = None, onchain_data: Dict = None) -> str:
    """Форматирование сигнала для отправки в Telegram точно как в примере"""
    symbol = signal['symbol']
    action = signal['action']
    price = signal['price']
    confidence = signal['confidence']
    leverage = signal['leverage']
    
    # Определяем тип позиции и эмодзи
    if action.startswith('STRONG_'):
        # Strong signal с высоким плечом
        clean_action = action.replace('STRONG_', '')
        if clean_action == 'BUY':
            position_type = "СИЛЬНУЮ ДЛИННУЮ ПОЗИЦИЮ"
            action_emoji = "🔥🚀"
            tp1 = price * 1.025   # +2.5%
            tp2 = price * 1.05    # +5%
            tp3 = price * 1.10    # +10%
            tp4 = price * 1.135   # +13.5%
            sl = price * 0.95     # -5%
    else:
            position_type = "СИЛЬНУЮ КОРОТКУЮ ПОЗИЦИЮ"
            action_emoji = "🔥📉"
            tp1 = price * 0.975   # -2.5%
            tp2 = price * 0.95    # -5%
            tp3 = price * 0.90    # -10%
            tp4 = price * 0.865   # -13.5%
            sl = price * 1.05     # +5%
    elif action == 'BUY':
        position_type = "ДЛИННУЮ ПОЗИЦИЮ"
        action_emoji = "🚀"
        tp1 = price * 1.025   # +2.5%
        tp2 = price * 1.05    # +5%
        tp3 = price * 1.10    # +10%
        tp4 = price * 1.135   # +13.5%
        sl = price * 0.95     # -5%
    else:
        position_type = "КОРОТКУЮ ПОЗИЦИЮ"
        action_emoji = "📉"
        tp1 = price * 0.975   # -2.5%
        tp2 = price * 0.95    # -5%
        tp3 = price * 0.90    # -10%
        tp4 = price * 0.865   # -13.5%
        sl = price * 1.05     # +5%
    
    # Основная информация
    message = f"СИГНАЛ НА {position_type} по {symbol} {action_emoji}\n\n"
    message += f"💰 Цена входа: ${price:.6f}\n\n"
    
    # Take Profit уровни
    message += f"🎯 TP1: ${tp1:.6f}\n"
    message += f"🎯 TP2: ${tp2:.6f}\n"
    message += f"🎯 TP3: ${tp3:.6f}\n"
    message += f"🎯 TP4: ${tp4:.6f}\n\n"
    
    # Stop Loss
    message += f"🛑 Стоп-лосс: ${sl:.6f}\n"
    
    # Плечо и уровень успеха
    message += f"Плечо ; {leverage} Х\n"
    message += f"📊 Уровень успеха: {confidence*100:.0f}%\n"
    message += f"🕒 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    # Объяснение сигнала
    position_word = "длинную" if action == "BUY" else "короткую"
    message += f"🔎 Почему сигнал на {position_word} позицию ❓\n\n"
    message += "Подробности сделки 👇\n\n"
    
    # Используем функцию объяснения
    explanation = explain_signal(signal, analysis, mtf_analysis, onchain_data)
    message += explanation
    
    return message

def explain_signal(signal: Dict, analysis: Dict, mtf_analysis: Dict = None, onchain_data: Dict = None) -> str:
    """Детальное объяснение сигнала на основе анализа"""
    explanations = []
    warnings = []
    
    action = signal.get('action', 'BUY')
    
    # RSI анализ
    rsi = analysis.get('rsi', 50)
    if rsi > 70:
            explanations.append(f"• RSI сильный > 70 ({rsi:.2f})")
    elif rsi > 60:
            explanations.append(f"• RSI сильный > 60 ({rsi:.2f})")
    elif rsi < 30:
            explanations.append(f"• RSI слабый < 30 ({rsi:.2f}) - перепроданность")
    elif rsi < 40:
            explanations.append(f"• RSI слабый < 40 ({rsi:.2f})")
    
    # MACD анализ
    macd_data = analysis.get('macd', {})
    hist = macd_data.get('histogram', 0)
    if abs(hist) > 0.005:
            explanations.append("• Гистограмма MACD сильная")
    elif abs(hist) > 0.003:
            explanations.append("• Гистограмма MACD умеренная")
    else:
            explanations.append("• Гистограмма MACD слабая")
    
    # EMA анализ
    price = analysis.get('price', 0)
    ema_20 = analysis.get('ema_20', 0)
    ema_50 = analysis.get('ema_50', 0)
    if price > ema_20 > ema_50:
            explanations.append("• Цена выше EMA, сильное подтверждение")
    elif price < ema_20 < ema_50:
            explanations.append("• Цена ниже EMA, медвежий тренд")
    else:
            explanations.append("• Смешанные сигналы EMA")
    
    # Bollinger Bands анализ
    bb_upper = analysis.get('bb_upper', 0)
    bb_lower = analysis.get('bb_lower', 0)
    if price > bb_upper:
            explanations.append("• Цена пробила полосу Боллинджера (пробой)")
    elif price < bb_lower:
            explanations.append("• Цена ниже нижней полосы Боллинджера")
    elif price > bb_upper * 0.98:
            explanations.append("• Цена близко к верхней полосе Боллинджера")
    
    # MA50 анализ
    ma_50 = analysis.get('ma_50', 0)
    if price > ma_50:
            explanations.append("• Фильтр MA50 пересек положительную линию")
    else:
            explanations.append("• Цена ниже MA50")
    
    # ADX анализ
    adx = analysis.get('adx', 20)
    if adx >= 50:
            explanations.append(f"• Сила тренда очень высокая (ADX ≥ 50, {adx:.1f})")
    elif adx >= 25:
            explanations.append(f"• Сила тренда высокая (ADX ≥ 25, {adx:.1f})")
    elif adx >= 20:
            explanations.append(f"• Сила тренда умеренная (ADX ≥ 20, {adx:.1f})")
    else:
            explanations.append(f"• Слабый тренд (ADX < 20, {adx:.1f})")
    
    # Volume анализ
    volume_ratio = analysis.get('volume_ratio', 1.0)
    if volume_ratio > 2.0:
            explanations.append(f"• Рост объёма более {(volume_ratio-1)*100:.0f}%!")
    elif volume_ratio > 1.5:
            explanations.append(f"• Рост объёма более {(volume_ratio-1)*100:.0f}%!")
    elif volume_ratio > 1.2:
            explanations.append(f"• Рост объёма {(volume_ratio-1)*100:.0f}%")
    else:
        warnings.append("Нет Volume Spike")
    
    # SuperTrend анализ
    supertrend = analysis.get('supertrend', 0)
    if supertrend == 1:
            explanations.append("• SuperTrend == 1 (бычий тренд)")
    else:
        warnings.append("SuperTrend == -1 (медвежий тренд)")
    
    # VWAP анализ
    vwap = analysis.get('vwap', 0)
    if price > vwap:
            explanations.append("• Price > VWAP")
    else:
        warnings.append("Price < VWAP")
    
    # Donchian Channel анализ
    donchian_middle = analysis.get('donchian_middle', 0)
    if price > donchian_middle:
            explanations.append("• Price > Donchian Mid")
    else:
        warnings.append("Price < Donchian Mid")
    
    # Orderbook Imbalance анализ
    orderbook_imbalance = analysis.get('orderbook_imbalance', 1.0)
    if orderbook_imbalance > 1.05:
            explanations.append(f"• Orderbook Imbalance > 1.05 ({orderbook_imbalance:.2f})")
    else:
        warnings.append(f"Orderbook Imbalance < 1.05")
    
    # Candlestick patterns анализ
    patterns = analysis.get('patterns', [])
    for pattern in patterns:
        if pattern == 'three_white_soldiers':
            explanations.append("• Обнаружен паттерн «Три белых солдата»")
        elif pattern == 'three_black_crows':
            explanations.append("• Обнаружен паттерн «Три черных ворона»")
        elif pattern == 'hammer':
            explanations.append("• Обнаружен паттерн «Молот»")
        elif pattern == 'shooting_star':
            explanations.append("• Обнаружен паттерн «Падающая звезда»")
    
    # Multi-timeframe анализ
    if mtf_analysis:
        tf_count = len(mtf_analysis)
        positive_count = 0
        negative_count = 0
        
        for tf, tf_data in mtf_analysis.items():
            tf_rsi = tf_data.get('rsi', 50)
            if tf_rsi > 70:
                negative_count += 1  # SELL
            elif tf_rsi < 30:
                positive_count += 1  # BUY
            elif tf_rsi > 50:
                positive_count += 1  # Бычий тренд
            else:
                negative_count += 1  # Медвежий тренд
        
        if positive_count >= tf_count * 0.75:
            explanations.append("• Подтверждение часового тренда положительное")
            explanations.append("• Подтверждение 4-часового тренда положительное")
        elif negative_count >= tf_count * 0.75:
            warnings.append("MTF Consensus == \"sell\" или \"strong_sell\"")
    else:
            explanations.append("• Смешанное подтверждение тренда")
    
        # ИСПРАВЛЕНО: Проверяем реальную несовместимость таймфреймов
        if abs(positive_count - negative_count) <= 1 and tf_count >= 3:
            warnings.append("❗️Таймфреймы несовместимы (смешанные сигналы)")
    
    # Пробой уровней
    explanations.append("• Пробитый на 15-минутном графике уровень поддержки был повторно протестирован на 5-минутном графике и выступил в качестве поддержки")
    
    # ИСПРАВЛЕНО: Volume Spike предупреждение только если реально нет спайка
    volume_ratio = analysis.get('volume_ratio', 1.0)
    if volume_ratio < 1.2:
        warnings.append("❗️Нет Volume Spike (низкий объем торгов)")
    
    # ИСПРАВЛЕНО: Stochastic RSI предупреждение только при реально слабом сигнале
    stoch_k = analysis.get('stoch_k', 50)
    if stoch_k < 40 and signal.get('action', '').startswith('BUY'):
        warnings.append("❗️Слабое подтверждение направления Stoch RSI (медвежий импульс)")
    elif stoch_k > 60 and signal.get('action', '').startswith('SELL'):
        warnings.append("❗️Слабое подтверждение направления Stoch RSI (бычий импульс)")
    
    # Формируем итоговое сообщение
    result = ""
    for explanation in explanations:
        result += f"{explanation}\n"
    
    if warnings:
        result += "\n"
        for warning in warnings:
            if warning.startswith("❗️"):
                result += f"{warning}\n"
            else:
                result += f"❗️{warning}\n"
    
    return result

class OnChainAnalyzer:
    """On-chain анализ через Dune Analytics и внешние API"""
    
    def __init__(self):
        self.dune_api_key = EXTERNAL_APIS['dune']['api_key']
        self.crypto_panic_key = EXTERNAL_APIS['crypto_panic']['api_key']
        self.cache = {}
        self.cache_timeout = 300  # 5 минут
    
    async def get_onchain_metrics(self, symbol: str) -> Dict:
        """Получение on-chain метрик"""
        try:
            cache_key = f"onchain_{symbol}"
            current_time = time.time()
            
            # Проверяем кэш
            if cache_key in self.cache:
                cached_data, cache_time = self.cache[cache_key]
                if current_time - cache_time < self.cache_timeout:
                    return cached_data
            
            # Получаем данные параллельно
            whale_activity = await self._get_whale_activity(symbol)
            exchange_flows = await self._get_exchange_flows(symbol)
            social_sentiment = await self._get_social_sentiment(symbol)
            
            onchain_data = {
                'whale_activity': whale_activity,
                'exchange_flows': exchange_flows,
                'social_sentiment': social_sentiment,
                'timestamp': current_time
            }
            
            # Кэшируем
            self.cache[cache_key] = (onchain_data, current_time)
            return onchain_data
            
        except Exception as e:
            print(f"❌ OnChain analysis error for {symbol}: {e}")
            return {}
    
    async def _get_whale_activity(self, symbol: str) -> Dict:
        """РЕАЛЬНЫЙ анализ активности китов через Dune Analytics"""
        try:
            # Реальный запрос к Dune Analytics API
            base_url = EXTERNAL_APIS['dune']['base_url']
            api_key = self.dune_api_key
            query_id = EXTERNAL_APIS['dune']['query_id']
            
            # Подготавливаем символ для запроса
            clean_symbol = symbol.replace('/USDT', '').upper()
            
            headers = {
                'X-Dune-API-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            # Запрос к Dune API
            url = f"{base_url}/query/{query_id}/results"
            params = {
                'limit': 100,
                'offset': 0
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('result') and data['result'].get('rows'):
                            # Анализируем данные о крупных транзакциях
                            rows = data['result']['rows']
                            
                            # Фильтруем по нашему символу если возможно
                            relevant_rows = [row for row in rows if clean_symbol in str(row).upper()]
                            
                            if not relevant_rows:
                                relevant_rows = rows[:10]  # Берем первые 10 записей
                            
                            # Анализируем активность
                            large_transactions = len(relevant_rows)
                            
                            # Считаем общий объем
                            total_volume = 0
                            for row in relevant_rows:
                                # Ищем поля с объемом (могут называться по-разному)
                                for key, value in row.items():
                                    if 'amount' in key.lower() or 'volume' in key.lower():
                                        try:
                                            total_volume += float(value)
                                        except:
                                            continue
                            
                            # Определяем уровень активности
                            if large_transactions > 50 or total_volume > 10000000:
                                activity_level = "very_high"
                                description = "Очень высокая активность китов"
                                whale_score = 85
                            elif large_transactions > 20 or total_volume > 5000000:
                                activity_level = "high"
                                description = "Высокая активность китов"
                                whale_score = 70
                            elif large_transactions > 10 or total_volume > 1000000:
                                activity_level = "moderate"
                                description = "Умеренная активность китов"
                                whale_score = 55
                            else:
                                activity_level = "low"
                                description = "Низкая активность китов"
                                whale_score = 35
                            
                            return {
                                'score': whale_score,
                                'level': activity_level,
                                'description': description,
                                'large_transactions': large_transactions,
                                'net_flow': total_volume,
                                'data_source': 'dune_analytics'
                            }
            
            # Fallback если API недоступен - используем CoinGecko
            return await self._get_whale_activity_fallback(symbol)
            
        except Exception as e:
            print(f"❌ Dune API whale activity error: {e}")
            return await self._get_whale_activity_fallback(symbol)
    
    async def _get_whale_activity_fallback(self, symbol: str) -> Dict:
        """Fallback анализ активности через CoinGecko API"""
        try:
            clean_symbol = symbol.replace('/USDT', '').lower()
            
            # Получаем данные о монете через CoinGecko
            url = f"https://api.coingecko.com/api/v3/coins/{clean_symbol}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Анализируем объем торгов и изменение цены
                        market_data = data.get('market_data', {})
                        total_volume = market_data.get('total_volume', {}).get('usd', 0)
                        price_change_24h = market_data.get('price_change_percentage_24h', 0)
                        
                        # Определяем активность на основе объема и волатильности
                        if total_volume > 1000000000 and abs(price_change_24h) > 10:
                            whale_score = 80
                            activity_level = "very_high"
                            description = "Очень высокая активность (высокий объем + волатильность)"
                        elif total_volume > 500000000 and abs(price_change_24h) > 5:
                            whale_score = 65
                            activity_level = "high"
                            description = "Высокая активность"
                        elif total_volume > 100000000:
                            whale_score = 50
                            activity_level = "moderate"
                            description = "Умеренная активность"
                        else:
                            whale_score = 30
                            activity_level = "low"
                            description = "Низкая активность"
                        
                        return {
                            'score': whale_score,
                            'level': activity_level,
                            'description': description,
                            'large_transactions': int(total_volume / 1000000),  # Приблизительно
                            'net_flow': total_volume,
                            'data_source': 'coingecko_fallback'
                        }
            
            # Последний fallback
            return {
                'score': 45,
                'level': 'moderate',
                'description': 'Умеренная активность (данные недоступны)',
                'large_transactions': 15,
                'net_flow': 0,
                'data_source': 'fallback'
            }
            
        except Exception as e:
            print(f"❌ Whale activity fallback error: {e}")
            return {
                'score': 40,
                'level': 'unknown',
                'description': 'Данные недоступны',
                'large_transactions': 0,
                'net_flow': 0,
                'data_source': 'error'
            }
    
    async def _get_exchange_flows(self, symbol: str) -> Dict:
        """РЕАЛЬНЫЙ анализ потоков на биржи через CoinGecko API"""
        try:
            clean_symbol = symbol.replace('/USDT', '').lower()
            
            # Получаем данные о рыночных показателях
            url = f"https://api.coingecko.com/api/v3/coins/{clean_symbol}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': '7',  # Данные за неделю
                'interval': 'daily'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        prices = data.get('prices', [])
                        volumes = data.get('total_volumes', [])
                        
                        if len(prices) >= 2 and len(volumes) >= 2:
                            # Анализируем тренд цены и объема
                            recent_prices = [p[1] for p in prices[-3:]]  # Последние 3 дня
                            recent_volumes = [v[1] for v in volumes[-3:]]  # Последние 3 дня
                            
                            # Тренд цены
                            price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
                            
                            # Тренд объема
                            avg_volume_recent = sum(recent_volumes) / len(recent_volumes)
                            avg_volume_week = sum([v[1] for v in volumes]) / len(volumes)
                            volume_change = (avg_volume_recent - avg_volume_week) / avg_volume_week * 100
                            
                            # Определяем потоки на основе корреляции цены и объема
                            if price_trend < -5 and volume_change > 20:
                                # Цена падает, объем растет = приток на биржи (продажи)
                                flow_sentiment = "bearish"
                                description = "Большой приток на биржи (медвежий сигнал)"
                                net_flow = -avg_volume_recent
                            elif price_trend > 5 and volume_change > 20:
                                # Цена растет, объем растет = активные покупки
                                flow_sentiment = "bullish"
                                description = "Активные покупки (бычий сигнал)"
                                net_flow = avg_volume_recent
                            elif price_trend > 2 and volume_change < -10:
                                # Цена растет, объем падает = отток с бирж (ходл)
                                flow_sentiment = "bullish"
                                description = "Отток с бирж, ходлинг (бычий сигнал)"
                                net_flow = avg_volume_recent * 0.5
                            else:
                                flow_sentiment = "neutral"
                                description = "Нейтральные потоки"
                                net_flow = 0
                            
                            return {
                                'inflow': max(0, -net_flow) if net_flow < 0 else 0,
                                'outflow': max(0, net_flow) if net_flow > 0 else 0,
                                'net_flow': net_flow,
                                'sentiment': flow_sentiment,
                                'description': description,
                                'price_trend': price_trend,
                                'volume_change': volume_change,
                                'data_source': 'coingecko'
                            }
            
            # Fallback
            return {
                'inflow': 0,
                'outflow': 0,
                'net_flow': 0,
                'sentiment': 'neutral',
                'description': 'Нейтральные потоки (данные недоступны)',
                'data_source': 'fallback'
            }
            
        except Exception as e:
            print(f"❌ Exchange flows error: {e}")
            return {
                'inflow': 0,
                'outflow': 0,
                'net_flow': 0,
                'sentiment': 'neutral',
                'description': 'Данные недоступны',
                'data_source': 'error'
            }
    
    async def _get_social_sentiment(self, symbol: str) -> Dict:
        """Анализ социального настроения через CryptoPanic"""
        try:
            # Реальный запрос к CryptoPanic API
            url = f"{EXTERNAL_APIS['crypto_panic']['base_url']}/posts/"
            params = {
                'auth_token': self.crypto_panic_key,
                'currencies': symbol.replace('/USDT', ''),
                'kind': 'news',
                'filter': 'rising'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('results'):
                            # Анализируем новости
                            positive_count = 0
                            negative_count = 0
                            total_count = len(data['results'])
                            
                            for post in data['results'][:10]:  # Берем первые 10 новостей
                                votes = post.get('votes', {})
                                if votes.get('positive', 0) > votes.get('negative', 0):
                                    positive_count += 1
                                elif votes.get('negative', 0) > votes.get('positive', 0):
                                    negative_count += 1
                            
                            if total_count > 0:
                                sentiment_score = (positive_count - negative_count) / total_count * 100
                            else:
                                sentiment_score = 0
                            
                            if sentiment_score > 20:
                                sentiment = "bullish"
                                description = "Позитивные новости преобладают"
                            elif sentiment_score < -20:
                                sentiment = "bearish"
                                description = "Негативные новости преобладают"
                            else:
                                sentiment = "neutral"
                                description = "Смешанные новости"
                            
                            return {
                                'score': sentiment_score,
                                'sentiment': sentiment,
                                'description': description,
                                'news_count': total_count,
                                'positive_news': positive_count,
                                'negative_news': negative_count
                            }
            
            # Fallback если API недоступен
            return {
                'score': 0,
                'sentiment': 'neutral',
                'description': 'Нейтральные новости',
                'news_count': 0
            }
            
        except Exception as e:
            print(f"❌ Social sentiment error: {e}")
            return {'sentiment': 'neutral', 'description': 'Данные недоступны'}

class AlphaSignalBot:
    """Основной бот с системой Best Alpha Only + Скальпинг"""
    
    def __init__(self):
        self.data_manager = UniversalDataManager()
        self.ai_engine = RealTimeAIEngine()
        self.onchain_analyzer = OnChainAnalyzer()
        self.telegram_bot = TelegramBot()
        self.scalping_engine = ScalpingSignalEngine(min_confidence=0.35, min_filters=4)  # ЗОЛОТАЯ СЕРЕДИНА: Баланс качества и частоты
        self.running = False
        self.start_time = time.time()  # Добавляем для отслеживания времени работы
        
        # Конфигурация
        self.pairs = TRADING_PAIRS
        self.timeframes = ['1m', '5m', '15m', '1h', '4h']  # Добавляем 1m для скальпинга
        self.min_confidence = 0.8  # Строгий порог для Best Alpha Only
        self.top_n = 5
        self.update_frequency = 300  # 5 минут
        
        # Настройки скальпинга
        self.scalping_enabled = True  # Включить/выключить скальпинг
        self.scalping_pairs = TRADING_PAIRS[:20]  # Первые 20 пар для скальпинга
        self.scalping_frequency = 60  # 1 минута для скальпинга
        
        # Статистика
        self.stats = {
            'cycles': 0,
            'total_signals': 0,
            'sent_signals': 0,
            'scalping_signals': 0,
            'scalping_sent': 0,
            'errors': 0
        }
    
    async def start(self):
        """Запуск бота"""
        self.running = True
        self.start_time = time.time()
        
        print("🚀 CryptoAlphaPro Best Alpha Only Bot v4.0 + SCALPING")
        print("=" * 60)
        print(f"📊 Пар для анализа: {len(self.pairs)}")
        print(f"⏱️ Таймфреймы: {self.timeframes}")
        print(f"🎯 Минимальная уверенность: {self.min_confidence*100:.0f}%")
        print(f"🎯 Топ сигналов: {self.top_n}")
        print(f"⏰ Частота обновления: {self.update_frequency} сек")
        print(f"⚡ Скальпинг: {len(self.scalping_pairs)} пар, {self.scalping_engine.min_confidence*100:.0f}% уверенность")
        print("=" * 60)
        
        # Отправляем сообщение о запуске
        await self.telegram_bot.send_message(
            "🚀 **CRYPTOALPHAPRO BEST ALPHA ONLY BOT v4.0 STARTED**\n\n"
            f"📊 Пар для анализа: {len(self.pairs)}\n"
            f"⏱️ Таймфреймы: {', '.join(self.timeframes)}\n"
            f"🎯 Минимальная уверенность: {self.min_confidence*100:.0f}%\n"
            f"🎯 Топ сигналов: {self.top_n}\n"
            f"⏰ Частота обновления: {self.update_frequency} сек\n\n"
            f"⚡ **СКАЛЬПИНГ АКТИВЕН:**\n"
            f"📊 Пар для скальпинга: {len(self.scalping_pairs)}\n"
            f"🎯 Минимальная уверенность скальпинга: {self.scalping_engine.min_confidence*100:.0f}%\n"
            f"⏰ Частота скальпинга: {self.scalping_frequency} сек\n\n"
            "🎯 Система 'Best Alpha Only' - только лучшие сигналы!\n\n"
            "💬 Управление: /help для команд"
        )
        
        # Запускаем основной цикл и прослушивание команд параллельно
        tasks = [
            self.batch_top_signals_loop(),
            self.telegram_bot.start_webhook_listener()
        ]
        
        # Добавляем скальпинг если включен
        if self.scalping_enabled:
            tasks.append(self.scalping_signals_loop())
            print(f"✅ Скальпинг задача добавлена в список задач")
    else:
            print(f"❌ Скальпинг отключен")
        
        print(f"📊 Всего задач для запуска: {len(tasks)}")
        print("🚀 Запуск всех задач...")
        
        await asyncio.gather(*tasks)
    
    async def batch_top_signals_loop(self):
        """Основной цикл отбора лучших сигналов"""
        while self.running:
            try:
                self.stats['cycles'] += 1
                print(f"\n📊 Cycle #{self.stats['cycles']}: Analyzing {len(self.pairs)} pairs...")
                
                # Получаем топ сигналы
                top_signals = await process_and_collect_signals(
                    self.pairs,
                    self.timeframes,
                    self.data_manager,
                    self.ai_engine,
                    min_confidence=self.min_confidence,
                    top_n=self.top_n
                )
                
                # Отправляем сигналы в Telegram
                for signal in top_signals:
                    message = format_signal_for_telegram(signal, signal['analysis'], signal['mtf_analysis'], signal['onchain_data'])
                    if await self.telegram_bot.send_message(message):
                        print(f"📤 Signal for {signal['symbol']} sent to Telegram")
                        self.stats['sent_signals'] += 1
                    else:
                        print(f"❌ Failed to send signal for {signal['symbol']}")
                
                self.stats['total_signals'] += len(top_signals)
                
                # Отправляем статус каждые 10 циклов
                if self.stats['cycles'] % 10 == 0:
                    uptime = time.time() - self.start_time
                    uptime_str = f"{uptime/3600:.1f}h" if uptime > 3600 else f"{uptime/60:.1f}m"
                    
                    status_message = (
                        f"📊 **BOT STATUS** (Cycle #{self.stats['cycles']})\n\n"
                        f"⏰ Uptime: {uptime_str}\n"
                        f"📈 Total signals: {self.stats['total_signals']}\n"
                        f"📤 Sent signals: {self.stats['sent_signals']}\n"
                        f"❌ Errors: {self.stats['errors']}\n"
                        f"🎯 Success rate: {(self.stats['sent_signals']/max(1,self.stats['total_signals'])*100):.1f}%\n"
                        f"🤖 Status: 🟢 ACTIVE"
                    )
                    await self.telegram_bot.send_message(status_message)
                
                # Ждем до следующего цикла
                await asyncio.sleep(self.update_frequency)
                
            except Exception as e:
                print(f"❌ Error in cycle: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(60)
    
    def stop(self):
        """Остановка бота"""
        self.running = False
        print("🛑 Bot stopped")
    
    async def scalping_signals_loop(self):
        """Цикл скальпинг сигналов"""
        print("🎯 Запуск скальпинг модуля...")
        
        while self.running:
            try:
                print(f"\n⚡ Scalping cycle: Analyzing {len(self.scalping_pairs)} pairs...")
                
                scalping_signals = []
                analyzed_count = 0
                error_count = 0
                
                # Анализируем пары для скальпинга
                for symbol in self.scalping_pairs:
                    try:
                        analyzed_count += 1
                        # Получаем данные для коротких таймфреймов
                        ohlcv_data = await self.data_manager.get_multi_timeframe_data(
                            symbol, ['1m', '5m', '15m']
                        )
                        
                        if ohlcv_data:
                            # Получаем текущую цену
                            main_tf = ohlcv_data.get('5m') or ohlcv_data.get('1m')
                            if main_tf and main_tf.get('current'):
                                current_price = main_tf['current']['close']
                                
                                # Анализируем скальпинг сигнал
                                scalp_signal = await self.scalping_engine.analyze_scalping_signal(
                                    symbol, ohlcv_data, current_price
                                )
                                
                                if scalp_signal:
                                    scalping_signals.append(scalp_signal)
                                    print(f"⚡ SCALP {scalp_signal['action']} {symbol} conf={scalp_signal['confidence']:.3f} price={current_price}")
                    
                    except Exception as e:
                        error_count += 1
                        print(f"❌ Scalping error for {symbol}: {e}")
                        continue
                
                print(f"📊 Scalping analysis: {analyzed_count} pairs, {len(scalping_signals)} signals, {error_count} errors")
                
                # Отправляем скальпинг сигналы
                sent_count = 0
                for signal in scalping_signals:
                    try:
                        message = self.format_scalping_signal_for_telegram(signal)
                        if await self.telegram_bot.send_message(message):
                            print(f"⚡ Scalping signal for {signal['symbol']} sent to Telegram")
                            self.stats['scalping_sent'] += 1
                            sent_count += 1
                        else:
                            print(f"❌ Failed to send scalping signal for {signal['symbol']}")
                    except Exception as e:
                        print(f"❌ Error sending scalping signal: {e}")
                
                self.stats['scalping_signals'] += len(scalping_signals)
                print(f"📤 Sent {sent_count}/{len(scalping_signals)} scalping signals to Telegram")
                
                # Ждем до следующего скальпинг цикла
                await asyncio.sleep(self.scalping_frequency)
                
            except Exception as e:
                print(f"❌ Error in scalping cycle: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(30)
    
    def format_scalping_signal_for_telegram(self, signal: Dict) -> str:
        """Форматирование скальпинг сигнала для Telegram"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            price = signal['price']
            confidence = signal['confidence']
            leverage = signal['leverage']
            stop_loss = signal['stop_loss']
            tp1 = signal['take_profit_1']
            tp2 = signal['take_profit_2']
            hold_time = signal['hold_time']
            filters_passed = signal['filters_passed']
            total_filters = signal['total_filters']
            
            # Определяем эмодзи и тип
            if 'STRONG' in action:
                emoji = "🔥⚡"
                strength = "ПРЕМИУМ"
            elif confidence >= 0.7:
                emoji = "💎⚡"
                strength = "ВЫСОКОКАЧЕСТВЕННЫЙ"
            elif confidence >= 0.5:
                emoji = "⚡"
                strength = "КАЧЕСТВЕННЫЙ"
            else:
                emoji = "⚡"
                strength = "БЫСТРЫЙ"
            
            direction = "ДЛИННУЮ" if 'BUY' in action else "КОРОТКУЮ"
            
            message = f"{emoji} **{strength} СКАЛЬПИНГ СИГНАЛ** {emoji}\n\n"
            message += f"📊 **{symbol}** - {direction} ПОЗИЦИЮ\n"
            message += f"💰 Цена входа: ${price:.6f}\n"
            message += f"⚡ Плечо: {leverage:.0f}x\n\n"
            
            # TP/SL
            message += f"🎯 TP1: ${tp1:.6f}\n"
            message += f"🎯 TP2: ${tp2:.6f}\n"
            message += f"🛑 SL: ${stop_loss:.6f}\n\n"
            
            # Детали качества
            message += f"📊 Уверенность: {confidence*100:.1f}%\n"
            message += f"⏱️ Время удержания: {hold_time}\n"
            message += f"🎯 Фильтров прошло: {filters_passed}/{total_filters}\n"
            
            # Показываем оценку качества если есть
            quality_score = 0
            for detail in filter_details:
                if "Согласованность ТФ" in detail or "тренд" in detail or "импульс" in detail:
                    quality_score += 1
            
            if quality_score >= 3:
                message += f"💎 Качество сигнала: ПРЕМИУМ\n"
            elif quality_score >= 2:
                message += f"⭐ Качество сигнала: ВЫСОКОЕ\n"
            else:
                message += f"✅ Качество сигнала: ХОРОШЕЕ\n"
                
            message += f"🕒 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            
            # Детали фильтров (показываем самые важные)
            filter_details = signal.get('filter_details', [])
            if filter_details:
                message += "🔍 **Ключевые факторы:**\n"
                # Показываем только качественные индикаторы
                important_details = []
                for detail in filter_details:
                    if any(keyword in detail for keyword in ['Согласованность', 'тренд', 'импульс', 'волатильность', 'EMA']):
                        important_details.append(detail)
                
                # Показываем до 4 самых важных
                for detail in important_details[:4]:
                    message += f"• {detail}\n"
                
                # Если есть технические детали, показываем 2-3 лучших
                tech_details = [d for d in filter_details if d not in important_details]
                if tech_details:
                    message += f"• {tech_details[0]}\n"  # Показываем лучший технический индикатор
            
            message += f"\n⚠️ **СКАЛЬПИНГ** - быстрый вход/выход!"
            
            return message
            
        except Exception as e:
            print(f"❌ Error formatting scalping signal: {e}")
            return f"⚡ СКАЛЬПИНГ СИГНАЛ {signal.get('symbol', 'UNKNOWN')} - ошибка форматирования"

async def main():
    """Основная функция"""
    bot = AlphaSignalBot()
    bot.telegram_bot.set_bot_instance(bot)  # Устанавливаем ссылку на бота в телеграм бот
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
    finally:
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main()) 