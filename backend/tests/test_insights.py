import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.insights_service import build_insights


def entry(ambience: str):
    return SimpleNamespace(ambience=ambience)


def analysis(emotion: str, keywords, minutes_ago: int = 0):
    return SimpleNamespace(
        emotion=emotion,
        keywords=json.dumps(keywords) if not isinstance(keywords, str) else keywords,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
    )


def test_empty_insights_are_explicit():
    assert build_insights([], []) == {
        "totalEntries": 0,
        "topEmotion": None,
        "mostUsedAmbience": None,
        "recentKeywords": [],
    }


def test_insights_aggregate_emotions_ambience_and_recent_keywords():
    entries = [entry("forest"), entry("forest"), entry("ocean")]
    analyses = [
        analysis("calm", ["rain", "trees", "quiet"], 1),
        analysis("calm", ["rain", "breathing", "quiet"], 2),
        analysis("hopeful", ["sunlight", "trail", "energy"], 3),
    ]

    result = build_insights(entries, analyses)

    assert result["totalEntries"] == 3
    assert result["topEmotion"] == "calm"
    assert result["mostUsedAmbience"] == "forest"
    assert result["recentKeywords"] == ["rain", "quiet", "trees"]


def test_insights_ignore_malformed_keyword_records():
    result = build_insights(
        [entry("mountain")],
        [
            analysis("reflective", "not-json", 0),
            analysis("reflective", ["clarity", "height", "perspective"], 1),
        ],
    )
    assert result["topEmotion"] == "reflective"
    assert result["recentKeywords"] == ["clarity", "height", "perspective"]
