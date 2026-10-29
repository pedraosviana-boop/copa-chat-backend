"""Rotas REST do chatbot."""
from flask import Blueprint, current_app, jsonify, request
from services.scope_guard import is_in_scope, OUT_OF_SCOPE_REPLY
from services.groq_service import generate_reply

chat_bp = Blueprint("chat", __name__)


def _validate_history(raw_history):
    if raw_history is None:
        return []
    if not isinstance(raw_history, list):
        raise ValueError("O histórico deve ser uma lista.")
    result = []
    total_chars = 0
    for item in raw_history[-current_app.config["MAX_HISTORY_MESSAGES"]:]:
        if not isinstance(item, dict):
            raise ValueError("Formato de histórico inválido.")
        role, content = item.get("role"), item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            raise ValueError("Formato de histórico inválido.")
        content = content.strip()
        if not content or len(content) > current_app.config["MAX_MESSAGE_CHARS"]:
            raise ValueError("Mensagem inválida no histórico.")
        total_chars += len(content)
        result.append({"role": role, "content": content})
    if total_chars > current_app.config["MAX_HISTORY_CHARS"]:
        raise ValueError("O histórico é muito longo.")
    return result


@chat_bp.post("/api/chat")
def chat():
    if not request.is_json:
        return jsonify(error="Envie o conteúdo em formato JSON."), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="JSON inválido."), 400
    message = payload.get("message")
    if not isinstance(message, str):
        return jsonify(error="O campo 'message' é obrigatório e deve ser texto."), 400
    message = message.strip()
    if not message:
        return jsonify(error="Digite uma pergunta antes de enviar."), 400
    if len(message) > current_app.config["MAX_MESSAGE_CHARS"]:
        return jsonify(error=f"A pergunta deve ter no máximo {current_app.config['MAX_MESSAGE_CHARS']} caracteres."), 413
    try:
        history = _validate_history(payload.get("history", []))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    # Não permita que campos extras do payload controlem o prompt de sistema.
    if not is_in_scope(message, history):
        return jsonify(reply=OUT_OF_SCOPE_REPLY, status="out_of_scope"), 200

    try:
        reply = current_app.config["GROQ_GENERATOR"](
            current_app.config["GROQ_API_KEY"],
            current_app.config["GROQ_MODEL"],
            message,
            history,
        )
        # Defesa adicional simples: não devolve conteúdo vazio.
        if not isinstance(reply, str) or not reply.strip():
            raise RuntimeError("Resposta vazia do provedor.")
        return jsonify(reply=reply.strip(), status="success"), 200
    except Exception:
        current_app.logger.exception("Falha ao consultar o provedor de IA.")
        return jsonify(error="O assistente está temporariamente indisponível. Tente novamente em instantes."), 503
