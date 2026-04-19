import re

from config import Config
from services.clarification_service import (
    build_clarification,
    clarification_store,
    infer_likely_medical_topic,
    is_affirmative_reply,
    is_negative_reply,
    suggest_clarification,
)
from services.openai_client import OpenAIAnswerClient
from services.prompt_builder import (
    build_source_payload,
    extract_comparison_terms,
    get_requested_answer_style,
)
from services.retriever import MedicalRetriever
from services.triage_service import MedicalTriageService
from utils.helpers import clean_text, is_emergency_message, snippet
from utils.logger import get_logger

INSUFFICIENT_CONTEXT_ANSWER = (
    "I do not have enough relevant medical-book context to answer that confidently."
)

URGENT_CARE_NOTE = (
    "If this involves severe symptoms, breathing difficulty, chest pain, stroke signs, "
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
        self.answer_client = OpenAIAnswerClient()
        self.triage_service = MedicalTriageService()

    @staticmethod
    def _build_warning(question: str) -> str:
        if is_emergency_message(question):
            return f"{Config.SAFETY_WARNING} {URGENT_CARE_NOTE}"
        return Config.SAFETY_WARNING

    @staticmethod
    def _is_refusal_answer(answer: str) -> bool:
        return clean_text(answer).lower().startswith(INSUFFICIENT_CONTEXT_ANSWER.lower())

    @staticmethod
    def _compact_text(value: str) -> str:
        return re.sub(r"[ \t]+", " ", str(value or "")).strip()

    @staticmethod
    def _build_response(
        answer: str,
        sources: list[dict],
        warning_question: str,
        triage: dict,
    ) -> dict:
        response = {
            "answer": answer,
            "sources": sources,
            "warning": ChatbotService._build_warning(warning_question),
            "need_level": triage.get("need_level", 0),
            "need_label": triage.get("need_label", "Informational"),
            "care_guidance": triage.get("care_guidance"),
            "suggest_nearby_care": bool(triage.get("suggest_nearby_care", False)),
            "triage_reason": triage.get("triage_reason"),
        }
        return response

    @staticmethod
    def _log_query_pipeline(
        raw_question: str,
        normalized_query: str,
        language: str,
        confidence: float,
        fallback_used: bool,
        clarification: bool,
        refusal: bool,
        reason: str,
        triage: dict,
    ) -> None:
        logger.info(
            "Query pipeline | raw=%r | normalized=%r | language=%s | confidence=%.2f | fallback_retrieval=%s | clarification=%s | refusal=%s | need_level=%s | need_label=%s | triage_reason=%s | reason=%s",
            raw_question,
            normalized_query,
            language,
            confidence,
            fallback_used,
            clarification,
            refusal,
            triage.get("need_level", 0),
            triage.get("need_label", "Informational"),
            triage.get("triage_reason", "unknown"),
            reason,
        )

    def _split_answer_sections(self, answer: str) -> tuple[str, str]:
        paragraphs = [
            paragraph.strip()
            for paragraph in str(answer or "").split("\n\n")
            if paragraph.strip()
        ]
        body_parts = []
        tail_parts = []
        tail_markers = (
            "educational use only.",
            "if you want",
            "if you'd like",
            "please consult",
            "the source context is limited",
            "source context is limited",
        )

        for paragraph in paragraphs:
            lowered = paragraph.lower()
            if lowered.startswith(tail_markers) or tail_parts:
                tail_parts.append(paragraph)
            else:
                body_parts.append(paragraph)

        body = "\n\n".join(body_parts) if body_parts else self._compact_text(answer)
        tail = "\n\n".join(tail_parts)
        return body, tail

    @staticmethod
    def _has_bullet_list(text: str) -> bool:
        return bool(re.search(r"(?m)^\s*[-*]\s+", text))

    @staticmethod
    def _has_numbered_list(text: str) -> bool:
        return bool(re.search(r"(?m)^\s*\d+\.\s+", text))

    @staticmethod
    def _has_comparison_headings(text: str) -> bool:
        return text.count("### ") >= 2 or "## " in text

    def _collect_points(self, text: str, max_items: int = 8) -> list[str]:
        if self._has_bullet_list(text):
            items = [
                self._compact_text(re.sub(r"^\s*[-*]\s+", "", line))
                for line in text.splitlines()
                if re.match(r"^\s*[-*]\s+", line)
            ]
            return [item for item in items if item][:max_items]

        if self._has_numbered_list(text):
            items = [
                self._compact_text(re.sub(r"^\s*\d+\.\s+", "", line))
                for line in text.splitlines()
                if re.match(r"^\s*\d+\.\s+", line)
            ]
            return [item for item in items if item][:max_items]

        paragraphs = [
            self._compact_text(paragraph)
            for paragraph in re.split(r"\n{2,}", text)
            if self._compact_text(paragraph)
        ]
        items: list[str] = []
        for paragraph in paragraphs:
            sentence_candidates = re.split(r"(?<=[.!?])\s+", paragraph)
            segments = (
                sentence_candidates
                if len(paragraphs) <= 2 and len(sentence_candidates) > 1
                else [paragraph]
            )
            for segment in segments:
                cleaned = self._compact_text(segment.strip("- "))
                if cleaned and cleaned not in items:
                    items.append(cleaned)
                if len(items) >= max_items:
                    return items
        return items[:max_items]

    def _normalize_bullets(self, answer: str) -> str:
        body, tail = self._split_answer_sections(answer)
        if self._has_bullet_list(body):
            return answer

        items = self._collect_points(body)
        if not items:
            return answer

        normalized = "\n".join(f"- {item}" for item in items)
        return f"{normalized}\n\n{tail}".strip() if tail else normalized

    def _normalize_numbered(self, answer: str) -> str:
        body, tail = self._split_answer_sections(answer)
        if self._has_numbered_list(body):
            return answer

        items = self._collect_points(body)
        if not items:
            return answer

        normalized = "\n".join(
            f"{index}. {item}" for index, item in enumerate(items, start=1)
        )
        return f"{normalized}\n\n{tail}".strip() if tail else normalized

    def _normalize_comparison(self, answer: str, question: str) -> str:
        body, tail = self._split_answer_sections(answer)
        if self._has_comparison_headings(body):
            return answer

        items = self._collect_points(body, max_items=10)
        if not items:
            return answer

        terms = extract_comparison_terms(question)
        if not terms:
            generic = "## Comparison\n\n" + "\n".join(f"- {item}" for item in items)
            return f"{generic}\n\n{tail}".strip() if tail else generic

        left, right = terms
        left_phrase = left.lower()
        right_phrase = right.lower()
        left_tokens = {
            token
            for token in re.findall(r"[a-zA-Z0-9]+", left_phrase)
            if len(token) >= 2
        }
        right_tokens = {
            token
            for token in re.findall(r"[a-zA-Z0-9]+", right_phrase)
            if len(token) >= 2
        }
        shared_tokens = left_tokens & right_tokens
        left_tokens -= shared_tokens
        right_tokens -= shared_tokens

        left_items = []
        right_items = []
        common_items = []
        for item in items:
            lowered = item.lower()
            left_hit = left_phrase in lowered or any(token in lowered for token in left_tokens)
            right_hit = right_phrase in lowered or any(token in lowered for token in right_tokens)
            if left_hit and not right_hit:
                left_items.append(item)
            elif right_hit and not left_hit:
                right_items.append(item)
            else:
                common_items.append(item)

        if not left_items and common_items:
            left_items.append(common_items.pop(0))
        if not right_items and common_items:
            right_items.append(common_items.pop(0))

        sections = [f"## {left} vs {right}"]
        if left_items:
            sections.append("\n".join([f"### {left}", *[f"- {item}" for item in left_items]]))
        if right_items:
            sections.append("\n".join([f"### {right}", *[f"- {item}" for item in right_items]]))
        if common_items:
            sections.append("\n".join(["### Key points", *[f"- {item}" for item in common_items]]))

        normalized = "\n\n".join(sections)
        return f"{normalized}\n\n{tail}".strip() if tail else normalized

    def _enforce_requested_format(self, answer: str, question: str) -> str:
        style = get_requested_answer_style(question)
        if style == "bullets":
            return self._normalize_bullets(answer)
        if style == "numbered":
            return self._normalize_numbered(answer)
        if style == "comparison":
            return self._normalize_comparison(answer, question)
        return answer

    def _format_grounded_summary(self, excerpts: list[str], question: str) -> str:
        style = get_requested_answer_style(question)
        cleaned_excerpts = [clean_text(excerpt) for excerpt in excerpts if clean_text(excerpt)]
        if not cleaned_excerpts:
            return INSUFFICIENT_CONTEXT_ANSWER

        if style == "comparison":
            terms = extract_comparison_terms(question)
            if terms:
                left, right = terms
                left_items = [
                    excerpt for excerpt in cleaned_excerpts if left.lower() in excerpt.lower()
                ]
                right_items = [
                    excerpt for excerpt in cleaned_excerpts if right.lower() in excerpt.lower()
                ]
                common_items = [
                    excerpt
                    for excerpt in cleaned_excerpts
                    if excerpt not in left_items and excerpt not in right_items
                ]
                sections = [f"## {left} vs {right}"]
                if left_items:
                    sections.append(
                        "\n".join([f"### {left}", *[f"- {excerpt}" for excerpt in left_items]])
                    )
                if right_items:
                    sections.append(
                        "\n".join([f"### {right}", *[f"- {excerpt}" for excerpt in right_items]])
                    )
                if common_items:
                    sections.append(
                        "\n".join(["### Key points", *[f"- {excerpt}" for excerpt in common_items]])
                    )
                sections.append("The source context is limited to the retrieved textbook excerpts.")
                return "\n\n".join(sections)

        if style == "numbered":
            steps = "\n".join(
                f"{index}. {excerpt}"
                for index, excerpt in enumerate(cleaned_excerpts[:6], start=1)
            )
            return (
                "Here is a step-by-step explanation from the retrieved medical-book context:\n\n"
                f"{steps}\n\n"
                "The source context is limited to the retrieved textbook excerpts."
            )

        if style == "bullets":
            bullet_lines = "\n".join(f"- {excerpt}" for excerpt in cleaned_excerpts[:6])
            return (
                "Here are the main points from the retrieved medical-book context:\n\n"
                f"{bullet_lines}\n\n"
                "The source context is limited to the retrieved textbook excerpts."
            )

        lead = cleaned_excerpts[0]
        if len(cleaned_excerpts) == 1:
            return f"{lead}\n\nThe source context is limited to the retrieved textbook excerpts."

        additional = "\n".join(f"- {excerpt}" for excerpt in cleaned_excerpts[1:4])
        return (
            f"{lead}\n\n"
            "Additional context from the retrieved medical-book excerpts:\n"
            f"{additional}\n\n"
            "The source context is limited to the retrieved textbook excerpts."
        )

    def _build_grounded_summary(self, retrieved_chunks: list[dict], question: str) -> str:
        excerpts = [snippet(chunk.get("text", ""), 220) for chunk in retrieved_chunks[:4]]
        summary = self._format_grounded_summary(excerpts, question)
        return self._enforce_requested_format(summary, question)

    def _build_retrieval_fallback(self, retrieved_chunks: list[dict], question: str) -> str:
        grounded_summary = self._build_grounded_summary(retrieved_chunks, question)
        if self._is_refusal_answer(grounded_summary):
            return INSUFFICIENT_CONTEXT_ANSWER

        answer = f"{OPENAI_UNAVAILABLE_NOTE}\n\n{grounded_summary}"
        if is_emergency_message(question):
            answer += f"\n\nUrgent note: {URGENT_CARE_NOTE}"
        return answer

    def _resolve_pending_clarification(self, session_key: str, raw_question: str) -> tuple[str | None, dict]:
        pending = clarification_store.get(session_key)
        if not pending:
            return raw_question, {
                "preferred_language": None,
                "style_question": raw_question,
            }

        if is_affirmative_reply(raw_question):
            clarification_store.clear(session_key)
            return pending["corrected_query"], {
                "preferred_language": pending.get("language"),
                "style_question": pending.get("original_query") or pending["corrected_query"],
            }

        if is_negative_reply(raw_question):
            clarification_store.clear(session_key)
            return None, {
                "preferred_language": pending.get("language"),
                "style_question": pending.get("original_query") or raw_question,
                "clarification_rejected": True,
            }

        clarification_store.clear(session_key)
        return raw_question, {
            "preferred_language": None,
            "style_question": raw_question,
        }

    def _maybe_prompt_for_clarification(self, session_key: str, raw_question: str, language: str, normalization: dict) -> dict | None:
        confidence = normalization.get("confidence", 0.0)
        suggested_topic = normalization.get("medical_topic")
        corrected_query = normalization.get("normalized_query")
        needs_clarification = bool(normalization.get("needs_clarification"))

        clarification = None
        if suggested_topic and (
            confidence < Config.NORMALIZATION_MEDIUM_CONFIDENCE
            or (needs_clarification and confidence < Config.NORMALIZATION_HIGH_CONFIDENCE)
        ):
            clarification = build_clarification(
                raw_question,
                suggested_topic,
                corrected_query=corrected_query,
            )

        if not clarification and confidence < Config.NORMALIZATION_MEDIUM_CONFIDENCE:
            clarification = suggest_clarification(raw_question)

        if not clarification:
            return None

        clarification_store.set(
            session_key,
            clarification["corrected_query"],
            clarification["suggested_term"],
            original_query=raw_question,
            language=language,
        )
        return {
            "answer": clarification["prompt"],
            "sources": [],
            "warning": self._build_warning(raw_question),
        }

    def _select_context_assessment(self, raw_question: str, normalized_query: str, confidence: float) -> tuple[dict, bool]:
        fallback_used = False
        normalized_text = clean_text(normalized_query)
        raw_text = clean_text(raw_question)

        if confidence >= Config.NORMALIZATION_HIGH_CONFIDENCE and normalized_text:
            return self.retriever.assess_context(normalized_text, retrieval_query=normalized_text), False

        if confidence >= Config.NORMALIZATION_MEDIUM_CONFIDENCE and normalized_text:
            primary = self.retriever.assess_context(normalized_text, retrieval_query=normalized_text)
            if primary.get("is_sufficient") or normalized_text.lower() == raw_text.lower():
                return primary, False

            fallback = self.retriever.assess_context(normalized_text, retrieval_query=raw_text)
            if fallback.get("is_sufficient"):
                return fallback, True
            if fallback.get("top_similarity", 0.0) > primary.get("top_similarity", 0.0):
                fallback_used = True
                return fallback, fallback_used
            return primary, False

        return self.retriever.assess_context(raw_text, retrieval_query=raw_text), False

    def answer(self, raw_message: str, session_id: str | None = None) -> dict:
        raw_question = clean_text(raw_message)
        if not raw_question:
            raise ValueError("Message is required.")
        if len(raw_question) > 1500:
            raise ValueError("Message is too long. Please keep it under 1500 characters.")

        session_key = clean_text(session_id) or "default"
        question, pending_meta = self._resolve_pending_clarification(session_key, raw_question)
        style_question = pending_meta.get("style_question") or raw_question

        if pending_meta.get("clarification_rejected"):
            triage = self.triage_service.assess(
                style_question,
                detected_language=pending_meta.get("preferred_language"),
            )
            self._log_query_pipeline(
                raw_question,
                "",
                pending_meta.get("preferred_language") or "english",
                0.0,
                False,
                True,
                True,
                "clarification_rejected",
                triage,
            )
            return self._build_response(
                INSUFFICIENT_CONTEXT_ANSWER,
                [],
                style_question,
                triage,
            )

        effective_question = question or raw_question

        normalization = self.answer_client.normalize_user_query(effective_question)
        if pending_meta.get("preferred_language") in {"hindi", "hinglish"}:
            normalization["language"] = pending_meta["preferred_language"]

        answer_language = normalization.get("language", "english")
        normalized_query = clean_text(normalization.get("normalized_query") or effective_question)
        confidence = float(normalization.get("confidence", 0.0))

        heuristic_topic = infer_likely_medical_topic(style_question)
        if heuristic_topic and heuristic_topic.get("confidence", 0.0) >= 0.80:
            heuristic_name = heuristic_topic["topic"]
            model_topic = clean_text(normalization.get("medical_topic") or "").lower()
            if heuristic_name not in normalized_query.lower() and heuristic_name != model_topic:
                normalization["medical_topic"] = heuristic_name
                normalization["normalized_query"] = clean_text(
                    heuristic_topic.get("normalized_query") or heuristic_name
                )
                normalization["confidence"] = round(
                    min(confidence, Config.NORMALIZATION_MEDIUM_CONFIDENCE - 0.01),
                    3,
                )
                normalization["needs_clarification"] = True
                normalized_query = normalization["normalized_query"]
                confidence = float(normalization["confidence"])

        triage = self.triage_service.assess(
            style_question,
            normalized_query=normalized_query,
            detected_language=answer_language,
            medical_topic=normalization.get("medical_topic"),
        )

        # Urgent symptom signals should not be delayed by a typo clarification prompt.
        clarification_response = None
        if triage.get("need_level", 0) < 3:
            clarification_response = self._maybe_prompt_for_clarification(
                session_key,
                style_question,
                answer_language,
                normalization,
            )
        if clarification_response:
            self._log_query_pipeline(
                raw_question,
                normalized_query,
                answer_language,
                confidence,
                False,
                True,
                False,
                "clarification_prompted",
                triage,
            )
            return self._build_response(
                clarification_response["answer"],
                [],
                style_question,
                triage,
            )

        context_assessment, fallback_used = self._select_context_assessment(
            effective_question,
            normalized_query,
            confidence,
        )
        retrieved_chunks = context_assessment.get("accepted_chunks", [])
        strict_refusal = not context_assessment.get("is_sufficient")

        if strict_refusal:
            self._log_query_pipeline(
                raw_question,
                normalized_query,
                answer_language,
                confidence,
                fallback_used,
                False,
                True,
                context_assessment.get("reason", "unknown"),
                triage,
            )
            return self._build_response(
                INSUFFICIENT_CONTEXT_ANSWER,
                [],
                style_question,
                triage,
            )

        try:
            answer = self.answer_client.generate_answer(
                style_question,
                normalized_query,
                retrieved_chunks,
                answer_language=answer_language,
            )
        except Exception as exc:
            logger.warning("OpenAI generation failed, falling back to retrieved context: %s", exc)
            answer = self._build_retrieval_fallback(retrieved_chunks, style_question)

        if self._is_refusal_answer(answer) and retrieved_chunks:
            strongest_similarity = context_assessment.get("top_similarity", 0.0)
            if strongest_similarity >= Config.STRONG_RELEVANCE_SCORE:
                logger.info(
                    "Model returned refusal despite strong context for question %r. Using grounded summary.",
                    raw_question,
                )
                answer = self._build_grounded_summary(retrieved_chunks, style_question)

        if not self._is_refusal_answer(answer):
            answer = self._enforce_requested_format(answer, style_question)

        if is_emergency_message(style_question) and "emergency" not in answer.lower():
            answer = f"{answer}\n\nUrgent note: {URGENT_CARE_NOTE}"

        refusal_response = self._is_refusal_answer(answer)
        self._log_query_pipeline(
            raw_question,
            normalized_query,
            answer_language,
            confidence,
            fallback_used,
            False,
            refusal_response,
            context_assessment.get("reason", "accepted"),
            triage,
        )
        return self._build_response(
            INSUFFICIENT_CONTEXT_ANSWER if refusal_response else answer,
            [] if refusal_response else build_source_payload(retrieved_chunks),
            style_question,
            triage,
        )

