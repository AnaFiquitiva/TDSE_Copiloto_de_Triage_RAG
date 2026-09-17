"""Orquesta un caso individual a través de ingesta -> recuperación ->
generación -> registro de auditoría (componentes 2 y 3 mínimo, Sección 4 del
documento del proyecto).

Soporta dos backends (ver README.md, sección "Backend LLM opcional"):

- ``"deterministic"`` (por defecto): TF-IDF (`Retriever`) + vecino-más-cercano
  (`MinimalGenerator`). Sin red, sin API key, 100% reproducible.
- ``"gemini"``: *embeddings* y generación reales vía la API de Gemini
  (`GeminiRetriever` + `LLMBackedGenerator`). Requiere `GEMINI_API_KEY`. Si la
  key no está configurada o la API falla, el pipeline cae automáticamente al
  backend determinista para ese caso (nunca deja al usuario sin respuesta por
  un problema de red), y lo deja registrado en el campo ``backend`` del
  registro de auditoría.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .audit import AuditLog, build_audit_record
from .generator import MinimalGenerator, Suggestion
from .ingest import Chunk, load_corpus
from .llm_client import LLMUnavailableError
from .llm_generator import LLMBackedGenerator
from .retrieval import GeminiRetriever, Retriever

DEFAULT_AUDIT_PATH = Path(__file__).resolve().parent.parent / "results" / "audit_log.jsonl"


@lru_cache(maxsize=None)
def _cached_corpus(corpus_format: str) -> tuple[Chunk, ...]:
    return tuple(load_corpus(corpus_format))


def build_generator(corpus_format: str, embedding_mode: str, k: int = 5) -> MinimalGenerator:
    chunks = list(_cached_corpus(corpus_format))
    retriever = Retriever(chunks, embedding_mode=embedding_mode)
    return MinimalGenerator(retriever, k=k)


def build_llm_generator(corpus_format: str, k: int = 5) -> LLMBackedGenerator:
    chunks = list(_cached_corpus(corpus_format))
    retriever = GeminiRetriever(chunks)
    return LLMBackedGenerator(retriever, k=k)


class CopilotoPipeline:
    """Pipeline reproducible para una celda experimental (corpus_format x
    embedding_mode). Ver Tabla de celdas 2x2 en la Sección 5 del documento."""

    def __init__(
        self,
        corpus_format: str,
        embedding_mode: str = "clinical_es",
        k: int = 5,
        audit_path: Path = DEFAULT_AUDIT_PATH,
        backend: str = "deterministic",
    ):
        if backend not in {"deterministic", "gemini"}:
            raise ValueError("backend debe ser 'deterministic' o 'gemini'")
        self.corpus_format = corpus_format
        self.embedding_mode = embedding_mode
        self.backend = backend
        self.generator = build_generator(corpus_format, embedding_mode, k=k)
        self._llm_generator: LLMBackedGenerator | None = None
        if backend == "gemini":
            # Construir el retriever de Gemini de una vez (dispara los
            # embeddings del corpus, cacheados en disco); si falla aquí
            # mismo (p. ej. sin API key), cada llamada a run_case() caerá al
            # backend determinista igualmente.
            try:
                self._llm_generator = build_llm_generator(corpus_format, k=k)
            except LLMUnavailableError:
                self._llm_generator = None
        self.audit_log = AuditLog(audit_path)

    def run_case(self, case_id: str, patient_text: str) -> Suggestion:
        backend_used = "deterministic"
        suggestion: Suggestion | None = None

        if self.backend == "gemini" and self._llm_generator is not None:
            try:
                suggestion = self._llm_generator.suggest(patient_text)
                backend_used = "gemini"
            except LLMUnavailableError:
                suggestion = None
        if suggestion is None:
            suggestion = self.generator.suggest(patient_text)
            if self.backend == "gemini":
                backend_used = "gemini_fallback_deterministic"

        record = build_audit_record(
            case_id=case_id,
            patient_text=patient_text,
            corpus_format=self.corpus_format,
            embedding_mode=self.embedding_mode,
            suggestion=suggestion,
            backend=backend_used,
        )
        self.audit_log.append(record)
        return suggestion
