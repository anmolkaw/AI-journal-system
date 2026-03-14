import hashlib


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def hash_text(text: str) -> str:
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()