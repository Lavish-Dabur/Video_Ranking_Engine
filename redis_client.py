import redis
import os
from urllib.parse import urlparse

REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN")

def create_redis_client():
    """Return a cache client when configured, without blocking API startup."""
    if not REDIS_URL:
        return None

    parsed = urlparse(
        REDIS_URL if "://" in REDIS_URL else f"rediss://{REDIS_URL}"
    )
    if not parsed.hostname:
        return None

    return redis.Redis(
        host=parsed.hostname,
        port=parsed.port or 6379,
        password=REDIS_TOKEN,
        ssl=parsed.scheme in {"https", "rediss"},
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        retry_on_timeout=False,
        health_check_interval=30,
    )


redis_client = create_redis_client()
