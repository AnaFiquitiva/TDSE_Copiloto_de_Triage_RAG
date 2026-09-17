"""Pruebas de la validación de seguridad de LLMBackedGenerator: el modelo
solo puede elegir una cita de la lista de candidatos que nosotros le dimos.
Se inyecta un `generate_fn` falso para no depender de red ni de una API key."""
import unittest

from src.ingest import Chunk
from src.llm_generator import LLMBackedGenerator
from src.retrieval import RankedChunk


class _FakeRetriever:
    def __init__(self, ranked_chunks):
        self._ranked_chunks = ranked_chunks

    def retrieve(self, query, k=5):
        return self._ranked_chunks[:k]


def _make_candidates():
    return [
        RankedChunk(
            chunk=Chunk("RES5596-N2", "texto nivel 2", "niveles", "reformatted", level=2),
            score=0.8,
        ),
        RankedChunk(
            chunk=Chunk("RES5596-N3", "texto nivel 3", "niveles", "reformatted", level=3),
            score=0.5,
        ),
    ]


class TestLLMBackedGenerator(unittest.TestCase):
    def test_valid_citation_from_candidates_is_accepted(self):
        candidates = _make_candidates()
        generator = LLMBackedGenerator(
            _FakeRetriever(candidates),
            generate_fn=lambda prompt: {"citation": "RES5596-N2", "abstain": False, "reasoning": "x"},
        )
        result = generator.suggest("un relato cualquiera")
        self.assertFalse(result.abstained)
        self.assertEqual(result.level, 2)
        self.assertEqual(result.citation, "RES5596-N2")

    def test_model_requested_abstention_is_honored(self):
        candidates = _make_candidates()
        generator = LLMBackedGenerator(
            _FakeRetriever(candidates),
            generate_fn=lambda prompt: {"citation": None, "abstain": True, "reasoning": "sin evidencia"},
        )
        result = generator.suggest("un relato ambiguo")
        self.assertTrue(result.abstained)
        self.assertEqual(result.reason, "abstencion_del_modelo")

    def test_hallucinated_citation_not_in_candidates_forces_abstention(self):
        """Seguridad crítica: si el modelo inventa un id que no le dimos como
        candidato, el sistema NUNCA debe aceptar un nivel — se abstiene."""
        candidates = _make_candidates()
        generator = LLMBackedGenerator(
            _FakeRetriever(candidates),
            generate_fn=lambda prompt: {
                "citation": "RES5596-N1-INVENTADO",
                "abstain": False,
                "reasoning": "el modelo alucino esta cita",
            },
        )
        result = generator.suggest("un relato cualquiera")
        self.assertTrue(result.abstained)
        self.assertIsNone(result.level)
        self.assertEqual(result.reason, "cita_invalida_del_modelo")

    def test_no_candidates_with_level_abstains_without_calling_model(self):
        chunk_sin_nivel = RankedChunk(
            chunk=Chunk("NOTA", "nota sin nivel", "niveles", "reformatted", level=None), score=0.9
        )
        called = {"n": 0}

        def fake_generate(prompt):
            called["n"] += 1
            return {"citation": None, "abstain": True, "reasoning": ""}

        generator = LLMBackedGenerator(_FakeRetriever([chunk_sin_nivel]), generate_fn=fake_generate)
        result = generator.suggest("texto")
        self.assertTrue(result.abstained)
        self.assertEqual(result.reason, "evidencia_insuficiente")
        self.assertEqual(called["n"], 0)  # no vale la pena llamar al modelo sin candidatos


if __name__ == "__main__":
    unittest.main()
