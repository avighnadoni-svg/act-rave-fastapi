from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel


class SourceRecord(BaseModel):
    updated_at: datetime | None = None


class Study(SourceRecord):
    study_id: str
    study_name: str
    phase: str
    target_subjects: int


class Site(SourceRecord):
    site_id: str
    study_id: str
    country: str
    investigator: str
    target_enrollment: int


class Subject(SourceRecord):
    subject_id: str
    study_id: str
    site_id: str
    sex: Literal["M", "F"]
    age: int
    status: str
    enroll_date: date


class Visit(SourceRecord):
    visit_id: str
    subject_id: str
    visit_name: str
    planned_date: date
    actual_date: date | None = None


class AdverseEvent(SourceRecord):
    ae_id: str
    subject_id: str
    ae_term: str
    severity: str
    serious: Literal["Y", "N"]
    event_date: date
    reported_date: date


class LabResult(SourceRecord):
    lab_id: str
    subject_id: str
    test: str
    value: float
    lower_limit: float
    upper_limit: float


class ProtocolDeviation(SourceRecord):
    deviation_id: str
    subject_id: str
    site_id: str
    deviation_type: str
    severity: str


class DataQuery(SourceRecord):
    query_id: str
    subject_id: str
    site_id: str
    open_date: date
    closed_date: date | None = None
