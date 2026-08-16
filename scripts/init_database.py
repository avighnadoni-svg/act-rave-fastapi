# scripts/init_database.py

import sys
from pathlib import Path


# ============================================================
# PROJECT PATH SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Now Python can find:
#
# act-rave-fastapi/
# ├── app/
# └── scripts/
#
from app.database import get_connection


# ============================================================
# SQL FILE
# ============================================================

SQL_FILE = PROJECT_ROOT / "sql" / "init_db.sql"


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    print("=" * 60)
    print("ACT RAVE POSTGRESQL INITIALIZATION")
    print("=" * 60)

    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_FILE}"
        )

    print(f"Reading SQL file: {SQL_FILE}")

    sql_script = SQL_FILE.read_text(
        encoding="utf-8"
    )

    with get_connection() as conn:

        with conn.cursor() as cur:

            print("Executing init_db.sql...")

            cur.execute(sql_script)

        conn.commit()

    print("Database initialized successfully.")


# ============================================================
# VERIFY TABLES
# ============================================================

def verify_database():

    tables = [
        "study",
        "site",
        "subject",
        "visit",
        "adverse_event",
        "lab_result",
        "protocol_deviation",
        "data_query"
    ]

    print()
    print("=" * 60)
    print("TABLE VERIFICATION")
    print("=" * 60)

    with get_connection() as conn:

        with conn.cursor() as cur:

            for table in tables:

                cur.execute(
                    f"""
                    SELECT COUNT(*) AS record_count
                    FROM {table}
                    """
                )

                result = cur.fetchone()

                print(
                    f"{table:<25}"
                    f"{result['record_count']}"
                )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    initialize_database()

    verify_database()