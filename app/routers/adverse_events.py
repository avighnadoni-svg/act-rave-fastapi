# app/routers/adverse_events.py

from xml.etree.ElementTree import (
    Element,
    SubElement,
    tostring,
)

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
)

from app.routers.common import (
    fetch_many,
    fetch_one,
    value_to_string,
)


router = APIRouter(
    prefix="/adverse-events",
    tags=["Adverse Events"],
)


# ============================================================
# XML BUILDER
# ============================================================

def build_adverse_event_xml(
    records: list[dict],
) -> bytes:
    """
    Convert adverse-event database rows into
    complex ACT XML response.
    """

    root = Element(
        "AdverseEventBatch",
        {
            "version": "1.0",
            "source": "RAVE_MOCK",
        },
    )

    # ========================================================
    # HEADER
    # ========================================================

    header = SubElement(
        root,
        "Header",
    )

    SubElement(
        header,
        "MessageType",
    ).text = "ACT_ADVERSE_EVENT_EXTRACT"

    SubElement(
        header,
        "RecordCount",
    ).text = str(
        len(records)
    )

    SubElement(
        header,
        "SchemaVersion",
    ).text = "1.0"


    # ========================================================
    # BODY
    # ========================================================

    body = SubElement(
        root,
        "Body",
    )

    events_node = SubElement(
        body,
        "AdverseEvents",
    )


    # ========================================================
    # RECORDS
    # ========================================================

    for row in records:

        event = SubElement(
            events_node,
            "AdverseEvent",
            {
                "id": value_to_string(
                    row.get("ae_id")
                )
            },
        )


        # ----------------------------------------------------
        # REFERENCES
        # ----------------------------------------------------

        references = SubElement(
            event,
            "References",
        )

        SubElement(
            references,
            "Study",
            {
                "id": value_to_string(
                    row.get("study_id")
                )
            },
        )

        SubElement(
            references,
            "Subject",
            {
                "id": value_to_string(
                    row.get("subject_id")
                )
            },
        )


        # ----------------------------------------------------
        # CLINICAL EVENT
        # ----------------------------------------------------

        clinical_event = SubElement(
            event,
            "ClinicalEvent",
        )

        event_details = SubElement(
            clinical_event,
            "EventDetails",
        )

        SubElement(
            event_details,
            "Term",
        ).text = value_to_string(
            row.get("event_term")
        )


        # ----------------------------------------------------
        # CLASSIFICATION
        # ----------------------------------------------------

        classification = SubElement(
            event_details,
            "Classification",
        )

        severity = value_to_string(
            row.get("severity")
        ).upper()

        severity_element = SubElement(
            classification,
            "Severity",
            {
                "code": severity
            },
        )

        severity_element.text = (
            severity
        )


        serious = value_to_string(
            row.get("serious")
        ).upper()

        seriousness_element = SubElement(
            classification,
            "Seriousness",
            {
                "flag": serious
            },
        )

        seriousness_element.text = (
            "true"
            if serious == "Y"
            else "false"
        )


        # ----------------------------------------------------
        # TIMELINE
        # ----------------------------------------------------

        timeline = SubElement(
            clinical_event,
            "Timeline",
        )

        SubElement(
            timeline,
            "EventDate",
        ).text = value_to_string(
            row.get("event_date")
        )

        SubElement(
            timeline,
            "ReportedDate",
        ).text = value_to_string(
            row.get("reported_date")
        )


        # ----------------------------------------------------
        # SAFETY ASSESSMENT
        # ----------------------------------------------------

        safety = SubElement(
            event,
            "SafetyAssessment",
        )

        if severity == "SEVERE":

            priority = "CRITICAL"

        elif serious == "Y":

            priority = "HIGH"

        else:

            priority = "NORMAL"


        SubElement(
            safety,
            "ProcessingPriority",
        ).text = priority

        SubElement(
            safety,
            "RequiresSafetyReview",
        ).text = (
            "true"
            if serious == "Y"
            else "false"
        )


        # ----------------------------------------------------
        # AUDIT
        # ----------------------------------------------------

        audit_trail = SubElement(
            event,
            "AuditTrail",
        )

        source = SubElement(
            audit_trail,
            "Source",
            {
                "system": "RAVE_MOCK",
                "domain": "SAFETY",
            },
        )

        source.text = (
            "Clinical Data Capture"
        )

        timestamps = SubElement(
            audit_trail,
            "Timestamps",
        )

        SubElement(
            timestamps,
            "LastUpdated",
        ).text = value_to_string(
            row.get("updated_at")
        )


    return tostring(
        root,
        encoding="utf-8",
        xml_declaration=False,
    )


