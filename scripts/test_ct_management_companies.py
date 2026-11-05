import copy
import csv
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_ct_management_companies as mc
import build_ct_management_relationships as rel
import extract_ct_ownership_orgs as ext
import validate_ct_management_companies as val

ROOT = Path(__file__).resolve().parents[1]
NEW = ["CMS Certification Number (CCN)", "Provider Name", "Provider Address", "City/Town", "State", "ZIP Code",
       "Role played by Owner or Manager in Facility", "Owner Type", "Owner Name", "Ownership Percentage",
       "Association Date", "Location", "Processing Date"]
OLD = ["PROVNUM", "PROVNAME", "ADDRESS", "CITY", "STATE", "ZIP", "ROLE_DESC", "OWNER_TYPE", "OWNER_NAME",
       "OWNER_PERCENTAGE", "ASSOCIATION_DATE", "filedate"]


def archive(tmp: Path, release: str, name: str, header: list[str], rows: list[list[str]]) -> Path:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    path = tmp / f"nursing-homes_{release}.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(name, buf.getvalue())
    return path


class ExtractTests(unittest.TestCase):
    def test_keeps_only_connecticut_organizations_and_no_addresses(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            rows_new = [
                ["075001", "HOME A", "1 MAIN ST", "HARTFORD", "CT", "06101", "OPERATIONAL/MANAGERIAL CONTROL",
                 "Organization", "ACME CARE LLC", "NOT APPLICABLE", "since 01/02/2019", "x", "2026-10-01"],
                ["075001", "HOME A", "1 MAIN ST", "HARTFORD", "CT", "06101", "W-2 MANAGING EMPLOYEE",
                 "Individual", "DOE, JANE", "", "since 01/02/2019", "x", "2026-10-01"],
                ["225001", "HOME B", "2 ELM ST", "BOSTON", "MA", "02101", "OPERATIONAL/MANAGERIAL CONTROL",
                 "Organization", "OTHER LLC", "", "since 01/02/2019", "x", "2026-10-01"],
            ]
            a = archive(tmp, "2026-10-28", "y2hd_NH_Ownership_Oct2026.csv", NEW, rows_new)
            b = archive(tmp, "2020-01-09", "Ownership_Download.csv", OLD,
                        [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[12]] for r in rows_new])
            for path in (a, b):
                release, rows = ext.extract(path)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["owner_name"], "ACME CARE LLC")
                self.assertEqual(set(rows[0]), set(ext.KEEP))
                self.assertNotIn("06101", json.dumps(rows))
            empty = tmp / "nursing-homes_2026-08-06.zip"
            with zipfile.ZipFile(empty, "w") as z:
                z.writestr("NH_ProviderInfo.csv", "x\n")
            self.assertIsNone(ext.extract(empty)[1])


def row(ccn, org, assoc="since 03/01/2018", role="OPERATIONAL/MANAGERIAL CONTROL"):
    return {"ccn": ccn, "provider_name": f"HOME {ccn}", "role": role, "owner_type": "Organization",
            "owner_name": org, "pct": "", "association": assoc, "processing_date": ""}


class RelationshipTests(unittest.TestCase):
    def setUp(self):
        r = ["2020-01-09", "2020-02-09", "2020-03-09", "2020-04-09", "2020-05-09", "2020-06-09", "2020-07-09"]
        self.out = rel.build({
            r[0]: [row("075001", "ACME CARE LLC"), row("075002", "ACME CARE LLC")],
            r[1]: [row("075001", "ACME CARE, LLC"), row("075009", "X", role="5% OR GREATER DIRECT OWNERSHIP INTEREST")],
            r[2]: [],                                                   # reporting gap
            r[3]: [row("075001", "ACME CARE LLC")],
            r[4]: [],
            r[5]: [],
            r[6]: [row("075001", "ACME CARE LLC", "since 06/15/2020"), row("075002", "ACME CARE LLC", "since 07/01/2020")],
        })

    def test_short_gaps_join_and_long_gaps_split(self):
        p = [x for x in self.out["relationships"] if x["ccn"] == "075001"]
        self.assertEqual(len(p), 1)                                     # gaps of 1 and 2 releases
        self.assertTrue(p[0]["current"])
        self.assertEqual(p[0]["association_dates"], ["2018-03-01", "2020-06-15"])
        q = [x for x in self.out["relationships"] if x["ccn"] == "075002"]
        self.assertEqual(len(q), 2)                                     # gap of 5 releases
        self.assertEqual((q[0]["last_seen"], q[0]["ended_by"]), ("2020-01-09", "2020-02-09"))
        self.assertEqual(q[1]["association_dates"], ["2020-07-01"])

    def test_only_management_roles_and_name_punctuation_joined(self):
        self.assertEqual({x["org"] for x in self.out["relationships"]}, {"ACME CARE LLC"})
        self.assertEqual(sum(self.out["name_variants"]["ACME CARE LLC"].values()), 6)


