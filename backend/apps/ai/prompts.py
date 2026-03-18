from __future__ import annotations

import json
from typing import Any


def build_scoring_prompt(payload: dict[str, Any]) -> str:
    """
    Construit un prompt FR. La sortie DOIT être un JSON strict (pas de markdown).

    payload contient toutes les données utiles (type_credit, revenus, charges, capital, durée, taux, TE, RAV, etc.).
    """
    ctx = json.dumps(payload, ensure_ascii=False)
    return (
        "Tu es un assistant fintech. Ta tâche: produire un score de faisabilité de crédit et une explication.\n"
        "Contraintes ABSOLUES:\n"
        "- Réponds uniquement en JSON strict (un seul objet), sans texte autour.\n"
        "- Champs requis: score_faisabilite (entier 0-100), texte_explication (string), recommandations (string), avertissements (string).\n"
        "- Langue: français.\n"
        "- Le score doit refléter les métriques fournies (endettement, reste à vivre, charges, apport, durée).\n"
        "- Si informations insuffisantes, score_faisabilite doit être entre 40 et 60 et expliquer l'incertitude.\n\n"
        "Données:\n"
        f"{ctx}\n"
    )

