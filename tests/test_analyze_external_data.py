import unittest

from experiments.analyze_external_data import level_distribution, time_to_attention_minutes


class TestAnalyzeExternalData(unittest.TestCase):
    def test_level_distribution_counts(self):
        rows = [{"triage": "III"}, {"triage": "III"}, {"triage": "I"}]
        dist = level_distribution(rows)
        self.assertEqual(dist["III"], 2)
        self.assertEqual(dist["I"], 1)

    def test_time_to_attention_discards_negative_and_outliers(self):
        rows = [
            {"triage": "II", "fecha_ing": "2020-01-01T08:00:00.000", "fecha_atencion": "2020-01-01T08:20:00.000"},
            {"triage": "II", "fecha_ing": "2020-01-01T08:00:00.000", "fecha_atencion": "2020-01-01T07:00:00.000"},
            {"triage": "II", "fecha_ing": "2020-01-01T08:00:00.000", "fecha_atencion": "2020-01-03T08:00:00.000"},
        ]
        durations = time_to_attention_minutes(rows)
        self.assertEqual(durations["II"], [20.0])


if __name__ == "__main__":
    unittest.main()
