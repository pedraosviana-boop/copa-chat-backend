"""Ponto de entrada da API Flask."""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from routes.chat import chat_bp
from services.groq_service import generate_reply


def create_app(test_config: dict | None = None, groq_generator=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    app.config["GROQ_GENERATOR"] = groq_generator or generate_reply
    if test_config:
        app.config.update(test_config)

    origins = app.config.get("FRONTEND_ORIGINS", [])
    CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=False)

    # Limiter usa armazenamento em memória por padrão: adequado para protótipo
    # de instância única; configure Redis/armazenamento compartilhado em produção escalada.
    Limiter(
        get_remote_address,
        app=app,
        default_limits=["30 per minute"],
        storage_uri=app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
    )
    app.register_blueprint(chat_bp)

    @app.get("/")
    def index():
        return jsonify(service="Mundo das Copas API", status="available")

    @app.get("/health")
    def health():
        # Não testa nem expõe credenciais do provedor.
        return jsonify(status="ok", service="mundo-das-copas-api"), 200

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="A requisição excede o tamanho permitido."), 413

    @app.errorhandler(429)
    def rate_limited(_error):
        return jsonify(error="Muitas mensagens em pouco tempo. Aguarde um instante e tente novamente."), 429

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=app.config["FLASK_DEBUG"])
