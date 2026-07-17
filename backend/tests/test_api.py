from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def register(client: TestClient, username: str = "alice") -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "correct-horse-123"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def create_entry(client: TestClient, headers: dict[str, str], text: str = "A calm walk") -> int:
    response = client.post(
        "/api/journal",
        headers=headers,
        json={"ambience": "forest", "text": text},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_authentication_is_required(client: TestClient):
    assert client.get("/api/journal").status_code == 401
    assert client.get("/api/journal/insights").status_code == 401


def test_registration_login_and_duplicate_username(client: TestClient):
    register(client)
    duplicate = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "another-password"},
    )
    assert duplicate.status_code == 409

    login = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "correct-horse-123"},
    )
    assert login.status_code == 200
    assert login.json()["tokenType"] == "bearer"


@pytest.mark.parametrize(
    "payload",
    [
        {"ambience": "forest", "text": ""},
        {"ambience": "city", "text": "Valid text"},
        {"ambience": "forest", "text": "x" * 10_001},
        {"ambience": "forest", "text": "Valid", "userId": "bob"},
    ],
)
def test_invalid_journal_payloads_are_rejected(client: TestClient, payload: dict):
    headers = register(client)
    assert client.post("/api/journal", headers=headers, json=payload).status_code == 422


def test_users_can_only_access_their_own_entries(client: TestClient):
    alice_headers = register(client, "alice")
    alice_entry = create_entry(client, alice_headers, "Alice private journal")
    bob_headers = register(client, "bob")

    bob_entries = client.get("/api/journal", headers=bob_headers)
    assert bob_entries.status_code == 200
    assert bob_entries.json() == []

    analysis = client.post(
        "/api/journal/analyze",
        headers=bob_headers,
        json={"entryId": alice_entry},
    )
    assert analysis.status_code == 404


def test_analysis_uses_stored_text_and_is_cached(client: TestClient, monkeypatch):
    headers = register(client)
    entry_id = create_entry(client, headers, "Text stored by the server")
    received: list[str] = []

    def fake_analysis(text: str):
        received.append(text)
        return {
            "emotion": "calm",
            "keywords": ["forest", "quiet"],
            "summary": "A calm reflection.",
        }

    monkeypatch.setattr("app.main.analyze_text", fake_analysis)
    first = client.post(
        "/api/journal/analyze",
        headers=headers,
        json={"entryId": entry_id},
    )
    second = client.post(
        "/api/journal/analyze",
        headers=headers,
        json={"entryId": entry_id},
    )

    assert first.status_code == second.status_code == 200
    assert first.json()["emotion"] == "calm"
    assert received == ["Text stored by the server"]


def test_insights_are_scoped_to_authenticated_user(client: TestClient, monkeypatch):
    headers = register(client)
    entry_id = create_entry(client, headers)
    monkeypatch.setattr(
        "app.main.analyze_text",
        lambda _text: {
            "emotion": "joyful",
            "keywords": ["trees", "sunlight"],
            "summary": "A joyful reflection.",
        },
    )
    assert client.post(
        "/api/journal/analyze",
        headers=headers,
        json={"entryId": entry_id},
    ).status_code == 200

    insights = client.get("/api/journal/insights", headers=headers)
    assert insights.status_code == 200
    assert insights.json() == {
        "totalEntries": 1,
        "topEmotion": "joyful",
        "mostUsedAmbience": "forest",
        "recentKeywords": ["trees", "sunlight"],
    }
