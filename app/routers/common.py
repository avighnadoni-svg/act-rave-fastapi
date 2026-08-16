# app/routers/common.py

import time
from typing import Any

from app.database import get_connection
from app.logging_config import get_logger


logger = get_logger(__name__)


# ============================================================
# FETCH COLLECTION
# ============================================================

def fetch_many(
    query: str,
    params: list[Any],
    offset: int,
    limit: int,
    order_by: str,
):
    """
    Common function used by collection endpoints.

    Supports:
    - filters
    - incremental extraction
    - pagination

    SQL text and parameter values are intentionally not
    written to logs to avoid leaking sensitive data.
    """

    final_query = f"""
        {query}
        ORDER BY updated_at, {order_by}
        OFFSET %s
        LIMIT %s
    """

    final_params = [
        *params,
        offset,
        limit,
    ]

    started_at = time.perf_counter()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    final_query,
                    final_params,
                )

                records = cur.fetchall()

        duration_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        logger.info(
            "Database collection query completed | "
            "rows=%s | offset=%s | limit=%s | "
            "order_by=%s | duration_ms=%s",
            len(records),
            offset,
            limit,
            order_by,
            duration_ms,
        )

        return records

    except Exception:
        duration_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        logger.exception(
            "Database collection query failed | "
            "offset=%s | limit=%s | order_by=%s | "
            "duration_ms=%s",
            offset,
            limit,
            order_by,
            duration_ms,
        )
        raise


# ============================================================
# FETCH ONE RECORD
# ============================================================

def fetch_one(
    query: str,
    params: tuple | list,
):
    """
    Common function used by GET-by-ID endpoints.

    SQL text and parameter values are intentionally not
    written to logs to avoid leaking sensitive data.
    """

    started_at = time.perf_counter()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    params,
                )

                record = cur.fetchone()

        duration_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        logger.info(
            "Database single-record query completed | "
            "found=%s | duration_ms=%s",
            record is not None,
            duration_ms,
        )

        return record

    except Exception:
        duration_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        logger.exception(
            "Database single-record query failed | "
            "duration_ms=%s",
            duration_ms,
        )
        raise


# ============================================================
# OUTPUT VALUE CONVERSION
# ============================================================

def value_to_string(value):
    """
    Convert database values to values suitable
    for CSV/XML output.
    """

    if value is None:
        return ""

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)
