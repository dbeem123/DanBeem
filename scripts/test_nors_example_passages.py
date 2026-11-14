import json
import re
import unittest
from pathlib import Path

from scripts.build_nors_primary_data import is_example_passage


DATA = Path(__file__).resolve().parents[1] / "data" / "appendix_pp"


class AppendixExamples(unittest.TestCase):
    def test_all_trigger_phrases_are_case_insensitive(self):
        for phrase in ("For example", "EXAMPLES INCLUDE", "Such as", "e.g.", "May Include"):
            with self.subTest(phrase=phrase):
                self.assertTrue(is_example_passage(f"Guidance: {phrase} a resident."))
        for text in ("This is ordinary guidance.", "maybe included", "such assertion"):
            with self.subTest(text=text):
                self.assertFalse(is_example_passage(text))

    def test_every_generated_passage_has_accurate_boolean_flag(self):
        index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
        pattern = re.compile(r"\b(?:for example|examples include|such as|may include)\b|(?<!\w)e\.g\.", re.I)
        examples = 0
        for item in index["tags"]:
            record = json.loads((DATA / f"{item['tag']}.json").read_text(encoding="utf-8"))
            for passage in record["passages"]:
                self.assertIs(type(passage.get("is_example")), bool)
                expected = bool(pattern.search(passage["text"])) or bool(passage.get("example_context_inherited"))
                self.assertEqual(passage["is_example"], expected, (item["tag"], passage["pdf_page"]))
                examples += expected
                if passage.get("example_context_inherited"):
                    previous = next(p for p in record["passages"] if p["id"] == passage["continued_from_passage_id"])
                    self.assertTrue(previous["is_example"])
                    self.assertTrue(previous["text"].rstrip().endswith(":"))
                    self.assertEqual(previous["continuation_passage_id"], passage["id"])
                    self.assertEqual(previous["pdf_page"] + 1, passage["pdf_page"])
        f567 = json.loads((DATA / "F567.json").read_text(encoding="utf-8"))
        lead = next(p for p in f567["passages"] if "Examples of noncompliance may include" in p["text"])
        self.assertIn("Requiring residents to deposit", lead["text"])
        self.assertGreater(examples, 0)


if __name__ == "__main__":
    unittest.main()
