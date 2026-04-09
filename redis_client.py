import redis
import os

REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN")

redis_client = redis.Redis(
    host=REDIS_URL.replace("https://", ""),
    port=6379,
    password=REDIS_TOKEN,
    ssl=True,
    decode_responses=True
)