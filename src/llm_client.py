"""Cliente mínimo para la API de Gemini (embeddings + generación), usado como
backend OPCIONAL de robustez (ver README.md, sección "Backend LLM opcional").

Deliberadamente NO usa el SDK oficial `google-generativeai` para no agregar
una dependencia externa al proyecto: solo usa `urllib` (biblioteca estándar).
El backend determinista (`src/retrieval.py` modos `generic`/`clinical_es` +
`src/generator.py`) sigue siendo el camino por defecto y no requiere nada de
este módulo.

**Manejo de la API key**: se lee EXCLUSIVAMENTE de la variable de entorno
`GEMINI_API_KEY`. Este módulo nunca la recibe como literal en el código ni la
escribe a ningún archivo. Ver README.md para cómo configurarla.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GENERATION_MODEL = "gemini-flash-lite-latest"
EMBEDDING_MODEL = "gemini-embedding-001"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 30
# Códigos de error transitorios sobre los que vale la pena reintentar.
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class LLMUnavailableError(Exception):
    """Se lanza cuando el backend Gemini no puede usarse: falta la API key,
    hay un error de red, o la respuesta no tiene el formato esperado. El
    llamador (CopilotoPipeline) decide si usar esto como señal para caer de
    vuelta al backend determinista."""


def get_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMUnavailableError(
            "No se encontró la variable de entorno GEMINI_API_KEY. Configúrala "
            "con tu propia API key (ver README.md, sección 'Backend LLM "
            "opcional') para usar el backend Gemini; de lo contrario, usa el "
            "backend determinista (por defecto)."
        )
    return api_key


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_error = LLMUnavailableError(
                f"Gemini API devolvió HTTP {exc.code}: {body[:300]}"
            )
            if exc.code not in RETRYABLE_STATUS_CODES or attempt == MAX_RETRIES:
                raise last_error from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = LLMUnavailableError(f"Error de red llamando a Gemini: {exc}")
            if attempt == MAX_RETRIES:
                raise last_error from exc
        time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise last_error or LLMUnavailableError("Fallo desconocido llamando a Gemini")


def embed_text(text: str, api_key: str | None = None) -> list[float]:
    """Obtiene el vector de embedding real de Gemini para `text`."""
    api_key = api_key or get_api_key()
    url = f"{API_BASE}/{EMBEDDING_MODEL}:embedContent?key={api_key}"
    payload = {"content": {"parts": [{"text": text}]}}
    try:
        response = _post_json(url, payload)
        return response["embedding"]["values"]
    except (KeyError, TypeError) as exc:
        raise LLMUnavailableError(f"Respuesta de embeddings con formato inesperado: {exc}") from exc


# Esquema de salida estructurada: fuerza a Gemini a responder SOLO con estos
# tres campos (ver README.md: la cita se valida siempre contra la lista de
# candidatos que nosotros mismos recuperamos; el nivel nunca se toma de un
# campo de texto libre del modelo).
_GENERATION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "citation": {
            "type": "STRING",
            "nullable": True,
            "description": "El id exacto del candidato elegido, o null si no hay evidencia suficiente.",
        },
        "abstain": {
            "type": "BOOLEAN",
            "description": "true si ningún candidato describe claramente el caso del relato.",
        },
        "reasoning": {"type": "STRING", "description": "Justificación breve, en español."},
    },
    "required": ["abstain", "reasoning"],
}


def generate_structured(prompt: str, api_key: str | None = None) -> dict:
    """Llama a Gemini con salida JSON forzada al esquema `_GENERATION_SCHEMA`."""
    api_key = api_key or get_api_key()
    url = f"{API_BASE}/{GENERATION_MODEL}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": _GENERATION_SCHEMA,
        },
    }
    try:
        response = _post_json(url, payload)
        text = response["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise LLMUnavailableError(f"Respuesta de generación con formato inesperado: {exc}") from exc