# ============================================================
# GET COLLECTION
# ============================================================

@router.get("")
def get_adverse_events(

    # --------------------------------------------------------
    # NEW: STUDY FILTER
    # --------------------------------------------------------

    study_id: str | None = Query(
        default=None
    ),

    subject_id: str | None = Query(
        default=None
    ),

    severity: str | None = Query(
        default=None
    ),

    serious: str | None = Query(
        default=None
    ),

    updated_since: str | None = Query(
        default=None
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
):

    # ========================================================
    # IMPORTANT
    #
    # adverse_event itself does not contain study_id.
    #
    # We derive it from SUBJECT.
    # ========================================================

    query = """
        SELECT
            ae.ae_id,
            ae.subject_id,

            s.study_id AS study_id,

            ae.event_term,
            ae.severity,
            ae.serious,
            ae.event_date,
            ae.reported_date,
            ae.updated_at

        FROM adverse_event ae

        INNER JOIN subject s
            ON ae.subject_id = s.subject_id

        WHERE 1 = 1
    """

    params = []


    # ========================================================
    # STUDY FILTER
    # ========================================================

    if study_id:

        query += """
            AND s.study_id = %s
        """

        params.append(
            study_id
        )


    # ========================================================
    # SUBJECT FILTER
    # ========================================================

    if subject_id:

        query += """
            AND ae.subject_id = %s
        """

        params.append(
            subject_id
        )


    # ========================================================
    # SEVERITY FILTER
    # ========================================================

    if severity:

        query += """
            AND UPPER(ae.severity) = UPPER(%s)
        """

        params.append(
            severity
        )


    # ========================================================
    # SERIOUS FILTER
    # ========================================================

    if serious:

        query += """
            AND UPPER(ae.serious) = UPPER(%s)
        """

        params.append(
            serious
        )


    # ========================================================
    # INCREMENTAL FILTER
    # ========================================================

    if updated_since:

        query += """
            AND ae.updated_at > %s
        """

        params.append(
            updated_since
        )


    # ========================================================
    # FETCH
    # ========================================================

    records = fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="ae_id",
    )


    # ========================================================
    # XML RESPONSE
    # ========================================================

    xml_data = (
        build_adverse_event_xml(
            records
        )
    )

    return Response(
        content=xml_data,
        media_type="application/xml",
    )


# ============================================================
# GET BY ID
# ============================================================

@router.get("/{ae_id}")
def get_adverse_event(
    ae_id: str,
):

    query = """
        SELECT
            ae.ae_id,
            ae.subject_id,

            s.study_id AS study_id,

            ae.event_term,
            ae.severity,
            ae.serious,
            ae.event_date,
            ae.reported_date,
            ae.updated_at

        FROM adverse_event ae

        INNER JOIN subject s
            ON ae.subject_id = s.subject_id

        WHERE ae.ae_id = %s
    """

    record = fetch_one(
        query=query,
        params=[ae_id],
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Adverse event "
                f"{ae_id} not found"
            ),
        )


    xml_data = (
        build_adverse_event_xml(
            [record]
        )
    )

    return Response(
        content=xml_data,
        media_type="application/xml",
    )