import pytest

from app.db import normalize_database_url, resolve_database_url


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("postgres://user:pass@host/db", "postgresql+psycopg://user:pass@host/db"),
        ("postgresql://user:pass@host/db", "postgresql+psycopg://user:pass@host/db"),
        ("postgresql+psycopg://user:pass@host/db", "postgresql+psycopg://user:pass@host/db"),
        ("sqlite:///./journal.db", "sqlite:///./journal.db"),
    ],
)
def test_normalize_database_url(source: str, expected: str):
    assert normalize_database_url(source) == expected


def test_production_requires_durable_database():
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        resolve_database_url(None, is_vercel=True, vercel_environment="production")


def test_vercel_preview_can_use_temporary_sqlite():
    assert (
        resolve_database_url(None, is_vercel=True, vercel_environment="preview")
        == "sqlite:////tmp/journal.db"
    )
