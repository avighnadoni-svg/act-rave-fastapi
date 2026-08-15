from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from app.data_store import load_json, get_by_id, filter_records, filter_updated_since, paginate
from app.models import LabResult

router = APIRouter(prefix="/lab-results", tags=["Lab Results"])


@router.get("", response_model=list[LabResult])
def list_records(
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    updated_since: datetime | None = None, subject_id: str | None = None, test: str | None = None,
):
    records = load_json("lab_results.json")
    records = filter_records(records, subject_id=subject_id, test=test)
    records = filter_updated_since(records, updated_since)
    response.headers["X-Total-Count"] = str(len(records))
    return paginate(records, offset=offset, limit=limit)


@router.get("/{lab_id}", response_model=LabResult)
def get_record(lab_id: str):
    records = load_json("lab_results.json")
    record = get_by_id(records, "lab_id", lab_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "LabResult not found"},
        )
    return record
