from threading import Lock

from config import Config
from services.embeddings import embed_texts
from services.pdf_loader import load_pdf_pages
from services.text_splitter import split_documents
from services.vector_store import ChromaVectorStore
from utils.logger import get_logger

logger = get_logger(__name__)

_INDEX_LOCK = Lock()


def describe_index_status(vector_store: ChromaVectorStore | None = None) -> dict:
    store = vector_store or ChromaVectorStore()
    count = store.count()
    pdf_path = Config.MEDICAL_BOOK_PATH

    return {
        "indexed": count > 0,
        "vector_store": "chroma",
        "document_name": pdf_path.name,
        "document_path": str(pdf_path),
        "pdf_found": pdf_path.exists(),
        "persist_dir": str(store.persist_dir),
        "chunks_indexed": count,
        "collection": store.collection_name,
    }


def ensure_index_ready(force_rebuild: bool = False) -> dict:
    with _INDEX_LOCK:
        vector_store = ChromaVectorStore()
        existing_count = vector_store.count()
        pdf_path = Config.MEDICAL_BOOK_PATH

        logger.info(
            "Index check | pdf_found=%s | pdf_path=%s | persist_dir=%s | collection=%s | existing_chunks=%s | force_rebuild=%s",
            pdf_path.exists(),
            pdf_path,
            vector_store.persist_dir,
            vector_store.collection_name,
            existing_count,
            force_rebuild,
        )

        if existing_count > 0 and not force_rebuild:
            status = describe_index_status(vector_store)
            status["status"] = "ready"
            status["reused_existing"] = True
            logger.info(
                "Index ready | reused_existing=%s | collection=%s | chunks_indexed=%s",
                True,
                vector_store.collection_name,
                existing_count,
            )
            return status

        pages = load_pdf_pages(pdf_path)
        chunks = split_documents(
            pages,
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
        )
        embeddings = embed_texts([chunk["text"] for chunk in chunks])

        vector_store.reset()
        chunks_indexed = vector_store.add_chunks(chunks, embeddings)

        status = describe_index_status(vector_store)
        status.update(
            {
                "status": "success",
                "reused_existing": False,
                "pages_loaded": len(pages),
                "chunks_created": len(chunks),
                "chunks_indexed": chunks_indexed,
            }
        )
        logger.info(
            "Index build complete | pages_loaded=%s | chunks_created=%s | chunks_indexed=%s | collection=%s",
            len(pages),
            len(chunks),
            chunks_indexed,
            vector_store.collection_name,
        )
        return status
