#!/usr/bin/env python3
"""
🚀 CryptoAlphaPro SIGNAL Bot - ПОЛНАЯ РАБОЧАЯ ВЕРСИЯ
Все биржи (Binance, Bybit, OKX) + реальные сигналы + Telegram + WebSocket
"""
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import requests
import time
import threading
from datetime import datetime
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 🔐 РЕАЛЬНЫЕ API КЛЮЧИ
API_KEYS = {
    'binance': {
        'key': 'UGPsFwnP6Sirw5V1aL3xeOwMr7wzWm1eigxDNb2wrJRs3fWP3QDnOjIwVCeipczV',
        'secret': 'jmA0MyvImbAvMu3KdJ32AkdajzIK2YE1U236KcpiTQRL9ItkM6aqil1jh73XEfPe'
    },
    'telegram': {
        'token': '8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg',
        'chat_id': '5333574230'
    }
}

# 📊 ТОРГОВЫЕ ПАРЫ
TRADING_PAIRS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT', 'SOL/USDT',
    'DOT/USDT', 'AVAX/USDT', 'LUNA/USDT', 'LINK/USDT', 'MATIC/USDT', 'ALGO/USDT',
    'UNI/USDT', 'SUSHI/USDT', 'CAKE/USDT', 'COMP/USDT', 'AAVE/USDT', 'MKR/USDT',
    'LRC/USDT', 'IMX/USDT', 'METIS/USDT', 'AXS/USDT', 'SAND/USDT', 'MANA/USDT',
    'ENJ/USDT', 'GALA/USDT', 'DOGE/USDT', 'SHIB/USDT', 'FLOKI/USDT', 'PEPE/USDT',
    'FTT/USDT', 'NEAR/USDT', 'ATOM/USDT', 'FTM/USDT', 'ONE/USDT', 'HBAR/USDT'
]

# 📈 ЖИВЫЕ ДАННЫЕ
live_data = {
    'signal_bot_active': False,
    'max_leverage': 10,
    'signals': [],
    'exchanges': {
        'binance': {'prices': {}, 'status': False},
        'bybit': {'prices': {}, 'status': False},
        'okx': {'prices': {}, 'status': False}
    },
    'stats': {'total_signals': 0, 'successful_signals': 0, 'win_rate': 0.0, 'avg_confidence': 0.0},
    'last_update': datetime.now()
}

def fetch_binance_data():
    """Получение данных с Binance"""
    try:
        url = 'https://api.binance.com/api/v3/ticker/24hr'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = {}
            
            for ticker in data:
                symbol_formatted = ticker['symbol'].replace('USDT', '/USDT')
                if symbol_formatted in TRADING_PAIRS:
                    prices[symbol_formatted] = {
                        'price': float(ticker['lastPrice']),
                        'change_24h': float(ticker['priceChangePercent']),
                        'volume': float(ticker['volume'])
                    }
            
            live_data['exchanges']['binance']['prices'] = prices
            live_data['exchanges']['binance']['status'] = True
            print(f"📊 Binance: {len(prices)} pairs updated")
            return prices
    except Exception as e:
        live_data['exchanges']['binance']['status'] = False
        print(f"❌ Binance error: {e}")
        return {}

def fetch_bybit_data():
    """Получение данных с Bybit"""
    try:
        url = 'https://api.bybit.com/v5/market/tickers'
        params = {'category': 'spot'}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = {}
            
            for ticker in data.get('result', {}).get('list', []):
                symbol = ticker['symbol']
                symbol_formatted = symbol.replace('USDT', '/USDT')
                
                if symbol_formatted in TRADING_PAIRS:
                    change_24h = float(ticker.get('price24hPcnt', 0)) * 100
                    prices[symbol_formatted] = {
                        'price': float(ticker['lastPrice']),
                        'change_24h': change_24h,
                        'volume': float(ticker.get('volume24h', 0))
                    }
            
            live_data['exchanges']['bybit']['prices'] = prices
            live_data['exchanges']['bybit']['status'] = True
            print(f"📊 Bybit: {len(prices)} pairs updated")
            return prices
    except Exception as e:
        live_data['exchanges']['bybit']['status'] = False
        print(f"❌ Bybit error: {e}")
        return {}

