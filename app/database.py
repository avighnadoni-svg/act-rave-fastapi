# app/database.py

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

from app.logging_config import get_logger


# ============================================================
# PROJECT ENVIRONMENT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(
    dotenv_path=ENV_FILE
)


# ============================================================
# LOGGING
# ============================================================

logger = get_logger(__name__)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    (
        "postgresql://"
        "rave_user:rave_password"
        "@127.0.0.1:5432/"
        "rave_db"
    ),
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Return a PostgreSQL connection.

    dict_row returns rows as dictionaries so FastAPI
    can easily serialize them to JSON.

    The connection string is intentionally never logged
    because it can contain credentials.
    """

    try:
        return psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row,
        )

    except Exception:
        logger.exception(
            "PostgreSQL connection failed"
        )
        raise


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

def test_connection():
    """
    Verify PostgreSQL connectivity.
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_database(), current_user;"
                )

                result = cur.fetchone()

        logger.info(
            "PostgreSQL connectivity check succeeded | "
            "database=%s | user=%s",
            result["current_database"],
            result["current_user"],
        )

        return result

    except Exception:
        logger.exception(
            "PostgreSQL connectivity check failed"
        )
        raise
