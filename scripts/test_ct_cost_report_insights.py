"""Tests for data/ct_cost_report_insights.json (Cost Report Insights page)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_ct_cost_report_insights as build  # noqa: E402


class InsightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads((ROOT / "data" / "ct_cost_report_insights.json").read_text(encoding="utf-8"))
        cls.keys = [m["key"] for m in cls.d["metrics"]]

    def test_shape(self):
        self.assertEqual(self.d["schema_version"], build.SCHEMA)
        self.assertGreaterEqual(len(self.d["homes"]), 150)
        self.assertEqual(self.d["years"][0], 2015)
        for h in self.d["homes"]:
            for y, r in h["years"].items():
                self.assertEqual(len(r["v"]), len(self.keys), (h["ccn"], y))

    def test_values_match_published_detail(self):
        bethel = next(h for h in self.d["homes"] if h["ccn"] == "075400")
        det = json.loads((ROOT / "data" / "cost_reports" / "075400.json").read_text(encoding="utf-8"))
        y = next(c for c in det["cost_years"] if c["cost_year"] == 2024)
        v = dict(zip(self.keys, bethel["years"]["2024"]["v"]))
        self.assertEqual(v["expenses"], y["direct_care"]["expenses_per_resident_day"])
        self.assertEqual(v["admin"], y["cost_breakdown"]["categories"]["admin"]["per_resident_day"])
        self.assertEqual(v["management_fees"], y["cost_breakdown"]["details"]["management_fees"]["per_resident_day"])

    def related_party_year(self, ccn, year):
        detail = json.loads((ROOT / "data" / "cost_reports" / f"{ccn}.json").read_text(encoding="utf-8"))
        index = json.loads((ROOT / "data" / "ct_nursing_home_cost_reports.json").read_text(encoding="utf-8"))
        report = next(y for y in detail["cost_years"] if y["cost_year"] == year)
        index_year = next(f for f in index["facilities"] if f["ccn"] == ccn)["years"][str(year)]
        insights = next(h for h in self.d["homes"] if h["ccn"] == ccn)["years"][str(year)]["v"]
        return report, index_year, dict(zip(self.keys, insights))

    def test_partial_related_party_year_withholds_comparable_values(self):
        report, index, insights = self.related_party_year("075330", 2022)
        rent = "rent_or_lease_paid_to_related_parties"
        self.assertGreater(report["related_party_unreadable_rows"], 0)
        self.assertGreater(report["related_party_total_reported"], 0)
        self.assertIs(report["related_party_total_complete"], False)
        self.assertNotIn(rent, report["cost_breakdown"]["details"])
        self.assertIn("rent or lease paid to related parties: some page 4 rows could not be read",
                      report["cost_breakdown"]["withheld_details"])
        self.assertIsNone(index["related_party_total_reported"])
        self.assertNotIn(f"{rent}_per_resident_day", index)
        for key in ("related_parties", "rent_related"):
            self.assertIsNone(build.year_values(report)[key])
            self.assertIsNone(insights[key])

    def test_complete_related_party_year_keeps_comparable_values(self):
        report, index, insights = self.related_party_year("075400", 2025)
        rent = "rent_or_lease_paid_to_related_parties"
        self.assertIsNot(report.get("related_party_total_complete"), False)
        self.assertEqual(report["related_party_total_reported"], 5694819)
        self.assertEqual(index["related_party_total_reported"], 5694819)
        self.assertEqual(report["cost_breakdown"]["details"][rent]["amount"], 10260)
        self.assertEqual(index[f"{rent}_per_resident_day"], 0.18)
        self.assertEqual(insights["rent_related"], 0.18)
        self.assertEqual(insights["related_parties"], round(5694819 / report["resident_days"]["resident_days_total"], 2))

    def test_bands_ordered_and_medians_match_index(self):
        idx = json.loads((ROOT / "data" / "ct_nursing_home_cost_reports.json").read_text(encoding="utf-8"))
        for k, years in self.d["bands"].items():
            for y, (lo, med, hi, n) in years.items():
                self.assertLessEqual(lo, med, (k, y))
                self.assertLessEqual(med, hi, (k, y))
                self.assertGreaterEqual(n, 10)
        self.assertAlmostEqual(self.d["bands"]["expenses"]["2025"][1], idx["statewide_medians"]["2025"]["expenses_per_resident_day"], places=1)

    def test_groups_cover_breakdown_categories_once(self):
        seen = [m for g in self.d["groups"] for m in g["metrics"]]
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(set(seen), {"nursing", "dietary", "housekeeping", "laundry", "other_staff", "other_fees", "admin",
                                     "resident_care", "plant", "property", "interest", "insurance"})
        self.assertLessEqual(len(self.d["groups"]), 8, "share chart stays at <= 8 colors")

    def test_cpi_factors(self):
        f = self.d["cpi"]["factor_to_base"]
        self.assertEqual(f[str(self.d["cpi"]["base_year"])], 1.0)
        years = sorted(f)
        self.assertTrue(all(f[a] >= f[b] for a, b in zip(years, years[1:])), "older years need larger factors")
        cpi = json.loads((ROOT / "data" / "reference" / "cpi_u_us_city_average.json").read_text(encoding="utf-8"))
        avg = build.cost_year_cpi(cpi)
        self.assertAlmostEqual(avg[2025], sum(cpi["monthly"][m] for m in ["2024-10", "2024-11", "2024-12"] + [f"2025-{i:02d}" for i in range(1, 10)]) / 12)

    def test_events_inside_window_and_sorted(self):
        for h in self.d["homes"]:
            dates = [e["date"] for e in h["events"]]
            self.assertEqual(dates, sorted(dates))

    def test_peer_groups(self):
        athena = [k for k, v in self.d["management_companies"].items() if "ATHENA" in (v["name"] or "")]
        self.assertTrue(athena)
        self.assertGreaterEqual(len(self.d["management_companies"][athena[0]]["homes"]), 10)
        self.assertEqual(build.size_bucket(161), "130 to 179 beds")
        self.assertEqual(build.medicaid_bucket(0.9), "85% or more Medicaid")


if __name__ == "__main__":
    unittest.main()
