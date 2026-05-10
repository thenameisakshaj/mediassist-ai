import json
from collections import OrderedDict
from urllib.parse import urlparse

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

WEB_FALLBACK_SYSTEM_PROMPT = """
You are MediAssist AI's trusted medical web fallback.
Use only trusted medical web search results from the configured allowed domains.
Do not use general model memory.

Rules:
- Start by saying the indexed medical book did not provide enough relevant context.
- Say the answer is based on trusted medical web sources.
- Keep the answer short, educational, and non-diagnostic.
- Do not prescribe medication or claim treatment certainty.
- If the sources do not support the answer, say the context is insufficient.
- For emergency warning signs, advise urgent professional care without diagnosing.
- End with a brief educational-use safety reminder.
""".strip()


class OpenAIAnswerClient:
    _normalization_cache: OrderedDict[str, dict] = OrderedDict()

    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = Config.OPENAI_MODEL
        self.chat_fallback_model = Config.OPENAI_CHAT_FALLBACK_MODEL
        self.normalization_model = Config.OPENAI_NORMALIZATION_MODEL
        self.web_fallback_model = Config.WEB_FALLBACK_MODEL

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

    @staticmethod
    def _domain_from_url(url: str) -> str:
        hostname = urlparse(str(url or "")).hostname or ""
        return hostname.lower().removeprefix("www.")

    @staticmethod
    def _matches_trusted_parent_domain(domain: str, allowed_domains: list[str]) -> bool:
        clean_domain = str(domain or "").lower().removeprefix("www.")
        return any(
            clean_domain == allowed or clean_domain.endswith(f".{allowed}")
            for allowed in allowed_domains
        )

    @classmethod
    def _is_allowed_domain(cls, domain: str, allowed_domains: list[str]) -> bool:
        clean_domain = str(domain or "").lower().removeprefix("www.")
        # Keep the fallback demo-ready by hiding test/staging/dev subdomains
        # even when their parent domain is on the medical trust list.
        if clean_domain.startswith(("test-", "test.", "staging.", "dev.")):
            return False
        return cls._matches_trusted_parent_domain(clean_domain, allowed_domains)

    @classmethod
    def _extract_web_sources(cls, response: object) -> list[dict]:
        try:
            response_payload = response.model_dump()
        except AttributeError:
            response_payload = response if isinstance(response, dict) else {}

        found_sources: list[dict] = []
        seen_urls: set[str] = set()

        def visit(value: object) -> None:
            if isinstance(value, dict):
                url = value.get("url")
                title = value.get("title") or value.get("name") or value.get("source")
                if url:
                    domain = cls._domain_from_url(str(url))
                    if str(url) not in seen_urls:
                        seen_urls.add(str(url))
                        found_sources.append(
                            {
                                "title": clean_text(title or domain),
                                "url": str(url),
                                "domain": domain,
                            }
                        )

                for nested_value in value.values():
                    visit(nested_value)
            elif isinstance(value, list):
                for item in value:
                    visit(item)

        visit(response_payload)
        return found_sources

    @classmethod
    def _extract_trusted_web_sources(cls, response: object, allowed_domains: list[str]) -> list[dict]:
        found_sources = [
            source
            for source in cls._extract_web_sources(response)
            if cls._is_allowed_domain(source.get("domain", ""), allowed_domains)
        ]
        return found_sources[: Config.WEB_FALLBACK_MAX_SOURCES]

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

    def search_trusted_medical_web(
        self,
        query: str,
        language: str | None = None,
    ) -> dict:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        allowed_domains = Config.WEB_FALLBACK_ALLOWED_DOMAINS
        language_instruction = {
            "hindi": "Answer in simple Hindi.",
            "hinglish": "Answer in natural Hinglish using Roman script.",
        }.get(language or "english", "Answer in English.")

        response_input = (
            "Search trusted medical sources and answer this medical question. "
            "Use only search results from these allowed medical domains: "
            f"{', '.join(allowed_domains)}. "
            f"{language_instruction}\n\n"
            f"Medical question: {clean_text(query)}"
        )
        filtered_tool = {
            "type": "web_search",
            "filters": {"allowed_domains": allowed_domains},
        }
        unfiltered_tool = {"type": "web_search"}

        try:
            response = self.client.responses.create(
                model=self.web_fallback_model,
                instructions=WEB_FALLBACK_SYSTEM_PROMPT,
                tools=[filtered_tool],
                tool_choice="auto",
                include=["web_search_call.action.sources"],
                input=response_input,
                max_output_tokens=700,
            )
        except Exception as exc:
            if "filters" not in str(exc).lower():
                raise

            logger.warning(
                "Web fallback model rejected domain filters. Retrying and validating returned domains."
            )
            response = self.client.responses.create(
                model=self.web_fallback_model,
                instructions=WEB_FALLBACK_SYSTEM_PROMPT,
                tools=[unfiltered_tool],
                tool_choice="auto",
                include=["web_search_call.action.sources"],
                input=response_input,
                max_output_tokens=700,
            )

        answer = clean_text(getattr(response, "output_text", ""))
        all_sources = self._extract_web_sources(response)
        sources = self._extract_trusted_web_sources(response, allowed_domains)
        untrusted_sources = [
            source
            for source in all_sources
            if not self._matches_trusted_parent_domain(
                source.get("domain", ""),
                allowed_domains,
            )
        ]

        if not answer or not sources or untrusted_sources:
            if untrusted_sources:
                logger.info(
                    "Trusted web fallback rejected untrusted domains: %s",
                    [source.get("domain") for source in untrusted_sources],
                )
            return {"success": False, "answer": "", "web_sources": []}

        return {
            "success": True,
            "answer": answer,
            "web_sources": sources,
        }
