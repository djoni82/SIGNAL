#!/usr/bin/env python3
"""
🚀 Professional WebSocket Connections - Real-time Data Streaming
Binance, Bybit, OKX - Orderbook, Trades, Tickers
"""
import asyncio
import websockets
import json
import logging
import time
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import aiohttp

@dataclass
class OrderBookLevel:
    price: float
    quantity: float
    timestamp: float

@dataclass
class OrderBook:
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: float
    exchange: str

@dataclass
class Trade:
    symbol: str
    price: float
    quantity: float
    side: str  # 'buy' or 'sell'
    timestamp: float
    exchange: str

@dataclass
class Ticker:
    symbol: str
    price: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    timestamp: float
    exchange: str

class BinanceWebSocket:
    """Binance WebSocket Handler"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.base_url = "wss://stream.binance.com:9443/ws/"
        self.connection = None
        
    async def connect(self):
        """Connect to Binance WebSocket"""
        # Format symbols for Binance (btcusdt@depth@100ms@ticker@trade)
        streams = []
        for symbol in self.symbols:
            symbol_lower = symbol.replace('/', '').lower()
            streams.extend([
                f"{symbol_lower}@depth20@100ms",
                f"{symbol_lower}@ticker",
                f"{symbol_lower}@trade"
            ])
        
        stream_name = "/".join(streams)
        url = f"{self.base_url}{stream_name}"
        
        try:
            self.connection = await websockets.connect(url)
            logging.info(f"✅ Binance WebSocket connected: {len(self.symbols)} symbols")
            await self._listen()
        except Exception as e:
            logging.error(f"❌ Binance WebSocket error: {e}")
            await asyncio.sleep(5)
            await self.connect()  # Reconnect
    
    async def _listen(self):
        """Listen for WebSocket messages"""
        async for message in self.connection:
            try:
                data = json.loads(message)
                await self._process_message(data)
            except Exception as e:
                logging.error(f"❌ Binance message error: {e}")
    
    async def _process_message(self, data: dict):
        """Process incoming WebSocket data"""
        if 'stream' not in data:
            return
            
        stream = data['stream']
        payload = data['data']
        
        # Order Book Depth
        if 'depth' in stream:
            symbol = stream.split('@')[0].upper()
            formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"  # BTCUSDT -> BTC/USDT
            
            orderbook = OrderBook(
                symbol=formatted_symbol,
                bids=[OrderBookLevel(float(bid[0]), float(bid[1]), time.time()) 
                      for bid in payload['bids'][:10]],
                asks=[OrderBookLevel(float(ask[0]), float(ask[1]), time.time()) 
                      for ask in payload['asks'][:10]],
                timestamp=time.time(),
                exchange='binance'
            )
            await self.callback('orderbook', orderbook)
        
        # Ticker Data
        elif 'ticker' in stream:
            symbol = payload['s']
            formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"
            
            ticker = Ticker(
                symbol=formatted_symbol,
                price=float(payload['c']),
                volume_24h=float(payload['v']),
                change_24h=float(payload['P']),
                high_24h=float(payload['h']),
                low_24h=float(payload['l']),
                timestamp=time.time(),
                exchange='binance'
            )
            await self.callback('ticker', ticker)
        
        # Trade Data
        elif 'trade' in stream:
            symbol = payload['s']
            formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"
            
            trade = Trade(
                symbol=formatted_symbol,
                price=float(payload['p']),
                quantity=float(payload['q']),
                side='buy' if payload['m'] == False else 'sell',
                timestamp=float(payload['T']) / 1000,
                exchange='binance'
            )
            await self.callback('trade', trade)

class BybitWebSocket:
    """Bybit WebSocket Handler"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.base_url = "wss://stream.bybit.com/v5/public/spot"
        self.connection = None
        
    async def connect(self):
        """Connect to Bybit WebSocket"""
        try:
            self.connection = await websockets.connect(self.base_url)
            
            # Subscribe to channels
            for symbol in self.symbols:
                bybit_symbol = symbol.replace('/', '')  # BTC/USDT -> BTCUSDT
                
                subscribe_msg = {
                    "op": "subscribe",
                    "args": [
                        f"orderbook.20.{bybit_symbol}",
                        f"tickers.{bybit_symbol}",
                        f"publicTrade.{bybit_symbol}"
                    ]
                }
                await self.connection.send(json.dumps(subscribe_msg))
            
            logging.info(f"✅ Bybit WebSocket connected: {len(self.symbols)} symbols")
            await self._listen()
        except Exception as e:
            logging.error(f"❌ Bybit WebSocket error: {e}")
            await asyncio.sleep(5)
            await self.connect()
    
    async def _listen(self):
        """Listen for WebSocket messages"""
        async for message in self.connection:
            try:
                data = json.loads(message)
                await self._process_message(data)
            except Exception as e:
                logging.error(f"❌ Bybit message error: {e}")
    
    async def _process_message(self, data: dict):
        """Process Bybit WebSocket data"""
        if 'topic' not in data:
            return
            
        topic = data['topic']
        payload = data['data']
        
        # Order Book
        if 'orderbook' in topic:
            symbol = topic.split('.')[-1]
            formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"
            
            orderbook = OrderBook(
                symbol=formatted_symbol,
                bids=[OrderBookLevel(float(bid[0]), float(bid[1]), time.time()) 
                      for bid in payload.get('b', [])[:10]],
                asks=[OrderBookLevel(float(ask[0]), float(ask[1]), time.time()) 
                      for ask in payload.get('a', [])[:10]],
                timestamp=time.time(),
                exchange='bybit'
            )
            await self.callback('orderbook', orderbook)
        
        # Ticker
        elif 'tickers' in topic:
            symbol = payload['symbol']
            formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"
            
            ticker = Ticker(
                symbol=formatted_symbol,
                price=float(payload['lastPrice']),
                volume_24h=float(payload['volume24h']),
                change_24h=float(payload['price24hPcnt']) * 100,
                high_24h=float(payload['highPrice24h']),
                low_24h=float(payload['lowPrice24h']),
                timestamp=time.time(),
                exchange='bybit'
            )
            await self.callback('ticker', ticker)
        
        # Trades
        elif 'publicTrade' in topic:
            for trade_data in payload:
                symbol = trade_data['s']
                formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"
                
                trade = Trade(
                    symbol=formatted_symbol,
                    price=float(trade_data['p']),
                    quantity=float(trade_data['v']),
                    side=trade_data['S'].lower(),
                    timestamp=float(trade_data['T']) / 1000,
                    exchange='bybit'
                )
                await self.callback('trade', trade)

