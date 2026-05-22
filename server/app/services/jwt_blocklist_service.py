import time
from redis import Redis, RedisError
from app.config import Config

_client = Redis.from_url(Config.REDIS_URL, decode_responses=True)

_JTI_PREFIX = "jwt:blocklist:"
_USER_INVALID_BEFORE_PREFIX = "jwt:user_invalid_before:"
_USER_INVALID_BEFORE_TTL = 86400  # 24 hours


def revoke_token(jti: str, exp: int) -> None:
    ttl = int(exp) - int(time.time())
    if ttl <= 0:
        return
    _client.setex(_JTI_PREFIX + jti, ttl, "1")


def is_token_revoked(jti: str) -> bool:
    try:
        return _client.exists(_JTI_PREFIX + jti) == 1
    except RedisError:
        return True


def invalidate_user_tokens(user_id: int) -> None:
    key = _USER_INVALID_BEFORE_PREFIX + str(user_id)
    _client.setex(key, _USER_INVALID_BEFORE_TTL, str(int(time.time())))


def is_token_invalid_for_user(user_id: int, iat: int) -> bool:
    try:
        raw = _client.get(_USER_INVALID_BEFORE_PREFIX + str(user_id))
        if raw is None:
            return False
        return iat < int(raw)
    except RedisError:
        return True
