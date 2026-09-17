import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.audit import AuditLog
from src.llm_client import LLMUnavailableError
from src.pipeline import CopilotoPipeline


class TestCopilotoPipeline(unittest.TestCase):
    def test_run_case_writes_audit_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_path = Path(tmp) / "audit.jsonl"
            pipeline = CopilotoPipeline(
                corpus_format="reformatted", embedding_mode="clinical_es", audit_path=audit_path
            )
            pipeline.run_case("T001", "El paciente no respira y no reacciona.")

            records = AuditLog(audit_path).read_all()
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["case_id"], "T001")
            self.assertIn("retrieved_fragments", record)
            self.assertIn("suggested_level", record)
            self.assertIn("abstained", record)

    def test_abstention_never_returns_a_level_without_citation(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_path = Path(tmp) / "audit.jsonl"
            pipeline = CopilotoPipeline(
                corpus_format="raw", embedding_mode="generic", audit_path=audit_path
            )
            suggestion = pipeline.run_case("T002", "algo me duele no se muy bien que es")
            if suggestion.abstained:
                self.assertIsNone(suggestion.level)
                self.assertIsNone(suggestion.citation)
            else:
                self.assertIsNotNone(suggestion.citation)


class TestGeminiBackendFallback(unittest.TestCase):
    def test_missing_api_key_falls_back_to_deterministic_transparently(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {}, clear=True):
            audit_path = Path(tmp) / "audit.jsonl"
            pipeline = CopilotoPipeline(
                corpus_format="reformatted", backend="gemini", audit_path=audit_path
            )
            suggestion = pipeline.run_case("T003", "El paciente no respira y no reacciona.")

            # Sin API key, el pipeline nunca debe fallar: cae al determinista.
            self.assertIsNotNone(suggestion)
            record = AuditLog(audit_path).read_all()[0]
            self.assertEqual(record["backend"], "gemini_fallback_deterministic")

    def test_llm_error_during_suggest_falls_back_per_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_path = Path(tmp) / "audit.jsonl"
            pipeline = CopilotoPipeline(
                corpus_format="reformatted", backend="gemini", audit_path=audit_path
            )
            # Forzar que exista un generador LLM "activo" cuyo suggest() falla,
            # para probar la ruta de fallback por-caso (no solo la de arranque).
            pipeline._llm_generator = _AlwaysFailingGenerator()

            suggestion = pipeline.run_case("T004", "vengo a pedir un certificado medico")
            self.assertIsNotNone(suggestion)
            record = AuditLog(audit_path).read_all()[0]
            self.assertEqual(record["backend"], "gemini_fallback_deterministic")


class _AlwaysFailingGenerator:
    def suggest(self, patient_text):
        raise LLMUnavailableError("fallo simulado de red")


if __name__ == "__main__":
    unittest.main()
