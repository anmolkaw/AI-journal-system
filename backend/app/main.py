import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db import Base, engine, get_db
from app.llm import LLMConfigurationError, LLMProviderError
from app.security import (
    create_access_token,
    get_current_user_id,
    hash_password,
    verify_password,
)
from app.services.analysis_service import analyze_text
from app.services.insights_service import build_insights
from app.utils.hash import hash_text

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AI-Assisted Journal System", version="1.0.0", lifespan=lifespan)

raw_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


def serialize_analysis(analysis) -> schemas.AnalyzeResponse:
    try:
        keywords = json.loads(analysis.keywords)
    except (TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Stored analysis is invalid") from exc
    return schemas.AnalyzeResponse(
        emotion=analysis.emotion,
        keywords=keywords,
        summary=analysis.summary,
    )


def serialize_entry(entry, analysis=None) -> schemas.JournalEntryResponse:
    return schemas.JournalEntryResponse(
        id=entry.id,
        userId=entry.user_id,
        ambience=entry.ambience,
        text=entry.text,
        createdAt=entry.created_at,
        analysis=serialize_analysis(analysis) if analysis else None,
    )


@app.get("/", tags=["health"])
def root():
    return {"message": "Journal API is running"}


@app.post(
    "/api/auth/register",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["authentication"],
)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if crud.get_user(db, payload.username):
        raise HTTPException(status_code=409, detail="Username is already registered")
    try:
        crud.create_user(db, payload.username, hash_password(payload.password))
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username is already registered") from exc
    return schemas.TokenResponse(
        accessToken=create_access_token(payload.username),
        userId=payload.username,
    )


@app.post(
    "/api/auth/login",
    response_model=schemas.TokenResponse,
    tags=["authentication"],
)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user(db, payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return schemas.TokenResponse(
        accessToken=create_access_token(user.id),
        userId=user.id,
    )


@app.post(
    "/api/journal",
    response_model=schemas.JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["journal"],
)
def create_journal(
    payload: schemas.JournalCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if payload.userId is not None and payload.userId != user_id:
        raise HTTPException(status_code=403, detail="userId must match the authenticated user")
    entry = crud.create_journal_entry(
        db=db,
        user_id=user_id,
        ambience=payload.ambience,
        text=payload.text,
    )
    return serialize_entry(entry)


@app.get(
    "/api/journal",
    response_model=list[schemas.JournalEntryResponse],
    tags=["journal"],
)
def get_journal_entries(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return [
        serialize_entry(entry, analysis)
        for entry, analysis in crud.get_entries_with_analyses(db, user_id)
    ]


@app.post(
    "/api/journal/analyze",
    response_model=schemas.AnalyzeResponse,
    tags=["analysis"],
)
def analyze_journal(
    payload: schemas.AnalyzeRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    entry = None
    ambience = None
    if payload.entryId is not None:
        entry = crud.get_entry_by_id_for_user(db, payload.entryId, user_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")

        existing = crud.get_analysis_by_entry_id(db, entry.id)
        if existing:
            return serialize_analysis(existing)

        text = entry.text
        ambience = entry.ambience
    else:
        text = payload.text or ""

    text_hash = hash_text(text)
    cached = crud.get_analysis_by_text_hash(db, text_hash)
    if cached:
        if entry is not None:
            cached = crud.create_analysis(
                db=db,
                journal_entry_id=entry.id,
                text_hash=text_hash,
                emotion=cached.emotion,
                keywords=cached.keywords,
                summary=cached.summary,
            )
        return serialize_analysis(cached)

    try:
        result = analyze_text(text, ambience)
    except LLMConfigurationError as exc:
        logger.error("Journal analysis configuration error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI analysis is not configured. Add a valid GROQ_API_KEY.",
        ) from exc
    except LLMProviderError as exc:
        logger.warning("Journal analysis provider error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="The analysis service is temporarily unavailable",
        ) from exc

    if entry is None:
        return schemas.AnalyzeResponse(**result)

    return serialize_analysis(
        crud.create_analysis(
            db=db,
            journal_entry_id=entry.id,
            text_hash=text_hash,
            emotion=result["emotion"],
            keywords=json.dumps(result["keywords"]),
            summary=result["summary"],
        )
    )


@app.get(
    "/api/journal/insights",
    response_model=schemas.InsightResponse,
    tags=["analysis"],
)
def get_journal_insights(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    entries = crud.get_entries_by_user(db, user_id)
    entry_ids = [entry.id for entry in entries]
    analyses = crud.get_analyses_for_entry_ids(db, entry_ids)
    return build_insights(entries, analyses)


def require_matching_user(requested_user_id: str, authenticated_user_id: str) -> None:
    if requested_user_id != authenticated_user_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's journal")


@app.get(
    "/api/journal/insights/{requested_user_id}",
    response_model=schemas.InsightResponse,
    tags=["assignment-compatible"],
)
def get_journal_insights_by_user_id(
    requested_user_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    require_matching_user(requested_user_id, user_id)
    return get_journal_insights(db, user_id)


@app.get(
    "/api/journal/{requested_user_id}",
    response_model=list[schemas.JournalEntryResponse],
    tags=["assignment-compatible"],
)
def get_journal_entries_by_user_id(
    requested_user_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    require_matching_user(requested_user_id, user_id)
    return get_journal_entries(db, user_id)
