import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def analyze_emotion_with_llm(text: str):
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY in environment")

    system_prompt = """
You are an emotion analysis assistant for wellness journal entries.
Return ONLY valid JSON with this exact schema:
{
  "emotion": "one short lowercase emotion label",
  "keywords": ["3 to 5 short keywords"],
  "summary": "one sentence summary"
}

Rules:
- No markdown
- No extra text
- Emotion must be a single label like calm, anxious, joyful, stressed, reflective, sad, hopeful
- Keywords must be short and meaningful
- Summary must be concise and neutral
""".strip()

    user_prompt = f'Analyze this journal entry:\n\n"{text}"'

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        # "response_format": {"type": "json_object"},
    }

    response = requests.post(
        GROQ_API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Groq API error: {response.status_code} - {response.text}")

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"Unexpected Groq response format: {data}") from exc

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Groq did not return valid JSON: {content}") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("LLM response was not a JSON object")

    emotion = parsed.get("emotion")
    keywords = parsed.get("keywords")
    summary = parsed.get("summary")

    if not emotion or not isinstance(emotion, str):
        raise RuntimeError("Invalid LLM response: missing emotion")
    if not keywords or not isinstance(keywords, list):
        raise RuntimeError("Invalid LLM response: missing keywords")
    if not summary or not isinstance(summary, str):
        raise RuntimeError("Invalid LLM response: missing summary")

    return {
        "emotion": emotion.strip().lower(),
        "keywords": [str(k).strip().lower() for k in keywords][:5],
        "summary": summary.strip(),
    }
