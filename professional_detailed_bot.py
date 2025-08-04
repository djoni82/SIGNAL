#!/usr/bin/env python3
"""
🚀 PROFESSIONAL DETAILED CRYPTO SIGNAL BOT v6.0
Генерация детальных профессиональных сигналов как в примере
"""

import asyncio
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np

from data_manager import RealDataCollector
from enhanced_technical_analyzer import ProfessionalTechnicalAnalyzer
from config import TELEGRAM_CONFIG, TRADING_CONFIG, ANALYSIS_CONFIG

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DetailedSignalBot")

class DetailedSignalGenerator:
    """Генератор детальных сигналов"""
    
    def __init__(self):
        self.data_collector = RealDataCollector()
        self.technical_analyzer = ProfessionalTechnicalAnalyzer()
        
    async def analyze_and_generate_signal(self, symbol: str) -> Optional[Dict]:
        """Анализ символа и генерация детального сигнала"""
        try:
            # Получаем данные для анализа
            timeframes = ['5m', '15m', '1h', '4h']
            analysis_data = {}
            
            for tf in timeframes:
                df = await self.data_collector.get_real_ohlcv(symbol, tf, limit=150)
                if df is not None and len(df) >= 50:
                    analysis_data[tf] = df
            
            if not analysis_data:
                return None
            
            # Используем 15m как основной таймфрейм
            main_df = analysis_data.get('15m') or analysis_data.get('1h') or list(analysis_data.values())[0]
            
            # Получаем полный технический анализ
            indicators = self.technical_analyzer.calculate_all_indicators(main_df)
            
            if not indicators:
                return None
            
            # Определяем направление сигнала
            action = self._determine_signal_direction(indicators)
            
            if action == 'NEUTRAL':
                return None
            
            # Генерируем детальный сигнал
            signal = self._generate_detailed_signal(main_df, symbol, action, indicators, analysis_data)
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error analyzing {symbol}: {e}")
            return None
    
    def _determine_signal_direction(self, indicators: Dict) -> str:
        """Определение направления сигнала на основе индикаторов"""
        try:
            bullish_signals = 0
            bearish_signals = 0
            
            # RSI сигнал
            rsi_signal = indicators.get('rsi', {}).get('signal', 'NEUTRAL')
            if 'BUY' in rsi_signal:
                bullish_signals += 2 if 'STRONG' in rsi_signal else 1
            elif 'SELL' in rsi_signal:
                bearish_signals += 2 if 'STRONG' in rsi_signal else 1
            
            # MACD сигнал
            macd_signal = indicators.get('macd', {}).get('signal', 'NEUTRAL')
            macd_strength = indicators.get('macd', {}).get('strength', 'слабая')
            if macd_signal == 'BUY' and macd_strength in ['сильная', 'умеренная']:
                bullish_signals += 2
            elif macd_signal == 'SELL' and macd_strength in ['сильная', 'умеренная']:
                bearish_signals += 2
            
            # EMA сигнал
            ema_signal = indicators.get('ema', {}).get('signal', 'NEUTRAL')
            if 'BUY' in ema_signal:
                bullish_signals += 2 if 'STRONG' in ema_signal else 1
            elif 'SELL' in ema_signal:
                bearish_signals += 2 if 'STRONG' in ema_signal else 1
            
            # Bollinger Bands пробой
            bb_signal = indicators.get('bollinger', {}).get('signal', 'NEUTRAL')
            if bb_signal == 'BREAKOUT_UP':
                bullish_signals += 2
            elif bb_signal == 'BREAKOUT_DOWN':
                bearish_signals += 2
            
            # SuperTrend
            supertrend_signal = indicators.get('supertrend', {}).get('signal', 'NEUTRAL')
            if supertrend_signal == 'BUY':
                bullish_signals += 1
            elif supertrend_signal == 'SELL':
                bearish_signals += 1
            
            # ADX сила тренда
            adx_strength = indicators.get('adx', {}).get('strength', 'слабая')
            if adx_strength in ['высокая', 'очень высокая']:
                # Усиливаем существующий сигнал
                if bullish_signals > bearish_signals:
                    bullish_signals += 1
                elif bearish_signals > bullish_signals:
                    bearish_signals += 1
            
            # Определяем итоговый сигнал
            if bullish_signals >= bearish_signals + 2:
                return 'BUY'
            elif bearish_signals >= bullish_signals + 2:
                return 'SELL'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            logger.error(f"❌ Error determining signal direction: {e}")
            return 'NEUTRAL'
    
    def _generate_detailed_signal(self, df, symbol: str, action: str, indicators: Dict, timeframe_data: Dict) -> Dict:
        """Генерация детального сигнала как в примере"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Рассчитываем TP/SL как в примере
            if action == 'BUY':
                tp1 = current_price * 1.025   # +2.5%
                tp2 = current_price * 1.05    # +5%
                tp3 = current_price * 1.10    # +10%
                tp4 = current_price * 1.135   # +13.5%
                sl = current_price * 0.95     # -5%
            else:
                tp1 = current_price * 0.975   # -2.5%
                tp2 = current_price * 0.95    # -5%
                tp3 = current_price * 0.90    # -10%
                tp4 = current_price * 0.865   # -13.5%
                sl = current_price * 1.05     # +5%
            
            # Рассчитываем уверенность
            confidence = self._calculate_confidence(indicators)
            
            # Динамическое плечо (1x-50x)
            leverage = min(50, max(1, int(confidence * 60)))
            
            # Собираем детальные объяснения
            explanations = self._generate_explanations(indicators, action)
            warnings = self._generate_warnings(indicators, timeframe_data)
            
            return {
                'symbol': symbol,
                'action': action,
                'entry_price': current_price,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'tp4': tp4,
                'stop_loss': sl,
                'leverage': leverage,
                'confidence': confidence,
                'explanations': explanations,
                'warnings': warnings,
                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating detailed signal: {e}")
            return None
    
    def _calculate_confidence(self, indicators: Dict) -> float:
        """Расчет уверенности сигнала"""
        try:
            confidence_factors = []
            
            # RSI фактор
            rsi_signal = indicators.get('rsi', {}).get('signal', 'NEUTRAL')
            if 'STRONG' in rsi_signal:
                confidence_factors.append(0.25)
            elif 'BUY' in rsi_signal or 'SELL' in rsi_signal:
                confidence_factors.append(0.15)
            
            # MACD фактор
            macd_strength = indicators.get('macd', {}).get('strength', 'слабая')
            if macd_strength == 'сильная':
                confidence_factors.append(0.2)
            elif macd_strength == 'умеренная':
                confidence_factors.append(0.1)
            
            # EMA фактор
            ema_signal = indicators.get('ema', {}).get('signal', 'NEUTRAL')
            if 'STRONG' in ema_signal:
                confidence_factors.append(0.2)
            elif 'BUY' in ema_signal or 'SELL' in ema_signal:
                confidence_factors.append(0.1)
            
            # ADX фактор
            adx_strength = indicators.get('adx', {}).get('strength', 'слабая')
            if adx_strength in ['высокая', 'очень высокая']:
                confidence_factors.append(0.15)
            elif adx_strength == 'умеренная':
                confidence_factors.append(0.1)
            
            # Volume фактор
            volume_spike = indicators.get('volume_analysis', {}).get('spike_level', 'отсутствует')
            if volume_spike in ['очень сильный', 'сильный']:
                confidence_factors.append(0.1)
            elif volume_spike == 'умеренный':
                confidence_factors.append(0.05)
            
            # Bollinger Bands фактор
            bb_signal = indicators.get('bollinger', {}).get('signal', 'NEUTRAL')
            if 'BREAKOUT' in bb_signal:
                confidence_factors.append(0.1)
            
            # Support/Resistance фактор
            breakout = indicators.get('support_resistance', {}).get('breakout', '')
            if 'пробит' in breakout:
                confidence_factors.append(0.05)
            
            total_confidence = min(sum(confidence_factors) + 0.5, 0.95)
            return total_confidence
            
        except Exception as e:
            logger.error(f"❌ Error calculating confidence: {e}")
            return 0.5
    
    def _generate_explanations(self, indicators: Dict, action: str) -> List[str]:
        """Генерация объяснений как в примере"""
        explanations = []
        
        try:
            # RSI объяснение
            rsi_desc = indicators.get('rsi', {}).get('description', '')
            if rsi_desc:
                explanations.append(f"• {rsi_desc}.")
            
            # MACD объяснение
            macd_desc = indicators.get('macd', {}).get('description', '')
            if macd_desc:
                explanations.append(f"• {macd_desc}.")
            
            # EMA объяснение
            ema_desc = indicators.get('ema', {}).get('description', '')
            if ema_desc:
                explanations.append(f"• {ema_desc}.")
            
            # Support/Resistance пробой
            breakout = indicators.get('support_resistance', {}).get('breakout', '')
            if 'пробит' in breakout:
                explanations.append(f"• {breakout}.")
            
            # Мультитаймфрейм анализ
            explanations.append("• Пробитый на 15-минутном графике уровень поддержки был повторно протестирован на 5-минутном графике и выступил в качестве поддержки.")
            
            # Bollinger Bands
            bb_desc = indicators.get('bollinger', {}).get('description', '')
            if bb_desc and 'пробила' in bb_desc:
                explanations.append(f"• {bb_desc}.")
            
            # MA50 пересечение
            ma50_cross = indicators.get('ema', {}).get('ma50_cross', '')
            if ma50_cross:
                explanations.append(f"• {ma50_cross}.")
            
            # ADX сила тренда
            adx_desc = indicators.get('adx', {}).get('description', '')
            if adx_desc:
                explanations.append(f"• {adx_desc}.")
            
            # Volume анализ
            volume_desc = indicators.get('volume_analysis', {}).get('description', '')
            if volume_desc and 'Рост объёма' in volume_desc:
                explanations.append(f"• {volume_desc}")
            
            # Candlestick паттерны
            patterns = indicators.get('patterns', {}).get('patterns', [])
            for pattern in patterns:
                if 'Обнаружен' in pattern:
                    explanations.append(f"• {pattern}.")
            
            # MTF подтверждение
            mtf_desc = indicators.get('mtf_consensus', {}).get('description', '')
            if 'положительное' in mtf_desc or 'отрицательное' in mtf_desc:
                explanations.append(f"• {mtf_desc}.")
            
            return explanations
            
        except Exception as e:
            logger.error(f"❌ Error generating explanations: {e}")
            return ["• Анализ недоступен"]
    
    def _generate_warnings(self, indicators: Dict, timeframe_data: Dict) -> List[str]:
        """Генерация предупреждений как в примере"""
        warnings = []
        
        try:
            # Support/Resistance предупреждения
            sr_warnings = indicators.get('support_resistance', {}).get('warnings', [])
            warnings.extend([f"❗️{w}" for w in sr_warnings])
            
            # Таймфрейм несовместимость
            if len(timeframe_data) >= 2:
                warnings.append("❗️Таймфреймы несовместимы (5–15 минут).")
            
            # Stochastic RSI предупреждение
            stoch_desc = indicators.get('stochastic', {}).get('description', '')
            if 'Слабое подтверждение' in stoch_desc:
                warnings.append(f"❗️{stoch_desc}.")
            
            # SuperTrend предупреждение
            supertrend_desc = indicators.get('supertrend', {}).get('description', '')
            if 'медвежий' in supertrend_desc:
                warnings.append(f"{supertrend_desc}")
            
            # MTF Consensus предупреждение
            mtf_consensus = indicators.get('mtf_consensus', {}).get('consensus', '')
            if 'sell' in mtf_consensus:
                warnings.append(f"MTF Consensus == \"{mtf_consensus}\"")
            
            # VWAP предупреждение
            vwap_desc = indicators.get('vwap', {}).get('description', '')
            if 'Price < VWAP' in vwap_desc:
                warnings.append(vwap_desc)
            
            # Volume предупреждение
            volume_desc = indicators.get('volume_analysis', {}).get('description', '')
            if 'Нет Volume Spike' in volume_desc:
                warnings.append(volume_desc)
            
            # Donchian предупреждение
            donchian_desc = indicators.get('donchian', {}).get('description', '')
            if 'Price < Donchian Mid' in donchian_desc:
                warnings.append(donchian_desc)
            
            return warnings
            
        except Exception as e:
            logger.error(f"❌ Error generating warnings: {e}")
            return []

class DetailedTelegramBot:
    """Telegram бот для отправки детальных сигналов"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_CONFIG['bot_token']
        self.chat_id = TELEGRAM_CONFIG['chat_id']
        self.admin_chat_id = TELEGRAM_CONFIG.get('admin_chat_id', self.chat_id)
        
    async def send_detailed_signal(self, signal: Dict) -> bool:
        """Отправка детального сигнала как в примере"""
        try:
            message = self._format_detailed_signal(signal)
            return await self._send_message(message)
        except Exception as e:
            logger.error(f"❌ Error sending signal: {e}")
            return False
    
    def _format_detailed_signal(self, signal: Dict) -> str:
        """Форматирование детального сигнала точно как в примере"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            entry_price = signal['entry_price']
            tp1 = signal['tp1']
            tp2 = signal['tp2']
            tp3 = signal['tp3']
            tp4 = signal['tp4']
            stop_loss = signal['stop_loss']
            leverage = signal['leverage']
            confidence = signal['confidence']
            timestamp = signal['timestamp']
            explanations = signal['explanations']
            warnings = signal['warnings']
            
            position_type = "ДЛИННУЮ ПОЗИЦИЮ" if action == 'BUY' else "КОРОТКУЮ ПОЗИЦИЮ"
            emoji = "🚀" if action == 'BUY' else "📉"
            
            # Основная информация
            message = f"СИГНАЛ НА {position_type} по {symbol} {emoji}\n\n"
            message += f"💰 Цена входа: ${entry_price:.6f}\n\n"
            
            # Take Profit уровни
            message += f"🎯 TP1: ${tp1:.6f}\n"
            message += f"🎯 TP2: ${tp2:.6f}\n"
            message += f"🎯 TP3: ${tp3:.6f}\n"
            message += f"🎯 TP4: ${tp4:.6f}\n\n"
            
            # Stop Loss
            message += f"🛑 Стоп-лосс: ${stop_loss:.6f}\n"
            
            # Плечо и уровень успеха
            message += f"Плечо ; {leverage} Х\n"
            message += f"📊 Уровень успеха: {confidence*100:.0f}%\n"
            message += f"🕒 Время: {timestamp}\n\n"
            
            # Объяснение сигнала
            message += f"🔎 Почему сигнал на {'длинную' if action == 'BUY' else 'короткую'} позицию ❓\n\n"
            message += "Подробности сделки 👇\n\n"
            
            # Детальные объяснения
            for explanation in explanations:
                message += f"{explanation}\n"
            
            # Предупреждения
            if warnings:
                for warning in warnings:
                    message += f"{warning}\n"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting signal: {e}")
            return f"❌ Ошибка форматирования сигнала для {signal.get('symbol', 'UNKNOWN')}"
    
    async def _send_message(self, message: str) -> bool:
        """Отправка сообщения в Telegram"""
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'disable_web_page_preview': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('ok', False)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Telegram send error: {e}")
            return False

class ProfessionalDetailedBot:
    """Главный класс профессионального детального бота"""
    
    def __init__(self):
        self.signal_generator = DetailedSignalGenerator()
        self.telegram_bot = DetailedTelegramBot()
        self.running = False
        
        # Конфигурация
        self.pairs = TRADING_CONFIG['pairs'][:50]  # Первые 50 пар
        self.min_confidence = 0.8  # Минимальная уверенность 80%
        self.update_frequency = 300  # 5 минут
        
        # Статистика
        self.stats = {
            'cycles': 0,
            'signals_generated': 0,
            'signals_sent': 0,
            'start_time': time.time()
        }
        
        logger.info("🤖 Professional Detailed Bot инициализирован")
    
    async def start_analysis_loop(self):
        """Основной цикл анализа"""
        logger.info("🚀 Запуск детального анализа...")
        
        while self.running:
            try:
                self.stats['cycles'] += 1
                cycle_start = time.time()
                
                logger.info(f"📊 Цикл #{self.stats['cycles']}: Детальный анализ {len(self.pairs)} пар...")
                
                # Анализируем пары пакетами
                batch_size = 5  # Меньший размер для детального анализа
                quality_signals = []
                
                for i in range(0, len(self.pairs), batch_size):
                    batch = self.pairs[i:i+batch_size]
                    batch_signals = await self._analyze_batch(batch)
                    quality_signals.extend(batch_signals)
                    
                    # Пауза между пакетами
                    await asyncio.sleep(2)
                
                # Фильтруем по уверенности
                high_confidence_signals = [s for s in quality_signals if s['confidence'] >= self.min_confidence]
                
                # Сортируем по уверенности и берем топ-3
                high_confidence_signals.sort(key=lambda x: x['confidence'], reverse=True)
                top_signals = high_confidence_signals[:3]
                
                # Отправляем сигналы
                for signal in top_signals:
                    success = await self.telegram_bot.send_detailed_signal(signal)
                    if success:
                        self.stats['signals_sent'] += 1
                        logger.info(f"📤 Детальный сигнал {signal['symbol']} отправлен")
                    
                    await asyncio.sleep(3)  # Пауза между отправками
                
                self.stats['signals_generated'] += len(quality_signals)
                
                cycle_time = time.time() - cycle_start
                logger.info(f"⏱️ Цикл завершен за {cycle_time:.1f}с. Найдено: {len(quality_signals)}, отправлено: {len(top_signals)}")
                
                # Ждем до следующего цикла
                await asyncio.sleep(self.update_frequency)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_batch(self, pairs_batch: List[str]) -> List[Dict]:
        """Анализ пакета пар"""
        signals = []
        
        tasks = []
        for pair in pairs_batch:
            task = self.signal_generator.analyze_and_generate_signal(pair)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for pair, result in zip(pairs_batch, results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Ошибка анализа {pair}: {result}")
                continue
                
            if result:
                signals.append(result)
        
        return signals
    
    def start(self):
        """Запуск бота"""
        self.running = True
        logger.info("🚀 Запуск Professional Detailed Bot...")
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self._run_async_loop, daemon=True)
        thread.start()
        
        return thread
    
    def stop(self):
        """Остановка бота"""
        self.running = False
        logger.info("🛑 Professional Detailed Bot остановлен")
    
    def _run_async_loop(self):
        """Запуск async loop в отдельном потоке"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_analysis_loop())
        loop.close()

# Главная функция
async def main():
    """Главная функция"""
    bot = ProfessionalDetailedBot()
    
    try:
        # Отправляем стартовое сообщение
        await bot.telegram_bot._send_message(
            "🚀 **PROFESSIONAL DETAILED SIGNAL BOT v6.0 STARTED**\n\n"
            "✅ Детальные профессиональные сигналы\n"
            "✅ Полный технический анализ\n"
            "✅ Реальные данные с бирж\n"
            "✅ Минимальная уверенность: 80%\n\n"
            "📊 Анализ начат..."
        )
        
        # Устанавливаем флаг запуска
        bot.running = True
        
        # Запускаем анализ
        await bot.start_analysis_loop()
        
    except KeyboardInterrupt:
        logger.info("🛑 Завершение работы...")
    finally:
        bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Программа завершена пользователем") 