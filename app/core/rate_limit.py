"""IP-based in-memory rate limiter middleware for BachNest API.

Uses a sliding-window counter per (IP, route) pair stored in a simple dict
protected by asyncio.Lock.  For production, swap the store for a Redis
INCR/EXPIRE approach via the existing REDIS_URL setting.
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


# (ip, path_prefix) -> list[request_timestamp]
_counters: Dict[Tuple[str, str], List[float]] = defaultdict(list)
_lock = asyncio.Lock()

# Routes exempt from rate-limiting (health checks, static assets, docs)
_EXEMPT_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/api/v1/health")

# Default policy: 60 requests per 60-second window per IP
DEFAULT_LIMIT = 60
DEFAULT_WINDOW_SECONDS = 60

# Tighter policy for auth endpoints to slow brute-force attempts
AUTH_LIMIT = 10
AUTH_WINDOW_SECONDS = 60
_AUTH_PREFIX = "/api/v1/auth"


def _client_ip(request: Request) -> str:
    """Extract the real client IP, respecting common reverse-proxy headers."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate-limit middleware.

    Attaches ``X-RateLimit-Limit``, ``X-RateLimit-Remaining``, and
    ``X-RateLimit-Reset`` headers to every non-exempt response so that
    API clients can self-throttle gracefully.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Skip exempt paths
        if any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        # Choose policy
        if path.startswith(_AUTH_PREFIX):
            limit, window = AUTH_LIMIT, AUTH_WINDOW_SECONDS
        else:
            limit, window = DEFAULT_LIMIT, DEFAULT_WINDOW_SECONDS

        ip = _client_ip(request)
        key = (ip, _AUTH_PREFIX if path.startswith(_AUTH_PREFIX) else "default")
        now = time.monotonic()
        window_start = now - window

        async with _lock:
            timestamps = _counters[key]
            # Evict timestamps outside the current window
            _counters[key] = [t for t in timestamps if t > window_start]
            current_count = len(_counters[key])

            if current_count >= limit:
                reset_at = int(_counters[key][0] + window - now) + 1
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "message": "Too many requests. Please slow down and try again shortly.",
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "details": {"retry_after_seconds": reset_at},
                        },
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_at),
                        "Retry-After": str(reset_at),
                    },
                )

            _counters[key].append(now)
            remaining = limit - current_count - 1

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(window)
        return response
