#!/usr/bin/env python3
"""
Telegram Integration - Интеграция с Telegram для отправки сигналов
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from config import TELEGRAM_CONFIG

logger = logging.getLogger(__name__)

class TelegramIntegration:
    """Интеграция с Telegram для отправки сообщений"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_CONFIG['bot_token']
        self.chat_id = TELEGRAM_CONFIG['chat_id']
        self.enable_telegram = TELEGRAM_CONFIG['enable_telegram']
        self.send_signals = TELEGRAM_CONFIG['send_signals']
        self.send_status = TELEGRAM_CONFIG['send_status']
        self.send_errors = TELEGRAM_CONFIG['send_errors']
        
        self.session = None
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if self.enable_telegram and self.bot_token != 'YOUR_TELEGRAM_BOT_TOKEN':
            logger.info("📱 Telegram интеграция инициализирована")
        else:
            logger.warning("⚠️ Telegram не настроен. Установите bot_token в config.py")
    
    async def __aenter__(self):
        """Асинхронный контекст менеджер - вход"""
        if self.enable_telegram:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекст менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def send_message(self, text: str, parse_mode: str = 'Markdown') -> bool:
        """Отправляет сообщение в Telegram"""
        if not self.enable_telegram or self.bot_token == 'YOUR_TELEGRAM_BOT_TOKEN':
            return False
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            async with self.session.post(url, json=data, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        logger.info("📤 Сообщение отправлено в Telegram")
                        return True
                    else:
                        logger.error(f"❌ Ошибка Telegram API: {result}")
                        return False
                else:
                    logger.error(f"❌ HTTP ошибка: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в Telegram: {e}")
            return False
    
    async def send_signal(self, signal: Dict[str, Any]) -> bool:
        """Отправляет торговый сигнал в Telegram"""
        if not self.send_signals:
            return False
        
        try:
            # Форматируем сигнал для Telegram
            message = self._format_signal_for_telegram(signal)
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сигнала: {e}")
            return False
    
    async def send_status_update(self, status: Dict[str, Any]) -> bool:
        """Отправляет статус бота в Telegram"""
        if not self.send_status:
            return False
        
        try:
            message = self._format_status_for_telegram(status)
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки статуса: {e}")
            return False
    
    async def send_error(self, error: str) -> bool:
        """Отправляет ошибку в Telegram"""
        if not self.send_errors:
            return False
        
        try:
            message = f"❌ **Ошибка бота:**\n\n{error}"
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки ошибки: {e}")
            return False
    
    def _format_signal_for_telegram(self, signal: Dict[str, Any]) -> str:
        """Форматирует сигнал для Telegram"""
        try:
            action = signal.get('action', 'HOLD')
            symbol = signal.get('symbol', 'UNKNOWN')
            price = signal.get('price', 0)
            confidence = signal.get('confidence', 0)
            alpha_score = signal.get('alpha_score', 0)
            risk_reward = signal.get('risk_reward', 0)
            
            # Определяем эмодзи для действия
            if action == 'BUY':
                action_emoji = "🚀"
                position_type = "ДЛИННУЮ ПОЗИЦИЮ"
            elif action == 'SELL':
                action_emoji = "📉"
                position_type = "КОРОТКУЮ ПОЗИЦИЮ"
            else:
                action_emoji = "⏸️"
                position_type = "ПОЗИЦИЮ"
            
            # Основное сообщение
            message = f"🚨 **СИГНАЛ НА {position_type}** {action_emoji}\n\n"
            message += f"**Пара:** {symbol}\n"
            message += f"**Действие:** {action}\n"
            message += f"**Цена входа:** ${price:.6f}\n\n"
            
            # Take Profit уровни
            if 'take_profit' in signal:
                tp_levels = signal['take_profit']
                message += "**🎯 Take Profit:**\n"
                for i, tp in enumerate(tp_levels[:3], 1):
                    profit_pct = ((tp - price) / price * 100) if action == 'BUY' else ((price - tp) / price * 100)
                    message += f"TP{i}: ${tp:.6f} (+{profit_pct:.1f}%)\n"
            
            # Stop Loss
            if 'stop_loss' in signal:
                sl = signal['stop_loss']
                loss_pct = ((sl - price) / price * 100) if action == 'BUY' else ((price - sl) / price * 100)
                message += f"\n**🛑 Stop Loss:** ${sl:.6f} ({loss_pct:.1f}%)\n"
            
            # Дополнительная информация
            message += f"\n**📊 Уровень успеха:** {confidence*100:.0f}%\n"
            message += f"**🧠 Alpha Score:** {alpha_score}/7\n"
            message += f"**⚖️ Risk/Reward:** {risk_reward:.2f}\n"
            message += f"**🕒 Время:** {signal.get('timestamp', 'N/A')}\n\n"
            
            # Объяснение сигнала
            if 'analysis' in signal:
                explanation = self._generate_signal_explanation(signal)
                if explanation:
                    message += f"**🔎 ТЕХНИЧЕСКИЙ АНАЛИЗ:**\n{explanation}\n\n"
            
            # Статистика
            message += "**📈 CryptoAlphaPro Signal Bot v3.0**\n"
            message += "Система 'Best Alpha Only' - только лучшие сигналы!\n"
            message += "⚠️ **Риск-менеджмент обязателен!**"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования сигнала: {e}")
            return f"❌ Ошибка форматирования сигнала: {e}"
    
    def _format_status_for_telegram(self, status: Dict[str, Any]) -> str:
        """Форматирует статус для Telegram"""
        try:
            message = "📊 **Статус CryptoAlphaPro Bot**\n\n"
            message += f"🔄 **Состояние:** {'🟢 Работает' if status.get('running', False) else '🔴 Остановлен'}\n"
            message += f"📈 **Всего сигналов:** {status.get('signal_count', 0)}\n"
            message += f"🔄 **Цикл:** #{status.get('cycle_count', 0)}\n"
            message += f"⏰ **Последний сигнал:** {status.get('last_signal_time_str', 'Нет')}\n"
            message += f"📊 **Пар:** {status.get('pairs_count', 0)}\n"
            message += f"⏱️ **Таймфреймов:** {status.get('timeframes_count', 0)}\n"
            message += f"🎯 **Минимальная уверенность:** {status.get('min_confidence', 0)*100:.0f}%\n"
            message += f"🎯 **Топ сигналов:** {status.get('top_signals', 0)}\n"
            message += f"⏰ **Частота обновления:** {status.get('update_frequency', 0)} сек\n\n"
            message += "**🤖 CryptoAlphaPro Signal Bot v3.0**"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования статуса: {e}")
            return f"❌ Ошибка форматирования статуса: {e}"
    
    def _generate_signal_explanation(self, signal: Dict[str, Any]) -> str:
        """Генерирует детальное объяснение сигнала"""
        try:
            analysis = signal.get('analysis', {})
            explanations = []
            warnings = []
            
            # RSI анализ
            rsi = analysis.get('rsi', 50)
            if rsi > 70:
                explanations.append(f"📊 **RSI:** {rsi:.2f} (Перекупленность)")
            elif rsi > 60:
                explanations.append(f"📊 **RSI:** {rsi:.2f} (Сильный тренд)")
            elif rsi < 30:
                explanations.append(f"📊 **RSI:** {rsi:.2f} (Перепроданность)")
            elif rsi < 40:
                explanations.append(f"📊 **RSI:** {rsi:.2f} (Слабый тренд)")
            else:
                explanations.append(f"📊 **RSI:** {rsi:.2f} (Нейтральный)")
            
            # MACD анализ
            macd_data = analysis.get('macd', {})
            if 'macd' in macd_data and 'signal' in macd_data and 'histogram' in macd_data:
                macd_line = macd_data['macd']
                signal_line = macd_data['signal']
                hist = macd_data['histogram']
                
                if macd_line > signal_line:
                    explanations.append(f"📈 **MACD:** Бычье расхождение (MACD: {macd_line:.4f}, Signal: {signal_line:.4f})")
                else:
                    explanations.append(f"📉 **MACD:** Медвежье расхождение (MACD: {macd_line:.4f}, Signal: {signal_line:.4f})")
                
                if abs(hist) > 0.005:
                    if hist > 0:
                        explanations.append(f"📊 **MACD Histogram:** Положительная ({hist:.4f})")
                    else:
                        explanations.append(f"📊 **MACD Histogram:** Отрицательная ({hist:.4f})")
            
            # EMA анализ
            ema_data = analysis.get('ema', {})
            if 'ema_20' in ema_data and 'ema_50' in ema_data:
                ema_20 = ema_data['ema_20']
                ema_50 = ema_data['ema_50']
                current_price = signal.get('price', 0)
                
                if current_price > ema_20 > ema_50:
                    explanations.append(f"📈 **EMA:** Бычий тренд (Цена > EMA20 > EMA50)")
                elif current_price < ema_20 < ema_50:
                    explanations.append(f"📉 **EMA:** Медвежий тренд (Цена < EMA20 < EMA50)")
                else:
                    explanations.append(f"📊 **EMA:** Смешанный тренд")
            
            # Bollinger Bands
            bb_data = analysis.get('bollinger_bands', {})
            if 'upper' in bb_data and 'lower' in bb_data and 'middle' in bb_data:
                upper = bb_data['upper']
                lower = bb_data['lower']
                middle = bb_data['middle']
                current_price = signal.get('price', 0)
                
                if current_price > upper:
                    explanations.append(f"📊 **Bollinger Bands:** Цена выше верхней полосы (Перекупленность)")
                elif current_price < lower:
                    explanations.append(f"📊 **Bollinger Bands:** Цена ниже нижней полосы (Перепроданность)")
                else:
                    explanations.append(f"📊 **Bollinger Bands:** Цена в пределах полос")
            
            # MA50 анализ
            ma_data = analysis.get('moving_averages', {})
            if 'ma_50' in ma_data:
                ma_50 = ma_data['ma_50']
                current_price = signal.get('price', 0)
                
                if current_price > ma_50:
                    explanations.append(f"📈 **MA50:** Цена выше MA50 (Бычий тренд)")
                else:
                    explanations.append(f"📉 **MA50:** Цена ниже MA50 (Медвежий тренд)")
            
            # ADX анализ
            adx_data = analysis.get('adx', {})
            if 'adx' in adx_data:
                adx = adx_data['adx']
                if adx >= 25:
                    explanations.append(f"💪 **ADX:** {adx:.1f} (Сильный тренд)")
                elif adx >= 20:
                    explanations.append(f"📊 **ADX:** {adx:.1f} (Умеренный тренд)")
                else:
                    explanations.append(f"📊 **ADX:** {adx:.1f} (Слабый тренд)")
            
            # Volume анализ
            volume_data = analysis.get('volume', {})
            if 'ratio' in volume_data:
                ratio = volume_data['ratio']
                if ratio > 1.5:
                    explanations.append(f"📊 **Volume Spike:** Рост объёма {(ratio-1)*100:.0f}%")
                elif ratio > 1.2:
                    explanations.append(f"📊 **Volume:** Умеренный рост объёма {(ratio-1)*100:.0f}%")
                elif ratio < 0.8:
                    explanations.append(f"📊 **Volume:** Падение объёма {(1-ratio)*100:.0f}%")
            
            # Candlestick Patterns
            patterns = analysis.get('patterns', [])
            if patterns:
                pattern_names = []
                for pattern in patterns:
                    if pattern.get('name'):
                        pattern_names.append(pattern['name'])
                if pattern_names:
                    explanations.append(f"🕯️ **Candlestick Patterns:** {', '.join(pattern_names)}")
            
            # Multi-Timeframe анализ
            mtf_data = signal.get('mtf_analysis', {})
            if mtf_data:
                mtf_agreement = mtf_data.get('agreement', 0)
                if mtf_agreement > 0.6:
                    explanations.append(f"⏰ **Multi-Timeframe:** Высокая согласованность ({mtf_agreement:.2f})")
                elif mtf_agreement > 0.4:
                    explanations.append(f"⏰ **Multi-Timeframe:** Умеренная согласованность ({mtf_agreement:.2f})")
                else:
                    explanations.append(f"⏰ **Multi-Timeframe:** Низкая согласованность ({mtf_agreement:.2f})")
            
            # Consensus score
            consensus_score = signal.get('consensus_score', 0)
            if consensus_score > 0.7:
                explanations.append(f"🎯 **Consensus Score:** Высокий ({consensus_score:.2f})")
            elif consensus_score > 0.5:
                explanations.append(f"🎯 **Consensus Score:** Умеренный ({consensus_score:.2f})")
            
            # Trend agreement
            trend_agreement = signal.get('trend_agreement', 0)
            if trend_agreement > 0.6:
                explanations.append(f"📈 **Trend Agreement:** Высокая ({trend_agreement:.2f})")
            elif trend_agreement > 0.4:
                explanations.append(f"📈 **Trend Agreement:** Умеренная ({trend_agreement:.2f})")
            
            # Предупреждения
            current_price = signal.get('price', 0)
            
            # Проверка расстояния до поддержки/сопротивления
            support_resistance = analysis.get('support_resistance', {})
            if 'nearest_support' in support_resistance and 'nearest_resistance' in support_resistance:
                support = support_resistance['nearest_support']
                resistance = support_resistance['nearest_resistance']
                
                support_distance = abs(current_price - support) / current_price * 100
                resistance_distance = abs(resistance - current_price) / current_price * 100
                
                if support_distance < 2:
                    warnings.append(f"⚠️ **Близко к поддержке:** {support_distance:.1f}%")
                if resistance_distance < 2:
                    warnings.append(f"⚠️ **Близко к сопротивлению:** {resistance_distance:.1f}%")
            
            # Проверка Stochastic RSI
            stoch_rsi = analysis.get('stochastic_rsi', {})
            if 'k' in stoch_rsi and 'd' in stoch_rsi:
                k = stoch_rsi['k']
                d = stoch_rsi['d']
                
                if k > 80 and d > 80:
                    warnings.append(f"⚠️ **Stoch RSI:** Перекупленность (K: {k:.1f}, D: {d:.1f})")
                elif k < 20 and d < 20:
                    warnings.append(f"⚠️ **Stoch RSI:** Перепроданность (K: {k:.1f}, D: {d:.1f})")
            
            # Формируем итоговое сообщение
            result = "\n".join(explanations)
            
            if warnings:
                result += "\n\n**⚠️ ПРЕДУПРЕЖДЕНИЯ:**\n" + "\n".join(warnings)
            
            return result if result else "Детальный анализ недоступен"
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации объяснения: {e}")
            return "Ошибка генерации объяснения" 