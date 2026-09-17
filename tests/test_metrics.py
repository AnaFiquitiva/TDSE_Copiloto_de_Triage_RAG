import unittest

from src import metrics


class TestSubTriageRate(unittest.TestCase):
    def test_no_sub_triage(self):
        pairs = [(1, 1), (2, 2), (3, 2)]  # el ultimo es sobre-triage, no sub-triage
        self.assertEqual(metrics.sub_triage_rate(pairs), 0.0)

    def test_pure_sub_triage(self):
        pairs = [(1, 2), (1, 3)]  # subestima en 1 y en 2 niveles
        self.assertAlmostEqual(metrics.sub_triage_rate(pairs), 1.5)

    def test_empty(self):
        self.assertEqual(metrics.sub_triage_rate([]), 0.0)


class TestWeightedKappa(unittest.TestCase):
    def test_perfect_agreement(self):
        pairs = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
        self.assertAlmostEqual(metrics.weighted_kappa(pairs), 1.0)

    def test_some_disagreement_is_less_than_one(self):
        pairs = [(1, 1), (2, 2), (3, 4), (4, 4), (5, 5)]
        kappa = metrics.weighted_kappa(pairs)
        self.assertLess(kappa, 1.0)
        self.assertGreater(kappa, 0.0)


class TestSensitivity(unittest.TestCase):
    def test_all_high_risk_detected(self):
        pairs = [(1, 1), (2, 2), (3, 3)]
        self.assertEqual(metrics.sensitivity_high_risk(pairs), 1.0)

    def test_missed_high_risk_case(self):
        pairs = [(1, 3), (2, 2)]  # el primero subestima I hacia III
        self.assertEqual(metrics.sensitivity_high_risk(pairs), 0.5)

    def test_no_high_risk_cases_is_nan(self):
        pairs = [(3, 3), (4, 4)]
        self.assertNotEqual(metrics.sensitivity_high_risk(pairs), metrics.sensitivity_high_risk(pairs))


class TestAbstentionMetrics(unittest.TestCase):
    def test_correct_and_improper_abstention(self):
        should_abstain = [True, True, False, False]
        actually_abstained = [True, False, False, True]
        result = metrics.abstention_metrics(should_abstain, actually_abstained)
        self.assertEqual(result["tasa_abstencion_correcta"], 0.5)
        self.assertEqual(result["tasa_abstencion_indebida"], 0.5)


if __name__ == "__main__":
    unittest.main()
