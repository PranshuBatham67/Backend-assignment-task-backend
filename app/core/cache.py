import redis
from typing import Optional, Any
import json
from app.config import settings

class CacheManager:
    """
    Redis cache manager for handling caching operations.
    Singleton pattern to reuse the same connection.
    """
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._initialize_client()
        return cls._instance
    
    @classmethod
    def _initialize_client(cls):
        """Initialize Redis client connection"""
        try:
            cls._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            cls._client.ping()
        except redis.ConnectionError:
            # If Redis is not available, cache operations will be no-ops
            print("Warning: Redis connection failed. Caching will be disabled.")
            cls._client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        Automatically deserializes JSON.
        """
        if not self._client:
            return None
        
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except (redis.RedisError, json.JSONDecodeError):
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set a value in cache with TTL (time to live) in seconds.
        Default TTL is 5 minutes.
        """
        if not self._client:
            return False
        
        try:
            serialized = json.dumps(value)
            return self._client.setex(key, ttl, serialized)
        except (redis.RedisError, TypeError):
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self._client:
            return False
        
        try:
            return bool(self._client.delete(key))
        except redis.RedisError:
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        Useful for cache invalidation.
        """
        if not self._client:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except redis.RedisError:
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        if not self._client:
            return False
        
        try:
            return bool(self._client.exists(key))
        except redis.RedisError:
            return False

# Global cache instance
cache = CacheManager()
