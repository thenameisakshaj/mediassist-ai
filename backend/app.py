from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes.chat_routes import chat_bp
from routes.contact_routes import contact_bp
from routes.index_routes import index_bp
from services.index_service import describe_index_status
from utils.logger import get_logger

logger = get_logger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=False,
    )

    app.register_blueprint(chat_bp)
    app.register_blueprint(index_bp)
    app.register_blueprint(contact_bp)

    @app.get("/api/health")
    def health_check():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        logger.exception("Unhandled server error: %s", error)
        return jsonify({"error": "Internal server error"}), 500

    try:
        index_status = describe_index_status()
        logger.info(
            "Startup index status | indexed=%s | pdf_found=%s | pdf_path=%s | persist_dir=%s | collection=%s | chunks_indexed=%s",
            index_status.get("indexed"),
            index_status.get("pdf_found"),
            index_status.get("document_path"),
            index_status.get("persist_dir"),
            index_status.get("collection"),
            index_status.get("chunks_indexed"),
        )
    except Exception as exc:
        logger.warning("Startup index status check failed: %s", exc)

    return app


app = create_app()


if __name__ == "__main__":
    # Keep dev mode on, but skip the Flask stat reloader so background starts stay single-process and stable.
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG, use_reloader=False)
