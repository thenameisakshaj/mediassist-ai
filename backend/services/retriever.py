import re

from config import Config
from services.embeddings import embed_texts
from services.vector_store import ChromaVectorStore
from utils.helpers import clean_text

QUESTION_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "did",
    "do",
    "does",
    "for",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "they",
    "this",
    "those",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}

# These generic query terms are ignored so the gate focuses on the medical topic itself.
GENERIC_QUERY_TERMS = {
    "about",
    "answer",
    "answers",
    "cause",
    "caused",
    "causes",
    "condition",
    "conditions",
    "define",
    "definition",
    "describe",
    "difference",
    "disease",
    "disorders",
    "effect",
    "effects",
    "explain",
    "explainer",
    "health",
    "healthcare",
    "match",
    "matches",
    "matching",
    "mean",
    "meaning",
    "medical",
    "medicine",
    "patient",
    "question",
    "symptom",
    "symptoms",
    "tell",
    "treat",
    "treatment",
    "treatments",
    "work",
    "works",
}


class MedicalRetriever:
    def __init__(self, vector_store: ChromaVectorStore | None = None):
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve(self, question: str) -> list[dict]:
        query_embedding = embed_texts([question])[0]
        return self.vector_store.query(query_embedding, n_results=Config.TOP_K)

    def assess_context(self, question: str) -> dict:
        focus_terms = self._extract_focus_terms(question)
        if not focus_terms:
            return {
                "is_sufficient": False,
                "accepted_chunks": [],
                "reason": "question_is_too_vague_or_meta",
                "focus_terms": [],
            }

        raw_matches = [self._annotate_match(match, focus_terms) for match in self.retrieve(question)]
        relevant_matches = [
            match
            for match in raw_matches
            if match.get("similarity", 0) >= Config.MIN_RELEVANCE_SCORE
        ]
        if not relevant_matches:
            return {
                "is_sufficient": False,
                "accepted_chunks": [],
                "reason": "similarity_below_threshold",
                "focus_terms": focus_terms,
            }

        keyword_supported = [
            match
            for match in relevant_matches
            if match.get("keyword_coverage", 0) >= Config.MIN_KEYWORD_COVERAGE
        ]
        if not keyword_supported:
            return {
                "is_sufficient": False,
                "accepted_chunks": [],
                "reason": "missing_key_question_terms_in_context",
                "focus_terms": focus_terms,
            }

        return {
            "is_sufficient": True,
            "accepted_chunks": keyword_supported[: Config.TOP_K],
            "reason": "accepted",
            "focus_terms": focus_terms,
        }

    @staticmethod
    def _extract_focus_terms(question: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z]+", clean_text(question).lower())
        focus_terms = []
        for token in tokens:
            if len(token) < 3:
                continue
            if token in QUESTION_STOPWORDS or token in GENERIC_QUERY_TERMS:
                continue
            if token not in focus_terms:
                focus_terms.append(token)
        return focus_terms

    @staticmethod
    def _annotate_match(match: dict, focus_terms: list[str]) -> dict:
        chunk_text = clean_text(match.get("text", "")).lower()
        matched_terms = [term for term in focus_terms if term in chunk_text]
        keyword_coverage = len(matched_terms) / len(focus_terms) if focus_terms else 0.0

        annotated_match = dict(match)
        annotated_match["matched_terms"] = matched_terms
        annotated_match["keyword_coverage"] = round(keyword_coverage, 4)
        return annotated_match
