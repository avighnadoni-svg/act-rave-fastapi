# app/models.py

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# ============================================================
# 1. STUDY
# ============================================================

class Study(BaseModel):

    study_id: str
    study_name: str
    phase: str | None = None
    target_subjects: int | None = None
    updated_at: datetime


# ============================================================
# 2. SITE
# ============================================================

class Site(BaseModel):

    site_id: str
    study_id: str
    country: str | None = None
    investigator: str | None = None
    target_enrollment: int | None = None
    updated_at: datetime


# ============================================================
# 3. SUBJECT
# ============================================================

class Subject(BaseModel):

    subject_id: str
    study_id: str
    site_id: str
    gender: str | None = None
    age: int | None = None
    status: str | None = None
    enrollment_date: date | None = None
    updated_at: datetime


# ============================================================
# 4. VISIT
# ============================================================

class Visit(BaseModel):

    visit_id: str
    subject_id: str
    visit_name: str | None = None
    planned_date: date | None = None
    actual_date: date | None = None
    updated_at: datetime


# ============================================================
# 5. ADVERSE EVENT
# ============================================================

class AdverseEvent(BaseModel):

    ae_id: str
    subject_id: str
    event_term: str | None = None
    severity: str | None = None
    serious: str | None = None
    event_date: date | None = None
    reported_date: date | None = None
    updated_at: datetime


# ============================================================
# 6. LAB RESULT
# ============================================================

class LabResult(BaseModel):

    lab_id: str
    subject_id: str
    test_name: str | None = None
    result_value: Decimal | None = None
    normal_low: Decimal | None = None
    normal_high: Decimal | None = None
    updated_at: datetime


# ============================================================
# 7. PROTOCOL DEVIATION
# ============================================================

class ProtocolDeviation(BaseModel):

    deviation_id: str
    subject_id: str
    site_id: str
    deviation_type: str | None = None
    severity: str | None = None
    updated_at: datetime


# ============================================================
# 8. DATA QUERY
# ============================================================

class DataQuery(BaseModel):

    query_id: str
    subject_id: str
    site_id: str
    opened_date: date | None = None
    resolved_date: date | None = None
    updated_at: datetime