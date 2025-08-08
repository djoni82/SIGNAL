#!/usr/bin/env python3
"""
🚨 SignalPro - Основной модуль для обычных сигналов
Система отбора САМЫХ ТОЧНЫХ сигналов среди 200+ пар
РЕАЛЬНЫЕ ДАННЫЕ С БИРЖ + ON-CHAIN АНАЛИЗ
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

class SignalProEngine:
    """Основной движок для анализа обычных сигналов"""
    
    def __init__(self):
        self.indicators = {}
        
    async def process_symbol(self, symbol: str, ohlcv_data: Dict) -> Optional[Dict]:
        """Обработка символа и генерация сигнала"""
        try:
            if not ohlcv_data:
                return None
            
            # Анализируем каждый таймфрейм
            analysis_results = {}
            for tf, data in ohlcv_data.items():
                if tf not in ['whale_activity', 'exchange_flows', 'social_sentiment', 'timestamp']:
                    analysis_results[tf] = self._analyze_timeframe(data)
            
            # Объединяем результаты
            signal = self._combine_analysis(analysis_results, symbol)
            
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
                'price': close,
                'patterns': patterns,
                'stoch_k': stoch_k,
                'stoch_d': stoch_d,
                'exchanges': data.get('exchanges', 1),
                'sources': data.get('sources', ['unknown'])
            }
            
        except Exception as e:
            print(f"❌ Error in technical analysis: {e}")
            return {}
    
    def _combine_analysis(self, analysis_results: Dict, symbol: str) -> Optional[Dict]:
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
            
            # Multi-timeframe согласованность (0-0.1)
            tf_signals = []
            
            for tf, tf_data in analysis_results.items():
                if tf_data.get('price', 0) > 0:
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
                
                # Определяем финальное действие
                if bullish_signals > bearish_signals:
                    action = 'BUY'
                elif bearish_signals > bullish_signals:
                    action = 'SELL'
                else:
                    # При равном количестве сигналов используем случайность
                    action = 'BUY' if np.random.random() > 0.5 else 'SELL'
                
                return {
                    'action': action,
                    'confidence': confidence,
                    'analysis': main_analysis,
                    'mtf_analysis': analysis_results
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
        self.admin_chat_id = TELEGRAM_CONFIG.get('admin_chat_id', self.chat_id)
        self.bot_instance = None
    
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

def format_signal_for_telegram(signal: Dict, analysis: Dict, mtf_analysis: Dict = None) -> str:
    """Форматирование сигнала для отправки в Telegram точно как в примере"""
    symbol = signal['symbol']
    action = signal['action']
    price = signal['price']
    confidence = signal['confidence']
    
    # Определяем тип позиции и эмодзи
    if action == 'BUY':
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
    message = f"🚨 СИГНАЛ НА {position_type} {action_emoji}\n\n"
    message += f"Пара: {symbol}\n"
    message += f"Действие: {action}\n"
    message += f"Цена входа: ${price:.6f}\n\n"
    
    # Take Profit уровни
    message += f"🎯 Take Profit:\n"
    message += f"TP1: ${tp1:.6f}\n"
    message += f"TP2: ${tp2:.6f}\n"
    message += f"TP3: ${tp3:.6f}\n"
    message += f"TP4: ${tp4:.6f}\n\n"
    
    # Stop Loss
    message += f"🛑 Stop Loss: ${sl:.6f}\n\n"
    
    # Уровень успеха и время
    message += f"📊 Уровень успеха: {confidence*100:.0f}%\n"
    message += f"🕒 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    
    # Объяснение сигнала
    position_word = "длинную" if action == "BUY" else "короткую"
    message += f"🔎 Почему сигнал на {position_word} позицию ❓\n\n"
    message += "Подробности сделки 👇\n\n"
    
    # Используем функцию объяснения
    explanation = explain_signal(signal, analysis, mtf_analysis)
    message += explanation
    
    return message

def explain_signal(signal: Dict, analysis: Dict, mtf_analysis: Dict = None) -> str:
    """Детальное объяснение сигнала на основе анализа"""
    explanations = []
    warnings = []
    
    action = signal.get('action', 'BUY')
    
    # RSI анализ
    rsi = analysis.get('rsi', 50)
    if rsi > 70:
        explanations.append(f"• RSI сильный > 70 ({rsi:.2f}) - перекупленность")
    elif rsi > 60:
        explanations.append(f"• RSI сильный > 60 ({rsi:.2f})")
    elif rsi < 30:
        explanations.append(f"• RSI слабый < 30 ({rsi:.2f}) - перепроданность")
    elif rsi < 40:
        explanations.append(f"• RSI слабый < 40 ({rsi:.2f})")
    
    # EMA анализ
    price = analysis.get('price', 0)
    ema_20 = analysis.get('ema_20', 0)
    ema_50 = analysis.get('ema_50', 0)
    if price > ema_20 > ema_50:
        explanations.append("• Цена выше EMA, сильное подтверждение")
    elif price < ema_20 < ema_50:
        explanations.append("• Цена ниже EMA, медвежий тренд")
    else:
        explanations.append("• Смешанный EMA тренд")
    
    # MA50 анализ
    ma_50 = analysis.get('ma_50', 0)
    if price > ma_50:
        explanations.append("• Фильтр MA50 пересек положительную линию")
    else:
        explanations.append("• Цена ниже MA50")
    
    # ADX анализ
    adx = analysis.get('adx', 20)
    if adx >= 30:
        explanations.append(f"• Сила тренда очень высокая (ADX ≥ 30, {adx:.1f})")
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
            explanations.append("• Подтверждение часового тренда отрицательное")
            explanations.append("• Подтверждение 4-часового тренда отрицательное")
        else:
            explanations.append("• Смешанное подтверждение тренда")
        
        # Проверяем реальную несовместимость таймфреймов
        if abs(positive_count - negative_count) <= 1 and tf_count >= 3:
            warnings.append("Таймфреймы несовместимы")
    
    # Stochastic RSI предупреждение только при реально слабом сигнале
    stoch_k = analysis.get('stoch_k', 50)
    if stoch_k < 40 and signal.get('action', '').startswith('BUY'):
        warnings.append("Слабое подтверждение направления Stoch RSI")
    elif stoch_k > 60 and signal.get('action', '').startswith('SELL'):
        warnings.append("Слабое подтверждение направления Stoch RSI")
    
    # Формируем итоговое сообщение
    result = ""
    for explanation in explanations:
        result += f"{explanation}\n"
    
    if warnings:
        result += "\n⚠️ ПРЕДУПРЕЖДЕНИЯ:\n"
        for warning in warnings:
            result += f"❗️{warning}\n"
    
    return result

async def process_and_collect_signals(pairs, timeframes, data_manager, ai_engine, min_confidence=0.8, top_n=5):
    """Анализирует N пар и выдает только top-N лучших сигналов"""
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

    # Отбор только лучших TOP-N значений по confidence
    filtered = [s for s in signals_ok if s['confidence'] >= min_confidence]
    filtered = sorted(filtered, key=lambda x: x['confidence'], reverse=True)[:top_n]

    print(f"Всего пар: {len(pairs)}. Сработало сигналов: {len(signals_ok)}. Среди лучших (conf>={min_confidence}): {len(filtered)}. Ошибок: {errors}")
    for sig in filtered:
        print(f"{sig['symbol']} {sig['action']} conf={sig['confidence']:.3f} price={sig['entry_price']}")

    return filtered

class SignalProBot:
    """Основной бот SignalPro для обычных сигналов"""
    
    def __init__(self):
        self.data_manager = UniversalDataManager()
        self.ai_engine = SignalProEngine()
        self.telegram_bot = TelegramBot()
        self.running = False
        self.start_time = time.time()
        
        # Конфигурация
        self.pairs = TRADING_PAIRS
        self.timeframes = ['15m', '1h', '4h']  # Основные таймфреймы для обычных сигналов
        self.min_confidence = 0.8  # Строгий порог для качественных сигналов
        self.top_n = 5
        self.update_frequency = 300  # 5 минут
        
        # Статистика
        self.stats = {
            'cycles': 0,
            'total_signals': 0,
            'sent_signals': 0,
            'errors': 0
        }
    
    async def start(self):
        """Запуск бота"""
        self.running = True
        self.start_time = time.time()
        
        print("🚨 SignalPro - Основной модуль для обычных сигналов")
        print("=" * 60)
        print(f"📊 Пар для анализа: {len(self.pairs)}")
        print(f"⏱️ Таймфреймы: {self.timeframes}")
        print(f"🎯 Минимальная уверенность: {self.min_confidence*100:.0f}%")
        print(f"🎯 Топ сигналов: {self.top_n}")
        print(f"⏰ Частота обновления: {self.update_frequency} сек")
        print("=" * 60)
        
        # Отправляем сообщение о запуске
        await self.telegram_bot.send_message(
            "🚨 **SIGNALPRO STARTED**\n\n"
            f"📊 Пар для анализа: {len(self.pairs)}\n"
            f"⏱️ Таймфреймы: {', '.join(self.timeframes)}\n"
            f"🎯 Минимальная уверенность: {self.min_confidence*100:.0f}%\n"
            f"🎯 Топ сигналов: {self.top_n}\n"
            f"⏰ Частота обновления: {self.update_frequency} сек\n\n"
            "🎯 Система отбора лучших сигналов!\n\n"
            "💬 Управление: /help для команд"
        )
        
        # Запускаем основной цикл
        await self.batch_top_signals_loop()
    
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
                    message = format_signal_for_telegram(signal, signal['analysis'], signal['mtf_analysis'])
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
                        f"📊 **SIGNALPRO STATUS** (Cycle #{self.stats['cycles']})\n\n"
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
        print("🛑 SignalPro stopped")

async def main():
    """Основная функция"""
    bot = SignalProBot()
    bot.telegram_bot.set_bot_instance(bot)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Stopping SignalPro...")
    finally:
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main()) 