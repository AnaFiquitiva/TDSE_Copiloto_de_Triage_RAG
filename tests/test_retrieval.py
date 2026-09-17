import unittest

from src.ingest import load_corpus
from src.retrieval import Retriever


class TestRetriever(unittest.TestCase):
    def setUp(self):
        self.chunks = load_corpus("reformatted")

    def test_retrieve_returns_k_results(self):
        retriever = Retriever(self.chunks, embedding_mode="generic")
        results = retriever.retrieve("me duele mucho el estomago", k=3)
        self.assertEqual(len(results), 3)

    def test_domain_lexicon_improves_match_for_lay_phrase(self):
        text = "el paciente tiene un dolor en el pecho que se corre al brazo"
        generic = Retriever(self.chunks, embedding_mode="generic")
        clinical = Retriever(self.chunks, embedding_mode="clinical_es")

        generic_top = generic.retrieve(text, k=1)[0]
        clinical_top = clinical.retrieve(text, k=1)[0]

        # El termino coloquial "dolor en el pecho" no comparte token con
        # "dolor toracico" salvo tras la normalizacion de dominio.
        self.assertGreaterEqual(clinical_top.score, generic_top.score)

    def test_invalid_embedding_mode_raises(self):
        with self.assertRaises(ValueError):
            Retriever(self.chunks, embedding_mode="not_a_mode")


if __name__ == "__main__":
    unittest.main()
