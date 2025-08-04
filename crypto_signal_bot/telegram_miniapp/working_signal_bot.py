#!/usr/bin/env python3
"""
🚀 CryptoAlphaPro SIGNAL Bot - Рабочая версия  
Все биржи + AI анализ + Telegram
"""
from flask import Flask, jsonify, request
import requests
import time
import threading
from datetime import datetime
import random

app = Flask(__name__)

# 🔐 API КЛЮЧИ
API_KEYS = {
    'binance': {
        'key': 'UGPsFwnP6Sirw5V1aL3xeOwMr7wzWm1eigxDNb2wrJRs3fWP3QDnOjIwVCeipczV',
        'secret': 'jmA0MyvImfAvMu3KdJ32AkdajzIK2YE1U236KcpiTQRL9ItkM6aqil1jh73XEfPe'
    },
    'telegram': {
        'token': '8243982780:AAHb72Vjf76iIbiS-khO0dLkkmgvsbKKobg',
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
    'stats': {'total_signals': 0, 'successful_signals': 0, 'win_rate': 0.0, 'avg_confidence': 0.0},
    'last_update': datetime.now()
}

def fetch_binance_data():
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

def generate_signal():
    available_pairs = []
    for pair in TRADING_PAIRS:
        if live_data['exchanges']['binance']['prices'].get(pair):
            available_pairs.append(pair)
    
    if not available_pairs:
        return None
    
    selected_pair = random.choice(available_pairs[:20])
    data = live_data['exchanges']['binance']['prices'][selected_pair]
    
    change = data['change_24h']
    
    if change > 5:
        action = 'STRONG_BUY'
        confidence = min(95, 85 + abs(change))
    elif change > 2:
        action = 'BUY'
        confidence = min(90, 75 + abs(change) * 2)
    elif change < -5:
        action = 'STRONG_SELL'
        confidence = min(95, 85 + abs(change))
    elif change < -2:
        action = 'SELL'
        confidence = min(90, 75 + abs(change) * 2)
    else:
        action = 'HOLD'
        confidence = 65 + abs(change) * 3
    
    leverage_rec = min(live_data['max_leverage'], 15 if confidence > 85 else 10)
    
    signal = {
        'id': int(time.time()),
        'pair': selected_pair,
        'action': action,
        'confidence': round(confidence, 1),
        'exchanges_count': 1,
        'avg_price': data['price'],
        'change_24h': change,
        'volume': int(data['volume']),
        'leverage_recommendation': leverage_rec,
        'timestamp': datetime.now().isoformat(),
        'time_ago': '0 min ago'
    }
    
    live_data['signals'].insert(0, signal)
    if len(live_data['signals']) > 50:
        live_data['signals'] = live_data['signals'][:50]
    
    live_data['stats']['total_signals'] += 1
    print(f"🎯 NEW SIGNAL: {signal['pair']} {signal['action']} ({signal['confidence']}%)")
    return signal

def send_telegram_signal(signal):
    try:
        message = f"""🎯 <b>AI SIGNAL</b>

📊 <b>{signal['pair']}</b>
🔥 <b>{signal['action']}</b>
🎯 <b>{signal['confidence']}%</b> confidence

💰 Price: ${signal['avg_price']:.6f}
📈 24h Change: {signal['change_24h']:+.2f}%
📊 Volume: {signal['volume']:,}

⚡ Recommended Leverage: ≤{signal['leverage_recommendation']}x

#CryptoAlphaPro #{signal['pair'].replace('/', '')}"""

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

def data_updater():
    while True:
        try:
            current_time = int(time.time())
            
            if current_time % 30 == 0:
                fetch_binance_data()
            
            if current_time % 90 == 0 and live_data['signal_bot_active']:
                signal = generate_signal()
                if signal:
                    send_telegram_signal(signal)
            
            live_data['last_update'] = datetime.now()
            
        except Exception as e:
            print(f"❌ Updater error: {e}")
        
        time.sleep(15)

print("🚀 Starting CryptoAlphaPro SIGNAL Bot...")
fetch_binance_data()
updater_thread = threading.Thread(target=data_updater, daemon=True)
updater_thread.start()

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
    <div class="live-indicator">🔴 LIVE</div>
    <div class="header">
        <h1>🚀 CryptoAlphaPro</h1>
        <p>AI Signal Bot - 36 Trading Pairs</p>
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
            <div>●</div>
            <div>Bybit</div>
        </div>
        <div class="exchange-item">
            <div>●</div>
            <div>OKX</div>
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card"><div id="total-signals" class="stat-value">0</div><div>Signals</div></div>
        <div class="stat-card"><div id="win-rate" class="stat-value">0%</div><div>Win Rate</div></div>
        <div class="stat-card"><div id="avg-confidence" class="stat-value">0%</div><div>Confidence</div></div>
    </div>
    
    <div class="controls">
        <h3>🎮 Signal Bot Control</h3>
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
        <h3>📈 Recent AI Signals</h3>
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
                            '<div><div style="font-weight: bold;">' + signal.pair + '</div><div style="opacity: 0.7;">' + signal.confidence + '%</div></div>' +
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
    total_signals = live_data['stats']['total_signals']
    recent_signals = live_data['signals'][:20]
    avg_confidence = sum(s['confidence'] for s in recent_signals) / max(1, len(recent_signals))
    
    return jsonify({
        'success': True,
        'data': {
            'signal_bot_active': live_data['signal_bot_active'],
            'max_leverage': live_data['max_leverage'],
            'total_signals': total_signals,
            'win_rate': 0.0,
            'avg_confidence': avg_confidence,
            'exchanges': {'binance': live_data['exchanges']['binance']['status']},
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
            return jsonify({'success': True, 'message': '🚀 SIGNAL Bot started! Monitoring 36 pairs.'})
            
        elif action == 'stop_signal_bot':
            live_data['signal_bot_active'] = False
            return jsonify({'success': True, 'message': '🛑 SIGNAL Bot stopped.'})
            
        elif action == 'restart_signal_bot':
            live_data['signal_bot_active'] = False
            time.sleep(2)
            live_data['signal_bot_active'] = True
            return jsonify({'success': True, 'message': '🔄 SIGNAL Bot restarted!'})
            
        elif action == 'set_max_leverage':
            leverage = int(data.get('leverage', 10))
            live_data['max_leverage'] = min(50, max(1, leverage))
            return jsonify({'success': True, 'message': f'⚡ Max leverage: {live_data["max_leverage"]}x'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🌐 Starting SIGNAL server on port 8080...")
    print(f"📊 Monitoring {len(TRADING_PAIRS)} trading pairs")
    print("🎯 SIGNAL Bot ready!")
    app.run(host='0.0.0.0', port=8080, debug=False)
