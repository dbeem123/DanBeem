import json
import unittest
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data" / "appendix_pp"


class AppendixSectionLabels(unittest.TestCase):
    def test_long_tag_guidance_does_not_return_to_regulation(self):
        for tag in ("F880", "F690", "F627", "F867", "F628"):
            with self.subTest(tag=tag):
                passages = json.loads((DATA / f"{tag}.json").read_text(encoding="utf-8"))["passages"]
                regulation = [p for p in passages if p["section_label"] == "Regulation"]
                self.assertGreater(len(regulation), 0)
                self.assertLessEqual(len(regulation), 20)
                non_rule_seen = False
                for passage in passages:
                    label = passage["section_label"]
                    if label not in ("Regulation", "Appendix PP text"):
                        non_rule_seen = True
                    if non_rule_seen:
                        self.assertNotEqual(label, "Regulation")


if __name__ == "__main__":
    unittest.main()