ADMINS = {"people": [{"id": "nha-1"}], "facilities": [
    {"ccn": "075001", "facility_name": "HOME ONE", "administrators": [
        {"person_id": "nha-1", "name": "Pat Doe", "license_number": "1", "start": "2019-01-01", "end": None, "open": True},
        {"person_id": None, "name": "Lee Roe", "license_number": None, "start": "2010-01-01", "end": "2015-01-01", "open": False}]}]}
HISTORY = {"history_window": {"latest_quarter": "2026Q1"}, "facility_quarterly_staffing_history": [
    {"ccn": "075001", "quarter": "2019Q2", "quarter_start_date": "2019-04-01", "quarter_end_date": "2019-06-30",
     "resident_days": 9000, "metrics": {"ct_direct_care_total_hprd_estimate": 3.2, "total_nurse_hprd": 3.6, "rn_hprd": 0.5}}]}
STAFFING = {"facilities": [{"ccn": "075001", "provider_name": "HOME ONE"}]}


def relationships():
    return {"releases": ["2020-01-09", "2026-10-28"], "provider_names": {"075001": "HOME ONE", "075002": "HOME TWO"},
            "name_variants": {"ACME CARE LLC": {"ACME CARE LLC": 2}, "ACME CARE INC": {"ACME CARE INC": 1},
                              "BETA & SONS LLC": {"BETA & SONS LLC": 1}, "BETA AND SONS LLC": {"BETA AND SONS LLC": 1}},
            "relationships": [
                {"ccn": "075001", "org": "ACME CARE LLC", "first_seen": "2020-01-09", "last_seen": "2026-10-28",
                 "ended_by": None, "current": True, "releases": 2, "association_dates": ["2018-03-01"],
                 "roles": ["OPERATIONAL/MANAGERIAL CONTROL"]},
                {"ccn": "075002", "org": "ACME CARE INC", "first_seen": "2020-01-09", "last_seen": "2020-01-09",
                 "ended_by": "2026-10-28", "current": False, "releases": 1, "association_dates": [],
                 "roles": ["OPERATIONAL/MANAGERIAL CONTROL"]},
                {"ccn": "075002", "org": "BETA & SONS LLC", "first_seen": "2026-10-28", "last_seen": "2026-10-28",
                 "ended_by": None, "current": True, "releases": 1, "association_dates": ["2026-09-01"],
                 "roles": ["CONTRACTED MANAGING EMPLOYEE"]},
                {"ccn": "075001", "org": "BETA AND SONS LLC", "first_seen": "2020-01-09", "last_seen": "2020-01-09",
                 "ended_by": "2026-10-28", "current": False, "releases": 1, "association_dates": ["2019-01-01"],
                 "roles": ["CONTRACTED MANAGING EMPLOYEE"]}]}


