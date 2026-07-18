import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


def normalize_database_url(database_url: str) -> str:
    """Use Psycopg 3 for PostgreSQL URLs supplied by hosting providers."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def resolve_database_url(
    configured_database_url: str | None,
    *,
    is_vercel: bool,
    vercel_environment: str | None,
) -> str:
    if vercel_environment == "production" and not configured_database_url:
        raise RuntimeError("DATABASE_URL is required in production")

    default_database_url = (
        "sqlite:////tmp/journal.db" if is_vercel else "sqlite:///./journal.db"
    )
    return normalize_database_url(configured_database_url or default_database_url)

# Local development and preview deployments may use SQLite. Production refuses
# to start without durable storage so user accounts can never silently disappear.
DATABASE_URL = resolve_database_url(
    os.getenv("DATABASE_URL"),
    is_vercel=bool(os.getenv("VERCEL")),
    vercel_environment=os.getenv("VERCEL_ENV"),
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
