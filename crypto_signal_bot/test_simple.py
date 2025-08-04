#!/usr/bin/env python3
"""
Простой тест CryptoAlphaPro бота
"""

import requests
import time
from datetime import datetime

# API ключи
API_KEYS = {
    'telegram': {
        'token': '8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg',
        'chat_id': '5333574230'
    }
}

def get_binance_data(symbol):
    """Получение данных с Binance"""
    try:
        binance_symbol = symbol.replace('/', '')
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            price = float(data['lastPrice'])
            change_24h = float(data['priceChangePercent'])
            volume = float(data['volume'])
            
            return {
                'price': price,
                'change_24h': change_24h,
                'volume': volume,
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice'])
            }
    except Exception as e:
        print(f"❌ Binance error: {e}")
    return None

def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{API_KEYS['telegram']['token']}/sendMessage"
        data = {
            'chat_id': API_KEYS['telegram']['chat_id'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def generate_simple_signal(symbol, data):
    """Генерация простого сигнала"""
    price = data['price']
    change = data['change_24h']
    
    # Простая логика
    if change > 2:
        signal = "STRONG_BUY"
        emoji = "🚀"
    elif change > 0.5:
        signal = "BUY"
        emoji = "📈"
    elif change < -2:
        signal = "STRONG_SELL"
        emoji = "💥"
    elif change < -0.5:
        signal = "SELL"
        emoji = "📉"
    else:
        signal = "NEUTRAL"
        emoji = "➡️"
    
    # Расчет SL/TP
    if signal in ["STRONG_BUY", "BUY"]:
        stop_loss = price * 0.98  # 2% SL
        take_profit = price * 1.04  # 4% TP
    else:
        stop_loss = price * 1.02
        take_profit = price * 0.96
    
    return {
        'symbol': symbol,
        'signal': signal,
        'emoji': emoji,
        'price': price,
        'change_24h': change,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'leverage': 10
    }

def main():
    """Основная функция"""
    print("🚀 CryptoAlphaPro Simple Test")
    print("=" * 40)
    
    # Тестовые пары
    pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    for symbol in pairs:
        print(f"\n🔍 Анализирую {symbol}...")
        
        # Получаем данные
        data = get_binance_data(symbol)
        if not data:
            print(f"❌ Нет данных для {symbol}")
            continue
        
        print(f"💰 Цена: ${data['price']:.2f}")
        print(f"📈 Изменение: {data['change_24h']:.2f}%")
        
        # Генерируем сигнал
        signal = generate_simple_signal(symbol, data)
        
        print(f"🎯 Сигнал: {signal['signal']}")
        print(f"🛡️ SL: ${signal['stop_loss']:.2f}")
        print(f"🎯 TP: ${signal['take_profit']:.2f}")
        
        # Формируем сообщение
        message = f"""
{signal['emoji']} <b>{signal['signal']} {signal['symbol']}</b>

💰 <b>Цена:</b> ${signal['price']:.2f}
📈 <b>24h Δ:</b> {signal['change_24h']:.2f}%
⚡ <b>Плечо:</b> {signal['leverage']}x

🛡️ <b>Stop Loss:</b> ${signal['stop_loss']:.2f}
🎯 <b>Take Profit:</b> ${signal['take_profit']:.2f}

⏰ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
🤖 CryptoAlphaPro v2.1
        """
        
        # Отправляем в Telegram
        if send_telegram_message(message):
            print(f"✅ Сигнал отправлен в Telegram")
        else:
            print(f"❌ Ошибка отправки")
        
        time.sleep(2)  # Пауза между запросами
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    main() 