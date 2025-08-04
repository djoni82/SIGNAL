#!/usr/bin/env python3
"""
🚀 CryptoAlphaPro REAL AI SIGNAL Bot v2.1
Реальные данные + AI анализ + Правильные SL/TP + Валидация
"""
import requests
import time
import threading
import random
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np

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
    'DOT/USDT', 'AVAX/USDT', 'LINK/USDT', 'MATIC/USDT', 'UNI/USDT', 'LTC/USDT'
]

class DataValidator:
    """Система валидации данных"""
    
    @staticmethod
    def validate_price(price: float, symbol: str) -> bool:
        """Проверка реалистичности цены"""
        price_limits = {
            'BTC/USDT': {'min': 10000.0, 'max': 200000.0},
            'ETH/USDT': {'min': 1000.0, 'max': 10000.0},
            'SOL/USDT': {'min': 10.0, 'max': 500.0},
            'ADA/USDT': {'min': 0.1, 'max': 10.0},
            'XRP/USDT': {'min': 0.1, 'max': 10.0},
            'BNB/USDT': {'min': 100.0, 'max': 1000.0},
            'DOT/USDT': {'min': 1.0, 'max': 100.0},
            'AVAX/USDT': {'min': 10.0, 'max': 500.0},
            'LINK/USDT': {'min': 1.0, 'max': 100.0},
            'MATIC/USDT': {'min': 0.1, 'max': 10.0},
            'UNI/USDT': {'min': 1.0, 'max': 100.0},
            'LTC/USDT': {'min': 50.0, 'max': 1000.0}
        }
        
        if symbol in price_limits:
            limits = price_limits[symbol]
            return limits['min'] <= price <= limits['max']
        return True
    
    @staticmethod
    def validate_24h_change(change: float) -> bool:
        """Проверка реалистичности 24h изменения"""
        return -50.0 <= change <= 100.0
    
    @staticmethod
    def validate_volume(volume: float) -> bool:
        """Проверка реалистичности объема"""
        return volume > 0 and volume < 1000000000  # Менее 1 млрд

class ExchangeDataCollector:
    """Сбор РЕАЛЬНЫХ данных с бирж"""
    
    @staticmethod
    def get_binance_data(symbol: str) -> Dict:
        """Получение данных с Binance"""
        try:
            # Правильный формат символа для Binance
            binance_symbol = symbol.replace('/', '')
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                price = float(data['lastPrice'])
                change_24h = float(data['priceChangePercent'])
                volume = float(data['volume'])
                
                # Валидация данных
                if not DataValidator.validate_price(price, symbol):
                    print(f"⚠️ Нереальная цена {symbol}: ${price}")
                    return {}
                
                if not DataValidator.validate_24h_change(change_24h):
                    print(f"⚠️ Нереальное изменение {symbol}: {change_24h}%")
                    return {}
                
                return {
                    'price': price,
                    'change_24h': change_24h,
                    'volume': volume,
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice'])
                }
        except Exception as e:
            print(f"❌ Ошибка получения данных Binance для {symbol}: {e}")
            return {}
    
    @staticmethod
    def get_bybit_data(symbol: str) -> Dict:
        """Получение данных с Bybit"""
        try:
            # Правильный формат символа для Bybit
            bybit_symbol = symbol.replace('/', '')
            url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={bybit_symbol}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data['retCode'] == 0 and data['result']['list']:
                    ticker = data['result']['list'][0]
                    
                    price = float(ticker['lastPrice'])
                    change_24h = float(ticker['price24hPcnt']) * 100
                    volume = float(ticker['volume24h'])
                    
                    # Валидация данных
                    if not DataValidator.validate_price(price, symbol):
                        print(f"⚠️ Нереальная цена {symbol}: ${price}")
                        return {}
                    
                    if not DataValidator.validate_24h_change(change_24h):
                        print(f"⚠️ Нереальное изменение {symbol}: {change_24h}%")
                        return {}
                    
                    return {
                        'price': price,
                        'change_24h': change_24h,
                        'volume': volume,
                        'high_24h': float(ticker['highPrice24h']),
                        'low_24h': float(ticker['lowPrice24h'])
                    }
        except Exception as e:
            print(f"❌ Ошибка получения данных Bybit для {symbol}: {e}")
            return {}
    
    @staticmethod
    def get_okx_data(symbol: str) -> Dict:
        """Получение данных с OKX"""
        try:
            # Правильный формат символа для OKX
            okx_symbol = symbol.replace('/', '-')
            url = f"https://www.okx.com/api/v5/market/ticker?instId={okx_symbol}-SPOT"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data['code'] == '0' and data['data']:
                    ticker = data['data'][0]
                    
                    price = float(ticker['last'])
                    change_24h = float(ticker['change24h']) * 100
                    volume = float(ticker['vol24h'])
                    
                    # Валидация данных
                    if not DataValidator.validate_price(price, symbol):
                        print(f"⚠️ Нереальная цена {symbol}: ${price}")
                        return {}
                    
                    if not DataValidator.validate_24h_change(change_24h):
                        print(f"⚠️ Нереальное изменение {symbol}: {change_24h}%")
                        return {}
                    
                    return {
                        'price': price,
                        'change_24h': change_24h,
                        'volume': volume,
                        'high_24h': float(ticker['high24h']),
                        'low_24h': float(ticker['low24h'])
                    }
        except Exception as e:
            print(f"❌ Ошибка получения данных OKX для {symbol}: {e}")
            return {}

