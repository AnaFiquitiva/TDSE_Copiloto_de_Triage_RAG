"""Registro de auditoría (Sección 4.3 del documento del proyecto).

Cada sugerencia generada por el pipeline debe quedar registrada con, como
mínimo: el relato de entrada, los fragmentos recuperados, la versión del
corpus y del modelo de recuperación usados, y la sugerencia final (incluida
la abstención). Este módulo escribe ese registro en formato JSON Lines para
que sea trivialmente auditable y reproducible.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .generator import Suggestion

AUDIT_MODEL_VERSION = "minimal-generator-v1"


def build_audit_record(
    case_id: str,
    patient_text: str,
    corpus_format: str,
    embedding_mode: str,
    suggestion: Suggestion,
    human_decision: dict | None = None,
) -> dict:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "input_text": patient_text,
        "corpus_format": corpus_format,
        "embedding_mode": embedding_mode,
        "model_version": AUDIT_MODEL_VERSION,
        "retrieved_fragments": [
            {
                "chunk_id": rc.chunk.chunk_id,
                "score": round(rc.score, 4),
                "source": rc.chunk.source,
                "corpus_format": rc.chunk.corpus_format,
            }
            for rc in suggestion.retrieved
        ],
        "suggested_level": suggestion.level,
        "citation": suggestion.citation,
        "confidence": round(suggestion.confidence, 4),
        "abstained": suggestion.abstained,
        "abstain_reason": suggestion.reason if suggestion.abstained else None,
        # La decisión final del personal de salud queda registrada aparte,
        # como lo exige el principio de "asistencia, no decisión" (Sección
        # 2.2): el sistema nunca sobrescribe este campo por sí mismo.
        "human_decision": human_decision,
    }


class AuditLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
