from __future__ import annotations

import csv
import json
import re
import unittest
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def normalized(text):
    return re.sub(r'\s+', ' ', text).strip()


class Revision7ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / 'docs/nors_ftag_review_batch_1.csv').open(encoding='utf-8-sig', newline='') as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.prior = read_json(DATA / 'nors_section_prior.json')
        cls.index = read_json(DATA / 'appendix_pp/index.json')['tags']
        anchors = {r['tag']: r['pdf_page_start'] for r in cls.index}
        cls.selected = {r['tag']: read_json(DATA / 'appendix_pp' / (r['tag'] + '.json'))
                        for r in cls.index if anchors['F550'] <= r['pdf_page_start'] < anchors['F620']}
        authority = read_json(DATA / 'nors_primary_authority.json')['authority_records']
        cls.table = {r['code']: r['text'] for r in authority if r['authority_type'] == 'nors_table_2_definition'}

    def test_added_stop_words_are_not_scored(self):
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            from build_ftag_review_batch_1 import terms
            self.assertEqual(terms('her his who there did having etc lack'), set())
            self.assertEqual(terms('her medication'), {'medication'})
        finally:
            sys.path.pop(0)

    def test_plural_and_suffix_matching_and_f567_e02(self):
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            from build_ftag_review_batch_1 import terms
            self.assertIn('fund', terms('funds') & terms('fund'))
            self.assertIn('deposit', terms('deposits') & terms('deposit'))
            self.assertIn('transfer', terms('transfers') & terms('transferred'))
            self.assertFalse(terms('requests follows residents') & terms('request follow resident'))
        finally:
            sys.path.pop(0)
        self.assertIn('E02', {r['candidate_code'] for r in self.rows if r['tag'] == 'F567'})

    def test_cross_page_evidence_retains_both_locators(self):
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            from build_ftag_review_batch_1 import linked_evidence
            first = {'id': 'p1', 'text': 'Examples include:', 'pdf_page': 12,
                     'section_label': 'Guidance', 'continuation_passage_id': 'p2'}
            second = {'id': 'p2', 'text': 'A resident was left waiting.', 'pdf_page': 13,
                      'section_label': 'Guidance', 'continued_from_passage_id': 'p1'}
            result = linked_evidence(first, {'p1': first, 'p2': second}, 'source.pdf')
            self.assertEqual(result['text'], 'Examples include: A resident was left waiting.')
            self.assertIn('PDF page 12; Guidance; p1', result['evidence_locator'])
            self.assertIn('PDF page 13; Guidance; p2', result['evidence_locator'])
        finally:
            sys.path.pop(0)

    def test_approved_prior_contains_only_verbatim_table2_category_headings(self):
        self.assertEqual(self.prior['status'], 'approved')
        self.assertEqual(self.prior['approved_by'], 'Daniel')
        self.assertEqual(self.prior['approved_date'], '2026-11-13')
        self.assertFalse(self.prior['controls_coding'])
        self.assertEqual(set(self.prior['sections']), {'483.10', '483.12'})
        self.assertIn('E', {item['letter'] for item in self.prior['sections']['483.12']['categories']})
        path = ROOT / 'source_data/NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf'
        if not path.exists():
            self.skipTest('ignored Table 2 source unavailable for heading verification')
        # The source extractor splits the word "Gross" at a line break.
        pages = [normalized(re.sub(r'Gro\s*\n\s*ss', 'Gross', p.extract_text() or ''))
                 for p in PdfReader(str(path)).pages]
        for section in self.prior['sections'].values():
            self.assertTrue(section['categories'])
            for item in section['categories']:
                self.assertRegex(item['letter'], r'^[A-L]$')
                self.assertTrue(item['locator'])
                self.assertTrue(any(normalized(item['heading']) in p for p in pages), item)
                if item['letter'] == 'A':
                    self.assertEqual(item['heading'], 'Abuse, Gross Neglect, Exploitation (Code A)')

    def test_one_decision_per_candidate_and_all_existing_links(self):
        self.assertEqual({r['tag'] for r in self.rows}, set(self.selected))
        by_tag = defaultdict(set)
        observed = set()
        for row in self.rows:
            tag, code = row['tag'], row['candidate_code']
            self.assertNotIn(code, by_tag[tag], (tag, code))
            by_tag[tag].add(code)
            if code:
                self.assertIn(code, self.table)
                self.assertEqual(row['table_2_definition'], self.table[code])
                observed.add((tag, code))
                if row['basis'] != 'existing_app_link':
                    page = self.selected[tag]['pdf_page_start']
                    boundary = next(item['pdf_page_start'] for item in self.index if item['tag'] == 'F600')
                    section = '483.10' if page < boundary else '483.12'
                    allowed = {item['letter'] for item in self.prior['sections'][section]['categories']}
                    self.assertIn(code[0], allowed, (tag, code, section))
            for field in ('decision', 'added_code', 'reviewer_note'):
                self.assertEqual(row[field], '')
        self.assertTrue(all(len(codes) <= 5 for codes in by_tag.values()))
        expected = set()
        for record in read_json(ROOT / 'crosswalk_catalog.json')['records']:
            links = record.get('appendix_pp_tags', [])
            if isinstance(links, dict):
                links = [links]
            for link in links:
                tag = str(link.get('citation', '') if isinstance(link, dict) else link).upper().strip()
                if tag in self.selected:
                    expected.add((tag, record['nors_minor_code']))
        self.assertTrue(expected <= observed, sorted(expected - observed))

    def test_evidence_is_verbatim_labeled_and_not_severity_boilerplate(self):
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            from build_ftag_review_batch_1 import linked_evidence
        finally:
            sys.path.pop(0)
        forbidden = set('will some can level limited medical during needs harm immediate report others based making failure risk appropriate may must also other including ensure her his who there did having etc lack'.split())
        for row in self.rows:
            record = self.selected[row['tag']]
            by_id = {p['id']: p for p in record['passages']}
            self.assertEqual(row['cms_title'], record['cms_short_title'])
            self.assertTrue(any(row['regulation_sentence'] == p['text'] for p in record['passages']
                                if p['section_label'] == 'Regulation'), row['tag'])
            count = 0
            for i in range(1, 4):
                text, locator = row[f'evidence_{i}_text'], row[f'evidence_{i}_locator']
                self.assertEqual(bool(text), bool(locator))
                if not text:
                    continue
                count += 1
                self.assertNotRegex(text, r'(?i)^severity level\s*1\s+does not apply')
                self.assertTrue(any(text == linked_evidence(p, by_id, record['source_file'])['text'] and
                                    linked_evidence(p, by_id, record['source_file'])['evidence_locator'] == locator and
                                    (linked_evidence(p, by_id, record['source_file'])['is_example'] or p['section_label'] in {'Deficiency categorization', 'Key elements of noncompliance', 'Regulation'})
                                    for p in record['passages']), (row['tag'], locator))
            self.assertTrue(1 <= count <= 3, (row['tag'], row['candidate_code'], count))
            shared = set(re.findall(r"[a-z][a-z0-9'-]*", row['shared_terms'].lower()))
            self.assertFalse(shared & forbidden, (row['tag'], shared & forbidden))


if __name__ == '__main__':
    unittest.main()
