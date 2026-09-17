"""Orquesta un caso individual a través de ingesta -> recuperación ->
generación -> registro de auditoría (componentes 2 y 3 mínimo, Sección 4 del
documento del proyecto)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .audit import AuditLog, build_audit_record
from .generator import MinimalGenerator, Suggestion
from .ingest import Chunk, load_corpus
from .retrieval import Retriever

DEFAULT_AUDIT_PATH = Path(__file__).resolve().parent.parent / "results" / "audit_log.jsonl"


@lru_cache(maxsize=None)
def _cached_corpus(corpus_format: str) -> tuple[Chunk, ...]:
    return tuple(load_corpus(corpus_format))


def build_generator(corpus_format: str, embedding_mode: str, k: int = 5) -> MinimalGenerator:
    chunks = list(_cached_corpus(corpus_format))
    retriever = Retriever(chunks, embedding_mode=embedding_mode)
    return MinimalGenerator(retriever, k=k)


class CopilotoPipeline:
    """Pipeline reproducible para una celda experimental (corpus_format x
    embedding_mode). Ver Tabla de celdas 2x2 en la Sección 5 del documento."""

    def __init__(
        self,
        corpus_format: str,
        embedding_mode: str,
        k: int = 5,
        audit_path: Path = DEFAULT_AUDIT_PATH,
    ):
        self.corpus_format = corpus_format
        self.embedding_mode = embedding_mode
        self.generator = build_generator(corpus_format, embedding_mode, k=k)
        self.audit_log = AuditLog(audit_path)

    def run_case(self, case_id: str, patient_text: str) -> Suggestion:
        suggestion = self.generator.suggest(patient_text)
        record = build_audit_record(
            case_id=case_id,
            patient_text=patient_text,
            corpus_format=self.corpus_format,
            embedding_mode=self.embedding_mode,
            suggestion=suggestion,
        )
        self.audit_log.append(record)
        return suggestion
