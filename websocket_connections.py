#!/usr/bin/env python3
"""
🔌 WebSocket подключения для CryptoAlphaPro
Реальное время + 100мс частота + Мультибиржевые данные
"""
import asyncio
import websockets
import json
import time
from typing import Dict, List, Callable
from datetime import datetime

class BinanceWebSocket:
    """WebSocket подключение к Binance"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.ws = None
        self.running = False
        
    async def connect(self):
        """Подключение к WebSocket"""
        try:
            # Формируем URL для всех символов
            streams = [f"{symbol.lower()}@ticker" for symbol in self.symbols]
            url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
            
            self.ws = await websockets.connect(url)
            self.running = True
            print(f"✅ Binance WebSocket подключен: {len(self.symbols)} символов")
            
            # Слушаем сообщения
            async for message in self.ws:
                if not self.running:
                    break
                    
                data = json.loads(message)
                await self._process_message(data)
                
        except Exception as e:
            print(f"❌ Binance WebSocket error: {e}")
        finally:
            if self.ws:
                await self.ws.close()
    
    async def _process_message(self, data: Dict):
        """Обработка сообщения"""
        try:
            symbol = data['s']
            price = float(data['c'])
            change_24h = float(data['P'])
            volume = float(data['v'])
            
            tick_data = {
                'exchange': 'binance',
                'symbol': symbol,
                'price': price,
                'change_24h': change_24h,
                'volume': volume,
                'timestamp': datetime.now(),
                'type': 'ticker'
            }
            
            await self.callback(tick_data)
            
        except Exception as e:
            print(f"❌ Binance message processing error: {e}")
    
    async def disconnect(self):
        """Отключение"""
        self.running = False
        if self.ws:
            await self.ws.close()

class BybitWebSocket:
    """WebSocket подключение к Bybit"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.ws = None
        self.running = False
        
    async def connect(self):
        """Подключение к WebSocket"""
        try:
            url = "wss://stream.bybit.com/v5/public/spot"
            self.ws = await websockets.connect(url)
            self.running = True
            print(f"✅ Bybit WebSocket подключен: {len(self.symbols)} символов")
            
            # Подписываемся на тикеры
            subscribe_msg = {
                "op": "subscribe",
                "args": [f"tickers.{symbol}" for symbol in self.symbols]
            }
            await self.ws.send(json.dumps(subscribe_msg))
            
            # Слушаем сообщения
            async for message in self.ws:
                if not self.running:
                    break
                    
                data = json.loads(message)
                await self._process_message(data)
                
        except Exception as e:
            print(f"❌ Bybit WebSocket error: {e}")
        finally:
            if self.ws:
                await self.ws.close()
    
    async def _process_message(self, data: Dict):
        """Обработка сообщения"""
        try:
            if 'data' in data and data['topic'].startswith('tickers.'):
                ticker_data = data['data']
                symbol = ticker_data['symbol']
                price = float(ticker_data['lastPrice'])
                change_24h = float(ticker_data['price24hPcnt']) * 100
                volume = float(ticker_data['volume24h'])
                
                tick_data = {
                    'exchange': 'bybit',
                    'symbol': symbol,
                    'price': price,
                    'change_24h': change_24h,
                    'volume': volume,
                    'timestamp': datetime.now(),
                    'type': 'ticker'
                }
                
                await self.callback(tick_data)
                
        except Exception as e:
            print(f"❌ Bybit message processing error: {e}")
    
    async def disconnect(self):
        """Отключение"""
        self.running = False
        if self.ws:
            await self.ws.close()

class OKXWebSocket:
    """WebSocket подключение к OKX"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.ws = None
        self.running = False
        
    async def connect(self):
        """Подключение к WebSocket"""
        try:
            url = "wss://ws.okx.com:8443/ws/v5/public"
            self.ws = await websockets.connect(url)
            self.running = True
            print(f"✅ OKX WebSocket подключен: {len(self.symbols)} символов")
            
            # Подписываемся на тикеры
            subscribe_msg = {
                "op": "subscribe",
                "args": [{"channel": "tickers", "instId": symbol} for symbol in self.symbols]
            }
            await self.ws.send(json.dumps(subscribe_msg))
            
            # Слушаем сообщения
            async for message in self.ws:
                if not self.running:
                    break
                    
                data = json.loads(message)
                await self._process_message(data)
                
        except Exception as e:
            print(f"❌ OKX WebSocket error: {e}")
        finally:
            if self.ws:
                await self.ws.close()
    
    async def _process_message(self, data: Dict):
        """Обработка сообщения"""
        try:
            if 'data' in data and data['arg']['channel'] == 'tickers':
                ticker_data = data['data'][0]
                symbol = ticker_data['instId']
                price = float(ticker_data['last'])
                change_24h = float(ticker_data['change24h']) * 100
                volume = float(ticker_data['vol24h'])
                
                tick_data = {
                    'exchange': 'okx',
                    'symbol': symbol,
                    'price': price,
                    'change_24h': change_24h,
                    'volume': volume,
                    'timestamp': datetime.now(),
                    'type': 'ticker'
                }
                
                await self.callback(tick_data)
                
        except Exception as e:
            print(f"❌ OKX message processing error: {e}")
    
    async def disconnect(self):
        """Отключение"""
        self.running = False
        if self.ws:
            await self.ws.close()

class MultiExchangeWebSocketManager:
    """Менеджер мультибиржевых WebSocket подключений"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.connections = {}
        self.running = False
        
        # Инициализация подключений
        self.connections['binance'] = BinanceWebSocket(symbols, callback)
        self.connections['bybit'] = BybitWebSocket(symbols, callback)
        self.connections['okx'] = OKXWebSocket(symbols, callback)
    
    async def start(self):
        """Запуск всех подключений"""
        self.running = True
        print("🚀 Запуск мультибиржевых WebSocket подключений...")
        
        # Запускаем все подключения параллельно
        tasks = []
        for exchange, connection in self.connections.items():
            task = asyncio.create_task(connection.connect())
            tasks.append(task)
        
        # Ждем завершения всех задач
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Остановка всех подключений"""
        self.running = False
        print("🛑 Остановка WebSocket подключений...")
        
        for connection in self.connections.values():
            await connection.disconnect()
    
    def get_status(self) -> Dict:
        """Получение статуса подключений"""
        return {
            exchange: connection.running 
            for exchange, connection in self.connections.items()
        }

# Пример использования
async def example_callback(tick_data: Dict):
    """Пример обработчика данных"""
    print(f"📊 {tick_data['exchange'].upper()}: {tick_data['symbol']} = ${tick_data['price']:.4f} ({tick_data['change_24h']:+.2f}%)")

async def main():
    """Пример использования"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    
    manager = MultiExchangeWebSocketManager(symbols, example_callback)
    
    try:
        await manager.start()
    except KeyboardInterrupt:
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(main()) 