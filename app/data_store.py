import json
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_by_id(records: list[dict[str, Any]], key: str, value: str):
    return next((record for record in records if record.get(key) == value), None)


def filter_records(records: list[dict[str, Any]], **filters):
    result = records
    for key, value in filters.items():
        if value is not None:
            result = [record for record in result if record.get(key) == value]
    return result


def filter_updated_since(records: list[dict[str, Any]], updated_since: datetime | None):
    if updated_since is None:
        return records

    result = []
    for record in records:
        value = record.get("updated_at")
        if not value:
            continue
        record_dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        compare_dt = updated_since
        if compare_dt.tzinfo is None:
            compare_dt = compare_dt.replace(tzinfo=record_dt.tzinfo)
        if record_dt >= compare_dt:
            result.append(record)
    return result


def paginate(records: list[dict[str, Any]], offset: int = 0, limit: int = 100):
    return records[offset : offset + limit]
