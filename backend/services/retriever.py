from config import Config
from services.embeddings import embed_texts
from services.vector_store import ChromaVectorStore


class MedicalRetriever:
    def __init__(self, vector_store: ChromaVectorStore | None = None):
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve(self, question: str) -> list[dict]:
        query_embedding = embed_texts([question])[0]
        matches = self.vector_store.query(query_embedding, n_results=Config.TOP_K)

        relevant = [
            match
            for match in matches
            if match.get("similarity", 0) >= Config.MIN_RELEVANCE_SCORE
        ]
        return relevant or matches[:1]
