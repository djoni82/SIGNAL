#!/usr/bin/env python3
"""
🧪 ТЕСТ СКАЛЬПИНГА - ОТЛАДКА ПРОБЛЕМЫ
"""

import asyncio
from scalping_engine import ScalpingSignalEngine
from alpha_signal_bot_main import UniversalDataManager

async def test_scalping_debug():
    print('🧪 ДИАГНОСТИКА СКАЛЬПИНГ МОДУЛЯ')
    print('=' * 50)
    
    # Тест 1: Экстремально мягкие настройки
    print('\n🔥 ТЕСТ 1: ЭКСТРЕМАЛЬНО МЯГКИЕ НАСТРОЙКИ')
    scalping_engine = ScalpingSignalEngine(min_confidence=0.10, min_filters=1)
    data_manager = UniversalDataManager()
    
    # Тестируем топ-5 самых волатильных пар
    test_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'DOGE/USDT']
    
    found_signals = 0
    
    for symbol in test_pairs:
        try:
            print(f'\n🔍 Анализ {symbol}:')
            
            # Получаем данные для скальпинга
            ohlcv_data = await data_manager.get_multi_timeframe_data(
                symbol, ['1m', '5m', '15m']
            )
            
            if ohlcv_data:
                # Проверяем качество данных
                for tf, data in ohlcv_data.items():
                    if data and data.get('historical_data'):
                        candles_count = len(data['historical_data'])
                        print(f'  📊 {tf}: {candles_count} свечей')
                
                # Получаем цену
                main_tf = ohlcv_data.get('5m') or ohlcv_data.get('1m')
                if main_tf and main_tf.get('current'):
                    current_price = main_tf['current']['close']
                    print(f'  💰 Цена: ${current_price:.2f}')
                    
                    # Анализируем скальпинг
                    signal = await scalping_engine.analyze_scalping_signal(
                        symbol, ohlcv_data, current_price
                    )
                    
                    if signal:
                        found_signals += 1
                        print(f'  🎉 НАЙДЕН СИГНАЛ!')
                        print(f'    Действие: {signal["action"]}')
                        print(f'    Уверенность: {signal["confidence"]*100:.1f}%')
                        print(f'    Плечо: {signal["leverage"]:.1f}x')
                        print(f'    Фильтров: {signal["filters_passed"]}/{signal["total_filters"]}')
                    else:
                        print(f'  ❌ Сигнал не найден')
            else:
                print(f'  ❌ Нет данных OHLCV')
                
        except Exception as e:
            print(f'  ❌ Ошибка: {e}')
    
    print(f'\n📊 РЕЗУЛЬТАТ ТЕСТА 1:')
    print(f'✅ Найдено сигналов: {found_signals}/{len(test_pairs)}')
    
    if found_signals == 0:
        print('\n🔧 ТЕСТ 2: ПРОВЕРКА ОТДЕЛЬНЫХ КОМПОНЕНТОВ')
        
        # Проверяем первую пару детально
        symbol = 'BTC/USDT'
        print(f'\n🔍 Детальная проверка {symbol}:')
        
        try:
            ohlcv_data = await data_manager.get_multi_timeframe_data(symbol, ['1m', '5m', '15m'])
            
            if ohlcv_data:
                print('✅ Данные получены')
                
                # Проверяем каждый таймфрейм
                for tf, data in ohlcv_data.items():
                    if data and data.get('historical_data'):
                        df_data = data['historical_data']
                        current = data.get('current', {})
                        
                        print(f'\n📊 {tf} таймфрейм:')
                        print(f'  Свечей: {len(df_data)}')
                        print(f'  Текущая цена: ${current.get("close", 0):.2f}')
                        print(f'  Объем: {current.get("volume", 0):,.0f}')
                        
                        # Проверяем последние 5 свечей на волатильность
                        if len(df_data) >= 5:
                            recent_closes = [candle['close'] for candle in df_data[-5:]]
                            volatility = (max(recent_closes) - min(recent_closes)) / min(recent_closes) * 100
                            print(f'  Волатильность (5 свечей): {volatility:.2f}%')
                
                # Пробуем создать скальпинг сигнал принудительно
                print(f'\n🧪 ПРИНУДИТЕЛЬНЫЙ ТЕСТ СКАЛЬПИНГА:')
                
                # Создаем супер-мягкий движок
                ultra_soft_engine = ScalpingSignalEngine(min_confidence=0.01, min_filters=0)
                
                main_tf = ohlcv_data.get('5m') or ohlcv_data.get('1m')
                if main_tf and main_tf.get('current'):
                    current_price = main_tf['current']['close']
                    
                    signal = await ultra_soft_engine.analyze_scalping_signal(
                        symbol, ohlcv_data, current_price
                    )
                    
                    if signal:
                        print(f'✅ УЛЬТРА-МЯГКИЙ ТЕСТ ПРОШЕЛ!')
                        print(f'  Сигнал: {signal["action"]}')
                        print(f'  Уверенность: {signal["confidence"]*100:.3f}%')
                    else:
                        print(f'❌ Даже ультра-мягкий тест не прошел')
            else:
                print('❌ Не удалось получить данные')
                
        except Exception as e:
            print(f'❌ Ошибка в детальной проверке: {e}')
    
    print('\n🏁 ДИАГНОСТИКА ЗАВЕРШЕНА')

if __name__ == "__main__":
    asyncio.run(test_scalping_debug()) 