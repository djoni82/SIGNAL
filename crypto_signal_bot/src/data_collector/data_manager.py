"""
Data Manager for CryptoAlphaPro
Handles data collection from multiple exchanges and external sources
"""

import asyncio
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import aiohttp
import websockets
import json
from concurrent.futures import ThreadPoolExecutor

from src.config.config_manager import ConfigManager
from src.data_collector.exchange_connector import ExchangeConnector
from src.data_collector.dune_collector import DuneCollector
from src.data_collector.news_collector import NewsCollector
from src.database.timescale_manager import TimescaleManager
from src.database.redis_manager import RedisManager


class DataManager:
    """Main data management class"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.exchanges: Dict[str, ExchangeConnector] = {}
        self.dune_collector = None
        self.news_collector = None
        self.db_manager = None
        self.redis_manager = None
        self.running = False
        self.data_tasks: List[asyncio.Task] = []
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Data storage
        self.latest_data: Dict[str, Dict] = {}
        self.price_alerts: Dict[str, float] = {}
        
    async def initialize(self):
        """Initialize all data collection components"""
        try:
            logger.info("🔄 Initializing Data Manager...")
            
            # Initialize database connections
            await self._initialize_databases()
            
            # Initialize exchange connectors
            await self._initialize_exchanges()
            
            # Initialize external data collectors
            await self._initialize_external_collectors()
            
            logger.success("✅ Data Manager initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Data Manager: {e}")
            raise
    
    async def _initialize_databases(self):
        """Initialize database connections"""
        try:
            # Initialize TimescaleDB for time series data
            timescale_config = self.config.get_database_config('timescale')
            self.db_manager = TimescaleManager(timescale_config)
            await self.db_manager.connect()
            
            # Initialize Redis for caching
            redis_config = self.config.get_database_config('redis')
            self.redis_manager = RedisManager(redis_config)
            await self.redis_manager.connect()
            
            logger.info("✅ Database connections established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize databases: {e}")
            raise
    
    async def _initialize_exchanges(self):
        """Initialize exchange connectors"""
        try:
            exchange_names = ['binance', 'bybit', 'okx']
            
            for exchange_name in exchange_names:
                try:
                    exchange_config = self.config.get_exchange_config(exchange_name)
                    connector = ExchangeConnector(exchange_name, exchange_config)
                    await connector.initialize()
                    self.exchanges[exchange_name] = connector
                    logger.info(f"✅ {exchange_name.title()} connector initialized")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to initialize {exchange_name}: {e}")
            
            if not self.exchanges:
                raise Exception("No exchange connectors initialized")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize exchanges: {e}")
            raise
    
    async def _initialize_external_collectors(self):
        """Initialize external data collectors"""
        try:
            # Initialize Dune Analytics collector
            dune_config = self.config.get('external_apis.dune')
            if dune_config:
                self.dune_collector = DuneCollector(dune_config)
                logger.info("✅ Dune Analytics collector initialized")
            
            # Initialize news collector
            news_config = {
                'cryptopanic': self.config.get('external_apis.cryptopanic'),
                'twitter': self.config.get('external_apis.twitter')
            }
            self.news_collector = NewsCollector(news_config)
            logger.info("✅ News collector initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize external collectors: {e}")
            raise
    
    async def start_data_collection(self):
        """Start all data collection tasks"""
        self.running = True
        
        try:
            # Start OHLCV data collection
            ohlcv_task = asyncio.create_task(
                self._collect_ohlcv_data(),
                name="ohlcv_collection"
            )
            self.data_tasks.append(ohlcv_task)
            
            # Start orderbook data collection
            orderbook_task = asyncio.create_task(
                self._collect_orderbook_data(),
                name="orderbook_collection"
            )
            self.data_tasks.append(orderbook_task)
            
            # Start on-chain data collection
            if self.dune_collector:
                onchain_task = asyncio.create_task(
                    self._collect_onchain_data(),
                    name="onchain_collection"
                )
                self.data_tasks.append(onchain_task)
            
            # Start news data collection
            news_task = asyncio.create_task(
                self._collect_news_data(),
                name="news_collection"
            )
            self.data_tasks.append(news_task)
            
            # Start WebSocket streams
            websocket_task = asyncio.create_task(
                self._start_websocket_streams(),
                name="websocket_streams"
            )
            self.data_tasks.append(websocket_task)
            
            logger.info(f"✅ Started {len(self.data_tasks)} data collection tasks")
            
            # Wait for all tasks
            await asyncio.gather(*self.data_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Error in data collection: {e}")
            raise
    
    async def _collect_ohlcv_data(self):
        """Collect OHLCV data from exchanges"""
        trading_pairs = self.config.get_trading_pairs()
        timeframes = self.config.get_timeframes()
        update_frequency = self.config.get('trading.update_frequency', 100)
        
        while self.running:
            try:
                for exchange_name, connector in self.exchanges.items():
                    for pair in trading_pairs:
                        for timeframe in timeframes:
                            try:
                                # Get OHLCV data
                                ohlcv_data = await connector.fetch_ohlcv(pair, timeframe, limit=100)
                                
                                if ohlcv_data:
                                    # Store in database
                                    await self._store_ohlcv_data(exchange_name, pair, timeframe, ohlcv_data)
                                    
                                    # Cache latest data
                                    cache_key = f"{exchange_name}:{pair}:{timeframe}"
                                    self.latest_data[cache_key] = {
                                        'timestamp': datetime.now(),
                                        'data': ohlcv_data[-1]  # Latest candle
                                    }
                                
                            except Exception as e:
                                logger.warning(f"⚠️  Failed to collect OHLCV for {pair} on {exchange_name}: {e}")
                
                # Wait before next update
                await asyncio.sleep(update_frequency / 1000)  # Convert ms to seconds
                
            except Exception as e:
                logger.error(f"❌ Error in OHLCV collection: {e}")
                await asyncio.sleep(5)
    
    async def _collect_orderbook_data(self):
        """Collect orderbook data from exchanges"""
        trading_pairs = self.config.get_trading_pairs()
        
        while self.running:
            try:
                for exchange_name, connector in self.exchanges.items():
                    for pair in trading_pairs:
                        try:
                            # Get orderbook data
                            orderbook = await connector.fetch_order_book(pair, limit=20)
                            
                            if orderbook:
                                # Store in Redis for fast access
                                await self._cache_orderbook_data(exchange_name, pair, orderbook)
                                
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to collect orderbook for {pair} on {exchange_name}: {e}")
                
                await asyncio.sleep(0.5)  # Update every 500ms
                
            except Exception as e:
                logger.error(f"❌ Error in orderbook collection: {e}")
                await asyncio.sleep(5)
    
    async def _collect_onchain_data(self):
        """Collect on-chain data from Dune Analytics"""
        while self.running:
            try:
                # Collect whale transfers
                whale_data = await self.dune_collector.get_whale_transfers()
                if whale_data:
                    await self._store_onchain_data('whale_transfers', whale_data)
                
                # Collect exchange flows
                flow_data = await self.dune_collector.get_exchange_flows()
                if flow_data:
                    await self._store_onchain_data('exchange_flows', flow_data)
                
                # Update every 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Error in on-chain data collection: {e}")
                await asyncio.sleep(300)
    
    async def _collect_news_data(self):
        """Collect news and social sentiment data"""
        while self.running:
            try:
                # Collect crypto news
                news_data = await self.news_collector.get_crypto_news()
                if news_data:
                    await self._store_news_data(news_data)
                
                # Collect Twitter sentiment
                twitter_data = await self.news_collector.get_twitter_sentiment()
                if twitter_data:
                    await self._store_sentiment_data(twitter_data)
                
                # Update every 10 minutes
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"❌ Error in news data collection: {e}")
                await asyncio.sleep(600)
    
    async def _start_websocket_streams(self):
        """Start WebSocket streams for real-time data"""
        tasks = []
        
        for exchange_name, connector in self.exchanges.items():
            if hasattr(connector, 'start_websocket'):
                task = asyncio.create_task(
                    connector.start_websocket(self._handle_websocket_message),
                    name=f"websocket_{exchange_name}"
                )
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _handle_websocket_message(self, exchange: str, message: dict):
        """Handle incoming WebSocket messages"""
        try:
            if message.get('type') == 'ticker':
                # Handle ticker updates
                await self._process_ticker_update(exchange, message)
            elif message.get('type') == 'trade':
                # Handle trade updates
                await self._process_trade_update(exchange, message)
            elif message.get('type') == 'orderbook':
                # Handle orderbook updates
                await self._process_orderbook_update(exchange, message)
                
        except Exception as e:
            logger.warning(f"⚠️  Error processing WebSocket message: {e}")
    
    async def _store_ohlcv_data(self, exchange: str, pair: str, timeframe: str, data: List):
        """Store OHLCV data in TimescaleDB"""
        try:
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['exchange'] = exchange
            df['pair'] = pair
            df['timeframe'] = timeframe
            
            await self.db_manager.insert_ohlcv_data(df)
            
        except Exception as e:
            logger.error(f"❌ Failed to store OHLCV data: {e}")
    
    async def _cache_orderbook_data(self, exchange: str, pair: str, orderbook: dict):
        """Cache orderbook data in Redis"""
        try:
            cache_key = f"orderbook:{exchange}:{pair}"
            await self.redis_manager.set(cache_key, json.dumps(orderbook), expire=10)
            
        except Exception as e:
            logger.error(f"❌ Failed to cache orderbook data: {e}")
    
    async def _store_onchain_data(self, data_type: str, data: List):
        """Store on-chain data"""
        try:
            await self.db_manager.insert_onchain_data(data_type, data)
            
        except Exception as e:
            logger.error(f"❌ Failed to store on-chain data: {e}")
    
    async def _store_news_data(self, news_data: List):
        """Store news data"""
        try:
            await self.db_manager.insert_news_data(news_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to store news data: {e}")
    
    async def _store_sentiment_data(self, sentiment_data: List):
        """Store sentiment data"""
        try:
            await self.db_manager.insert_sentiment_data(sentiment_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to store sentiment data: {e}")
    
    async def get_latest_price(self, exchange: str, pair: str) -> Optional[float]:
        """Get latest price for a trading pair"""
        try:
            if exchange in self.exchanges:
                ticker = await self.exchanges[exchange].fetch_ticker(pair)
                return ticker.get('last') if ticker else None
        except Exception as e:
            logger.warning(f"⚠️  Failed to get latest price: {e}")
        return None
    
    async def get_historical_data(self, exchange: str, pair: str, timeframe: str, 
                                 start_time: datetime, end_time: datetime) -> Optional[pd.DataFrame]:
        """Get historical OHLCV data"""
        try:
            return await self.db_manager.get_ohlcv_data(exchange, pair, timeframe, start_time, end_time)
        except Exception as e:
            logger.error(f"❌ Failed to get historical data: {e}")
            return None
    
    async def get_orderbook(self, exchange: str, pair: str) -> Optional[dict]:
        """Get cached orderbook data"""
        try:
            cache_key = f"orderbook:{exchange}:{pair}"
            cached_data = await self.redis_manager.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"⚠️  Failed to get orderbook: {e}")
        return None
    
    def is_healthy(self) -> bool:
        """Check if data collection is healthy"""
        try:
            # Check if we have recent data
            current_time = datetime.now()
            for key, data in self.latest_data.items():
                if (current_time - data['timestamp']).seconds > 300:  # 5 minutes
                    return False
            return len(self.latest_data) > 0
        except:
            return False
    
    async def check_database_health(self) -> bool:
        """Check database connections health"""
        try:
            if self.db_manager:
                await self.db_manager.health_check()
            if self.redis_manager:
                await self.redis_manager.health_check()
            return True
        except:
            return False
    
    async def check_exchange_health(self) -> bool:
        """Check exchange connections health"""
        healthy_count = 0
        for connector in self.exchanges.values():
            if await connector.health_check():
                healthy_count += 1
        return healthy_count > 0
    
    async def shutdown(self):
        """Shutdown data collection"""
        logger.info("🛑 Shutting down Data Manager...")
        self.running = False
        
        # Cancel all tasks
        for task in self.data_tasks:
            if not task.done():
                task.cancel()
        
        # Close connections
        for connector in self.exchanges.values():
            await connector.close()
        
        if self.db_manager:
            await self.db_manager.close()
        
        if self.redis_manager:
            await self.redis_manager.close()
        
        self.executor.shutdown(wait=True)
        logger.success("✅ Data Manager shutdown completed") 