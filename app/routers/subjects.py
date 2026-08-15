from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from app.data_store import load_json, get_by_id, filter_records, filter_updated_since, paginate
from app.models import Subject

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("", response_model=list[Subject])
def list_records(
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    updated_since: datetime | None = None, study_id: str | None = None, site_id: str | None = None, status: str | None = None,
):
    records = load_json("subjects.json")
    records = filter_records(records, study_id=study_id, site_id=site_id, status=status)
    records = filter_updated_since(records, updated_since)
    response.headers["X-Total-Count"] = str(len(records))
    return paginate(records, offset=offset, limit=limit)


@router.get("/{subject_id}", response_model=Subject)
def get_record(subject_id: str):
    records = load_json("subjects.json")
    record = get_by_id(records, "subject_id", subject_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Subject not found"},
        )
    return record
