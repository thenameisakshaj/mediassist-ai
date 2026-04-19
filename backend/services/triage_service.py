import re

from services.clarification_service import detect_query_language, normalize_query_terms
from utils.helpers import clean_text

TRIAGE_LABELS = {
    0: "Informational",
    1: "Monitor",
    2: "Consult doctor",
    3: "Urgent",
}

INFORMATIONAL_PATTERNS = (
    r"\bwhat is\b",
    r"\bwhat are\b",
    r"\bwhat causes\b",
    r"\bcauses? of\b",
    r"\bexplain\b",
    r"\bdifference between\b",
    r"\bcompare\b",
    r"\bcomparison\b",
    r"\bdefine\b",
    r"\btell me about\b",
    r"\bsymptoms? of\b",
)

DURATION_PATTERNS = (
    r"\bfor \d+ days?\b",
    r"\bsince \d+ days?\b",
    r"\bpast few days\b",
    r"\bfrom last \d+ days?\b",
    r"\b\d+ din se\b",
    r"\bkal se\b",
    r"\bkayi din se\b",
    r"\bkaee din se\b",
    r"\bseveral days\b",
)

URGENT_PATTERNS = (
    r"\bcannot breathe\b",
    r"\bcan't breathe\b",
    r"\bcant breathe\b",
    r"\bdifficulty breathing\b",
    r"\btrouble breathing\b",
    r"\bbreathing trouble\b",
    r"\bloss of consciousness\b",
    r"\bunconscious\b",
    r"\bfainting\b",
    r"\bfainted\b",
    r"\bsevere bleeding\b",
    r"\bheavy bleeding\b",
    r"\bbleeding heavily\b",
    r"\bstroke symptoms?\b",
    r"\bone side of (?:my )?body is weak\b",
    r"\bone-sided weakness\b",
    r"\bsudden chest pain\b",
    r"\bchest pain with sweating\b",
    r"\bsaans nahi aa rahi\b",
    r"\bsaans nahi aa raha\b",
    r"\bsaans lene me bahut dikkat\b",
    r"\bbehosh\b",
    r"\bkhun bahut nikal raha\b",
    r"\bkhun bahut nikal rahi\b",
)

MODERATE_SEVERITY_PATTERNS = (
    r"\bhigh fever\b",
    r"\btez bukhar\b",
    r"\bsevere headache\b",
    r"\bsevere pain\b",
    r"\bbad pain\b",
    r"\bconstant pain\b",
    r"\bunbearable pain\b",
    r"\bworsening\b",
    r"\bnot going away\b",
    r"\bbreathing issue\b",
    r"\bsaans lene me dikkat\b",
    r"\bbreathing difficulty\b",
    r"\bsevere weakness\b",
)

SYMPTOM_CONTEXT_PATTERNS = (
    r"\bi have\b",
    r"\bi am having\b",
    r"\bi'm having\b",
    r"\bi feel\b",
    r"\bi am feeling\b",
    r"\bi'm feeling\b",
    r"\bi also have\b",
    r"\bmy\b",
    r"\bmujhe\b",
    r"\bmuje\b",
    r"\bmera\b",
    r"\bmere\b",
    r"\bmeri\b",
    r"\bho raha\b",
    r"\bho rahi\b",
    r"\bho rahe\b",
    r"\baa raha\b",
    r"\baa rahi\b",
)

MEDICAL_HINT_PATTERNS = (
    r"\basthma\b",
    r"\banemia\b",
    r"\bdiabetes\b",
    r"\bfever\b",
    r"\bbukhar\b",
    r"\bbhukar\b",
    r"\bheadache\b",
    r"\bsir dard\b",
    r"\bsardard\b",
    r"\bstomach pain\b",
    r"\bpet dard\b",
    r"\bpet me jalan\b",
    r"\bgastritis\b",
    r"\bcough\b",
    r"\bkhansi\b",
    r"\bweakness\b",
    r"\bkamzori\b",
    r"\bbreathing\b",
    r"\bsaans\b",
    r"\bchest pain\b",
    r"\bstroke\b",
    r"\bbleeding\b",
    r"\bunconscious\b",
)

SYMPTOM_GROUP_PATTERNS = {
    "fever": (r"\bfever\b", r"\bbukhar\b", r"\bbhukar\b", r"\btez bukhar\b"),
    "headache": (r"\bheadache\b", r"\bsir dard\b", r"\bsardard\b", r"\bmigraine\b"),
    "abdominal": (
        r"\bstomach pain\b",
        r"\bstomachache\b",
        r"\babdominal pain\b",
        r"\bpet dard\b",
        r"\bpet me dard\b",
        r"\bpet me jalan\b",
        r"\bjalan\b",
        r"\bgastritis\b",
    ),
    "respiratory": (
        r"\bbreathing issue\b",
        r"\bbreathing difficulty\b",
        r"\bdifficulty breathing\b",
        r"\bshortness of breath\b",
        r"\bsaans lene me dikkat\b",
        r"\bsaans nahi aa rahi\b",
        r"\bsaans nahi aa raha\b",
        r"\bcough\b",
        r"\bkhansi\b",
    ),
    "weakness": (r"\bweak\b", r"\bweakness\b", r"\bkamzori\b", r"\bthakan\b", r"\bfatigue\b"),
    "bleeding": (r"\bbleeding\b", r"\bkhun\b"),
    "chest_pain": (r"\bchest pain\b", r"\bseene me dard\b"),
    "consciousness": (r"\bfainting\b", r"\bfainted\b", r"\bunconscious\b", r"\bbehosh\b"),
}


