#!/usr/bin/env python3
"""Tests for the static reporting API (scripts/build_reporting_api.py).

Builds the API into a temp folder from the committed /data and checks schema
validity, evidence rules, missing-data handling, entity separation and the
Cherry Brook screening case. Run: python scripts/test_reporting_api.py
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_reporting_api as b  # noqa: E402

CHERRY_BROOK = "075396"
CLOSED_HOME = "075001"


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


class ReportingApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="reporting-api-"))
        cls.stats = b.Builder(cls.tmp).run()
        cls.v1 = cls.tmp / "v1"
        cls.schema = jload(ROOT / "scripts" / "reporting_api_report.schema.json")
        cls.reports = sorted(cls.v1.glob("reports/*/*.json"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ------------------------------------------------------------ structure
    def test_every_roster_ccn_has_all_endpoints_and_reports(self):
        roster = jload(ROOT / "data" / "nursing_home_facility_roster_ct.json")["records"]
        for r in roster:
            ccn = r["ccn"]
            for ep in ("profile", "ownership", "staffing", "financials", "inspections"):
                self.assertTrue((self.v1 / "facilities" / ccn / f"{ep}.json").exists(), (ccn, ep))
            for t in b.REPORT_TYPES:
                self.assertTrue((self.v1 / "reports" / t / f"{ccn}.json").exists(), (ccn, t))

    def test_invalid_ccn_has_no_file(self):
        for bad in ("000000", "07539", "ABCDEF", "../etc"):
            self.assertFalse((self.v1 / "facilities" / bad / "profile.json").exists(), bad)

    def test_index_templates_resolve(self):
        idx = jload(self.v1 / "index.json")
        for key, tpl in idx["url_templates"].items():
            path = tpl.replace(b.SITE + "/api/", "").format(ccn=CHERRY_BROOK, report_type="staffing-analysis",
                                                              company_id="mc-athena-health-care-associates-inc")
            self.assertTrue((self.tmp / path).exists(), (key, path))

    def test_build_is_deterministic(self):
        tmp2 = Path(tempfile.mkdtemp(prefix="reporting-api-2-"))
        try:
            b.Builder(tmp2).run()
            for rel in ("v1/index.json", f"v1/reports/facility-comprehensive/{CHERRY_BROOK}.json", "v1/search-index.json"):
                h1 = hashlib.sha256((self.tmp / rel).read_bytes()).hexdigest()
                h2 = hashlib.sha256((tmp2 / rel).read_bytes()).hexdigest()
                self.assertEqual(h1, h2, rel)
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

    # --------------------------------------------------------------- schema
    def test_all_reports_validate_against_schema(self):
        import jsonschema
        v = jsonschema.Draft202012Validator(self.schema, format_checker=jsonschema.FormatChecker())
        self.assertGreater(len(self.reports), 1000)
        for p in self.reports:
            errs = list(v.iter_errors(jload(p)))
            self.assertEqual(errs, [], f"{p}: {errs[0].message if errs else ''}")

    # ------------------------------------------------------------- evidence
    def test_findings_carry_traceable_evidence(self):
        for p in self.reports:
            rep = jload(p)
            for f in rep["findings"]:
                self.assertTrue(f["evidence"], (p, f["id"]))
                for e in f["evidence"]:
                    self.assertTrue(e["url"] or e["site_file"], (p, f["id"]))
                    self.assertTrue(e["dataset"] and e["agency"], (p, f["id"]))
                    self.assertIn("record_id", e)
                if f["kind"] == "calculated":
                    self.assertTrue(f.get("formula"), (p, f["id"]))
            keys = {s["source_key"] for s in rep["sources"]}
            for f in rep["findings"]:
                for e in f["evidence"]:
                    self.assertIn(e["source_key"], keys, (p, f["id"]))

    def test_possible_associations_never_assert_conflict(self):
        hedges = ("does not by itself", "by name only", "can mean", "not proof")
        n = 0
        for p in self.reports:
            for f in jload(p)["findings"]:
                if f["kind"] == "possible_association":
                    n += 1
                    s = f["statement"].lower()
                    self.assertTrue(any(h in s for h in hedges), (p, f["statement"][:120]))
                    self.assertNotIn("conflict of interest exists", s)
        self.assertGreater(n, 50)

    # ------------------------------------------------------------ Cherry Brook
    def test_cherry_brook_related_party_screening(self):
        rep = jload(self.v1 / "reports" / "related-party-screening" / f"{CHERRY_BROOK}.json")
        text = json.dumps(rep).upper()
        rp = [f for f in rep["findings"] if f["id"].startswith("rp-2025") and f["kind"] == "confirmed_fact"]
        self.assertTrue(any("NEW HORIZONS" in f["statement"].upper() and "288,000" in f["statement"] for f in rp))
        # Athena: historical management, not current
        mg = [r for r in rep["relationships"] if r.get("company_id") == "mc-athena-health-care-associates-inc"]
        self.assertEqual(len(mg), 1)
        self.assertFalse(mg[0]["current"])
        self.assertEqual(mg[0]["end"], "2025-03-26")
        # Serene / Adir are not in the data and must not appear as findings
        self.assertNotIn("SERENE", text)
        self.assertNotIn("ADIR", text)
        self.assertTrue(any(f["kind"] == "investigative_question" for f in rep["findings"]))

    def test_unlisted_names_absent_from_search_index(self):
        keys = [e["key"] for e in jload(self.v1 / "search-index.json")["entries"]]
        for name in ("SERENE HEALTH SERVICES", "ADIR HEALTHCARE"):
            self.assertFalse(any(b.norm_name(name) in k for k in keys), name)
        self.assertTrue(any("NEW HORIZONS" in k for k in keys))

    # --------------------------------------------------------- entity rules
    def test_same_name_different_ids_not_merged(self):
        entries = jload(self.v1 / "search-index.json")["entries"]
        by_name = {}
        for e in entries:
            if e["type"].startswith("cms_owner"):
                by_name.setdefault(e["key"], set()).add(e["id"])
        self.assertTrue(any(len(ids) > 1 for ids in by_name.values()),
                        "expected at least one name shared by different CMS associate ids, kept separate")

    def test_shared_principals_use_cms_ids(self):
        own = jload(self.v1 / "facilities" / CHERRY_BROOK / "ownership.json")
        for r in own["cms_ownership_and_control"]:
            for other in r["also_listed_at_ccns"]:
                o2 = jload(self.v1 / "facilities" / other / "ownership.json")
                self.assertTrue(any(x["cms_associate_id"] == r["cms_associate_id"] for x in o2["cms_ownership_and_control"]))

    # --------------------------------------------------------- missing data
    def test_missing_cost_reports_are_explicit(self):
        idx = jload(ROOT / "data" / "ct_nursing_home_cost_reports.json")
        have = {f["ccn"] for f in idx["facilities"]}
        no_cost = [c for c in (p.parent.name for p in self.v1.glob("facilities/*/profile.json")) if c not in have
                   or not jload(self.v1 / "facilities" / c / "financials.json")["years"]]
        for ccn in no_cost:
            rep = jload(self.v1 / "reports" / "financial-transparency" / f"{ccn}.json")
            self.assertTrue(any(m["field"] == "dss_cost_reports" for m in rep["missing_data"]), ccn)
            self.assertNotIn("direct_care_per_resident_day", rep["metrics"])

    def test_closed_home_flagged(self):
        rep = jload(self.v1 / "reports" / "facility-comprehensive" / f"{CLOSED_HOME}.json")
        self.assertEqual(rep["findings"][0]["id"], "status")
        self.assertIn("closed", rep["findings"][0]["statement"])

    def test_staffing_quarters_sorted_with_benchmarks(self):
        st = jload(self.v1 / "facilities" / CHERRY_BROOK / "staffing.json")
        qs = [q["quarter"] for q in st["quarters"]]
        self.assertEqual(qs, sorted(qs))
        self.assertTrue(all(q["statewide_median_total_nurse_hprd"] is not None for q in st["quarters"]))

    def test_wages_not_confused_with_department_spending(self):
        fin = jload(self.v1 / "facilities" / CHERRY_BROOK / "financials.json")
        y = fin["years"][-1]
        for dept in ("dietary", "housekeeping", "laundry"):
            self.assertLessEqual(y[dept]["wages_reported"], y[dept]["total_department_cost"], dept)
        self.assertIn("Not total department spending", fin["definitions"]["wages_reported"])

    # ------------------------------------------------------------- privacy
    def test_no_individual_addresses_or_local_paths(self):
        for p in list(self.v1.glob("facilities/*/ownership.json"))[:40]:
            for r in jload(p)["cms_ownership_and_control"]:
                self.assertNotIn("address", r)
        sample = (self.v1 / "reports" / "facility-comprehensive" / f"{CHERRY_BROOK}.json").read_text(encoding="utf-8")
        for bad in ("C:\\", "X:\\", "/home/", "Users\\Dan"):
            self.assertNotIn(bad, sample)

    # ---------------------------------------------------------- page parity
    def test_js_normalization_matches_python(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        js = (ROOT / "Assets" / "reporting-api-reports.js").read_text(encoding="utf-8")
        start = js.index("function norm(s)")
        end = js.index("\n  }\n", start) + 4
        samples = ["Athena Health Care Associates, Inc.", "New Horizons Inc. d/b/a Cherry", "I CARE MANAGEMENT", "O'Brien & Co., LLC"]
        code = js[start:end] + "\nconsole.log(JSON.stringify(%s.map(norm)));" % json.dumps(samples)
        out = subprocess.run([node, "-e", code], capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(out), [b.norm_name(s) for s in samples])


if __name__ == "__main__":
    unittest.main(verbosity=1)
