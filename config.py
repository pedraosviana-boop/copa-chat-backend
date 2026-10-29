"""Configurações da aplicação, carregadas do ambiente."""
import os
from dotenv import load_dotenv

load_dotenv()


def csv_origins(value: str) -> list[str]:
    return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]


class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "")
    FRONTEND_ORIGINS = csv_origins(
        os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5500,http://localhost:5500")
    )
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    MAX_MESSAGE_CHARS = 1200
    MAX_HISTORY_MESSAGES = 12
    MAX_HISTORY_CHARS = 6000
