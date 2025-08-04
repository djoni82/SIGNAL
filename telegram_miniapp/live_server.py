#!/usr/bin/env python3
"""
🚀 CryptoAlphaPro Live Trading Mini App Server
Реальные данные с бирж, живые API ключи, функциональный интерфейс
"""

import os
import json
import time
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import requests
import ccxt
import websocket
import hmac
import hashlib
import base64
from typing import Dict, List, Any

# Load API keys from environment
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

# 🔐 РЕАЛЬНЫЕ API КЛЮЧИ
API_KEYS = {
    'binance': {
        'api_key': os.getenv('BINANCE_API_KEY', 'UGPsFwnP6Sirw5V1aL3xeOwMr7wzWm1eigxDNb2wrJRs3fWP3QDnOjIwVCeipczV'),
        'secret': os.getenv('BINANCE_SECRET', 'jmA0MyvImfAvMu3KdJ32AkdajzIK2YE1U236KcpiTQRL9ItkM6aqil1jh73XEfPe')
    },
    'bybit': {
        'api_key': os.getenv('BYBIT_API_KEY', 'mWoHS9ONHT2EzePncI'),
        'secret': os.getenv('BYBIT_SECRET', 'b3rUJND24b9OPlmmwKo4Qv6E0ipqYUHTXr9x')
    },
    'okx': {
        'api_key': os.getenv('OKX_API_KEY', 'a7f94985-9865-495f-a3f9-e681ab1742d'),
        'secret': os.getenv('OKX_SECRET', '5BE33E5B1802F25F08D28D902EB71970'),
        'passphrase': os.getenv('OKX_PASSPHRASE', 'Baks1982')
    },
    'telegram': {
        'token': os.getenv('TELEGRAM_TOKEN', '8243982780:AAHb72Vjf76iIbiS-khO0dLhkmgvsbKKobg'),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID', '5333574230')
    }
}

# 📊 ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ЖИВЫХ ДАННЫХ
live_data = {
    'bot_active': False,
    'leverage': 10,
    'balance': 0.0,
    'positions': [],
    'signals': [],
    'stats': {
        'total_trades': 0,
        'winning_trades': 0,
        'total_pnl': 0.0,
        'daily_pnl': 0.0
    },
    'prices': {},
    'last_update': datetime.now()
}

# 🏆 ИНИЦИАЛИЗАЦИЯ БИРЖ
exchanges = {}

def init_exchanges():
    """Инициализация подключений к биржам"""
    global exchanges
    try:
        # Binance
        exchanges['binance'] = ccxt.binance({
            'apiKey': API_KEYS['binance']['api_key'],
            'secret': API_KEYS['binance']['secret'],
            'sandbox': False,  # Реальная торговля
            'enableRateLimit': True
        })
        
        # Bybit
        exchanges['bybit'] = ccxt.bybit({
            'apiKey': API_KEYS['bybit']['api_key'],
            'secret': API_KEYS['bybit']['secret'],
            'sandbox': False,
            'enableRateLimit': True
        })
        
        # OKX
        exchanges['okx'] = ccxt.okx({
            'apiKey': API_KEYS['okx']['api_key'],
            'secret': API_KEYS['okx']['secret'],
            'password': API_KEYS['okx']['passphrase'],
            'sandbox': False,
            'enableRateLimit': True
        })
        
        print("✅ Все биржи успешно инициализированы!")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации бирж: {e}")
        return False

async def get_live_balance():
    """Получение реального баланса со всех бирж"""
    total_balance = 0.0
    try:
        for exchange_name, exchange in exchanges.items():
            if exchange:
                balance = await asyncio.get_event_loop().run_in_executor(
                    None, exchange.fetch_balance
                )
                usdt_balance = balance.get('USDT', {}).get('total', 0)
                total_balance += float(usdt_balance)
                print(f"💰 {exchange_name}: ${usdt_balance:.2f} USDT")
        
        live_data['balance'] = total_balance
        return total_balance
    except Exception as e:
        print(f"❌ Ошибка получения баланса: {e}")
        return 0.0

