#!/usr/bin/env python3
"""
Тест реальных данных для CryptoAlphaPro Bot
"""

import asyncio
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime

async def test_real_data():
    print('🚀 Тестирование РЕАЛЬНЫХ данных...')
    
    # Инициализируем биржу
    binance = ccxt.binance({'enableRateLimit': True})
    
    try:
        # Получаем реальные данные
        ohlcv = binance.fetch_ohlcv('BTC/USDT', '1h', limit=50)
        
        if ohlcv and len(ohlcv) >= 50:
            closes = [candle[4] for candle in ohlcv]
            highs = [candle[2] for candle in ohlcv]
            lows = [candle[3] for candle in ohlcv]
            volumes = [candle[5] for candle in ohlcv]
            
            # РЕАЛЬНЫЙ RSI расчет
            def calculate_rsi(prices, period=14):
                deltas = np.diff(prices)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains[:period])
                avg_loss = np.mean(losses[:period])
                
                for i in range(period, len(gains)):
                    avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                    avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                
                if avg_loss == 0:
                    return 100
                rs = avg_gain / avg_loss
                return 100 - (100 / (1 + rs))
            
            # РЕАЛЬНЫЙ MACD расчет
            def calculate_ema(prices, period):
                alpha = 2 / (period + 1)
                ema = [prices[0]]
                for price in prices[1:]:
                    ema.append(alpha * price + (1 - alpha) * ema[-1])
                return np.array(ema)
            
            rsi = calculate_rsi(closes)
            current_price = closes[-1]
            
            ema_12 = calculate_ema(closes, 12)
            ema_26 = calculate_ema(closes, 26)
            macd = ema_12[-1] - ema_26[-1]
            
            # Volume analysis
            avg_volume = np.mean(volumes[-20:])
            volume_ratio = volumes[-1] / avg_volume
            
            print('=' * 50)
            print('📊 BTC/USDT РЕАЛЬНЫЕ ДАННЫЕ:')
            print('=' * 50)
            print(f'💰 Текущая цена: ${current_price:,.2f}')
            print(f'📈 RSI (14): {rsi:.2f}')
            print(f'📊 MACD: {macd:.4f}')
            print(f'📊 EMA 12: ${ema_12[-1]:,.2f}')
            print(f'📊 EMA 26: ${ema_26[-1]:,.2f}')
            print(f'📈 Volume Ratio: {volume_ratio:.2f}x')
            print(f'🕒 Время: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}')
            print(f'✅ Данные получены с Binance (последние 50 свечей)')
            
            # Проверяем что данные свежие
            last_timestamp = ohlcv[-1][0]
            current_time = datetime.now().timestamp() * 1000
            age_minutes = (current_time - last_timestamp) / (1000 * 60)
            
            print(f'⏰ Возраст данных: {age_minutes:.1f} минут')
            
            if age_minutes < 120:  # Данные свежее 2 часов
                print('✅ ДАННЫЕ СВЕЖИЕ И РЕАЛЬНЫЕ!')
            else:
                print('⚠️ Данные устаревшие')
                
            print('=' * 50)
            print('🎯 АНАЛИЗ:')
            
            if rsi > 70:
                print('📈 RSI: Перекупленность (возможен откат)')
            elif rsi < 30:
                print('📉 RSI: Перепроданность (возможен отскок)')
            else:
                print('📊 RSI: Нормальная зона')
                
            if macd > 0:
                print('📈 MACD: Бычий сигнал')
            else:
                print('📉 MACD: Медвежий сигнал')
                
            if volume_ratio > 1.5:
                print('📊 Volume: Повышенная активность')
            else:
                print('📊 Volume: Обычная активность')
                
            print('=' * 50)
            
        else:
            print('❌ Не удалось получить достаточно данных')
            
    except Exception as e:
        print(f'❌ Ошибка: {e}')

if __name__ == "__main__":
    asyncio.run(test_real_data()) 