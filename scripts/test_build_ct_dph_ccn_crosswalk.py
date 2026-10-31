import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_ct_dph_ccn_crosswalk as xw

CMS = [
    {"ccn": "075001", "name": "ST JOSEPH'S CENTER", "address": "6448 MAIN STREET", "city": "TRUMBULL", "zip": "06611"},
    {"ccn": "075442", "name": "60 WEST", "address": "60 WEST STREET", "city": "ROCKY HILL", "zip": "06067"},
    {"ccn": "075348", "name": "ADVANCED CENTER FOR NURSING & REHABILITATION", "address": "169 DAVENPORT AVENUE",
     "city": "NEW HAVEN", "zip": "06519"},
    {"ccn": "075999", "name": "WEST HARTFORD HEALTH & REHABILITATION CENTER", "address": "130 LOOMIS DRIVE",
     "city": "WEST HARTFORD", "zip": "06107"},
]


def dph(lic, name, address, city, zip_code):
    return {"license_raw": lic, "state_facility_license_id": xw.normalize_license(lic), "name": name,
            "address": address, "city": city, "zip": xw.normalize_zip(zip_code), "status": "ACTIVE",
            "effective_date": "", "expiration_date": ""}


class NormalizeTests(unittest.TestCase):
    def test_zip_letter_o(self):
        self.assertEqual(xw.normalize_zip("O6897"), "06897")
        self.assertEqual(xw.normalize_zip("6107"), "06107")

    def test_address(self):
        self.assertEqual(xw.normalize_address("169 Davenport Ave., Suite 2"), ("169", "DAVENPORT AVE"))
        self.assertEqual(xw.normalize_address("60 West Street"), ("60", "W ST"))

    def test_license(self):
        self.assertEqual(xw.normalize_license("000123"), "123")


class BuildTests(unittest.TestCase):
    def test_tiers_and_one_ccn_per_license(self):
        rows = [
            dph("000101", "WEST HARTFORD HEALTH AND REHABILITATION CENTER", "130 Loomis Dr", "West Hartford", "06107"),
            dph("000102", "ADVANCED CENTER FOR NURSING AND REHAB", "169 Davenport Ave", "New Haven", "06519"),
            dph("000103", "ADVANCED NURSING ANNEX", "169 Davenport Ave", "New Haven", "06519"),
            dph("000104", "NOWHERE MANOR", "1 Unknown Rd", "Salisbury", "06068"),
        ]
        result = xw.build(rows, CMS)
        by_lic = {r["state_facility_license_id"]: r for r in result["rows"]}
        self.assertEqual(by_lic["101"]["ccn"], "075999")
        self.assertEqual(by_lic["101"]["match_tier"], "auto_high")
        self.assertEqual(by_lic["102"]["ccn"], "075348")
        self.assertEqual(by_lic["103"]["match_tier"], "review")  # same CCN already claimed
        self.assertIsNone(by_lic["104"]["ccn"])
        self.assertEqual(by_lic["104"]["match_tier"], "unmatched")
        self.assertEqual(result["publication_status"], "staging_review_required")
        ccns = [r["ccn"] for r in result["rows"] if r["match_tier"] in ("auto_high", "likely")]
        self.assertEqual(len(ccns), len(set(ccns)))

    def test_cli_roundtrip_has_no_person_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "dph.csv"
            with src.open("w", newline="", encoding="utf-8") as handle:
                w = csv.writer(handle)
                w.writerow(["FACILITY NAME", "ADDRESS", "CITY", "STATE", "ZIP", "LICENSE NO.", "STATUS",
                            "EFFECTIVE DATE", "EXPIRATION DATE", ""])
                w.writerow(["60 WEST", "60 WEST ST", "ROCKY HILL", "CT", "O6067", "000555", "ACTIVE", "1/1/2020", "6/30/2027", ""])
            loaded = xw.load_dph(src)
            self.assertEqual(loaded[0]["zip"], "06067")
            result = xw.build(loaded, CMS)
            text = json.dumps(result)
            for banned in ("FIRST NAME", "LAST NAME", "first_name", "last_name"):
                self.assertNotIn(banned, text)
            self.assertEqual(result["rows"][0]["ccn"], "075442")
            md = xw.review_markdown(result)
            self.assertIn("CMS facilities with no license match", md)


if __name__ == "__main__":
    unittest.main()
