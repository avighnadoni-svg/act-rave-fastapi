from collections import defaultdict, deque
from time import monotonic
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory demo limiter: 10 requests/sec and 20 requests/5 sec per client."""

    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # Keep health/docs usable while developing.
        if request.url.path in {"/", "/health", "/docs", "/openapi.json"}:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = monotonic()
        q = self.requests[client]

        while q and now - q[0] > 5:
            q.popleft()

        last_second = sum(1 for ts in q if now - ts <= 1)
        if last_second >= 10 or len(q) >= 20:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Retry after 1 second.",
                },
                headers={"Retry-After": "1"},
            )

        q.append(now)
        return await call_next(request)
