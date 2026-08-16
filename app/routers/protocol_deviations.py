# app/routers/protocol_deviations.py

import csv
import io

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
    prefix="/protocol-deviations",
    tags=["Protocol Deviations"],
)


# ============================================================
# CSV BUILDER
# ============================================================

def build_protocol_deviation_csv(
    records: list[dict],
) -> str:
    """
    Convert Protocol Deviation records into CSV.

    study_id is included so downstream ingestion
    can organize data study-wise in S3.
    """

    buffer = io.StringIO()


    # ========================================================
    # CSV COLUMNS
    # ========================================================

    fieldnames = [
        "deviation_id",
        "study_id",
        "subject_id",
        "site_id",
        "deviation_type",
        "severity",
        "updated_at",
    ]


    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        lineterminator="\n",
    )


    writer.writeheader()


    # ========================================================
    # RECORDS
    # ========================================================

    for row in records:

        writer.writerow(
            {
                "deviation_id":
                    value_to_string(
                        row.get(
                            "deviation_id"
                        )
                    ),

                "study_id":
                    value_to_string(
                        row.get(
                            "study_id"
                        )
                    ),

                "subject_id":
                    value_to_string(
                        row.get(
                            "subject_id"
                        )
                    ),

                "site_id":
                    value_to_string(
                        row.get(
                            "site_id"
                        )
                    ),

                "deviation_type":
                    value_to_string(
                        row.get(
                            "deviation_type"
                        )
                    ),

                "severity":
                    value_to_string(
                        row.get(
                            "severity"
                        )
                    ),

                "updated_at":
                    value_to_string(
                        row.get(
                            "updated_at"
                        )
                    ),
            }
        )


    return buffer.getvalue()


# ============================================================
# GET COLLECTION
# ============================================================

@router.get("")
def get_protocol_deviations(

    # --------------------------------------------------------
    # STUDY
    # --------------------------------------------------------

    study_id: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # SUBJECT
    # --------------------------------------------------------

    subject_id: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # SITE
    # --------------------------------------------------------

    site_id: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # SEVERITY
    # --------------------------------------------------------

    severity: str | None = Query(
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
    # PROTOCOL DEVIATION -> SUBJECT -> STUDY
    #
    # protocol_deviation already has:
    #
    # subject_id
    # site_id
    #
    # study_id is derived from SUBJECT.
    # ========================================================

    query = """
        SELECT

            pd.deviation_id,

            pd.subject_id,

            pd.site_id,

            s.study_id AS study_id,

            pd.deviation_type,

            pd.severity,

            pd.updated_at

        FROM protocol_deviation pd

        INNER JOIN subject s
            ON pd.subject_id = s.subject_id

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
            AND pd.subject_id = %s
        """

        params.append(
            subject_id
        )


    # ========================================================
    # SITE FILTER
    # ========================================================

    if site_id:

        query += """
            AND pd.site_id = %s
        """

        params.append(
            site_id
        )


    # ========================================================
    # SEVERITY FILTER
    # ========================================================

    if severity:

        query += """
            AND UPPER(pd.severity) = UPPER(%s)
        """

        params.append(
            severity
        )


    # ========================================================
    # INCREMENTAL FILTER
    # ========================================================

    if updated_since:

        query += """
            AND pd.updated_at > %s
        """

        params.append(
            updated_since
        )


    # ========================================================
    # FETCH DATA
    # ========================================================

    records = fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="deviation_id",
    )


    # ========================================================
    # CSV RESPONSE
    # ========================================================

    csv_data = (
        build_protocol_deviation_csv(
            records
        )
    )


    return Response(
        content=csv_data,
        media_type="text/csv",
    )


# ============================================================
# GET BY ID
# ============================================================

@router.get("/{deviation_id}")
def get_protocol_deviation(
    deviation_id: str,
):

    query = """
        SELECT

            pd.deviation_id,

            pd.subject_id,

            pd.site_id,

            s.study_id AS study_id,

            pd.deviation_type,

            pd.severity,

            pd.updated_at

        FROM protocol_deviation pd

        INNER JOIN subject s
            ON pd.subject_id = s.subject_id

        WHERE pd.deviation_id = %s
    """


    record = fetch_one(
        query=query,
        params=[
            deviation_id
        ],
    )


    if not record:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Protocol deviation "
                f"{deviation_id} not found"
            ),
        )


    csv_data = (
        build_protocol_deviation_csv(
            [
                record
            ]
        )
    )


    return Response(
        content=csv_data,
        media_type="text/csv",
    )