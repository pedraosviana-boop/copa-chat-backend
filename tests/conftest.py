import pytest
from app import create_app


@pytest.fixture
def app():
    def fake_generator(api_key, model, message, history):
        return "Resposta simulada de teste sobre Copas do Mundo."
    application = create_app(
        {
            "TESTING": True,
            "GROQ_API_KEY": "test-key",
            "GROQ_MODEL": "test-model",
            "FRONTEND_ORIGINS": ["http://localhost:5500"],
            "RATELIMIT_STORAGE_URI": "memory://",
        },
        groq_generator=fake_generator,
    )
    application.config["GROQ_GENERATOR_CALLED"] = False
    original_generator = application.config["GROQ_GENERATOR"]
    def tracked_generator(*args):
        application.config["GROQ_GENERATOR_CALLED"] = True
        return original_generator(*args)
    application.config["GROQ_GENERATOR"] = tracked_generator
    return application


@pytest.fixture
def client(app):
    return app.test_client()
