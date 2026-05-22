import time
from redis import Redis, RedisError
from app.config import Config

_client = Redis.from_url(Config.REDIS_URL, decode_responses=True)
_KEY_PREFIX = "jwt:blocklist:"


def revoke_token(jti: str, exp: int) -> None:
    ttl = int(exp) - int(time.time())
    if ttl <= 0:
        return
    _client.setex(_KEY_PREFIX + jti, ttl, "1")


def is_token_revoked(jti: str) -> bool:
    try:
        return _client.exists(_KEY_PREFIX + jti) == 1
    except RedisError:
        return True
