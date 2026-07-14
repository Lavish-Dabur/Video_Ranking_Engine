import json
import logging
from redis_client import redis_client

CACHE_TTL = 300  # 5 minutes
logger = logging.getLogger(__name__)

def get_cache(query):
    try:
        data = redis_client.get(query)
        if data:
            return json.loads(data)
    except Exception as exc:
        logger.warning("Redis cache read failed; continuing without cache: %s", exc)
        return None

def set_cache(query, results):
    try:
        redis_client.setex(
            query,
            CACHE_TTL,
            json.dumps(results)
        )
    except Exception as exc:
        logger.warning("Redis cache write failed; continuing without cache: %s", exc)
