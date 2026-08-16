# app/main.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.database import get_connection
from app.rate_limit import rate_limit_middleware

from app.routers.studies import router as studies_router
from app.routers.sites import router as sites_router
from app.routers.subjects import router as subjects_router
from app.routers.visits import router as visits_router
from app.routers.adverse_events import (
    router as adverse_events_router,
)
from app.routers.lab_results import (
    router as lab_results_router,
)
from app.routers.protocol_deviations import (
    router as protocol_deviations_router,
)
from app.routers.data_queries import (
    router as data_queries_router,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="ACT Rave Mock API",
    description="""
    PostgreSQL-backed mock clinical Rave API.

    Different source APIs intentionally expose
    different message formats:

    STUDY              -> JSON
    SITE               -> CSV
    SUBJECT            -> JSON
    VISIT              -> XML
    ADVERSE EVENT      -> XML
    LAB RESULT         -> JSON
    PROTOCOL DEVIATION -> CSV
    DATA QUERY         -> XML

    This provides a realistic heterogeneous
    ingestion source for the ACT data platform.
    """,
    version="3.0.0",
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
    studies_router
)

app.include_router(
    sites_router
)

app.include_router(
    subjects_router
)

app.include_router(
    visits_router
)

app.include_router(
    adverse_events_router
)

app.include_router(
    lab_results_router
)

app.include_router(
    protocol_deviations_router
)

app.include_router(
    data_queries_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "application": "ACT Rave Mock API",
        "version": "3.0.0",

        "formats": {
            "studies": "JSON",
            "sites": "CSV",
            "subjects": "JSON",
            "visits": "XML",
            "adverse_events": "XML",
            "lab_results": "JSON",
            "protocol_deviations": "CSV",
            "data_queries": "XML",
        },

        "status": "running",
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
                    """
                    SELECT
                        current_database(),
                        current_user
                    """
                )

                result = cur.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
            "database_name":
                result["current_database"],
            "database_user":
                result["current_user"],
        }

    except Exception as exc:

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(exc),
            },
        )