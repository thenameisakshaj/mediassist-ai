import re
from difflib import SequenceMatcher, get_close_matches
from time import time

from utils.helpers import clean_text

COMMON_MEDICAL_TOPICS = {
    "acne",
    "addiction",
    "adenoid",
    "adhd",
    "aids",
    "albinism",
    "alcoholism",
    "allergy",
    "alopecia",
    "alzheimer",
    "amenorrhea",
    "amnesia",
    "amputation",
    "anaphylaxis",
    "anemia",
    "aneurysm",
    "angina",
    "anorexia",
    "anosmia",
    "anxiety",
    "appendicitis",
    "arrhythmia",
    "arthritis",
    "arthroscopy",
    "asthma",
    "atherosclerosis",
    "autism",
    "backache",
    "backpain",
    "baldness",
    "bedsores",
    "bipolar",
    "bladder",
    "bleeding",
    "blindness",
    "bloating",
    "bloodpressure",
    "boils",
    "bonecancer",
    "botulism",
    "bronchitis",
    "bruise",
    "bulimia",
    "burns",
    "bursitis",
    "cancer",
    "candidiasis",
    "carbuncle",
    "caries",
    "cataract",
    "celiac",
    "cellulitis",
    "cerebralpalsy",
    "cervicalcancer",
    "chickenpox",
    "chlamydia",
    "cholera",
    "cholesterol",
    "cholecystitis",
    "cirrhosis",
    "cold",
    "colic",
    "colitis",
    "coloncancer",
    "coma",
    "concussion",
    "conjunctivitis",
    "constipation",
    "copd",
    "coronaryarterydisease",
    "covid",
    "cramps",
    "crohn",
    "croup",
    "cyst",
    "cystitis",
    "deafness",
    "dehydration",
    "dementia",
    "dengue",
    "depression",
    "dermatitis",
    "diabetes",
    "diarrhea",
    "diphtheria",
    "dizziness",
    "downsyndrome",
    "dysentery",
    "dyslexia",
    "eczema",
    "edema",
    "emphysema",
    "encephalitis",
    "endometriosis",
    "epilepsy",
    "erectiledysfunction",
    "fever",
    "fibromyalgia",
    "flu",
    "fracture",
    "fungalinfection",
    "gallstones",
    "gastritis",
    "gastroenteritis",
    "gerd",
    "gingivitis",
    "glaucoma",
    "goiter",
    "gonorrhea",
    "gout",
    "headache",
    "hearingloss",
    "heartattack",
    "heartdisease",
    "heartfailure",
    "hemorrhoids",
    "hepatitis",
    "hernia",
    "herpes",
    "highbloodpressure",
    "hiv",
    "hpv",
    "hyperglycemia",
    "hypertension",
    "hypoglycemia",
    "hypotension",
    "hypothyroidism",
    "impetigo",
    "indigestion",
    "infertility",
    "influenza",
    "insomnia",
    "irritablebowelsyndrome",
    "jaundice",
    "kidneydisease",
    "kidneystone",
    "laryngitis",
    "leprosy",
    "leukemia",
    "liverdisease",
    "lupus",
    "lymphoma",
    "malaria",
    "malnutrition",
    "measles",
    "meningitis",
    "menopause",
    "menstrualcramps",
    "migraine",
    "miscarriage",
    "mumps",
    "myopia",
    "nasalcancer",
    "nausea",
    "nephritis",
    "neuralgia",
    "obesity",
    "osteoarthritis",
    "osteomyelitis",
    "osteoporosis",
    "otitis",
    "ovariancancer",
    "pancreatitis",
    "paralysis",
    "parkinson",
    "pelvicinflammatorydisease",
    "periodpain",
    "periods",
    "piles",
    "pneumonia",
    "polio",
    "polycysticovarysyndrome",
    "pregnancy",
    "prematurity",
    "prostatecancer",
    "psoriasis",
    "ptsd",
    "rabies",
    "rash",
    "retinopathy",
    "rheumaticfever",
    "rheumatoidarthritis",
    "ringworm",
    "rosacea",
    "rubella",
    "scabies",
    "scarletfever",
    "schizophrenia",
    "seizure",
    "sepsis",
    "sinusitis",
    "skininfection",
    "smallpox",
    "sprain",
    "stomachache",
    "stomatitis",
    "stroke",
    "sunburn",
    "swineflu",
    "syphilis",
    "tachycardia",
    "tetanus",
    "thalassemia",
    "thyroid",
    "tonsillitis",
    "toothache",
    "tuberculosis",
    "tumor",
    "typhoid",
    "ulcer",
    "urinarytractinfection",
    "urticaria",
    "uterinefibroid",
    "vaginitis",
    "varicoseveins",
    "vertigo",
    "viralfever",
    "vomiting",
    "warts",
    "whoopingcough",
    "wound",
    "yeastinfection",
}

