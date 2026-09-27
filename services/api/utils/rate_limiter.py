import os

import jwt
from fastapi import Request, HTTPException
from redis.exceptions import RedisError

from api.utils.logging import log_event
from api.utils.metrics import journal_rate_limit_rejections_total
from api.utils.utils import ALGORITHM, get_client_ip

RATE_LIMIT_LUA = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

async def user_identifier(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(auth[7:], os.getenv("JWT_SECRET_KEY"), algorithms=[ALGORITHM])
            if payload.get("sub") and payload.get("purpose") == "access":
                return f"user:{payload['sub']}"
        except jwt.PyJWTError:
            pass
    return f"ip:{get_client_ip(request) or 'unknown'}"

class RateLimiter:
    def __init__(self, times: int, seconds: int, name: str, identifier=user_identifier):
        self.times = times
        self.seconds = seconds
        self.identifier = identifier
        self.name = name

    async def __call__(self, request: Request):
        identifier = await self.identifier(request)
        route = request.scope["route"].path
        key = f"ratelimit:{self.name}:{identifier}:{route}"
        redis = request.app.state.redis_client
        try:
            count = await redis.eval(RATE_LIMIT_LUA, 1, key, self.seconds)
        except RedisError as e:
            log_event("WARNING", "rate_limit_skipped", reason="redis unavailable", error=str(e))
            return
        if count > self.times:
            journal_rate_limit_rejections_total.labels(limiter=self.name, route=route).inc()
            raise HTTPException(429, "Too Many Requests",
                                headers={"Retry-After": str(self.seconds)})