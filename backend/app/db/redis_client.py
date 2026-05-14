import json

import redis

from app.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_cache(key: str):
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None


def set_cache(key: str, data: dict, ttl_seconds: int = 1800):
    redis_client.setex(key, ttl_seconds, json.dumps(data, ensure_ascii=False))


def delete_cache(key: str):
    redis_client.delete(key)


def delete_cache_pattern(pattern: str):
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