class OKXWebSocket:
    """OKX WebSocket Handler"""
    
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = symbols
        self.callback = callback
        self.base_url = "wss://ws.okx.com:8443/ws/v5/public"
        self.connection = None
        
    async def connect(self):
        """Connect to OKX WebSocket"""
        try:
            self.connection = await websockets.connect(self.base_url)
            
            # Subscribe to channels
            args = []
            for symbol in self.symbols:
                okx_symbol = symbol.replace('/', '-')  # BTC/USDT -> BTC-USDT
                args.extend([
                    {"channel": "books", "instId": okx_symbol},
                    {"channel": "tickers", "instId": okx_symbol},
                    {"channel": "trades", "instId": okx_symbol}
                ])
            
            subscribe_msg = {"op": "subscribe", "args": args}
            await self.connection.send(json.dumps(subscribe_msg))
            
            logging.info(f"✅ OKX WebSocket connected: {len(self.symbols)} symbols")
            await self._listen()
        except Exception as e:
            logging.error(f"❌ OKX WebSocket error: {e}")
            await asyncio.sleep(5)
            await self.connect()
    
    async def _listen(self):
        """Listen for WebSocket messages"""
        async for message in self.connection:
            try:
                data = json.loads(message)
                await self._process_message(data)
            except Exception as e:
                logging.error(f"❌ OKX message error: {e}")
    
    async def _process_message(self, data: dict):
        """Process OKX WebSocket data"""
        if 'data' not in data:
            return
            
        arg = data.get('arg', {})
        channel = arg.get('channel')
        inst_id = arg.get('instId')
        
        if not channel or not inst_id:
            return
            
        formatted_symbol = inst_id.replace('-', '/')
        payload = data['data'][0] if data['data'] else {}
        
        # Order Book
        if channel == 'books':
            orderbook = OrderBook(
                symbol=formatted_symbol,
                bids=[OrderBookLevel(float(bid[0]), float(bid[1]), time.time()) 
                      for bid in payload.get('bids', [])[:10]],
                asks=[OrderBookLevel(float(ask[0]), float(ask[1]), time.time()) 
                      for ask in payload.get('asks', [])[:10]],
                timestamp=time.time(),
                exchange='okx'
            )
            await self.callback('orderbook', orderbook)
        
        # Ticker
        elif channel == 'tickers':
            ticker = Ticker(
                symbol=formatted_symbol,
                price=float(payload['last']),
                volume_24h=float(payload['vol24h']),
                change_24h=float(payload['sodUtc8']) * 100,
                high_24h=float(payload['high24h']),
                low_24h=float(payload['low24h']),
                timestamp=time.time(),
                exchange='okx'
            )
            await self.callback('ticker', ticker)
        
        # Trades
        elif channel == 'trades':
            trade = Trade(
                symbol=formatted_symbol,
                price=float(payload['px']),
                quantity=float(payload['sz']),
                side=payload['side'],
                timestamp=float(payload['ts']) / 1000,
                exchange='okx'
            )
            await self.callback('trade', trade)

