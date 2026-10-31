import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_ct_legislative_research_stats as stats_builder
import validate_ct_legislative_tracker as validator

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.tracker = load("ct_ltcop_legislative_tracker.json")
        self.stats = load("ct_legislative_research_stats.json")

    def test_published_files_validate(self):
        self.assertEqual(validator.problems(self.tracker, self.stats), [])

    def test_validator_catches_bad_entries(self):
        bad = copy.deepcopy(self.tracker)
        bad["bills_current"].append({"id": "2027-sb1", "session": "2027", "bill": "SB 1", "status": "maybe",
                                     "title": "x", "topics": ["nope"], "summary": "", "related": ["missing"]})
        found = "\n".join(validator.problems(bad, self.stats))
        for expected in ("unknown status maybe", "unknown topic nope", "needs bill_status_url",
                         "needs last_action_date", "related id missing not found"):
            self.assertIn(expected, found)

    def test_stats_rebuild_matches_published(self):
        rebuilt = {s["key"]: s["display"] for s in stats_builder.build()["stats"]}
        published = {s["key"]: s["display"] for s in self.stats["stats"]}
        self.assertEqual(rebuilt, published)

    def test_key_numbers(self):
        s = {x["key"]: x for x in self.stats["stats"]}
        self.assertEqual(s["homes_below_300"]["value"], 36)
        self.assertEqual(s["homes_below_360"]["value"], 120)
        self.assertEqual(s["ltcop_complaints"]["value"], 3253)
        for x in self.stats["stats"]:
            self.assertTrue(x["source"] and x["period"] and x["caveat"], x["key"])

    def test_session_dates(self):
        self.assertEqual(self.tracker["session"]["convenes"], "2027-01-06")
        self.assertEqual(self.tracker["session"]["adjourns"], "2027-06-09")


if __name__ == "__main__":
    unittest.main()
