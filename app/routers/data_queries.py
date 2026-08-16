# app/routers/data_queries.py

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
    prefix="/data-queries",
    tags=["Data Query - XML"],
)


def add_query_element(
    parent,
    record,
):

    query_element = ET.SubElement(
        parent,
        "DataQuery",
        {
            "id": record["query_id"]
        },
    )

    clinical_context = ET.SubElement(
        query_element,
        "ClinicalContext",
    )

    ET.SubElement(
        clinical_context,
        "Subject",
        {
            "id": record["subject_id"]
        },
    )

    ET.SubElement(
        clinical_context,
        "Site",
        {
            "id": record["site_id"]
        },
    )

    lifecycle = ET.SubElement(
        query_element,
        "Lifecycle",
    )

    ET.SubElement(
        lifecycle,
        "OpenedDate",
    ).text = value_to_string(
        record["opened_date"]
    )

    ET.SubElement(
        lifecycle,
        "ResolvedDate",
    ).text = value_to_string(
        record["resolved_date"]
    )

    status = (
        "OPEN"
        if record["resolved_date"] is None
        else "RESOLVED"
    )

    ET.SubElement(
        lifecycle,
        "Status",
    ).text = status

    audit = ET.SubElement(
        query_element,
        "AuditTrail",
    )

    source = ET.SubElement(
        audit,
        "Source",
        {
            "system": "RAVE_MOCK"
        },
    )

    source.text = "Clinical Data Management"

    ET.SubElement(
        audit,
        "UpdatedAt",
    ).text = value_to_string(
        record["updated_at"]
    )


def records_to_xml(records):

    root = ET.Element(
        "ClinicalDataQueryExtract",
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
        "RecordCount",
    ).text = str(len(records))

    ET.SubElement(
        header,
        "SourceSystem",
    ).text = "RAVE_MOCK"

    body = ET.SubElement(
        root,
        "Body",
    )

    queries = ET.SubElement(
        body,
        "Queries",
    )

    for record in records:
        add_query_element(
            queries,
            record,
        )

    return ET.tostring(
        root,
        encoding="unicode",
    )


@router.get("")
def get_data_queries(
    subject_id: str | None = None,
    site_id: str | None = None,
    updated_since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):

    query = """
        SELECT
            query_id,
            subject_id,
            site_id,
            opened_date,
            resolved_date,
            updated_at
        FROM data_query
        WHERE 1 = 1
    """

    params = []

    if subject_id:
        query += " AND subject_id = %s"
        params.append(subject_id)

    if site_id:
        query += " AND site_id = %s"
        params.append(site_id)

    if updated_since:
        query += " AND updated_at > %s"
        params.append(updated_since)

    records = fetch_many(
        query,
        params,
        offset,
        limit,
        "query_id",
    )

    return Response(
        content=records_to_xml(records),
        media_type="application/xml",
    )


@router.get("/{query_id}")
def get_data_query(query_id: str):

    query = """
        SELECT
            query_id,
            subject_id,
            site_id,
            opened_date,
            resolved_date,
            updated_at
        FROM data_query
        WHERE query_id = %s
    """

    record = fetch_one(
        query,
        (query_id,),
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Data Query {query_id} not found",
        )

    return Response(
        content=records_to_xml([record]),
        media_type="application/xml",
    )