import json
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from app.db import Base, engine, get_db
from app import crud, schemas
from app.services.analysis_service import analyze_text
from app.services.insights_service import build_insights
from app.utils.hash import hash_text

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Assisted Journal System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ideal-rotary-phone-r4444rxgjw9p2695-3000.app.github.dev",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Journal API is running"}


@app.post("/api/journal")
def create_journal(payload: schemas.JournalCreate, db: Session = Depends(get_db)):
    entry = crud.create_journal_entry(
        db=db,
        user_id=payload.userId,
        ambience=payload.ambience,
        text=payload.text,
    )
    return {
        "id": entry.id,
        "userId": entry.user_id,
        "ambience": entry.ambience,
        "text": entry.text,
        "createdAt": entry.created_at.isoformat() if entry.created_at else "",
    }


@app.get("/api/journal/{user_id}")
def get_journal_entries(user_id: str, db: Session = Depends(get_db)):
    entries = crud.get_entries_by_user(db, user_id)

    response = []
    for entry in entries:
        analysis = crud.get_analysis_by_entry_id(db, entry.id)

        analysis_data = None
        if analysis:
            try:
                analysis_data = {
                    "emotion": analysis.emotion,
                    "keywords": json.loads(analysis.keywords),
                    "summary": analysis.summary,
                }
            except Exception:
                analysis_data = None

        response.append(
            {
                "id": entry.id,
                "userId": entry.user_id,
                "ambience": entry.ambience,
                "text": entry.text,
                "createdAt": entry.created_at.isoformat() if entry.created_at else "",
                "analysis": analysis_data,
            }
        )

    return response


@app.post("/api/journal/analyze")
def analyze_journal(payload: schemas.AnalyzeRequest, db: Session = Depends(get_db)):
    try:
        text_hash = hash_text(payload.text)

        cached = crud.get_analysis_by_text_hash(db, text_hash)
        if cached:
            if payload.entryId is not None:
                existing_entry_analysis = crud.get_analysis_by_entry_id(db, payload.entryId)
                if not existing_entry_analysis:
                    crud.create_analysis(
                        db=db,
                        journal_entry_id=payload.entryId,
                        text_hash=text_hash,
                        emotion=cached.emotion,
                        keywords=cached.keywords,
                        summary=cached.summary,
                    )

            return {
                "emotion": cached.emotion,
                "keywords": json.loads(cached.keywords),
                "summary": cached.summary,
            }

        result = analyze_text(payload.text)

        crud.create_analysis(
            db=db,
            journal_entry_id=payload.entryId,
            text_hash=text_hash,
            emotion=result["emotion"],
            keywords=json.dumps(result["keywords"]),
            summary=result["summary"],
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/journal/insights/{user_id}")
def get_journal_insights(user_id: str, db: Session = Depends(get_db)):
    entries = crud.get_entries_by_user(db, user_id)
    entry_ids = [entry.id for entry in entries]
    analyses = crud.get_analyses_for_entry_ids(db, entry_ids)

    return build_insights(entries, analyses)