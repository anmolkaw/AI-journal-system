import json
from collections import Counter


def build_insights(entries, analyses):
    total_entries = len(entries)

    top_emotion = None
    most_used_ambience = None
    recent_keywords = []

    if entries:
        ambience_counter = Counter(entry.ambience for entry in entries)
        most_used_ambience = ambience_counter.most_common(1)[0][0]

    if analyses:
        emotion_counter = Counter(a.emotion for a in analyses if a.emotion)
        if emotion_counter:
            top_emotion = emotion_counter.most_common(1)[0][0]

        sorted_analyses = sorted(
            analyses,
            key=lambda a: a.created_at if a.created_at else 0,
            reverse=True,
        )

        keyword_counter = Counter()
        for analysis in sorted_analyses[:5]:
            try:
                keywords = json.loads(analysis.keywords)
                for keyword in keywords:
                    keyword_counter[str(keyword).strip().lower()] += 1
            except Exception:
                continue

        recent_keywords = [k for k, _ in keyword_counter.most_common(3)]

    return {
        "totalEntries": total_entries,
        "topEmotion": top_emotion,
        "mostUsedAmbience": most_used_ambience,
        "recentKeywords": recent_keywords,
    }