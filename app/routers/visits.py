# app/routers/visits.py

from datetime import datetime
import xml.etree.ElementTree as ET

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.routers.common import (
    fetch_many,
    fetch_one,
    value_to_string,
)


router = APIRouter(
    prefix="/visits",
    tags=["Visit - XML"],
)


def create_visit_element(parent, record):

    visit = ET.SubElement(
        parent,
        "Visit",
        {
            "id": record["visit_id"]
        },
    )

    references = ET.SubElement(
        visit,
        "References",
    )

    ET.SubElement(
        references,
        "Subject",
        {
            "id": record["subject_id"]
        },
    )

    schedule = ET.SubElement(
        visit,
        "Schedule",
    )

    ET.SubElement(
        schedule,
        "VisitName",
    ).text = value_to_string(
        record["visit_name"]
    )

    dates = ET.SubElement(
        schedule,
        "Dates",
    )

    ET.SubElement(
        dates,
        "PlannedDate",
    ).text = value_to_string(
        record["planned_date"]
    )

    ET.SubElement(
        dates,
        "ActualDate",
    ).text = value_to_string(
        record["actual_date"]
    )

    audit = ET.SubElement(
        visit,
        "Audit",
    )

    ET.SubElement(
        audit,
        "SourceSystem",
    ).text = "RAVE_MOCK"

    ET.SubElement(
        audit,
        "UpdatedAt",
    ).text = value_to_string(
        record["updated_at"]
    )


def records_to_xml(records):

    root = ET.Element(
        "VisitExtract",
        {
            "version": "1.0"
        },
    )

    header = ET.SubElement(
        root,
        "Header",
    )

    ET.SubElement(
        header,
        "MessageType",
    ).text = "VISIT_EXTRACT"

    ET.SubElement(
        header,
        "RecordCount",
    ).text = str(len(records))

    body = ET.SubElement(
        root,
        "Body",
    )

    visits = ET.SubElement(
        body,
        "Visits",
    )

    for record in records:
        create_visit_element(
            visits,
            record,
        )

    return ET.tostring(
        root,
        encoding="unicode",
        xml_declaration=False,
    )


@router.get("")
def get_visits(
    subject_id: str | None = None,
    updated_since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):

    query = """
        SELECT
            visit_id,
            subject_id,
            visit_name,
            planned_date,
            actual_date,
            updated_at
        FROM visit
        WHERE 1 = 1
    """

    params = []

    if subject_id:
        query += " AND subject_id = %s"
        params.append(subject_id)

    if updated_since:
        query += " AND updated_at > %s"
        params.append(updated_since)

    records = fetch_many(
        query,
        params,
        offset,
        limit,
        "visit_id",
    )

    return Response(
        content=records_to_xml(records),
        media_type="application/xml",
    )


@router.get("/{visit_id}")
def get_visit(visit_id: str):

    query = """
        SELECT
            visit_id,
            subject_id,
            visit_name,
            planned_date,
            actual_date,
            updated_at
        FROM visit
        WHERE visit_id = %s
    """

    record = fetch_one(
        query,
        (visit_id,),
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Visit {visit_id} not found",
        )

    return Response(
        content=records_to_xml([record]),
        media_type="application/xml",
    )