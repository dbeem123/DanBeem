"""Fail-case tests for the public policy layer (validator, content scan, fail-closed export).

All records here are synthetic test fixtures, not policy content.
Run: python scripts/test_ct_policy.py
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_public_policy as exporter  # noqa: E402
import validate_ct_policy as validator  # noqa: E402

RULES = validator.load("ct_policy_rules.json")
TRACKER = validator.load("ct_ltcop_legislative_tracker.json")
STATS = validator.load("ct_legislative_research_stats.json")["stats"]
BILL = TRACKER["bills_past"][0]["id"]
ACT = validator.load("ct_ltcop_act_reference.json")["acts"][0]["id"]
THREAD = validator.load("ct_ltcop_legislative_threads.json")["threads"][0]["id"]
TOPIC = TRACKER["topics"][0]["id"]
STAT = STATS[0]["key"]
SRC = "https://www.cga.ct.gov/current/pub/chap_368v.htm"


def record(pid="NH-900", **extra):
    r = {
        "id": pid, "title": "Synthetic test record", "status": "active", "priority_areas": ["test_area"],
        "population": ["NH"], "pathway": ["statute"], "question": "What does current law require?",
        "current_law": [{"citation": "CGS 19a-550", "quote": "Synthetic quoted text.", "source_url": SRC, "verified_date": "2026-11-27"}],
        "sources": [{"label": "Connecticut General Statutes, chapter 368v", "url": SRC, "as_of": "2026-11-27"}],
        "bill_ids": [BILL], "act_ids": [ACT], "thread_ids": [THREAD], "topic_ids": [TOPIC], "stat_keys": [STAT],
        "last_verified": "2026-11-27",
    }
    r.update(extra)
    return r


def public_doc(*policies, approved=None):
    doc = copy.deepcopy(validator.load("ct_policy_public.json"))
    doc["policies"] = list(policies)
    if approved is not None:
        doc["approved"] = approved
    return doc


def problems(doc=None, **others):
    docs = {"ct_policy_public.json": doc or public_doc()}
    docs.update(others)
    return validator.problems(docs, run_scan=False)


class ValidatorTests(unittest.TestCase):
    def test_published_files_validate(self):
        self.assertEqual(validator.problems(), [])

    def test_good_record_passes(self):
        self.assertEqual(problems(public_doc(record())), [])

    def assertFlags(self, doc, needle, **others):
        found = problems(doc, **others)
        self.assertTrue(any(needle in p for p in found), f"expected {needle!r} in {found}")

    def test_internal_key_fails(self):
        self.assertFlags(public_doc(record(owner="someone")), "unknown key 'owner'")

    def test_draft_key_fails(self):
        self.assertFlags(public_doc(record(draft_text="x")), "forbidden key 'draft_text'")

    def test_unknown_file_key_fails(self):
        doc = public_doc(record())
        doc["notes_for_me"] = "x"
        self.assertFlags(doc, "unknown key 'notes_for_me'")

    def test_email_phone_path_and_markers_fail(self):
        for text, needle in (
            ("Contact someone@example.org", "email address"),
            ("Call 860-555-0100", "phone number"),
            ("See C:\\Users\\x\\policy.docx", "Windows path"),
            ("CONFIDENTIAL review copy", "confidential marker"),
            ("Do not publish yet", "do-not-publish marker"),
            ("Draft language attached", "draft language marker"),
        ):
            self.assertFlags(public_doc(record(question=text)), needle)

    def test_statute_wording_is_not_a_marker(self):
        q = {"citation": "CGS 19a-550", "quote": "records of the program shall remain confidential, unless otherwise provided", "source_url": SRC, "verified_date": "2026-11-27"}
        self.assertEqual(problems(public_doc(record(current_law=[q]))), [])

    def test_unapproved_gated_field_fails(self):
        gap = {"text": "Synthetic gap.", "basis_label": "Statute", "basis_url": SRC}
        self.assertFlags(public_doc(record(gaps=[gap])), "gaps needs approval")
        self.assertEqual(problems(public_doc(record(gaps=[gap]), approved={"NH-900": ["gaps"]})), [])

    def test_unpublished_position_fails(self):
        self.assertFlags(public_doc(record(position_id="pos-1")), "not a published position")

    def test_dangling_ids_fail(self):
        self.assertFlags(public_doc(record(bill_ids=["2099-hb0001"])), "dangling bill id")
        self.assertFlags(public_doc(record(thread_ids=["no-such-thread"])), "dangling thread id")
        self.assertFlags(public_doc(record(see_also=["NH-999"])), "dangling see_also id")
        self.assertFlags(public_doc(record(parent="NH-999")), "dangling parent")

    def test_duplicate_and_malformed_ids_fail(self):
        self.assertFlags(public_doc(record(), record()), "duplicate id")
        self.assertFlags(public_doc(record("nh-1")), "id must match")

    def test_quote_needs_verified_date_and_allowed_https_source(self):
        q = {"citation": "CGS 19a-550", "quote": "x", "source_url": SRC}
        self.assertFlags(public_doc(record(current_law=[q])), "quote without verified_date")
        q2 = dict(q, verified_date="2026-11-27", source_url="http://www.cga.ct.gov/x")
        self.assertFlags(public_doc(record(current_law=[q2])), "needs an https URL")
        q3 = dict(q2, source_url="https://example.com/x")
        self.assertFlags(public_doc(record(current_law=[q3])), "not on the allowed list")

    def test_gap_needs_published_basis(self):
        gap = {"text": "Synthetic gap.", "basis_label": "Statute"}
        self.assertFlags(public_doc(record(gaps=[gap]), approved={"NH-900": ["gaps"]}), "gap without a published basis")

    def test_label_cannot_change(self):
        doc = public_doc(record())
        doc["label"] = "Program position"
        self.assertFlags(doc, "label must equal")

    def test_implementation_unverified_is_not_overdue(self):
        impl = copy.deepcopy(validator.load("ct_implementation.json"))
        item = {"id": "i1", "act_id": ACT, "provision": "Synthetic provision", "agency": "DSS",
                "deadline": "2027-02-15", "status": "overdue_verified", "evidence_url": SRC, "source_url": SRC, "checked_date": "2026-11-27"}
        impl["items"] = [item]
        self.assertFlags(None, "overdue only when", **{"ct_implementation.json": impl})
        impl["items"] = [dict(item, status="unverified")]
        self.assertEqual(problems(None, **{"ct_implementation.json": impl}), [])
        impl["items"] = [dict(item, deadline="2026-01-01", status="not_due")]
        self.assertFlags(None, "not_due but the deadline has passed", **{"ct_implementation.json": impl})

    def test_regulatory_window_and_authority_quote(self):
        reg = copy.deepcopy(validator.load("ct_regulatory_actions.json"))
        reg["actions"] = [{"id": "r1", "agency": "DPH", "title": "Synthetic", "stage": "comment_open", "url": SRC,
                           "comment_open": "2027-02-01", "comment_close": "2027-01-01", "checked_date": "2026-11-27"}]
        self.assertFlags(None, "comment window ends before it opens", **{"ct_regulatory_actions.json": reg})
        auth = copy.deepcopy(validator.load("ct_ltc_authorities.json"))
        auth["authorities"] = [{"id": "a1", "kind": "state_statute", "citation": "CGS 19a-550", "quote": "x", "source_url": SRC}]
        self.assertFlags(None, "quote without verified_date", **{"ct_ltc_authorities.json": auth})


class LawPageTests(unittest.TestCase):
    def test_law_page_matches_the_data(self):
        import build_ct_law_page as page
        doc = json.loads((validator.DATA / "ct_ltc_authorities.json").read_text(encoding="utf-8"))
        current = (page.OUT).read_text(encoding="utf-8")
        self.assertEqual(current, page.render(doc), "Run python scripts/build_ct_law_page.py")
        for a in doc["authorities"]:
            self.assertIn(f'id="{a["id"]}"', current)


class ExportTests(unittest.TestCase):
    def run_build(self, private):
        return exporter.build(private, RULES, source_version="test", today="2026-11-27")

    def test_unapproved_record_excluded_and_internal_dropped(self):
        keep = record("NH-901", release_eligible=True, owner="x", draft_text="x", fiscal_notes="x")
        drop = record("NH-902", release_eligible=False)
        pol, _, notes = self.run_build({"policies": [keep, drop]})
        self.assertEqual([p["id"] for p in pol["policies"]], ["NH-901"])
        self.assertFalse({"owner", "draft_text", "fiscal_notes", "release_eligible"} & set(pol["policies"][0]))
        self.assertTrue(any("NH-902" in n for n in notes))
        self.assertEqual(validator.problems({"ct_policy_public.json": pol}, run_scan=False), [])

    def test_gated_field_needs_approval_evidence_and_listing(self):
        gap = [{"text": "Synthetic gap.", "basis_label": "Statute", "basis_url": SRC}]
        base = record("NH-903", release_eligible=True, gaps=gap)
        pol, _, _ = self.run_build({"policies": [dict(base, approval_status="approved", approved_fields=["gaps"])]})
        self.assertNotIn("gaps", pol["policies"][0])  # no evidence
        pol, _, _ = self.run_build({"policies": [dict(base, approval_status="approved", approval_evidence="x", approved_fields=[])]})
        self.assertNotIn("gaps", pol["policies"][0])  # not listed
        pol, _, _ = self.run_build({"policies": [dict(base, approval_status="approved", approval_evidence="x", approved_fields=["gaps"])]})
        self.assertEqual(pol["policies"][0]["gaps"], gap)
        self.assertEqual(pol["approved"], {"NH-903": ["gaps"]})
        self.assertNotIn("approval_evidence", json.dumps(pol))

    def test_unknown_key_stops_everything(self):
        with self.assertRaises(exporter.ExportError):
            self.run_build({"policies": [record("NH-904", release_eligible=True, mystery="x")]})
        with self.assertRaises(exporter.ExportError):
            self.run_build({"policies": [], "extra": []})

    def test_cli_dry_run_writes_nothing_and_bad_content_stops(self):
        before = (validator.DATA / "ct_policy_public.json").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "p.json"
            good.write_text(json.dumps({"policies": [record("NH-905", release_eligible=True)]}))
            self.assertEqual(exporter.main([str(good), "--source-version", "t1"]), 0)
            bad = Path(tmp) / "b.json"
            bad.write_text(json.dumps({"policies": [record("NH-906", release_eligible=True, question="email me at a@b.org")]}))
            self.assertEqual(exporter.main([str(bad), "--source-version", "t1", "--write"]), 1)
            self.assertEqual(exporter.main([str(good), "--source-version", "C:\\x"]), 2)
        self.assertEqual((validator.DATA / "ct_policy_public.json").read_bytes(), before)

    def test_diff_lists_new_removed_changed(self):
        lines = exporter.diff([{"id": "A", "x": 1}, {"id": "B"}], [{"id": "A", "x": 2}, {"id": "C"}], "policy")
        self.assertIn("+ policy C (new, becomes public)", lines)
        self.assertIn("- policy B (removed from public)", lines)
        self.assertIn("~ policy A: x", lines)


if __name__ == "__main__":
    unittest.main()
