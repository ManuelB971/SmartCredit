from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AiDecision:
    score_faisabilite: int
    texte_explication: str
    recommandations: str
    avertissements: str
    resume_executif: str = ""
    points_forts_dossier: List[str] = field(default_factory=list)
    risques_identifies: List[str] = field(default_factory=list)
    prochaines_etapes: List[str] = field(default_factory=list)


class AiParseError(ValueError):
    pass


def _parse_list(val: object) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if isinstance(x, str) and x.strip()]
    if isinstance(val, str):
        return [s.strip() for s in val.split("\n") if s.strip()]
    return []


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

    resume = ""
    if "resume_executif" in obj and obj["resume_executif"]:
        resume = str(obj["resume_executif"]).strip()

    return AiDecision(
        score_faisabilite=score,
        texte_explication=req_str("texte_explication"),
        recommandations=req_str("recommandations"),
        avertissements=req_str("avertissements"),
        resume_executif=resume,
        points_forts_dossier=_parse_list(obj.get("points_forts_dossier")),
        risques_identifies=_parse_list(obj.get("risques_identifies")),
        prochaines_etapes=_parse_list(obj.get("prochaines_etapes")),
    )

