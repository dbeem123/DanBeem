from __future__ import annotations

import hashlib
import json
import re
import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = ROOT / "source_data"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


class PlainHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


class NorsPrimaryDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = read_json(DATA / "nors_source_pack_lock.json")
        cls.lock_by_name = {r["name"]: r for r in cls.lock["revision4_source_inventory"]["files"]}
        cls.authorities = read_json(DATA / "nors_primary_authority.json")["authority_records"]
        cls.tags = read_json(DATA / "appendix_pp" / "index.json")["tags"]
        cls.term_index = read_json(DATA / "term_index.json")["terms"]
        cls.ambiguity = read_json(DATA / "nors_code_ambiguity.json")["codes"]
        cls.pdf_pages = {}
        cls.file_hashes = {}

    @classmethod
    def pdf_text_pages(cls, filename):
        if filename not in cls.pdf_pages:
            cls.pdf_pages[filename] = [p.extract_text() or "" for p in PdfReader(str(SOURCES / filename)).pages]
        return cls.pdf_pages[filename]

    def test_every_authority_hash_matches_the_additive_source_lock(self):
        for record in self.authorities:
            filename = Path(record["source_file"]).name
            self.assertIn(filename, self.lock_by_name, record["id"])
            locked = self.lock_by_name[filename]
            self.assertEqual(record["source_sha256"], locked["sha256"], record["id"])
            path = ROOT / record["source_file"]
            if path.is_file():
                if path not in self.file_hashes:
                    self.file_hashes[path] = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(self.file_hashes[path], record["source_sha256"], record["id"])

    def test_all_local_authority_texts_are_exact_normalized_source_substrings(self):
        html_plain = {}
        for record in self.authorities:
            path = ROOT / record["source_file"]
            if not path.is_file():
                continue  # CI without ignored originals still validates source hashes above.
            filename = path.name
            text = record["text"]
            if path.suffix.lower() == ".pdf":
                page_match = re.search(r"PDF page (\d+)", record["locator"])
                self.assertIsNotNone(page_match, record["id"])
                pno = int(page_match.group(1))
                pages = self.pdf_text_pages(filename)
                self.assertGreaterEqual(pno, 1, record["id"])
                self.assertLessEqual(pno, len(pages), record["id"])
                self.assertIn(normalized(text), normalized(pages[pno - 1]), record["id"])
            elif path.suffix.lower() in {".html", ".htm"}:
                if path not in html_plain:
                    parser = PlainHTML()
                    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
                    html_plain[path] = normalized(" ".join(parser.parts))
                self.assertIn(normalized(text), html_plain[path], record["id"])
            else:
                self.fail(f"Unexpected authority source type for {record['id']}: {path.suffix}")

    def test_all_60_table2_codes_and_topic_mappings_are_complete(self):
        catalog = read_json(ROOT / "crosswalk_catalog.json")["records"]
        expected = {r["nors_minor_code"]: [r["topic_slug"]] for r in catalog}
        self.assertEqual(len(expected), 60)
        actual = {r["code"] for r in self.authorities if r["authority_type"] == "nors_table_2_definition"}
        self.assertEqual(actual, set(expected))
        companion = {r["code"] for r in self.authorities if r["authority_type"] == "norc_nors_handout"}
        self.assertEqual(companion, set(expected))
        mapping = read_json(ROOT / "nors_to_topic.json")
        self.assertEqual(mapping, expected)
        self.assertFalse(any(re.fullmatch(r"F\d{3,4}", key) for key in mapping))

    def test_nors_principles_parts_one_through_four_and_app_guidance_label(self):
        guidance = [r for r in self.authorities if r["authority_type"] == "nors_training_or_faq"]
        represented = {Path(r["source_file"]).name for r in guidance}
        for roman in ("I", "II", "III", "IV"):
            self.assertIn(f"nors-training-part-{roman}-basic-principles.pdf", represented)
        app_guidance = read_json(DATA / "nors_complaint_code_guidance.json")["items"]
        self.assertEqual(len(app_guidance), 17)
        self.assertTrue(all(r.get("display_label") == "App guidance, not official NORS text" for r in app_guidance))

    def test_appendix_index_covers_all_active_tag_headers_and_files(self):
        pages = self.pdf_text_pages("som107ap_pp_guidelines_ltcf_0.pdf")
        page_map = read_json(DATA / "appendix_pp_tag_pages.json")["appendix_pp_tag_page_rows"]
        mapped_status = {row["f_tag"]: row.get("status") for row in page_map}
        header = re.compile(r"(?m)^\s*(F\d{3,4})\s*\n\s*\(Rev\.")
        all_headers = []
        for pno, text in enumerate(pages, 1):
            for match in header.finditer(text):
                all_headers.append((match.group(1), pno, match.start()))
        actual_active = set()
        for i, (tag, pno, offset) in enumerate(all_headers):
            if mapped_status.get(tag) in {"reserved", "deleted"}:
                continue
            next_page, next_offset = all_headers[i + 1][1:] if i + 1 < len(all_headers) else (len(pages), len(pages[-1]))
            excerpt = []
            for page_no in range(pno, next_page + 1):
                raw = pages[page_no - 1]
                lo = offset if page_no == pno else 0
                hi = next_offset if page_no == next_page else len(raw)
                excerpt.append(raw[lo:hi])
            if re.search(r"(?:This tag number is in reserve for future use|tag number is reserved|this tag is deleted)", " ".join(excerpt), re.I):
                continue
            actual_active.add(tag)
        # The existing crosswalk page map also holds active shared sections with no standalone F-tag header.
        actual_active.update(tag for tag, state in mapped_status.items() if state == "confirmed" and tag not in {x[0] for x in all_headers})
        indexed = {r["tag"] for r in self.tags}
        self.assertEqual(indexed, actual_active)
        self.assertEqual(len(indexed), len(self.tags))
        for tag in indexed:
            record = read_json(DATA / "appendix_pp" / f"{tag}.json")
            self.assertEqual(record["tag"], tag)
            self.assertEqual(record["source_sha256"], self.lock_by_name["som107ap_pp_guidelines_ltcf_0.pdf"]["sha256"])
            self.assertGreaterEqual(record["pdf_page_start"], 1)
            self.assertLessEqual(record["pdf_page_start"], record["pdf_page_end"])
            for passage in record["passages"]:
                pno = passage["pdf_page"]
                self.assertGreaterEqual(pno, record["pdf_page_start"])
                self.assertLessEqual(pno, record["pdf_page_end"])
                self.assertIn(normalized(passage["text"]), normalized(pages[pno - 1]), f"{tag} page {pno}")

    def test_f554_regulation_guidance_and_investigation_are_distinct_and_exact(self):
        f554 = read_json(DATA / "appendix_pp" / "F554.json")
        self.assertEqual(f554["pdf_page_start"], 17)
        self.assertIn("483.10(c)(7)", f554["cfr_section"])
        sections = {p["section_label"] for p in f554["passages"]}
        self.assertIn("Regulation", sections)
        self.assertIn("Guidance", sections)
        self.assertIn("Probes / investigative protocol", sections)
        self.assertFalse(any(r.get("controls_coding", True) for r in self.authorities if r["authority_type"].startswith("cms_")))

    def test_ambiguity_is_limited_to_nors_table2_text_and_has_no_empty_records(self):
        expected = {c for c in {r["nors_minor_code"] for r in read_json(ROOT / "crosswalk_catalog.json")["records"]} if c.startswith("D") or c in {"F03", "F04", "J01", "F02", "F05", "F07", "F08", "F12", "A05", "C03", "J03"}}
        self.assertEqual({r["code"] for r in self.ambiguity}, expected)
        table = {r["code"]: r for r in self.authorities if r["authority_type"] == "nors_table_2_definition"}
        self.assertTrue(all(r["ambiguity"] for r in self.ambiguity))
        for row in self.ambiguity:
            for item in row["neighbors"] + row["ambiguity"]:
                self.assertIn(item["locator"], {r["locator"] for r in table.values()})
                owner = next((r for r in table.values() if r["locator"] == item["locator"]), None)
                self.assertIsNotNone(owner)
                self.assertIn(normalized(item["source_quote"]), normalized(owner["text"]))
        for row in self.ambiguity:
            for item in row["ambiguity"]:
                self.assertIn("does not choose", item["review_prompt"])

    def test_term_index_locations_resolve_and_classes_remain_separate(self):
        authority_ids = {r["id"] for r in self.authorities}
        tag_ids = {r["id"] for r in self.tags}
        for term, entries in self.term_index.items():
            self.assertTrue(entries, term)
            for entry in entries:
                self.assertIn(entry["source_class"], {"nors", "appendix_pp"})
                self.assertIn(entry["record_id"], authority_ids if entry["source_class"] == "nors" else tag_ids)
                self.assertTrue(entry["locators"])
        for term in ("self-administer", "wrong", "medication", "medications"):
            self.assertIn(term, self.term_index, term)
        for term in ("self-administer", "wrong", "medication"):
            classes = {entry["source_class"] for entry in self.term_index[term]}
            self.assertTrue(classes <= {"nors", "appendix_pp"})

    def test_wrong_medication_given_has_source_support_on_both_result_sides(self):
        def ids(term, source_class):
            return {entry["record_id"] for entry in self.term_index[term] if entry["source_class"] == source_class}
        self.assertIn("nors-table2-f04", ids("medication", "nors"))
        self.assertIn("nors-table2-f04", ids("given", "nors"))
        self.assertIn("appendix-pp-f755", ids("medication", "appendix_pp"))
        self.assertIn("appendix-pp-f755", ids("given", "appendix_pp"))
        self.assertIn("appendix-pp-f760", ids("wrong", "appendix_pp"))
        self.assertIn("appendix-pp-f760", ids("medication", "appendix_pp"))


if __name__ == "__main__":
    unittest.main()
