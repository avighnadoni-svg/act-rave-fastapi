# app/routers/visits.py

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
    prefix="/visits",
    tags=["Visits"],
)


# ============================================================
# XML BUILDER
# ============================================================

def build_visit_xml(
    records: list[dict],
) -> bytes:
    """
    Build ACT Visit XML response.

    study_id is derived through SUBJECT and included
    in the XML so downstream ingestion can partition
    data by study.
    """

    root = Element(
        "VisitExtract",
        {
            "version": "1.0",
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
        "SourceSystem",
    ).text = "RAVE_MOCK"

    SubElement(
        header,
        "RecordCount",
    ).text = str(
        len(records)
    )


    # ========================================================
    # BODY
    # ========================================================

    body = SubElement(
        root,
        "Body",
    )

    visits_node = SubElement(
        body,
        "Visits",
    )


    # ========================================================
    # VISIT RECORDS
    # ========================================================

    for row in records:

        visit = SubElement(
            visits_node,
            "Visit",
            {
                "id": value_to_string(
                    row.get("visit_id")
                )
            },
        )


        # ----------------------------------------------------
        # REFERENCES
        # ----------------------------------------------------

        references = SubElement(
            visit,
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
        # SCHEDULE
        # ----------------------------------------------------

        schedule = SubElement(
            visit,
            "Schedule",
        )

        SubElement(
            schedule,
            "VisitName",
        ).text = value_to_string(
            row.get("visit_name")
        )

        dates = SubElement(
            schedule,
            "Dates",
        )

        SubElement(
            dates,
            "PlannedDate",
        ).text = value_to_string(
            row.get("planned_date")
        )

        SubElement(
            dates,
            "ActualDate",
        ).text = value_to_string(
            row.get("actual_date")
        )


        # ----------------------------------------------------
        # AUDIT
        # ----------------------------------------------------

        audit = SubElement(
            visit,
            "Audit",
        )

        SubElement(
            audit,
            "SourceSystem",
        ).text = "RAVE_MOCK"

        SubElement(
            audit,
            "UpdatedAt",
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
def get_visits(

    study_id: str | None = Query(
        default=None
    ),

    subject_id: str | None = Query(
        default=None
    ),

    visit_name: str | None = Query(
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
    # VISIT -> SUBJECT -> STUDY
    #
    # visit does not physically store study_id.
    # We derive it from subject.
    # ========================================================

    query = """
        SELECT
            v.visit_id,
            v.subject_id,

            s.study_id AS study_id,

            v.visit_name,
            v.planned_date,
            v.actual_date,
            v.updated_at

        FROM visit v

        INNER JOIN subject s
            ON v.subject_id = s.subject_id

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
            AND v.subject_id = %s
        """

        params.append(
            subject_id
        )


    # ========================================================
    # VISIT NAME FILTER
    # ========================================================

    if visit_name:

        query += """
            AND UPPER(v.visit_name) = UPPER(%s)
        """

        params.append(
            visit_name
        )


    # ========================================================
    # INCREMENTAL FILTER
    # ========================================================

    if updated_since:

        query += """
            AND v.updated_at > %s
        """

        params.append(
            updated_since
        )


    # ========================================================
    # DATABASE FETCH
    # ========================================================

    records = fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="visit_id",
    )


    # ========================================================
    # XML RESPONSE
    # ========================================================

    xml_data = build_visit_xml(
        records
    )

    return Response(
        content=xml_data,
        media_type="application/xml",
    )


# ============================================================
# GET VISIT BY ID
# ============================================================

@router.get("/{visit_id}")
def get_visit(
    visit_id: str,
):

    query = """
        SELECT
            v.visit_id,
            v.subject_id,

            s.study_id AS study_id,

            v.visit_name,
            v.planned_date,
            v.actual_date,
            v.updated_at

        FROM visit v

        INNER JOIN subject s
            ON v.subject_id = s.subject_id

        WHERE v.visit_id = %s
    """

    record = fetch_one(
        query=query,
        params=[
            visit_id
        ],
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Visit {visit_id} not found"
            ),
        )


    xml_data = build_visit_xml(
        [record]
    )

    return Response(
        content=xml_data,
        media_type="application/xml",
    )