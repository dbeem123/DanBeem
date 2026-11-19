import gzip
import json
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

from build_ct_daily_staffing import collect, number
from fetch_ct_daily_staffing import pages, summarize_workers


class DailyStaffingTests(unittest.TestCase):
    def test_worker_counts_distinct_across_roles_and_contracts(self):
        def row(worker, role, kind, hours, excluded=""):
            return dict(PROVNUM="075001", SYS_EMPLEE_ID=worker, EMPLEE_JOB_CD_ID=role,
                        EMP_CTR=kind, WORK_HRS_NUM=hours, WORK_HRS_FN=excluded)
        summary = summarize_workers([row("a", 7, "emp", 2), row("a", 7, "ctr", 1),
                                     row("a", 6, "emp", 2), row("b", 7, "emp", 4),
                                     row("c", 7, "emp", 0), row("d", 1, "emp", 7, "1")])
        self.assertEqual(summary, {"075001": {"total": 2, "roles": {7: 2, 6: 1}}})

    def test_api_filters_use_release_specific_case(self):
        with patch("fetch_ct_daily_staffing.cms_keys", return_value={"STATE":"state"}), \
             patch("fetch_ct_daily_staffing.request", return_value=[{"state":"CT"}]) as get:
            self.assertEqual(list(pages("release", STATE="CT")), [{"STATE":"CT"}])
            self.assertEqual(get.call_args.args[1]["filter[state]"], "CT")

    def test_missing_and_excluded_hours(self):
        base = dict(STATE="CT", PROVNUM="75001", CY_QTR="2026Q2", WORKDATE="20260615", MDSCENSUS="0",
                    Hrs_FoodSvc="0", Hrs_FoodSvc_emp="0", Hrs_Admin="3", Hrs_Admin_fn="1")
        days = defaultdict(dict)
        collect(days, [base], [(17,4,"FeedAsst",""),(1,5,"Admin","")], "2026Q2")
        record = days["075001"]["20260615"]
        self.assertEqual(record["roles"], {17:[0,0,None,0],1:[None,None,None,1]})
        self.assertEqual(record["census"], 0)
        self.assertIsNone(number(""))
        with self.assertRaises(ValueError):
            number("nan")

    def test_published_manifest_and_sample(self):
        root = Path(__file__).resolve().parents[1] / "data/ct_daily_staffing"
        index = json.loads((root / "index.json").read_bytes())
        role_ids = [r["id"] for r in index["roles"]]
        self.assertEqual(len(set(role_ids)), 32)
        for ccn, quarters in index["facilities"].items():
            self.assertEqual(quarters, sorted(set(quarters)))
            for quarter in quarters:
                self.assertTrue((root / quarter / (ccn + ".json.gz")).is_file())
        latest = max(index["quarters"])
        home = "075319"
        with gzip.open(root / latest / (home + ".json.gz"), "rt") as stream:
            for census, workers, fields in json.load(stream).values():
                self.assertEqual(len(fields), len(role_ids))
                self.assertGreater(census, 0)
                self.assertGreater(workers, 0)
                self.assertLessEqual(max((row[3] or 0) for row in fields), workers)
