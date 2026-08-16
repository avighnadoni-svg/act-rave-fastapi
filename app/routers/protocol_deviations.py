# app/routers/protocol_deviations.py

import csv
import io

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.routers.common import (
    fetch_many,
    fetch_one,
    value_to_string,
)


router = APIRouter(
    prefix="/protocol-deviations",
    tags=["Protocol Deviation - CSV"],
)


CSV_COLUMNS = [
    "deviation_id",
    "subject_id",
    "site_id",
    "deviation_type",
    "severity",
    "updated_at",
]


def records_to_csv(records):

    buffer = io.StringIO()

    writer = csv.DictWriter(
        buffer,
        fieldnames=CSV_COLUMNS,
    )

    writer.writeheader()

    for record in records:

        writer.writerow({
            column: value_to_string(
                record.get(column)
            )
            for column in CSV_COLUMNS
        })

    return buffer.getvalue()


@router.get("")
def get_protocol_deviations(
    subject_id: str | None = None,
    site_id: str | None = None,
    severity: str | None = None,
    updated_since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):

    query = """
        SELECT
            deviation_id,
            subject_id,
            site_id,
            deviation_type,
            severity,
            updated_at
        FROM protocol_deviation
        WHERE 1 = 1
    """

    params = []

    if subject_id:
        query += " AND subject_id = %s"
        params.append(subject_id)

    if site_id:
        query += " AND site_id = %s"
        params.append(site_id)

    if severity:
        query += " AND severity = %s"
        params.append(severity)

    if updated_since:
        query += " AND updated_at > %s"
        params.append(updated_since)

    records = fetch_many(
        query,
        params,
        offset,
        limit,
        "deviation_id",
    )

    return Response(
        content=records_to_csv(records),
        media_type="text/csv",
    )


@router.get("/{deviation_id}")
def get_protocol_deviation(
    deviation_id: str,
):

    query = """
        SELECT
            deviation_id,
            subject_id,
            site_id,
            deviation_type,
            severity,
            updated_at
        FROM protocol_deviation
        WHERE deviation_id = %s
    """

    record = fetch_one(
        query,
        (deviation_id,),
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Protocol Deviation "
                f"{deviation_id} not found"
            ),
        )

    return Response(
        content=records_to_csv([record]),
        media_type="text/csv",
    )