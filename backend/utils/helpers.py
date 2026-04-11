import re


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def snippet(value: str, max_chars: int = 360) -> str:
    text = clean_text(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rsplit(" ", 1)[0] + "..."


def is_emergency_message(message: str) -> bool:
    emergency_terms = {
        "can't breathe",
        "cannot breathe",
        "chest pain",
        "stroke",
        "seizure",
        "unconscious",
        "heavy bleeding",
        "poison",
        "suicide",
        "overdose",
        "emergency",
        "severe allergic",
        "anaphylaxis",
    }
    lowered = message.lower()
    return any(term in lowered for term in emergency_terms)
