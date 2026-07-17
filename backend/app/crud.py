from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import JournalAnalysis, JournalEntry, User


def create_user(db: Session, user_id: str, password_hash: str):
    user = User(id=user_id, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()


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


def get_entries_with_analyses(db: Session, user_id: str):
    return (
        db.query(JournalEntry, JournalAnalysis)
        .outerjoin(JournalAnalysis, JournalAnalysis.journal_entry_id == JournalEntry.id)
        .filter(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.created_at.desc())
        .all()
    )


def get_entry_by_id_for_user(db: Session, entry_id: int, user_id: str):
    return (
        db.query(JournalEntry)
        .filter(JournalEntry.id == entry_id, JournalEntry.user_id == user_id)
        .first()
    )


def create_analysis(
    db: Session,
    journal_entry_id: int,
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
    try:
        db.commit()
        db.refresh(analysis)
        return analysis
    except IntegrityError:
        db.rollback()
        existing = get_analysis_by_entry_id(db, journal_entry_id)
        if existing:
            return existing
        raise


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
