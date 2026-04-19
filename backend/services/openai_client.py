import json
from collections import OrderedDict

from openai import OpenAI

from config import Config
from services.clarification_service import (
    detect_query_language,
    infer_likely_medical_topic,
    normalize_query_terms,
)
from services.prompt_builder import MEDICAL_SYSTEM_PROMPT, build_user_prompt
from utils.helpers import clean_text
from utils.logger import get_logger

logger = get_logger(__name__)

NORMALIZATION_SYSTEM_PROMPT = """
You normalize multilingual medical user queries for a retrieval system.
You must never answer the medical question.
Return only valid JSON with exactly these keys:
- language: one of english, hindi, hinglish
- normalized_query: concise English retrieval query
- medical_topic: short English medical topic string or null
- confidence: float between 0.0 and 1.0
- needs_clarification: true or false

Rules:
- Correct spelling mistakes conservatively.
- Understand English, Hindi, and Hinglish.
- Keep normalized_query medically relevant and concise.
- If the query is non-medical, vague, meta, or unrelated, do not force a medical topic.
- If correction is uncertain, set needs_clarification to true.
- Do not add explanations, markdown, or extra fields.
""".strip()

ALLOWED_LANGUAGES = {"english", "hindi", "hinglish"}


class OpenAIAnswerClient:
    _normalization_cache: OrderedDict[str, dict] = OrderedDict()

    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = Config.OPENAI_MODEL
        self.chat_fallback_model = Config.OPENAI_CHAT_FALLBACK_MODEL
        self.normalization_model = Config.OPENAI_NORMALIZATION_MODEL

    @staticmethod
    def _should_use_chat_fallback(exc: Exception) -> bool:
        message = str(exc).lower()
        return "api.responses.write" in message or (
            "responses" in message and "scope" in message
        )

    @staticmethod
    def _clamp_confidence(value: object, fallback: float = 0.0) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = float(fallback)
        return round(max(0.0, min(1.0, number)), 3)

    @staticmethod
    def _looks_english_query(text: str) -> bool:
        return bool(text) and not any("\u0900" <= char <= "\u097F" for char in text)

    @staticmethod
    def _extract_response_text(content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    parts.append(text)
                    continue
                if isinstance(item, dict) and item.get("text"):
                    parts.append(str(item["text"]))
            return "".join(parts)
        return str(content or "")

    @classmethod
    def _cache_get(cls, cache_key: str) -> dict | None:
        cached = cls._normalization_cache.get(cache_key)
        if not cached:
            return None
        cls._normalization_cache.move_to_end(cache_key)
        return dict(cached)

    @classmethod
    def _cache_set(cls, cache_key: str, value: dict) -> None:
        cls._normalization_cache[cache_key] = dict(value)
        cls._normalization_cache.move_to_end(cache_key)
        while len(cls._normalization_cache) > Config.NORMALIZATION_CACHE_SIZE:
            cls._normalization_cache.popitem(last=False)

    def _build_normalization_fallback(self, query: str) -> dict:
        normalized_query = clean_text(normalize_query_terms(query)) or clean_text(query)
        topic_guess = infer_likely_medical_topic(query)
        language = detect_query_language(query)

        medical_topic = topic_guess.get("topic") if topic_guess else None
        confidence = 0.0
        needs_clarification = False

        if topic_guess:
            confidence = topic_guess.get("confidence", 0.0)
            normalized_query = clean_text(topic_guess.get("normalized_query") or normalized_query)
            if topic_guess.get("method") == "direct_topic":
                confidence = 0.82
            else:
                confidence = min(confidence, 0.44)
                needs_clarification = True

        return {
            "language": language,
            "normalized_query": normalized_query or clean_text(query),
            "medical_topic": medical_topic,
            "confidence": self._clamp_confidence(confidence),
            "needs_clarification": needs_clarification,
        }

    def _sanitize_normalization_result(self, payload: object, query: str) -> dict:
        fallback = self._build_normalization_fallback(query)
        if not isinstance(payload, dict):
            return fallback

        language = clean_text(payload.get("language", fallback["language"])).lower()
        if language not in ALLOWED_LANGUAGES:
            language = fallback["language"]

        normalized_query = clean_text(payload.get("normalized_query", fallback["normalized_query"]))
        if not normalized_query:
            normalized_query = fallback["normalized_query"]
        if not self._looks_english_query(normalized_query):
            normalized_query = fallback["normalized_query"]

        medical_topic = payload.get("medical_topic")
        if medical_topic is None:
            cleaned_topic = None
        else:
            cleaned_topic = clean_text(medical_topic)
            medical_topic = cleaned_topic if cleaned_topic.lower() != "null" else None

        if medical_topic and medical_topic.lower() not in normalized_query.lower():
            medical_topic = medical_topic.lower()
        elif medical_topic:
            medical_topic = medical_topic.lower()

        confidence = self._clamp_confidence(payload.get("confidence"), fallback["confidence"])
        needs_clarification = payload.get("needs_clarification")
        if not isinstance(needs_clarification, bool):
            needs_clarification = fallback["needs_clarification"]

        if not medical_topic:
            guess = infer_likely_medical_topic(normalized_query)
            if guess and guess.get("confidence", 0.0) >= 0.78:
                medical_topic = guess["topic"]

        if confidence < Config.NORMALIZATION_MEDIUM_CONFIDENCE and medical_topic:
            needs_clarification = True

        return {
            "language": language,
            "normalized_query": normalized_query,
            "medical_topic": medical_topic,
            "confidence": confidence,
            "needs_clarification": needs_clarification,
        }

    def normalize_user_query(self, query: str) -> dict:
        cleaned_query = clean_text(query)
        cache_key = cleaned_query.lower()
        if not cleaned_query:
            return self._build_normalization_fallback(query)

        cached = self._cache_get(cache_key)
        if cached:
            return cached

        fallback = self._build_normalization_fallback(cleaned_query)
        if not self.client:
            self._cache_set(cache_key, fallback)
            return dict(fallback)

        try:
            response = self.client.chat.completions.create(
                model=self.normalization_model,
                messages=[
                    {"role": "system", "content": NORMALIZATION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Normalize this query for medical retrieval and return JSON only:\n{cleaned_query}",
                    },
                ],
                temperature=0,
                response_format={"type": "json_object"},
                max_completion_tokens=220,
            )
            content = self._extract_response_text(response.choices[0].message.content)
            parsed = json.loads(content)
            normalized = self._sanitize_normalization_result(parsed, cleaned_query)
            self._cache_set(cache_key, normalized)
            return dict(normalized)
        except Exception as exc:
            logger.warning("Query normalization failed; using conservative fallback: %s", exc)
            self._cache_set(cache_key, fallback)
            return dict(fallback)

    def _generate_with_chat_completions(
        self,
        user_question: str,
        normalized_query: str,
        retrieved_chunks: list[dict],
        answer_language: str,
    ) -> str:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        response = self.client.chat.completions.create(
            model=self.chat_fallback_model,
            messages=[
                {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_user_prompt(
                        user_question,
                        retrieved_chunks,
                        normalized_query=normalized_query,
                        answer_language=answer_language,
                    ),
                },
            ],
            max_completion_tokens=650,
        )
        return self._extract_response_text(response.choices[0].message.content).strip()

    def generate_answer(
        self,
        user_question: str,
        normalized_query: str,
        retrieved_chunks: list[dict],
        answer_language: str = "english",
    ) -> str:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=MEDICAL_SYSTEM_PROMPT,
                input=build_user_prompt(
                    user_question,
                    retrieved_chunks,
                    normalized_query=normalized_query,
                    answer_language=answer_language,
                ),
                max_output_tokens=650,
            )
            return response.output_text.strip()
        except Exception as exc:
            if not self._should_use_chat_fallback(exc):
                raise

            logger.warning(
                "Responses API was unavailable for this request. Falling back to chat completions."
            )
            return self._generate_with_chat_completions(
                user_question,
                normalized_query,
                retrieved_chunks,
                answer_language,
            )
