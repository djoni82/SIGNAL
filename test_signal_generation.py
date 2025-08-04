#!/usr/bin/env python3
"""
Test Signal Generation - Тестирование генерации сигналов
"""

import asyncio
import logging
from universal_data_manager import UniversalDataManager
from advanced_ai_engine import AdvancedAIEngine

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_signal_generation():
    """Тестирует генерацию сигналов"""
    
    # Конфигурация с очень мягкими порогами для тестирования
    config = {
        'analysis': {
            'min_confidence': 0.3,  # 30% для тестирования
            'min_risk_reward': 1.0,  # 1.0 для тестирования
            'max_signals_per_cycle': 5
        }
    }
    
    # Инициализируем компоненты
    data_manager = UniversalDataManager()
    ai_engine = AdvancedAIEngine(config)
    
    # Тестовые пары (меньше для быстрого тестирования)
    test_pairs = [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
        'DOT/USDT', 'LINK/USDT', 'MATIC/USDT', 'AVAX/USDT', 'ATOM/USDT'
    ]
    
    timeframes = ['15m', '1h', '4h']
    
    logger.info("🧪 Начинаем тестирование генерации сигналов...")
    logger.info(f"📊 Тестовые пары: {len(test_pairs)}")
    logger.info(f"⏱️ Таймфреймы: {timeframes}")
    logger.info(f"🎯 Минимальная уверенность: {config['analysis']['min_confidence']*100:.0f}%")
    
    try:
        async with data_manager:
            # Получаем сигналы
            signals = await ai_engine.process_and_collect_signals(
                test_pairs,
                timeframes,
                data_manager,
                min_confidence=config['analysis']['min_confidence'],
                top_n=5
            )
            
            logger.info(f"✅ Тестирование завершено!")
            logger.info(f"📈 Найдено сигналов: {len(signals)}")
            
            if signals:
                logger.info("🎯 Найденные сигналы:")
                for i, signal in enumerate(signals, 1):
                    logger.info(f"  {i}. {signal['symbol']} {signal['action']} "
                              f"conf={signal['confidence']:.3f} "
                              f"alpha={signal['alpha_score']} "
                              f"rr={signal['risk_reward']:.2f}")
            else:
                logger.info("📭 Сигналы не найдены")
                
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")

async def main():
    """Основная функция"""
    await test_signal_generation()

if __name__ == "__main__":
    asyncio.run(main()) 