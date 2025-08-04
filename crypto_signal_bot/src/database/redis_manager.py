"""
Redis Manager for CryptoAlphaPro
High-performance caching and pub/sub operations
"""

import redis.asyncio as redis
import json
import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from loguru import logger
import pickle
import hashlib


class RedisManager:
    """Redis connection and operations manager"""
    
    def __init__(self, config):
        self.config = config
        self.redis_client = None
        self.pubsub = None
        self.connection_retries = 0
        self.max_retries = 5
        
        # Cache configuration
        self.default_ttl = 300  # 5 minutes
        self.cache_prefix = "crypto_alpha_pro"
        
    async def connect(self):
        """Establish Redis connection"""
        try:
            # Create Redis connection
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.database,
                password=self.config.password,
                decode_responses=False,  # Keep bytes for pickle
                max_connections=self.config.max_connections,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Initialize pub/sub
            self.pubsub = self.redis_client.pubsub()
            
            logger.success("✅ Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            if self.connection_retries < self.max_retries:
                self.connection_retries += 1
                logger.info(f"🔄 Retrying Redis connection ({self.connection_retries}/{self.max_retries})...")
                await asyncio.sleep(2)
                await self.connect()
            else:
                raise

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.cache_prefix}:{key}"

    async def set(self, key: str, value: Any, expire: Optional[int] = None, serialize: bool = True) -> bool:
        """Set a value in Redis with optional expiration"""
        try:
            cache_key = self._make_key(key)
            ttl = expire or self.default_ttl
            
            # Serialize data
            if serialize:
                if isinstance(value, (dict, list)):
                    serialized_value = json.dumps(value, default=str)
                else:
                    serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # Set with expiration
            result = await self.redis_client.setex(cache_key, ttl, serialized_value)
            
            logger.debug(f"💾 Cached: {key} (TTL: {ttl}s)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to set Redis key {key}: {e}")
            return False

    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Get a value from Redis"""
        try:
            cache_key = self._make_key(key)
            value = await self.redis_client.get(cache_key)
            
            if value is None:
                return None
            
            # Deserialize data
            if deserialize:
                try:
                    # Try JSON first
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    try:
                        # Try pickle
                        return pickle.loads(value)
                    except:
                        # Return as string
                        return value.decode('utf-8') if isinstance(value, bytes) else value
            else:
                return value.decode('utf-8') if isinstance(value, bytes) else value
            
        except Exception as e:
            logger.error(f"❌ Failed to get Redis key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            cache_key = self._make_key(key)
            result = await self.redis_client.delete(cache_key)
            return result > 0
        except Exception as e:
            logger.error(f"❌ Failed to delete Redis key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            cache_key = self._make_key(key)
            return await self.redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"❌ Failed to check Redis key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        try:
            cache_key = self._make_key(key)
            return await self.redis_client.expire(cache_key, seconds)
        except Exception as e:
            logger.error(f"❌ Failed to set expiration for Redis key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        try:
            cache_key = self._make_key(key)
            return await self.redis_client.ttl(cache_key)
        except Exception as e:
            logger.error(f"❌ Failed to get TTL for Redis key {key}: {e}")
            return -1

    # Hash operations for structured data
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields"""
        try:
            cache_key = self._make_key(name)
            # Serialize values
            serialized_mapping = {}
            for field, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[field] = json.dumps(value, default=str)
                else:
                    serialized_mapping[field] = str(value)
            
            return await self.redis_client.hset(cache_key, mapping=serialized_mapping)
        except Exception as e:
            logger.error(f"❌ Failed to set Redis hash {name}: {e}")
            return 0

    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field"""
        try:
            cache_key = self._make_key(name)
            value = await self.redis_client.hget(cache_key, key)
            if value:
                try:
                    return json.loads(value.decode('utf-8'))
                except:
                    return value.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get Redis hash field {name}:{key}: {e}")
            return None

    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        try:
            cache_key = self._make_key(name)
            data = await self.redis_client.hgetall(cache_key)
            result = {}
            for field, value in data.items():
                field_name = field.decode('utf-8') if isinstance(field, bytes) else field
                try:
                    result[field_name] = json.loads(value.decode('utf-8'))
                except:
                    result[field_name] = value.decode('utf-8') if isinstance(value, bytes) else value
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get Redis hash {name}: {e}")
            return {}

    # List operations for queues
    async def lpush(self, name: str, *values) -> int:
        """Push values to list head"""
        try:
            cache_key = self._make_key(name)
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value, default=str))
                else:
                    serialized_values.append(str(value))
            return await self.redis_client.lpush(cache_key, *serialized_values)
        except Exception as e:
            logger.error(f"❌ Failed to push to Redis list {name}: {e}")
            return 0

    async def rpop(self, name: str) -> Optional[Any]:
        """Pop value from list tail"""
        try:
            cache_key = self._make_key(name)
            value = await self.redis_client.rpop(cache_key)
            if value:
                try:
                    return json.loads(value.decode('utf-8'))
                except:
                    return value.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"❌ Failed to pop from Redis list {name}: {e}")
            return None

    async def llen(self, name: str) -> int:
        """Get list length"""
        try:
            cache_key = self._make_key(name)
            return await self.redis_client.llen(cache_key)
        except Exception as e:
            logger.error(f"❌ Failed to get Redis list length {name}: {e}")
            return 0

    # Pub/Sub operations
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel"""
        try:
            if isinstance(message, (dict, list)):
                serialized_message = json.dumps(message, default=str)
            else:
                serialized_message = str(message)
            
            return await self.redis_client.publish(channel, serialized_message)
        except Exception as e:
            logger.error(f"❌ Failed to publish to Redis channel {channel}: {e}")
            return 0

    async def subscribe(self, *channels) -> None:
        """Subscribe to channels"""
        try:
            await self.pubsub.subscribe(*channels)
            logger.info(f"📡 Subscribed to Redis channels: {channels}")
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to Redis channels: {e}")

    async def unsubscribe(self, *channels) -> None:
        """Unsubscribe from channels"""
        try:
            await self.pubsub.unsubscribe(*channels)
            logger.info(f"📡 Unsubscribed from Redis channels: {channels}")
        except Exception as e:
            logger.error(f"❌ Failed to unsubscribe from Redis channels: {e}")

    async def get_message(self, timeout: float = 1.0) -> Optional[Dict]:
        """Get message from subscribed channels"""
        try:
            message = await self.pubsub.get_message(timeout=timeout)
            if message and message['type'] == 'message':
                data = message['data']
                try:
                    message['data'] = json.loads(data.decode('utf-8'))
                except:
                    message['data'] = data.decode('utf-8') if isinstance(data, bytes) else data
                return message
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get Redis message: {e}")
            return None

    # Special methods for crypto data
    async def cache_ticker(self, exchange: str, pair: str, ticker_data: Dict, ttl: int = 60) -> bool:
        """Cache ticker data with short TTL"""
        key = f"ticker:{exchange}:{pair}"
        return await self.set(key, ticker_data, expire=ttl)

    async def get_ticker(self, exchange: str, pair: str) -> Optional[Dict]:
        """Get cached ticker data"""
        key = f"ticker:{exchange}:{pair}"
        return await self.get(key)

    async def cache_orderbook(self, exchange: str, pair: str, orderbook_data: Dict, ttl: int = 10) -> bool:
        """Cache orderbook data with very short TTL"""
        key = f"orderbook:{exchange}:{pair}"
        return await self.set(key, orderbook_data, expire=ttl)

    async def get_orderbook(self, exchange: str, pair: str) -> Optional[Dict]:
        """Get cached orderbook data"""
        key = f"orderbook:{exchange}:{pair}"
        return await self.get(key)

    async def cache_signal(self, signal: Dict, ttl: int = 3600) -> bool:
        """Cache trading signal"""
        key = f"signal:{signal['exchange']}:{signal['symbol']}:{int(time.time())}"
        return await self.set(key, signal, expire=ttl)

    async def get_recent_signals(self, exchange: str = None, pair: str = None, limit: int = 10) -> List[Dict]:
        """Get recent signals"""
        try:
            pattern = f"{self._make_key('signal')}:"
            if exchange:
                pattern += f"{exchange}:"
            if pair:
                pattern += f"{pair}:"
            pattern += "*"
            
            keys = await self.redis_client.keys(pattern)
            signals = []
            
            for key in sorted(keys, reverse=True)[:limit]:
                signal = await self.redis_client.get(key)
                if signal:
                    try:
                        signals.append(json.loads(signal.decode('utf-8')))
                    except:
                        continue
            
            return signals
        except Exception as e:
            logger.error(f"❌ Failed to get recent signals: {e}")
            return []

    async def increment_counter(self, key: str, amount: int = 1, expire: Optional[int] = None) -> int:
        """Increment counter with optional expiration"""
        try:
            cache_key = self._make_key(key)
            result = await self.redis_client.incr(cache_key, amount)
            if expire and result == amount:  # First increment
                await self.redis_client.expire(cache_key, expire)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to increment Redis counter {key}: {e}")
            return 0

    async def get_counter(self, key: str) -> int:
        """Get counter value"""
        try:
            cache_key = self._make_key(key)
            value = await self.redis_client.get(cache_key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"❌ Failed to get Redis counter {key}: {e}")
            return 0

    # Rate limiting
    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """Check if action is rate limited"""
        try:
            cache_key = self._make_key(f"rate_limit:{key}")
            current = await self.redis_client.incr(cache_key)
            if current == 1:
                await self.redis_client.expire(cache_key, window)
            return current > limit
        except Exception as e:
            logger.error(f"❌ Failed to check rate limit for {key}: {e}")
            return False

    # Performance monitoring
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get Redis performance statistics"""
        try:
            info = await self.redis_client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory': info.get('used_memory', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': (info.get('keyspace_hits', 0) / 
                           max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)) * 100,
                'uptime_in_seconds': info.get('uptime_in_seconds', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
        except Exception as e:
            logger.error(f"❌ Failed to get Redis performance stats: {e}")
            return {}

    async def cleanup_expired_keys(self, pattern: str = None) -> int:
        """Cleanup expired keys"""
        try:
            search_pattern = f"{self._make_key('*')}" if not pattern else f"{self._make_key(pattern)}"
            keys = await self.redis_client.keys(search_pattern)
            
            expired_count = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    continue
                elif ttl == -2:  # Already expired
                    await self.redis_client.delete(key)
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"🧹 Cleaned up {expired_count} expired Redis keys")
            
            return expired_count
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired keys: {e}")
            return 0

    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            pong = await self.redis_client.ping()
            if pong:
                logger.debug("✅ Redis health check passed")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Redis health check failed: {e}")
            return False

    async def close(self):
        """Close Redis connections"""
        try:
            if self.pubsub:
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("✅ Redis connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing Redis connections: {e}") 