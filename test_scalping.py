#!/usr/bin/env python3
"""
Тест скальпинг модуля
"""

import asyncio
from scalping_engine import ScalpingSignalEngine
from alpha_signal_bot_main import UniversalDataManager

async def test_scalping():
    print("⚡ ТЕСТ СКАЛЬПИНГ МОДУЛЯ")
    print("=" * 50)
    
    # Инициализируем движки
    data_manager = UniversalDataManager()
    scalping_engine = ScalpingSignalEngine(min_confidence=0.70, min_filters=3)  # Очень низкие требования для теста
    
    test_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    for symbol in test_pairs:
        print(f"\n🔍 Тестируем {symbol}...")
        
        try:
            # Получаем данные для коротких таймфреймов
            ohlcv_data = await data_manager.get_multi_timeframe_data(
                symbol, ['1m', '5m', '15m']
            )
            
            if ohlcv_data:
                print(f"✅ Получены данные для {len(ohlcv_data)} таймфреймов")
                
                # Получаем текущую цену
                main_tf = ohlcv_data.get('5m') or ohlcv_data.get('1m')
                if main_tf and main_tf.get('current'):
                    current_price = main_tf['current']['close']
                    print(f"💰 Текущая цена: ${current_price:.6f}")
                    
                    # Анализируем скальпинг сигнал
                    scalp_signal = await scalping_engine.analyze_scalping_signal(
                        symbol, ohlcv_data, current_price
                    )
                    
                    if scalp_signal:
                        print(f"🎉 СКАЛЬПИНГ СИГНАЛ НАЙДЕН!")
                        print(f"   Действие: {scalp_signal['action']}")
                        print(f"   Уверенность: {scalp_signal['confidence']*100:.1f}%")
                        print(f"   Плечо: {scalp_signal['leverage']:.0f}x")
                        print(f"   Фильтров: {scalp_signal['filters_passed']}/{scalp_signal['total_filters']}")
                        
                        # Показываем первые 3 фильтра
                        details = scalp_signal.get('filter_details', [])[:3]
                        for detail in details:
                            print(f"   • {detail}")
                    else:
                        print("❌ Скальпинг сигнал не найден")
                else:
                    print("❌ Нет текущей цены")
            else:
                print("❌ Нет данных")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(test_scalping()) 