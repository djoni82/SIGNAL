import asyncio
import json
import logging
import websockets
import time
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

class BinanceWSClient:
    """
    Direct WebSocket client for Binance Futures (Public Data).
    Provides real-time Funding Rates, Open Interest, and Liquidations.
    """
    
    def __init__(self, symbols: List[str]):
        # Store original keys for data storage (e.g. BTC/USDT:USDT)
        self.original_symbols = symbols
        # Generate stream names (e.g. BTCUSDT)
        self.symbols = []
        self.stream_to_ccxt = {}
        
        for orig in symbols:
            # Strip CCXT additions: "BTC/USDT:USDT" -> "BTCUSDT"
            stream_part = orig.split(':')[0].replace('/', '').lower()
            self.symbols.append(stream_part)
            # Map "BTCUSDT" -> "BTC/USDT:USDT"
            self.stream_to_ccxt[stream_part.upper()] = orig
            
        # Store data with EXACT keys passed during init
        self.data = {
            s: {
                'funding_rate': 0.0,
                'open_interest': 0.0,
                'last_liq_buy': 0.0,
                'last_liq_sell': 0.0,
                'liq_volume_ratio': 1.0,
                'timestamp': 0
            } for s in symbols
        }
        self.running = False
        self._tasks: List[asyncio.Task] = []
        self._start_time = 0

    def is_connected(self) -> bool:
        """Returns True if the client is running and healthy."""
        if not self.running: return False
        if time.time() - self._start_time < 60:
            return True
        now_ms = time.time() * 1000
        for d in self.data.values():
            if d['timestamp'] > 0 and (now_ms - d['timestamp']) < 180000: # 3 min stale check
                return True
        return False

    async def stop(self):
        """Stops all WebSocket tasks."""
        self.running = False
        for task in self._tasks:
            task.cancel()
        self._tasks = []

    async def restart(self):
        """Restarts the client."""
        await self.stop()
        await asyncio.sleep(2)
        await self.start()

    async def start(self):
        """Starts the WebSocket event loop using Combined Streams."""
        if self.running: return
        self.running = True
        self._start_time = time.time()
        logger.info(f"🚀 [WS] Initializing Binance WS for {len(self.symbols)} symbols...")
        
        streams = []
        for s in self.symbols:
            streams.append(f"{s}@markPrice")
            streams.append(f"{s}@openInterest")
            streams.append(f"{s}@forceOrder")
            
        # Split into smaller chunks (Max 50 streams per connection recommended)
        chunk_size = 20
        for i in range(0, len(streams), chunk_size):
            chunk = streams[i:i + chunk_size]
            self._tasks.append(asyncio.create_task(self._listen_combined_streams(chunk)))

    async def _listen_combined_streams(self, streams: List[str]):
        """Listens to a combined stream of multiple events."""
        stream_str = "/".join(streams)
        url = f"wss://fstream.binance.com/stream?streams={stream_str}"
        
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    logger.info(f"✅ [WS] Connected to {len(streams)} streams")
                    while self.running:
                        msg = await ws.recv()
                        payload = json.loads(msg)
                        
                        stream_name = payload.get('stream')
                        data = payload.get('data')
                        if not stream_name or not data: continue
                            
                        symbol_raw = stream_name.split('@')[0].upper()
                        target_key = self.stream_to_ccxt.get(symbol_raw)
                        if not target_key: continue
                            
                        # Update timestamp
                        event_time = data.get('E', int(time.time() * 1000))
                        self.data[target_key]['timestamp'] = event_time
                        
                        # 1. MARK PRICE (Funding Rate)
                        if 'markPrice' in stream_name:
                            if 'r' in data:
                                self.data[target_key]['funding_rate'] = float(data['r'])
                                
                        # 2. OPEN INTEREST
                        elif 'openInterest' in stream_name:
                             if 'o' in data:
                                self.data[target_key]['open_interest'] = float(data['o'])
                                
                        # 3. LIQUIDATIONS
                        elif 'forceOrder' in stream_name:
                            order = data.get('o', {})
                            side = order.get('S')
                            q = float(order.get('q', 0))
                            p = float(order.get('p', 0))
                            usd_val = q * p
                            
                            if side == 'BUY':
                                self.data[target_key]['last_liq_buy'] += usd_val
                            else:
                                self.data[target_key]['last_liq_sell'] += usd_val
                                
                            total_liq = self.data[target_key]['last_liq_buy'] + self.data[target_key]['last_liq_sell']
                            if total_liq > 0:
                                self.data[target_key]['liq_volume_ratio'] = self.data[target_key]['last_liq_sell'] / max(1, self.data[target_key]['last_liq_buy'])
            except Exception as e:
                if self.running:
                    # Silent reconnect for production
                    await asyncio.sleep(5)

    def get_metrics(self, symbol: str) -> Dict:
        """Returns the latest cached metrics for a symbol."""
        target_symbol = symbol
        if target_symbol not in self.data:
            # Fuzzy match for symbols from differnet exchanges
            tag = symbol.split(':')[0].replace('/', '').upper()
            found_key = None
            for key in self.data.keys():
                clean_key = key.split(':')[0].replace('/', '').upper()
                if clean_key == tag:
                    found_key = key
                    break
            if found_key:
                target_symbol = found_key
            else:
                return self._empty_metrics()
        
        d = self.data[target_symbol]
        now_ms = time.time() * 1000
        if d['timestamp'] == 0 or (now_ms - d['timestamp']) > 1800000:
            return self._empty_metrics()
        
        return {
            'funding_rate': d['funding_rate'],
            'open_interest': d['open_interest'],
            'liq_ratio': d['liq_volume_ratio'],
            'is_ws': True
        }

    def _empty_metrics(self) -> Dict:
        return {
            'funding_rate': 0.0,
            'open_interest': 0.0,
            'liq_ratio': 1.0,
            'is_ws': False
        }
