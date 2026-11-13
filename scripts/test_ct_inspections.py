#!/usr/bin/env python3
"""Checks for the Inspections data and the Connecticut facility roster."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INS = json.loads((ROOT / "data/ct_inspections.json").read_text(encoding="utf-8"))
ROSTER = json.loads((ROOT / "data/nursing_home_facility_roster_ct.json").read_text(encoding="utf-8"))
HEALTH = json.loads((ROOT / "data/nursing_home_health_deficiencies_ct.json").read_text(encoding="utf-8"))
FIRE = json.loads((ROOT / "data/nursing_home_fire_safety_deficiencies_ct.json").read_text(encoding="utf-8"))
MAP = json.loads((ROOT / "data/reference/resident_rights_tag_map.json").read_text(encoding="utf-8"))


class InspectionsData(unittest.TestCase):
    def test_every_citation_is_kept(self):
        kinds = [r[7] for r in INS["rows"]]
        self.assertEqual(kinds.count(0), len(HEALTH["deficiencies"]))
        self.assertEqual(kinds.count(1) + kinds.count(2), len(FIRE["deficiencies"]))
        self.assertEqual(INS["meta"]["citation_rows"], len(INS["rows"]))

    def test_row_values(self):
        n = len(INS["homes"])
        for r in INS["rows"]:
            self.assertTrue(0 <= r[0] < n)
            self.assertRegex(r[1], r"^\d{4}-\d{2}-\d{2}$")
            self.assertIn(r[2], INS["tags"])
            self.assertIn(r[3], list("ABCDEFGHIJKL") + [""])
            self.assertTrue(0 <= r[4] <= 7 and 0 <= r[6] <= 3 and r[7] in (0, 1, 2))
            if r[5]:
                self.assertRegex(r[5], r"^\d{4}-\d{2}-\d{2}$")

    def test_kind_matches_prefix(self):
        for r in INS["rows"]:
            self.assertEqual(r[2][0], {0: "F", 1: "K", 2: "E"}[r[7]], r)

    def test_scope_severity_counts_match_source(self):
        from collections import Counter
        src = Counter((d.get("scope_severity_code") or "").strip().upper() for d in HEALTH["deficiencies"])
        out = Counter(r[3] for r in INS["rows"] if r[7] == 0)
        self.assertEqual(src, out)

    def test_ccns_are_six_character_strings(self):
        for h in INS["homes"]:
            self.assertRegex(h[0], r"^\d{6}$")
        for r in ROSTER["records"]:
            self.assertRegex(r["ccn"], r"^\d{6}$")

    def test_groups_use_tag_spelling_of_the_data(self):
        for g in INS["groups"]:
            for t in g["tags"]:
                self.assertRegex(t, r"^F\d{4}$")
        self.assertEqual(len(INS["groups"]), len(MAP["groups"]))
        tagged = {t for t, v in INS["tags"].items() if v[2]}
        self.assertIn("F0600", tagged)
        self.assertIn("F0623", tagged)

    def test_appendix_pp_links_point_to_pages(self):
        pages = [v[3] for v in INS["tags"].values() if v[3]]
        self.assertGreater(len(pages), 50)
        self.assertTrue(all(isinstance(p, int) and p > 0 for p in pages))

    def test_f554_is_mapped_to_medication_self_administration(self):
        group = next(g for g in MAP["groups"] if g["id"] == "medication_self_administration")
        self.assertIn("F554", group["tags"])
        self.assertNotIn("F554", next(g for g in MAP["groups"] if g["id"] == "care")["tags"])
        self.assertEqual(INS["tags"]["F0554"][2], "medication_self_administration")
        self.assertEqual(INS["tags"]["F0554"][3], 17)
        self.assertEqual(INS["tagref"]["F0554"][1], "42 CFR 483.10(c)(7)")

    def test_f556_reserved_page_anchor_matches_appendix_pp(self):
        row = next(r for r in json.loads((ROOT / "data/appendix_pp_tag_pages.json").read_text(encoding="utf-8"))["appendix_pp_tag_page_rows"] if r["f_tag"] == "F556")
        self.assertEqual(row["status"], "reserved")
        self.assertEqual(row["appendix_pp_pdf_page_start"], 20)

    def test_scores_from_provider_info(self):
        scores = INS["scores"]
        self.assertEqual(len(scores), INS["meta"]["denominators"]["provider_info_homes"])
        arden = scores[str([h[0] for h in INS["homes"]].index("075228"))]
        self.assertIsInstance(arden["weighted_score"], (int, float))
        self.assertIn(arden["health_rating"], (1, 2, 3, 4, 5))

    def test_survey_dates_and_risk_based_footnote(self):
        types = INS["meta"]["survey_types"]
        for v in INS["surveys"].values():
            for s in v:
                self.assertRegex(s[0], r"^\d{4}-\d{2}-\d{2}$")
                self.assertTrue(0 <= s[1] < len(types))
        # Footnote counts in the meta are only those seen in Connecticut rows.
        ct_29 = sum(1 for v in INS["surveys"].values() for s in v if s[3] == "29")
        self.assertEqual(ct_29, INS["meta"]["inspection_dates_footnotes"].get("29", 0))


class Roster(unittest.TestCase):
    def test_nothing_dropped(self):
        s = ROSTER["metadata"]["summary"]
        ccns = {r["ccn"] for r in ROSTER["records"]}
        self.assertEqual(len(ccns), len(ROSTER["records"]))
        self.assertEqual(len(ccns), s["all_ccns_seen"])
        self.assertTrue({h[0] for h in INS["homes"]} <= ccns)
        self.assertEqual(sum(r["in_provider_info"] for r in ROSTER["records"]), s["provider_info_homes"])
        self.assertEqual(sum(r["in_pbj_latest_quarter"] for r in ROSTER["records"]), s["pbj_homes_latest_quarter"])

    def test_every_gap_is_explained(self):
        for r in ROSTER["records"]:
            if not r["in_provider_info"] or not r["in_pbj_latest_quarter"]:
                self.assertTrue(r["notes"], r["ccn"])


class Wording(unittest.TestCase):
    def test_no_rankings_on_the_page(self):
        js = (ROOT / "Assets/nursing-home-inspections.js").read_text(encoding="utf-8")
        html = (ROOT / "staffing/tools/nursing-home-inspections.html").read_text(encoding="utf-8")
        for text in (js, html):
            self.assertIsNone(re.search(r"\b(worst|best|ranked|ranking of|rank \d)\b", text, re.I))


if __name__ == "__main__":
    unittest.main()
