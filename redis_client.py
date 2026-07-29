import os
from urllib.parse import urlparse

import redis
import requests

REDIS_URL = os.getenv("REDIS_URL") or os.getenv("REDIS-URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN")


class UpstashRestClient:
    """HTTP REST client for Upstash Redis endpoints."""

    def __init__(self, url, token):
        self.url = url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def get(self, key):
        try:
            resp = requests.get(f"{self.url}/get/{key}", headers=self.headers, timeout=2)
            if resp.status_code == 200:
                return resp.json().get("result")
        except Exception:
            return None
        return None

    def setex(self, key, ttl, value):
        try:
            requests.post(
                f"{self.url}/set/{key}",
                data=value,
                params={"EX": ttl},
                headers=self.headers,
                timeout=2,
            )
        except Exception:
            pass


def create_redis_client():
    """Return a cache client when configured, supporting both TCP Redis and Upstash REST API."""
    if not REDIS_URL:
        return None

    if REDIS_URL.startswith("http://") or REDIS_URL.startswith("https://"):
        return UpstashRestClient(REDIS_URL, REDIS_TOKEN)

    url_str = REDIS_URL if "://" in REDIS_URL else f"rediss://{REDIS_URL}"
    parsed = urlparse(url_str)
    if not parsed.hostname:
        return None

    try:
        return redis.Redis(
            host=parsed.hostname,
            port=parsed.port or 6379,
            password=parsed.password or REDIS_TOKEN,
            ssl=parsed.scheme in {"rediss"},
            ssl_cert_reqs=None,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=False,
        )
    except Exception as e:
        print("Redis Client Init Error:", e)
        return None


redis_client = create_redis_client()
