from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OllamaConfig:
    host: str
    model: str
    timeout_sec: float


def get_ollama_config() -> OllamaConfig:
    host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434").rstrip("/")
    model = os.getenv("AI_MODEL", "llama3.1:8b")
    timeout_sec = float(os.getenv("AI_TIMEOUT_SEC", "6"))
    return OllamaConfig(host=host, model=model, timeout_sec=timeout_sec)


class OllamaError(RuntimeError):
    pass


def ollama_generate(prompt: str, *, config: OllamaConfig | None = None) -> str:
    """
    Appelle Ollama /api/generate en mode non-streaming et retourne le champ 'response' (texte).
    """
    cfg = config or get_ollama_config()
    url = f"{cfg.host}/api/generate"
    payload: dict[str, Any] = {
        "model": cfg.model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_sec) as resp:
            raw = resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        raise OllamaError(f"Ollama indisponible: {e}") from e

    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise OllamaError(f"Réponse Ollama non JSON: {raw[:2000]}") from e

    if "response" not in obj:
        raise OllamaError(f"Réponse Ollama inattendue: {raw[:2000]}")
    return str(obj["response"])

