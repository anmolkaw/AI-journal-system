from sqlalchemy.orm import Session
from app.models import JournalEntry, JournalAnalysis


def create_journal_entry(db: Session, user_id: str, ambience: str, text: str):
    entry = JournalEntry(user_id=user_id, ambience=ambience, text=text)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_entries_by_user(db: Session, user_id: str):
    return (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.created_at.desc())
        .all()
    )


def get_entry_by_id(db: Session, entry_id: int):
    return db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()


def create_analysis(
    db: Session,
    journal_entry_id: int | None,
    text_hash: str,
    emotion: str,
    keywords: str,
    summary: str,
):
    analysis = JournalAnalysis(
        journal_entry_id=journal_entry_id,
        text_hash=text_hash,
        emotion=emotion,
        keywords=keywords,
        summary=summary,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis_by_text_hash(db: Session, text_hash: str):
    return db.query(JournalAnalysis).filter(JournalAnalysis.text_hash == text_hash).first()


def get_analysis_by_entry_id(db: Session, entry_id: int):
    return (
        db.query(JournalAnalysis)
        .filter(JournalAnalysis.journal_entry_id == entry_id)
        .order_by(JournalAnalysis.created_at.desc())
        .first()
    )


def get_analyses_for_entry_ids(db: Session, entry_ids: list[int]):
    if not entry_ids:
        return []
    return db.query(JournalAnalysis).filter(JournalAnalysis.journal_entry_id.in_(entry_ids)).all()