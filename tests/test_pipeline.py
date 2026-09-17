import json
import tempfile
import unittest
from pathlib import Path

from src.audit import AuditLog
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


if __name__ == "__main__":
    unittest.main()
