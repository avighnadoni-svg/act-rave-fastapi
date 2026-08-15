"""Example ACT ingestion client.

Demonstrates:
- GET-only extraction
- 30 second timeout
- pagination
- retry with exponential backoff for 429/5xx
- Retry-After handling
- bounded parallel extraction across endpoints
"""

import asyncio
from typing import Any
import httpx

BASE_URL = "http://127.0.0.1:8000"
PAGE_SIZE = 100
MAX_RETRIES = 4
CONCURRENCY = 4

ENDPOINTS = [
    "/studies",
    "/sites",
    "/subjects",
    "/visits",
    "/adverse-events",
    "/lab-results",
    "/protocol-deviations",
    "/data-queries",
]


async def get_with_retry(client: httpx.AsyncClient, url: str, params: dict[str, Any]):
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.get(url, params=params)
            if response.status_code == 429:
                wait = float(response.headers.get("Retry-After", 2 ** attempt))
                await asyncio.sleep(wait)
                continue
            if response.status_code >= 500:
                await asyncio.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response
        except (httpx.TimeoutException, httpx.TransportError):
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"Request failed after retries: {url}")


async def extract_endpoint(client: httpx.AsyncClient, endpoint: str):
    all_rows: list[dict[str, Any]] = []
    offset = 0

    while True:
        response = await get_with_retry(
            client,
            f"{BASE_URL}{endpoint}",
            {"offset": offset, "limit": PAGE_SIZE},
        )
        rows = response.json()
        all_rows.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    print(f"{endpoint}: {len(all_rows)} records")
    return endpoint, all_rows


async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=30.0) as client:
        async def bounded(endpoint: str):
            async with semaphore:
                return await extract_endpoint(client, endpoint)

        results = await asyncio.gather(*(bounded(e) for e in ENDPOINTS))

    return dict(results)


if __name__ == "__main__":
    asyncio.run(main())
