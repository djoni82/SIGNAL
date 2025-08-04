#!/usr/bin/env python3
"""
Enhanced Signal Bot with Detailed Explanations
Продвинутый бот сигналов с детальными объяснениями
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from signal_explainer import SignalExplainer
from advanced_technical_analyzer import AdvancedTechnicalAnalyzer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedSignalBot:
    """Продвинутый бот сигналов с детальными объяснениями"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.explainer = SignalExplainer()
        self.analyzer = AdvancedTechnicalAnalyzer()
        self.last_signal_time = 0
        self.signal_count = 0
        
        # Настройки сигналов
        self.signal_config = config.get('signals', {})
        self.min_confidence = self.signal_config.get('min_confidence', 0.3)
        self.signal_interval = self.signal_config.get('interval', 300)  # 5 минут
        
        # Список торговых пар
        self.trading_pairs = config.get('trading_pairs', [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
            'DOT/USDT', 'LINK/USDT', 'MATIC/USDT', 'AVAX/USDT', 'ATOM/USDT'
        ])
        
        logger.info(f"🚀 Enhanced Signal Bot инициализирован с {len(self.trading_pairs)} парами")
    
    async def start(self):
        """Запускает бота"""
        self.running = True
        logger.info("🚀 Бот запущен")
        
        while self.running:
            try:
                await self.run_single_cycle()
                await asyncio.sleep(self.signal_config.get('cycle_interval', 60))
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле бота: {e}")
                await asyncio.sleep(10)
    
    async def stop(self):
        """Останавливает бота"""
        self.running = False
        logger.info("🛑 Бот остановлен")
    
    async def run_single_cycle(self):
        """Выполняет один цикл анализа"""
        logger.info("🔄 Начинаю цикл анализа...")
        
        for pair in self.trading_pairs:
            try:
                await self.analyze_pair(pair)
                await asyncio.sleep(1)  # Небольшая пауза между парами
            except Exception as e:
                logger.error(f"❌ Ошибка анализа {pair}: {e}")
    
    async def analyze_pair(self, pair: str):
        """Анализирует одну торговую пару"""
        try:
            # Получаем данные (симуляция)
            data = await self.get_market_data(pair)
            if data is None or len(data) < 50:
                return
            
            # Анализируем данные
            analysis = self.analyzer._analyze_single_timeframe(data)
            
            # Добавляем уровни поддержки и сопротивления
            support_resistance = self.analyzer.calculate_support_resistance(data)
            analysis.update(support_resistance)
            
            # Генерируем сигнал
            signal = self.generate_signal(pair, data, analysis)
            
            if signal and signal.get('action') not in ['HOLD', 'SKIP']:
                # Проверяем интервал между сигналами
                current_time = time.time()
                if current_time - self.last_signal_time >= self.signal_interval:
                    await self.send_signal(signal, analysis)
                    self.last_signal_time = current_time
                    self.signal_count += 1
                    
        except Exception as e:
            logger.error(f"❌ Ошибка анализа {pair}: {e}")
    
    async def get_market_data(self, pair: str) -> Optional[pd.DataFrame]:
        """Получает рыночные данные (симуляция)"""
        try:
            # Создаем симулированные данные
            dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
            
            # Создаем реалистичные данные с трендом
            base_price = 0.378300 if 'M/' in pair else 50000 if 'BTC' in pair else 3000
            trend = np.linspace(0, 0.02, 100)
            noise = np.random.normal(0, base_price * 0.001, 100)
            
            prices = base_price + trend + noise
            
            # Создаем OHLC данные
            data = []
            for i, (date, price) in enumerate(zip(dates, prices)):
                open_price = price
                high_price = price + abs(np.random.normal(0, price * 0.002))
                low_price = price - abs(np.random.normal(0, price * 0.002))
                close_price = price + np.random.normal(0, price * 0.001)
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
            logger.error(f"❌ Ошибка получения данных для {pair}: {e}")
            return None
    
    def generate_signal(self, pair: str, data: pd.DataFrame, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Генерирует торговый сигнал"""
        try:
            current_price = data['close'].iloc[-1]
            
            # Анализируем индикаторы
            rsi = analysis.get('rsi', 50)
            macd_hist = analysis.get('macd', {}).get('histogram', 0)
            adx = analysis.get('adx', {}).get('adx', 0)
            volume_ratio = analysis.get('volume', {}).get('ratio', 1.0)
            
            # Определяем действие
            action = 'HOLD'
            confidence = 0.5
            
            # RSI анализ
            if rsi > 70:
                action = 'SELL'
                confidence += 0.2
            elif rsi < 30:
                action = 'BUY'
                confidence += 0.2
            
            # MACD анализ
            if macd_hist > 0.01:
                if action == 'BUY':
                    confidence += 0.15
                elif action == 'HOLD':
                    action = 'BUY'
                    confidence += 0.15
            elif macd_hist < -0.01:
                if action == 'SELL':
                    confidence += 0.15
                elif action == 'HOLD':
                    action = 'SELL'
                    confidence += 0.15
            
            # ADX анализ (сила тренда)
            if adx > 25:
                confidence += 0.1
            
            # Volume анализ
            if volume_ratio > 1.5:
                confidence += 0.1
            
            # Проверяем минимальную уверенность
            if confidence < self.min_confidence:
                action = 'HOLD'
                confidence = 0.5
            
            # Создаем сигнал
            signal = {
                'action': action,
                'symbol': pair,
                'price': current_price,
                'confidence': min(confidence, 0.95),
                'take_profit': self.explainer.calculate_take_profit_levels(current_price, 'long' if action == 'BUY' else 'short'),
                'stop_loss': self.explainer.calculate_stop_loss(current_price, 'long' if action == 'BUY' else 'short')
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сигнала для {pair}: {e}")
            return None
    
    async def send_signal(self, signal: Dict[str, Any], analysis: Dict[str, Any]):
        """Отправляет сигнал с детальным объяснением"""
        try:
            # Создаем мультитаймфреймовый анализ
            mtf_analysis = {
                'timeframes': {
                    '15m': {'trend': 'bullish' if signal['action'] == 'BUY' else 'bearish'},
                    '1h': {'trend': 'bullish' if signal['action'] == 'BUY' else 'bearish'},
                    '4h': {'trend': 'neutral'}
                },
                'overall_trend': 'bullish' if signal['action'] == 'BUY' else 'bearish'
            }
            
            # Генерируем детальное сообщение
            message = self.explainer.format_signal_message(signal, analysis, mtf_analysis)
            
            # Добавляем статистику
            message += f"\n📈 Статистика бота:\n"
            message += f"• Всего сигналов: {self.signal_count}\n"
            message += f"• Последний сигнал: {datetime.now().strftime('%H:%M:%S')}\n"
            message += f"• Уверенность: {signal['confidence']*100:.0f}%\n"
            
            # Отправляем сообщение (симуляция)
            logger.info(f"📤 Отправляю сигнал для {signal['symbol']}:")
            print("\n" + "="*60)
            print(message)
            print("="*60 + "\n")
            
            # Здесь можно добавить отправку в Telegram
            # await self.telegram_bot.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сигнала: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус бота"""
        return {
            'running': self.running,
            'signal_count': self.signal_count,
            'last_signal_time': self.last_signal_time,
            'trading_pairs': len(self.trading_pairs),
            'min_confidence': self.min_confidence
        }

async def main():
    """Основная функция"""
    # Конфигурация
    config = {
        'signals': {
            'min_confidence': 0.3,
            'interval': 300,  # 5 минут между сигналами
            'cycle_interval': 60  # 1 минута между циклами
        },
        'trading_pairs': [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
            'DOT/USDT', 'LINK/USDT', 'MATIC/USDT', 'AVAX/USDT', 'ATOM/USDT'
        ]
    }
    
    # Создаем и запускаем бота
    bot = EnhancedSignalBot(config)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
        await bot.stop()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main()) 