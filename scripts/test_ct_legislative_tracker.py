import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_ct_legislative_research_stats as stats_builder
import validate_ct_legislative_tracker as validator
import validate_ct_session_tracker as session_validator
import ct_session_weekly_report as weekly

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
        self.assertEqual(s["ltcop_funding"]["display"], "$2.42 million")
        topics = {topic["id"]: topic for topic in self.tracker["topics"]}
        self.assertNotIn("raised DPH civil penalties", topics["quality_oversight"]["why"])
        self.assertNotIn("every", topics["discharge_rights"]["context_facts"][0]["text"].lower())
        for x in self.stats["stats"]:
            self.assertTrue(x["source"] and x["period"] and x["caveat"], x["key"])

    def test_session_dates(self):
        self.assertEqual(self.tracker["session"]["convenes"], "2027-01-06")
        self.assertEqual(self.tracker["session"]["adjourns"], "2027-06-09")


class SessionTrackerTests(unittest.TestCase):
    def setUp(self):
        self.data = load("ct_ltcop_bill_tracker_2026.json")

    def test_2026_file_validates(self):
        self.assertEqual(session_validator.problems(self.data), [])

    def test_2026_counts(self):
        bills = self.data["bills"]
        self.assertEqual(len(bills), 131)
        self.assertEqual(sum(b["list"] == 1 for b in bills), 111)
        self.assertEqual(sum(b["status"] == "signed" for b in bills), 20)
        self.assertEqual({b["bill"]: b["public_act"] for b in bills if b["status"] == "signed"}["SB 125"], "PA 26-103")

    def test_validator_catches_bad_rows(self):
        bad = copy.deepcopy(self.data)
        bad["bills"][0].update({"status": "signed", "public_act": None})
        bad["bills"][1].update({"status": "maybe"})
        found = "\n".join(session_validator.problems(bad))
        self.assertIn("signed bill needs public_act", found)
        self.assertIn("unknown status maybe", found)

    def test_final_report_rejects_in_progress_status(self):
        bad = copy.deepcopy(self.data)
        bad["bills"][2].update({"status": "introduced", "public_act": None})
        self.assertIn("in-progress status introduced", "\n".join(session_validator.problems(bad)))


class Session2027Tests(unittest.TestCase):
    def setUp(self):
        self.data = load("ct_ltcop_bill_tracker_2027.json")

    def test_2027_file_validates_and_matches_session(self):
        self.assertEqual(session_validator.problems(self.data), [])
        self.assertEqual(self.data["session"]["convenes"], "2027-01-06")
        self.assertEqual(self.data["session"]["adjourns"], "2027-06-09")
        self.assertFalse(self.data["report"]["final"])

    def test_2027_statuses_cover_in_progress_and_end_of_session(self):
        ids = {s["id"] for s in self.data["statuses"]}
        self.assertTrue({"introduced", "hearing", "committee_passed", "passed_one", "passed_both",
                         "signed", "vetoed", "hearing_only", "no_action"} <= ids)


class WeeklyReportTests(unittest.TestCase):
    def setUp(self):
        self.cur = copy.deepcopy(load("ct_ltcop_bill_tracker_2026.json"))
        self.cur["report"].update({"label": "Week of 10/26/2026 (test)", "final": False})
        for b in self.cur["bills"][:3]:
            b["status"] = "committee_passed" if b["status"] != "committee_passed" else "passed_one"
        self.cur["bills"][3]["status"] = "hearing"
        self.cur["bills"][3]["latest_action_date"] = "2026-09-01"

    def test_report_lists_moves_new_bills_and_checklist(self):
        prev = copy.deepcopy(load("ct_ltcop_bill_tracker_2026.json"))
        prev["bills"] = prev["bills"][1:]
        text = weekly.render(self.cur, prev)
        self.assertIn("**New:** " + self.cur["bills"][0]["bill"], text)
        self.assertIn("**Moved:** " + self.cur["bills"][1]["bill"], text)
        self.assertIn("| " + self.cur["bills"][3]["bill"] + " |", text)
        self.assertIn("60 \u26a0", text)
        self.assertNotIn("| SB 125 |", text)

    def test_empty_session_renders(self):
        text = weekly.render(load("ct_ltcop_bill_tracker_2027.json"), None)
        self.assertIn("No previous version found", text)
        self.assertIn("No bills yet.", text)


if __name__ == "__main__":
    unittest.main()
