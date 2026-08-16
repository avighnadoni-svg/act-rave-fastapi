# app/routers/sites.py

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
    prefix="/sites",
    tags=["Site - CSV"],
)


CSV_COLUMNS = [
    "site_id",
    "study_id",
    "country",
    "investigator",
    "target_enrollment",
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
def get_sites(
    study_id: str | None = None,
    country: str | None = None,
    updated_since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):

    query = """
        SELECT
            site_id,
            study_id,
            country,
            investigator,
            target_enrollment,
            updated_at
        FROM site
        WHERE 1 = 1
    """

    params = []

    if study_id:
        query += " AND study_id = %s"
        params.append(study_id)

    if country:
        query += " AND country = %s"
        params.append(country)

    if updated_since:
        query += " AND updated_at > %s"
        params.append(updated_since)

    records = fetch_many(
        query,
        params,
        offset,
        limit,
        "site_id",
    )

    return Response(
        content=records_to_csv(records),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                'inline; filename="sites.csv"'
        },
    )


@router.get("/{site_id}")
def get_site(site_id: str):

    query = """
        SELECT
            site_id,
            study_id,
            country,
            investigator,
            target_enrollment,
            updated_at
        FROM site
        WHERE site_id = %s
    """

    record = fetch_one(
        query,
        (site_id,),
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Site {site_id} not found",
        )

    return Response(
        content=records_to_csv([record]),
        media_type="text/csv",
    )