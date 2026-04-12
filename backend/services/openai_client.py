from openai import OpenAI

from config import Config
from services.prompt_builder import MEDICAL_SYSTEM_PROMPT, build_user_prompt
from utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIAnswerClient:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.chat_fallback_model = Config.OPENAI_CHAT_FALLBACK_MODEL

    @staticmethod
    def _should_use_chat_fallback(exc: Exception) -> bool:
        message = str(exc).lower()
        return "api.responses.write" in message or (
            "responses" in message and "scope" in message
        )

    def _generate_with_chat_completions(
        self, question: str, retrieved_chunks: list[dict]
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.chat_fallback_model,
            messages=[
                {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_user_prompt(question, retrieved_chunks),
                },
            ],
            max_completion_tokens=650,
        )
        return response.choices[0].message.content.strip()

    def generate_answer(self, question: str, retrieved_chunks: list[dict]) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=MEDICAL_SYSTEM_PROMPT,
                input=build_user_prompt(question, retrieved_chunks),
                max_output_tokens=650,
            )
            return response.output_text.strip()
        except Exception as exc:
            if not self._should_use_chat_fallback(exc):
                raise

            logger.warning(
                "Responses API was unavailable for this request. Falling back to chat completions."
            )
            return self._generate_with_chat_completions(question, retrieved_chunks)
