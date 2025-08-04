#!/usr/bin/env python3
"""
Test Telegram - Тестирование Telegram интеграции
"""

import asyncio
import logging
from datetime import datetime

from telegram_integration import TelegramIntegration
from config import TELEGRAM_CONFIG

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_integration():
    """Тестирует интеграцию с Telegram"""
    print("🧪 Тестирование Telegram интеграции")
    print("=" * 50)
    
    # Проверяем настройки
    print(f"📱 Токен бота: {TELEGRAM_CONFIG['bot_token']}")
    print(f"💬 Chat ID: {TELEGRAM_CONFIG['chat_id']}")
    print(f"✅ Telegram включен: {TELEGRAM_CONFIG['enable_telegram']}")
    print()
    
    if TELEGRAM_CONFIG['bot_token'] == 'YOUR_TELEGRAM_BOT_TOKEN':
        print("❌ Токен бота не настроен!")
        print("💡 Запустите: python setup_telegram.py")
        return False
    
    if TELEGRAM_CONFIG['chat_id'] == 'YOUR_CHAT_ID':
        print("❌ Chat ID не настроен!")
        print("💡 Запустите: python setup_telegram.py")
        return False
    
    # Создаем интеграцию
    telegram = TelegramIntegration()
    
    try:
        # Тест 1: Простое сообщение
        print("📤 Тест 1: Отправка простого сообщения...")
        test_message = f"🧪 Тестовое сообщение от CryptoAlphaPro Bot\nВремя: {datetime.now().strftime('%H:%M:%S')}"
        success = await telegram.send_message(test_message)
        
        if success:
            print("✅ Простое сообщение отправлено!")
        else:
            print("❌ Ошибка отправки простого сообщения")
            return False
        
        # Тест 2: Статус бота
        print("\n📤 Тест 2: Отправка статуса бота...")
        status = {
            'running': True,
            'signal_count': 42,
            'cycle_count': 15,
            'last_signal_time_str': '14:30:25',
            'pairs_count': 343,
            'timeframes_count': 4,
            'min_confidence': 0.3,
            'top_signals': 10,
            'update_frequency': 300
        }
        
        success = await telegram.send_status_update(status)
        
        if success:
            print("✅ Статус бота отправлен!")
        else:
            print("❌ Ошибка отправки статуса")
            return False
        
        # Тест 3: Торговый сигнал
        print("\n📤 Тест 3: Отправка торгового сигнала...")
        test_signal = {
            'action': 'BUY',
            'symbol': 'BTC/USDT',
            'price': 43250.50,
            'confidence': 0.85,
            'alpha_score': 6,
            'risk_reward': 2.5,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'take_profit': [43500.00, 43800.00, 44100.00],
            'stop_loss': 42900.00,
            'analysis': {
                'rsi': 35.2,
                'macd': {'histogram': 0.025},
                'adx': {'adx': 28.5},
                'volume': {'ratio': 1.8}
            },
            'consensus_score': 0.75,
            'trend_agreement': 0.65
        }
        
        success = await telegram.send_signal(test_signal)
        
        if success:
            print("✅ Торговый сигнал отправлен!")
        else:
            print("❌ Ошибка отправки сигнала")
            return False
        
        # Тест 4: Ошибка
        print("\n📤 Тест 4: Отправка ошибки...")
        test_error = "Тестовая ошибка для проверки системы уведомлений"
        success = await telegram.send_error(test_error)
        
        if success:
            print("✅ Сообщение об ошибке отправлено!")
        else:
            print("❌ Ошибка отправки сообщения об ошибке")
            return False
        
        print("\n🎉 Все тесты пройдены успешно!")
        print("📱 Telegram интеграция работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    finally:
        await telegram.__aexit__(None, None, None)

async def test_signal_formatting():
    """Тестирует форматирование сигналов"""
    print("\n📝 Тестирование форматирования сигналов...")
    
    telegram = TelegramIntegration()
    
    # Тестовые сигналы
    test_signals = [
        {
            'action': 'BUY',
            'symbol': 'ETH/USDT',
            'price': 2650.75,
            'confidence': 0.92,
            'alpha_score': 7,
            'risk_reward': 3.2,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'take_profit': [2680.00, 2710.00, 2740.00],
            'stop_loss': 2620.00,
            'analysis': {
                'rsi': 28.5,
                'macd': {'histogram': 0.035},
                'adx': {'adx': 32.1},
                'volume': {'ratio': 2.1}
            },
            'consensus_score': 0.88,
            'trend_agreement': 0.72
        },
        {
            'action': 'SELL',
            'symbol': 'SOL/USDT',
            'price': 98.45,
            'confidence': 0.78,
            'alpha_score': 5,
            'risk_reward': 2.1,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'take_profit': [96.00, 94.50, 93.00],
            'stop_loss': 101.00,
            'analysis': {
                'rsi': 72.8,
                'macd': {'histogram': -0.018},
                'adx': {'adx': 25.3},
                'volume': {'ratio': 1.5}
            },
            'consensus_score': 0.65,
            'trend_agreement': 0.58
        }
    ]
    
    for i, signal in enumerate(test_signals, 1):
        print(f"\n📊 Тестовый сигнал #{i}:")
        formatted = telegram._format_signal_for_telegram(signal)
        print(formatted)
        print("-" * 50)

async def main():
    """Главная функция"""
    print("🚀 CryptoAlphaPro Bot - Тестирование Telegram")
    print("=" * 60)
    
    # Основные тесты
    success = await test_telegram_integration()
    
    if success:
        # Тестируем форматирование (без отправки)
        await test_signal_formatting()
        
        print("\n✅ Все тесты завершены!")
        print("🎯 Telegram готов к работе с ботом")
    else:
        print("\n❌ Тесты не пройдены!")
        print("🔧 Проверьте настройки Telegram")

if __name__ == "__main__":
    asyncio.run(main()) 