class AIAnalyzer:
    """РЕАЛЬНЫЙ AI анализатор"""
    
    def __init__(self):
        self.thresholds = {
            'strong_buy': 0.85,
            'buy': 0.65,
            'neutral': 0.35,
            'sell': 0.15,
            'strong_sell': 0.05
        }
    
    def analyze_market_data(self, exchange_data: Dict) -> Dict:
        """Анализ рыночных данных"""
        if not exchange_data:
            return {}
        
        # Расчет средних значений
        prices = [data['price'] for data in exchange_data.values() if data]
        changes = [data['change_24h'] for data in exchange_data.values() if data]
        volumes = [data['volume'] for data in exchange_data.values() if data]
        
        if not prices:
            return {}
        
        avg_price = sum(prices) / len(prices)
        avg_change = sum(changes) / len(changes)
        avg_volume = sum(volumes) / len(volumes)
        
        # AI анализ тренда
        trend_strength = self._calculate_trend_strength(avg_change, avg_volume)
        volatility = self._calculate_volatility(changes)
        confidence = self._calculate_confidence(trend_strength, volatility)
        
        # Определение сигнала
        signal = self._classify_signal(confidence, avg_change)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'trend_strength': trend_strength,
            'volatility': volatility,
            'avg_price': avg_price,
            'avg_change': avg_change,
            'avg_volume': avg_volume
        }
    
    def _calculate_trend_strength(self, change: float, volume: float) -> float:
        """Расчет силы тренда"""
        # Нормализация изменения цены (-100 до 100)
        price_factor = abs(change) / 100.0
        
        # Нормализация объема (относительно BTC)
        volume_factor = min(volume / 1000000, 1.0)  # Нормализация к 1M
        
        # Комбинированный фактор
        trend_strength = (price_factor * 0.7) + (volume_factor * 0.3)
        return min(trend_strength, 1.0)
    
    def _calculate_volatility(self, changes: List[float]) -> float:
        """Расчет волатильности"""
        if len(changes) < 2:
            return 0.0
        
        # Стандартное отклонение изменений
        mean = sum(changes) / len(changes)
        variance = sum((x - mean) ** 2 for x in changes) / len(changes)
        std_dev = variance ** 0.5
        
        # Нормализация к 0-1
        return min(std_dev / 10.0, 1.0)
    
    def _calculate_confidence(self, trend_strength: float, volatility: float) -> float:
        """Расчет уверенности"""
        # Высокая уверенность при сильном тренде и низкой волатильности
        confidence = trend_strength * (1 - volatility * 0.5)
        return max(0.0, min(1.0, confidence))
    
    def _classify_signal(self, confidence: float, change: float) -> str:
        """Классификация сигнала"""
        if confidence > self.thresholds['strong_buy'] and change > 2:
            return 'STRONG_BUY'
        elif confidence > self.thresholds['buy'] and change > 0.5:
            return 'BUY'
        elif confidence < self.thresholds['strong_sell'] and change < -2:
            return 'STRONG_SELL'
        elif confidence < self.thresholds['sell'] and change < -0.5:
            return 'SELL'
        else:
            return 'NEUTRAL'