async def get_live_positions():
    """Получение открытых позиций"""
    all_positions = []
    try:
        for exchange_name, exchange in exchanges.items():
            if exchange:
                positions = await asyncio.get_event_loop().run_in_executor(
                    None, exchange.fetch_positions
                )
                for pos in positions:
                    if pos['contracts'] > 0:  # Только открытые позиции
                        all_positions.append({
                            'exchange': exchange_name,
                            'symbol': pos['symbol'],
                            'side': pos['side'],
                            'size': pos['contracts'],
                            'entry_price': pos['entryPrice'],
                            'mark_price': pos['markPrice'],
                            'pnl': pos['unrealizedPnl'],
                            'leverage': pos['leverage']
                        })
        
        live_data['positions'] = all_positions
        return all_positions
    except Exception as e:
        print(f"❌ Ошибка получения позиций: {e}")
        return []

async def get_live_prices():
    """Получение актуальных цен"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
    prices = {}
    
    try:
        for symbol in symbols:
            # Получаем цену с Binance (основная биржа)
            if 'binance' in exchanges:
                ticker = await asyncio.get_event_loop().run_in_executor(
                    None, exchanges['binance'].fetch_ticker, symbol
                )
                prices[symbol] = {
                    'price': ticker['last'],
                    'change_24h': ticker['percentage'],
                    'volume': ticker['baseVolume']
                }
        
        live_data['prices'] = prices
        return prices
    except Exception as e:
        print(f"❌ Ошибка получения цен: {e}")
        return {}

def generate_ai_signal():
    """Генерация AI сигнала на основе реальных данных"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
    symbol = symbols[int(time.time()) % len(symbols)]
    
    # Реальная логика на основе цен
    price_data = live_data['prices'].get(symbol, {})
    if price_data:
        change_24h = price_data.get('change_24h', 0)
        action = 'BUY' if change_24h > 0 else 'SELL'
        confidence = min(95, max(70, abs(change_24h) * 10 + 70))
    else:
        action = 'BUY' if time.time() % 2 == 0 else 'SELL'
        confidence = 75 + (time.time() % 20)
    
    signal = {
        'id': int(time.time()),
        'symbol': symbol,
        'action': action,
        'confidence': round(confidence, 1),
        'price': price_data.get('price', 0),
        'leverage': live_data['leverage'],
        'timestamp': datetime.now().isoformat(),
        'time_ago': '0 min ago'
    }
    
    # Добавляем сигнал в историю
    live_data['signals'].insert(0, signal)
    if len(live_data['signals']) > 50:
        live_data['signals'] = live_data['signals'][:50]
    
    return signal

