"""Tests for build_ct_daily_minimums: rule periods, daily flags, anomaly context and the built files."""
import datetime as dt
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ct_daily_minimums as m  # noqa: E402

RULES = m.load_rules()


def day(census, don=8, rn_admin=0, rn=40, lpn_admin=0, lpn=30, cna=200, nat=0, med=0, contract=0.0, workers=None, excluded=0):
    """A synthetic day record in the daily-file format: [census, workers_total, entries]."""
    hours = [don, rn_admin, rn, lpn_admin, lpn, cna, nat, med]
    entries = []
    for i, h in enumerate(hours):
        ctr = contract * h
        count = None if workers is None else workers[i]
        entries.append([h, h - ctr, ctr, count, excluded if i == 2 else 0])
    entries += [[0, 0, 0, 0, 0]] * 24
    return [census, None, entries]


def flags(record, key="20250115"):
    return m.evaluate_day(key, record, RULES)["flags"]


def has(flag_value, name):
    return bool(flag_value & m.BIT[name])


class RulePeriods(unittest.TestCase):
    def test_boundaries(self):
        cases = {"2021-12-31": "pre2022", "2022-01-01": "statute2022", "2023-02-28": "statute2022",
                 "2023-03-01": "interim2023", "2024-01-04": "interim2023", "2024-01-05": "policy2024", "2026-06-30": "policy2024"}
        for date, expected in cases.items():
            self.assertEqual(m.rule_for(RULES, dt.date.fromisoformat(date))["id"], expected, date)

    def test_periods_are_contiguous_and_sourced(self):
        periods = RULES["periods"]
        for a, b in zip(periods, periods[1:]):
            self.assertEqual(a["_to"] + dt.timedelta(days=1), b["_from"], (a["id"], b["id"]))
        for p in periods:
            self.assertTrue(p["sources"] and all(s["url"].startswith("https://") for s in p["sources"]), p["id"])

    def test_current_numbers(self):
        current = m.rule_for(RULES, dt.date(2026, 1, 1))
        self.assertEqual((current["total"], current["licensed"], current["aide"]), (3.0, 0.84, None))
        interim = m.rule_for(RULES, dt.date(2023, 6, 1))
        self.assertEqual((interim["licensed"], interim["aide"]), (0.84, 2.16))


class DailyFlags(unittest.TestCase):
    # 100 residents: DON 8 + RN 40 + LPN 30 + CNA 200 = 278 h -> 2.78 all, 2.70 direct, 0.78 licensed
    def test_short_day_on_every_basis(self):
        f = flags(day(100))
        self.assertTrue(has(f, "below_total"))
        self.assertTrue(has(f, "below_licensed"))
        self.assertFalse(has(f, "below_direct_only"))

    def test_meets_only_if_director_counts(self):
        f = flags(day(100, don=8, rn=46, lpn=40, cna=210))  # all 3.04, direct 2.96
        self.assertFalse(has(f, "below_total"))
        self.assertTrue(has(f, "below_direct_only"))

    def test_compliant_day(self):
        f = flags(day(100, rn=50, lpn=40, cna=230))
        for name in ("below_total", "below_direct_only", "below_licensed", "rn_under_8"):
            self.assertFalse(has(f, name), name)

    def test_exactly_at_minimum_is_not_short(self):
        f = flags(day(100, don=0, rn=44, lpn=40, cna=216))  # 3.00 total, 0.84 licensed
        self.assertFalse(has(f, "below_total"))
        self.assertFalse(has(f, "below_licensed"))

    def test_aide_rule_only_in_interim_period(self):
        record = day(100, rn=60, lpn=40, cna=200)  # aide 2.00
        self.assertTrue(has(flags(record, "20230615"), "below_aide"))
        self.assertFalse(has(flags(record, "20250615"), "below_aide"))

    def test_pre2022_uses_1_9_total_only(self):
        record = day(100, don=0, rn=20, lpn=20, cna=160)  # 2.00 total, 0.40 licensed
        f = flags(record, "20210615")
        self.assertFalse(has(f, "below_total"))
        self.assertFalse(has(f, "below_licensed"))
        self.assertTrue(has(flags(record, "20220615"), "below_total"))

    def test_rn_under_8_ignores_director(self):
        f = flags(day(100, don=24, rn=6, lpn=60, cna=230))
        self.assertTrue(has(f, "rn_under_8"))
        self.assertFalse(has(flags(day(100, don=0, rn_admin=4, rn=4, lpn=60, cna=240)), "rn_under_8"))

    def test_implausible_day_is_not_counted_as_short(self):
        f = flags(day(100, don=0, rn=10, lpn=10, cna=50))  # 0.70
        self.assertTrue(has(f, "implausible"))
        self.assertFalse(has(f, "below_total"))

    def test_missing_or_excluded_hours_not_evaluated(self):
        self.assertTrue(has(flags(day(0)), "not_evaluated"))
        self.assertTrue(has(flags(day(100, excluded=1)), "not_evaluated"))
        missing = day(100)
        missing[2][4][0] = None
        self.assertTrue(has(flags(missing), "not_evaluated"))

    def test_contract_and_long_hours(self):
        self.assertTrue(has(flags(day(100, rn=50, lpn=40, cna=230, contract=0.6)), "high_contract"))
        self.assertFalse(has(flags(day(100, rn=50, lpn=40, cna=230, contract=0.4)), "high_contract"))
        # 328 nursing hours over 20 workers = 16.4 h each
        self.assertTrue(has(flags(day(100, rn=50, lpn=40, cna=230, workers=[1, 0, 4, 0, 3, 12, 0, 0])), "long_hours"))
        self.assertFalse(has(flags(day(100, rn=50, lpn=40, cna=230, workers=[1, 0, 6, 0, 5, 28, 0, 0])), "long_hours"))
        self.assertFalse(has(flags(day(100, rn=50, lpn=40, cna=230)), "long_hours"))  # no worker counts


