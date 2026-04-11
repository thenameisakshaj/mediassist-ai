from flask import Blueprint, jsonify

from config import Config
from services.embeddings import embed_texts
from services.pdf_loader import load_pdf_pages
from services.text_splitter import split_documents
from services.vector_store import ChromaVectorStore
from utils.logger import get_logger

index_bp = Blueprint("index_routes", __name__, url_prefix="/api")
logger = get_logger(__name__)


@index_bp.post("/index/rebuild")
def rebuild_index():
    try:
        pages = load_pdf_pages(Config.MEDICAL_BOOK_PATH)
        chunks = split_documents(
            pages,
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
        )
        embeddings = embed_texts([chunk["text"] for chunk in chunks])

        vector_store = ChromaVectorStore()
        vector_store.reset()
        chunks_indexed = vector_store.add_chunks(chunks, embeddings)

        return jsonify({"status": "success", "chunks_indexed": chunks_indexed})
    except Exception as exc:
        logger.exception("Index rebuild failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


@index_bp.get("/index/status")
def index_status():
    try:
        return jsonify(ChromaVectorStore().status())
    except Exception as exc:
        logger.exception("Index status failed: %s", exc)
        return (
            jsonify(
                {
                    "indexed": False,
                    "vector_store": "chroma",
                    "document_name": Config.MEDICAL_BOOK_PATH.name,
                    "error": str(exc),
                }
            ),
            500,
        )
