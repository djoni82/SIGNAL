"""
Exchange Connector for CryptoAlphaPro
Real-time connection to multiple cryptocurrency exchanges
"""

import ccxt.pro as ccxt
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from loguru import logger
import pandas as pd
import aiohttp


class ExchangeConnector:
    """Real exchange connector with WebSocket support"""
    
    def __init__(self, exchange_name: str, config):
        self.exchange_name = exchange_name
        self.config = config
        self.exchange = None
        self.websocket_running = False
        self.last_heartbeat = time.time()
        self.rate_limiter = {}
        
    async def initialize(self):
        """Initialize exchange connection"""
        try:
            # Create exchange instance based on name
            if self.exchange_name == 'binance':
                self.exchange = ccxt.binance({
                    'apiKey': self.config.api_key,
                    'secret': self.config.secret,
                    'sandbox': self.config.sandbox,
                    'rateLimit': self.config.rate_limit,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',  # spot, margin, future, delivery
                    }
                })
            elif self.exchange_name == 'bybit':
                self.exchange = ccxt.bybit({
                    'apiKey': self.config.api_key,
                    'secret': self.config.secret,
                    'sandbox': self.config.sandbox,
                    'rateLimit': self.config.rate_limit,
                    'enableRateLimit': True,
                })
            elif self.exchange_name == 'okx':
                self.exchange = ccxt.okx({
                    'apiKey': self.config.api_key,
                    'secret': self.config.secret,
                    'password': self.config.passphrase,
                    'sandbox': self.config.sandbox,
                    'rateLimit': self.config.rate_limit,
                    'enableRateLimit': True,
                })
            else:
                raise ValueError(f"Unsupported exchange: {self.exchange_name}")
            
            # Test connection
            await self.exchange.load_markets()
            logger.success(f"✅ {self.exchange_name} connector initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.exchange_name}: {e}")
            raise

    async def fetch_ohlcv(self, pair: str, timeframe: str, limit: int = 100) -> Optional[List]:
        """Fetch OHLCV data"""
        try:
            await self._check_rate_limit('ohlcv')
            
            # Fetch candlestick data
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol=pair,
                timeframe=timeframe,
                limit=limit
            )
            
            logger.debug(f"📊 Fetched {len(ohlcv)} OHLCV candles for {pair} on {self.exchange_name}")
            return ohlcv
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch OHLCV for {pair}: {e}")
            return None

    async def fetch_order_book(self, pair: str, limit: int = 20) -> Optional[Dict]:
        """Fetch order book data"""
        try:
            await self._check_rate_limit('orderbook')
            
            orderbook = await self.exchange.fetch_order_book(pair, limit)
            
            return {
                'symbol': pair,
                'timestamp': orderbook.get('timestamp', int(time.time() * 1000)),
                'datetime': orderbook.get('datetime'),
                'bids': orderbook.get('bids', [])[:limit],
                'asks': orderbook.get('asks', [])[:limit],
                'spread': self._calculate_spread(orderbook),
                'exchange': self.exchange_name
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch orderbook for {pair}: {e}")
            return None

    async def fetch_ticker(self, pair: str) -> Optional[Dict]:
        """Fetch ticker data"""
        try:
            await self._check_rate_limit('ticker')
            
            ticker = await self.exchange.fetch_ticker(pair)
            
            return {
                'symbol': pair,
                'timestamp': ticker.get('timestamp', int(time.time() * 1000)),
                'last': ticker.get('last'),
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'volume': ticker.get('baseVolume'),
                'change': ticker.get('change'),
                'percentage': ticker.get('percentage'),
                'high': ticker.get('high'),
                'low': ticker.get('low'),
                'open': ticker.get('open'),
                'close': ticker.get('close'),
                'exchange': self.exchange_name
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch ticker for {pair}: {e}")
            return None

    async def fetch_trades(self, pair: str, limit: int = 50) -> Optional[List]:
        """Fetch recent trades"""
        try:
            await self._check_rate_limit('trades')
            
            trades = await self.exchange.fetch_trades(pair, limit=limit)
            
            processed_trades = []
            for trade in trades:
                processed_trades.append({
                    'timestamp': trade.get('timestamp'),
                    'side': trade.get('side'),
                    'amount': trade.get('amount'),
                    'price': trade.get('price'),
                    'cost': trade.get('cost'),
                    'symbol': pair,
                    'exchange': self.exchange_name
                })
            
            return processed_trades
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch trades for {pair}: {e}")
            return None

    async def start_websocket(self, callback: Callable):
        """Start WebSocket streams for real-time data"""
        self.websocket_running = True
        
        try:
            logger.info(f"🔄 Starting WebSocket streams for {self.exchange_name}")
            
            # Start multiple streams concurrently
            tasks = []
            
            # Ticker stream
            tasks.append(asyncio.create_task(
                self._ticker_stream(callback),
                name=f"ticker_stream_{self.exchange_name}"
            ))
            
            # Trades stream  
            tasks.append(asyncio.create_task(
                self._trades_stream(callback),
                name=f"trades_stream_{self.exchange_name}"
            ))
            
            # Orderbook stream
            tasks.append(asyncio.create_task(
                self._orderbook_stream(callback),
                name=f"orderbook_stream_{self.exchange_name}"
            ))
            
            # Wait for all streams
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ WebSocket error for {self.exchange_name}: {e}")
        finally:
            self.websocket_running = False

    async def _ticker_stream(self, callback: Callable):
        """Stream ticker updates"""
        while self.websocket_running:
            try:
                # Use ccxt.pro for WebSocket
                ticker = await self.exchange.watch_ticker('BTC/USDT')
                
                await callback(self.exchange_name, {
                    'type': 'ticker',
                    'data': ticker,
                    'timestamp': int(time.time() * 1000)
                })
                
            except Exception as e:
                logger.warning(f"⚠️  Ticker stream error: {e}")
                await asyncio.sleep(1)

    async def _trades_stream(self, callback: Callable):
        """Stream trade updates"""
        while self.websocket_running:
            try:
                trades = await self.exchange.watch_trades('BTC/USDT')
                
                await callback(self.exchange_name, {
                    'type': 'trade',
                    'data': trades,
                    'timestamp': int(time.time() * 1000)
                })
                
            except Exception as e:
                logger.warning(f"⚠️  Trades stream error: {e}")
                await asyncio.sleep(1)

    async def _orderbook_stream(self, callback: Callable):
        """Stream orderbook updates"""
        while self.websocket_running:
            try:
                orderbook = await self.exchange.watch_order_book('BTC/USDT')
                
                await callback(self.exchange_name, {
                    'type': 'orderbook',
                    'data': orderbook,
                    'timestamp': int(time.time() * 1000)
                })
                
            except Exception as e:
                logger.warning(f"⚠️  Orderbook stream error: {e}")
                await asyncio.sleep(1)

    async def _check_rate_limit(self, endpoint: str):
        """Check and enforce rate limits"""
        current_time = time.time()
        
        if endpoint not in self.rate_limiter:
            self.rate_limiter[endpoint] = {
                'last_request': 0,
                'requests_count': 0,
                'window_start': current_time
            }
        
        limiter = self.rate_limiter[endpoint]
        
        # Reset window if needed (1 minute window)
        if current_time - limiter['window_start'] > 60:
            limiter['requests_count'] = 0
            limiter['window_start'] = current_time
        
        # Check if we need to wait
        min_interval = 60 / self.config.rate_limit  # requests per minute
        time_since_last = current_time - limiter['last_request']
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        limiter['last_request'] = time.time()
        limiter['requests_count'] += 1

    def _calculate_spread(self, orderbook: Dict) -> float:
        """Calculate bid-ask spread"""
        try:
            if orderbook.get('bids') and orderbook.get('asks'):
                best_bid = orderbook['bids'][0][0]
                best_ask = orderbook['asks'][0][0]
                return (best_ask - best_bid) / best_ask * 100
        except:
            pass
        return 0.0

    async def get_trading_fees(self, pair: str) -> Dict:
        """Get trading fees for a pair"""
        try:
            await self.exchange.load_markets()
            market = self.exchange.market(pair)
            
            return {
                'maker': market.get('maker', 0.001),
                'taker': market.get('taker', 0.001),
                'percentage': True,
                'tierBased': market.get('tierBased', False)
            }
        except Exception as e:
            logger.warning(f"⚠️  Failed to get fees for {pair}: {e}")
            return {'maker': 0.001, 'taker': 0.001, 'percentage': True}

    async def get_market_info(self, pair: str) -> Optional[Dict]:
        """Get market information"""
        try:
            await self.exchange.load_markets()
            market = self.exchange.market(pair)
            
            return {
                'symbol': pair,
                'base': market['base'],
                'quote': market['quote'],
                'active': market.get('active', True),
                'type': market.get('type', 'spot'),
                'spot': market.get('spot', True),
                'margin': market.get('margin', False),
                'future': market.get('future', False),
                'option': market.get('option', False),
                'contract': market.get('contract', False),
                'settle': market.get('settle'),
                'contractSize': market.get('contractSize'),
                'linear': market.get('linear'),
                'inverse': market.get('inverse'),
                'expiry': market.get('expiry'),
                'expiryDatetime': market.get('expiryDatetime'),
                'strike': market.get('strike'),
                'optionType': market.get('optionType'),
                'precision': {
                    'amount': market['precision']['amount'],
                    'price': market['precision']['price'],
                },
                'limits': {
                    'amount': market['limits']['amount'],
                    'price': market['limits']['price'],
                    'cost': market['limits']['cost'],
                },
                'info': market.get('info', {})
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to get market info for {pair}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check exchange connection health"""
        try:
            # Test with a simple API call
            await self.exchange.fetch_status()
            self.last_heartbeat = time.time()
            return True
        except Exception as e:
            logger.warning(f"⚠️  Health check failed for {self.exchange_name}: {e}")
            return False

    async def get_server_time(self) -> int:
        """Get exchange server time"""
        try:
            time_data = await self.exchange.fetch_time()
            return time_data
        except:
            return int(time.time() * 1000)

    async def close(self):
        """Close exchange connection"""
        self.websocket_running = False
        if self.exchange:
            await self.exchange.close()
            logger.info(f"✅ {self.exchange_name} connection closed") 