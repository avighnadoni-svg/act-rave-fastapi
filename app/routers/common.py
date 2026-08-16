# app/routers/common.py

from typing import Any

from app.database import get_connection


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

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                final_query,
                final_params,
            )

            return cur.fetchall()


def fetch_one(
    query: str,
    params: tuple,
):
    """
    Common function used by GET-by-ID endpoints.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                query,
                params,
            )

            return cur.fetchone()


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