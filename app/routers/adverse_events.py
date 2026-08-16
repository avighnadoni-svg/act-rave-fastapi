# app/routers/adverse_events.py

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
    prefix="/adverse-events",
    tags=["Adverse Event - XML"],
)


def add_adverse_event(
    parent,
    record,
):

    ae = ET.SubElement(
        parent,
        "AdverseEvent",
        {
            "id": record["ae_id"]
        },
    )

    # --------------------------------------------------------
    # REFERENCES
    # --------------------------------------------------------

    references = ET.SubElement(
        ae,
        "References",
    )

    ET.SubElement(
        references,
        "Subject",
        {
            "id": record["subject_id"]
        },
    )

    # --------------------------------------------------------
    # CLINICAL EVENT
    # --------------------------------------------------------

    clinical_event = ET.SubElement(
        ae,
        "ClinicalEvent",
    )

    event_details = ET.SubElement(
        clinical_event,
        "EventDetails",
    )

    ET.SubElement(
        event_details,
        "Term",
    ).text = value_to_string(
        record["event_term"]
    )

    classification = ET.SubElement(
        event_details,
        "Classification",
    )

    severity = ET.SubElement(
        classification,
        "Severity",
        {
            "code": value_to_string(
                record["severity"]
            )
        },
    )

    severity.text = value_to_string(
        record["severity"]
    )

    serious_value = (
        record["serious"] == "Y"
    )

    serious = ET.SubElement(
        classification,
        "Seriousness",
        {
            "flag": value_to_string(
                record["serious"]
            )
        },
    )

    serious.text = str(
        serious_value
    ).lower()

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    timeline = ET.SubElement(
        clinical_event,
        "Timeline",
    )

    ET.SubElement(
        timeline,
        "EventDate",
    ).text = value_to_string(
        record["event_date"]
    )

    ET.SubElement(
        timeline,
        "ReportedDate",
    ).text = value_to_string(
        record["reported_date"]
    )

    # --------------------------------------------------------
    # SAFETY CLASSIFICATION
    # --------------------------------------------------------

    safety = ET.SubElement(
        ae,
        "SafetyAssessment",
    )

    priority = "NORMAL"

    if record["serious"] == "Y":
        priority = "HIGH"

    if record["severity"] == "SEVERE":
        priority = "CRITICAL"

    ET.SubElement(
        safety,
        "ProcessingPriority",
    ).text = priority

    ET.SubElement(
        safety,
        "RequiresSafetyReview",
    ).text = (
        "true"
        if record["serious"] == "Y"
        else "false"
    )

    # --------------------------------------------------------
    # AUDIT TRAIL
    # --------------------------------------------------------

    audit = ET.SubElement(
        ae,
        "AuditTrail",
    )

    source = ET.SubElement(
        audit,
        "Source",
        {
            "system": "RAVE_MOCK",
            "domain": "SAFETY",
        },
    )

    source.text = "Clinical Data Capture"

    timestamps = ET.SubElement(
        audit,
        "Timestamps",
    )

    ET.SubElement(
        timestamps,
        "LastUpdated",
    ).text = value_to_string(
        record["updated_at"]
    )


def records_to_xml(records):

    root = ET.Element(
        "AdverseEventBatch",
        {
            "version": "1.0",
            "source": "RAVE_MOCK",
        },
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    header = ET.SubElement(
        root,
        "Header",
    )

    ET.SubElement(
        header,
        "MessageType",
    ).text = "ACT_ADVERSE_EVENT_EXTRACT"

    ET.SubElement(
        header,
        "RecordCount",
    ).text = str(len(records))

    ET.SubElement(
        header,
        "SchemaVersion",
    ).text = "1.0"

    # --------------------------------------------------------
    # BODY
    # --------------------------------------------------------

    body = ET.SubElement(
        root,
        "Body",
    )

    events = ET.SubElement(
        body,
        "AdverseEvents",
    )

    for record in records:
        add_adverse_event(
            events,
            record,
        )

    return ET.tostring(
        root,
        encoding="unicode",
    )


@router.get("")
def get_adverse_events(
    subject_id: str | None = None,
    serious: str | None = None,
    severity: str | None = None,
    updated_since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):

    query = """
        SELECT
            ae_id,
            subject_id,
            event_term,
            severity,
            serious,
            event_date,
            reported_date,
            updated_at
        FROM adverse_event
        WHERE 1 = 1
    """

    params = []

    if subject_id:
        query += " AND subject_id = %s"
        params.append(subject_id)

    if serious:
        query += " AND serious = %s"
        params.append(serious)

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
        "ae_id",
    )

    return Response(
        content=records_to_xml(records),
        media_type="application/xml",
    )


@router.get("/{ae_id}")
def get_adverse_event(ae_id: str):

    query = """
        SELECT
            ae_id,
            subject_id,
            event_term,
            severity,
            serious,
            event_date,
            reported_date,
            updated_at
        FROM adverse_event
        WHERE ae_id = %s
    """

    record = fetch_one(
        query,
        (ae_id,),
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Adverse Event {ae_id} not found",
        )

    return Response(
        content=records_to_xml([record]),
        media_type="application/xml",
    )