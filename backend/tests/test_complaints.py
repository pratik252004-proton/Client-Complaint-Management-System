import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_complaints.db")
os.environ.setdefault("GROQ_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db

engine = create_engine(
    "sqlite:///./test_complaints.db", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_complaints.db"):
        os.remove("test_complaints.db")


client = TestClient(app)


def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_and_get_complaint():
    payload = {
        "complaint_source": "Email",
        "customer_name": "Acme Pharma Distributors",
        "product_name": "Amoxicillin Trihydrate",
        "product_strength": "500mg Capsules",
        "batch_lot_number": "AMX-2026-0417",
        "complaint_type": "Product Quality",
        "detailed_description": "Discoloration reported in a subset of capsules.",
        "initial_severity": "Major",
        "priority": "High",
    }
    res = client.post("/api/complaints", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["customer_name"] == "Acme Pharma Distributors"
    assert body["status"] == "Pending Triage"

    complaint_id = body["id"]
    res = client.get(f"/api/complaints/{complaint_id}")
    assert res.status_code == 200
    assert res.json()["batch_lot_number"] == "AMX-2026-0417"


def test_list_and_filter_complaints():
    res = client.get("/api/complaints", params={"search": "Acme"})
    assert res.status_code == 200
    results = res.json()
    assert len(results) >= 1
    assert any("Acme" in (r["customer_name"] or "") for r in results)


def test_update_complaint_status():
    res = client.post(
        "/api/complaints",
        json={"customer_name": "Test Co", "product_name": "Test Product"},
    )
    complaint_id = res.json()["id"]

    res = client.patch(f"/api/complaints/{complaint_id}", json={"status": "Under Review"})
    assert res.status_code == 200
    assert res.json()["status"] == "Under Review"


def test_get_nonexistent_complaint_returns_404():
    res = client.get("/api/complaints/does-not-exist")
    assert res.status_code == 404


def test_delete_complaint():
    res = client.post("/api/complaints", json={"customer_name": "Delete Me"})
    complaint_id = res.json()["id"]

    res = client.delete(f"/api/complaints/{complaint_id}")
    assert res.status_code == 204

    res = client.get(f"/api/complaints/{complaint_id}")
    assert res.status_code == 404