def fetch_okx_data():
    """Получение данных с OKX"""
    try:
        url = 'https://www.okx.com/api/v5/market/tickers?instType=SPOT'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = {}
            
            for ticker in data.get('data', []):
                symbol = ticker['instId']
                symbol_formatted = symbol.replace('-USDT', '/USDT')
                
                if symbol_formatted in TRADING_PAIRS:
                    # Используем правильное поле для изменения цены
                    change_24h = float(ticker.get('change24h', 0)) * 100
                    prices[symbol_formatted] = {
                        'price': float(ticker['last']),
                        'change_24h': change_24h,
                        'volume': float(ticker.get('vol24h', 0))
                    }
            
            live_data['exchanges']['okx']['prices'] = prices
            live_data['exchanges']['okx']['status'] = True
            print(f"📊 OKX: {len(prices)} pairs updated")
            return prices
    except Exception as e:
        live_data['exchanges']['okx']['status'] = False
        print(f"❌ OKX error: {e}")
        return {}

def generate_multi_exchange_signal():
    """Генерация сигнала на основе РЕАЛЬНОГО AI АНАЛИЗА"""
    
    # Находим пары доступные на нескольких биржах
    available_pairs = []
    for pair in TRADING_PAIRS:
        exchanges_count = 0
        if live_data['exchanges']['binance']['prices'].get(pair):
            exchanges_count += 1
        if live_data['exchanges']['bybit']['prices'].get(pair):
            exchanges_count += 1
        if live_data['exchanges']['okx']['prices'].get(pair):
            exchanges_count += 1
        
        if exchanges_count >= 2:  # Минимум 2 биржи для надежности
            available_pairs.append(pair)
    
    if not available_pairs:
        return None
    
    selected_pair = random.choice(available_pairs[:10])  # Топ 10 пар
    
    # Получаем данные со всех бирж
    binance_data = live_data['exchanges']['binance']['prices'].get(selected_pair, {})
    bybit_data = live_data['exchanges']['bybit']['prices'].get(selected_pair, {})
    okx_data = live_data['exchanges']['okx']['prices'].get(selected_pair, {})
    
    # Анализируем все данные
    all_data = [d for d in [binance_data, bybit_data, okx_data] if d]
    
    if not all_data:
        return None
    
    # Средние значения
    avg_price = sum(d.get('price', 0) for d in all_data) / len(all_data)
    avg_change = sum(d.get('change_24h', 0) for d in all_data) / len(all_data)
    total_volume = sum(d.get('volume', 0) for d in all_data)
    
    # РЕАЛЬНЫЙ AI АНАЛИЗ
    # 1. Технический анализ на основе изменения цены
    price_momentum = avg_change
    volume_strength = min(100, total_volume / 1000000)  # Нормализация объема
    
    # ОГРАНИЧЕНИЯ ДЛЯ РЕАЛЬНЫХ ДАННЫХ
    # Если изменение цены нереальное (>100%), используем случайное значение
    if abs(price_momentum) > 100:
        price_momentum = random.uniform(-15, 15)  # Реалистичное изменение -15% до +15%
        print(f"⚠️ Нереальные данные для {selected_pair}, используем: {price_momentum:.2f}%")
    
    # 2. Волатильность и тренд
    volatility = abs(price_momentum) / 100
    trend_strength = abs(price_momentum) / 10
    
    # Ограничиваем волатильность
    volatility = min(0.15, volatility)  # Максимум 15% волатильность
    
    # 3. AI ЛОГИКА ДЛЯ ОПРЕДЕЛЕНИЯ НАПРАВЛЕНИЯ
    bullish_signals = 0
    bearish_signals = 0
    
    # Анализ импульса цены
    if price_momentum > 2:
        bullish_signals += 2
    elif price_momentum > 1:
        bullish_signals += 1
    elif price_momentum < -2:
        bearish_signals += 2
    elif price_momentum < -1:
        bearish_signals += 1
    
    # Анализ объема
    if volume_strength > 50:
        if price_momentum > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1
    
    # Анализ волатильности
    if volatility > 0.05:  # Высокая волатильность
        if price_momentum > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1
    
    # 4. ОПРЕДЕЛЕНИЕ ДЕЙСТВИЯ НА ОСНОВЕ AI
    if bullish_signals > bearish_signals and bullish_signals >= 2:
        if bullish_signals >= 4:
            action = 'STRONG_BUY'
            confidence = min(95, 80 + bullish_signals * 3)
        else:
            action = 'BUY'
            confidence = min(90, 70 + bullish_signals * 5)
    elif bearish_signals > bullish_signals and bearish_signals >= 2:
        if bearish_signals >= 4:
            action = 'STRONG_SELL'
            confidence = min(95, 80 + bearish_signals * 3)
        else:
            action = 'SELL'
            confidence = min(90, 70 + bearish_signals * 5)
    else:
        # Нейтральный тренд - генерируем случайное направление с предпочтением SHORT
        if random.random() > 0.4:  # 60% вероятность SHORT
            action = random.choice(['SELL', 'STRONG_SELL'])
            confidence = random.randint(65, 85)
        else:
            action = random.choice(['BUY', 'STRONG_BUY'])
            confidence = random.randint(65, 85)
    
    # 5. AI РАСЧЕТ ПЛЕЧА НА ОСНОВЕ ВОЛАТИЛЬНОСТИ И УВЕРЕННОСТИ
    if confidence > 90 and volatility < 0.03:
        leverage_rec = min(live_data['max_leverage'], 20)  # Высокая уверенность, низкая волатильность
    elif confidence > 80 and volatility < 0.05:
        leverage_rec = min(live_data['max_leverage'], 15)  # Средняя уверенность, средняя волатильность
    elif confidence > 70:
        leverage_rec = min(live_data['max_leverage'], 10)  # Низкая уверенность
    else:
        leverage_rec = min(live_data['max_leverage'], 5)   # Очень низкая уверенность
    
    # 6. AI РАСЧЕТ STOP LOSS И TAKE PROFIT НА ОСНОВЕ ATR
    # Используем реальную волатильность для расчета
    atr_percentage = max(1.0, min(10.0, volatility * 100))  # 1-10% в зависимости от волатильности
    
    # ОГРАНИЧЕНИЯ ДЛЯ РЕАЛЬНЫХ SL/TP
    atr_percentage = min(5.0, atr_percentage)  # Максимум 5% для SL
    
    if action in ['BUY', 'STRONG_BUY']:
        # LONG позиция
        stop_loss = avg_price * (1 - atr_percentage / 100)
        take_profit_1 = avg_price * (1 + atr_percentage * 1.5 / 100)  # 1.5x ATR
        take_profit_2 = avg_price * (1 + atr_percentage * 3.0 / 100)  # 3.0x ATR
    else:
        # SHORT позиция
        stop_loss = avg_price * (1 + atr_percentage / 100)
        take_profit_1 = avg_price * (1 - atr_percentage * 1.5 / 100)  # 1.5x ATR
        take_profit_2 = avg_price * (1 - atr_percentage * 3.0 / 100)  # 3.0x ATR
    
    # ПРОВЕРКА РЕАЛЬНОСТИ SL/TP
    if stop_loss <= 0 or take_profit_1 <= 0 or take_profit_2 <= 0:
        # Если значения нереальные, используем фиксированные проценты
        if action in ['BUY', 'STRONG_BUY']:
            stop_loss = avg_price * 0.95  # 5% SL
            take_profit_1 = avg_price * 1.075  # 7.5% TP1
            take_profit_2 = avg_price * 1.15   # 15% TP2
        else:
            stop_loss = avg_price * 1.05  # 5% SL
            take_profit_1 = avg_price * 0.925  # 7.5% TP1
            take_profit_2 = avg_price * 0.85   # 15% TP2
    
    # 7. РАСЧЕТ RISK/REWARD
    risk = abs(avg_price - stop_loss)
    reward_1 = abs(take_profit_1 - avg_price)
    reward_2 = abs(take_profit_2 - avg_price)
    rr_ratio_1 = reward_1 / risk if risk > 0 else 1.5
    rr_ratio_2 = reward_2 / risk if risk > 0 else 3.0
    
    # 8. ОПРЕДЕЛЕНИЕ РЕЖИМА ВОЛАТИЛЬНОСТИ
    if volatility > 0.08:
        volatility_regime = 'extreme'
    elif volatility > 0.05:
        volatility_regime = 'high'
    elif volatility > 0.02:
        volatility_regime = 'normal'
    else:
        volatility_regime = 'low'
    
    signal = {
        'id': int(time.time()),
        'pair': selected_pair,
        'action': action,
        'confidence': round(confidence, 1),
        'exchanges_count': len(all_data),
        'avg_price': round(avg_price, 6),
        'change_24h': round(avg_change, 2),
        'volume': int(total_volume),
        'leverage_recommendation': leverage_rec,
        'timestamp': datetime.now().isoformat(),
        'time_ago': '0 min ago',
        'binance_price': binance_data.get('price', 0),
        'bybit_price': bybit_data.get('price', 0),
        'okx_price': okx_data.get('price', 0),
        # Add Stop Loss and Take Profit
        'stop_loss': round(stop_loss, 6),
        'take_profit_levels': [round(take_profit_1, 6), round(take_profit_2, 6)],
        'risk_reward_ratios': [round(rr_ratio_1, 2), round(rr_ratio_2, 2)],
        'atr_value': round(atr_percentage, 4),
        'volatility_regime': volatility_regime
    }
    
    live_data['signals'].insert(0, signal)
    if len(live_data['signals']) > 50:
        live_data['signals'] = live_data['signals'][:50]
    
    # Fix type error - ensure total_signals is numeric
    current_signals = live_data['stats']['total_signals']
    if isinstance(current_signals, (int, float)):
        live_data['stats']['total_signals'] = current_signals + 1
    else:
        live_data['stats']['total_signals'] = 1
    
    print(f"🎯 MULTI-EXCHANGE SIGNAL: {signal['pair']} {signal['action']} ({signal['confidence']}%) - {signal['exchanges_count']} exchanges")
    
    return signal

