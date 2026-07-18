from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.security import JWT_ALGORITHM, JWT_SECRET

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


def test_health_endpoint(client: TestClient):
    assert client.get("/").json() == {"message": "Journal API is running"}


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "password": "valid-password"},
        {"username": "a" * 65, "password": "valid-password"},
        {"username": "not allowed", "password": "valid-password"},
        {"username": "alice!", "password": "valid-password"},
        {"username": "alice", "password": "short"},
        {"username": "alice", "password": "x" * 129},
        {"username": "alice", "password": "valid-password", "role": "admin"},
    ],
)
def test_invalid_registration_payloads_are_rejected(client: TestClient, payload: dict):
    assert client.post("/api/auth/register", json=payload).status_code == 422


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


@pytest.mark.parametrize("password", ["wrong-password", "", "CORRECT-HORSE-123"])
def test_login_rejects_invalid_passwords(client: TestClient, password: str):
    register(client)
    response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": password},
    )
    assert response.status_code in {401, 422}


def test_invalid_expired_and_unknown_user_tokens_are_rejected(client: TestClient):
    register(client)
    expired = jwt.encode(
        {
            "sub": "alice",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    unknown = jwt.encode(
        {
            "sub": "deleted-user",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    for token in ["not-a-jwt", expired, unknown]:
        response = client.get(
            "/api/journal",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "payload",
    [
        {"ambience": "forest", "text": ""},
        {"ambience": "forest", "text": "   \n\t"},
        {"ambience": "city", "text": "Valid text"},
        {"ambience": "forest", "text": "x" * 10_001},
        {"ambience": "forest", "text": "Valid", "unexpected": True},
    ],
)
def test_invalid_journal_payloads_are_rejected(client: TestClient, payload: dict):
    headers = register(client)
    assert client.post("/api/journal", headers=headers, json=payload).status_code == 422


def test_journal_accepts_boundary_length_and_returns_newest_first(client: TestClient):
    headers = register(client)
    first_id = create_entry(client, headers, "first")
    boundary = client.post(
        "/api/journal",
        headers=headers,
        json={"ambience": "mountain", "text": "x" * 10_000},
    )

    assert boundary.status_code == 201
    entries = client.get("/api/journal", headers=headers).json()
    assert [entry["id"] for entry in entries] == [boundary.json()["id"], first_id]
    assert len(entries[0]["text"]) == 10_000


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

    def fake_analysis(text: str, ambience: str | None = None):
        received.append(text)
        assert ambience == "forest"
        return {
            "emotion": "calm",
            "keywords": ["forest", "quiet", "reflection"],
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


def test_assignment_compatible_text_analysis(client: TestClient, monkeypatch):
    headers = register(client)
    received: list[tuple[str, str | None]] = []

    def fake_analysis(text: str, ambience: str | None = None):
        received.append((text, ambience))
        return {
            "emotion": "reflective",
            "keywords": ["rain", "nature", "peace"],
            "summary": "The user describes a reflective and peaceful nature experience.",
        }

    monkeypatch.setattr("app.main.analyze_text", fake_analysis)
    response = client.post(
        "/api/journal/analyze",
        headers=headers,
        json={"text": "I felt peaceful while listening to the rain."},
    )

    assert response.status_code == 200
    assert response.json() == {
        "emotion": "reflective",
        "keywords": ["rain", "nature", "peace"],
        "summary": "The user describes a reflective and peaceful nature experience.",
    }
    assert received == [("I felt peaceful while listening to the rain.", None)]


def test_text_analysis_reuses_cached_entry_analysis(client: TestClient, monkeypatch):
    headers = register(client)
    text = "The same reflection with different spacing"
    entry_id = create_entry(client, headers, text)
    calls: list[str] = []

    def fake_analysis(value: str, _ambience=None):
        calls.append(value)
        return {
            "emotion": "reflective",
            "keywords": ["same", "reflection", "spacing"],
            "summary": "The user offers a reflective note about a repeated experience.",
        }

    monkeypatch.setattr("app.main.analyze_text", fake_analysis)
    assert client.post(
        "/api/journal/analyze", headers=headers, json={"entryId": entry_id}
    ).status_code == 200
    cached = client.post(
        "/api/journal/analyze",
        headers=headers,
        json={"text": "  THE same reflection   with different spacing  "},
    )

    assert cached.status_code == 200
    assert cached.json()["emotion"] == "reflective"
    assert calls == [text]


def test_duplicate_entries_share_cached_analysis(client: TestClient, monkeypatch):
    headers = register(client)
    first = create_entry(client, headers, "Repeated reflection")
    second = create_entry(client, headers, " repeated   REFLECTION ")
    calls = 0

    def fake_analysis(_text: str, _ambience=None):
        nonlocal calls
        calls += 1
        return {
            "emotion": "calm",
            "keywords": ["repeated", "reflection", "calm"],
            "summary": "The repeated reflection conveys a calm emotional tone.",
        }

    monkeypatch.setattr("app.main.analyze_text", fake_analysis)
    for entry_id in [first, second]:
        assert client.post(
            "/api/journal/analyze", headers=headers, json={"entryId": entry_id}
        ).status_code == 200

    assert calls == 1
    entries = client.get("/api/journal", headers=headers).json()
    assert all(entry["analysis"]["emotion"] == "calm" for entry in entries)


def test_missing_entry_and_provider_errors_are_mapped(client: TestClient, monkeypatch):
    from app.llm import LLMConfigurationError, LLMProviderError

    headers = register(client)
    assert client.post(
        "/api/journal/analyze", headers=headers, json={"entryId": 999}
    ).status_code == 404

    monkeypatch.setattr(
        "app.main.analyze_text",
        lambda *_args: (_ for _ in ()).throw(LLMConfigurationError("bad key")),
    )
    configured = client.post(
        "/api/journal/analyze", headers=headers, json={"text": "Valid reflection"}
    )
    assert configured.status_code == 503
    assert "GROQ_API_KEY" in configured.json()["detail"]

    monkeypatch.setattr(
        "app.main.analyze_text",
        lambda *_args: (_ for _ in ()).throw(LLMProviderError("timeout")),
    )
    unavailable = client.post(
        "/api/journal/analyze", headers=headers, json={"text": "Another reflection"}
    )
    assert unavailable.status_code == 502
    assert unavailable.json()["detail"] == "The analysis service is temporarily unavailable"


@pytest.mark.parametrize(
    "payload",
    [{}, {"entryId": 1, "text": "Only one source is allowed"}],
)
def test_analysis_requires_exactly_one_source(client: TestClient, payload: dict):
    headers = register(client)
    assert client.post("/api/journal/analyze", headers=headers, json=payload).status_code == 422


def test_assignment_compatible_user_routes_are_authorized(client: TestClient):
    alice_headers = register(client, "alice")
    create_entry(client, alice_headers)
    register(client, "bob")

    assert client.get("/api/journal/alice", headers=alice_headers).status_code == 200
    assert client.get("/api/journal/insights/alice", headers=alice_headers).status_code == 200
    assert client.get("/api/journal/bob", headers=alice_headers).status_code == 403


def test_assignment_user_id_is_accepted_but_cannot_be_spoofed(client: TestClient):
    headers = register(client, "alice")
    accepted = client.post(
        "/api/journal",
        headers=headers,
        json={"userId": "alice", "ambience": "forest", "text": "A valid entry"},
    )
    rejected = client.post(
        "/api/journal",
        headers=headers,
        json={"userId": "bob", "ambience": "forest", "text": "Spoofed owner"},
    )
    assert accepted.status_code == 201
    assert rejected.status_code == 403


def test_insights_are_scoped_to_authenticated_user(client: TestClient, monkeypatch):
    headers = register(client)
    entry_id = create_entry(client, headers)
    monkeypatch.setattr(
        "app.main.analyze_text",
        lambda _text, _ambience=None: {
            "emotion": "joyful",
            "keywords": ["trees", "sunlight", "energy"],
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
        "recentKeywords": ["trees", "sunlight", "energy"],
    }
