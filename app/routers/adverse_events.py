from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from app.data_store import load_json, get_by_id, filter_records, filter_updated_since, paginate
from app.models import AdverseEvent

router = APIRouter(prefix="/adverse-events", tags=["Adverse Events"])


@router.get("", response_model=list[AdverseEvent])
def list_records(
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    updated_since: datetime | None = None, subject_id: str | None = None, serious: str | None = None, severity: str | None = None,
):
    records = load_json("adverse_events.json")
    records = filter_records(records, subject_id=subject_id, serious=serious, severity=severity)
    records = filter_updated_since(records, updated_since)
    response.headers["X-Total-Count"] = str(len(records))
    return paginate(records, offset=offset, limit=limit)


@router.get("/{ae_id}", response_model=AdverseEvent)
def get_record(ae_id: str):
    records = load_json("adverse_events.json")
    record = get_by_id(records, "ae_id", ae_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "AdverseEvent not found"},
        )
    return record
