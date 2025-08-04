#!/usr/bin/env python3
"""
🚀 SCALPING SIGNAL ENGINE v1.0
Скальпинг модуль для коротких таймфреймов с жесткими фильтрами
"""

import asyncio
import time
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import ccxt

class ScalpingSignalEngine:
    """Движок для скальпинг сигналов на коротких таймфреймах"""
    
    def __init__(self, min_confidence=0.95, min_filters=8):
        self.min_confidence = min_confidence
        self.min_filters = min_filters  # Требуем совпадение минимум 8 из 10 фильтров
        self.scalping_timeframes = ['1m', '3m', '5m', '15m']
        
        print(f"🎯 Scalping Engine initialized: min_confidence={min_confidence*100:.0f}%, min_filters={min_filters}")
    
    async def analyze_scalping_signal(self, symbol: str, ohlcv_data: Dict, current_price: float) -> Optional[Dict]:
        """
        Анализ скальпингового сигнала по коротким таймфреймам
        Требует совпадения ВСЕХ ключевых фильтров для максимальной точности
        """
        try:
            # Проверяем наличие данных для коротких таймфреймов
            required_tfs = ['1m', '5m', '15m']  # Минимально необходимые ТФ
            available_tfs = []
            
            for tf in required_tfs:
                if tf in ohlcv_data and ohlcv_data[tf] and ohlcv_data[tf].get('historical_data'):
                    if len(ohlcv_data[tf]['historical_data']) >= 30:  # Минимум 30 свечей
                        available_tfs.append(tf)
            
            if len(available_tfs) < 2:  # Нужно минимум 2 таймфрейма
                return None
            
            # Анализируем каждый таймфрейм
            tf_analysis = {}
            for tf in available_tfs:
                analysis = self._analyze_scalping_timeframe(ohlcv_data[tf], tf)
                if analysis:
                    tf_analysis[tf] = analysis
            
            if len(tf_analysis) < 2:
                return None
            
            # Проверяем фильтры и рассчитываем уверенность
            signal = self._evaluate_scalping_filters(tf_analysis, symbol, current_price)
            
            return signal
            
        except Exception as e:
            print(f"❌ Scalping analysis error for {symbol}: {e}")
            return None
    
    def _analyze_scalping_timeframe(self, data: Dict, timeframe: str) -> Dict:
        """Анализ одного таймфрейма для скальпинга"""
        try:
            historical_data = data.get('historical_data', [])
            current_data = data.get('current', {})
            
            if len(historical_data) < 30:
                return {}
            
            # Создаем DataFrame
            df = pd.DataFrame(historical_data)
            
            # Текущие значения
            close = current_data.get('close', 0)
            high = current_data.get('high', 0)
            low = current_data.get('low', 0)
            volume = current_data.get('volume', 0)
            
            # Массивы для расчетов
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            volumes = df['volume'].values
            
            # БЫСТРЫЕ индикаторы для скальпинга
            
            # 1. Быстрый RSI (7 периодов)
            rsi_fast = self._calculate_fast_rsi(closes, period=7)
            
            # 2. Быстрый MACD (5,13,4)
            macd_fast = self._calculate_fast_macd(closes)
            
            # 3. Быстрые EMA (8, 21)
            ema_8 = self._calculate_ema(closes, 8)
            ema_21 = self._calculate_ema(closes, 21)
            
            # 4. Быстрый Stochastic (5,3,3)
            stoch_fast = self._calculate_fast_stochastic(highs, lows, closes)
            
            # 5. Быстрый ADX (7 периодов)
            adx_fast = self._calculate_fast_adx(highs, lows, closes)
            
            # 6. Volume momentum (5 периодов)
            volume_momentum = self._calculate_volume_momentum(volumes)
            
            # 7. Price momentum
            price_momentum = self._calculate_price_momentum(closes)
            
            # 8. Быстрый ATR для волатильности
            atr_fast = self._calculate_fast_atr(highs, lows, closes)
            
            # 9. Bollinger Bands squeeze
            bb_squeeze = self._calculate_bb_squeeze(closes)
            
            # 10. Support/Resistance break
            sr_break = self._calculate_sr_break(highs, lows, closes)
            
            return {
                'timeframe': timeframe,
                'price': close,
                'rsi_fast': rsi_fast,
                'macd_fast': macd_fast,
                'ema_8': ema_8,
                'ema_21': ema_21,
                'ema_cross': 1 if ema_8 > ema_21 else -1,
                'stoch_fast': stoch_fast,
                'adx_fast': adx_fast,
                'volume_momentum': volume_momentum,
                'price_momentum': price_momentum,
                'atr_fast': atr_fast,
                'bb_squeeze': bb_squeeze,
                'sr_break': sr_break,
                'volatility': atr_fast / close if close > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Scalping TF analysis error: {e}")
            return {}
    
    def _evaluate_scalping_filters(self, tf_analysis: Dict, symbol: str, current_price: float) -> Optional[Dict]:
        """Оценка фильтров для скальпинг сигнала"""
        try:
            # Счетчики фильтров
            bullish_filters = 0
            bearish_filters = 0
            total_filters = 0
            
            filter_details = []
            
            # Анализируем каждый таймфрейм
            for tf, analysis in tf_analysis.items():
                if not analysis:
                    continue
                
                # 1. RSI фильтр
                rsi = analysis.get('rsi_fast', 50)
                if rsi > 65:
                    bearish_filters += 1
                    filter_details.append(f"{tf} RSI={rsi:.1f} (SELL)")
                elif rsi < 35:
                    bullish_filters += 1
                    filter_details.append(f"{tf} RSI={rsi:.1f} (BUY)")
                total_filters += 1
                
                # 2. MACD фильтр
                macd = analysis.get('macd_fast', {})
                if macd.get('histogram', 0) > 0:
                    bullish_filters += 1
                    filter_details.append(f"{tf} MACD+ (BUY)")
                else:
                    bearish_filters += 1
                    filter_details.append(f"{tf} MACD- (SELL)")
                total_filters += 1
                
                # 3. EMA Cross фильтр
                ema_cross = analysis.get('ema_cross', 0)
                if ema_cross > 0:
                    bullish_filters += 1
                    filter_details.append(f"{tf} EMA8>21 (BUY)")
                else:
                    bearish_filters += 1
                    filter_details.append(f"{tf} EMA8<21 (SELL)")
                total_filters += 1
                
                # 4. Stochastic фильтр
                stoch = analysis.get('stoch_fast', {})
                stoch_k = stoch.get('k', 50)
                if stoch_k > 70:
                    bearish_filters += 1
                    filter_details.append(f"{tf} Stoch={stoch_k:.1f} (SELL)")
                elif stoch_k < 30:
                    bullish_filters += 1
                    filter_details.append(f"{tf} Stoch={stoch_k:.1f} (BUY)")
                total_filters += 1
                
                # 5. ADX фильтр (сила тренда)
                adx = analysis.get('adx_fast', 15)
                if adx >= 25:
                    # ADX показывает силу тренда, направление определяется другими индикаторами
                    if ema_cross > 0:
                        bullish_filters += 0.5
                    else:
                        bearish_filters += 0.5
                    filter_details.append(f"{tf} ADX={adx:.1f} (STRONG)")
                total_filters += 1
                
                # 6. Volume Momentum фильтр
                vol_momentum = analysis.get('volume_momentum', 0)
                if vol_momentum > 20:
                    bullish_filters += 1
                    filter_details.append(f"{tf} Vol+{vol_momentum:.1f}% (BUY)")
                elif vol_momentum < -20:
                    bearish_filters += 1
                    filter_details.append(f"{tf} Vol{vol_momentum:.1f}% (SELL)")
                total_filters += 1
                
                # 7. Price Momentum фильтр
                price_momentum = analysis.get('price_momentum', 0)
                if price_momentum > 0.5:
                    bullish_filters += 1
                    filter_details.append(f"{tf} Price+{price_momentum:.1f}% (BUY)")
                elif price_momentum < -0.5:
                    bearish_filters += 1
                    filter_details.append(f"{tf} Price{price_momentum:.1f}% (SELL)")
                total_filters += 1
                
                # 8. BB Squeeze фильтр (готовность к движению)
                bb_squeeze = analysis.get('bb_squeeze', False)
                if bb_squeeze:
                    # Squeeze означает готовность к сильному движению
                    if ema_cross > 0:
                        bullish_filters += 0.5
                    else:
                        bearish_filters += 0.5
                    filter_details.append(f"{tf} BB_Squeeze (READY)")
                total_filters += 1
                
                # 9. S/R Break фильтр
                sr_break = analysis.get('sr_break', 0)
                if sr_break > 0:
                    bullish_filters += 1
                    filter_details.append(f"{tf} SR_Break+ (BUY)")
                elif sr_break < 0:
                    bearish_filters += 1
                    filter_details.append(f"{tf} SR_Break- (SELL)")
                total_filters += 1
            
            # Определяем направление и уверенность
            if bullish_filters >= bearish_filters and bullish_filters >= self.min_filters:
                action = 'BUY'
                confidence = bullish_filters / total_filters if total_filters > 0 else 0
                filters_passed = bullish_filters
            elif bearish_filters >= bullish_filters and bearish_filters >= self.min_filters:
                action = 'SELL'
                confidence = bearish_filters / total_filters if total_filters > 0 else 0
                filters_passed = bearish_filters
            else:
                return None  # Недостаточно фильтров
            
            # Проверяем минимальную уверенность
            if confidence < self.min_confidence:
                return None
            
            # Рассчитываем плечо для скальпинга
            if confidence >= 0.98:
                leverage = 30.0  # Максимальное плечо для скальпинга
                action = f"SCALP_STRONG_{action}"
            elif confidence >= 0.95:
                leverage = 20.0
                action = f"SCALP_{action}"
            else:
                leverage = 15.0
                action = f"SCALP_{action}"
            
            # Рассчитываем быстрые SL/TP для скальпинга
            main_tf_analysis = tf_analysis.get('5m') or tf_analysis.get('1m') or list(tf_analysis.values())[0]
            atr = main_tf_analysis.get('atr_fast', current_price * 0.01)
            
            if action.startswith('SCALP') and 'BUY' in action:
                stop_loss = current_price - (atr * 1.5)  # Узкий SL
                take_profit_1 = current_price + (atr * 2.0)  # Быстрый TP1
                take_profit_2 = current_price + (atr * 3.5)  # TP2
            else:
                stop_loss = current_price + (atr * 1.5)
                take_profit_1 = current_price - (atr * 2.0)
                take_profit_2 = current_price - (atr * 3.5)
            
            return {
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'leverage': leverage,
                'price': current_price,
                'stop_loss': stop_loss,
                'take_profit_1': take_profit_1,
                'take_profit_2': take_profit_2,
                'filters_passed': filters_passed,
                'total_filters': total_filters,
                'filter_details': filter_details,
                'timeframes_analyzed': list(tf_analysis.keys()),
                'signal_type': 'SCALPING',
                'hold_time': '5-15 minutes',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Filter evaluation error: {e}")
            return None
    
    # Быстрые индикаторы для скальпинга
    def _calculate_fast_rsi(self, prices, period=7):
        """Быстрый RSI для скальпинга"""
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            if len(gains) < period:
                return 50
            
            avg_gain = np.mean(gains[:period])
            avg_loss = np.mean(losses[:period])
            
            for i in range(period, len(gains)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                return 100
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        except:
            return 50
    
    def _calculate_fast_macd(self, prices):
        """Быстрый MACD (5,13,4) для скальпинга"""
        try:
            if len(prices) < 13:
                return {'macd': 0, 'signal': 0, 'histogram': 0}
            
            ema_5 = self._calculate_ema(prices, 5)
            ema_13 = self._calculate_ema(prices, 13)
            macd_line = ema_5 - ema_13
            
            # Сигнальная линия (EMA от MACD)
            macd_array = []
            for i in range(len(prices)):
                if i >= 12:
                    macd_array.append(self._calculate_ema(prices[:i+1], 5) - self._calculate_ema(prices[:i+1], 13))
            
            if len(macd_array) >= 4:
                signal_line = self._calculate_ema(np.array(macd_array), 4)
                histogram = macd_line - signal_line
            else:
                signal_line = macd_line
                histogram = 0
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        except:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
    
    def _calculate_ema(self, prices, period):
        """Экспоненциальная скользящая средняя"""
        try:
            if len(prices) < period:
                return prices[-1] if len(prices) > 0 else 0
            
            alpha = 2 / (period + 1)
            ema = prices[0]
            for price in prices[1:]:
                ema = alpha * price + (1 - alpha) * ema
            return ema
        except:
            return 0
    
    def _calculate_fast_stochastic(self, highs, lows, closes, k_period=5, d_period=3):
        """Быстрый стохастик для скальпинга"""
        try:
            if len(highs) < k_period:
                return {'k': 50, 'd': 50}
            
            highest_high = np.max(highs[-k_period:])
            lowest_low = np.min(lows[-k_period:])
            
            if highest_high == lowest_low:
                k = 50
            else:
                k = 100 * (closes[-1] - lowest_low) / (highest_high - lowest_low)
            
            # D = сглаженная версия K
            d = k * 0.9  # Упрощенно
            
            return {'k': k, 'd': d}
        except:
            return {'k': 50, 'd': 50}
    
    def _calculate_fast_adx(self, highs, lows, closes, period=7):
        """Быстрый ADX для скальпинга"""
        try:
            if len(highs) < period + 1:
                return 20
            
            # Упрощенный расчет ADX
            tr_list = []
            dm_plus_list = []
            dm_minus_list = []
            
            for i in range(1, len(highs)):
                # True Range
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                tr = max(tr1, tr2, tr3)
                tr_list.append(tr)
                
                # Directional Movement
                dm_plus = max(highs[i] - highs[i-1], 0) if highs[i] - highs[i-1] > lows[i-1] - lows[i] else 0
                dm_minus = max(lows[i-1] - lows[i], 0) if lows[i-1] - lows[i] > highs[i] - highs[i-1] else 0
                
                dm_plus_list.append(dm_plus)
                dm_minus_list.append(dm_minus)
            
            if len(tr_list) >= period:
                atr = np.mean(tr_list[-period:])
                di_plus = 100 * np.mean(dm_plus_list[-period:]) / atr if atr > 0 else 0
                di_minus = 100 * np.mean(dm_minus_list[-period:]) / atr if atr > 0 else 0
                
                if (di_plus + di_minus) > 0:
                    dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
                    return dx
            
            return 20
        except:
            return 20
    
    def _calculate_volume_momentum(self, volumes, period=5):
        """Моментум объема"""
        try:
            if len(volumes) < period + 1:
                return 0
            
            current_avg = np.mean(volumes[-period:])
            previous_avg = np.mean(volumes[-period-1:-1])
            
            if previous_avg > 0:
                return (current_avg - previous_avg) / previous_avg * 100
            return 0
        except:
            return 0
    
    def _calculate_price_momentum(self, prices, period=3):
        """Моментум цены"""
        try:
            if len(prices) < period + 1:
                return 0
            
            current_price = prices[-1]
            previous_price = prices[-period-1]
            
            if previous_price > 0:
                return (current_price - previous_price) / previous_price * 100
            return 0
        except:
            return 0
    
    def _calculate_fast_atr(self, highs, lows, closes, period=7):
        """Быстрый ATR"""
        try:
            if len(highs) < period + 1:
                return abs(highs[-1] - lows[-1]) if len(highs) > 0 else 0
            
            tr_list = []
            for i in range(1, len(highs)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                tr_list.append(max(tr1, tr2, tr3))
            
            return np.mean(tr_list[-period:])
        except:
            return 0
    
    def _calculate_bb_squeeze(self, prices, period=10):
        """Bollinger Bands Squeeze"""
        try:
            if len(prices) < period:
                return False
            
            recent_prices = prices[-period:]
            sma = np.mean(recent_prices)
            std = np.std(recent_prices)
            
            # Squeeze когда стандартное отклонение очень мало
            return std / sma < 0.02 if sma > 0 else False
        except:
            return False
    
    def _calculate_sr_break(self, highs, lows, closes, period=10):
        """Пробой поддержки/сопротивления"""
        try:
            if len(highs) < period:
                return 0
            
            resistance = np.max(highs[-period:])
            support = np.min(lows[-period:])
            current_price = closes[-1]
            
            # Пробой сопротивления
            if current_price > resistance * 1.001:
                return 1
            # Пробой поддержки
            elif current_price < support * 0.999:
                return -1
            
            return 0
        except:
            return 0 