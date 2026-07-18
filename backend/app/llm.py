import json
import os
from typing import Literal

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

EmotionLabel = Literal[
    "calm",
    "joyful",
    "hopeful",
    "reflective",
    "anxious",
    "stressed",
    "sad",
    "lonely",
    "frustrated",
    "tired",
    "mixed",
    "neutral",
]


class LLMConfigurationError(RuntimeError):
    """The analysis provider is missing or has rejected its credentials."""


class LLMProviderError(RuntimeError):
    """The analysis provider was unavailable or returned an invalid response."""


class EmotionAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    emotion: EmotionLabel
    keywords: list[str] = Field(min_length=3, max_length=5)
    summary: str = Field(min_length=12, max_length=240)

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, keywords: list[str]) -> list[str]:
        normalized = [keyword.strip().lower() for keyword in keywords if keyword.strip()]
        if not 3 <= len(normalized) <= 5:
            raise ValueError("keywords must contain 3 to 5 non-empty values")
        if len(normalized) != len(set(normalized)):
            raise ValueError("keywords must be unique")
        if any(len(keyword) > 32 for keyword in normalized):
            raise ValueError("keywords must be concise")
        return normalized


SYSTEM_PROMPT = """
You analyze the emotional tone of a private nature-session journal entry.

Use only evidence present in the journal. Do not diagnose a medical condition,
infer sensitive facts, or give advice. Choose one emotion from the supplied
schema. Use "mixed" when two tones are equally prominent and "neutral" when the
entry has too little emotional evidence. Keywords must be concrete themes from
the entry, not generic sentiment words. The summary must be one neutral,
third-person sentence that connects the emotional tone to the stated experience.
Return the schema-constrained JSON object now.
""".strip()


def _response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "emotion_analysis",
            "strict": True,
            "schema": EmotionAnalysis.model_json_schema(),
        },
    }


def analyze_emotion_with_llm(text: str, ambience: str | None = None) -> dict:
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key":
        raise LLMConfigurationError("GROQ_API_KEY is not configured")

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"ambience": ambience or "not provided", "journal": text},
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.1,
        # GPT-OSS uses part of this budget for hidden reasoning. A very small
        # ceiling can produce an empty structured response before JSON is emitted.
        "max_completion_tokens": 800,
        "reasoning_effort": "low",
        "response_format": _response_format(),
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise LLMProviderError("Groq request failed") from exc

    if response.status_code in {401, 403}:
        raise LLMConfigurationError("Groq rejected the configured API key")
    if response.status_code != 200:
        raise LLMProviderError(f"Groq returned HTTP {response.status_code}")

    try:
        content = response.json()["choices"][0]["message"]["content"]
        analysis = EmotionAnalysis.model_validate_json(content)
    except (KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
        raise LLMProviderError("Groq returned an invalid emotion analysis") from exc

    return analysis.model_dump()
