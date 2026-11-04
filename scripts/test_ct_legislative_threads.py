"""Tests for the storylines, act reference, topic backgrounds, positions schema and
session tooling added in the topics expansion. Run: python scripts/test_ct_legislative_threads.py"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ct_session_weekly_report as weekly  # noqa: E402
import validate_ct_legislative_threads as v  # noqa: E402
import validate_ct_session_tracker as session_v  # noqa: E402


def load(name: str) -> dict:
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


class Base(unittest.TestCase):
    def setUp(self):
        self.tracker = load("ct_ltcop_legislative_tracker.json")
        self.acts = load("ct_ltcop_act_reference.json")
        self.threads = load("ct_ltcop_legislative_threads.json")
        self.positions = load("ct_ltcop_positions.json")
        self.topics = {t["id"] for t in self.tracker["topics"]}
        self.refs = v.all_refs(self.tracker, self.acts)
        self.watch = {b["id"] for b in self.tracker["bills_current"]}

    def thread_problems(self, threads):
        return v.thread_problems(threads, self.topics, self.refs, self.watch)


class PublishedFilesTests(Base):
    def test_validator_passes(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_ct_legislative_threads.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Threads OK: 12 storylines", result.stdout)

    def test_act_reference_matches_builder(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_ct_ltcop_act_reference.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_starting_threads(self):
        ids = [t["id"] for t in self.threads["threads"]]
        self.assertEqual(ids, ["staffing-floor", "staffing-ratios", "direct-care-spending", "discharge-protections", "ownership-transparency", "resident-voice",
                               "assisted-living-oversight", "room-size-capacity", "paying-for-care",
                               "cfc-and-waivers", "husky-c-limits", "pace"])

    def test_every_enacted_past_bill_is_in_the_act_list(self):
        act_ids = {a["id"] for a in self.acts["acts"]}
        missing = [b["id"] for b in self.tracker["bills_past"] if b["enacted"] and b["id"] not in act_ids]
        self.assertEqual(missing, [])
        for b in self.tracker["bills_past"]:
            if b["enacted"]:
                act = next(a for a in self.acts["acts"] if a["id"] == b["id"])
                self.assertTrue(act["public_act"].startswith(b["public_act"]), b["id"])

    def test_acts_cover_every_session(self):
        self.assertEqual(sorted({a["session"] for a in self.acts["acts"]}), [2021, 2022, 2023, 2024, 2025, 2026])
        self.assertGreaterEqual(len(self.acts["acts"]), 50)

    def test_source_checked_corrections(self):
        events = {e["label"]: e for t in self.threads["threads"] for e in t["events"]}
        fax = next(e for e in events.values() if "2022-14" in e["what"])
        self.assertEqual(fax["date"], "2022-02-09")
        pna = next(a for a in self.acts["acts"] if a["id"] == "2021-sb1202")
        self.assertEqual(pna["public_act"], "PA 21-2 (June Special Session)")
        sb1026 = next(e for e in events.values() if e.get("ref") == "2023-sb1026")
        self.assertEqual(sb1026["date"], "2023-03-15")
        community = next(a for a in self.acts["acts"] if a["id"] == "2022-hb5506")
        self.assertIn("Community Ombudsman", community["summary"])

    def test_positions_ship_empty(self):
        self.assertEqual(self.positions["positions"], [])
        self.assertTrue(self.positions["approval_required"])

    def test_threads_never_state_a_position(self):
        self.assertIn(v.NON_POSITION, self.threads["disclaimer"])
        text = json.dumps(self.threads).lower()
        for phrase in ("the program supports", "the program opposes", "ltcop supports", "ltcop opposes", "we support", "we oppose"):
            self.assertNotIn(phrase, text)


class ComparisonTests(Base):
    def test_staffing_comparison_covers_three_approaches(self):
        comp = next(c for c in self.threads["comparisons"] if c["id"] == "staffing-approaches")
        self.assertEqual([r["thread"] for r in comp["rows"]], ["staffing-floor", "staffing-ratios", "direct-care-spending"])
        for r in comp["rows"]:
            self.assertTrue(r["reasons"], r["thread"])
        self.assertEqual(v.comparison_problems(self.threads, self.topics), [])

    def test_direct_care_spending_bills_are_tracked(self):
        past = {b["id"]: b for b in self.tracker["bills_past"]}
        for bid in ("2021-hb6011", "2022-hb5310", "2024-sb156", "2025-sb805", "2026-sb328"):
            self.assertIn(bid, past)
            self.assertFalse(past[bid]["enacted"])
        spend = next(t for t in self.threads["threads"] if t["id"] == "direct-care-spending")
        self.assertEqual({e["ref"] for e in spend["events"] if e["kind"] == "bill"},
                         {"2021-hb6011", "2022-hb5310", "2024-sb156", "2025-sb805", "2026-sb328"})
        self.assertIn("2027-watch-direct-care-spending", spend["watch"])

    def test_bad_comparison_is_caught(self):
        bad = copy.deepcopy(self.threads)
        row = bad["comparisons"][0]["rows"][0]
        row["thread"] = "nope"
        row["reasons"][0]["source_url"] = ""
        row["now_source"] = "http://x"
        found = "\n".join(v.comparison_problems(bad, self.topics))
        self.assertIn("unknown thread nope", found)
        self.assertIn("reason needs an https source_url", found)
        self.assertIn("needs an https now_source", found)


class HomeCareTests(Base):
    def test_home_care_topic_and_watch_items(self):
        topic = next(t for t in self.tracker["topics"] if t["id"] == "home_community_care")
        self.assertGreaterEqual(len(topic["background"]), 2)
        for wid in ("2027-watch-cfc", "2027-watch-husky-c", "2027-watch-pace"):
            self.assertIn(wid, self.watch)

    def test_cfc_storyline_records_the_proposal_and_its_outcome(self):
        cfc = next(t for t in self.threads["threads"] if t["id"] == "cfc-and-waivers")
        labels = [e["label"] for e in cfc["events"]]
        self.assertIn("Governor proposes ending CFC and moving participants to waivers", labels)
        self.assertIn("Final budget keeps CFC as a state plan option", labels)
        self.assertIn("2027-watch-budget", cfc["watch"])

    def test_husky_c_bills_are_tracked_as_not_enacted(self):
        past = {b["id"]: b for b in self.tracker["bills_past"]}
        for bid in ("2025-hb6911", "2025-sb807", "2026-hb5302", "2026-sb326", "2022-hb5333"):
            self.assertFalse(past[bid]["enacted"], bid)


class ThreadValidatorTests(Base):
    def test_bad_threads_are_caught(self):
        bad = copy.deepcopy(self.threads)
        th = bad["threads"][0]
        th["events"][0]["ref"] = "2099-hb1"
        th["events"][1]["source_url"] = "http://example.com"
        th["events"][2]["label"] = "one two three four five six seven eight nine ten eleven twelve thirteen"
        th["events"][3]["kind"] = "rumor"
        th["events"][4]["date"] = "2020-01-01"
        th["watch"] = ["2027-watch-nothing"]
        th["topics"] = ["not_a_topic"]
        th["status"] = "maybe"
        bad["threads"][1]["id"] = th["id"]
        found = "\n".join(self.thread_problems(bad))
        for expect in ("ref 2099-hb1 not found", "needs an https source_url", "label missing or over 12 words",
                       "unknown kind rumor", "not in date order", "watch id 2027-watch-nothing", "unknown topic not_a_topic",
                       "unknown status maybe", "duplicate id"):
            self.assertIn(expect, found)

    def test_long_summary_and_missing_disclaimer(self):
        bad = copy.deepcopy(self.threads)
        bad["threads"][0]["summary"] = "word " * 61
        bad["disclaimer"] = "Storylines."
        found = "\n".join(self.thread_problems(bad))
        self.assertIn("summary over 60 words", found)
        self.assertIn("non-position line", found)

    def test_good_fixture_passes(self):
        self.assertEqual(self.thread_problems(self.threads), [])


class ActAndBackgroundTests(Base):
    def test_bad_acts_are_caught(self):
        bad = copy.deepcopy(self.acts)
        bad["acts"][1]["id"] = bad["acts"][0]["id"]
        bad["acts"][2]["summary"] = "word " * 31
        bad["acts"][3]["source_url"] = "https://example.com/act.pdf"
        bad["acts"][4]["public_act"] = "Public Act 21"
        bad["acts"][5]["topics"] = []
        found = "\n".join(v.act_problems(bad, self.topics))
        for expect in ("duplicate id", "summary over 30 words", "cga.ct.gov", "public_act must look like", "needs at least one topic"):
            self.assertIn(expect, found)

    def test_bad_background_is_caught(self):
        bad = copy.deepcopy(self.tracker)
        bad["topics"][0]["background"][0]["year"] = 2022
        bad["topics"][1]["background"][0]["source_url"] = ""
        bad["topics"][2]["background"] = bad["topics"][2]["background"][:1]
        found = "\n".join(v.background_problems(bad))
        self.assertIn("before 2021", found)
        self.assertIn("needs an https source_url", found)
        self.assertIn("2 to 6 entries", found)

    def test_every_topic_has_sourced_background(self):
        self.assertEqual(v.background_problems(self.tracker), [])


class PositionTests(Base):
    def test_approved_fixture_passes(self):
        fixture = {"schema_version": "ct-ltcop-positions-1.0", "approval_required": True, "positions": [
            {"id": "fixture-1", "topic": "staffing_workforce", "threads": ["staffing-floor"], "text": "Fixture text for a test only.",
             "basis_url": "https://example.org/record", "basis_label": "Fixture record", "approved_by": "Fixture approver", "approved_date": "2026-01-01"}]}
        self.assertEqual(v.position_problems(fixture, self.topics, {"staffing-floor"}), [])

    def test_unapproved_or_draft_positions_are_refused(self):
        fixture = {"schema_version": "ct-ltcop-positions-1.0", "approval_required": True, "positions": [
            {"id": "fixture-2", "topic": "staffing_workforce", "text": "Fixture text.", "basis_url": "https://example.org"}],
            "draft_positions": []}
        found = "\n".join(v.position_problems(fixture, self.topics, set()))
        self.assertIn("draft keys are not allowed", found)
        self.assertIn("needs approved_by", found)
        self.assertIn("needs approved_date", found)


class SessionToolTests(unittest.TestCase):
    def setUp(self):
        self.cur = load("ct_ltcop_bill_tracker_2026.json")
        self.threads = load("ct_ltcop_legislative_threads.json")

    def test_session_validator_accepts_optional_topics(self):
        data = copy.deepcopy(self.cur)
        data["bills"][0]["topics"] = ["staffing_workforce"]
        self.assertEqual(session_v.problems(data), [])
        data["bills"][0]["topics"] = ["nope"]
        self.assertTrue(any("unknown topic" in p for p in session_v.problems(data)))

    def test_weekly_report_groups_moves_by_storyline(self):
        prev = copy.deepcopy(self.cur)
        bill = next(b for b in prev["bills"] if b["id"] == "2026-sb125")
        bill["status"] = "passed_one"
        text = weekly.render(self.cur, prev, threads=self.threads)
        self.assertIn("## Moves by storyline", text)
        self.assertIn("### Nursing home financial transparency and accountability", text)
        self.assertIn("SB 125: Passed one chamber → Signed into law", text)

    def test_weekly_report_lists_untagged_bills(self):
        cur = copy.deepcopy(self.cur)
        for b in cur["bills"]:
            b["topics"] = ["staffing_workforce"]
        cur["bills"][0]["topics"] = []
        text = weekly.render(cur, cur, threads=self.threads)
        self.assertIn("## Untagged bills", text)
        self.assertIn(f"**No topic:** {cur['bills'][0]['bill']}", text)
        self.assertIn("**In no storyline:**", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
