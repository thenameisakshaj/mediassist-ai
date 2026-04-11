from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes.chat_routes import chat_bp
from routes.contact_routes import contact_bp
from routes.index_routes import index_bp
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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
