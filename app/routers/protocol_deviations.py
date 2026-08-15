from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Response
from app.data_store import load_json, get_by_id, filter_records, filter_updated_since, paginate
from app.models import ProtocolDeviation

router = APIRouter(prefix="/protocol-deviations", tags=["Protocol Deviations"])


@router.get("", response_model=list[ProtocolDeviation])
def list_records(
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    updated_since: datetime | None = None, subject_id: str | None = None, site_id: str | None = None, severity: str | None = None,
):
    records = load_json("protocol_deviations.json")
    records = filter_records(records, subject_id=subject_id, site_id=site_id, severity=severity)
    records = filter_updated_since(records, updated_since)
    response.headers["X-Total-Count"] = str(len(records))
    return paginate(records, offset=offset, limit=limit)


@router.get("/{deviation_id}", response_model=ProtocolDeviation)
def get_record(deviation_id: str):
    records = load_json("protocol_deviations.json")
    record = get_by_id(records, "deviation_id", deviation_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": "ProtocolDeviation not found"},
        )
    return record
