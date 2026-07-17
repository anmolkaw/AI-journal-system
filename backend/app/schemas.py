from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class RegisterRequest(StrictModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    accessToken: str
    tokenType: Literal["bearer"] = "bearer"
    userId: str


class JournalCreate(StrictModel):
    ambience: Literal["forest", "ocean", "mountain"]
    text: str = Field(min_length=1, max_length=10_000)


class AnalyzeRequest(StrictModel):
    entryId: int = Field(gt=0)


class AnalyzeResponse(BaseModel):
    emotion: str
    keywords: list[str]
    summary: str


class JournalEntryResponse(BaseModel):
    id: int
    userId: str
    ambience: Literal["forest", "ocean", "mountain"]
    text: str
    createdAt: datetime
    analysis: AnalyzeResponse | None = None


class InsightResponse(BaseModel):
    totalEntries: int
    topEmotion: str | None
    mostUsedAmbience: str | None
    recentKeywords: list[str]