CLARIFICATION_IGNORE_TERMS = {
    "a",
    "about",
    "am",
    "an",
    "and",
    "answer",
    "answers",
    "are",
    "batao",
    "bataye",
    "batana",
    "bullet",
    "bullets",
    "can",
    "compare",
    "difference",
    "differences",
    "do",
    "does",
    "explain",
    "for",
    "hai",
    "hain",
    "how",
    "i",
    "in",
    "is",
    "ka",
    "ke",
    "ki",
    "kya",
    "list",
    "match",
    "matches",
    "me",
    "medical",
    "medicine",
    "mere",
    "mujhe",
    "muje",
    "my",
    "of",
    "or",
    "point",
    "points",
    "please",
    "question",
    "source",
    "sources",
    "step",
    "steps",
    "symptom",
    "symptoms",
    "tell",
    "the",
    "this",
    "vs",
    "versus",
    "what",
    "why",
}

AFFIRMATIVE_REPLIES = {
    "correct",
    "haan",
    "haan ji",
    "ha",
    "han",
    "han ji",
    "ji",
    "ok yes",
    "please do",
    "right",
    "yes",
    "yes please",
    "yep",
    "yup",
}

NEGATIVE_REPLIES = {
    "na",
    "nah",
    "nahi",
    "nahi ji",
    "no",
    "no thanks",
    "no thank you",
    "nope",
    "not that",
    "wrong",
}

ROMAN_HINDI_MEDICAL_MAP = {
    "bhukar": "fever",
    "bukhar": "fever",
    "buker": "fever",
    "chakkar": "vertigo",
    "daaney": "acne",
    "daane": "acne",
    "gale": "tonsillitis",
    "galedard": "tonsillitis",
    "gale dard": "tonsillitis",
    "ghabrahat": "anxiety",
    "jalan": "gastritis",
    "jukham": "flu",
    "kamzori": "anemia",
    "khansi": "bronchitis",
    "khaansi": "bronchitis",
    "khujli": "scabies",
    "petdard": "stomachache",
    "pet dard": "stomachache",
    "saans": "asthma",
    "saansphoolna": "asthma",
    "saans phoolna": "asthma",
    "sardi": "flu",
    "sardard": "headache",
    "sir dard": "headache",
    "thakan": "anemia",
    "ulti": "vomiting",
    "ultiyan": "vomiting",
    "zukham": "flu",
}

MULTI_WORD_ROMAN_HINDI_MAP = {
    "gale dard": "tonsillitis",
    "pet dard": "stomachache",
    "saans phoolna": "asthma",
    "sir dard": "headache",
}

HINDI_HINT_TERMS = {
    "bhukar",
    "bukhar",
    "hai",
    "haan",
    "han",
    "ji",
    "kya",
    "mujhe",
    "muje",
    "nahi",
    "saans",
    "sir",
}

DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")


class ClarificationStore:
    def __init__(self):
        self._pending: dict[str, dict] = {}

    def _purge_expired(self) -> None:
        now = time()
        expired_keys = [
            key
            for key, value in self._pending.items()
            if value.get("expires_at", 0) <= now
        ]
        for key in expired_keys:
            self._pending.pop(key, None)

    def get(self, session_id: str | None) -> dict | None:
        if not session_id:
            return None
        self._purge_expired()
        return self._pending.get(session_id)

    def set(
        self,
        session_id: str | None,
        corrected_query: str,
        suggested_term: str,
        original_query: str | None = None,
        language: str | None = None,
    ) -> None:
        if not session_id:
            return
        self._pending[session_id] = {
            "corrected_query": corrected_query,
            "suggested_term": suggested_term,
            "original_query": original_query or corrected_query,
            "language": language or "english",
            "expires_at": time() + 600,
        }

    def clear(self, session_id: str | None) -> None:
        if not session_id:
            return
        self._pending.pop(session_id, None)


clarification_store = ClarificationStore()


def is_affirmative_reply(message: str) -> bool:
    normalized = clean_text(message).lower()
    return any(
        normalized == reply or normalized.startswith(f"{reply} ")
        for reply in AFFIRMATIVE_REPLIES
    )


def is_negative_reply(message: str) -> bool:
    normalized = clean_text(message).lower()
    return any(
        normalized == reply or normalized.startswith(f"{reply} ")
        for reply in NEGATIVE_REPLIES
    )


