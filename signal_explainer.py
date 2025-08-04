#!/usr/bin/env python3
"""
Signal Explainer - Детальное объяснение торговых сигналов
"""

import math
from typing import Dict, List, Any, Optional
from datetime import datetime

class SignalExplainer:
    """Класс для генерации детальных объяснений торговых сигналов"""
    
    def __init__(self):
        self.thresholds = {
            'rsi_strong': 60,
            'rsi_weak': 40,
            'macd_hist_threshold': 0.01,
            'adx_strong': 25,
            'volume_spike': 1.5,
            'bb_breakout': 0.95,
            'support_distance': 0.05,  # 5%
            'resistance_distance': 0.05  # 5%
        }
    
    def explain_signal(self, signal: Dict[str, Any], analysis: Dict[str, Any], 
                      mtf_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Генерирует детальное объяснение сигнала
        
        Args:
            signal: Словарь с данными сигнала
            analysis: Словарь с техническим анализом
            mtf_analysis: Мультитаймфреймовый анализ
            
        Returns:
            Строка с объяснением сигнала
        """
        explanations = []
        warnings = []
        
        # RSI анализ
        if 'rsi' in analysis:
            rsi = analysis['rsi']
            if rsi > self.thresholds['rsi_strong']:
                explanations.append(f"• RSI сильный > 60 ({rsi:.2f})")
            elif rsi < self.thresholds['rsi_weak']:
                explanations.append(f"• RSI слабый < 40 ({rsi:.2f})")
            else:
                explanations.append(f"• RSI нейтральный ({rsi:.2f})")
        
        # MACD анализ
        if 'macd' in analysis:
            macd_data = analysis['macd']
            if 'histogram' in macd_data:
                hist = macd_data['histogram']
                if abs(hist) > self.thresholds['macd_hist_threshold']:
                    if hist > 0:
                        explanations.append(f"• Гистограмма MACD сильная ({hist:.3f})")
                    else:
                        explanations.append(f"• Гистограмма MACD отрицательная ({hist:.3f})")
        
        # EMA анализ
        if 'ema' in analysis:
            ema_data = analysis['ema']
            if 'ema_8' in ema_data and 'ema_21' in ema_data:
                ema_8 = ema_data['ema_8']
                ema_21 = ema_data['ema_21']
                if ema_8 > ema_21:
                    explanations.append("• Цена выше EMA, сильное подтверждение")
                else:
                    explanations.append("• Цена ниже EMA, слабое подтверждение")
        
        # Bollinger Bands анализ
        if 'bollinger' in analysis:
            bb_data = analysis['bollinger']
            if 'position' in bb_data:
                position = bb_data['position']
                if position > self.thresholds['bb_breakout']:
                    explanations.append("• Цена пробила полосу Боллинджера (пробой)")
                elif position < 0.05:
                    explanations.append("• Цена у нижней полосы Боллинджера")
        
        # ADX анализ (сила тренда)
        if 'adx' in analysis:
            adx_data = analysis['adx']
            if 'adx' in adx_data:
                adx = adx_data['adx']
                if adx >= self.thresholds['adx_strong']:
                    explanations.append(f"• Сила тренда высокая (ADX ≥ 25, {adx:.1f})")
                else:
                    explanations.append(f"• Сила тренда слабая (ADX < 25, {adx:.1f})")
        
        # Volume анализ
        if 'volume' in analysis:
            volume_data = analysis['volume']
            if 'ratio' in volume_data:
                ratio = volume_data['ratio']
                if ratio > self.thresholds['volume_spike']:
                    explanations.append(f"• Рост объёма более {(ratio-1)*100:.0f}%!")
                elif ratio < 0.7:
                    explanations.append(f"• Снижение объёма на {(1-ratio)*100:.0f}%")
        
        # Паттерны
        if 'patterns' in analysis:
            patterns = analysis['patterns']
            if 'bullish_three_white_soldiers' in patterns:
                explanations.append("• Обнаружен паттерн «Три белых солдата»")
            if 'bearish_three_black_crows' in patterns:
                explanations.append("• Обнаружен паттерн «Три черных ворона»")
            if 'doji' in patterns:
                explanations.append("• Обнаружен паттерн «Доджи»")
        
        # Мультитаймфреймовый анализ
        if mtf_analysis:
            mtf_explanations = self._analyze_mtf(mtf_analysis)
            explanations.extend(mtf_explanations)
        
        # Уровни поддержки и сопротивления
        support_warnings = self._analyze_support_resistance(signal, analysis)
        warnings.extend(support_warnings)
        
        # Собираем результат
        result = "\n".join(explanations)
        
        if warnings:
            result += "\n\n❗️ Предупреждения:\n" + "\n".join(warnings)
        
        return result
    
    def _analyze_mtf(self, mtf_analysis: Dict[str, Any]) -> List[str]:
        """Анализ мультитаймфреймовых данных"""
        explanations = []
        
        if 'timeframes' in mtf_analysis:
            timeframes = mtf_analysis['timeframes']
            
            # Проверяем согласованность таймфреймов
            bullish_count = 0
            bearish_count = 0
            
            for tf, data in timeframes.items():
                if data.get('trend') == 'bullish':
                    bullish_count += 1
                elif data.get('trend') == 'bearish':
                    bearish_count += 1
            
            if bullish_count > bearish_count:
                explanations.append(f"• Подтверждение тренда положительное ({bullish_count}/{len(timeframes)} таймфреймов)")
            elif bearish_count > bullish_count:
                explanations.append(f"• Подтверждение тренда отрицательное ({bearish_count}/{len(timeframes)} таймфреймов)")
            else:
                explanations.append("• Таймфреймы несовместимы")
        
        return explanations
    
    def _analyze_support_resistance(self, signal: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Анализ уровней поддержки и сопротивления"""
        warnings = []
        
        current_price = signal.get('price', 0)
        if current_price <= 0:
            return warnings
        
        # Анализ поддержки
        if 'support' in analysis:
            support = analysis['support']
            if support > 0:
                distance = (current_price - support) / current_price
                if distance > self.thresholds['support_distance']:
                    warnings.append(f"❗️ Уровень поддержки находится далеко от цены: ${support:.4f} ({distance*100:.1f}%)")
        
        # Анализ сопротивления
        if 'resistance' in analysis:
            resistance = analysis['resistance']
            if resistance > 0:
                distance = (resistance - current_price) / current_price
                if distance > self.thresholds['resistance_distance']:
                    warnings.append(f"❗️ Уровень сопротивления находится далеко от цены: ${resistance:.4f} ({distance*100:.1f}%)")
        
        return warnings
    
    def format_signal_message(self, signal: Dict[str, Any], analysis: Dict[str, Any], 
                            mtf_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Форматирует полное сообщение сигнала с объяснением
        
        Args:
            signal: Данные сигнала
            analysis: Технический анализ
            mtf_analysis: Мультитаймфреймовый анализ
            
        Returns:
            Отформатированное сообщение
        """
        # Основная информация сигнала
        action = signal.get('action', 'HOLD')
        symbol = signal.get('symbol', 'UNKNOWN')
        price = signal.get('price', 0)
        confidence = signal.get('confidence', 0)
        
        # Определяем тип позиции
        if action in ['BUY', 'STRONG_BUY']:
            position_type = "ДЛИННУЮ ПОЗИЦИЮ"
        elif action in ['SELL', 'STRONG_SELL']:
            position_type = "КОРОТКУЮ ПОЗИЦИЮ"
        else:
            position_type = "ПОЗИЦИЮ"
        
        # Формируем основное сообщение
        msg = f"🚨 СИГНАЛ НА {position_type} по {symbol} 🚀\n\n"
        msg += f"💰 Цена входа: ${price:.6f}\n\n"
        
        # Take Profit уровни
        if 'take_profit' in signal:
            tp_levels = signal['take_profit']
            for i, tp in enumerate(tp_levels[:4], 1):
                msg += f"🎯 TP{i}: ${tp:.6f}\n"
        
        # Stop Loss
        if 'stop_loss' in signal:
            sl = signal['stop_loss']
            msg += f"\n🛑 Стоп-лосс: ${sl:.6f}\n"
        
        # Дополнительная информация
        msg += f"\n📊 Уровень успеха: {confidence*100:.0f}%\n"
        msg += f"🕒 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Объяснение сигнала
        explanation = self.explain_signal(signal, analysis, mtf_analysis)
        if explanation:
            msg += f"🔎 Почему сигнал на {position_type.lower()} ❓\n\n"
            msg += "Подробности сделки 👇\n\n"
            msg += explanation
        
        return msg
    
    def calculate_take_profit_levels(self, entry_price: float, direction: str = 'long') -> List[float]:
        """Рассчитывает уровни Take Profit"""
        if direction == 'long':
            return [
                entry_price * 1.025,  # TP1: +2.5%
                entry_price * 1.05,   # TP2: +5%
                entry_price * 1.10,   # TP3: +10%
                entry_price * 1.15    # TP4: +15%
            ]
        else:
            return [
                entry_price * 0.975,  # TP1: -2.5%
                entry_price * 0.95,   # TP2: -5%
                entry_price * 0.90,   # TP3: -10%
                entry_price * 0.85    # TP4: -15%
            ]
    
    def calculate_stop_loss(self, entry_price: float, direction: str = 'long', 
                          atr: Optional[float] = None) -> float:
        """Рассчитывает Stop Loss"""
        if atr:
            # Используем ATR для динамического SL
            if direction == 'long':
                return entry_price - (atr * 2)
            else:
                return entry_price + (atr * 2)
        else:
            # Фиксированный процент
            if direction == 'long':
                return entry_price * 0.95  # -5%
            else:
                return entry_price * 1.05  # +5% 