class MultiExchangeWebSocketManager:
    """Manager for all exchange WebSocket connections"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.callbacks = {}
        self.data_handlers = {}
        
        # WebSocket instances
        self.binance_ws = BinanceWebSocket(symbols, self._handle_data)
        self.bybit_ws = BybitWebSocket(symbols, self._handle_data)
        self.okx_ws = OKXWebSocket(symbols, self._handle_data)
        
        # Live data storage
        self.live_data = {
            'orderbooks': {},  # symbol: {exchange: OrderBook}
            'tickers': {},     # symbol: {exchange: Ticker}
            'trades': [],      # Recent trades (last 1000)
            'stats': {
                'messages_per_second': 0,
                'connected_exchanges': 0,
                'last_update': time.time()
            }
        }
        
        logging.basicConfig(level=logging.INFO)
    
    def add_callback(self, data_type: str, callback: Callable):
        """Add callback for specific data type"""
        if data_type not in self.callbacks:
            self.callbacks[data_type] = []
        self.callbacks[data_type].append(callback)
    
    async def _handle_data(self, data_type: str, data):
        """Handle incoming WebSocket data"""
        # Store data
        if data_type == 'orderbook':
            symbol = data.symbol
            if symbol not in self.live_data['orderbooks']:
                self.live_data['orderbooks'][symbol] = {}
            self.live_data['orderbooks'][symbol][data.exchange] = data
            
        elif data_type == 'ticker':
            symbol = data.symbol
            if symbol not in self.live_data['tickers']:
                self.live_data['tickers'][symbol] = {}
            self.live_data['tickers'][symbol][data.exchange] = data
            
        elif data_type == 'trade':
            self.live_data['trades'].append(data)
            # Keep only last 1000 trades
            if len(self.live_data['trades']) > 1000:
                self.live_data['trades'] = self.live_data['trades'][-1000:]
        
        # Update stats
        self.live_data['stats']['last_update'] = time.time()
        
        # Call registered callbacks
        if data_type in self.callbacks:
            for callback in self.callbacks[data_type]:
                try:
                    await callback(data)
                except Exception as e:
                    logging.error(f"❌ Callback error: {e}")
    
    async def start(self):
        """Start all WebSocket connections"""
        tasks = [
            asyncio.create_task(self.binance_ws.connect()),
            asyncio.create_task(self.bybit_ws.connect()),
            asyncio.create_task(self.okx_ws.connect())
        ]
        
        logging.info("🚀 Starting Multi-Exchange WebSocket Manager...")
        await asyncio.gather(*tasks)
    
    def get_best_bid_ask(self, symbol: str) -> Dict:
        """Get best bid/ask across all exchanges"""
        if symbol not in self.live_data['orderbooks']:
            return {}
            
        best_bid = 0
        best_ask = float('inf')
        bid_exchange = None
        ask_exchange = None
        
        for exchange, orderbook in self.live_data['orderbooks'][symbol].items():
            if orderbook.bids:
                bid_price = orderbook.bids[0].price
                if bid_price > best_bid:
                    best_bid = bid_price
                    bid_exchange = exchange
            
            if orderbook.asks:
                ask_price = orderbook.asks[0].price
                if ask_price < best_ask:
                    best_ask = ask_price
                    ask_exchange = exchange
        
        return {
            'symbol': symbol,
            'best_bid': best_bid,
            'best_ask': best_ask if best_ask != float('inf') else 0,
            'bid_exchange': bid_exchange,
            'ask_exchange': ask_exchange,
            'spread': (best_ask - best_bid) if best_ask != float('inf') else 0,
            'spread_percent': ((best_ask - best_bid) / best_bid * 100) if best_bid > 0 and best_ask != float('inf') else 0
        }
    
    def get_arbitrage_opportunities(self, min_spread_percent: float = 0.1) -> List[Dict]:
        """Find arbitrage opportunities"""
        opportunities = []
        
        for symbol in self.live_data['orderbooks']:
            best_prices = self.get_best_bid_ask(symbol)
            if best_prices.get('spread_percent', 0) > min_spread_percent:
                opportunities.append({
                    **best_prices,
                    'profit_potential': best_prices.get('spread_percent', 0),
                    'timestamp': time.time()
                })
        
        return sorted(opportunities, key=lambda x: x['profit_potential'], reverse=True)

# Usage Example
async def main():
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
    
    manager = MultiExchangeWebSocketManager(symbols)
    
    # Add callbacks
    async def on_ticker_update(ticker: Ticker):
        print(f"📊 {ticker.exchange.upper()} {ticker.symbol}: ${ticker.price:.2f} ({ticker.change_24h:+.2f}%)")
    
    async def on_arbitrage_found(data):
        opportunities = manager.get_arbitrage_opportunities(0.2)
        if opportunities:
            opp = opportunities[0]
            print(f"🎯 ARBITRAGE: {opp['symbol']} - {opp['profit_potential']:.2f}% spread")
    
    manager.add_callback('ticker', on_ticker_update)
    
    # Start WebSocket manager
    await manager.start()

if __name__ == "__main__":
    asyncio.run(main()) 