class CompanyTests(unittest.TestCase):
    def setUp(self):
        dph = {mc.identity("Acme Care, LLC"): {"name": "ACME CARE, LLC", "license_number": "MC.1", "status": "ACTIVE",
                                               "effective": "2019-01-01", "expires": "2027-06-30"}}
        self.out = mc.build(relationships(), dph, HISTORY, STAFFING, ADMINS)
        self.by = {c["id"]: c for c in self.out["companies"]}

    def test_identity_keeps_legal_suffixes_apart_but_joins_ampersands(self):
        self.assertIn("mc-acme-care-llc", self.by)
        self.assertIn("mc-acme-care-inc", self.by)
        self.assertEqual(self.by["mc-beta-and-sons-llc"]["homes_total"], 2)

    def test_dph_badge_periods_and_administrators(self):
        acme = self.by["mc-acme-care-llc"]
        self.assertEqual(acme["dph_license"]["license_number"], "MC.1")
        self.assertIsNone(self.by["mc-acme-care-inc"]["dph_license"])
        home = acme["homes"][0]
        self.assertEqual((home["start"], home["end"], home["current"]), ("2018-03-01", None, True))
        self.assertEqual([a["name"] for a in home["administrators"]], ["Pat Doe"])   # Lee Roe left in 2015
        self.assertEqual(home["context"]["quarters"], 1)
        inc = self.by["mc-acme-care-inc"]["homes"][0]
        self.assertEqual(inc["start_basis"], "listed in the first CMS release in this data")
        self.assertEqual((inc["end"], inc["ended_before"]), ("2020-01-09", "2026-10-28"))

    def test_dph_only_companies_listed_and_reviewed_alias_links_license(self):
        dph = {mc.identity("Acme Care, LLC"): {"name": "ACME CARE, LLC", "license_number": "MC.1", "status": "ACTIVE",
                                               "effective": None, "expires": None},
               mc.identity("Gamma Management Inc"): {"name": "GAMMA MANAGEMENT INC", "license_number": "MC.2",
                                                    "status": "ACTIVE", "effective": None, "expires": None},
               mc.identity("Acme Care Inc."): {"name": "ACME CARE INC.", "license_number": "MC.3", "status": "ACTIVE",
                                              "effective": None, "expires": None}}
        out = mc.build(relationships(), dph, HISTORY, STAFFING, ADMINS)
        by = {c["id"]: c for c in out["companies"]}
        self.assertEqual(by["mc-gamma-management-inc"]["homes"], [])
        self.assertEqual(by["mc-acme-care-inc"]["dph_license"]["license_number"], "MC.3")
        self.assertEqual(out["summary"]["dph_licensed_without_cms_listing"], 1)
        unreviewed = [{"cms_name": "BETA AND SONS LLC", "dph_name": "GAMMA MANAGEMENT INC", "reviewed": False, "note": "x"}]
        out = mc.build(relationships(), dph, HISTORY, STAFFING, ADMINS, unreviewed)
        self.assertIsNone({c["id"]: c for c in out["companies"]}["mc-beta-and-sons-llc"]["dph_license"])
        reviewed = [dict(unreviewed[0], reviewed=True)]
        out = mc.build(relationships(), dph, HISTORY, STAFFING, ADMINS, reviewed)
        by = {c["id"]: c for c in out["companies"]}
        self.assertEqual(by["mc-beta-and-sons-llc"]["dph_license"]["license_number"], "MC.2")
        self.assertNotIn("mc-gamma-management-inc", by)              # no duplicate DPH-only entry
        self.assertEqual(val.problems(out, {"nha-1"}), [])

    def test_validator_accepts_good_and_rejects_private_or_inconsistent(self):
        self.assertEqual(val.problems(self.out, {"nha-1"}), [])
        bad = copy.deepcopy(self.out)
        bad["companies"][0]["name"] = "ACME 12 Main Street"
        self.assertTrue(val.problems(bad))
        bad = copy.deepcopy(self.out)
        bad["companies"][0]["homes"][0]["current"] = not bad["companies"][0]["homes"][0]["current"]
        self.assertTrue(any("current flag" in p for p in val.problems(bad)))
        bad = copy.deepcopy(self.out)
        bad["caveats"] = []
        self.assertTrue(val.problems(bad))

    def test_published_file_passes_when_present(self):
        path = ROOT / "data" / "ct_nursing_home_management_companies.json"
        if path.exists():
            admins = json.loads((ROOT / "data" / "ct_nursing_home_administrators.json").read_text())
            self.assertEqual(val.problems(json.loads(path.read_text()), {p["id"] for p in admins["people"]}), [])


if __name__ == "__main__":
    unittest.main()
