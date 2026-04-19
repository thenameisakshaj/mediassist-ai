from flask import Blueprint, jsonify, request

from services.chatbot_service import ChatbotService
from utils.logger import get_logger

chat_bp = Blueprint("chat_routes", __name__, url_prefix="/api")
logger = get_logger(__name__)

SUGGESTED_PROMPTS = [
    "What is acne?",
    "What causes fever?",
    "Explain migraine symptoms",
    "What is anemia?",
]


@chat_bp.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    session_id = payload.get("session_id")

    try:
        response = ChatbotService().answer(message, session_id=session_id)
        return jsonify(response)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        logger.warning("Chat service unavailable: %s", exc)
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.exception("Chat request failed: %s", exc)
        return jsonify({"error": "Unable to generate an answer right now."}), 500


@chat_bp.get("/suggested-prompts")
def suggested_prompts():
    return jsonify({"prompts": SUGGESTED_PROMPTS})
