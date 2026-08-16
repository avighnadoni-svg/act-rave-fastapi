# app/main.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.database import get_connection
from app.rate_limit import rate_limit_middleware
from app.routers.clinical import router as clinical_router


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="ACT Rave Mock API",
    description="""
    PostgreSQL backed mock Rave Clinical API.

    PostgreSQL
        ↓
    FastAPI
        ↓
    JSON
        ↓
    Airflow
        ↓
    AWS S3
        ↓
    Snowflake
    """,
    version="2.0.0"
)


# ============================================================
# RATE LIMITING
# ============================================================

app.middleware("http")(
    rate_limit_middleware
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    clinical_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "application": "ACT Rave Mock API",
        "version": "2.0.0",
        "status": "running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    "SELECT current_database(), current_user"
                )

                result = cur.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
            "database_name": result[
                "current_database"
            ],
            "database_user": result[
                "current_user"
            ]
        }

    except Exception as exc:

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(exc)
            }
        )