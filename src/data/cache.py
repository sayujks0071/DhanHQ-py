"""
Caching layer for the Liquid F&O Trading System.
"""

import redis
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from ..config import config


@dataclass
class CacheConfig:
    """Cache configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True


class CacheManager:
    """Redis-based cache manager."""
    
    def __init__(self, cache_config: Optional[CacheConfig] = None):
        self.logger = logging.getLogger(__name__)
        self.config = cache_config or CacheConfig()
        self.redis_client = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=True
            )
            
            # Test connection
            self.redis_client.ping()
            self.logger.info("Connected to Redis cache")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if not self.is_connected():
            return default
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Try pickle
                try:
                    return pickle.loads(value.encode())
                except:
                    return value
                    
        except Exception as e:
            self.logger.warning(f"Failed to get cache key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self.is_connected():
            return False
        
        try:
            # Try JSON serialization first
            try:
                serialized = json.dumps(value, default=str)
            except (TypeError, ValueError):
                # Fall back to pickle
                serialized = pickle.dumps(value)
            
            if ttl:
                return self.redis_client.setex(key, ttl, serialized)
            else:
                return self.redis_client.set(key, serialized)
                
        except Exception as e:
            self.logger.warning(f"Failed to set cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            self.logger.warning(f"Failed to delete cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            self.logger.warning(f"Failed to check cache key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            self.logger.warning(f"Failed to set expiration for key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get TTL for key."""
        if not self.is_connected():
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            self.logger.warning(f"Failed to get TTL for key {key}: {e}")
            return -1
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        if not self.is_connected():
            return []
        
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            self.logger.warning(f"Failed to get keys with pattern {pattern}: {e}")
            return []
    
    def clear(self, pattern: str = "*") -> int:
        """Clear keys matching pattern."""
        if not self.is_connected():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            self.logger.warning(f"Failed to clear keys with pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.is_connected():
            return {"connected": False}
        
        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            self.logger.warning(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return hits / total
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        if not self.is_connected():
            return {"connected": False}
        
        try:
            info = self.redis_client.info("memory")
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_rss": info.get("used_memory_rss", 0),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "maxmemory": info.get("maxmemory", 0),
                "maxmemory_policy": info.get("maxmemory_policy", "noeviction")
            }
        except Exception as e:
            self.logger.warning(f"Failed to get memory usage: {e}")
            return {"connected": False, "error": str(e)}


class DataCache:
    """High-level data cache with TTL management."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        
        # Default TTL values (in seconds)
        self.ttl_config = {
            'instruments': 3600,  # 1 hour
            'candles': 300,       # 5 minutes
            'option_chain': 60,   # 1 minute
            'quotes': 10,         # 10 seconds
            'funds': 30,          # 30 seconds
            'positions': 30,      # 30 seconds
            'orders': 10,         # 10 seconds
        }
    
    def get_instruments(self, exchange_segment: str = None) -> Optional[Dict]:
        """Get cached instruments."""
        key = f"instruments:{exchange_segment or 'all'}"
        return self.cache_manager.get(key)
    
    def set_instruments(self, instruments: Dict, exchange_segment: str = None) -> bool:
        """Cache instruments."""
        key = f"instruments:{exchange_segment or 'all'}"
        ttl = self.ttl_config['instruments']
        return self.cache_manager.set(key, instruments, ttl)
    
    def get_candles(self, security_id: str, timeframe: str, 
                   start_date: str, end_date: str) -> Optional[Dict]:
        """Get cached candles."""
        key = f"candles:{security_id}:{timeframe}:{start_date}:{end_date}"
        return self.cache_manager.get(key)
    
    def set_candles(self, security_id: str, timeframe: str, 
                   start_date: str, end_date: str, candles: Dict) -> bool:
        """Cache candles."""
        key = f"candles:{security_id}:{timeframe}:{start_date}:{end_date}"
        ttl = self.ttl_config['candles']
        return self.cache_manager.set(key, candles, ttl)
    
    def get_option_chain(self, underlying: str, expiry_date: str) -> Optional[Dict]:
        """Get cached option chain."""
        key = f"option_chain:{underlying}:{expiry_date}"
        return self.cache_manager.get(key)
    
    def set_option_chain(self, underlying: str, expiry_date: str, 
                        chain: Dict) -> bool:
        """Cache option chain."""
        key = f"option_chain:{underlying}:{expiry_date}"
        ttl = self.ttl_config['option_chain']
        return self.cache_manager.set(key, chain, ttl)
    
    def get_quote(self, security_id: str) -> Optional[Dict]:
        """Get cached quote."""
        key = f"quote:{security_id}"
        return self.cache_manager.get(key)
    
    def set_quote(self, security_id: str, quote: Dict) -> bool:
        """Cache quote."""
        key = f"quote:{security_id}"
        ttl = self.ttl_config['quotes']
        return self.cache_manager.set(key, quote, ttl)
    
    def get_funds(self) -> Optional[Dict]:
        """Get cached funds data."""
        key = "funds"
        return self.cache_manager.get(key)
    
    def set_funds(self, funds: Dict) -> bool:
        """Cache funds data."""
        key = "funds"
        ttl = self.ttl_config['funds']
        return self.cache_manager.set(key, funds, ttl)
    
    def get_positions(self) -> Optional[List]:
        """Get cached positions."""
        key = "positions"
        return self.cache_manager.get(key)
    
    def set_positions(self, positions: List) -> bool:
        """Cache positions."""
        key = "positions"
        ttl = self.ttl_config['positions']
        return self.cache_manager.set(key, positions, ttl)
    
    def get_orders(self) -> Optional[List]:
        """Get cached orders."""
        key = "orders"
        return self.cache_manager.get(key)
    
    def set_orders(self, orders: List) -> bool:
        """Cache orders."""
        key = "orders"
        ttl = self.ttl_config['orders']
        return self.cache_manager.set(key, orders, ttl)
    
    def invalidate_security(self, security_id: str) -> None:
        """Invalidate all cache entries for a security."""
        patterns = [
            f"quote:{security_id}",
            f"candles:{security_id}:*",
            f"option_chain:*:{security_id}:*"
        ]
        
        for pattern in patterns:
            self.cache_manager.clear(pattern)
    
    def invalidate_all(self) -> None:
        """Invalidate all cache entries."""
        self.cache_manager.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = self.cache_manager.get_stats()
        
        # Add cache key counts
        key_counts = {}
        for data_type in self.ttl_config.keys():
            pattern = f"{data_type}:*"
            keys = self.cache_manager.keys(pattern)
            key_counts[data_type] = len(keys)
        
        stats['key_counts'] = key_counts
        return stats
