from flask import Blueprint, jsonify

from services.index_service import describe_index_status, ensure_index_ready
from utils.logger import get_logger

index_bp = Blueprint("index_routes", __name__, url_prefix="/api")
logger = get_logger(__name__)


@index_bp.post("/index/rebuild")
def rebuild_index():
    try:
        result = ensure_index_ready(force_rebuild=True)
        return jsonify(result)
    except Exception as exc:
        logger.exception("Index rebuild failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


@index_bp.get("/index/status")
def index_status():
    try:
        return jsonify(describe_index_status())
    except Exception as exc:
        logger.exception("Index status failed: %s", exc)
        return (
            jsonify(
                {
                    "indexed": False,
                    "vector_store": "chroma",
                    "error": str(exc),
                }
            ),
            500,
        )