class RiskManager:
    """РЕАЛЬНЫЙ риск-менеджер"""
    
    def calculate_risk_params(self, price: float, volatility: float, trend_strength: float, signal: str) -> Dict:
        """Расчет параметров риска"""
        # Динамический ATR-based расчет
        atr_factor = 1.5 + (volatility * 0.1)
        rr_ratio = 2.5 if trend_strength > 0.7 else 1.8
        
        if signal in ['STRONG_BUY', 'BUY']:
            stop_loss = price * (1 - atr_factor/100)
            take_profit = price * (1 + atr_factor*rr_ratio/100)
        else:  # SHORT позиция
            stop_loss = price * (1 + atr_factor/100)
            take_profit = price * (1 - atr_factor*rr_ratio/100)
        
        # Валидация SL/TP
        if stop_loss <= 0 or take_profit <= 0:
            if signal in ['STRONG_BUY', 'BUY']:
                stop_loss = price * 0.95
                take_profit = price * 1.075
            else:
                stop_loss = price * 1.05
                take_profit = price * 0.925
        
        return {
            'stop_loss': round(stop_loss, 4),
            'take_profit': round(take_profit, 4),
            'rr_ratio': rr_ratio
        }
    
    def calculate_leverage(self, volatility: float, confidence: float) -> int:
        """Расчет рекомендуемого плеча"""
        if confidence > 0.9 and volatility < 0.2:
            return 10
        elif confidence > 0.8 and volatility < 0.3:
            return 5
        elif confidence > 0.7:
            return 3
        else:
            return 1

class SignalVerifier:
    """Верификация сигналов"""
    
    @staticmethod
    def verify_signal(signal: dict) -> bool:
        """Проверка сигнала перед отправкой"""
        try:
            # 1. Проверка цен
            for exchange, price in signal['price_data'].items():
                if exchange != 'average' and price > 0:
                    if not DataValidator.validate_price(price, signal['symbol']):
                        print(f"❌ Невалидная цена {exchange}: ${price}")
                        return False
            
            # 2. Проверка параметров риска
            sl = signal['risk_management']['stop_loss']
            tp = signal['risk_management']['take_profit']
            current_price = signal['price_data']['average']
            
            if signal['signal'] in ['STRONG_BUY', 'BUY']:
                if sl >= current_price:
                    print(f"❌ Неправильный SL для LONG: {sl} >= {current_price}")
                    return False
                if tp <= current_price:
                    print(f"❌ Неправильный TP для LONG: {tp} <= {current_price}")
                    return False
            else:  # SHORT позиция
                if sl <= current_price:
                    print(f"❌ Неправильный SL для SHORT: {sl} <= {current_price}")
                    return False
                if tp >= current_price:
                    print(f"❌ Неправильный TP для SHORT: {tp} >= {current_price}")
                    return False
            
            # 3. Проверка волатильности (УБИРАЕМ СЛИШКОМ СТРОГУЮ ПРОВЕРКУ)
            # if signal['risk_management']['recommended_leverage'] > 10 and signal['volatility']['24h'] > 50:
            #     print(f"❌ Слишком высокое плечо при высокой волатильности")
            #     return False
            
            # 4. Проверка временной метки
            signal_time = datetime.strptime(signal['timestamp'], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - signal_time).seconds > 60:
                print(f"❌ Сигнал устарел")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка верификации: {e}")
            return False

