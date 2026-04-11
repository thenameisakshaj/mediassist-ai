from openai import OpenAI

from config import Config
from services.prompt_builder import MEDICAL_SYSTEM_PROMPT, build_user_prompt


class OpenAIAnswerClient:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL

    def generate_answer(self, question: str, retrieved_chunks: list[dict]) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=MEDICAL_SYSTEM_PROMPT,
            input=build_user_prompt(question, retrieved_chunks),
            max_output_tokens=650,
        )
        return response.output_text.strip()
