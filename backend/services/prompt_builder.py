import re

from config import Config
from utils.helpers import clean_text, snippet

MEDICAL_SYSTEM_PROMPT = """
You are MediAssist AI, an educational medical assistant for an academic project.
Use only the retrieved medical-book context supplied by the backend.

Rules:
- Do not diagnose, prescribe, or claim treatment certainty.
- If the retrieved context is insufficient, loosely related, or misses key question terms, say exactly:
  "I do not have enough relevant medical-book context to answer that confidently."
- Refuse vague, out-of-domain, or meta-validation questions unless the provided context directly answers them.
- If the retrieved context clearly names the medical topic and gives a usable general overview, answer from it instead of refusing.
- Keep answers concise, readable, and grounded in the provided context.
- Encourage users to consult licensed healthcare professionals.
- If the user describes emergency warning signs, advise immediate professional or emergency help.
- Do not fabricate sources, page numbers, citations, or medical facts.
"""


def get_requested_answer_style(question: str) -> str:
    lowered = f" {clean_text(question).lower()} "
    if re.search(r"\b(difference between|difference of|differences between|compare|comparison|versus|vs)\b", lowered):
        return "comparison"
    if re.search(r"\b(step by step|stepwise|steps?)\b", lowered):
        return "numbered"
    if re.search(r"\b(in points?|bullet points?|bullets?|key points?|list|pointwise)\b", lowered):
        return "bullets"
    return "default"


def extract_comparison_terms(question: str) -> tuple[str, str] | None:
    normalized = clean_text(question)
    patterns = [
        r"difference(?:s)? between (.+?) and (.+)",
        r"compare (.+?) and (.+)",
        r"(.+?)\s+(?:vs\.?|versus)\s+(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        left = clean_text(match.group(1).strip(" ?.,:"))
        right = clean_text(match.group(2).strip(" ?.,:"))
        if left and right:
            return left, right
    return None


def build_format_instruction(question: str) -> str:
    style = get_requested_answer_style(question)
    if style == "comparison":
        return (
            "Return a clean Markdown comparison with a short heading and separate bullet sections for each side. "
            "Do not collapse the comparison into plain paragraphs."
        )
    if style == "numbered":
        return (
            "Return a numbered Markdown list so the explanation is clearly step by step. "
            "Do not use plain paragraphs for the main answer."
        )
    if style == "bullets":
        return (
            "Return a Markdown bullet list with short readable points. "
            "Do not use plain paragraphs for the main answer."
        )
    return "Use short paragraphs, and switch to bullets only when they improve clarity."


def build_language_instruction(answer_language: str) -> str:
    if answer_language == "hindi":
        return "Answer in simple Hindi."
    if answer_language == "hinglish":
        return "Answer in natural Hinglish using Roman script."
    return "Answer in English."


def build_context_block(retrieved_chunks: list[dict]) -> str:
    lines = []
    for index, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "medical_book.pdf")
        page = metadata.get("page", "unknown")
        lines.append(
            f"[Source {index}: {source}, page {page}, similarity {chunk.get('similarity', 0)}]\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(lines)


def build_user_prompt(
    question: str,
    retrieved_chunks: list[dict],
    normalized_query: str | None = None,
    answer_language: str = "english",
) -> str:
    resolved_query = clean_text(normalized_query or question)
    return f"""
Retrieved medical-book context:
{build_context_block(retrieved_chunks)}

Original user question:
{question}

Normalized retrieval query (English):
{resolved_query}

Answer requirements:
- Answer from the retrieved context only.
- Treat the normalized retrieval query as the medical intent to answer.
- If the context is weak, partial, or missing key terms from the question, return exactly:
  "I do not have enough relevant medical-book context to answer that confidently."
- If the context clearly names the condition or topic and gives a general textbook overview, provide that grounded overview instead of refusing.
- Do not infer from related-but-different topics.
- Do not interpret vague references or meta-questions unless the retrieved text directly resolves them.
- Start with the key educational answer.
- {build_language_instruction(answer_language)}
- Follow this formatting preference when relevant: {build_format_instruction(question)}
- Mention when the source context is limited.
- End with a short safety reminder: {Config.SAFETY_WARNING}
""".strip()


def build_source_payload(retrieved_chunks: list[dict]) -> list[dict]:
    sources = []
    for index, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk.get("metadata", {})
        sources.append(
            {
                "source": metadata.get("source", "medical_book.pdf"),
                "page": metadata.get("page"),
                "chunk_index": metadata.get("chunk_index"),
                "similarity": chunk.get("similarity"),
                "snippet": snippet(chunk.get("text", ""), 420),
                "label": f"Source {index}",
            }
        )
    return sources
