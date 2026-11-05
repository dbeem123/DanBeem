import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_ct_administrators_public as pub
import validate_ct_administrators as val

ROOT = Path(__file__).resolve().parents[1]


def role(rid, lic, fac, start, end, open_=False, name="Pat A Doe"):
    return {"id": rid, "name_raw": name.upper(), "name": name, "license_number": lic,
            "facility_license": fac, "facility_name": f"HOME {fac}", "start": start, "end": end,
            "open": open_, "flags": []}


def review():
    return {
        "privacy_check": "passed", "source_as_of": "2026-11-05",
        "summary": {"earliest_role_date": "2010-01-01", "latest_role_date": "2026-10-01"},
        "sources": [{"id": "ct_open_data_ngch_56tr", "as_of": "2026-11-05T15:00:00+00:00"}],
        "crosswalk_review": [
            {"facility_license": "1", "facility_name": "HOME 1"},
            {"facility_license": "2", "facility_name": "HOME 2"},
            {"facility_license": "3", "facility_name": "HOME 3"},
        ],
        "people": [
            {"id": "nha-10", "name": "Pat A Doe", "license_number": "10", "license_status": "ACTIVE",
             "license_as_of": "2026-11-05", "license_issued": "1901-01-01", "license_expires": "2028-01-31",
             "license_observations": [{"name": "PAT A DOE", "source": "ct_open_data_ngch_56tr"},
                                      {"name": "PAT DOE", "source": "ct_dph_nursing_home_administrator_registry"}],
             "roles": [
                 role("r1", "10", "1", "2018-01-01", "2020-06-30"),
                 role("r1b", "10", "1", "2018-01-01", "2020-06-30"),       # exact duplicate
                 role("r2", "10", "2", "2020-06-30", "2021-12-31"),       # one-day handoff only
                 role("r3", "10", "3", "2021-11-01", None, open_=True),   # two-month overlap with r2
             ]},
            {"id": "nha-20", "name": "Lee Roe", "license_number": "20", "license_status": "INACTIVE",
             "license_as_of": "2026-11-05", "license_issued": "2001-05-01", "license_expires": "2019-01-31",
             "license_observations": [{"name": "LEE ROE", "source": "ct_open_data_ngch_56tr"}],
             "roles": [role("r4", "20", "3", None, "2015-01-01", name="Lee Roe")]},
        ],
        "unlinked_roles": [
            role("u1", None, "3", "2021-11-01", None, open_=True),            # repeats r3 exactly
            role("u2", None, "2", "2005-01-01", "2009-01-01", name="Sam Q Poe"),
        ],
    }


DECISIONS = {"1": "075001", "2": "075002", "3": "075003"}
HISTORY = {"history_window": {"latest_quarter": "2026Q1"}, "facility_quarterly_staffing_history": [
    {"ccn": "075001", "quarter": f"{y}Q{q}", "quarter_start_date": f"{y}-{3*q-2:02d}-01",
     "quarter_end_date": f"{y}-{3*q:02d}-{30 if q in (2, 3) else 31}", "resident_days": 9000,
     "metrics": {"ct_direct_care_total_hprd_estimate": 3.0 + q / 10, "total_nurse_hprd": 3.5, "rn_hprd": 0.5}}
    for y in (2017, 2018, 2019, 2020, 2021) for q in (1, 2, 3, 4) if (y, q) >= (2017, 4)]}
