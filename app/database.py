# app/database.py

import os

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rave_user:rave_password@postgres:5432/rave_db"
)


def get_connection():
    """
    Return a PostgreSQL connection.

    dict_row returns rows as dictionaries so FastAPI
    can easily serialize them to JSON.
    """

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


def test_connection():
    """
    Verify PostgreSQL connectivity.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user;")
            return cur.fetchone()