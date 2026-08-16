# app/rate_limit.py

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from app.logging_config import get_logger


logger = get_logger(__name__)


request_history = defaultdict(deque)


async def rate_limit_middleware(
    request: Request,
    call_next,
):

    # Swagger/OpenAPI should not be restricted.
    if request.url.path in [
        "/docs",
        "/redoc",
        "/openapi.json",
    ]:
        return await call_next(request)

    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    now = time.monotonic()

    history = request_history[client_ip]

    # Remove calls older than 5 seconds.
    while history and now - history[0] > 5:
        history.popleft()

    # ========================================================
    # MAXIMUM 20 REQUESTS / 5 SECONDS
    # ========================================================

    if len(history) >= 20:

        logger.warning(
            "API rate limit exceeded | "
            "client_ip=%s | method=%s | path=%s | "
            "rule=20_requests_per_5_seconds | retry_after=5",
            client_ip,
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=429,
            content={
                "detail": "API rate limit exceeded"
            },
            headers={
                "Retry-After": "5"
            },
        )

    # ========================================================
    # MAXIMUM 10 REQUESTS / SECOND
    # ========================================================

    last_second_count = sum(
        1
        for timestamp in history
        if now - timestamp <= 1
    )

    if last_second_count >= 10:

        logger.warning(
            "API rate limit exceeded | "
            "client_ip=%s | method=%s | path=%s | "
            "rule=10_requests_per_second | retry_after=1",
            client_ip,
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=429,
            content={
                "detail": "API rate limit exceeded"
            },
            headers={
                "Retry-After": "1"
            },
        )

    history.append(now)

    return await call_next(request)