STAFFING = {"facilities": [
    {"ccn": "075001", "provider_name": "HOME 1", "address": "1 A ST"},
    {"ccn": "075002", "provider_name": "HOME 2", "address": "2 B ST"},
    {"ccn": "075003", "provider_name": "HOME 3", "address": "3 C ST"},
    {"ccn": "075009", "provider_name": "UNCOVERED HOME", "address": "9 D ST"},
    {"ccn": "075008", "provider_name": "CLOSED HOME", "address": ""},
]}


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.out = pub.build(review(), DECISIONS, HISTORY, STAFFING)
        self.people = {p["id"]: p for p in self.out["people"]}

    def test_duplicates_collapse_and_handoffs_are_not_overlaps(self):
        roles = {r["id"]: r for r in self.people["nha-10"]["roles"]}
        self.assertNotIn("r1b", roles)
        self.assertFalse(roles["r1"]["overlap"])        # one-day handoff into r2
        self.assertTrue(roles["r2"]["overlap"] and roles["r3"]["overlap"])

    def test_placeholder_issue_date_and_names(self):
        p = self.people["nha-10"]
        self.assertIsNone(p["license_issued"])
        self.assertEqual(p["name"], "Pat A Doe")
        self.assertIn("Pat Doe", p["other_names"])

    def test_unlinked_roles_only_under_facilities_and_exact_repeats_dropped(self):
        fac = {f["facility_license"]: f for f in self.out["facilities"]}
        unlinked = [a for f in fac.values() for a in f["administrators"] if a["person_id"] is None]
        self.assertEqual([a["name"] for a in unlinked], ["Sam Q Poe"])
        self.assertEqual(self.out["summary"]["unlinked_roles"], 1)
        self.assertEqual(len(self.out["people"]), 2)

    def test_tenure_context_uses_quarter_midpoints_and_needs_a_start(self):
        roles = {r["id"]: r for r in self.people["nha-10"]["roles"]}
        ctx = roles["r1"]["context"]
        self.assertEqual((ctx["first_quarter"], ctx["last_quarter"], ctx["quarters"]), ("2018Q1", "2020Q2", 10))
        self.assertIsNone(self.people["nha-20"]["roles"][0]["context"])  # no start recorded

    def test_coverage_lists_active_cms_homes_missing_from_dph(self):
        self.assertEqual([c["ccn"] for c in self.out["coverage"]["cms_homes_not_in_dph_export"]], ["075009"])

    def test_suppression_removes_person_everywhere(self):
        out = pub.build(review(), DECISIONS, HISTORY, STAFFING,
                        [{"action": "suppress_person", "person_id": "nha-20"}])
        self.assertNotIn("nha-20", {p["id"] for p in out["people"]})
        self.assertFalse(any(a["person_id"] == "nha-20" for f in out["facilities"] for a in f["administrators"]))
        self.assertEqual(out["corrections_applied"], 1)

    def test_rejects_unreviewed_privacy_or_duplicate_ccn(self):
        bad = review()
        bad["privacy_check"] = "failed"
        with self.assertRaises(ValueError):
            pub.build(bad, DECISIONS, HISTORY, STAFFING)
        path = ROOT / "data" / "testing" / "_tmp_decisions.json"
        path.parent.mkdir(exist_ok=True)
        try:
            path.write_text(json.dumps([
                {"facility_license": "1", "ccn": "075001", "decision": "accepted", "note": "x"},
                {"facility_license": "2", "ccn": "075001", "decision": "accepted", "note": "y"}]))
            with self.assertRaises(ValueError):
                pub.load_decisions(path)
        finally:
            path.unlink(missing_ok=True)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.good = pub.build(review(), DECISIONS, HISTORY, STAFFING)
        self.ccns = {f["ccn"] for f in STAFFING["facilities"]}

    def test_good_fixture_passes(self):
        self.assertEqual(val.problems(self.good, self.ccns), [])

    def test_private_values_and_fields_fail(self):
        for mutate in (
            lambda d: d["people"][0].__setitem__("name", "Pat Doe 12 Elm Street"),
            lambda d: d["people"][0].__setitem__("other_names", ["Pat Doe 06511"]),
            lambda d: d["people"][0].__setitem__("other_names", ["pat@example.com"]),
            lambda d: d["facilities"][0].__setitem__("zip", "06511"),
        ):
            bad = copy.deepcopy(self.good)
            mutate(bad)
            self.assertTrue(val.problems(bad, self.ccns), mutate)

    def test_integrity_failures(self):
        bad = copy.deepcopy(self.good)
        bad["facilities"][1]["ccn"] = bad["facilities"][0]["ccn"]
        self.assertTrue(any("more than one" in p for p in val.problems(bad, self.ccns)))
        bad = copy.deepcopy(self.good)
        bad["people"][0]["license_issued"] = "1901-01-01"
        self.assertTrue(val.problems(bad, self.ccns))
        bad = copy.deepcopy(self.good)
        bad["caveats"] = bad["caveats"][:1]
        self.assertTrue(any("performance caveat" in p for p in val.problems(bad, self.ccns)))

    def test_published_file_passes_when_present(self):
        path = ROOT / "data" / "ct_nursing_home_administrators.json"
        if path.exists():
            staffing = json.loads((ROOT / "data" / "nursing_home_staffing_ct.json").read_text())
            data = json.loads(path.read_text())
            self.assertEqual(val.problems(data, {f["ccn"] for f in staffing["facilities"]}), [])


if __name__ == "__main__":
    unittest.main()
