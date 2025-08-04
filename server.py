#!/usr/bin/env python3
"""
🚀 CryptoAlphaPro SIGNAL Bot - Рабочая версия
Все биржи + внешние API + AI анализ + Telegram
"""
from flask import Flask, jsonify, request
import requests
import hashlib
import hmac
import time
import threading
import json
from datetime import datetime
import os
import random

app = Flask(__name__)

# 🔐 РЕАЛЬНЫЕ API КЛЮЧИ
API_KEYS = {
    'binance': {
        'key': 'UGPsFwnP6Sirw5V1aL3xeOwMr7wzWm1eigxDNb2wrJRs3fWP3QDnOjIwVCeipczV',
        'secret': 'jmA0MyvImfAvMu3KdJ32AkdajzIK2YE1U236KcpiTQRL9ItkM6aqil1jh73XEfPe'
    },
    'bybit': {
        'key': 'mWoHS9ONHT2EzePncI',
        'secret': 'b3rUJND24b9OPlmmwKo4Qv6E0ipqYUHTXr9x'
    },
    'okx': {
        'key': 'a7f94985-9865-495f-a3f9-e681ab1742d',
        'secret': '5BE33E5B1802F25F08D28D902EB71970',
        'passphrase': 'Baks1982'
    },
    'telegram': {
        'token': '8243982780:AAHb72Vjf76iIbiS-khO0dLkkmgvsbKKobg',
        'chat_id': '5333574230'
    }
}

# 📊 ВСЕ ТОРГОВЫЕ ПАРЫ
TRADING_PAIRS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT', 'SOL/USDT',
    'DOT/USDT', 'AVAX/USDT', 'LUNA/USDT', 'LINK/USDT', 'MATIC/USDT', 'ALGO/USDT',
    'UNI/USDT', 'SUSHI/USDT', 'CAKE/USDT', 'COMP/USDT', 'AAVE/USDT', 'MKR/USDT',
    'LRC/USDT', 'IMX/USDT', 'METIS/USDT', 'AXS/USDT', 'SAND/USDT', 'MANA/USDT',
    'ENJ/USDT', 'GALA/USDT', 'DOGE/USDT', 'SHIB/USDT', 'FLOKI/USDT', 'PEPE/USDT',
    'FTT/USDT', 'NEAR/USDT', 'ATOM/USDT', 'FTM/USDT', 'ONE/USDT', 'HBAR/USDT'
]