class MedicalTriageService:
    @staticmethod
    def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(pattern, text) for pattern in patterns)

    @staticmethod
    def _find_symptom_groups(text: str) -> list[str]:
        matches = []
        for group, patterns in SYMPTOM_GROUP_PATTERNS.items():
            if any(re.search(pattern, text) for pattern in patterns):
                matches.append(group)
        return matches

    @staticmethod
    def _looks_like_short_symptom_statement(text: str) -> bool:
        words = re.findall(r"[a-zA-Z0-9]+", text)
        if not words or len(words) > 9:
            return False
        return not MedicalTriageService._contains_any(text, INFORMATIONAL_PATTERNS)

    @staticmethod
    def _build_result(level: int, reason: str, guidance: str | None = None) -> dict:
        return {
            "need_level": level,
            "need_label": TRIAGE_LABELS[level],
            "care_guidance": guidance,
            "suggest_nearby_care": level >= 2,
            "triage_reason": reason,
        }

    def assess(
        self,
        raw_query: str,
        normalized_query: str | None = None,
        detected_language: str | None = None,
        medical_topic: str | None = None,
    ) -> dict:
        raw_text = clean_text(raw_query).lower()
        normalized_text = clean_text(normalized_query).lower()
        normalized_raw_text = normalize_query_terms(raw_text).lower()
        language = detected_language or detect_query_language(raw_query)

        combined_parts = [part for part in (raw_text, normalized_raw_text, normalized_text) if part]
        combined_text = " | ".join(dict.fromkeys(combined_parts))

        has_urgent_combo = (
            "chest pain" in combined_text
            and (
                "difficulty breathing" in combined_text
                or "cannot breathe" in combined_text
                or "can't breathe" in combined_text
                or "saans nahi aa rahi" in raw_text
            )
        )
        if has_urgent_combo or self._contains_any(combined_text, URGENT_PATTERNS):
            return self._build_result(
                3,
                "urgent_warning_signs",
                "This may require urgent medical attention. Please seek immediate care.",
            )

        symptom_groups = self._find_symptom_groups(combined_text)
        has_duration = self._contains_any(raw_text, DURATION_PATTERNS) or self._contains_any(
            combined_text, DURATION_PATTERNS
        )
        has_moderate_severity = self._contains_any(raw_text, MODERATE_SEVERITY_PATTERNS) or self._contains_any(
            combined_text, MODERATE_SEVERITY_PATTERNS
        )
        has_symptom_context = self._contains_any(raw_text, SYMPTOM_CONTEXT_PATTERNS)
        looks_like_short_statement = self._looks_like_short_symptom_statement(raw_text)
        informational = self._contains_any(raw_text, INFORMATIONAL_PATTERNS)

        medical_signal = bool(medical_topic) or bool(symptom_groups) or self._contains_any(
            combined_text, MEDICAL_HINT_PATTERNS
        )

        # Symptom-based triage wins over informational phrasing when the user describes active symptoms.
        symptom_query = bool(symptom_groups) and (
            has_symptom_context or has_duration or has_moderate_severity or looks_like_short_statement
        )

        if symptom_query:
            if has_duration:
                return self._build_result(
                    2,
                    "persistent_symptoms",
                    "Since your symptoms have lasted several days, it may be a good idea to consult a doctor.",
                )
            if len(symptom_groups) >= 2:
                return self._build_result(
                    2,
                    "multiple_symptoms",
                    "Because you mentioned multiple ongoing symptoms, seeking medical advice may be appropriate.",
                )
            if has_moderate_severity or "respiratory" in symptom_groups or "chest_pain" in symptom_groups:
                return self._build_result(
                    2,
                    "moderate_or_function_affecting_symptoms",
                    "Because you described more concerning symptoms, it would be sensible to consult a doctor.",
                )
            return self._build_result(
                1,
                "mild_symptom_report",
                "Monitor your symptoms and seek medical advice if they persist or worsen.",
            )

        if not medical_signal:
            return self._build_result(0, "non_medical_or_out_of_scope")

        if informational or medical_topic or language in {"english", "hindi", "hinglish"}:
            return self._build_result(0, "informational_query")

        return self._build_result(0, "informational_query")
