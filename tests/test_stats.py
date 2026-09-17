import unittest

from src.stats import build_contingency_table, chi2_sf, chi_square_independence_test


class TestChi2Sf(unittest.TestCase):
    def test_known_critical_values(self):
        # Valores de tabla estandar de chi-cuadrado (p = 0.05)
        self.assertAlmostEqual(chi2_sf(3.841, 1), 0.05, places=3)
        self.assertAlmostEqual(chi2_sf(7.815, 3), 0.05, places=3)
        self.assertAlmostEqual(chi2_sf(15.507, 8), 0.05, places=3)

    def test_zero_statistic_gives_p_value_one(self):
        self.assertEqual(chi2_sf(0, 5), 1.0)


class TestContingencyTable(unittest.TestCase):
    def test_build_table_counts(self):
        rows = [
            {"grupo": "A", "nivel": "1"},
            {"grupo": "A", "nivel": "1"},
            {"grupo": "A", "nivel": "2"},
            {"grupo": "B", "nivel": "2"},
        ]
        row_labels, col_labels, table = build_contingency_table(rows, "grupo", "nivel")
        self.assertEqual(row_labels, ["A", "B"])
        self.assertEqual(col_labels, ["1", "2"])
        self.assertEqual(table, [[2, 1], [0, 1]])


class TestChiSquareIndependence(unittest.TestCase):
    def test_independent_groups_have_high_p_value(self):
        # Misma proporcion en ambos grupos: no deberia haber asociacion.
        table = [[100, 100], [50, 50]]
        result = chi_square_independence_test(table)
        self.assertGreater(result["p_value"], 0.9)

    def test_strongly_associated_groups_have_low_p_value(self):
        table = [[100, 0], [0, 100]]
        result = chi_square_independence_test(table)
        self.assertLess(result["p_value"], 0.001)

    def test_degrees_of_freedom(self):
        table = [[1, 2, 3], [4, 5, 6]]
        result = chi_square_independence_test(table)
        self.assertEqual(result["df"], 2)


if __name__ == "__main__":
    unittest.main()
