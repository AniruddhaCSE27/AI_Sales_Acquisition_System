from __future__ import annotations

import time
from collections import defaultdict, deque

from redis import Redis

from app.core.config import settings

_memory_buckets: dict[str, deque[float]] = defaultdict(deque)
_redis_client: Redis | None = None


def _client() -> Redis | None:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=0.2, socket_timeout=0.2)
        _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = None
        return None


def too_many_requests(key: str) -> bool:
    if not settings.rate_limit_enabled:
        return False
    limit = settings.rate_limit_requests
    window = settings.rate_limit_window_seconds
    client = _client()
    if client is not None:
        try:
            redis_key = f"{settings.rate_limit_redis_prefix}:{key}:{int(time.time() // window)}"
            count = client.incr(redis_key)
            if count == 1:
                client.expire(redis_key, window + 5)
            return int(count) > limit
        except Exception:
            pass

    now = time.time()
    bucket = _memory_buckets[key]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False
