#!/usr/bin/env python3
"""
Universal Crypto Alpha Bot - Основной бот с Telegram интеграцией
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

from universal_data_manager import UniversalDataManager
from advanced_ai_engine import AdvancedAIEngine
from signal_explainer import SignalExplainer
from telegram_integration import TelegramIntegration
from config import TRADING_CONFIG, ANALYSIS_CONFIG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_alpha_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UniversalCryptoAlphaBot:
    """Основной бот с системой 'Best Alpha Only' и Telegram интеграцией"""
    
    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self.signal_count = 0
        self.last_signal_time = None
        self.last_signal_time_str = "Нет"
        
        # Конфигурация
        self.config = {
            'trading': TRADING_CONFIG,
            'analysis': ANALYSIS_CONFIG
        }
        
        # Инициализация компонентов
        self.data_manager = UniversalDataManager()
        self.ai_engine = AdvancedAIEngine(self.config)
        self.signal_explainer = SignalExplainer()
        self.telegram = TelegramIntegration()
        
        # Конфигурация
        self.pairs = TRADING_CONFIG['pairs']
        self.timeframes = TRADING_CONFIG['timeframes']
        self.update_frequency = TRADING_CONFIG['update_frequency']
        self.min_confidence = TRADING_CONFIG['min_confidence']
        self.top_signals = TRADING_CONFIG['top_signals']
        
        logger.info(f"🤖 CryptoAlphaPro Bot инициализирован")
        logger.info(f"📊 Пар для анализа: {len(self.pairs)}")
        logger.info(f"⏱️ Таймфреймы: {self.timeframes}")
        logger.info(f"🎯 Минимальная уверенность: {self.min_confidence*100:.0f}%")
        logger.info(f"🎯 Топ сигналов: {self.top_signals}")
        logger.info(f"⏰ Частота обновления: {self.update_frequency} сек")
    
    async def start(self):
        """Запускает бота"""
        if self.running:
            logger.warning("⚠️ Бот уже запущен!")
            return
        
        self.running = True
        logger.info("🚀 Бот запущен!")
        
        # Отправляем статус в Telegram
        await self._send_status_update()
        
        try:
            await self.batch_top_signals_loop()
        except Exception as e:
            logger.error(f"❌ Ошибка в основном цикле: {e}")
            await self.telegram.send_error(f"Ошибка в основном цикле: {e}")
        finally:
            self.running = False
            logger.info("🛑 Бот остановлен")
    
    async def stop(self):
        """Останавливает бота"""
        self.running = False
        logger.info("🛑 Остановка бота...")
    
    async def batch_top_signals_loop(self):
        """Основной цикл обработки сигналов с отправкой в Telegram"""
        logger.info("🔄 Запуск основного цикла обработки сигналов...")
        
        while self.running:
            try:
                cycle_start = time.time()
                self.cycle_count += 1
                
                logger.info(f"🔄 Цикл #{self.cycle_count} - Анализ {len(self.pairs)} пар...")
                
                # Получаем топ сигналы
                top_signals = await self._process_and_collect_signals()
                
                # Отправляем сигналы в Telegram
                if top_signals:
                    logger.info(f"📤 Отправка {len(top_signals)} сигналов в Telegram...")
                    for signal in top_signals:
                        await self._send_signal_to_telegram(signal)
                        self.signal_count += 1
                        self.last_signal_time = datetime.now()
                        self.last_signal_time_str = self.last_signal_time.strftime("%H:%M:%S")
                else:
                    logger.info("📭 Сигналов не найдено")
                
                # Отправляем статус каждые 10 циклов
                if self.cycle_count % 10 == 0:
                    await self._send_status_update()
                
                cycle_time = time.time() - cycle_start
                logger.info(f"✅ Цикл #{self.cycle_count} завершен за {cycle_time:.2f} сек")
                
                # Ждем до следующего цикла
                await asyncio.sleep(self.update_frequency)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле #{self.cycle_count}: {e}")
                await self.telegram.send_error(f"Ошибка в цикле #{self.cycle_count}: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед повтором
    
    async def _process_and_collect_signals(self) -> List[Dict[str, Any]]:
        """Обрабатывает пары и собирает топ сигналы"""
        all_signals = []
        errors = 0
        
        async def analyze_pair(pair):
            try:
                # Получаем данные по всем таймфреймам
                ohlcv_data = await self.data_manager.get_multi_timeframe_data(pair, self.timeframes)
                if not ohlcv_data:
                    return None
                
                # Генерируем сигнал
                signal = await self.ai_engine.process_symbol(pair, ohlcv_data)
                if signal and signal.get('action') in ('BUY', 'SELL'):
                    # Патчинг confidence
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
                    
                    # Добавляем объяснение
                    if 'analysis' in signal:
                        try:
                            explanation = self.signal_explainer.explain_signal(
                                signal, 
                                signal['analysis'],
                                signal.get('mtf_analysis')
                            )
                            signal['explanation'] = explanation
                        except Exception as e:
                            logger.error(f"❌ Ошибка объяснения сигнала {pair}: {e}")
                            signal['explanation'] = "Объяснение недоступно"
                    
                    return signal
                return None
                
            except Exception as e:
                logger.error(f"❌ Ошибка анализа {pair}: {e}")
                nonlocal errors
                errors += 1
                return None
        
        # Асинхронный анализ всех пар
        tasks = [analyze_pair(pair) for pair in self.pairs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные сигналы
        signals_ok = []
        for result in results:
            if isinstance(result, Exception):
                errors += 1
            elif result is not None:
                signals_ok.append(result)
        
        # Отбор только лучших TOP-N сигналов
        filtered = [s for s in signals_ok if s['confidence'] >= self.min_confidence]
        filtered = sorted(filtered, key=lambda x: x['confidence'], reverse=True)[:self.top_signals]
        
        logger.info(f"📊 Всего пар: {len(self.pairs)}. Сработало сигналов: {len(signals_ok)}. "
                   f"Среди лучших (conf>={self.min_confidence}): {len(filtered)}. Ошибок: {errors}")
        
        for sig in filtered:
            logger.info(f"🎯 {sig['symbol']} {sig['action']} conf={sig['confidence']:.3f} "
                       f"price={sig.get('price', 0):.6f}")
        
        return filtered
    
    async def _send_signal_to_telegram(self, signal: Dict[str, Any]):
        """Отправляет сигнал в Telegram"""
        try:
            success = await self.telegram.send_signal(signal)
            if success:
                logger.info(f"📤 Сигнал {signal['symbol']} отправлен в Telegram")
            else:
                logger.warning(f"⚠️ Не удалось отправить сигнал {signal['symbol']} в Telegram")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сигнала в Telegram: {e}")
    
    async def _send_status_update(self):
        """Отправляет статус бота в Telegram"""
        try:
            status = {
                'running': self.running,
                'signal_count': self.signal_count,
                'cycle_count': self.cycle_count,
                'last_signal_time_str': self.last_signal_time_str,
                'pairs_count': len(self.pairs),
                'timeframes_count': len(self.timeframes),
                'min_confidence': self.min_confidence,
                'top_signals': self.top_signals,
                'update_frequency': self.update_frequency
            }
            
            success = await self.telegram.send_status_update(status)
            if success:
                logger.info("📤 Статус отправлен в Telegram")
            else:
                logger.warning("⚠️ Не удалось отправить статус в Telegram")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки статуса в Telegram: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус бота"""
        return {
            'running': self.running,
            'signal_count': self.signal_count,
            'cycle_count': self.cycle_count,
            'last_signal_time_str': self.last_signal_time_str,
            'pairs_count': len(self.pairs),
            'timeframes_count': len(self.timeframes),
            'min_confidence': self.min_confidence,
            'top_signals': self.top_signals,
            'update_frequency': self.update_frequency
        }

async def main():
    """Главная функция"""
    bot = UniversalCryptoAlphaBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
        await bot.stop()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        await bot.telegram.send_error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 