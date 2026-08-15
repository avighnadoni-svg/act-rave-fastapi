from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from app.data_store import load_json, get_by_id, filter_records, filter_updated_since, paginate
from app.models import Visit

router = APIRouter(prefix="/visits", tags=["Visits"])


@router.get("", response_model=list[Visit])
def list_records(
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    updated_since: datetime | None = None, subject_id: str | None = None,
):
    records = load_json("visits.json")
    records = filter_records(records, subject_id=subject_id)
    records = filter_updated_since(records, updated_since)
    response.headers["X-Total-Count"] = str(len(records))
    return paginate(records, offset=offset, limit=limit)


@router.get("/{visit_id}", response_model=Visit)
def get_record(visit_id: str):
    records = load_json("visits.json")
    record = get_by_id(records, "visit_id", visit_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Visit not found"},
        )
    return record
