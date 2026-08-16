# app/routers/studies.py

from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from app.routers.common import (
    fetch_many,
    fetch_one,
)


router = APIRouter(
    prefix="/studies",
    tags=["Study - JSON"],
)


# ============================================================
# TRANSFORM STUDY
# ============================================================

def transform_study(
    record: dict,
) -> dict:
    """
    Convert database study record into
    nested RAVE Mock JSON.
    """

    return {

        "study": {

            "identifier":
                record["study_id"],

            "details": {

                "name":
                    record["study_name"],

                "phase":
                    record["phase"],
            },

            "enrollment": {

                "target_subjects":
                    record["target_subjects"],
            },
        },


        "audit": {

            "source_system":
                "RAVE_MOCK",

            "last_updated":
                record["updated_at"],
        },
    }


# ============================================================
# GET STUDIES
# ============================================================

@router.get("")
def get_studies(

    # --------------------------------------------------------
    # STUDY FILTER
    #
    # Important for multi-study ACT ingestion.
    #
    # Example:
    #
    # /studies?study_id=ONC101
    # --------------------------------------------------------

    study_id: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # PHASE FILTER
    # --------------------------------------------------------

    phase: str | None = Query(
        default=None
    ),


    # --------------------------------------------------------
    # INCREMENTAL WATERMARK
    # --------------------------------------------------------

    updated_since: datetime | None = Query(
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
    # BASE QUERY
    # ========================================================

    query = """
        SELECT

            study_id,

            study_name,

            phase,

            target_subjects,

            updated_at

        FROM study

        WHERE 1 = 1
    """


    params = []


    # ========================================================
    # STUDY FILTER
    # ========================================================

    if study_id:

        query += """
            AND study_id = %s
        """

        params.append(
            study_id
        )


    # ========================================================
    # PHASE FILTER
    # ========================================================

    if phase:

        query += """
            AND UPPER(phase) = UPPER(%s)
        """

        params.append(
            phase
        )


    # ========================================================
    # INCREMENTAL FILTER
    # ========================================================

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(
            updated_since
        )


    # ========================================================
    # FETCH
    # ========================================================

    records = fetch_many(

        query=
            query,

        params=
            params,

        offset=
            offset,

        limit=
            limit,

        order_by=
            "study_id",
    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "metadata": {

            "entity":
                "study",

            "format":
                "JSON",

            "record_count":
                len(records),

            "offset":
                offset,

            "limit":
                limit,
        },


        "data": [

            transform_study(
                record
            )

            for record in records
        ],
    }


# ============================================================
# GET STUDY BY ID
# ============================================================

@router.get("/{study_id}")
def get_study(
    study_id: str,
):

    query = """
        SELECT

            study_id,

            study_name,

            phase,

            target_subjects,

            updated_at

        FROM study

        WHERE study_id = %s
    """


    record = fetch_one(

        query=
            query,

        params=[
            study_id
        ],
    )


    if not record:

        raise HTTPException(

            status_code=
                404,

            detail=(
                f"Study "
                f"{study_id} "
                f"not found"
            ),
        )


    return transform_study(
        record
    )