class ContextFlags(unittest.TestCase):
    def build_days(self, census_and_cna):
        return [m.evaluate_day(f"202501{i + 1:02d}", day(c, rn=50, lpn=40, cna=cna), RULES) for i, (c, cna) in enumerate(census_and_cna)]

    def test_low_outlier_and_census_jump(self):
        days = self.build_days([(100, 230)] * 6 + [(100, 120)] + [(130, 300)])
        m.add_context_flags(days)
        self.assertTrue(has(days[6]["flags"], "low_outlier"))
        self.assertFalse(has(days[0]["flags"], "low_outlier"))
        self.assertTrue(has(days[7]["flags"], "census_jump"))
        self.assertFalse(has(days[1]["flags"], "census_jump"))

    def test_summary_weekend_gap(self):
        # 2025-01-04 and 05 are a weekend
        days = self.build_days([(100, 230)] * 3 + [(100, 150)] * 2 + [(100, 230)] * 2)
        m.add_context_flags(days)
        s = m.summarize(days)
        self.assertEqual(s["evaluated"], 7)
        self.assertGreater(s["weekend_gap"], 0.15)
        self.assertEqual(s["worst_day"], "20250104")

    def test_summary_marks_suspect_reporting(self):
        days = [m.evaluate_day(f"202501{i + 1:02d}", day(100, don=0, rn=5, lpn=5, cna=20), RULES) for i in range(5)]
        m.add_context_flags(days)
        s = m.summarize(days)
        self.assertTrue(s["suspect_reporting"])
        self.assertEqual(s["below_total"], 0)


class BuiltFiles(unittest.TestCase):
    def test_build_small_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data/ct_daily_staffing/2025Q1").mkdir(parents=True)
            (root / "data/ct_staffing_minimum_rules.json").write_text(m.RULES.read_text(encoding="utf-8"), encoding="utf-8")
            (root / "data/ct_daily_staffing/index.json").write_text(json.dumps(
                {"quarters": {"2025Q1": {}}, "historical_homes": {"075999": "TEST HOME"}}), encoding="utf-8")
            daily = {"20250101": day(100), "20250102": day(100, rn=50, lpn=40, cna=230)}
            (root / "data/ct_daily_staffing/2025Q1/075999.json.gz").write_bytes(gzip.compress(json.dumps(daily).encode()))
            index = m.build(root=root, out=root / "out")
            self.assertEqual(index["quarters"]["2025Q1"]["below_total"], 1)
            self.assertEqual(index["names"]["075999"], "TEST HOME")
            data = json.loads(gzip.decompress((root / "out/2025Q1.json.gz").read_bytes()))
            rows = data["facilities"]["075999"]["days"]
            self.assertEqual(len(rows[0]), len(index["day_fields"]))
            self.assertEqual(rows[0][0], "20250101")


@unittest.skipUnless((m.OUT / "index.json").exists(), "built data not present")
class RealData(unittest.TestCase):
    def test_every_quarter_built_and_counts_consistent(self):
        index = json.loads((m.OUT / "index.json").read_text(encoding="utf-8"))
        catalog = json.loads((m.DAILY / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(set(index["quarters"]), set(catalog["quarters"]))
        for q, s in index["quarters"].items():
            self.assertLessEqual(s["evaluated"], s["days"], q)
            self.assertEqual(s["days"], catalog["quarters"][q]["facility_days"], q)


if __name__ == "__main__":
    unittest.main()
