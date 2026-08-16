# app/main.py

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import get_connection
from app.logging_config import (
    LOG_FILE,
    configure_logging,
    get_logger,
    reset_request_id,
    set_request_id,
)
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
# LOGGING
# ============================================================

configure_logging()
logger = get_logger(__name__)


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Log application startup and shutdown without exposing
    credentials or sensitive configuration values.
    """

    logger.info(
        "ACT Rave Mock API starting | version=3.0.0 | "
        "log_file=%s",
        LOG_FILE,
    )

    yield

    logger.info(
        "ACT Rave Mock API stopping | version=3.0.0"
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
    lifespan=lifespan,
)


# ============================================================
# RATE LIMITING
# ============================================================

app.middleware("http")(
    rate_limit_middleware
)


# ============================================================
# REQUEST / RESPONSE LOGGING
# ============================================================

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    """
    Log one structured start/completion record per HTTP request.

    Only selected operational query parameters are logged.
    Request/response bodies, credentials, tokens, and complete
    clinical payloads are intentionally excluded.
    """

    request_id = (
        request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )

    token = set_request_id(
        request_id
    )

    started_at = time.perf_counter()

    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    safe_query_parameters = {}

    safe_parameter_names = (
        "study_id",
        "subject_id",
        "site_id",
        "updated_since",
        "offset",
        "limit",
        "phase",
        "country",
        "status",
        "severity",
        "visit_name",
    )

    for parameter_name in safe_parameter_names:
        parameter_value = request.query_params.get(
            parameter_name
        )

        if parameter_value is not None:
            safe_query_parameters[
                parameter_name
            ] = parameter_value

    logger.info(
        "HTTP request started | method=%s | path=%s | "
        "client_ip=%s | query=%s",
        request.method,
        request.url.path,
        client_ip,
        safe_query_parameters or "{}",
    )

    try:
        response = await call_next(
            request
        )

        duration_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        log_method = (
            logger.warning
            if response.status_code >= 400
            else logger.info
        )

        log_method(
            "HTTP request completed | method=%s | path=%s | "
            "status_code=%s | duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response

    except Exception:
        duration_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        logger.exception(
            "HTTP request failed | method=%s | path=%s | "
            "duration_ms=%s",
            request.method,
            request.url.path,
            duration_ms,
        )

        raise

    finally:
        reset_request_id(
            token
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

        logger.info(
            "Health check succeeded | database=%s | user=%s",
            result["current_database"],
            result["current_user"],
        )

        return {
            "status": "healthy",
            "database": "connected",
            "database_name":
                result["current_database"],
            "database_user":
                result["current_user"],
        }

    except Exception:
        logger.exception(
            "Health check failed | database=disconnected"
        )

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": "Database connectivity check failed",
            },
        )
