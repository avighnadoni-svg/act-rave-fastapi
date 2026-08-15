from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.rate_limit import RateLimitMiddleware
from app.routers import (
    studies,
    sites,
    subjects,
    visits,
    adverse_events,
    lab_results,
    protocol_deviations,
    data_queries,
)

app = FastAPI(
    title="ACT Rave Mock API",
    version="1.1.0",
    description="Read-only mock Rave-style API for ACT ingestion practice.",
)

app.add_middleware(RateLimitMiddleware)

app.include_router(studies.router)
app.include_router(sites.router)
app.include_router(subjects.router)
app.include_router(visits.router)
app.include_router(adverse_events.router)
app.include_router(lab_results.router)
app.include_router(protocol_deviations.router)
app.include_router(data_queries.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Unexpected server error",
        },
    )


@app.get("/", tags=["System"])
def root():
    return {
        "message": "ACT Rave Mock API is running",
        "mode": "read-only",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
def health():
    return {"status": "UP"}
