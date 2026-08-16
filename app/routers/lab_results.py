# app/routers/lab_results.py

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.routers.common import (
    fetch_many,
    fetch_one,
)


router = APIRouter(
    prefix="/lab-results",
    tags=["Lab Result - JSON"],
)


def get_interpretation(
    value,
    low,
    high,
):

    if value is None:
        return "UNKNOWN"

    if low is not None and value < low:
        return "LOW"

    if high is not None and value > high:
        return "HIGH"

    return "NORMAL"


def transform_lab(record):

    interpretation = get_interpretation(
        record["result_value"],
        record["normal_low"],
        record["normal_high"],
    )

    return {
        "lab_result": {
            "identifier": record["lab_id"],

            "subject": {
                "subject_id": record["subject_id"],
            },

            "test": {
                "name": record["test_name"],

                "result": {
                    "value": record[
                        "result_value"
                    ],

                    "reference_range": {
                        "low": record[
                            "normal_low"
                        ],
                        "high": record[
                            "normal_high"
                        ],
                    },

                    "interpretation": {
                        "code": interpretation,

                        "abnormal": (
                            interpretation
                            != "NORMAL"
                        ),
                    },
                },
            },
        },

        "metadata": {
            "source": {
                "system": "RAVE_MOCK",
                "domain": "LAB",
            },

            "audit": {
                "updated_at": record[
                    "updated_at"
                ],
            },
        },
    }


@router.get("")
def get_lab_results(
    subject_id: str | None = None,
    test: str | None = None,
    updated_since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):

    query = """
        SELECT
            lab_id,
            subject_id,
            test_name,
            result_value,
            normal_low,
            normal_high,
            updated_at
        FROM lab_result
        WHERE 1 = 1
    """

    params = []

    if subject_id:
        query += " AND subject_id = %s"
        params.append(subject_id)

    if test:
        query += " AND test_name = %s"
        params.append(test)

    if updated_since:
        query += " AND updated_at > %s"
        params.append(updated_since)

    records = fetch_many(
        query,
        params,
        offset,
        limit,
        "lab_id",
    )

    return {
        "laboratory_extract": {
            "record_count": len(records),

            "results": [
                transform_lab(record)
                for record in records
            ],
        }
    }


@router.get("/{lab_id}")
def get_lab_result(lab_id: str):

    query = """
        SELECT
            lab_id,
            subject_id,
            test_name,
            result_value,
            normal_low,
            normal_high,
            updated_at
        FROM lab_result
        WHERE lab_id = %s
    """

    record = fetch_one(
        query,
        (lab_id,),
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Lab Result {lab_id} not found",
        )

    return transform_lab(record)