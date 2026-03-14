from pydantic import BaseModel
from typing import List, Optional


class JournalCreate(BaseModel):
    userId: str
    ambience: str
    text: str


class AnalyzeRequest(BaseModel):
    text: str
    entryId: Optional[int] = None


class AnalyzeResponse(BaseModel):
    emotion: str
    keywords: List[str]
    summary: str


class EntryWithAnalysis(BaseModel):
    id: int
    userId: str
    ambience: str
    text: str
    createdAt: str
    analysis: Optional[AnalyzeResponse] = None


class InsightResponse(BaseModel):
    totalEntries: int
    topEmotion: Optional[str]
    mostUsedAmbience: Optional[str]
    recentKeywords: List[str]