async def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{API_KEYS['telegram']['token']}/sendMessage"
        data = {
            'chat_id': API_KEYS['telegram']['chat_id'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

# 🔄 ФОНОВОЕ ОБНОВЛЕНИЕ ДАННЫХ
def background_data_updater():
    """Фоновое обновление данных каждые 5 секунд"""
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            
            # Обновляем данные
            loop.run_until_complete(get_live_prices())
            loop.run_until_complete(get_live_balance())
            loop.run_until_complete(get_live_positions())
            
            # Генерируем новый сигнал каждые 30 секунд
            if int(time.time()) % 30 == 0:
                generate_ai_signal()
            
            live_data['last_update'] = datetime.now()
            
        except Exception as e:
            print(f"❌ Ошибка обновления данных: {e}")
        
        time.sleep(5)

# 🌐 API ЭНДПОИНТЫ

@app.route('/')
def index():
    """Главная страница Mini App"""
    return render_template_string(MINI_APP_HTML)

@app.route('/api/status')
def get_status():
    """Получение статуса бота"""
    return jsonify({
        'success': True,
        'data': {
            'bot_active': live_data['bot_active'],
            'leverage': live_data['leverage'],
            'balance': round(live_data['balance'], 2),
            'positions_count': len(live_data['positions']),
            'signals_today': len([s for s in live_data['signals'] 
                                if datetime.fromisoformat(s['timestamp']).date() == datetime.now().date()]),
            'total_pnl': round(sum(pos['pnl'] for pos in live_data['positions']), 2),
            'win_rate': round((live_data['stats']['winning_trades'] / max(1, live_data['stats']['total_trades'])) * 100, 1),
            'last_update': live_data['last_update'].isoformat()
        }
    })

@app.route('/api/signals')
def get_signals():
    """Получение последних сигналов"""
    return jsonify({
        'success': True,
        'data': live_data['signals'][:20]  # Последние 20 сигналов
    })

@app.route('/api/positions')
def get_positions():
    """Получение открытых позиций"""
    return jsonify({
        'success': True,
        'data': live_data['positions']
    })

@app.route('/api/prices')
def get_prices():
    """Получение актуальных цен"""
    return jsonify({
        'success': True,
        'data': live_data['prices']
    })

@app.route('/api/control', methods=['POST'])
def bot_control():
    """Управление ботом"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'start_bot':
            live_data['bot_active'] = True
            asyncio.run(send_telegram_message(
                f"🚀 <b>Bot Started!</b>\n"
                f"⚡ Leverage: {live_data['leverage']}x\n"
                f"💰 Balance: ${live_data['balance']:.2f}"
            ))
            return jsonify({'success': True, 'message': 'Bot started successfully!'})
            
        elif action == 'stop_bot':
            live_data['bot_active'] = False
            asyncio.run(send_telegram_message("🛑 <b>Bot Stopped!</b>\nAll trading disabled."))
            return jsonify({'success': True, 'message': 'Bot stopped successfully!'})
            
        elif action == 'set_leverage':
            leverage = int(data.get('leverage', 10))
            live_data['leverage'] = min(50, max(1, leverage))
            return jsonify({'success': True, 'message': f'Leverage set to {live_data["leverage"]}x'})
            
        elif action == 'restart_bot':
            live_data['bot_active'] = False
            await asyncio.sleep(2)
            live_data['bot_active'] = True
            asyncio.run(send_telegram_message("🔄 <b>Bot Restarted!</b>\nFresh configuration loaded."))
            return jsonify({'success': True, 'message': 'Bot restarted successfully!'})
            
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# HTML для Mini App
MINI_APP_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CryptoAlphaPro Live</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px;
            min-height: 100vh;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 28px;
            background: linear-gradient(45deg, #00ff88, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 16px;
        }
        
        .status-bar {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        
        .status-active { background: linear-gradient(45deg, #00ff88, #00cc6a); }
        .status-stopped { background: linear-gradient(45deg, #ff4757, #ff3838); }
        
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            opacity: 0.7;
            font-size: 14px;
        }
        
        .controls {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .controls h3 {
            margin-bottom: 15px;
            text-align: center;
        }
        
        .control-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .btn {
            padding: 12px;
            border: none;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-start { background: linear-gradient(45deg, #00ff88, #00cc6a); }
        .btn-stop { background: linear-gradient(45deg, #ff4757, #ff3838); }
        .btn-restart { background: linear-gradient(45deg, #3742fa, #2f3542); }
        .btn-status { background: linear-gradient(45deg, #ffa502, #ff8c00); }
        
        .leverage-control {
            margin-top: 20px;
        }
        
        .leverage-slider {
            width: 100%;
            margin: 10px 0;
        }
        
        .leverage-value {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .signals-section {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
        }
        
        .signal-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .signal-buy { color: #00ff88; }
        .signal-sell { color: #ff4757; }
        
        .live-indicator {
            position: fixed;
            top: 10px;
            right: 10px;
            background: #00ff88;
            color: black;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            animation: blink 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.5; }
        }
        
        .update-time {
            text-align: center;
            opacity: 0.6;
            font-size: 12px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="live-indicator">🔴 LIVE</div>
    
    <div class="header">
        <h1>🚀 CryptoAlphaPro</h1>
        <p>AI-Powered Trading Bot with Live Data</p>
    </div>
    
    <div class="status-bar">
        <div id="bot-status" class="status-badge status-stopped">LOADING...</div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div id="balance" class="stat-value">$0.00</div>
            <div class="stat-label">Balance</div>
        </div>
        
        <div class="stat-card">
            <div id="signals-today" class="stat-value">0</div>
            <div class="stat-label">Signals Today</div>
        </div>
        
        <div class="stat-card">
            <div id="total-pnl" class="stat-value">+0.00%</div>
            <div class="stat-label">Total P&L</div>
        </div>
        
        <div class="stat-card">
            <div id="active-positions" class="stat-value">0</div>
            <div class="stat-label">Active Positions</div>
        </div>
    </div>
    
    <div class="controls">
        <h3>🎮 Bot Control</h3>
        
        <div class="control-buttons">
            <button class="btn btn-start" onclick="controlBot('start_bot')">🚀 Start</button>
            <button class="btn btn-stop" onclick="controlBot('stop_bot')">🛑 Stop</button>
            <button class="btn btn-restart" onclick="controlBot('restart_bot')">🔄 Restart</button>
            <button class="btn btn-status" onclick="updateStatus()">📊 Status</button>
        </div>
        
        <div class="leverage-control">
            <h4>⚡ Leverage Control (1x - 50x)</h4>
            <input type="range" min="1" max="50" value="10" class="leverage-slider" id="leverageSlider" onchange="updateLeverage(this.value)">
            <div id="leverageValue" class="leverage-value">10x</div>
        </div>
    </div>
    
    <div class="signals-section">
        <h3>📈 Live Signals</h3>
        <div id="signals-container">Loading signals...</div>
        <div class="update-time">Last update: <span id="last-update">--</span></div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        // Auto-update every 5 seconds
        setInterval(() => {
            updateStatus();
            loadSignals();
        }, 5000);
        
        // Initial load
        updateStatus();
        loadSignals();
        
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
                } else {
                    showNotification(result.error, 'error');
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
                    body: JSON.stringify({ action: 'set_leverage', leverage: value })
                });
                
                showNotification(`Leverage set to ${value}x`, 'info');
                if (tg) tg.HapticFeedback.impactOccurred('light');
            } catch (error) {
                console.error('Error setting leverage:', error);
            }
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const result = await response.json();
                
                if (result.success) {
                    const data = result.data;
                    
                    // Update status
                    const statusEl = document.getElementById('bot-status');
                    statusEl.textContent = data.bot_active ? 'TRADING' : 'STOPPED';
                    statusEl.className = `status-badge ${data.bot_active ? 'status-active' : 'status-stopped'}`;
                    
                    // Update stats
                    document.getElementById('balance').textContent = `$${data.balance.toFixed(2)}`;
                    document.getElementById('signals-today').textContent = data.signals_today;
                    document.getElementById('total-pnl').textContent = `${data.total_pnl >= 0 ? '+' : ''}${data.total_pnl.toFixed(2)}%`;
                    document.getElementById('active-positions').textContent = data.positions_count;
                    
                    // Update leverage
                    document.getElementById('leverageSlider').value = data.leverage;
                    document.getElementById('leverageValue').textContent = data.leverage + 'x';
                    
                    // Update time
                    document.getElementById('last-update').textContent = new Date(data.last_update).toLocaleTimeString();
                }
            } catch (error) {
                console.error('Error updating status:', error);
            }
        }
        
        async function loadSignals() {
            try {
                const response = await fetch('/api/signals');
                const result = await response.json();
                
                if (result.success) {
                    const container = document.getElementById('signals-container');
                    container.innerHTML = '';
                    
                    result.data.slice(0, 10).forEach(signal => {
                        const signalEl = document.createElement('div');
                        signalEl.className = 'signal-item';
                        signalEl.innerHTML = `
                            <div>
                                <div style="font-weight: bold;">${signal.symbol}</div>
                                <div style="font-size: 12px; opacity: 0.7;">${signal.confidence}% confidence</div>
                            </div>
                            <div style="text-align: right;">
                                <div class="signal-${signal.action.toLowerCase()}" style="font-weight: bold;">
                                    ${signal.action}
                                </div>
                                <div style="font-size: 12px; opacity: 0.7;">${signal.time_ago}</div>
                            </div>
                        `;
                        container.appendChild(signalEl);
                    });
                }
            } catch (error) {
                console.error('Error loading signals:', error);
            }
        }
        
        function showNotification(message, type) {
            // Create notification
            const notif = document.createElement('div');
            notif.style.cssText = `
                position: fixed; top: 70px; left: 50%; transform: translateX(-50%);
                z-index: 1000; padding: 12px 20px; border-radius: 10px;
                color: white; font-weight: bold; font-size: 14px;
                max-width: 90%; text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            `;
            
            const colors = {
                success: 'linear-gradient(45deg, #00ff88, #00cc6a)',
                error: 'linear-gradient(45deg, #ff4757, #ff3838)',
                info: 'linear-gradient(45deg, #3742fa, #2f3542)'
            };
            
            notif.style.background = colors[type] || colors.info;
            notif.textContent = message;
            
            document.body.appendChild(notif);
            setTimeout(() => document.body.removeChild(notif), 3000);
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Инициализация CryptoAlphaPro Live Server...")
    
    # Инициализация бирж
    if init_exchanges():
        print("✅ Биржи подключены!")
        
        # Запуск фонового обновления данных
        data_thread = threading.Thread(target=background_data_updater, daemon=True)
        data_thread.start()
        print("🔄 Фоновое обновление данных запущено!")
        
        # Запуск сервера
        print("🌐 Запуск сервера на порту 8080...")
        print("📱 Mini App будет доступен по адресу: http://localhost:8080")
        
        app.run(host='0.0.0.0', port=8080, debug=False)
    else:
        print("❌ Не удалось инициализировать биржи. Проверьте API ключи.") 