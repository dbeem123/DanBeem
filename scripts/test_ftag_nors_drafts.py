import json
import re
import unittest
from pathlib import Path

from build_ftag_nors_drafts import has_term

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


class DraftPairingsTests(unittest.TestCase):
    def test_coverage_evidence_and_example_priority(self):
        result = read(DATA / "ftag_nors_crosswalk.json")
        tags = result["tags"]
        self.assertFalse(result["controls_coding"])
        self.assertEqual({x["f_tag"] for x in tags}, {x["tag"] for x in read(DATA / "appendix_pp/index.json")["tags"]})
        codes = {x["id"]: x for x in read(DATA / "nors_primary_authority.json")["authority_records"] if x["authority_type"] == "nors_table_2_definition"}
        for tag in tags:
            source = read(DATA / "appendix_pp" / (tag["f_tag"] + ".json"))
            passages = {p["id"]: p for p in source["passages"]}
            self.assertEqual(tag["status"], "draft")
            self.assertFalse(tag["controls_coding"])
            self.assertEqual(bool(tag["unmapped_reason"]), not bool(tag["pairings"]))
            for pair in tag["pairings"]:
                self.assertEqual(pair["status"], "draft")
                self.assertFalse(pair["controls_coding"])
                pp = pair["appendix_pp"]
                nors = pair["nors_table_2"]
                passage = passages[pp["passage_id"]]
                code = codes[nors["authority_id"]]
                self.assertIn(pp["excerpt"], passage["text"])
                self.assertIn(nors["excerpt"], code["text"])
                self.assertTrue(pair["shared_terms"])
                self.assertTrue(all(has_term(passage["text"], term) and has_term(code["text"], term) for term in pair["shared_terms"]))
                if pp["is_example"]:
                    self.assertTrue(passage["is_example"])
                    self.assertEqual(pair["mapping_basis"], "both")
                else:
                    self.assertFalse(any(p.get("is_example") and any(has_term(p["text"], term) for term in pair["shared_terms"]) for p in source["passages"]))
        f554 = next(row for row in tags if row["f_tag"] == "F554")
        d09 = next(row for row in f554["pairings"] if row["nors_code"] == "D09")
        self.assertEqual(d09["evidence_strength"], "weak_generic_term")

    def test_review_batch_scope(self):
        text = (ROOT / "docs/nors_ftag_crosswalk_review_batch_1.md").read_text(encoding="utf-8")
        tags = {row["f_tag"]: row for row in read(DATA / "ftag_nors_crosswalk.json")["tags"]}
        for tag in re.findall(r"^\| (F\d+) \|", text, re.M):
            self.assertRegex(tags[tag]["cfr_section"], r"^§?483\.(?:10|12)(?:\(|$)")
        self.assertIn("weak", text.lower())


if __name__ == "__main__":
    unittest.main()
