from config import Config
from utils.helpers import snippet

MEDICAL_SYSTEM_PROMPT = """
You are MediAssist AI, an educational medical assistant for an academic project.
Use only the retrieved medical-book context supplied by the backend.

Rules:
- Do not diagnose, prescribe, or claim treatment certainty.
- If the retrieved context is insufficient, say exactly:
  "I do not have enough relevant medical-book context to answer that confidently."
- Keep answers concise, readable, and grounded in the provided context.
- Encourage users to consult licensed healthcare professionals.
- If the user describes emergency warning signs, advise immediate professional or emergency help.
- Do not fabricate sources, page numbers, citations, or medical facts.
"""


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


def build_user_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    return f"""
Retrieved medical-book context:
{build_context_block(retrieved_chunks)}

User question:
{question}

Answer requirements:
- Answer from the retrieved context only.
- Start with the key educational answer.
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
