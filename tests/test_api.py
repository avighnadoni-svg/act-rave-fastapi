from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_get_studies():
    response = client.get("/studies")
    assert response.status_code == 200
    assert response.json()[0]["study_id"] == "ONC101"
    assert "updated_at" in response.json()[0]


def test_get_serious_adverse_events():
    response = client.get("/adverse-events?serious=Y")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert all(row["serious"] == "Y" for row in payload)


def test_pagination():
    response = client.get("/sites?offset=0&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.headers["X-Total-Count"] == "5"


def test_incremental_filter():
    response = client.get("/adverse-events?updated_since=2026-02-08T12:00:00Z")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_get_subject_404():
    response = client.get("/subjects/SUB999")
    assert response.status_code == 404
