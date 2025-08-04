#!/usr/bin/env python3
"""
Тест Telegram отправки сигналов для Alpha Signal Bot
"""

import asyncio
from alpha_signal_bot import TelegramBot, format_signal_for_telegram, explain_signal

async def test_telegram_connection():
    """Тест подключения к Telegram"""
    print("🔍 Тестирование подключения к Telegram...")
    
    telegram = TelegramBot()
    
    # Тестовое сообщение
    test_message = "🧪 **ТЕСТ ALPHA SIGNAL BOT**\n\n"
    test_message += "✅ Подключение к Telegram работает\n"
    test_message += "🤖 Бот готов к отправке сигналов\n"
    test_message += "📊 Система 'Best Alpha Only' активна"
    
    result = await telegram.send_message(test_message)
    
    if result:
        print("✅ Telegram подключение работает!")
        return True
    else:
        print("❌ Ошибка подключения к Telegram")
        return False

async def test_signal_formatting():
    """Тест форматирования сигналов"""
    print("\n🔍 Тестирование форматирования сигналов...")
    
    # Тестовый сигнал
    test_signal = {
        'symbol': 'BTC/USDT',
        'action': 'BUY',
        'entry_price': 50000.0,
        'confidence': 0.85,
        'analysis': {
            'rsi': 65.5,
            'macd': {
                'macd': 0.002,
                'signal': 0.001,
                'histogram': 0.001
            },
            'ema_20': 50100.0,
            'ema_50': 49900.0,
            'bb_upper': 50200.0,
            'bb_lower': 49800.0,
            'ma_50': 50050.0,
            'adx': 28.5,
            'volume_ratio': 1.8,
            'price': 50000.0
        },
        'mtf_analysis': {
            '15m': {'rsi': 65, 'price': 50000},
            '1h': {'rsi': 62, 'price': 50000},
            '4h': {'rsi': 58, 'price': 50000}
        }
    }
    
    # Форматируем сигнал
    formatted_message = format_signal_for_telegram(test_signal)
    
    print("📝 Отформатированное сообщение:")
    print("=" * 50)
    print(formatted_message)
    print("=" * 50)
    
    return formatted_message

async def test_signal_sending():
    """Тест отправки сигнала"""
    print("\n🔍 Тестирование отправки сигнала...")
    
    telegram = TelegramBot()
    
    # Создаем тестовый сигнал
    test_signal = {
        'symbol': 'ETH/USDT',
        'action': 'SELL',
        'entry_price': 3200.0,
        'confidence': 0.82,
        'analysis': {
            'rsi': 35.2,
            'macd': {
                'macd': -0.003,
                'signal': -0.001,
                'histogram': -0.002
            },
            'ema_20': 3180.0,
            'ema_50': 3220.0,
            'bb_upper': 3250.0,
            'bb_lower': 3150.0,
            'ma_50': 3210.0,
            'adx': 32.1,
            'volume_ratio': 2.1,
            'price': 3200.0
        },
        'mtf_analysis': {
            '15m': {'rsi': 35, 'price': 3200},
            '1h': {'rsi': 38, 'price': 3200},
            '4h': {'rsi': 42, 'price': 3200}
        }
    }
    
    # Форматируем и отправляем
    message = format_signal_for_telegram(test_signal)
    result = await telegram.send_message(message)
    
    if result:
        print("✅ Тестовый сигнал отправлен в Telegram!")
        return True
    else:
        print("❌ Ошибка отправки тестового сигнала")
        return False

async def test_explanation_function():
    """Тест функции объяснения сигналов"""
    print("\n🔍 Тестирование функции объяснения...")
    
    # Тестовые данные
    signal = {'action': 'BUY'}
    analysis = {
        'rsi': 82.49,
        'macd': {'histogram': 0.008},
        'ema_20': 0.38,
        'ema_50': 0.37,
        'bb_upper': 0.39,
        'bb_lower': 0.36,
        'ma_50': 0.375,
        'adx': 28.5,
        'volume_ratio': 1.5,
        'price': 0.3783
    }
    mtf_analysis = {
        '15m': {'rsi': 82, 'price': 0.3783},
        '1h': {'rsi': 78, 'price': 0.3783},
        '4h': {'rsi': 75, 'price': 0.3783}
    }
    
    explanation = explain_signal(signal, analysis, mtf_analysis)
    
    print("📝 Объяснение сигнала:")
    print("=" * 50)
    print(explanation)
    print("=" * 50)
    
    return explanation

async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ALPHA SIGNAL BOT")
    print("=" * 60)
    
    # Тест 1: Подключение к Telegram
    telegram_ok = await test_telegram_connection()
    
    # Тест 2: Форматирование сигналов
    await test_signal_formatting()
    
    # Тест 3: Функция объяснения
    await test_explanation_function()
    
    # Тест 4: Отправка сигнала
    if telegram_ok:
        await test_signal_sending()
    
    print("\n✅ Тестирование завершено!")
    print("🤖 Бот готов к работе!")

if __name__ == "__main__":
    asyncio.run(main()) 