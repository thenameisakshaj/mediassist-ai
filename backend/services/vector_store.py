from pathlib import Path
from typing import Any

import chromadb

from config import Config


class ChromaVectorStore:
    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str | None = None,
    ):
        self.persist_dir = Path(persist_dir or Config.VECTOR_STORE_DIR)
        self.collection_name = collection_name or Config.CHROMA_COLLECTION_NAME
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self):
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
        batch_size: int = 128,
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have matching lengths.")

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            batch_embeddings = embeddings[start : start + batch_size]
            ids = [
                f"{chunk['metadata'].get('source', 'medical_book')}-"
                f"p{chunk['metadata'].get('page', 'x')}-"
                f"c{chunk['metadata'].get('chunk_index', start + index)}"
                for index, chunk in enumerate(batch)
            ]
            self.collection.add(
                ids=ids,
                documents=[chunk["text"] for chunk in batch],
                metadatas=[chunk["metadata"] for chunk in batch],
                embeddings=batch_embeddings,
            )

        return len(chunks)

    def count(self) -> int:
        return self.collection.count()

    def query(self, query_embedding: list[float], n_results: int = 4) -> list[dict]:
        if self.count() == 0:
            return []

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]

        matches = []
        for document, metadata, distance, match_id in zip(
            documents, metadatas, distances, ids
        ):
            similarity = max(0.0, 1.0 - float(distance))
            matches.append(
                {
                    "id": match_id,
                    "text": document,
                    "metadata": metadata or {},
                    "distance": float(distance),
                    "similarity": round(similarity, 4),
                }
            )

        return matches

    def status(self) -> dict:
        count = self.count()
        return {
            "indexed": count > 0,
            "vector_store": "chroma",
            "document_name": Config.MEDICAL_BOOK_PATH.name,
            "document_path": str(Config.MEDICAL_BOOK_PATH),
            "pdf_found": Config.MEDICAL_BOOK_PATH.exists(),
            "persist_dir": str(self.persist_dir),
            "chunks_indexed": count,
            "collection": self.collection_name,
        }
