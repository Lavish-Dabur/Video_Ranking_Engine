import redis
import os
from urllib.parse import urlparse

REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN")

def create_redis_client():
    """Return a cache client when configured, without blocking API startup."""
    if not REDIS_URL:
        return None

    url_str = REDIS_URL if "://" in REDIS_URL else f"rediss://{REDIS_URL}"
    parsed = urlparse(url_str)
    if not parsed.hostname:
        return None

    try:
        return redis.Redis(
            host=parsed.hostname,
            port=parsed.port or 6379,
            password=parsed.password or REDIS_TOKEN,
            ssl=parsed.scheme in {"https", "rediss"},
            ssl_cert_reqs=None,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=False,
        )
    except Exception as e:
        print("Redis Client Init Error:", e)
        return None


redis_client = create_redis_client()

