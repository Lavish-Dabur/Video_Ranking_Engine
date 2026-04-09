import json
from redis_client import redis_client

CACHE_TTL = 300  # 5 minutes

def get_cache(query):
    try:
        data = redis_client.get(query)
        if data:
            return json.loads(data)
    except:
        return None

def set_cache(query, results):
    try:
        redis_client.setex(
            query,
            CACHE_TTL,
            json.dumps(results)
        )
    except:
        pass