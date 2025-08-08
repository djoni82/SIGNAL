#!/usr/bin/env python3
import asyncio
import json
import time
from typing import Dict, List, Tuple
import websockets

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

_timeframe_map = {
    '1m': '1m',
    '3m': '3m',
    '5m': '5m',
    '15m': '15m',
    '1h': '1h',
    '4h': '4h',
}


def _symbol_to_stream(symbol: str) -> str:
    # 'BTC/USDT' -> 'btcusdt'
    return symbol.replace('/', '').lower()


class BinanceWSManager:
    """Maintains Binance klines via WebSocket with auto-reconnect and in-memory cache."""

    def __init__(self, max_candles: int = 300):
        self.max_candles = max_candles
        # cache[(symbol, tf)] = list[dict(timestamp, open, high, low, close, volume)]
        self._cache: Dict[Tuple[str, str], List[Dict]] = {}
        self._running = False
        self._tasks: Dict[Tuple[str, str], asyncio.Task] = {}

    def is_running(self) -> bool:
        return self._running

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False
        for task in list(self._tasks.values()):
            task.cancel()
        self._tasks.clear()

    async def subscribe(self, symbol: str, timeframe: str):
        if timeframe not in _timeframe_map:
            return
        key = (symbol, timeframe)
        if key in self._tasks and not self._tasks[key].done():
            return
        if not self._running:
            await self.start()
        task = asyncio.create_task(self._ws_loop(symbol, timeframe))
        self._tasks[key] = task

    async def subscribe_many(self, pairs: List[str], timeframes: List[str]):
        await self.start()
        tasks = []
        for sym in pairs:
            for tf in timeframes:
                if tf in _timeframe_map:
                    tasks.append(self.subscribe(sym, tf))
        if tasks:
            await asyncio.gather(*tasks)

    def get_cached_ohlcv(self, symbol: str, timeframe: str) -> List[Dict]:
        return self._cache.get((symbol, timeframe), [])

    async def _ws_loop(self, symbol: str, timeframe: str):
        stream = f"{_symbol_to_stream(symbol)}@kline_{_timeframe_map[timeframe]}"
        url = f"wss://stream.binance.com:9443/ws/{stream}"
        backoff = 1
        while self._running:
            try:
                async with websockets.connect(url, ping_interval=15, ping_timeout=10, close_timeout=5) as ws:
                    backoff = 1
                    async for msg in ws:
                        try:
                            data = json.loads(msg)
                        except Exception:
                            continue
                        k = data.get('k') or data.get('data', {}).get('k')
                        if not k:
                            continue
                        # kline fields
                        ts = int(k.get('t', 0))
                        o = float(k.get('o', 0.0))
                        h = float(k.get('h', 0.0))
                        l = float(k.get('l', 0.0))
                        c = float(k.get('c', 0.0))
                        v = float(k.get('v', 0.0))
                        is_closed = bool(k.get('x', False))

                        key = (symbol, timeframe)
                        arr = self._cache.setdefault(key, [])

                        # Append/replace last candle by timestamp
                        if arr and arr[-1]['timestamp'] == ts:
                            arr[-1].update({
                                'open': o, 'high': h, 'low': l, 'close': c, 'volume': v
                            })
                        else:
                            arr.append({
                                'timestamp': ts,
                                'open': o,
                                'high': h,
                                'low': l,
                                'close': c,
                                'volume': v
                            })
                        # Trim
                        if len(arr) > self.max_candles:
                            del arr[:-self.max_candles]
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30) 