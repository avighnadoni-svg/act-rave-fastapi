# app/rate_limit.py

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse


request_history = defaultdict(deque)


async def rate_limit_middleware(
    request: Request,
    call_next
):

    # Swagger/OpenAPI should not be restricted
    if request.url.path in [
        "/docs",
        "/redoc",
        "/openapi.json"
    ]:
        return await call_next(request)

    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    now = time.monotonic()

    history = request_history[client_ip]

    # Remove calls older than 5 seconds
    while history and now - history[0] > 5:
        history.popleft()

    # ----------------------------------------
    # Maximum 20 requests / 5 seconds
    # ----------------------------------------

    if len(history) >= 20:

        return JSONResponse(
            status_code=429,
            content={
                "detail": "API rate limit exceeded"
            },
            headers={
                "Retry-After": "5"
            }
        )

    # ----------------------------------------
    # Maximum 10 requests / second
    # ----------------------------------------

    last_second_count = sum(
        1
        for timestamp in history
        if now - timestamp <= 1
    )

    if last_second_count >= 10:

        return JSONResponse(
            status_code=429,
            content={
                "detail": "API rate limit exceeded"
            },
            headers={
                "Retry-After": "1"
            }
        )

    history.append(now)

    return await call_next(request)