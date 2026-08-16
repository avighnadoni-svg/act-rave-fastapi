# app/routers/subjects.py

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.routers.common import (
    fetch_many,
    fetch_one,
)


router = APIRouter(
    prefix="/subjects",
    tags=["Subject - JSON"],
)


def transform_subject(record):

    return {
        "subject": {
            "identifier": record["subject_id"],

            "trial_context": {
                "study": {
                    "study_id": record["study_id"],
                },
                "site": {
                    "site_id": record["site_id"],
                },
            },

            "demographics": {
                "gender": record["gender"],
                "age": record["age"],
            },

            "clinical_status": {
                "status": record["status"],
            },

            "enrollment": {
                "date": record["enrollment_date"],
            },
        },

        "audit": {
            "source": {
                "system": "RAVE_MOCK",
                "module": "SUBJECT",
            },
            "timestamps": {
                "updated_at": record["updated_at"],
            },
        },
    }


@router.get("")
def get_subjects(
    study_id: str | None = None,
    site_id: str | None = None,
    status: str | None = None,
    updated_since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):

    query = """
        SELECT
            subject_id,
            study_id,
            site_id,
            gender,
            age,
            status,
            enrollment_date,
            updated_at
        FROM subject
        WHERE 1 = 1
    """

    params = []

    if study_id:
        query += " AND study_id = %s"
        params.append(study_id)

    if site_id:
        query += " AND site_id = %s"
        params.append(site_id)

    if status:
        query += " AND status = %s"
        params.append(status)

    if updated_since:
        query += " AND updated_at > %s"
        params.append(updated_since)

    records = fetch_many(
        query,
        params,
        offset,
        limit,
        "subject_id",
    )

    return {
        "response": {
            "entity": "subject",
            "record_count": len(records),

            "subjects": [
                transform_subject(record)
                for record in records
            ],
        }
    }


@router.get("/{subject_id}")
def get_subject(subject_id: str):

    query = """
        SELECT
            subject_id,
            study_id,
            site_id,
            gender,
            age,
            status,
            enrollment_date,
            updated_at
        FROM subject
        WHERE subject_id = %s
    """

    record = fetch_one(
        query,
        (subject_id,),
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Subject {subject_id} not found",
        )

    return transform_subject(record)