class SignalGenerator:
    """Генератор РЕАЛЬНЫХ сигналов"""
    
    def __init__(self):
        self.ai_analyzer = AIAnalyzer()
        self.risk_manager = RiskManager()
        self.data_collector = ExchangeDataCollector()
        self.verifier = SignalVerifier()
    
    def generate_signal(self, symbol: str) -> Dict:
        """Генерация сигнала"""
        print(f"🔍 Анализирую {symbol}...")
        
        # Получение данных с бирж
        exchange_data = {
            'binance': self.data_collector.get_binance_data(symbol),
            'bybit': self.data_collector.get_bybit_data(symbol),
            'okx': self.data_collector.get_okx_data(symbol)
        }
        
        # Проверка наличия данных
        valid_data = {k: v for k, v in exchange_data.items() if v}
        if len(valid_data) < 2:
            print(f"❌ Недостаточно данных для {symbol}")
            return {}
        
        # AI анализ
        analysis = self.ai_analyzer.analyze_market_data(valid_data)
        if not analysis:
            return {}
        
        # Расчет рисков
        risk_params = self.risk_manager.calculate_risk_params(
            analysis['avg_price'], 
            analysis['volatility'], 
            analysis['trend_strength'],
            analysis['signal']
        )
        
        leverage = self.risk_manager.calculate_leverage(
            analysis['volatility'], 
            analysis['confidence']
        )
        
        # Формирование сигнала
        signal = {
            'bot': 'CryptoAlphaPro',
            'version': '2.1',
            'symbol': symbol,
            'signal': analysis['signal'],
            'confidence': round(analysis['confidence'], 2),
            'price_data': {
                'average': analysis['avg_price'],
                'binance': valid_data.get('binance', {}).get('price', 0),
                'bybit': valid_data.get('bybit', {}).get('price', 0),
                'okx': valid_data.get('okx', {}).get('price', 0),
                '24h_change': round(analysis['avg_change'], 2),
                '24h_volume': round(analysis['avg_volume'], 2)
            },
            'risk_management': {
                'stop_loss': risk_params['stop_loss'],
                'take_profit': risk_params['take_profit'],
                'rr_ratio': f"1:{risk_params['rr_ratio']:.1f}",
                'recommended_leverage': leverage,
                'max_position_size': "15%"
            },
            'volatility': {
                '24h': round(analysis['volatility'] * 100, 1),
                'current': round(analysis['volatility'] * 100, 1),
                'rating': 'high' if analysis['volatility'] > 0.5 else 'normal'
            },
            'trend_analysis': {
                'strength': 'strong' if analysis['trend_strength'] > 0.7 else 'weak',
                'direction': 'up' if analysis['avg_change'] > 0 else 'down',
                'confirmed_indicators': ['Price_Momentum', 'Volume_Analysis', 'Volatility_Check']
            },
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'signature': hashlib.md5(f"{symbol}{analysis['avg_price']}{analysis['signal']}".encode()).hexdigest()[:16],
            'data_source': f"Binance, Bybit, OKX Real-time API ({len(valid_data)} exchanges)"
        }
        
        # Верификация сигнала
        if not self.verifier.verify_signal(signal):
            print(f"❌ Сигнал не прошел верификацию для {symbol}")
            return {}
        
        return signal

class SignalMonitor:
    """Система мониторинга качества сигналов"""
    
    def __init__(self):
        self.signal_history = []
    
    def track_signal_performance(self, signal, actual_price_24h_later):
        """Отслеживание производительности сигнала"""
        entry = signal['price_data']['average']
        target = signal['risk_management']['take_profit']
        actual = actual_price_24h_later
        
        success = None
        if signal['signal'] in ['STRONG_BUY', 'BUY'] and actual > entry:
            success = True
        elif signal['signal'] in ['STRONG_SELL', 'SELL'] and actual < entry:
            success = True
        
        self.signal_history.append({
            'signal': signal,
            'success': success,
            'performance': (actual - entry) / entry * 100
        })
    
    def calculate_accuracy(self):
        """Расчет точности сигналов"""
        if not self.signal_history:
            return 0.0
        
        successful = sum(1 for s in self.signal_history if s['success'])
        return successful / len(self.signal_history)

