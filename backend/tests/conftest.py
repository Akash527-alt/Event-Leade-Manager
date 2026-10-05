import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    # In-memory SQLite shared across threads, fresh for every test.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def make_lead(client):
    def _make(**overrides):
        payload = {
            "name": "Asha Rao",
            "company": "Acme Corp",
            "email": "asha@acme.com",
            "event": "SaaStr 2026",
            "notes": "Interested in analytics. Wants a demo next week.",
            "status": "not_contacted",
        }
        payload.update(overrides)
        response = client.post("/api/leads", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
