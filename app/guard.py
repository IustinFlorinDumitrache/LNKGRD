import time
from datetime import UTC, datetime

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.redis_client import get_redis

KILL_SWITCH_KEY = "killswitch"
BLOCK_PREFIX = "blocked:ip:"

#
EXEMPT_PREFIXES = ("/admin", "/health", "/metrics", "/docs", "/openapi.json")


def client_ip(request: Request) -> str:
    if get_settings().trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ---------- blocklist ----------

def block_ip(ip: str, ttl_seconds: int | None = None, reason: str = "manual") -> int:
    ttl = ttl_seconds or get_settings().default_block_ttl_seconds
    get_redis().set(BLOCK_PREFIX + ip, reason, ex=ttl)
    return ttl


def unblock_ip(ip: str) -> bool:
    return bool(get_redis().delete(BLOCK_PREFIX + ip))


def list_blocked() -> list[dict]:
    r = get_redis()
    return [
        {"ip": key.removeprefix(BLOCK_PREFIX), "reason": r.get(key), "expires_in": r.ttl(key)}
        for key in r.scan_iter(match=BLOCK_PREFIX + "*")
    ]


# ---------- kill switch ----------

def set_kill_switch(enabled: bool) -> None:
    if enabled:
        get_redis().set(KILL_SWITCH_KEY, "1")
    else:
        get_redis().delete(KILL_SWITCH_KEY)


def kill_switch_on() -> bool:
    return get_redis().get(KILL_SWITCH_KEY) == "1"


# ---------- rate limiting ----------

def _hit(key: str, window_seconds: int) -> int:
    pipe = get_redis().pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds, nx=True)
    count, _ = pipe.execute()
    return int(count)


def check_key_quota(api_key_id: int) -> None:
    limit = get_settings().links_per_key_per_day
    day = datetime.now(UTC).strftime("%Y%m%d")
    if _hit(f"quota:key:{api_key_id}:{day}", 86400) > limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Daily quota of {limit} links exceeded for this API key",
        )


class GuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(EXEMPT_PREFIXES):
            return await call_next(request)

        ip = client_ip(request)

        if kill_switch_on():
            return JSONResponse({"detail": "Service temporarily disabled"}, status_code=503)

        if get_redis().exists(BLOCK_PREFIX + ip):
            return JSONResponse({"detail": "Your IP has been blocked"}, status_code=403)

        minute = int(time.time() // 60)
        if _hit(f"rl:ip:{ip}:{minute}", 60) > get_settings().requests_per_ip_per_minute:
            retry_after = 60 - int(time.time()) % 60
            return JSONResponse(
                {"detail": "Too many requests"},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)