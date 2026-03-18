from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class AiDecision:
    score_faisabilite: int
    texte_explication: str
    recommandations: str
    avertissements: str


class AiParseError(ValueError):
    pass


def parse_ai_json(text: str) -> AiDecision:
    """
    Parse la sortie attendue (JSON strict) renvoyée par le LLM.
    """
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise AiParseError(f"JSON invalide: {text[:2000]}") from e

    def req_str(key: str) -> str:
        v = obj.get(key)
        if not isinstance(v, str) or not v.strip():
            raise AiParseError(f"Champ manquant/invalid: {key}")
        return v.strip()

    score = obj.get("score_faisabilite")
    if not isinstance(score, int):
        raise AiParseError("score_faisabilite doit être un entier")
    if score < 0 or score > 100:
        raise AiParseError("score_faisabilite hors plage 0-100")

    return AiDecision(
        score_faisabilite=score,
        texte_explication=req_str("texte_explication"),
        recommandations=req_str("recommandations"),
        avertissements=req_str("avertissements"),
    )

