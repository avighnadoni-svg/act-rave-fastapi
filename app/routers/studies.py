# app/routers/studies.py

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.routers.common import (
    fetch_many,
    fetch_one,
)


router = APIRouter(
    prefix="/studies",
    tags=["Study - JSON"],
)


def transform_study(record):

    return {
        "study": {
            "identifier": record["study_id"],
            "details": {
                "name": record["study_name"],
                "phase": record["phase"],
            },
            "enrollment": {
                "target_subjects": record["target_subjects"],
            },
        },
        "audit": {
            "source_system": "RAVE_MOCK",
            "last_updated": record["updated_at"],
        },
    }


@router.get("")
def get_studies(
    phase: str | None = None,
    updated_since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):

    query = """
        SELECT
            study_id,
            study_name,
            phase,
            target_subjects,
            updated_at
        FROM study
        WHERE 1 = 1
    """

    params = []

    if phase:
        query += " AND phase = %s"
        params.append(phase)

    if updated_since:
        query += " AND updated_at > %s"
        params.append(updated_since)

    records = fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="study_id",
    )

    return {
        "metadata": {
            "entity": "study",
            "format": "JSON",
            "record_count": len(records),
            "offset": offset,
            "limit": limit,
        },
        "data": [
            transform_study(record)
            for record in records
        ],
    }


@router.get("/{study_id}")
def get_study(study_id: str):

    query = """
        SELECT
            study_id,
            study_name,
            phase,
            target_subjects,
            updated_at
        FROM study
        WHERE study_id = %s
    """

    record = fetch_one(
        query,
        (study_id,),
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Study {study_id} not found",
        )

    return transform_study(record)