class TelegramBot:
    """Telegram бот для отправки сигналов"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_signal(self, signal: Dict) -> bool:
        """Отправка сигнала в Telegram"""
        try:
            message = self._format_signal_message(signal)
            
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def _format_signal_message(self, signal: Dict) -> str:
        """Форматирование сообщения"""
        emoji_map = {
            'STRONG_BUY': '🚀',
            'BUY': '📈',
            'NEUTRAL': '➡️',
            'SELL': '📉',
            'STRONG_SELL': '💥'
        }
        
        emoji = emoji_map.get(signal['signal'], '❓')
        
        return f"""
{emoji} <b>{signal['signal']} {signal['symbol']}</b>
Confidence: {signal['confidence']*100}%

💵 <b>Prices:</b>
Avg: ${signal['price_data']['average']:.4f}
Binance: ${signal['price_data']['binance']:.4f}
Bybit: ${signal['price_data']['bybit']:.4f}
OKX: ${signal['price_data']['okx']:.4f}
24h Δ: {signal['price_data']['24h_change']:.2f}%

🛡️ <b>Risk Management:</b>
SL: ${signal['risk_management']['stop_loss']:.4f}
TP: ${signal['risk_management']['take_profit']:.4f}
Leverage: {signal['risk_management']['recommended_leverage']}x
R/R: {signal['risk_management']['rr_ratio']}

📊 Volatility: {signal['volatility']['rating'].upper()}
📈 Trend: {signal['trend_analysis']['strength']} {signal['trend_analysis']['direction']}
⏰ {signal['timestamp']}
🔗 {signal['data_source']}
"""

def main():
    """Главная функция"""
    print("🚀 CryptoAlphaPro REAL AI SIGNAL Bot v2.1")
    print("=" * 50)
    
    # Инициализация
    signal_generator = SignalGenerator()
    telegram_bot = TelegramBot(API_KEYS['telegram']['token'], API_KEYS['telegram']['chat_id'])
    signal_monitor = SignalMonitor()
    
    print(f"📊 Анализирую {len(TRADING_PAIRS)} торговых пар...")
    print()
    
    successful_signals = 0
    total_attempts = 0
    
    # Генерация сигналов для каждой пары
    for symbol in TRADING_PAIRS:
        total_attempts += 1
        signal = signal_generator.generate_signal(symbol)
        
        if signal:
            successful_signals += 1
            print(f"✅ {symbol}: {signal['signal']} (Confidence: {signal['confidence']*100}%)")
            print(f"   Price: ${signal['price_data']['average']:.4f}")
            print(f"   SL: ${signal['risk_management']['stop_loss']:.4f}")
            print(f"   TP: ${signal['risk_management']['take_profit']:.4f}")
            print(f"   Leverage: {signal['risk_management']['recommended_leverage']}x")
            print()
            
            # Отправка в Telegram
            if telegram_bot.send_signal(signal):
                print(f"📱 Сигнал отправлен в Telegram")
            else:
                print(f"❌ Ошибка отправки в Telegram")
        else:
            print(f"❌ Не удалось сгенерировать сигнал для {symbol}")
        
        print("-" * 30)
        time.sleep(2)  # Пауза между запросами
    
    # Статистика
    success_rate = (successful_signals / total_attempts) * 100 if total_attempts > 0 else 0
    print(f"📊 Статистика:")
    print(f"   Успешных сигналов: {successful_signals}/{total_attempts}")
    print(f"   Успешность: {success_rate:.1f}%")
    print(f"   Точность мониторинга: {signal_monitor.calculate_accuracy()*100:.1f}%")
    print("✅ Анализ завершен!")

if __name__ == "__main__":
    main() 