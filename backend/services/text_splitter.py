from copy import deepcopy


def split_documents(
    documents: list[dict], chunk_size: int = 700, chunk_overlap: int = 90
) -> list[dict]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    chunks = []
    chunk_index = 0

    for document in documents:
        text = document["text"]
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            if end < len(text):
                boundary = text.rfind(" ", start, end)
                if boundary > start + int(chunk_size * 0.6):
                    end = boundary

            chunk_text = text[start:end].strip()
            if chunk_text:
                metadata = deepcopy(document.get("metadata", {}))
                metadata["chunk_index"] = chunk_index
                metadata["text_length"] = len(chunk_text)
                chunks.append({"text": chunk_text, "metadata": metadata})
                chunk_index += 1

            if end >= len(text):
                break

            start = max(end - chunk_overlap, start + 1)

    return chunks
