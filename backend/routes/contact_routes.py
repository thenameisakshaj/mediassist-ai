from flask import Blueprint, jsonify, request

from utils.helpers import clean_text
from utils.logger import get_logger

contact_bp = Blueprint("contact_routes", __name__, url_prefix="/api")
logger = get_logger(__name__)


@contact_bp.post("/contact")
def contact():
    payload = request.get_json(silent=True) or {}
    name = clean_text(payload.get("name", ""))
    email = clean_text(payload.get("email", ""))
    message = clean_text(payload.get("message", ""))

    if not name or not email or not message:
        return jsonify({"error": "Name, email, and message are required."}), 400

    logger.info("Contact form received from %s <%s>", name, email)
    return jsonify({"status": "received"})
