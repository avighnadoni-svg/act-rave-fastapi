from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from app.data_store import load_json, get_by_id, filter_records, filter_updated_since, paginate
from app.models import Study

router = APIRouter(prefix="/studies", tags=["Studies"])


@router.get("", response_model=list[Study])
def list_records(
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    updated_since: datetime | None = None,
):
    records = load_json("studies.json")
    records = filter_updated_since(records, updated_since)
    response.headers["X-Total-Count"] = str(len(records))
    return paginate(records, offset=offset, limit=limit)


@router.get("/{study_id}", response_model=Study)
def get_record(study_id: str):
    records = load_json("studies.json")
    record = get_by_id(records, "study_id", study_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "Study not found"},
        )
    return record