# 📈 ДАННЫЕ БОТА
live_data = {
    'signal_bot_active': False,
    'max_leverage': 10,
    'signals': [],
    'exchanges': {
        'binance': {'prices': {}, 'status': False},
        'bybit': {'prices': {}, 'status': False},
        'okx': {'prices': {}, 'status': False}
    },
    'stats': {
        'total_signals': 0,
        'successful_signals': 0,
        'win_rate': 0.0,
        'avg_confidence': 0.0
    },
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
                        'volume': float(ticker['volume']),
                        'high': float(ticker['highPrice']),
                        'low': float(ticker['lowPrice'])
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
                        'volume': float(ticker.get('volume24h', 0)),
                        'high': float(ticker.get('highPrice24h', 0)),
                        'low': float(ticker.get('lowPrice24h', 0))
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
                    change_24h = float(ticker.get('sodUtc8', 0)) * 100
                    prices[symbol_formatted] = {
                        'price': float(ticker['last']),
                        'change_24h': change_24h,
                        'volume': float(ticker.get('vol24h', 0)),
                        'high': float(ticker.get('high24h', 0)),
                        'low': float(ticker.get('low24h', 0))
                    }
            
            live_data['exchanges']['okx']['prices'] = prices
            live_data['exchanges']['okx']['status'] = True
            print(f"📊 OKX: {len(prices)} pairs updated")
            return prices
    except Exception as e:
        live_data['exchanges']['okx']['status'] = False
        print(f"❌ OKX error: {e}")
        return {}

def generate_ai_signal():
    """Генерация AI сигнала на основе данных всех бирж"""
    
    # Находим активные пары
    available_pairs = []
    for pair in TRADING_PAIRS:
        if (live_data['exchanges']['binance']['prices'].get(pair) or 
            live_data['exchanges']['bybit']['prices'].get(pair) or 
            live_data['exchanges']['okx']['prices'].get(pair)):
            available_pairs.append(pair)
    
    if not available_pairs:
        return None
    
    selected_pair = random.choice(available_pairs[:20])  # Топ 20 пар
    
    # Получаем данные
    binance_data = live_data['exchanges']['binance']['prices'].get(selected_pair, {})
    bybit_data = live_data['exchanges']['bybit']['prices'].get(selected_pair, {})
    okx_data = live_data['exchanges']['okx']['prices'].get(selected_pair, {})
    
    # Анализируем данные
    all_data = [binance_data, bybit_data, okx_data]
    valid_data = [d for d in all_data if d]
    
    if not valid_data:
        return None
    
    # Средние значения
    avg_price = sum(d.get('price', 0) for d in valid_data) / len(valid_data)
    avg_change = sum(d.get('change_24h', 0) for d in valid_data) / len(valid_data)
    total_volume = sum(d.get('volume', 0) for d in valid_data)
    
    # AI логика
    if avg_change > 5:
        action = 'STRONG_BUY'
        confidence = min(95, 85 + abs(avg_change))
    elif avg_change > 2:
        action = 'BUY'
        confidence = min(90, 75 + abs(avg_change) * 2)
    elif avg_change < -5:
        action = 'STRONG_SELL'
        confidence = min(95, 85 + abs(avg_change))
    elif avg_change < -2:
        action = 'SELL'
        confidence = min(90, 75 + abs(avg_change) * 2)
    else:
        action = 'HOLD'
        confidence = 65 + abs(avg_change) * 3
    
    # Рекомендация плеча
    volatility = abs(avg_change) / 100
    if confidence > 90 and volatility < 0.02:
        leverage_rec = min(live_data['max_leverage'], 30)
    elif confidence > 80 and volatility < 0.05:
        leverage_rec = min(live_data['max_leverage'], 20)
    else:
        leverage_rec = min(live_data['max_leverage'], 10)
    
    signal = {
        'id': int(time.time()),
        'pair': selected_pair,
        'action': action,
        'confidence': round(confidence, 1),
        'exchanges_count': len(valid_data),
        'avg_price': round(avg_price, 6),
        'change_24h': round(avg_change, 2),
        'volume': int(total_volume),
        'leverage_recommendation': leverage_rec,
        'timestamp': datetime.now().isoformat(),
        'time_ago': '0 min ago'
    }
    
    live_data['signals'].insert(0, signal)
    if len(live_data['signals']) > 100:
        live_data['signals'] = live_data['signals'][:100]
    
    live_data['stats']['total_signals'] += 1
    
    print(f"🎯 NEW SIGNAL: {signal['pair']} {signal['action']} ({signal['confidence']}%) - {signal['exchanges_count']} exchanges")
    
    return signal

def send_telegram_message(signal):
    """Отправка сигнала в Telegram"""
    try:
        message = f"""🎯 <b>MULTI-EXCHANGE AI SIGNAL</b>

📊 <b>{signal['pair']}</b>
🔥 <b>{signal['action']}</b>
🎯 <b>{signal['confidence']}%</b> confidence

💰 Average Price: ${signal['avg_price']:.6f}
📈 24h Change: {signal['change_24h']:+.2f}%
📊 Volume: {signal['volume']:,}

⚡ Recommended Leverage: ≤{signal['leverage_recommendation']}x
🏛️ Active Exchanges: {signal['exchanges_count']}/3

#CryptoAlphaPro #MultiExchange #{signal['pair'].replace('/', '')}"""

        tg_token = API_KEYS['telegram']['token']
        tg_chat = API_KEYS['telegram']['chat_id']
        url = f'https://api.telegram.org/bot{tg_token}/sendMessage'
        
        data = {
            'chat_id': tg_chat,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def data_updater():
    """Фоновое обновление данных"""
    while True:
        try:
            current_time = int(time.time())
            
            # Обновляем биржи каждые 20 секунд
            if current_time % 20 == 0:
                fetch_binance_data()
                fetch_bybit_data()
                fetch_okx_data()
            
            # Генерируем сигнал каждые 2 минуты (если бот активен)
            if current_time % 120 == 0 and live_data['signal_bot_active']:
                signal = generate_ai_signal()
                if signal:
                    send_telegram_message(signal)
            
            live_data['last_update'] = datetime.now()
            
        except Exception as e:
            print(f"❌ Updater error: {e}")
        
        time.sleep(10)

# Инициализация
print("🚀 Starting CryptoAlphaPro SIGNAL Bot...")
print("📡 Connecting to exchanges...")

fetch_binance_data()
fetch_bybit_data()
fetch_okx_data()

updater_thread = threading.Thread(target=data_updater, daemon=True)
updater_thread.start()
print("🔄 Data updater started!")

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
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 20px; min-height: 100vh;
        }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 {
            font-size: 24px; background: linear-gradient(45deg, #00ff88, #00d4ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px;
        }
        .status-bar { display: flex; justify-content: center; margin-bottom: 20px; }
        .status-badge { padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 13px; animation: pulse 2s infinite; }
        .status-active { background: linear-gradient(45deg, #00ff88, #00cc6a); }
        .status-stopped { background: linear-gradient(45deg, #ff4757, #ff3838); }
        .exchange-status { display: flex; justify-content: space-around; margin: 15px 0; font-size: 12px; }
        .exchange-item { text-align: center; }
        .exchange-ok { color: #00ff88; }
        .exchange-error { color: #ff4757; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
        .stat-card {
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 12px;
            padding: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.2);
        }
        .stat-value { font-size: 18px; font-weight: bold; margin-bottom: 3px; }
        .stat-label { opacity: 0.7; font-size: 11px; }
        .controls {
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px;
            padding: 20px; margin-bottom: 20px;
        }
        .control-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
        .btn { padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 12px; }
        .btn-start { background: linear-gradient(45deg, #00ff88, #00cc6a); }
        .btn-stop { background: linear-gradient(45deg, #ff4757, #ff3838); }
        .btn-restart { background: linear-gradient(45deg, #3742fa, #2f3542); }
        .btn-status { background: linear-gradient(45deg, #ffa502, #ff8c00); }
        .leverage-slider { width: 100%; margin: 8px 0; }
        .leverage-value { text-align: center; font-size: 20px; font-weight: bold; color: #00d4ff; }
        .signals-section { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 15px; }
        .signal-item {
            display: flex; justify-content: space-between; align-items: center; padding: 8px;
            background: rgba(255,255,255,0.05); border-radius: 6px; margin-bottom: 8px; font-size: 11px;
        }
        .signal-buy { color: #00ff88; }
        .signal-sell { color: #ff4757; }
        .signal-strong-buy { color: #00ff88; font-weight: bold; }
        .signal-strong-sell { color: #ff4757; font-weight: bold; }
        .signal-hold { color: #ffa502; }
        .live-indicator {
            position: fixed; top: 10px; right: 10px; background: #00ff88; color: black;
            padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; animation: blink 1s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="live-indicator">🔴 LIVE</div>
    <div class="header">
        <h1>🚀 CryptoAlphaPro</h1>
        <p>Multi-Exchange AI Signal Bot</p>
        <p style="font-size: 11px; opacity: 0.7;">36 pairs • 3 exchanges • Real-time signals</p>
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
        <div class="stat-card"><div id="total-signals" class="stat-value">0</div><div class="stat-label">Total Signals</div></div>
        <div class="stat-card"><div id="win-rate" class="stat-value">0%</div><div class="stat-label">Win Rate</div></div>
        <div class="stat-card"><div id="avg-confidence" class="stat-value">0%</div><div class="stat-label">Avg Confidence</div></div>
    </div>
    
    <div class="controls">
        <h3 style="font-size: 16px; margin-bottom: 12px;">🎮 Signal Bot Control</h3>
        <div class="control-buttons">
            <button class="btn btn-start" onclick="controlBot('start_signal_bot')">🚀 Start Signals</button>
            <button class="btn btn-stop" onclick="controlBot('stop_signal_bot')">🛑 Stop Signals</button>
            <button class="btn btn-restart" onclick="controlBot('restart_signal_bot')">🔄 Restart</button>
            <button class="btn btn-status" onclick="updateStatus()">📊 Refresh</button>
        </div>
        <div class="leverage-control">
            <h4 style="font-size: 13px;">⚡ Max Leverage (1x - 50x)</h4>
            <input type="range" min="1" max="50" value="10" class="leverage-slider" id="leverageSlider" onchange="updateLeverage(this.value)">
            <div id="leverageValue" class="leverage-value">10x</div>
        </div>
    </div>
    
    <div class="signals-section">
        <h3 style="font-size: 16px; margin-bottom: 10px;">📈 Recent AI Signals</h3>
        <div id="signals-container">Loading signals...</div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready(); tg.expand();
        
        setInterval(() => { updateStatus(); loadSignals(); }, 5000);
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
                showNotification(`Max leverage: ${value}x`, 'info');
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
                    
                    // Exchange status
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
                    result.data.slice(0, 8).forEach(signal => {
                        const signalEl = document.createElement('div');
                        signalEl.className = 'signal-item';
                        signalEl.innerHTML = 
                            '<div>' +
                                '<div style="font-weight: bold;">' + signal.pair + '</div>' +
                                '<div style="opacity: 0.7;">' + signal.confidence + '% • ' + signal.exchanges_count + '/3</div>' +
                            '</div>' +
                            '<div style="text-align: right;">' +
                                '<div class="signal-' + signal.action.toLowerCase().replace('_', '-') + '" style="font-weight: bold;">' + signal.action + '</div>' +
                                '<div style="opacity: 0.7;">≤' + signal.leverage_recommendation + 'x</div>' +
                            '</div>';
                        container.appendChild(signalEl);
                    });
                }
            } catch (error) {}
        }
        
        function showNotification(message, type) {
            const notif = document.createElement('div');
            notif.style.cssText = 'position: fixed; top: 60px; left: 50%; transform: translateX(-50%); z-index: 1000; padding: 10px 16px; border-radius: 8px; color: white; font-weight: bold; font-size: 12px; max-width: 90%; text-align: center;';
            const colors = { success: 'linear-gradient(45deg, #00ff88, #00cc6a)', error: 'linear-gradient(45deg, #ff4757, #ff3838)', info: 'linear-gradient(45deg, #3742fa, #2f3542)' };
            notif.style.background = colors[type] || colors.info;
            notif.textContent = message;
            document.body.appendChild(notif);
            setTimeout(() => document.body.removeChild(notif), 2500);
        }
    </script>
</body>
</html>'''

@app.route('/api/status')
def api_status():
    """Статус бота"""
    total_signals = live_data['stats']['total_signals']
    successful_signals = live_data['stats']['successful_signals']
    win_rate = (successful_signals / max(1, total_signals)) * 100
    
    recent_signals = live_data['signals'][:20]
    avg_confidence = sum(s['confidence'] for s in recent_signals) / max(1, len(recent_signals))
    
    return jsonify({
        'success': True,
        'data': {
            'signal_bot_active': live_data['signal_bot_active'],
            'max_leverage': live_data['max_leverage'],
            'total_signals': total_signals,
            'win_rate': win_rate,
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
    """Последние сигналы"""
    return jsonify({
        'success': True,
        'data': live_data['signals'][:50]
    })

@app.route('/api/control', methods=['POST'])
def api_control():
    """Управление ботом"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'start_signal_bot':
            live_data['signal_bot_active'] = True
            return jsonify({'success': True, 'message': f'🚀 SIGNAL Bot started! Monitoring {len(TRADING_PAIRS)} pairs on 3 exchanges.'})
            
        elif action == 'stop_signal_bot':
            live_data['signal_bot_active'] = False
            return jsonify({'success': True, 'message': '🛑 SIGNAL Bot stopped. No more signals will be generated.'})
            
        elif action == 'restart_signal_bot':
            live_data['signal_bot_active'] = False
            time.sleep(2)
            live_data['signal_bot_active'] = True
            return jsonify({'success': True, 'message': '🔄 SIGNAL Bot restarted with fresh data!'})
            
        elif action == 'set_max_leverage':
            leverage = int(data.get('leverage', 10))
            live_data['max_leverage'] = min(50, max(1, leverage))
            return jsonify({'success': True, 'message': f'⚡ Max leverage set to {live_data["max_leverage"]}x'})
            
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print(f"🌐 Starting SIGNAL server on port 8080...")
    print(f"📊 Monitoring {len(TRADING_PAIRS)} trading pairs")
    print("🏛️ Exchanges: Binance, Bybit, OKX")
    print("🎯 SIGNAL Bot ready to generate signals!")
    
    app.run(host='0.0.0.0', port=8080, debug=False) 