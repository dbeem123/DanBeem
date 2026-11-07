"""Tests for the DSS cost-report parser and the published cost-report data."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "cost_reports"))
sys.path.insert(0, str(ROOT / "scripts"))

from cr_extract import extract, derive, checks  # noqa: E402
from cr_entities import extract_entities, categorize  # noqa: E402
from cr_parse import split_pages, page_header  # noqa: E402
from cr_period import read_period  # noqa: E402
import build_ct_cost_reports as build  # noqa: E402

FIX = ROOT / "scripts" / "cost_reports" / "fixtures"


class ParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new = extract((FIX / "bethel_2023.txt").read_text(encoding="utf-8"))   # 2023 form: combined CCNH / RHNS column
        cls.old = extract((FIX / "governors_house_2016.txt").read_text(encoding="utf-8"))  # 2016 form: separate CCNH and RHNS

    def test_header_combined_and_separate_columns(self):
        _, P = self.new
        names = [n for n, _ in page_header(P["10"][0])[0]]
        self.assertEqual(names[:3], ["NH", "NH.Adjustment", "NH.Hours"])
        _, P = self.old
        names = [n for n, _ in page_header(P["10"][0])[0]]
        self.assertEqual(names[:4], ["CCNH", "CCNH.Hours", "RHNS", "RHNS.Hours"])

    def test_resident_days_new_form(self):
        r, _ = self.new
        self.assertEqual(r["days_medicare"], 8931)
        self.assertEqual(r["days_medicaid_ct"], 32507)
        self.assertEqual(r["days_private"], 5058)          # CCNH/RHNS column, not the all-levels 12,837
        self.assertEqual(r["days_total_care"], 50847)
        self.assertEqual(r["resident_days_total"], 50929)
        self.assertTrue(checks(r)["days_sum"])

    def test_salaries_hours_and_pool_old_form(self):
        r, _ = self.old   # values checked by eye against the PDF page images
        self.assertEqual(r["sal_don"], 112062)
        self.assertEqual(r["sal_rn_direct"], 672868)
        self.assertEqual(r["hrs_rn_direct"], 17107)
        self.assertEqual(r["sal_rn_admin"], 7093)
        self.assertEqual(r["sal_lpn_direct"], 514692)
        self.assertEqual(r["sal_aides"], 942128)
        self.assertEqual(r["hrs_aides"], 54434)
        self.assertEqual(r["sal_total"], 3013968)
        self.assertEqual(r["pool_rn_direct"], 5978)
        self.assertEqual(r["pool_lpn_direct"], -5215)

    def test_revenue_and_balance_sheet(self):
        r, _ = self.new
        self.assertEqual(r["rev_total"], 26633262)
        self.assertEqual(r["rev_total_all"], 29128791)
        self.assertEqual(r["liabilities_total"], 32320105)
        self.assertEqual(r["net_income_p36"], 1122291)
        c = checks(r)
        self.assertTrue(c["revenue_sum"] and c["liabilities_sum"] and c["has_core"])

    def test_direct_care_definition(self):
        r, _ = self.new
        d = derive(r)
        self.assertEqual(d["direct_salaries"], 354617 + 1080590 + 435274 + 1139860 + 85951 + 2729617)
        self.assertEqual(d["nursing_pool"], 251659 + 1510295 + 798649)
        self.assertAlmostEqual(d["direct_care_total"], d["direct_salaries"] + d["nursing_pool"] + d["direct_fringe_allocated"])
        self.assertTrue(150 < d["direct_care_per_resident_day"] < 260)

    def test_entities(self):
        _, P = self.new
        e = extract_entities(P)
        names = [p["name"] for p in e["partners_members"]]
        self.assertIn("Bethel Investors, LLC", names)
        self.assertEqual(e["partners_members"][0]["percent"], 51.0)
        self.assertEqual(e["management_services"][0]["cost"], 1135620)
        rp = {r["name_guess"]: r for r in e["related_parties"]}
        self.assertEqual(rp["Bethel Realty"]["cost_reported"], 2030126)
        self.assertEqual(rp["Bethel Realty"]["category"], "rent / lease / real estate")
        self.assertEqual(categorize("Drugs/OTC/RX Consulting"), "pharmacy / supplies")

    def test_plausibility_flags(self):
        self.assertIn("resident days vs beds", build.plausible({"resident_days_total": 900000, "beds_certified": 100}, {}))
        self.assertEqual(build.plausible({"resident_days_total": 33000, "beds_certified": 100},
                                         {"direct_care_per_resident_day": 180, "nursing_hours_per_resident_day": 4.2,
                                          "direct_care_share_of_expenses": 0.41}), [])


class PeriodTests(unittest.TestCase):
    def test_certification_sentence(self):
        s, e = read_period("I certify ... for the cost report period beginning October 1, 2024 and ending June 14, 2025, and that", 2025)
        self.assertEqual((s.isoformat(), e.isoformat()), ("2024-10-01", "2025-06-14"))

    def test_period_covered_box_and_misspelling(self):
        s, e = read_period("Period Covered: From To\nHome LLC 6/7/2024 9/30/2024", 2024)
        self.assertEqual((s.isoformat(), e.isoformat()), ("2024-06-07", "2024-09-30"))
        s, e = read_period("period beginning October 1, 2024 and ending Septembe 30, 2025", 2025)
        self.assertEqual(e.isoformat(), "2025-09-30")

    def test_rejects_dates_outside_the_cost_year(self):
        self.assertEqual(read_period("period beginning October 1, 2020 and ending September 30, 2021", 2025), (None, None))

    def test_fixtures_are_full_years(self):
        for name, year in (("bethel_2023.txt", 2023), ("governors_house_2016.txt", 2016)):
            s, e = read_period((FIX / name).read_text(encoding="utf-8"), year)
            if s:
                self.assertGreaterEqual((e - s).days, 359)


class PublishedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx = json.loads((ROOT / "data" / "ct_nursing_home_cost_reports.json").read_text(encoding="utf-8"))

    def test_schema_and_detail_files(self):
        self.assertEqual(self.idx["schema_version"], "ct-nursing-home-cost-reports-1.0")
        for f in self.idx["facilities"]:
            self.assertRegex(f["ccn"], r"^07\d{4}$")
            if f["has_detail"]:
                self.assertTrue((ROOT / "data" / "cost_reports" / f"{f['ccn']}.json").exists(), f["ccn"])

    def test_validated_years_in_range(self):
        for f in self.idx["facilities"]:
            for y, r in f["years"].items():
                self.assertTrue(2010 <= int(y) <= 2026)
                if r["validated"] and r["direct_care_per_resident_day"] is not None:
                    self.assertTrue(40 <= r["direct_care_per_resident_day"] <= 900, (f["ccn"], y))


if __name__ == "__main__":
    unittest.main()
