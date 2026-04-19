import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


def load_env_files() -> None:
    for candidate in (".env", "local.env"):
        env_path = BASE_DIR / candidate
        if env_path.exists():
            load_dotenv(env_path, override=False)


load_env_files()


def resolve_backend_path(value: str, default: str) -> Path:
    raw_path = Path(value or default)
    return raw_path if raw_path.is_absolute() else BASE_DIR / raw_path


def resolve_medical_book_path() -> Path:
    configured_path = resolve_backend_path(
        os.getenv("MEDICAL_BOOK_PATH", "data/medical_book.pdf"), "data/medical_book.pdf"
    )

    if configured_path.exists():
        return configured_path

    pdf_candidates = sorted((BASE_DIR / "data").glob("*.pdf"))
    if len(pdf_candidates) == 1:
        return pdf_candidates[0]

    return configured_path


class Config:
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    OPENAI_CHAT_FALLBACK_MODEL = os.getenv("OPENAI_CHAT_FALLBACK_MODEL", "gpt-4.1-mini")
    OPENAI_NORMALIZATION_MODEL = os.getenv("OPENAI_NORMALIZATION_MODEL", "gpt-4.1-mini")

    VECTOR_STORE_DIR = resolve_backend_path(
        os.getenv("VECTOR_STORE_DIR", "storage/chroma_db"), "storage/chroma_db"
    )
    MEDICAL_BOOK_PATH = resolve_medical_book_path()

    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "medical_book_chunks")
    EMBEDDING_MODEL_NAME = os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
    )

    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "90"))
    TOP_K = int(os.getenv("TOP_K", "4"))

    # Strict RAG refusal uses both similarity and keyword coverage before generation.
    MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.42"))
    MIN_KEYWORD_COVERAGE = float(os.getenv("MIN_KEYWORD_COVERAGE", "0.60"))
    STRONG_RELEVANCE_SCORE = float(os.getenv("STRONG_RELEVANCE_SCORE", "0.62"))

    # Query normalization confidence policy stays separate from the retrieval gate.
    NORMALIZATION_HIGH_CONFIDENCE = float(os.getenv("NORMALIZATION_HIGH_CONFIDENCE", "0.75"))
    NORMALIZATION_MEDIUM_CONFIDENCE = float(os.getenv("NORMALIZATION_MEDIUM_CONFIDENCE", "0.45"))
    NORMALIZATION_CACHE_SIZE = int(os.getenv("NORMALIZATION_CACHE_SIZE", "128"))

    SAFETY_WARNING = (
        "Educational use only. MediAssist AI is not a substitute for a licensed "
        "healthcare professional and must not be used for emergencies, diagnosis, "
        "or treatment decisions."
    )