def detect_query_language(text: str) -> str:
    raw = str(text or "")
    lowered = clean_text(raw).lower()
    if DEVANAGARI_PATTERN.search(raw):
        return "hindi"
    if any(term in lowered for term in HINDI_HINT_TERMS):
        return "hinglish"
    if any(term in lowered for term in ROMAN_HINDI_MEDICAL_MAP):
        return "hinglish"
    return "english"


def normalize_query_terms(text: str) -> str:
    normalized = clean_text(text).lower()
    for source, target in MULTI_WORD_ROMAN_HINDI_MAP.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)

    tokens = re.findall(r"[a-zA-Z0-9]+", normalized)
    rebuilt_tokens = [ROMAN_HINDI_MEDICAL_MAP.get(token, token) for token in tokens]
    return " ".join(rebuilt_tokens)


def _extract_focus_terms(question: str) -> list[str]:
    normalized = normalize_query_terms(question)
    tokens = re.findall(r"[a-zA-Z0-9]+", normalized)
    focus_terms = []
    for token in tokens:
        if len(token) < 4:
            continue
        if token in CLARIFICATION_IGNORE_TERMS:
            continue
        if token not in focus_terms:
            focus_terms.append(token)
    return focus_terms


def _replace_focus_term(question: str, focus_term: str, suggested_term: str) -> str:
    normalized_question = normalize_query_terms(question)
    corrected_query = re.sub(
        rf"\b{re.escape(focus_term)}\b",
        suggested_term,
        normalized_question,
        count=1,
    )
    return clean_text(corrected_query or suggested_term)


def infer_likely_medical_topic(question: str) -> dict | None:
    normalized_question = normalize_query_terms(question)
    if not normalized_question or len(normalized_question) > 160:
        return None

    focus_terms = _extract_focus_terms(question)
    if not focus_terms:
        return None

    direct_topics = [term for term in focus_terms if term in COMMON_MEDICAL_TOPICS]
    if direct_topics:
        topic = direct_topics[0]
        return {
            "topic": topic,
            "confidence": 0.93,
            "normalized_query": clean_text(normalized_question),
            "method": "direct_topic",
        }

    if len(focus_terms) != 1:
        return None

    focus_term = focus_terms[0]
    match = get_close_matches(
        focus_term,
        sorted(COMMON_MEDICAL_TOPICS),
        n=1,
        cutoff=0.78,
    )
    if not match:
        return None

    topic = match[0]
    confidence = SequenceMatcher(None, focus_term, topic).ratio()
    corrected_query = _replace_focus_term(question, focus_term, topic)
    return {
        "topic": topic,
        "confidence": round(confidence, 3),
        "normalized_query": corrected_query,
        "method": "fuzzy_topic",
    }


def build_clarification(
    question: str,
    suggested_term: str,
    corrected_query: str | None = None,
) -> dict | None:
    suggested = clean_text(suggested_term).lower()
    if not suggested or suggested not in COMMON_MEDICAL_TOPICS:
        return None

    focus_terms = _extract_focus_terms(question)
    focus_term = focus_terms[0] if focus_terms else ""
    language = detect_query_language(question)
    resolved_query = clean_text(corrected_query)

    # For Hindi/Hinglish clarification prompts, keep the follow-up query as a clean English
    # medical topic so an affirmative reply does not re-enter normalization with a mixed-language sentence.
    if language != "english":
        resolved_query = suggested
    elif not resolved_query:
        if focus_term:
            resolved_query = _replace_focus_term(question, focus_term, suggested)
        else:
            resolved_query = suggested

    if not resolved_query:
        return None

    return {
        "suggested_term": suggested,
        "corrected_query": resolved_query,
        "prompt": f"Are you asking about {suggested}?",
    }


def suggest_clarification(question: str) -> dict | None:
    cleaned_question = normalize_query_terms(question)
    if not cleaned_question or len(cleaned_question) > 80:
        return None

    focus_terms = _extract_focus_terms(question)
    if len(focus_terms) != 1:
        return None

    focus_term = focus_terms[0]
    if focus_term in COMMON_MEDICAL_TOPICS:
        return None

    match = get_close_matches(
        focus_term,
        sorted(COMMON_MEDICAL_TOPICS),
        n=1,
        cutoff=0.80,
    )
    if not match:
        return None

    suggested_term = match[0]
    confidence = SequenceMatcher(None, focus_term, suggested_term).ratio()
    if confidence < 0.80:
        return None

    return build_clarification(
        question,
        suggested_term,
        corrected_query=_replace_focus_term(question, focus_term, suggested_term),
    )


