import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_nursing_home_ct_statewide_context as builder

ROOT = Path(__file__).resolve().parents[1]


def row(quarter, total, licensed, status, applicable, below_total=None, below_licensed=None):
    return {
        "quarter": quarter,
        "quarter_label": f"Q{quarter[-1]} {quarter[:4]}",
        "ct_comparison_period_status": status,
        "ct_comparison_applicable_for_public_status": applicable,
        "ct_total_direct_care_below_comparison_point": below_total,
        "ct_licensed_below_comparison_point": below_licensed,
        "metrics": {
            "ct_direct_care_total_hprd_estimate": total,
            "ct_direct_care_licensed_nurse_hprd_estimate": licensed,
        },
    }


REFERENCE = {"scenario_levels": [
    {"hprd": 3.0, "label": "current", "kind": "current"},
    {"hprd": 3.6, "label": "proposed", "kind": "proposed"},
]}


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.history = {
            "generated_at": "2026-09-24T00:00:00",
            "history_window": {"quarters": ["2021Q4", "2026Q1"]},
            "facility_quarterly_staffing_history": [
                row("2021Q4", 2.5, 0.5, "reference_only", False),
                row("2021Q4", 3.5, 1.0, "reference_only", False),
                row("2026Q1", 2.9, 0.80, "applicable_full_quarter", True, True, True),
                row("2026Q1", 3.4, 1.0, "applicable_full_quarter", True, False, False),
                row("2026Q1", 3.7, 1.2, "applicable_full_quarter", True, False, False),
            ],
        }

    def test_no_status_counts_before_applicable_quarters(self):
        out = builder.build(self.history, REFERENCE)
        early = out["statewide_quarterly"][0]
        self.assertIsNone(early["below_total_3_00_count"])
        self.assertIsNone(early["below_licensed_0_84_count"])
        self.assertEqual(early["median_ct_direct_care_total_hprd"], 3.0)

    def test_applicable_quarter_uses_public_flags(self):
        latest = builder.build(self.history, REFERENCE)["statewide_quarterly"][-1]
        self.assertEqual(latest["below_total_3_00_count"], 1)
        self.assertEqual(latest["below_licensed_0_84_count"], 1)
        self.assertEqual(latest["facilities_reporting"], 3)

    def test_scenarios_latest_quarter_only(self):
        levels = builder.build(self.history, REFERENCE)["latest_quarter_scenarios"]["levels"]
        self.assertEqual([lv["facilities_below"] for lv in levels], [1, 2])
        self.assertEqual(levels[1]["facilities_with_estimate"], 3)

    def test_published_export_matches_known_2026q2_values(self):
        path = ROOT / "data" / "nursing_home_ct_statewide_context.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        latest = data["statewide_quarterly"][-1]
        self.assertEqual(latest["quarter"], "2026Q2")
        self.assertEqual((latest["facilities_reporting"], latest["below_total_3_00_count"],
                          latest["below_licensed_0_84_count"]), (171, 18, 4))
        by_level = {lv["hprd"]: lv["facilities_below"] for lv in data["latest_quarter_scenarios"]["levels"]}
        self.assertEqual(by_level[3.6], 95)
        first_applicable = next(r for r in data["statewide_quarterly"] if r["ct_comparison_applicable_for_public_status"])
        self.assertEqual(first_applicable["quarter"], "2023Q2")


if __name__ == "__main__":
    unittest.main()
