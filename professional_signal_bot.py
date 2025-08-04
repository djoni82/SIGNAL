#!/usr/bin/env python3
"""
🚀 PROFESSIONAL CRYPTO ALPHA PRO SIGNAL BOT v5.0
- Полное управление через Telegram (/start, /stop, /status, /restart)
- WebSocket real-time данные с 3 бирж
- Расширенные индикаторы (SuperTrend, Donchian, VWAP)
- Только реальные данные, никаких симуляций
- Профессиональная архитектура для production
"""

import asyncio
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
import signal
import sys

from data_manager import RealDataCollector, AdvancedTechnicalAnalyzer
from config import TELEGRAM_CONFIG, TRADING_CONFIG, ANALYSIS_CONFIG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_alpha_pro.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CryptoAlphaPro")

class TradingBotController:
    """Контроллер торгового бота с управлением через состояния"""
    
    def __init__(self):
        # Состояние бота
        self.running = False
        self.websocket_running = False
        self.analysis_running = False
        
        # Потоки выполнения
        self.main_thread = None
        self.websocket_thread = None
        self.telegram_thread = None
        
        # Компоненты
        self.data_collector = RealDataCollector()
        self.telegram_bot = None
        
        # Статистика
        self.stats = {
            'start_time': None,
            'cycles_completed': 0,
            'signals_generated': 0,
            'signals_sent': 0,
            'errors': 0,
            'websocket_messages': 0,
            'last_signal_time': None
        }
        
        # Конфигурация
        self.pairs = TRADING_CONFIG['pairs'][:50]  # Первые 50 пар для тестирования
        self.timeframes = ['5m', '15m', '1h', '4h']
        self.min_confidence = ANALYSIS_CONFIG['min_confidence']
        self.update_frequency = TRADING_CONFIG['update_frequency']
        
        # Кэш сигналов
        self.signal_cache = {}
        self.last_prices = {}
        
        logger.info("🤖 TradingBotController инициализирован")
    
    async def trading_analysis_loop(self):
        """Основной цикл анализа и генерации сигналов"""
        logger.info("🔄 Запуск основного цикла анализа...")
        self.stats['start_time'] = time.time()
        
        while self.analysis_running:
            try:
                cycle_start = time.time()
                self.stats['cycles_completed'] += 1
                
                logger.info(f"📊 Цикл #{self.stats['cycles_completed']}: Анализ {len(self.pairs)} пар...")
                
                # Анализируем пары пакетами для оптимизации
                batch_size = 10
                all_signals = []
                
                for i in range(0, len(self.pairs), batch_size):
                    batch = self.pairs[i:i+batch_size]
                    batch_signals = await self._analyze_batch(batch)
                    all_signals.extend(batch_signals)
                    
                    # Небольшая пауза между пакетами
                    await asyncio.sleep(1)
                
                # Фильтруем и сортируем сигналы
                quality_signals = self._filter_quality_signals(all_signals)
                
                if quality_signals:
                    logger.info(f"✅ Найдено {len(quality_signals)} качественных сигналов")
                    
                    # Отправляем лучшие сигналы
                    for signal in quality_signals[:5]:  # Топ 5 сигналов
                        await self._send_signal_to_telegram(signal)
                        self.stats['signals_sent'] += 1
                        await asyncio.sleep(2)  # Пауза между отправками
                
                # Статистика цикла
                cycle_time = time.time() - cycle_start
                logger.info(f"⏱️ Цикл завершен за {cycle_time:.1f}с. Найдено сигналов: {len(all_signals)}, качественных: {len(quality_signals)}")
                
                # Ждем до следующего цикла
                await asyncio.sleep(self.update_frequency)
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"❌ Ошибка в цикле анализа: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def _analyze_batch(self, pairs_batch: List[str]) -> List[Dict]:
        """Анализ пакета торговых пар"""
        signals = []
        
        # Анализируем пары параллельно
        tasks = []
        for pair in pairs_batch:
            task = self.data_collector.analyze_symbol_advanced(pair, self.timeframes)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for pair, result in zip(pairs_batch, results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Ошибка анализа {pair}: {result}")
                continue
                
            if result and result.get('timeframes'):
                signal = self._generate_signal_from_analysis(result)
                if signal:
                    signals.append(signal)
                    self.stats['signals_generated'] += 1
        
        return signals
    
    def _generate_signal_from_analysis(self, analysis: Dict) -> Optional[Dict]:
        """Генерация сигнала на основе расширенного анализа"""
        try:
            symbol = analysis['symbol']
            timeframes = analysis['timeframes']
            
            if not timeframes:
                return None
            
            # Берем основной таймфрейм (15m)
            main_tf = timeframes.get('15m') or timeframes.get('1h') or list(timeframes.values())[0]
            
            if not main_tf:
                return None
            
            # Анализируем индикаторы
            price = main_tf['price']
            supertrend = main_tf['supertrend']
            donchian = main_tf['donchian']
            vwap = main_tf['vwap']
            rsi = main_tf['advanced_rsi']
            
            # Рассчитываем confidence на основе согласованности индикаторов
            confidence_factors = []
            signal_direction = None
            
            # SuperTrend анализ
            if supertrend['trend'] == 'BULLISH' and supertrend['strength'] > 1.0:
                confidence_factors.append(0.25)
                signal_direction = 'BUY'
            elif supertrend['trend'] == 'BEARISH' and supertrend['strength'] > 1.0:
                confidence_factors.append(0.25)
                signal_direction = 'SELL'
            
            # Donchian Channel анализ
            if donchian['signal'] == 'BREAKOUT_UP' and donchian['breakout_potential'] > 0.8:
                confidence_factors.append(0.2)
                if signal_direction != 'SELL':
                    signal_direction = 'BUY'
            elif donchian['signal'] == 'BREAKOUT_DOWN' and donchian['breakout_potential'] > 0.8:
                confidence_factors.append(0.2)
                if signal_direction != 'BUY':
                    signal_direction = 'SELL'
            
            # VWAP анализ
            if vwap['signal'] == 'UNDERVALUED' and abs(vwap['deviation_pct']) > 2:
                confidence_factors.append(0.15)
                if signal_direction != 'SELL':
                    signal_direction = 'BUY'
            elif vwap['signal'] == 'OVERVALUED' and abs(vwap['deviation_pct']) > 2:
                confidence_factors.append(0.15)
                if signal_direction != 'BUY':
                    signal_direction = 'SELL'
            
            # RSI анализ
            if rsi['signal'] in ['BUY', 'STRONG_BUY']:
                confidence_factors.append(0.2)
                if signal_direction != 'SELL':
                    signal_direction = 'BUY'
            elif rsi['signal'] in ['SELL', 'STRONG_SELL']:
                confidence_factors.append(0.2)
                if signal_direction != 'BUY':
                    signal_direction = 'SELL'
            
            # Мультитаймфрейм согласованность
            tf_agreement = self._calculate_timeframe_agreement(timeframes)
            confidence_factors.append(tf_agreement * 0.2)
            
            # Итоговая уверенность
            total_confidence = min(sum(confidence_factors), 0.95)
            
            # Проверяем минимальную уверенность
            if total_confidence < self.min_confidence:
                return None
            
            if not signal_direction:
                return None
            
            # Новостной фильтр
            news_sentiment = analysis.get('news', {})
            if news_sentiment.get('sentiment') == 'very_bearish' and signal_direction == 'BUY':
                total_confidence *= 0.8  # Снижаем уверенность при негативных новостях
            elif news_sentiment.get('sentiment') == 'very_bullish' and signal_direction == 'SELL':
                total_confidence *= 0.8
            
            # Проверяем повторно после новостного фильтра
            if total_confidence < self.min_confidence:
                return None
            
            # Рассчитываем TP/SL уровни
            tp_levels, sl_level = self._calculate_tp_sl(price, signal_direction, supertrend, donchian)
            
            # Рассчитываем плечо
            leverage = self._calculate_leverage(total_confidence, main_tf.get('volume', 0))
            
            return {
                'symbol': symbol,
                'action': signal_direction,
                'confidence': total_confidence,
                'entry_price': price,
                'tp_levels': tp_levels,
                'sl_level': sl_level,
                'leverage': leverage,
                'analysis': {
                    'supertrend': supertrend,
                    'donchian': donchian,
                    'vwap': vwap,
                    'rsi': rsi,
                    'timeframe_agreement': tf_agreement,
                    'news_sentiment': news_sentiment.get('sentiment', 'neutral')
                },
                'timestamp': datetime.now().isoformat(),
                'data_quality': 'REAL'
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сигнала: {e}")
            return None
    
    def _calculate_timeframe_agreement(self, timeframes: Dict) -> float:
        """Расчет согласованности между таймфреймами"""
        try:
            signals = []
            
            for tf_name, tf_data in timeframes.items():
                if 'supertrend' in tf_data and 'advanced_rsi' in tf_data:
                    st_signal = 1 if tf_data['supertrend']['trend'] == 'BULLISH' else -1
                    rsi_signal = 1 if tf_data['advanced_rsi']['rsi'] < 50 else -1
                    
                    # Средний сигнал для таймфрейма
                    avg_signal = (st_signal + rsi_signal) / 2
                    signals.append(avg_signal)
            
            if len(signals) < 2:
                return 0.5
            
            # Рассчитываем согласованность
            positive_signals = sum(1 for s in signals if s > 0)
            negative_signals = sum(1 for s in signals if s < 0)
            total_signals = len(signals)
            
            agreement = max(positive_signals, negative_signals) / total_signals
            return agreement
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета согласованности: {e}")
            return 0.5
    
    def _calculate_tp_sl(self, price: float, direction: str, supertrend: Dict, donchian: Dict) -> tuple:
        """Расчет уровней Take Profit и Stop Loss"""
        try:
            if direction == 'BUY':
                # Take Profit уровни
                tp1 = price * 1.02    # +2%
                tp2 = price * 1.05    # +5%
                tp3 = price * 1.10    # +10%
                tp4 = price * 1.15    # +15%
                
                # Stop Loss на основе SuperTrend или Donchian
                sl_supertrend = supertrend.get('support_resistance', price * 0.95)
                sl_donchian = donchian.get('lower', price * 0.95)
                sl_level = max(sl_supertrend, sl_donchian, price * 0.93)  # Минимум -7%
                
            else:  # SELL
                # Take Profit уровни
                tp1 = price * 0.98    # -2%
                tp2 = price * 0.95    # -5%
                tp3 = price * 0.90    # -10%
                tp4 = price * 0.85    # -15%
                
                # Stop Loss
                sl_supertrend = supertrend.get('support_resistance', price * 1.05)
                sl_donchian = donchian.get('upper', price * 1.05)
                sl_level = min(sl_supertrend, sl_donchian, price * 1.07)  # Максимум +7%
            
            return [tp1, tp2, tp3, tp4], sl_level
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета TP/SL: {e}")
            # Fallback значения
            if direction == 'BUY':
                return [price * 1.02, price * 1.05, price * 1.10, price * 1.15], price * 0.95
            else:
                return [price * 0.98, price * 0.95, price * 0.90, price * 0.85], price * 1.05
    
    def _calculate_leverage(self, confidence: float, volume: float) -> float:
        """Расчет плеча на основе уверенности и объема"""
        try:
            # Базовое плечо
            base_leverage = 3.0
            
            # Множитель уверенности (0.8-0.95 -> 1.0-1.5)
            confidence_multiplier = 0.5 + (confidence - 0.8) / 0.15 * 1.0
            
            # Множитель объема (нормализация)
            volume_multiplier = min(volume / 1000000, 2.0) if volume > 0 else 1.0
            
            leverage = base_leverage * confidence_multiplier * volume_multiplier
            return max(1.0, min(leverage, 10.0))  # Ограничиваем 1x-10x
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета плеча: {e}")
            return 3.0
    
    def _filter_quality_signals(self, signals: List[Dict]) -> List[Dict]:
        """Фильтрация качественных сигналов"""
        if not signals:
            return []
        
        # Фильтруем по минимальной уверенности
        quality_signals = [s for s in signals if s.get('confidence', 0) >= self.min_confidence]
        
        # Сортируем по уверенности
        quality_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Удаляем дубликаты по символам
        seen_symbols = set()
        unique_signals = []
        for signal in quality_signals:
            symbol = signal.get('symbol')
            if symbol not in seen_symbols:
                seen_symbols.add(symbol)
                unique_signals.append(signal)
        
        return unique_signals
    
    async def _send_signal_to_telegram(self, signal: Dict):
        """Отправка сигнала в Telegram"""
        try:
            if not self.telegram_bot:
                return
            
            message = self._format_signal_message(signal)
            success = await self.telegram_bot.send_message(message)
            
            if success:
                logger.info(f"📤 Сигнал {signal['symbol']} отправлен в Telegram")
                self.stats['last_signal_time'] = time.time()
            else:
                logger.error(f"❌ Не удалось отправить сигнал {signal['symbol']}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сигнала: {e}")
    
    def _format_signal_message(self, signal: Dict) -> str:
        """Форматирование сигнала для Telegram"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            price = signal['entry_price']
            confidence = signal['confidence']
            leverage = signal['leverage']
            tp_levels = signal['tp_levels']
            sl_level = signal['sl_level']
            analysis = signal['analysis']
            
            action_emoji = "🚀" if action == 'BUY' else "📉"
            position_type = "ДЛИННУЮ ПОЗИЦИЮ" if action == 'BUY' else "КОРОТКУЮ ПОЗИЦИЮ"
            
            message = f"🚨 **ПРОФЕССИОНАЛЬНЫЙ СИГНАЛ НА {position_type}** {action_emoji}\n\n"
            message += f"**Пара:** {symbol}\n"
            message += f"**Действие:** {action}\n"
            message += f"**Цена входа:** ${price:.6f}\n"
            message += f"**⚡ Плечо:** {leverage:.1f}x\n"
            message += f"**🎯 Уверенность:** {confidence*100:.1f}%\n\n"
            
            # Take Profit уровни
            message += "**🎯 Take Profit:**\n"
            for i, tp in enumerate(tp_levels, 1):
                message += f"TP{i}: ${tp:.6f}\n"
            
            message += f"\n**🛑 Stop Loss:** ${sl_level:.6f}\n\n"
            
            # Время
            message += f"**🕒 Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            
            # Детальный анализ
            message += "**🔍 ПРОФЕССИОНАЛЬНЫЙ АНАЛИЗ:**\n\n"
            
            # SuperTrend
            st = analysis['supertrend']
            message += f"• **SuperTrend:** {st['trend']} (сила: {st['strength']:.1f}%)\n"
            
            # Donchian Channel
            dc = analysis['donchian']
            message += f"• **Donchian Channel:** {dc['signal']} (позиция: {dc['position_pct']:.1f}%)\n"
            
            # VWAP
            vwap = analysis['vwap']
            message += f"• **VWAP:** {vwap['signal']} (отклонение: {vwap['deviation_pct']:.1f}%)\n"
            
            # RSI
            rsi = analysis['rsi']
            message += f"• **Advanced RSI:** {rsi['signal']} ({rsi['rsi']:.1f})\n"
            
            # Согласованность таймфреймов
            tf_agreement = analysis['timeframe_agreement']
            message += f"• **Мультитаймфрейм согласованность:** {tf_agreement*100:.0f}%\n"
            
            # Новостной фон
            news = analysis['news_sentiment']
            message += f"• **Новостной фон:** {news}\n\n"
            
            message += "**⚡ ДАННЫЕ: 100% РЕАЛЬНЫЕ (WebSocket + REST API)**\n"
            message += "**🤖 CryptoAlphaPro v5.0 - Professional Trading Bot**"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования сигнала: {e}")
            return f"❌ Ошибка форматирования сигнала для {signal.get('symbol', 'UNKNOWN')}"
    
    async def start_websocket_streams(self):
        """Запуск WebSocket потоков"""
        try:
            self.websocket_running = True
            logger.info("🌐 Запуск WebSocket потоков...")
            
            # Запускаем WebSocket для топ пар
            top_pairs = self.pairs[:20]  # Топ 20 пар для WebSocket
            await self.data_collector.start_realtime_streams(top_pairs)
            
        except Exception as e:
            logger.error(f"❌ Ошибка WebSocket потоков: {e}")
            self.websocket_running = False
    
    async def stop_websocket_streams(self):
        """Остановка WebSocket потоков"""
        try:
            self.websocket_running = False
            await self.data_collector.stop_realtime_streams()
            logger.info("🛑 WebSocket потоки остановлены")
        except Exception as e:
            logger.error(f"❌ Ошибка остановки WebSocket: {e}")
    
    def start_bot(self) -> str:
        """Запуск торгового бота"""
        try:
            if self.running:
                return "🤖 Бот уже работает!"
            
            logger.info("🚀 Запуск CryptoAlphaPro Bot...")
            
            self.running = True
            self.analysis_running = True
            
            # Запускаем основной поток анализа
            self.main_thread = threading.Thread(target=self._run_analysis_loop, daemon=True)
            self.main_thread.start()
            
            # Запускаем WebSocket поток
            self.websocket_thread = threading.Thread(target=self._run_websocket_loop, daemon=True)
            self.websocket_thread.start()
            
            return "🚀 **CRYPTOALPHAPRO BOT ЗАПУЩЕН!**\n\n" + \
                   f"📊 Пар для анализа: {len(self.pairs)}\n" + \
                   f"⏱️ Таймфреймы: {', '.join(self.timeframes)}\n" + \
                   f"🎯 Минимальная уверенность: {self.min_confidence*100:.0f}%\n" + \
                   f"⏰ Частота обновления: {self.update_frequency}с\n\n" + \
                   "🌐 WebSocket потоки активны\n" + \
                   "📡 Реальные данные с 3 бирж\n" + \
                   "🔍 Расширенные индикаторы включены"
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return f"❌ Ошибка запуска: {e}"
    
    def stop_bot(self) -> str:
        """Остановка торгового бота"""
        try:
            if not self.running:
                return "🤖 Бот уже остановлен!"
            
            logger.info("🛑 Остановка CryptoAlphaPro Bot...")
            
            self.running = False
            self.analysis_running = False
            
            # Останавливаем WebSocket
            if self.websocket_running:
                asyncio.create_task(self.stop_websocket_streams())
            
            # Ждем завершения потоков
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=10)
            
            if self.websocket_thread and self.websocket_thread.is_alive():
                self.websocket_thread.join(timeout=10)
            
            return "🛑 **CRYPTOALPHAPRO BOT ОСТАНОВЛЕН**\n\n" + \
                   f"⏱️ Время работы: {self._get_uptime()}\n" + \
                   f"🔄 Циклов завершено: {self.stats['cycles_completed']}\n" + \
                   f"📊 Сигналов сгенерировано: {self.stats['signals_generated']}\n" + \
                   f"📤 Сигналов отправлено: {self.stats['signals_sent']}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота: {e}")
            return f"❌ Ошибка остановки: {e}"
    
    def get_status(self) -> str:
        """Получение статуса бота"""
        try:
            status = "🟢 РАБОТАЕТ" if self.running else "🔴 ОСТАНОВЛЕН"
            uptime = self._get_uptime()
            
            # Последний сигнал
            last_signal = "Никогда"
            if self.stats['last_signal_time']:
                last_signal_ago = time.time() - self.stats['last_signal_time']
                if last_signal_ago < 3600:
                    last_signal = f"{last_signal_ago/60:.0f} мин назад"
                else:
                    last_signal = f"{last_signal_ago/3600:.1f} ч назад"
            
            return f"📊 **СТАТУС CRYPTOALPHAPRO BOT**\n\n" + \
                   f"**Состояние:** {status}\n" + \
                   f"**⏱️ Время работы:** {uptime}\n" + \
                   f"**🔄 Циклов:** {self.stats['cycles_completed']}\n" + \
                   f"**📊 Сигналов сгенерировано:** {self.stats['signals_generated']}\n" + \
                   f"**📤 Сигналов отправлено:** {self.stats['signals_sent']}\n" + \
                   f"**❌ Ошибок:** {self.stats['errors']}\n" + \
                   f"**📡 WebSocket:** {'🟢 Активен' if self.websocket_running else '🔴 Неактивен'}\n" + \
                   f"**🕐 Последний сигнал:** {last_signal}\n\n" + \
                   f"**📈 Пар в анализе:** {len(self.pairs)}\n" + \
                   f"**🎯 Минимальная уверенность:** {self.min_confidence*100:.0f}%"
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            return f"❌ Ошибка получения статуса: {e}"
    
    def _get_uptime(self) -> str:
        """Получение времени работы"""
        if not self.stats['start_time']:
            return "Не запущен"
        
        uptime_seconds = time.time() - self.stats['start_time']
        
        if uptime_seconds < 60:
            return f"{uptime_seconds:.0f} сек"
        elif uptime_seconds < 3600:
            return f"{uptime_seconds/60:.0f} мин"
        else:
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            return f"{hours:.0f}ч {minutes:.0f}м"
    
    def _run_analysis_loop(self):
        """Запуск анализа в отдельном потоке"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.trading_analysis_loop())
        except Exception as e:
            logger.error(f"❌ Ошибка в потоке анализа: {e}")
        finally:
            loop.close()
    
    def _run_websocket_loop(self):
        """Запуск WebSocket в отдельном потоке"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_websocket_streams())
        except Exception as e:
            logger.error(f"❌ Ошибка в WebSocket потоке: {e}")
        finally:
            loop.close()

# Telegram Bot для управления
class TelegramBotManager:
    """Менеджер Telegram бота для управления торговым ботом"""
    
    def __init__(self, trading_controller: TradingBotController):
        self.bot_token = TELEGRAM_CONFIG['bot_token']
        self.chat_id = TELEGRAM_CONFIG['chat_id']
        self.admin_chat_id = TELEGRAM_CONFIG.get('admin_chat_id', self.chat_id)
        self.trading_controller = trading_controller
        self.running = False
        
        # Устанавливаем ссылку в контроллере
        trading_controller.telegram_bot = self
    
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
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('ok', False)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Telegram send error: {e}")
            return False
    
    async def start_polling(self):
        """Запуск прослушивания команд"""
        self.running = True
        offset = 0
        
        logger.info("📱 Telegram bot polling started...")
        
        while self.running:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                params = {'offset': offset, 'limit': 10, 'timeout': 30}
                
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=35) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('ok') and data.get('result'):
                                for update in data['result']:
                                    await self._process_update(update)
                                    offset = update['update_id'] + 1
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Telegram polling error: {e}")
                await asyncio.sleep(5)
    
    async def _process_update(self, update: Dict):
        """Обработка обновлений Telegram"""
        try:
            if 'message' not in update:
                return
            
            message = update['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            user_id = message['from']['id']
            
            # Проверяем права доступа
            if chat_id != str(self.admin_chat_id):
                await self.send_message("❌ У вас нет прав для управления ботом", chat_id)
                return
            
            # Обрабатываем команды
            if text.startswith('/'):
                await self._handle_command(text, chat_id)
            
        except Exception as e:
            logger.error(f"❌ Error processing update: {e}")
    
    async def _handle_command(self, command: str, chat_id: str):
        """Обработка команд управления"""
        try:
            command = command.lower().strip()
            
            if command in ['/start', '/startbot']:
                response = self.trading_controller.start_bot()
                await self.send_message(response, chat_id)
                
            elif command in ['/stop', '/stopbot']:
                response = self.trading_controller.stop_bot()
                await self.send_message(response, chat_id)
                
            elif command == '/status':
                response = self.trading_controller.get_status()
                await self.send_message(response, chat_id)
                
            elif command == '/restart':
                # Останавливаем и запускаем заново
                stop_response = self.trading_controller.stop_bot()
                await self.send_message(stop_response, chat_id)
                await asyncio.sleep(3)
                start_response = self.trading_controller.start_bot()
                await self.send_message(f"🔄 **ПЕРЕЗАПУСК ЗАВЕРШЕН**\n\n{start_response}", chat_id)
                
            elif command == '/help':
                help_text = "📚 **КОМАНДЫ УПРАВЛЕНИЯ CRYPTOALPHAPRO BOT**\n\n" + \
                           "🚀 `/start` или `/startbot` - Запустить бота\n" + \
                           "🛑 `/stop` или `/stopbot` - Остановить бота\n" + \
                           "📊 `/status` - Статус и статистика\n" + \
                           "🔄 `/restart` - Перезапустить бота\n" + \
                           "📚 `/help` - Эта справка\n\n" + \
                           "**Особенности v5.0:**\n" + \
                           "• WebSocket real-time данные\n" + \
                           "• SuperTrend, Donchian, VWAP индикаторы\n" + \
                           "• Реальные on-chain данные\n" + \
                           "• Профессиональная фильтрация сигналов"
                await self.send_message(help_text, chat_id)
                
            else:
                await self.send_message("❌ Неизвестная команда. Используйте /help", chat_id)
                
        except Exception as e:
            logger.error(f"❌ Command handling error: {e}")
            await self.send_message("❌ Ошибка выполнения команды", chat_id)
    
    def stop_polling(self):
        """Остановка прослушивания"""
        self.running = False

# Главная функция
async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск CryptoAlphaPro Professional Signal Bot v5.0")
    
    # Создаем контроллер торгового бота
    trading_controller = TradingBotController()
    
    # Создаем Telegram менеджер
    telegram_manager = TelegramBotManager(trading_controller)
    
    # Обработчик сигналов для корректного завершения
    def signal_handler(signum, frame):
        logger.info("🛑 Получен сигнал завершения...")
        trading_controller.stop_bot()
        telegram_manager.stop_polling()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Отправляем приветственное сообщение
        await telegram_manager.send_message(
            "🤖 **CRYPTOALPHAPRO BOT v5.0 ONLINE**\n\n" +
            "Профессиональный торговый бот готов к работе!\n\n" +
            "**Команды управления:**\n" +
            "🚀 `/startbot` - Запустить торговлю\n" +
            "📊 `/status` - Проверить статус\n" +
            "📚 `/help` - Полная справка\n\n" +
            "**Новые возможности v5.0:**\n" +
            "• WebSocket real-time потоки\n" +
            "• SuperTrend, Donchian, VWAP\n" +
            "• Реальные on-chain данные\n" +
            "• Профессиональная архитектура"
        )
        
        # Запускаем Telegram polling
        await telegram_manager.start_polling()
        
    except KeyboardInterrupt:
        logger.info("🛑 Завершение работы...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        trading_controller.stop_bot()
        telegram_manager.stop_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Программа завершена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка запуска: {e}")
        sys.exit(1) 