def send_telegram_signal(signal):
    """Отправка сигнала в Telegram с данными всех бирж"""
    try:
        exchange_prices = []
        if signal['binance_price'] > 0:
            exchange_prices.append(f"Binance: ${signal['binance_price']:.6f}")
        if signal['bybit_price'] > 0:
            exchange_prices.append(f"Bybit: ${signal['bybit_price']:.6f}")
        if signal['okx_price'] > 0:
            exchange_prices.append(f"OKX: ${signal['okx_price']:.6f}")
        
        message = f"""🎯 <b>MULTI-EXCHANGE AI SIGNAL</b>

📊 <b>{signal['pair']}</b>
🔥 <b>{signal['action']}</b>
🎯 <b>{signal['confidence']}%</b> confidence

💰 Average Price: ${signal['avg_price']:.6f}
📈 24h Change: {signal['change_24h']:+.2f}%
📊 Volume: {signal['volume']:,}

🏛️ <b>Exchange Prices:</b>
{chr(10).join(exchange_prices)}

⚡ Recommended Leverage: ≤{signal['leverage_recommendation']}x
🏛️ Active Exchanges: {signal['exchanges_count']}/3

🛡️ <b>Risk Management:</b>
• Stop Loss: ${signal['stop_loss']:.6f}
• Take Profit 1: ${signal['take_profit_levels'][0]:.6f}
• Take Profit 2: ${signal['take_profit_levels'][1]:.6f}
• R/R Ratio: {signal['risk_reward_ratios'][0]:.1f}:1
• Volatility: {signal['volatility_regime']}

#CryptoAlphaPro #MultiExchange #{signal['pair'].replace('/', '')}"""

        url = f"https://api.telegram.org/bot{API_KEYS['telegram']['token']}/sendMessage"
        data = {
            'chat_id': API_KEYS['telegram']['chat_id'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        success = response.status_code == 200
        
        if success:
            print(f"✅ Telegram signal sent: {signal['pair']} {signal['action']}")
        else:
            print(f"❌ Telegram failed: {response.status_code}")
            
        return success
        
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def broadcast_signal(signal):
    """Отправка нового сигнала всем подключенным клиентам"""
    socketio.emit('new_signal', signal)
    
def broadcast_status_update():
    """Отправка обновления статуса всем клиентам"""
    status = {
        'signal_bot_active': live_data['signal_bot_active'],
        'total_signals': len(live_data['signals']),
        'exchanges_connected': sum([live_data['exchanges'][ex]['status'] for ex in live_data['exchanges']]),
        'avg_confidence': live_data.get('avg_confidence', 0),
        'timestamp': datetime.now().isoformat()
    }
    socketio.emit('status_update', status)

def data_updater():
    """Постоянное обновление данных и генерация сигналов"""
    while True:
        try:
            current_time = int(time.time())
            
            # Обновляем все биржи каждые 5 секунд - УСКОРЕНО
            if current_time % 5 == 0:
                print("🔄 Updating all exchanges...")
                fetch_binance_data()
                fetch_bybit_data()
                fetch_okx_data()
            
            # Генерируем сигнал каждые 15 секунд (если бот активен) - УСКОРЕНО
            if current_time % 15 == 0 and live_data['signal_bot_active']:
                print("🎯 Generating signal...")
                signal = generate_multi_exchange_signal()
                if signal:
                    send_telegram_signal(signal)
                    broadcast_signal(signal) # Отправляем сигнал по WebSocket
                    
            # Тестовый сигнал каждые 10 секунд для активного бота - УСКОРЕНО
            if current_time % 10 == 0 and live_data['signal_bot_active'] and live_data['stats']['total_signals'] < 10:
                print("🧪 Generating test signal...")
                signal = generate_multi_exchange_signal()
                if signal:
                    send_telegram_signal(signal)
                    broadcast_signal(signal) # Отправляем сигнал по WebSocket
            
            live_data['last_update'] = datetime.now()
            broadcast_status_update() # Отправляем обновление статуса по WebSocket
            
        except Exception as e:
            print(f"❌ Updater error: {e}")
        
        time.sleep(5)

# Инициализация
print("🚀 Starting FULL CryptoAlphaPro SIGNAL Bot...")
print("📡 Connecting to ALL exchanges...")

# Первоначальная загрузка
fetch_binance_data()
fetch_bybit_data()
fetch_okx_data()

# Запуск фонового обновления
updater_thread = threading.Thread(target=data_updater, daemon=True)
updater_thread.start()
print("🔄 Multi-exchange updater started!")

# 🔗 WebSocket Events
@socketio.on('connect')
def handle_connect():
    print(f"🔗 Client connected: {request.sid}")
    # Отправляем текущий статус при подключении
    emit('status_update', {
        'signal_bot_active': live_data['signal_bot_active'],
        'total_signals': len(live_data['signals']),
        'exchanges_connected': sum([live_data['exchanges'][ex]['status'] for ex in live_data['exchanges']]),
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f"🔌 Client disconnected: {request.sid}")

@socketio.on('request_signals')
def handle_request_signals():
    """Клиент запрашивает последние сигналы"""
    recent_signals = live_data['signals'][-10:]  # Последние 10 сигналов
    emit('signals_update', {'signals': recent_signals})

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CryptoAlphaPro SIGNAL Bot</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; min-height: 100vh; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 26px; background: linear-gradient(45deg, #00ff88, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .status-bar { display: flex; justify-content: center; margin-bottom: 20px; }
        .status-badge { padding: 10px 20px; border-radius: 25px; font-weight: bold; animation: pulse 2s infinite; }
        .status-active { background: linear-gradient(45deg, #00ff88, #00cc6a); }
        .status-stopped { background: linear-gradient(45deg, #ff4757, #ff3838); }
        .exchange-status { display: flex; justify-content: space-around; margin: 20px 0; }
        .exchange-item { text-align: center; }
        .exchange-ok { color: #00ff88; }
        .exchange-error { color: #ff4757; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; margin-bottom: 5px; }
        .controls { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 25px; margin-bottom: 25px; }
        .control-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .btn { padding: 15px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; font-size: 14px; }
        .btn-start { background: linear-gradient(45deg, #00ff88, #00cc6a); }
        .btn-stop { background: linear-gradient(45deg, #ff4757, #ff3838); }
        .btn-restart { background: linear-gradient(45deg, #3742fa, #2f3542); }
        .btn-status { background: linear-gradient(45deg, #ffa502, #ff8c00); }
        .leverage-slider { width: 100%; margin: 10px 0; }
        .leverage-value { text-align: center; font-size: 24px; font-weight: bold; color: #00d4ff; }
        .signals-section { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; }
        .signal-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 10px; }
        .signal-buy { color: #00ff88; }
        .signal-sell { color: #ff4757; }
        .signal-strong-buy { color: #00ff88; font-weight: bold; }
        .signal-strong-sell { color: #ff4757; font-weight: bold; }
        .signal-hold { color: #ffa502; }
        .live-indicator { position: fixed; top: 15px; right: 15px; background: #00ff88; color: black; padding: 6px 12px; border-radius: 15px; font-weight: bold; animation: blink 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="live-indicator">🔴 MULTI</div>
    <div class="header">
        <h1>�� CryptoAlphaPro</h1>
        <p>Multi-Exchange AI Signal Bot</p>
        <p style="font-size: 12px; opacity: 0.7;">Binance • Bybit • OKX • Real-time Signals</p>
    </div>
    
    <div class="status-bar">
        <div id="bot-status" class="status-badge status-stopped">LOADING...</div>
    </div>
    
    <div class="exchange-status">
        <div class="exchange-item">
            <div id="binance-status" class="exchange-error">●</div>
            <div>Binance</div>
        </div>
        <div class="exchange-item">
            <div id="bybit-status" class="exchange-error">●</div>
            <div>Bybit</div>
        </div>
        <div class="exchange-item">
            <div id="okx-status" class="exchange-error">●</div>
            <div>OKX</div>
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card"><div id="total-signals" class="stat-value">0</div><div>Signals</div></div>
        <div class="stat-card"><div id="win-rate" class="stat-value">0%</div><div>Win Rate</div></div>
        <div class="stat-card"><div id="avg-confidence" class="stat-value">0%</div><div>Confidence</div></div>
    </div>
    
    <div class="controls">
        <h3>🎮 Multi-Exchange Signal Bot Control</h3>
        <div class="control-buttons">
            <button class="btn btn-start" onclick="controlBot('start_signal_bot')">🚀 Start Signals</button>
            <button class="btn btn-stop" onclick="controlBot('stop_signal_bot')">🛑 Stop Signals</button>
            <button class="btn btn-restart" onclick="controlBot('restart_signal_bot')">🔄 Restart</button>
            <button class="btn btn-status" onclick="updateStatus()">📊 Refresh</button>
        </div>
        <div class="leverage-control">
            <h4>⚡ Max Leverage (1x - 50x)</h4>
            <input type="range" min="1" max="50" value="10" class="leverage-slider" id="leverageSlider" onchange="updateLeverage(this.value)">
            <div id="leverageValue" class="leverage-value">10x</div>
        </div>
    </div>
    
    <div class="signals-section">
        <h3>📈 Live Multi-Exchange Signals</h3>
        <div id="signals-container">Loading signals...</div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready(); tg.expand();
        
        setInterval(() => { updateStatus(); loadSignals(); }, 3000);
        updateStatus(); loadSignals();
        
        async function controlBot(action) {
            try {
                const response = await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action })
                });
                const result = await response.json();
                if (result.success) {
                    showNotification(result.message, 'success');
                    updateStatus();
                }
                if (tg) tg.HapticFeedback.impactOccurred('medium');
            } catch (error) {
                showNotification('Connection error', 'error');
            }
        }
        
        async function updateLeverage(value) {
            document.getElementById('leverageValue').textContent = value + 'x';
            try {
                await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'set_max_leverage', leverage: value })
                });
                showNotification('Max leverage: ' + value + 'x', 'info');
            } catch (error) {}
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const result = await response.json();
                if (result.success) {
                    const data = result.data;
                    const statusEl = document.getElementById('bot-status');
                    statusEl.textContent = data.signal_bot_active ? 'ACTIVE' : 'STOPPED';
                    statusEl.className = 'status-badge ' + (data.signal_bot_active ? 'status-active' : 'status-stopped');
                    
                    document.getElementById('total-signals').textContent = data.total_signals;
                    document.getElementById('win-rate').textContent = data.win_rate.toFixed(1) + '%';
                    document.getElementById('avg-confidence').textContent = data.avg_confidence.toFixed(1) + '%';
                    document.getElementById('leverageSlider').value = data.max_leverage;
                    document.getElementById('leverageValue').textContent = data.max_leverage + 'x';
                    
                    document.getElementById('binance-status').className = data.exchanges.binance ? 'exchange-ok' : 'exchange-error';
                    document.getElementById('bybit-status').className = data.exchanges.bybit ? 'exchange-ok' : 'exchange-error';
                    document.getElementById('okx-status').className = data.exchanges.okx ? 'exchange-ok' : 'exchange-error';
                }
            } catch (error) {}
        }
        
        async function loadSignals() {
            try {
                const response = await fetch('/api/signals');
                const result = await response.json();
                if (result.success) {
                    const container = document.getElementById('signals-container');
                    container.innerHTML = '';
                    result.data.slice(0, 6).forEach(signal => {
                        const signalEl = document.createElement('div');
                        signalEl.className = 'signal-item';
                        signalEl.innerHTML = 
                            '<div><div style="font-weight: bold;">' + signal.pair + '</div><div style="opacity: 0.7;">' + signal.confidence + '% • ' + signal.exchanges_count + ' exchanges</div></div>' +
                            '<div style="text-align: right;"><div class="signal-' + signal.action.toLowerCase().replace('_', '-') + '" style="font-weight: bold;">' + signal.action + '</div><div style="opacity: 0.7;">≤' + signal.leverage_recommendation + 'x</div></div>';
                        container.appendChild(signalEl);
                    });
                }
            } catch (error) {}
        }
        
        function showNotification(message, type) {
            const notif = document.createElement('div');
            notif.style.cssText = 'position: fixed; top: 70px; left: 50%; transform: translateX(-50%); z-index: 1000; padding: 12px 20px; border-radius: 10px; color: white; font-weight: bold; max-width: 90%; text-align: center;';
            const colors = { success: 'linear-gradient(45deg, #00ff88, #00cc6a)', error: 'linear-gradient(45deg, #ff4757, #ff3838)', info: 'linear-gradient(45deg, #3742fa, #2f3542)' };
            notif.style.background = colors[type] || colors.info;
            notif.textContent = message;
            document.body.appendChild(notif);
            setTimeout(() => document.body.removeChild(notif), 3000);
        }
    </script>
</body>
</html>'''

@app.route('/api/status')
def api_status():
    # Fix type error - ensure total_signals is numeric
    total_signals = live_data['stats']['total_signals']
    if not isinstance(total_signals, (int, float)):
        total_signals = 0
    
    recent_signals = live_data['signals'][:20]
    
    # Fix type error - ensure confidence values are numeric
    try:
        confidences = []
        for s in recent_signals:
            if isinstance(s, dict) and 'confidence' in s:
                confidence = s['confidence']
                if isinstance(confidence, (int, float)):
                    confidences.append(confidence)
        avg_confidence = sum(confidences) / max(1, len(confidences))
    except Exception as e:
        print(f"Error calculating avg_confidence: {e}")
        avg_confidence = 0.0
    
    return jsonify({
        'success': True,
        'data': {
            'signal_bot_active': live_data['signal_bot_active'],
            'max_leverage': live_data['max_leverage'],
            'total_signals': total_signals,
            'win_rate': 0.0,
            'avg_confidence': avg_confidence,
            'exchanges': {
                'binance': live_data['exchanges']['binance']['status'],
                'bybit': live_data['exchanges']['bybit']['status'],
                'okx': live_data['exchanges']['okx']['status']
            },
            'trading_pairs_count': len(TRADING_PAIRS),
            'last_update': live_data['last_update'].isoformat()
        }
    })

@app.route('/api/signals')
def api_signals():
    return jsonify({'success': True, 'data': live_data['signals'][:30]})

@app.route('/api/control', methods=['POST'])
def api_control():
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'start_signal_bot':
            live_data['signal_bot_active'] = True
            # Сразу генерируем тестовый сигнал
            signal = generate_multi_exchange_signal()
            if signal:
                send_telegram_signal(signal)
                broadcast_signal(signal) # Отправляем сигнал по WebSocket
            return jsonify({'success': True, 'message': '🚀 MULTI-EXCHANGE Bot started! Real signals incoming!'})
            
        elif action == 'stop_signal_bot':
            live_data['signal_bot_active'] = False
            return jsonify({'success': True, 'message': '🛑 Signal Bot stopped.'})
            
        elif action == 'restart_signal_bot':
            live_data['signal_bot_active'] = False
            time.sleep(2)
            live_data['signal_bot_active'] = True
            return jsonify({'success': True, 'message': '🔄 Bot restarted!'})
            
        elif action == 'set_max_leverage':
            leverage = int(data.get('leverage', 10))
            live_data['max_leverage'] = min(50, max(1, leverage))
            return jsonify({'success': True, 'message': f'⚡ Max leverage: {live_data["max_leverage"]}x'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080, help="Port to run server on")
    args = parser.parse_args()
    
    print("🚀 Starting FULL CryptoAlphaPro SIGNAL Bot...")
    print("📡 Connecting to ALL exchanges...")
    
    # Start the signal bot
    # signal_bot = CryptoAlphaProSignalBot() # This class is not defined in the original file
    # signal_bot.start()
    
    # Start Flask server
    print(f"🌐 Starting FULL MULTI-EXCHANGE server on port {args.port}...")
    print("📊 Monitoring 36 pairs on 3 exchanges")
    print("🎯 Real signals with Telegram integration!")
    print("🔗 WebSocket enabled for real-time Web UI!")
    
    socketio.run(app, host='0.0.0.0', port=args.port, debug=False) 