from config import Config
from services.openai_client import OpenAIAnswerClient
from services.prompt_builder import build_source_payload
from services.retriever import MedicalRetriever
from utils.helpers import clean_text, is_emergency_message, snippet
from utils.logger import get_logger

INSUFFICIENT_CONTEXT_ANSWER = (
    "I do not have enough relevant medical-book context to answer that confidently."
)

URGENT_CARE_NOTE = (
    " If this involves severe symptoms, breathing difficulty, chest pain, stroke signs, "
    "heavy bleeding, loss of consciousness, poisoning, or another emergency, seek "
    "immediate professional or emergency help now."
)

OPENAI_UNAVAILABLE_NOTE = (
    "OpenAI response generation is unavailable right now, so this answer is a direct "
    "summary of the most relevant retrieved book context."
)

logger = get_logger(__name__)


class ChatbotService:
    def __init__(self):
        self.retriever = MedicalRetriever()

    def _build_retrieval_fallback(self, retrieved_chunks: list[dict], question: str) -> str:
        excerpts = []
        for chunk in retrieved_chunks[:2]:
            excerpt = snippet(chunk.get("text", ""), 360)
            if excerpt:
                excerpts.append(excerpt)

        if not excerpts:
            answer = INSUFFICIENT_CONTEXT_ANSWER
        else:
            joined = "\n\n".join(
                f"Relevant medical-book context {index + 1}: {excerpt}"
                for index, excerpt in enumerate(excerpts)
            )
            answer = (
                f"{OPENAI_UNAVAILABLE_NOTE}\n\n"
                f"{joined}\n\n"
                "Please treat this as educational information only and confirm important "
                "decisions with a licensed healthcare professional."
            )

        if is_emergency_message(question):
            answer += f"\n\nUrgent note:{URGENT_CARE_NOTE.strip()}"

        return answer

    def answer(self, raw_message: str) -> dict:
        question = clean_text(raw_message)
        if not question:
            raise ValueError("Message is required.")
        if len(question) > 1500:
            raise ValueError("Message is too long. Please keep it under 1500 characters.")

        retrieved_chunks = self.retriever.retrieve(question)
        has_relevant_context = any(
            chunk.get("similarity", 0) >= Config.MIN_RELEVANCE_SCORE
            for chunk in retrieved_chunks
        )

        if not retrieved_chunks or not has_relevant_context:
            answer = INSUFFICIENT_CONTEXT_ANSWER
            if is_emergency_message(question):
                answer += URGENT_CARE_NOTE
            return {
                "answer": answer,
                "sources": build_source_payload(retrieved_chunks),
                "warning": Config.SAFETY_WARNING,
            }

        try:
            answer = OpenAIAnswerClient().generate_answer(question, retrieved_chunks)
        except Exception as exc:
            logger.warning("OpenAI generation failed, falling back to retrieved context: %s", exc)
            answer = self._build_retrieval_fallback(retrieved_chunks, question)

        if is_emergency_message(question) and "emergency" not in answer.lower():
            answer = f"{answer}\n\nUrgent note:{URGENT_CARE_NOTE.strip()}"

        return {
            "answer": answer,
            "sources": build_source_payload(retrieved_chunks),
            "warning": Config.SAFETY_WARNING,
        }
