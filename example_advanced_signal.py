#!/usr/bin/env python3
"""
Пример использования продвинутых функций сигналов
"""

import pandas as pd
import numpy as np
from datetime import datetime
from signal_explainer import SignalExplainer
from advanced_technical_analyzer import AdvancedTechnicalAnalyzer

def create_sample_data() -> pd.DataFrame:
    """Создает пример данных для демонстрации"""
    # Создаем пример данных OHLCV
    dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
    
    # Создаем трендовые данные
    base_price = 0.378300
    trend = np.linspace(0, 0.02, 100)  # Восходящий тренд
    noise = np.random.normal(0, 0.001, 100)
    
    prices = base_price + trend + noise
    
    # Создаем OHLC данные
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        # Создаем реалистичные OHLC данные
        open_price = price
        high_price = price + abs(np.random.normal(0, 0.002))
        low_price = price - abs(np.random.normal(0, 0.002))
        close_price = price + np.random.normal(0, 0.001)
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

def generate_advanced_signal():
    """Генерирует продвинутый сигнал с объяснением"""
    
    # Создаем анализаторы
    explainer = SignalExplainer()
    analyzer = AdvancedTechnicalAnalyzer()
    
    # Создаем пример данных
    df = create_sample_data()
    
    # Анализируем данные
    analysis = analyzer._analyze_single_timeframe(df)
    
    # Добавляем уровни поддержки и сопротивления
    support_resistance = analyzer.calculate_support_resistance(df)
    analysis.update(support_resistance)
    
    # Создаем сигнал
    current_price = df['close'].iloc[-1]
    signal = {
        'action': 'BUY',
        'symbol': 'M/USDT',
        'price': current_price,
        'confidence': 0.84,
        'take_profit': explainer.calculate_take_profit_levels(current_price, 'long'),
        'stop_loss': explainer.calculate_stop_loss(current_price, 'long')
    }
    
    # Создаем мультитаймфреймовый анализ (упрощенная версия)
    mtf_analysis = {
        'timeframes': {
            '15m': {'trend': 'bullish'},
            '1h': {'trend': 'bullish'},
            '4h': {'trend': 'neutral'}
        },
        'overall_trend': 'bullish'
    }
    
    # Генерируем сообщение сигнала
    message = explainer.format_signal_message(signal, analysis, mtf_analysis)
    
    return message, signal, analysis, mtf_analysis

def test_advanced_features():
    """Тестирует продвинутые функции"""
    print("🧪 Тестирование продвинутых функций сигналов...")
    print("=" * 60)
    
    # Генерируем сигнал
    message, signal, analysis, mtf_analysis = generate_advanced_signal()
    
    print("📊 Сгенерированный сигнал:")
    print(message)
    
    print("\n🔍 Детали анализа:")
    print(f"RSI: {analysis.get('rsi', 'N/A'):.2f}")
    print(f"MACD Histogram: {analysis.get('macd', {}).get('histogram', 'N/A'):.4f}")
    print(f"ADX: {analysis.get('adx', {}).get('adx', 'N/A'):.1f}")
    print(f"Volume Ratio: {analysis.get('volume', {}).get('ratio', 'N/A'):.2f}")
    print(f"Support: ${analysis.get('support', 'N/A'):.6f}")
    print(f"Resistance: ${analysis.get('resistance', 'N/A'):.6f}")
    
    print("\n📈 Паттерны:")
    patterns = analysis.get('patterns', {})
    for pattern, detected in patterns.items():
        if detected:
            print(f"✅ {pattern}")
    
    print("\n⏰ Мультитаймфреймовый анализ:")
    for timeframe, tf_data in mtf_analysis.get('timeframes', {}).items():
        trend = tf_data.get('trend', 'neutral')
        print(f"{timeframe}: {trend}")
    
    print(f"\n🎯 Общий тренд: {mtf_analysis.get('overall_trend', 'neutral')}")
    
    return True

if __name__ == "__main__":
    test_advanced_features() 