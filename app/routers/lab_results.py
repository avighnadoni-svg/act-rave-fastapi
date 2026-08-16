# app/routers/lab_results.py

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from app.routers.common import (
    fetch_many,
    fetch_one,
    value_to_string,
)


router = APIRouter(
    prefix="/lab-results",
    tags=["Lab Results"],
)


# ============================================================
# LAB INTERPRETATION
# ============================================================

def _calculate_interpretation(
    result_value,
    normal_low,
    normal_high,
) -> tuple[str, bool]:
    """
    Calculate whether a lab result is:

        LOW
        NORMAL
        HIGH
        UNKNOWN

    Returns:

        interpretation_code
        abnormal_flag
    """

    if (
        result_value is None
        or normal_low is None
        or normal_high is None
    ):
        return (
            "UNKNOWN",
            False,
        )

    try:

        value = float(
            result_value
        )

        low = float(
            normal_low
        )

        high = float(
            normal_high
        )

    except (
        TypeError,
        ValueError,
    ):

        return (
            "UNKNOWN",
            False,
        )


    if value < low:

        return (
            "LOW",
            True,
        )


    if value > high:

        return (
            "HIGH",
            True,
        )


    return (
        "NORMAL",
        False,
    )


# ============================================================
# BUILD ONE LAB RESULT
# ============================================================

def _build_lab_result(
    row: dict,
) -> dict:
    """
    Convert one database record into the
    nested Rave Mock JSON structure.
    """

    (
        interpretation_code,
        abnormal,
    ) = _calculate_interpretation(
        result_value=row.get(
            "result_value"
        ),
        normal_low=row.get(
            "normal_low"
        ),
        normal_high=row.get(
            "normal_high"
        ),
    )


    return {

        # ====================================================
        # LAB RESULT
        # ====================================================

        "lab_result": {

            "identifier":
                value_to_string(
                    row.get(
                        "lab_id"
                    )
                ),


            # ================================================
            # STUDY
            #
            # NEW:
            # study_id travels with every lab record.
            # ================================================

            "study": {

                "study_id":
                    value_to_string(
                        row.get(
                            "study_id"
                        )
                    ),
            },


            # ================================================
            # SUBJECT
            # ================================================

            "subject": {

                "subject_id":
                    value_to_string(
                        row.get(
                            "subject_id"
                        )
                    ),
            },


            # ================================================
            # TEST
            # ================================================

            "test": {

                "name":
                    value_to_string(
                        row.get(
                            "test_name"
                        )
                    ),


                "result": {

                    "value":
                        row.get(
                            "result_value"
                        ),


                    # ========================================
                    # REFERENCE RANGE
                    # ========================================

                    "reference_range": {

                        "low":
                            row.get(
                                "normal_low"
                            ),

                        "high":
                            row.get(
                                "normal_high"
                            ),
                    },


                    # ========================================
                    # INTERPRETATION
                    # ========================================

                    "interpretation": {

                        "code":
                            interpretation_code,

                        "abnormal":
                            abnormal,
                    },
                },
            },
        },


        # ====================================================
        # METADATA
        # ====================================================

        "metadata": {

            "source_system":
                "RAVE_MOCK",

            "audit": {

                "updated_at":
                    value_to_string(
                        row.get(
                            "updated_at"
                        )
                    ),
            },
        },
    }


# ============================================================
# BUILD COLLECTION PAYLOAD
# ============================================================

def build_lab_result_payload(
    records: list[dict],
) -> dict:
    """
    Build nested JSON response for
    multiple lab results.
    """

    results = [

        _build_lab_result(
            row
        )

        for row in records
    ]


    return {

        "laboratory_extract": {

            "metadata": {

                "source_system":
                    "RAVE_MOCK",

                "record_count":
                    len(results),
            },


            "results":
                results,
        }
    }


# ============================================================
# GET COLLECTION
# ============================================================

@router.get("")
def get_lab_results(

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
    # LAB TEST FILTER
    # --------------------------------------------------------

    test_name: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # INCREMENTAL FILTER
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
    # LAB RESULT -> SUBJECT -> STUDY
    #
    # lab_result does not need study_id physically stored.
    #
    # We derive it through SUBJECT.
    # ========================================================

    query = """
        SELECT

            lr.lab_id,

            lr.subject_id,

            s.study_id AS study_id,

            lr.test_name,

            lr.result_value,

            lr.normal_low,

            lr.normal_high,

            lr.updated_at

        FROM lab_result lr

        INNER JOIN subject s
            ON lr.subject_id = s.subject_id

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
            AND lr.subject_id = %s
        """

        params.append(
            subject_id
        )


    # ========================================================
    # TEST FILTER
    # ========================================================

    if test_name:

        query += """
            AND UPPER(lr.test_name) = UPPER(%s)
        """

        params.append(
            test_name
        )


    # ========================================================
    # INCREMENTAL FILTER
    # ========================================================

    if updated_since:

        query += """
            AND lr.updated_at > %s
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
        order_by="lab_id",
    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return build_lab_result_payload(
        records
    )


# ============================================================
# GET LAB RESULT BY ID
# ============================================================

@router.get("/{lab_id}")
def get_lab_result(
    lab_id: str,
):

    query = """
        SELECT

            lr.lab_id,

            lr.subject_id,

            s.study_id AS study_id,

            lr.test_name,

            lr.result_value,

            lr.normal_low,

            lr.normal_high,

            lr.updated_at

        FROM lab_result lr

        INNER JOIN subject s
            ON lr.subject_id = s.subject_id

        WHERE lr.lab_id = %s
    """


    record = fetch_one(
        query=query,
        params=[
            lab_id
        ],
    )


    if not record:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Lab result "
                f"{lab_id} not found"
            ),
        )


    return build_lab_result_payload(
        [
            record
        ]
    )