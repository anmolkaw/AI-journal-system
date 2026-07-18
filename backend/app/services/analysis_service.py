from app.llm import analyze_emotion_with_llm


def analyze_text(text: str, ambience: str | None = None):
    return analyze_emotion_with_llm(text, ambience)
