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
    "disease",
    "disorders",
    "effect",
    "effects",
    "explain",
    "explainer",
    "explanation",
    "health",
    "healthcare",
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
    "type",
    "types",
    "work",
    "works",
}

FORMAT_REQUEST_TERMS = {
    "between",
    "bullet",
    "bullets",
    "compare",
    "comparison",
    "difference",
    "differences",
    "different",
    "format",
    "formatted",
    "key",
    "list",
    "listed",
    "main",
    "outline",
    "point",
    "points",
    "step",
    "steps",
    "summarize",
    "summary",
    "table",
    "versus",
    "vs",
}

META_QUERY_TERMS = {
    "citation",
    "citations",
    "match",
    "matches",
    "matching",
    "source",
    "sources",
}

NON_TOPIC_TERMS = QUESTION_STOPWORDS | GENERIC_QUERY_TERMS | FORMAT_REQUEST_TERMS | META_QUERY_TERMS


class MedicalRetriever:
    def __init__(self, vector_store: ChromaVectorStore | None = None):
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve(self, query: str) -> list[dict]:
        normalized_query = clean_text(query)
        if not normalized_query:
            return []
        query_embedding = embed_texts([normalized_query])[0]
        return self.vector_store.query(query_embedding, n_results=Config.TOP_K)

    def assess_context(self, focus_query: str, retrieval_query: str | None = None) -> dict:
        focus_text = clean_text(focus_query)
        retrieval_text = clean_text(retrieval_query or focus_query)
        focus_terms = self._extract_focus_terms(focus_text)
        if not focus_terms:
            return {
                "is_sufficient": False,
                "accepted_chunks": [],
                "reason": "question_is_too_vague_or_meta",
                "focus_terms": [],
                "top_similarity": 0.0,
                "retrieval_query": retrieval_text,
            }

        raw_matches = [
            self._annotate_match(match, focus_terms)
            for match in self.retrieve(retrieval_text)
        ]
        relevant_matches = [
            match
            for match in raw_matches
            if match.get("similarity", 0.0) >= Config.MIN_RELEVANCE_SCORE
        ]
        if not relevant_matches:
            return {
                "is_sufficient": False,
                "accepted_chunks": [],
                "reason": "similarity_below_threshold",
                "focus_terms": focus_terms,
                "top_similarity": raw_matches[0].get("similarity", 0.0) if raw_matches else 0.0,
                "retrieval_query": retrieval_text,
            }

        keyword_supported = [
            match
            for match in relevant_matches
            if match.get("keyword_coverage", 0.0) >= Config.MIN_KEYWORD_COVERAGE
        ]
        if not keyword_supported:
            return {
                "is_sufficient": False,
                "accepted_chunks": [],
                "reason": "missing_key_question_terms_in_context",
                "focus_terms": focus_terms,
                "top_similarity": relevant_matches[0].get("similarity", 0.0),
                "retrieval_query": retrieval_text,
            }

        accepted_chunks = keyword_supported[: Config.TOP_K]
        return {
            "is_sufficient": True,
            "accepted_chunks": accepted_chunks,
            "reason": "accepted",
            "focus_terms": focus_terms,
            "top_similarity": accepted_chunks[0].get("similarity", 0.0),
            "retrieval_query": retrieval_text,
        }

    @staticmethod
    def _extract_focus_terms(question: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z0-9]+", clean_text(question).lower())
        focus_terms = []
        for token in tokens:
            if len(token) < 3:
                continue
            if token in NON_TOPIC_TERMS:
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


