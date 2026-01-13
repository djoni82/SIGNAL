import asyncio
import json
import logging
import websockets
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

    async def start(self):
        """Starts the WebSocket event loop using Combined Streams."""
        if self.running: return
        self.running = True
        logger.info(f"🚀 [WS] Starting Binance Optimized WS for {len(self.symbols)} symbols...")
        
        # Binance limits URL length, so we might need multiple connections if too many streams
        # But for 90 symbols * 3 streams = 270 streams, it might fit or strictly split
        # We'll buffer streams into chunks of 100 to be safe
        
        streams = []
        for s in self.symbols:
            streams.append(f"{s}@markPrice")
            streams.append(f"{s}@openInterest")
            streams.append(f"{s}@forceOrder")
            
        # Split into chunks of 100 streams per connection
        chunk_size = 100
        for i in range(0, len(streams), chunk_size):
            chunk = streams[i:i + chunk_size]
            self._tasks.append(asyncio.create_task(self._listen_combined_streams(chunk)))

    async def _listen_combined_streams(self, streams: List[str]):
        """Listens to a combined stream of multiple events."""
        stream_str = "/".join(streams)
        url = f"wss://fstream.binance.com/stream?streams={stream_str}"
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    logger.info(f"✅ Connected to Combined WS (Chunk {len(streams)} streams)")
                    while self.running:
                        msg = await ws.recv()
                        payload = json.loads(msg)
                        
                        # Payload format: {"stream": "btcusdt@markPrice", "data": {...}}
                        stream_name = payload.get('stream')
                        data = payload.get('data')
                        
                        if not stream_name or not data:
                            continue
                            
                        # Extract symbol from stream name (e.g. "btcusdt@markPrice" -> "BTCUSDT")
                        symbol_raw = stream_name.split('@')[0].upper()
                        # Convert to CCXT format using reverse mapping
                        target_key = self.stream_to_ccxt.get(symbol_raw)
                        
                        if not target_key:
                            continue
                            
                        event_type = data.get('e')
                        
                        # 1. MARK PRICE (Funding Rate)
                        if 'markPrice' in stream_name:
                            if 'r' in data:
                                self.data[target_key]['funding_rate'] = float(data['r'])
                                self.data[target_key]['timestamp'] = data['E']
                                
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
                            
                            if side == 'SELL':
                                self.data[target_key]['last_liq_sell'] += usd_val
                            else:
                                self.data[target_key]['last_liq_buy'] += usd_val
                            
                            buy = max(self.data[target_key]['last_liq_buy'], 1.0)
                            sell = max(self.data[target_key]['last_liq_sell'], 1.0)
                            self.data[target_key]['liq_volume_ratio'] = buy / sell
                            self.data[target_key]['timestamp'] = data['E']

            except Exception as e:
                if self.running:
                    logger.error(f"WS Combined Stream Error: {e}")
                    await asyncio.sleep(5)

    def is_connected(self) -> bool:
        """Checks if the WS is operational based on recent activity (last 2 mins)."""
        import time
        now_ms = time.time() * 1000
        # If any symbol has received an update in the last 2 minutes, consider it alive
        for symbol, d in self.data.items():
            if now_ms - d['timestamp'] < 120000: # 2 mins
                return True
        return False

    async def restart(self):
        """Restarts the WS connection."""
        logger.info("Restarting Binance WebSocket client...")
        await self.stop()
        await asyncio.sleep(2)
        await self.start()

    def get_metrics(self, symbol: str) -> Dict:
        """Returns the latest cached metrics for a symbol."""
        # Symbol is expected to be the EXACT key used during init (CCXT format)
        if symbol not in self.data:
            # Try to match it if it's not an exact match
            tag = symbol.split(':')[0].replace('/', '').upper() # "OP/USDT" -> "OPUSDT"
            found_key = None
            for key in self.data.keys():
                clean_key = key.split(':')[0].replace('/', '').upper() # "OP/USDT:USDT" -> "OPUSDT"
                if clean_key == tag:
                    found_key = key
                    break
            if not found_key:
                return {'is_ws': False}
            symbol = found_key
        
        d = self.data[symbol]
        # If data hasn't arrived (timestamp == 0), return False
        if d['timestamp'] == 0:
            return {'is_ws': False}
        
        return {
            'funding_rate': d['funding_rate'],
            'open_interest': d['open_interest'],
            'liq_ratio': d['liq_volume_ratio'],
            'is_ws': True
        }
