import csv
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CMSTitleTests(unittest.TestCase):
    def test_citation_titles_match_locked_csv(self):
        source = ROOT / "source_data/cms_survey/NH_CitationDescriptions_May2026.csv"
        lock = json.loads((ROOT / "data/nors_source_pack_lock.json").read_text(encoding="utf-8-sig"))
        entry = next(x for x in lock["revision4_source_inventory"]["files"] if x["name"] == source.name)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), entry["sha256"])
        with source.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        titles = {f"F{int(m.group(1))}": row["Deficiency Description"].strip()
                  for row in rows if (m := re.fullmatch(r"F-0*(\d+)", row["Deficiency Prefix and Number"].strip()))}
        tags = json.loads((ROOT / "data/appendix_pp/index.json").read_text(encoding="utf-8"))["tags"]
        for tag in tags:
            self.assertIn(tag["tag"], titles)
            self.assertEqual(tag["cms_short_title"], titles[tag["tag"]])
            self.assertEqual(tag["cms_short_title_status"], "cms_citation_description")


if __name__ == "__main__":
    unittest.main()
