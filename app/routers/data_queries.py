# app/routers/data_queries.py

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
    prefix="/data-queries",
    tags=["Data Queries"],
)


# ============================================================
# XML BUILDER
# ============================================================

def build_data_query_xml(
    records: list[dict],
) -> bytes:
    """
    Build Clinical Data Query XML.

    study_id is included so downstream processing
    can organize ACT data study-wise.
    """

    root = Element(
        "ClinicalDataQueryExtract",
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

    queries_node = SubElement(
        body,
        "Queries",
    )


    # ========================================================
    # RECORDS
    # ========================================================

    for row in records:

        query_node = SubElement(
            queries_node,
            "DataQuery",
            {
                "id": value_to_string(
                    row.get(
                        "query_id"
                    )
                )
            },
        )


        # ----------------------------------------------------
        # CLINICAL CONTEXT
        # ----------------------------------------------------

        clinical_context = SubElement(
            query_node,
            "ClinicalContext",
        )


        SubElement(
            clinical_context,
            "Study",
            {
                "id": value_to_string(
                    row.get(
                        "study_id"
                    )
                )
            },
        )


        SubElement(
            clinical_context,
            "Subject",
            {
                "id": value_to_string(
                    row.get(
                        "subject_id"
                    )
                )
            },
        )


        SubElement(
            clinical_context,
            "Site",
            {
                "id": value_to_string(
                    row.get(
                        "site_id"
                    )
                )
            },
        )


        # ----------------------------------------------------
        # LIFECYCLE
        # ----------------------------------------------------

        lifecycle = SubElement(
            query_node,
            "Lifecycle",
        )


        SubElement(
            lifecycle,
            "OpenedDate",
        ).text = value_to_string(
            row.get(
                "opened_date"
            )
        )


        SubElement(
            lifecycle,
            "ResolvedDate",
        ).text = value_to_string(
            row.get(
                "resolved_date"
            )
        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status = (
            "RESOLVED"
            if row.get("resolved_date")
            else "OPEN"
        )


        SubElement(
            lifecycle,
            "Status",
        ).text = status


        # ----------------------------------------------------
        # AUDIT
        # ----------------------------------------------------

        audit = SubElement(
            query_node,
            "AuditTrail",
        )


        SubElement(
            audit,
            "SourceSystem",
        ).text = "RAVE_MOCK"


        SubElement(
            audit,
            "UpdatedAt",
        ).text = value_to_string(
            row.get(
                "updated_at"
            )
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
def get_data_queries(

    # --------------------------------------------------------
    # STUDY FILTER
    # --------------------------------------------------------

    study_id: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # SUBJECT FILTER
    # --------------------------------------------------------

    subject_id: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # SITE FILTER
    # --------------------------------------------------------

    site_id: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # INCREMENTAL WATERMARK
    # --------------------------------------------------------

    updated_since: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

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
    # DATA QUERY -> SUBJECT -> STUDY
    #
    # DATA_QUERY contains subject_id + site_id.
    # We derive study_id from SUBJECT.
    # ========================================================

    query = """
        SELECT

            dq.query_id,

            dq.subject_id,

            dq.site_id,

            s.study_id AS study_id,

            dq.opened_date,

            dq.resolved_date,

            dq.updated_at

        FROM data_query dq

        INNER JOIN subject s
            ON dq.subject_id = s.subject_id

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
            AND dq.subject_id = %s
        """

        params.append(
            subject_id
        )


    # ========================================================
    # SITE FILTER
    # ========================================================

    if site_id:

        query += """
            AND dq.site_id = %s
        """

        params.append(
            site_id
        )


    # ========================================================
    # INCREMENTAL FILTER
    # ========================================================

    if updated_since:

        query += """
            AND dq.updated_at > %s
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
        order_by="query_id",
    )


    # ========================================================
    # XML RESPONSE
    # ========================================================

    xml_data = build_data_query_xml(
        records
    )


    return Response(
        content=xml_data,
        media_type="application/xml",
    )


# ============================================================
# GET BY ID
# ============================================================

@router.get("/{query_id}")
def get_data_query(
    query_id: str,
):

    query = """
        SELECT

            dq.query_id,

            dq.subject_id,

            dq.site_id,

            s.study_id AS study_id,

            dq.opened_date,

            dq.resolved_date,

            dq.updated_at

        FROM data_query dq

        INNER JOIN subject s
            ON dq.subject_id = s.subject_id

        WHERE dq.query_id = %s
    """


    record = fetch_one(
        query=query,
        params=[
            query_id
        ],
    )


    if not record:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Data query "
                f"{query_id} not found"
            ),
        )


    xml_data = build_data_query_xml(
        [
            record
        ]
    )


    return Response(
        content=xml_data,
        media_type="application/xml",
    )