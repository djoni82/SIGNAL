#!/usr/bin/env python3
"""
Детальный тест скальпинг модуля с отладкой
"""

import asyncio
from scalping_engine import ScalpingSignalEngine
from alpha_signal_bot_main import UniversalDataManager

async def test_scalping_debug():
    print("⚡ ДЕТАЛЬНЫЙ ТЕСТ СКАЛЬПИНГ МОДУЛЯ")
    print("=" * 60)
    
    # Инициализируем движки с очень низкими требованиями
    data_manager = UniversalDataManager()
    scalping_engine = ScalpingSignalEngine(min_confidence=0.50, min_filters=2)  # ОЧЕНЬ низкие требования
    
    symbol = 'BTC/USDT'
    print(f"\n🔍 Детальный тест {symbol}...")
    
    try:
        # Получаем данные для коротких таймфреймов
        ohlcv_data = await data_manager.get_multi_timeframe_data(
            symbol, ['1m', '5m', '15m']
        )
        
        if ohlcv_data:
            print(f"✅ Получены данные для таймфреймов: {list(ohlcv_data.keys())}")
            
            for tf, data in ohlcv_data.items():
                if data and data.get('historical_data'):
                    print(f"  {tf}: {len(data['historical_data'])} свечей")
                else:
                    print(f"  {tf}: НЕТ данных")
            
            # Получаем текущую цену
            main_tf = ohlcv_data.get('5m') or ohlcv_data.get('1m')
            if main_tf and main_tf.get('current'):
                current_price = main_tf['current']['close']
                print(f"💰 Текущая цена: ${current_price:.6f}")
                
                # Вручную тестируем анализ каждого таймфрейма
                available_tfs = []
                tf_analysis = {}
                
                for tf in ['1m', '5m', '15m']:
                    if tf in ohlcv_data and ohlcv_data[tf] and ohlcv_data[tf].get('historical_data'):
                        if len(ohlcv_data[tf]['historical_data']) >= 30:
                            available_tfs.append(tf)
                            analysis = scalping_engine._analyze_scalping_timeframe(ohlcv_data[tf], tf)
                            if analysis:
                                tf_analysis[tf] = analysis
                                print(f"\n📊 Анализ {tf}:")
                                print(f"  RSI: {analysis.get('rsi_fast', 'N/A'):.1f}")
                                print(f"  EMA8: {analysis.get('ema_8', 'N/A'):.6f}")
                                print(f"  EMA21: {analysis.get('ema_21', 'N/A'):.6f}")
                                print(f"  EMA Cross: {analysis.get('ema_cross', 'N/A')}")
                                print(f"  MACD Hist: {analysis.get('macd_fast', {}).get('histogram', 'N/A')}")
                                print(f"  ADX: {analysis.get('adx_fast', 'N/A'):.1f}")
                                print(f"  Vol Momentum: {analysis.get('volume_momentum', 'N/A'):.1f}%")
                                print(f"  Price Momentum: {analysis.get('price_momentum', 'N/A'):.1f}%")
                            else:
                                print(f"\n❌ Анализ {tf} не удался")
                
                print(f"\n🎯 Доступных таймфреймов: {len(available_tfs)}")
                print(f"🎯 Успешных анализов: {len(tf_analysis)}")
                
                if len(tf_analysis) >= 2:
                    print(f"\n⚡ Запускаем оценку фильтров...")
                    
                    # Вручную оцениваем фильтры
                    bullish_filters = 0
                    bearish_filters = 0
                    total_filters = 0
                    filter_details = []
                    
                    for tf, analysis in tf_analysis.items():
                        print(f"\n📋 Фильтры для {tf}:")
                        
                        # 1. RSI фильтр
                        rsi = analysis.get('rsi_fast', 50)
                        if rsi > 65:
                            bearish_filters += 1
                            filter_details.append(f"{tf} RSI={rsi:.1f} (SELL)")
                            print(f"  ❌ RSI={rsi:.1f} > 65 -> SELL")
                        elif rsi < 35:
                            bullish_filters += 1
                            filter_details.append(f"{tf} RSI={rsi:.1f} (BUY)")
                            print(f"  ✅ RSI={rsi:.1f} < 35 -> BUY")
                        else:
                            print(f"  ⚪ RSI={rsi:.1f} -> NEUTRAL")
                        total_filters += 1
                        
                        # 2. MACD фильтр
                        macd = analysis.get('macd_fast', {})
                        hist = macd.get('histogram', 0)
                        if hist > 0:
                            bullish_filters += 1
                            filter_details.append(f"{tf} MACD+ (BUY)")
                            print(f"  ✅ MACD Hist={hist:.6f} > 0 -> BUY")
                        else:
                            bearish_filters += 1
                            filter_details.append(f"{tf} MACD- (SELL)")
                            print(f"  ❌ MACD Hist={hist:.6f} <= 0 -> SELL")
                        total_filters += 1
                        
                        # 3. EMA Cross фильтр
                        ema_cross = analysis.get('ema_cross', 0)
                        if ema_cross > 0:
                            bullish_filters += 1
                            filter_details.append(f"{tf} EMA8>21 (BUY)")
                            print(f"  ✅ EMA Cross > 0 -> BUY")
                        else:
                            bearish_filters += 1
                            filter_details.append(f"{tf} EMA8<21 (SELL)")
                            print(f"  ❌ EMA Cross <= 0 -> SELL")
                        total_filters += 1
                    
                    print(f"\n📊 ИТОГОВЫЕ ФИЛЬТРЫ:")
                    print(f"  Бычьих: {bullish_filters}")
                    print(f"  Медвежьих: {bearish_filters}")
                    print(f"  Всего: {total_filters}")
                    
                    if bullish_filters >= 2:
                        confidence = bullish_filters / total_filters
                        print(f"  Уверенность: {confidence*100:.1f}%")
                        if confidence >= 0.50:
                            print(f"  ✅ СИГНАЛ НАЙДЕН! BUY с уверенностью {confidence*100:.1f}%")
                        else:
                            print(f"  ❌ Уверенность слишком низкая ({confidence*100:.1f}% < 50%)")
                    elif bearish_filters >= 2:
                        confidence = bearish_filters / total_filters
                        print(f"  Уверенность: {confidence*100:.1f}%")
                        if confidence >= 0.50:
                            print(f"  ✅ СИГНАЛ НАЙДЕН! SELL с уверенностью {confidence*100:.1f}%")
                        else:
                            print(f"  ❌ Уверенность слишком низкая ({confidence*100:.1f}% < 50%)")
                    else:
                        print(f"  ❌ Недостаточно фильтров (нужно минимум 2)")
                    
                    # Теперь попробуем полный анализ
                    print(f"\n🔥 ПОЛНЫЙ АНАЛИЗ СКАЛЬПИНГА:")
                    scalp_signal = await scalping_engine.analyze_scalping_signal(
                        symbol, ohlcv_data, current_price
                    )
                    
                    if scalp_signal:
                        print(f"🎉 СКАЛЬПИНГ СИГНАЛ НАЙДЕН!")
                        print(f"   Действие: {scalp_signal['action']}")
                        print(f"   Уверенность: {scalp_signal['confidence']*100:.1f}%")
                        print(f"   Плечо: {scalp_signal['leverage']:.0f}x")
                        print(f"   Фильтров: {scalp_signal['filters_passed']}/{scalp_signal['total_filters']}")
                    else:
                        print("❌ Скальпинг сигнал НЕ найден (полный анализ)")
                else:
                    print(f"❌ Недостаточно таймфреймов для анализа ({len(tf_analysis)} < 2)")
            else:
                print("❌ Нет текущей цены")
        else:
            print("❌ Нет данных")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_scalping_debug()) 