from app.llm import analyze_emotion_with_llm


def analyze_text(text: str):
    return analyze_emotion_with_llm(text)