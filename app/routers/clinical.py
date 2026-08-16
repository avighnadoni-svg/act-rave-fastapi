# app/routers/clinical.py

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.database import get_connection
from app.models import (
    Study,
    Site,
    Subject,
    Visit,
    AdverseEvent,
    LabResult,
    ProtocolDeviation,
    DataQuery,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=["Clinical Data"]
)


# ============================================================
# COMMON DATABASE FUNCTIONS
# ============================================================

def fetch_many(
    query: str,
    params: list[Any],
    offset: int,
    limit: int,
    order_by: str,
):
    """
    Execute SELECT query returning multiple rows.

    order_by is supplied internally by our code,
    not by the API user.
    """

    final_query = f"""
        {query}

        ORDER BY updated_at, {order_by}
        OFFSET %s
        LIMIT %s
    """

    final_params = [
        *params,
        offset,
        limit,
    ]

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                final_query,
                final_params,
            )

            records = cur.fetchall()

    return records


def fetch_one(
    query: str,
    params: tuple,
):
    """
    Execute SELECT query returning a single row.
    """

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                params,
            )

            record = cur.fetchone()

    return record


# ============================================================
# 1. STUDY
# ============================================================

@router.get(
    "/studies",
    response_model=list[Study],
)
def get_studies(
    phase: str | None = None,
    updated_since: datetime | None = None,
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

    # --------------------------------------------------------
    # Business filters
    # --------------------------------------------------------

    if phase:

        query += """
            AND phase = %s
        """

        params.append(phase)

    # --------------------------------------------------------
    # Incremental filter
    # --------------------------------------------------------

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(updated_since)

    return fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="study_id",
    )


@router.get(
    "/studies/{study_id}",
    response_model=Study,
)
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
        query=query,
        params=(study_id,),
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=f"Study {study_id} not found",
        )

    return record


# ============================================================
# 2. SITE
# ============================================================

@router.get(
    "/sites",
    response_model=list[Site],
)
def get_sites(
    study_id: str | None = None,
    country: str | None = None,
    updated_since: datetime | None = None,
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

        query += """
            AND study_id = %s
        """

        params.append(study_id)

    if country:

        query += """
            AND country = %s
        """

        params.append(country)

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(updated_since)

    return fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="site_id",
    )


