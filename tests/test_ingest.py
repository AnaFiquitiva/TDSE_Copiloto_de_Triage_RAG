import unittest

from src.ingest import canonical_citation, load_corpus


class TestLoadCorpus(unittest.TestCase):
    def test_reformatted_has_all_level_definitions(self):
        chunks = load_corpus("reformatted")
        levels = {c.level for c in chunks if c.source == "niveles_triage"}
        self.assertEqual(levels, {1, 2, 3, 4, 5})

    def test_raw_has_same_number_of_alarm_chunks_as_reformatted(self):
        raw_alarm = [c for c in load_corpus("raw") if c.source == "signos_alarma"]
        reformatted_alarm = [c for c in load_corpus("reformatted") if c.source == "signos_alarma"]
        self.assertEqual(len(raw_alarm), len(reformatted_alarm))

    def test_raw_chunks_have_levels_extracted_from_text(self):
        raw_alarm = [c for c in load_corpus("raw") if c.source == "signos_alarma"]
        self.assertTrue(all(c.level is not None for c in raw_alarm))

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            load_corpus("not_a_format")


class TestCanonicalCitation(unittest.TestCase):
    def test_raw_alarm_id_maps_to_semantic_citation(self):
        self.assertEqual(canonical_citation("ALARMA-RAW-0"), "ALARMA-DOLOR-TORACICO-GRAVE")

    def test_regular_citation_is_identity(self):
        self.assertEqual(canonical_citation("RES5596-N2"), "RES5596-N2")


if __name__ == "__main__":
    unittest.main()
