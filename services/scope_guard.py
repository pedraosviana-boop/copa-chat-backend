"""Classificador conservador para manter o chatbot no domínio das Copas.

Este filtro combina termos e padrões simples. Ele não é um classificador semântico
perfeito; perguntas ambíguas são aceitas para análise pelo prompt de sistema.
Para produção com maior risco, substitua/expanda por um classificador dedicado.
"""
import re
import unicodedata

ALLOWED_TERMS = {
    "copa", "copas", "mundial", "mundiais", "fifa", "selecao", "selecoes",
    "campeao", "campea", "campeoes", "vice", "artilheiro", "artilheiros",
    "gol", "gols", "final", "finais", "semifinal", "quartas", "oitavas",
    "grupo", "grupos", "classificacao", "eliminatoria", "eliminatorias",
    "jogador", "jogadores", "tecnico", "tecnicos", "selecao brasileira",
    "brasil", "argentina", "alemanha", "franca", "italia", "uruguai",
    "espanha", "inglaterra", "portugal", "holanda", "mexico", "japao",
    "coreia", "marrocos", "croacia", "estadio", "sede", "sedes", "masculina",
    "feminina", "feminino", "masculino", "recorde", "recordes", "estatistica",
    "estatisticas", "placar", "partida", "partidas", "jogo", "jogos",
    "penalti", "penaltis", "cartao", "cartoes", "regra", "regras", "formato",
    "historia", "historico", "ano", "anos", "1930", "1934", "1938", "1950",
    "1954", "1958", "1962", "1966", "1970", "1974", "1978", "1982", "1986",
    "1990", "1994", "1998", "2002", "2006", "2010", "2014", "2018", "2022",
    "2026", "2030", "2034", "pele", "messi", "ronaldo", "marta", "klose",
    "maradona", "neymar", "zidane", "mbappe", "cruyff", "caf u", "cafú",
}
OUT_OF_SCOPE_PATTERNS = [
    r"\b(receita|bolo|cozinhar|cozinha|programar|programacao|python|javascript|html|css)\b",
    r"\b(resolva|calcule|equacao|integral|derivada|tarefa de matematica)\b",
    r"\b(religiao|presidente|eleicao|partido politico|investimento|emprestimo)\b",
    r"\b(senha|chave da api|api key|prompt de sistema|instrucoes internas)\b",
    r"\b(me ensine a fazer malware|invadir|hackear)\b",
]
DOMAIN_CONTEXT = (
    "copa do mundo", "copas do mundo", "copa feminina", "copa masculina",
    "mundial de futebol", "futebol", "seleção", "selecao", "jogador",
    "jogadores", "artilheiro", "campeão", "campeao", "final", "gols",
    "gol", "fifa", "eliminatórias", "eliminatorias", "placar", "partida",
    "brasil", "argentina", "alemanha", "frança", "franca", "messi", "pelé",
    "pele", "marta", "maradona", "klose", "ronaldo", "mbappé", "mbappe",
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def is_in_scope(message: str, history: list[dict] | None = None) -> bool:
    """Return True for domain-related or plausibly contextual follow-up questions."""
    normalized = normalize(message)
    if any(re.search(pattern, normalized) for pattern in OUT_OF_SCOPE_PATTERNS):
        # A direct football context can permit ordinary terms like "Python" only
        # if the message genuinely asks about the tournament; never permit secrets.
        if re.search(r"\b(chave da api|api key|prompt de sistema|instrucoes internas)\b", normalized):
            return False
        return False

    if any(term in normalized for term in map(normalize, DOMAIN_CONTEXT)):
        return True

    # Follow-ups such as "e em 2002?" are allowed only if the previous turn
    # in the supplied history had an in-scope topic. The history is bounded by the API.
    if history:
        short_followup = len(normalized.split()) <= 8 and bool(
            re.search(r"\b(e em|e quem|e qual|e quantos|e quantas|e ela|e ele|por que|por quê|quando|onde|quem|qual)\b", normalized)
            or re.fullmatch(r"(e )?\d{4}\??", normalized)
        )
        if short_followup:
            prior_user_messages = [item.get("content", "") for item in history if item.get("role") == "user"]
            if prior_user_messages and any(
                any(term in normalize(prior) for term in map(normalize, DOMAIN_CONTEXT))
                for prior in prior_user_messages[-3:]
            ):
                return True

    # Common direct subject terms; broad country-only terms can create false positives,
    # so require a specific tournament/football cue above or a clear historical year.
    if re.search(r"\b(quem ganhou|quem venceu|quantas copas|maior artilheiro|campeao de \d{4}|campea de \d{4})\b", normalized) or re.search(r"\b(quem venceu|quem ganhou|quem foi campeao|quem foi campea) em (19|20)\d{2}\b", normalized):
        return True
    return False


OUT_OF_SCOPE_REPLY = (
    "Sou especialista exclusivamente em Copas do Mundo de futebol. ⚽🌍 "
    "Posso ajudar com campeões, seleções, jogadores, finais, estatísticas e curiosidades dos torneios. "
    "Que tal perguntar algo sobre a história das Copas?"
)