@router.get(
    "/sites/{site_id}",
    response_model=Site,
)
def get_site(
    site_id: str,
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
        WHERE site_id = %s
    """

    record = fetch_one(
        query=query,
        params=(site_id,),
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=f"Site {site_id} not found",
        )

    return record


# ============================================================
# 3. SUBJECT
# ============================================================

@router.get(
    "/subjects",
    response_model=list[Subject],
)
def get_subjects(
    study_id: str | None = None,
    site_id: str | None = None,
    status: str | None = None,
    updated_since: datetime | None = None,
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

    query = """
        SELECT
            subject_id,
            study_id,
            site_id,
            gender,
            age,
            status,
            enrollment_date,
            updated_at
        FROM subject
        WHERE 1 = 1
    """

    params = []

    if study_id:

        query += """
            AND study_id = %s
        """

        params.append(study_id)

    if site_id:

        query += """
            AND site_id = %s
        """

        params.append(site_id)

    if status:

        query += """
            AND status = %s
        """

        params.append(status)

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(updated_since)

    return fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="subject_id",
    )


@router.get(
    "/subjects/{subject_id}",
    response_model=Subject,
)
def get_subject(
    subject_id: str,
):

    query = """
        SELECT
            subject_id,
            study_id,
            site_id,
            gender,
            age,
            status,
            enrollment_date,
            updated_at
        FROM subject
        WHERE subject_id = %s
    """

    record = fetch_one(
        query=query,
        params=(subject_id,),
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=f"Subject {subject_id} not found",
        )

    return record


# ============================================================
# 4. VISIT
# ============================================================

@router.get(
    "/visits",
    response_model=list[Visit],
)
def get_visits(
    subject_id: str | None = None,
    updated_since: datetime | None = None,
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

        query += """
            AND subject_id = %s
        """

        params.append(subject_id)

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(updated_since)

    return fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="visit_id",
    )


@router.get(
    "/visits/{visit_id}",
    response_model=Visit,
)
def get_visit(
    visit_id: str,
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
        WHERE visit_id = %s
    """

    record = fetch_one(
        query=query,
        params=(visit_id,),
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=f"Visit {visit_id} not found",
        )

    return record


# ============================================================
# 5. ADVERSE EVENT
# ============================================================

@router.get(
    "/adverse-events",
    response_model=list[AdverseEvent],
)
def get_adverse_events(
    subject_id: str | None = None,
    serious: str | None = None,
    severity: str | None = None,
    updated_since: datetime | None = None,
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

        query += """
            AND subject_id = %s
        """

        params.append(subject_id)

    if serious:

        query += """
            AND serious = %s
        """

        params.append(serious)

    if severity:

        query += """
            AND severity = %s
        """

        params.append(severity)

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(updated_since)

    return fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="ae_id",
    )


@router.get(
    "/adverse-events/{ae_id}",
    response_model=AdverseEvent,
)
def get_adverse_event(
    ae_id: str,
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
        WHERE ae_id = %s
    """

    record = fetch_one(
        query=query,
        params=(ae_id,),
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=f"Adverse Event {ae_id} not found",
        )

    return record


# ============================================================
# 6. LAB RESULT
# ============================================================

@router.get(
    "/lab-results",
    response_model=list[LabResult],
)
def get_lab_results(
    subject_id: str | None = None,
    test: str | None = None,
    updated_since: datetime | None = None,
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

    query = """
        SELECT
            lab_id,
            subject_id,
            test_name,
            result_value,
            normal_low,
            normal_high,
            updated_at
        FROM lab_result
        WHERE 1 = 1
    """

    params = []

    if subject_id:

        query += """
            AND subject_id = %s
        """

        params.append(subject_id)

    if test:

        query += """
            AND test_name = %s
        """

        params.append(test)

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(updated_since)

    return fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="lab_id",
    )


@router.get(
    "/lab-results/{lab_id}",
    response_model=LabResult,
)
def get_lab_result(
    lab_id: str,
):

    query = """
        SELECT
            lab_id,
            subject_id,
            test_name,
            result_value,
            normal_low,
            normal_high,
            updated_at
        FROM lab_result
        WHERE lab_id = %s
    """

    record = fetch_one(
        query=query,
        params=(lab_id,),
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=f"Lab Result {lab_id} not found",
        )

    return record


# ============================================================
# 7. PROTOCOL DEVIATION
# ============================================================

@router.get(
    "/protocol-deviations",
    response_model=list[ProtocolDeviation],
)
def get_protocol_deviations(
    subject_id: str | None = None,
    site_id: str | None = None,
    severity: str | None = None,
    updated_since: datetime | None = None,
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

    query = """
        SELECT
            deviation_id,
            subject_id,
            site_id,
            deviation_type,
            severity,
            updated_at
        FROM protocol_deviation
        WHERE 1 = 1
    """

    params = []

    if subject_id:

        query += """
            AND subject_id = %s
        """

        params.append(subject_id)

    if site_id:

        query += """
            AND site_id = %s
        """

        params.append(site_id)

    if severity:

        query += """
            AND severity = %s
        """

        params.append(severity)

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(updated_since)

    return fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="deviation_id",
    )


@router.get(
    "/protocol-deviations/{deviation_id}",
    response_model=ProtocolDeviation,
)
def get_protocol_deviation(
    deviation_id: str,
):

    query = """
        SELECT
            deviation_id,
            subject_id,
            site_id,
            deviation_type,
            severity,
            updated_at
        FROM protocol_deviation
        WHERE deviation_id = %s
    """

    record = fetch_one(
        query=query,
        params=(deviation_id,),
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=f"Protocol Deviation {deviation_id} not found",
        )

    return record


# ============================================================
# 8. DATA QUERY
# ============================================================

@router.get(
    "/data-queries",
    response_model=list[DataQuery],
)
def get_data_queries(
    subject_id: str | None = None,
    site_id: str | None = None,
    updated_since: datetime | None = None,
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

        query += """
            AND subject_id = %s
        """

        params.append(subject_id)

    if site_id:

        query += """
            AND site_id = %s
        """

        params.append(site_id)

    if updated_since:

        query += """
            AND updated_at > %s
        """

        params.append(updated_since)

    return fetch_many(
        query=query,
        params=params,
        offset=offset,
        limit=limit,
        order_by="query_id",
    )


@router.get(
    "/data-queries/{query_id}",
    response_model=DataQuery,
)
def get_data_query(
    query_id: str,
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
        WHERE query_id = %s
    """

    record = fetch_one(
        query=query,
        params=(query_id,),
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail=f"Data Query {query_id} not found",
        )

    return record