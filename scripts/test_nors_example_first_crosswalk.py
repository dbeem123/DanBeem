import csv
import unittest
from pathlib import Path

from scripts.build_nors_example_first_crosswalk import (
    FIELDS, ROOT, build_rows, candidate_rank_key, use_text,
)


class ExampleFirstCrosswalk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.summary = build_rows()

    def test_use_extraction_preserves_verbatim_instruction(self):
        definition = "A01 Complaint description. Use A02 when the facts match. Use A03 for another case."
        self.assertEqual(use_text(definition), "Use A02 when the facts match. Use A03 for another case.")

    def test_multiple_distinct_passes_rank_above_a_larger_single_pass_score(self):
        corroborated = {
            "support_pass_count": 3, "example_match_count": 1,
            "example_match_score": "5.0", "nors_code": "F13",
        }
        single_pass = {
            "support_pass_count": 1, "example_match_count": 9,
            "example_match_score": "99.0", "nors_code": "F06",
        }
        self.assertLess(candidate_rank_key(corroborated), candidate_rank_key(single_pass))

    def test_every_candidate_starts_from_example_and_is_nonoperative(self):
        self.assertGreater(len(self.rows), 0)
        for row in self.rows:
            self.assertIn(row["batch"], (4, 5, 6))
            self.assertTrue(row["appendix_example_text"])
            self.assertIn("appendix-pp-", row["appendix_example_locator"])
            self.assertTrue(row["table_2_definition"])
            self.assertIn("Table 2 row", row["table_2_locator"])
            self.assertTrue(row["shared_terms"])
            self.assertEqual(row["status"], "draft")
            self.assertEqual(row["controls_coding"], "false")
            self.assertEqual(int(row["support_pass_count"]), len(row["support_passes"].split("; ")))
        self.assertEqual(set(self.summary), {4, 5, 6})

    def test_example_first_trace_surfaces_foot_care_infection_control(self):
        row = next(row for row in self.rows if row["tag"] == "F687" and row["nors_code"] == "F13")
        self.assertIn("infection prevention practices", row["appendix_example_text"])
        self.assertIn("equipment/devices", row["appendix_example_text"])
        self.assertIn("infection", row["table_2_definition"].lower())
        self.assertEqual(row["status"], "draft")

    def test_generated_csv_has_exact_review_columns(self):
        path = ROOT / "docs/nors_ftag_example_first_batches_4_6.csv"
        if not path.exists():
            self.skipTest("Generate the review CSV before checking its persisted schema")
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, FIELDS)
            for row in reader:
                self.assertEqual(row["status"], "draft")
                self.assertEqual(row["controls_coding"], "false")


if __name__ == "__main__":
    unittest.main()
