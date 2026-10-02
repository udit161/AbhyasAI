import json
import hashlib
import time
from typing import Optional, Dict, Any, List, Tuple
from app.core.config import settings


class _InMemoryTTLCache:
    """
    In-memory fallback TTL cache used when Redis server is unreachable.
    """
    def __init__(self, max_items: int = 1000):
        self.max_items = max_items
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            expires_at, value = self._cache[key]
            if time.time() < expires_at:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        if len(self._cache) >= self.max_items:
            now = time.time()
            expired_keys = [k for k, (exp, _) in self._cache.items() if now >= exp]
            for k in expired_keys:
                del self._cache[k]
            if len(self._cache) >= self.max_items:
                first_key = next(iter(self._cache))
                del self._cache[first_key]

        expires_at = time.time() + ttl
        self._cache[key] = (expires_at, value)

    def clear(self):
        self._cache.clear()


class CacheService:
    """
    Production Redis caching service with automatic fallback to in-memory TTL cache.
    Caches frequent RAG query responses to reduce LLM latency and API costs.
    """

    def __init__(self):
        self.redis_client = None
        self.fallback_cache = _InMemoryTTLCache()
        self._init_redis()

    def _init_redis(self):
        if settings.REDIS_URL:
            try:
                import redis
                client = redis.Redis.from_url(
                    settings.REDIS_URL,
                    socket_timeout=0.5,
                    socket_connect_timeout=0.5,
                    decode_responses=True,
                )
                client.ping()
                self.redis_client = client
            except Exception:
                self.redis_client = None

    def generate_cache_key(
        self,
        video_id: str,
        current_timestamp: float,
        query: str,
        permitted_doc_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Generates a unique deterministic cache key string for a RAG query payload.
        """
        docs_str = ",".join(sorted(permitted_doc_ids)) if permitted_doc_ids else ""
        raw_key = f"rag_cache:{video_id}:{current_timestamp:.1f}:{query.strip().lower()}:{docs_str}"
        return "rag_cache:" + hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached response dict if present and valid.
        """
        if self.redis_client:
            try:
                cached_str = self.redis_client.get(cache_key)
                if cached_str:
                    return json.loads(cached_str)
            except Exception:
                pass

        return self.fallback_cache.get(cache_key)

    def set_cached_response(
        self,
        cache_key: str,
        response_data: Dict[str, Any],
        ttl: Optional[int] = None,
    ):
        """
        Stores RAG response dict into cache with TTL expiry.
        """
        ttl_seconds = ttl or settings.CACHE_TTL_SECONDS
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, ttl_seconds, json.dumps(response_data))
                return
            except Exception:
                pass

        self.fallback_cache.set(cache_key, response_data, ttl=ttl_seconds)


cache_service = CacheService()
