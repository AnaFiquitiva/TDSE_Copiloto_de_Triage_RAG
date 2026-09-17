import unittest

from src.baseline import RuleBasedBaseline


class TestRuleBasedBaseline(unittest.TestCase):
    def setUp(self):
        self.baseline = RuleBasedBaseline()

    def test_level1_keyword_wins_over_lower_levels(self):
        result = self.baseline.classify("El paciente no respira y no reacciona a nada.")
        self.assertEqual(result.level, 1)

    def test_default_level_when_no_keyword_matches(self):
        result = self.baseline.classify("Un relato que no contiene ninguna palabra clave reconocida.")
        self.assertEqual(result.level, 3)
        self.assertIsNone(result.matched_keyword)

    def test_administrative_request_maps_to_level5(self):
        result = self.baseline.classify("Vengo a pedir un certificado medico para el trabajo.")
        self.assertEqual(result.level, 5)


if __name__ == "__main__":
    unittest.main()
