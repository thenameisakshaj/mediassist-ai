from config import Config
from services.openai_client import OpenAIAnswerClient
from services.prompt_builder import build_source_payload
from services.retriever import MedicalRetriever
from utils.helpers import clean_text, is_emergency_message

INSUFFICIENT_CONTEXT_ANSWER = (
    "I do not have enough relevant medical-book context to answer that confidently."
)

URGENT_CARE_NOTE = (
    " If this involves severe symptoms, breathing difficulty, chest pain, stroke signs, "
    "heavy bleeding, loss of consciousness, poisoning, or another emergency, seek "
    "immediate professional or emergency help now."
)


class ChatbotService:
    def __init__(self):
        self.retriever = MedicalRetriever()

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

        answer = OpenAIAnswerClient().generate_answer(question, retrieved_chunks)
        if is_emergency_message(question) and "emergency" not in answer.lower():
            answer = f"{answer}\n\nUrgent note:{URGENT_CARE_NOTE.strip()}"

        return {
            "answer": answer,
            "sources": build_source_payload(retrieved_chunks),
            "warning": Config.SAFETY_WARNING,
        }
