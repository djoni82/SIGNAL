"""
TimescaleDB Manager for CryptoAlphaPro
High-performance time-series database operations
"""

import asyncio
import asyncpg
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import json
import time


class TimescaleManager:
    """TimescaleDB connection and operations manager"""
    
    def __init__(self, config):
        self.config = config
        self.pool = None
        self.connection_retries = 0
        self.max_retries = 5
        self.batch_size = 1000
        
    async def connect(self):
        """Establish connection pool to TimescaleDB"""
        try:
            # Create connection string
            connection_string = (
                f"postgresql://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                connection_string,
                min_size=5,
                max_size=self.config.max_connections,
                command_timeout=60,
                server_settings={
                    'jit': 'off'  # Disable JIT for better performance with time-series queries
                }
            )
            
            # Test connection and create tables
            await self._initialize_schema()
            
            logger.success("✅ TimescaleDB connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to TimescaleDB: {e}")
            if self.connection_retries < self.max_retries:
                self.connection_retries += 1
                logger.info(f"🔄 Retrying connection ({self.connection_retries}/{self.max_retries})...")
                await asyncio.sleep(5)
                await self.connect()
            else:
                raise

    async def _initialize_schema(self):
        """Initialize database schema and hypertables"""
        async with self.pool.acquire() as conn:
            # Create OHLCV hypertable
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ohlcv_data (
                    time TIMESTAMPTZ NOT NULL,
                    exchange TEXT NOT NULL,
                    pair TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open DECIMAL(20,8) NOT NULL,
                    high DECIMAL(20,8) NOT NULL,
                    low DECIMAL(20,8) NOT NULL,
                    close DECIMAL(20,8) NOT NULL,
                    volume DECIMAL(20,8) NOT NULL,
                    trades_count INTEGER,
                    vwap DECIMAL(20,8),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create hypertable if not exists
            try:
                await conn.execute("""
                    SELECT create_hypertable('ohlcv_data', 'time', 
                                           chunk_time_interval => INTERVAL '1 day',
                                           if_not_exists => TRUE);
                """)
            except Exception as e:
                logger.debug(f"Hypertable may already exist: {e}")
            
            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ohlcv_exchange_pair_time 
                ON ohlcv_data (exchange, pair, time DESC);
                
                CREATE INDEX IF NOT EXISTS idx_ohlcv_pair_timeframe_time 
                ON ohlcv_data (pair, timeframe, time DESC);
            """)
            
            # Create on-chain data table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS onchain_data (
                    time TIMESTAMPTZ NOT NULL,
                    data_type TEXT NOT NULL,
                    symbol TEXT,
                    value DECIMAL(20,8),
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            try:
                await conn.execute("""
                    SELECT create_hypertable('onchain_data', 'time',
                                           chunk_time_interval => INTERVAL '1 day',
                                           if_not_exists => TRUE);
                """)
            except Exception as e:
                logger.debug(f"Onchain hypertable may already exist: {e}")
            
            # Create news and sentiment tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS news_data (
                    time TIMESTAMPTZ NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    source TEXT NOT NULL,
                    url TEXT,
                    sentiment_score DECIMAL(3,2),
                    symbols TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS sentiment_data (
                    time TIMESTAMPTZ NOT NULL,
                    source TEXT NOT NULL,
                    symbol TEXT,
                    sentiment_score DECIMAL(3,2) NOT NULL,
                    volume_mentions INTEGER,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create trade signals table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_signals (
                    time TIMESTAMPTZ NOT NULL,
                    exchange TEXT NOT NULL,
                    pair TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence DECIMAL(3,2) NOT NULL,
                    entry_price DECIMAL(20,8),
                    stop_loss DECIMAL(20,8),
                    take_profit DECIMAL(20,8)[],
                    leverage DECIMAL(5,2),
                    indicators JSONB,
                    ml_predictions JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create portfolio tracking table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    time TIMESTAMPTZ NOT NULL,
                    total_value DECIMAL(20,8) NOT NULL,
                    pnl_daily DECIMAL(20,8),
                    pnl_total DECIMAL(20,8),
                    positions JSONB,
                    risk_metrics JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            logger.info("✅ Database schema initialized")

    async def insert_ohlcv_data(self, data: pd.DataFrame):
        """Insert OHLCV data efficiently using batch operations"""
        try:
            if data.empty:
                return
            
            # Prepare data for insertion
            records = []
            for _, row in data.iterrows():
                records.append((
                    row['timestamp'],
                    row['exchange'],
                    row['pair'],
                    row['timeframe'],
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume']),
                    row.get('trades_count'),
                    row.get('vwap')
                ))
            
            # Batch insert with ON CONFLICT handling
            async with self.pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO ohlcv_data 
                    (time, exchange, pair, timeframe, open, high, low, close, volume, trades_count, vwap)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (time, exchange, pair, timeframe) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        trades_count = EXCLUDED.trades_count,
                        vwap = EXCLUDED.vwap
                """, records)
            
            logger.debug(f"📊 Inserted {len(records)} OHLCV records")
            
        except Exception as e:
            logger.error(f"❌ Failed to insert OHLCV data: {e}")
            raise

    async def get_ohlcv_data(self, exchange: str, pair: str, timeframe: str, 
                            start_time: datetime, end_time: datetime) -> Optional[pd.DataFrame]:
        """Retrieve OHLCV data with optimized query"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT time, open, high, low, close, volume, trades_count, vwap
                    FROM ohlcv_data
                    WHERE exchange = $1 AND pair = $2 AND timeframe = $3
                    AND time >= $4 AND time <= $5
                    ORDER BY time ASC
                """
                
                rows = await conn.fetch(query, exchange, pair, timeframe, start_time, end_time)
                
                if not rows:
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame([dict(row) for row in rows])
                df['timestamp'] = df['time']
                df = df.drop('time', axis=1)
                
                # Ensure proper data types
                numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'vwap']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                logger.debug(f"📊 Retrieved {len(df)} OHLCV records for {pair}")
                return df
                
        except Exception as e:
            logger.error(f"❌ Failed to get OHLCV data: {e}")
            return None

    async def insert_onchain_data(self, data_type: str, data: List[Dict]):
        """Insert on-chain data"""
        try:
            if not data:
                return
            
            records = []
            for item in data:
                records.append((
                    item.get('timestamp', datetime.now()),
                    data_type,
                    item.get('symbol'),
                    float(item.get('value', 0)),
                    json.dumps(item.get('metadata', {}))
                ))
            
            async with self.pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO onchain_data (time, data_type, symbol, value, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT DO NOTHING
                """, records)
            
            logger.debug(f"🔗 Inserted {len(records)} on-chain records")
            
        except Exception as e:
            logger.error(f"❌ Failed to insert on-chain data: {e}")

    async def insert_news_data(self, data: List[Dict]):
        """Insert news data"""
        try:
            if not data:
                return
            
            records = []
            for news in data:
                records.append((
                    news.get('published_at', datetime.now()),
                    news.get('title', ''),
                    news.get('content', ''),
                    news.get('source', ''),
                    news.get('url', ''),
                    float(news.get('sentiment_score', 0)) if news.get('sentiment_score') else None,
                    news.get('symbols', []),
                    json.dumps(news.get('metadata', {}))
                ))
            
            async with self.pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO news_data (time, title, content, source, url, sentiment_score, symbols, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT DO NOTHING
                """, records)
            
            logger.debug(f"📰 Inserted {len(records)} news records")
            
        except Exception as e:
            logger.error(f"❌ Failed to insert news data: {e}")

    async def insert_sentiment_data(self, data: List[Dict]):
        """Insert sentiment data"""
        try:
            if not data:
                return
            
            records = []
            for sentiment in data:
                records.append((
                    sentiment.get('timestamp', datetime.now()),
                    sentiment.get('source', ''),
                    sentiment.get('symbol', ''),
                    float(sentiment.get('sentiment_score', 0)),
                    int(sentiment.get('volume_mentions', 0)),
                    json.dumps(sentiment.get('metadata', {}))
                ))
            
            async with self.pool.acquire() as conn:
                await conn.executemany("""
                    INSERT INTO sentiment_data (time, source, symbol, sentiment_score, volume_mentions, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, records)
            
            logger.debug(f"💭 Inserted {len(records)} sentiment records")
            
        except Exception as e:
            logger.error(f"❌ Failed to insert sentiment data: {e}")

    async def insert_trade_signal(self, signal: Dict):
        """Insert trade signal"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO trade_signals 
                    (time, exchange, pair, action, confidence, entry_price, stop_loss, take_profit, leverage, indicators, ml_predictions)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, 
                    datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00')),
                    signal['exchange'],
                    signal['symbol'],
                    signal['action'],
                    float(signal['confidence']),
                    float(signal.get('entry_range', [0])[0]) if signal.get('entry_range') else None,
                    float(signal.get('stop_loss', 0)),
                    signal.get('take_profit', []),
                    float(signal.get('leverage', 1)),
                    json.dumps(signal.get('indicators', {})),
                    json.dumps(signal.get('analysis', {}))
                )
            
            logger.debug(f"🎯 Inserted trade signal for {signal['symbol']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to insert trade signal: {e}")

    async def get_latest_price(self, exchange: str, pair: str, timeframe: str = '1m') -> Optional[float]:
        """Get latest price for a pair"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT close FROM ohlcv_data
                    WHERE exchange = $1 AND pair = $2 AND timeframe = $3
                    ORDER BY time DESC
                    LIMIT 1
                """, exchange, pair, timeframe)
                
                return float(row['close']) if row else None
                
        except Exception as e:
            logger.error(f"❌ Failed to get latest price: {e}")
            return None

    async def get_price_history(self, pair: str, timeframe: str, hours: int = 24) -> Optional[pd.DataFrame]:
        """Get price history for analysis"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT time, close, volume
                    FROM ohlcv_data
                    WHERE pair = $1 AND timeframe = $2
                    AND time >= $3 AND time <= $4
                    ORDER BY time ASC
                """, pair, timeframe, start_time, end_time)
                
                if not rows:
                    return None
                
                df = pd.DataFrame([dict(row) for row in rows])
                df['close'] = pd.to_numeric(df['close'])
                df['volume'] = pd.to_numeric(df['volume'])
                
                return df
                
        except Exception as e:
            logger.error(f"❌ Failed to get price history: {e}")
            return None

    async def get_volatility_metrics(self, pair: str, timeframe: str, periods: int = 20) -> Dict:
        """Calculate volatility metrics"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    WITH returns AS (
                        SELECT 
                            close,
                            LAG(close) OVER (ORDER BY time) as prev_close
                        FROM ohlcv_data
                        WHERE pair = $1 AND timeframe = $2
                        ORDER BY time DESC
                        LIMIT $3
                    ),
                    log_returns AS (
                        SELECT LN(close / prev_close) as log_return
                        FROM returns
                        WHERE prev_close IS NOT NULL
                    )
                    SELECT 
                        STDDEV(log_return) * SQRT(252) as annualized_volatility,
                        AVG(log_return) as mean_return,
                        COUNT(*) as sample_size
                    FROM log_returns
                """, pair, timeframe, periods)
                
                if row:
                    return {
                        'annualized_volatility': float(row['annualized_volatility']) if row['annualized_volatility'] else 0,
                        'mean_return': float(row['mean_return']) if row['mean_return'] else 0,
                        'sample_size': int(row['sample_size'])
                    }
                
                return {'annualized_volatility': 0, 'mean_return': 0, 'sample_size': 0}
                
        except Exception as e:
            logger.error(f"❌ Failed to calculate volatility metrics: {e}")
            return {'annualized_volatility': 0, 'mean_return': 0, 'sample_size': 0}

    async def get_performance_stats(self) -> Dict:
        """Get database performance statistics"""
        try:
            async with self.pool.acquire() as conn:
                # Table sizes
                tables_stats = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC
                """)
                
                # Connection stats
                connection_stats = await conn.fetchrow("""
                    SELECT 
                        sum(numbackends) as active_connections,
                        count(*) as databases
                    FROM pg_stat_database
                """)
                
                return {
                    'tables': [dict(row) for row in tables_stats],
                    'active_connections': int(connection_stats['active_connections']),
                    'pool_size': len(self.pool._holders),
                    'pool_free': len([h for h in self.pool._holders if h._con is None])
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get performance stats: {e}")
            return {}

    async def health_check(self):
        """Check database health"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.debug("✅ TimescaleDB health check passed")
                    return True
        except Exception as e:
            logger.error(f"❌ TimescaleDB health check failed: {e}")
            return False

    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Cleanup old data to manage storage"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            async with self.pool.acquire() as conn:
                # Delete old OHLCV data (keep only recent timeframes)
                deleted_ohlcv = await conn.execute("""
                    DELETE FROM ohlcv_data 
                    WHERE time < $1 AND timeframe IN ('1m', '5m', '15m')
                """, cutoff_date)
                
                # Delete old news data
                deleted_news = await conn.execute("""
                    DELETE FROM news_data WHERE time < $1
                """, cutoff_date)
                
                logger.info(f"🧹 Cleaned up old data: {deleted_ohlcv} OHLCV, {deleted_news} news records")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old data: {e}")

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ TimescaleDB connections closed") 