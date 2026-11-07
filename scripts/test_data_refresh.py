"""Offline tests for the data-source registry, the freshness check and the refresh helpers."""
import csv
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "refresh"))

import validate_data_freshness as fresh  # noqa: E402
import refresh_sources as rs  # noqa: E402


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = json.loads((ROOT / "data" / "data_sources.json").read_text(encoding="utf-8"))

    def test_every_source_is_complete(self):
        ids = set()
        for s in self.reg["sources"]:
            for k in ("id", "name", "publisher", "page", "access", "frequency", "frequency_basis", "check",
                      "max_age_days", "version_kind", "feeds"):
                self.assertIn(k, s, f"{s.get('id')} lacks {k}")
            self.assertTrue(s["page"].startswith("https://"))
            self.assertNotIn(s["id"], ids)
            ids.add(s["id"])
            self.assertIn(s["access"]["type"], ("cms_provider_data", "cms_data_api", "socrata", "manual"))

    def test_methodology_page_lists_every_source(self):
        html = (ROOT / "staffing" / "tools" / "nursing-home-staffing-methodology.html").read_text(encoding="utf-8")
        for s in self.reg["sources"]:
            self.assertIn(f'data-source-id="{s["id"]}"', html, s["id"])
            self.assertIn(s["page"], html, s["id"])

    def test_every_source_version_is_found_on_the_site(self):
        have = fresh.on_site_versions()
        for s in self.reg["sources"]:
            self.assertIn(s["id"], have, f"no on-site version found for {s['id']}")


class FreshnessTests(unittest.TestCase):
    def test_file_name_dates(self):
        self.assertEqual(fresh.month_from_name("NH_ProviderInfo_Aug2026.csv"), dt.date(2026, 8, 1))
        self.assertEqual(fresh.month_from_name("SNF_Enrollments_2026.05.01.csv"), dt.date(2026, 5, 1))
        self.assertEqual(fresh.month_from_name("2026-10"), dt.date(2026, 10, 1))
        self.assertEqual(fresh.quarter_end("2025Q4"), dt.date(2025, 12, 31))
        self.assertEqual(fresh.quarter_end("2026Q1"), dt.date(2026, 3, 31))

    def test_overdue_follows_the_limit(self):
        rows = {r["id"]: r for r in fresh.report(dt.date(2026, 11, 6))}
        pbj = rows["cms_pbj"]
        self.assertEqual(pbj["status"], "OK" if pbj["age_days"] <= pbj["max_age_days"] else "OVERDUE")
        far = {r["id"]: r for r in fresh.report(dt.date(2030, 1, 1))}
        self.assertTrue(all(r["status"] == "OVERDUE" for r in far.values()))


class RefreshHelperTests(unittest.TestCase):
    def test_latest_pdc(self):
        item = {"modified": "2026-10-01", "distribution": [{"downloadURL":
                "https://data.cms.gov/provider-data/sites/default/files/resources/x/NH_ProviderInfo_Oct2026.csv"}]}
        when, url, modified = rs.latest_pdc(item)
        self.assertEqual((when, modified), (dt.date(2026, 10, 1), "2026-10-01"))
        self.assertTrue(url.endswith("NH_ProviderInfo_Oct2026.csv"))

    def test_latest_catalog_picks_newest_csv(self):
        cat = {"dataset": [{"title": "Skilled Nursing Facility Change of Ownership", "distribution": [
            {"title": "Skilled Nursing Facility Change of Ownership : 2025-09-01", "mediaType": "text/csv",
             "downloadURL": "https://data.cms.gov/a/SNF_CHOW_2025.10.01.csv"},
            {"title": "Skilled Nursing Facility Change of Ownership : 2025-12-01", "format": "API",
             "accessURL": "https://data.cms.gov/data-api/v1/dataset/x/data"},
            {"title": "Skilled Nursing Facility Change of Ownership : 2025-12-01", "mediaType": "text/csv",
             "downloadURL": "https://data.cms.gov/b/SNF_CHOW_2026.01.02.csv"}]}]}
        when, url = rs.latest_catalog(cat, "Skilled Nursing Facility Change of Ownership")
        self.assertEqual(when, dt.date(2025, 12, 1))
        self.assertTrue(url.endswith("SNF_CHOW_2026.01.02.csv"))

    def test_is_newer(self):
        self.assertTrue(rs.is_newer("cms_pbj", "quarter", dt.date(2026, 4, 1), dt.date(2026, 3, 31)))
        self.assertFalse(rs.is_newer("cms_pbj", "quarter", dt.date(2026, 1, 1), dt.date(2026, 3, 31)))
        self.assertTrue(rs.is_newer("x", "month", dt.date(2026, 10, 1), dt.date(2026, 8, 1)))
        self.assertFalse(rs.is_newer("x", "month", dt.date(2026, 8, 15), dt.date(2026, 8, 1)))
        self.assertIsNone(rs.is_newer("x", "month", None, dt.date(2026, 8, 1)))

    def test_ct_copy(self):
        with tempfile.TemporaryDirectory() as t:
            src, dst = Path(t) / "a.csv", Path(t) / "b.csv"
            with open(src, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["PROVNUM", "STATE", "MDScensus"])
                w.writerows([["075001", "CT", "150"], ["335001", "NY", "90"], ["075002", "ct", "80"]])
            n, col = rs.ct_copy(src, dst)
            self.assertEqual((n, col), (2, "STATE"))
            self.assertEqual(len(dst.read_text(encoding="utf-8").strip().splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
