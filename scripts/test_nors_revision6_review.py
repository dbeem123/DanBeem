from __future__ import annotations

import csv
import hashlib
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


class Revision6ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / 'docs/nors_ftag_review_batch_1.csv').open(encoding='utf-8-sig', newline='') as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.index = read_json(DATA / 'appendix_pp/index.json')['tags']
        anchors = {r['tag']: r['pdf_page_start'] for r in cls.index}
        # F917, for example, cites 483.10 in a cross-reference, but belongs
        # to the later physical-environment section. Use document boundaries.
        cls.selected = {r['tag']: read_json(DATA / 'appendix_pp' / (r['tag'] + '.json'))
                        for r in cls.index if anchors['F550'] <= r['pdf_page_start'] < anchors['F620']}
        cls.authority = read_json(DATA / 'nors_primary_authority.json')['authority_records']
        cls.table = {r['code']: r['text'] for r in cls.authority if r['authority_type'] == 'nors_table_2_definition'}
        cls.lock = {r['source_file']: r for r in read_json(DATA / 'nors_source_pack_lock.json')['revision4_source_inventory']['files']}
        cls.pdf_pages = {}

    def test_scope_and_exact_passage_coverage(self):
        self.assertTrue(self.rows)
        self.assertEqual({r['tag'] for r in self.rows}, set(self.selected))
        by_tag = defaultdict(list)
        for row in self.rows:
            by_tag[row['tag']].append(row)
            tag = self.selected[row['tag']]
            self.assertEqual(row['cms_title'], tag['cms_short_title'])
            self.assertTrue(any(row['verbatim_situation'] == p['text'] and str(p['pdf_page']) in row['locator']
                                for p in tag['passages']), (row['tag'], row['locator']))
            for field in ('decision', 'added_code', 'reviewer_note'):
                self.assertEqual(row[field], '')
        for tag, record in self.selected.items():
            expected = [p for p in record['passages'] if p['is_example'] or p['section_label'] in
                        {'Deficiency categorization', 'Key elements of noncompliance'}]
            if not expected:
                expected = [p for p in record['passages'] if p['section_label'] == 'Regulation'][:1]
            self.assertTrue(expected, tag)
            for passage in expected:
                self.assertTrue(any(row['verbatim_situation'] == passage['text'] and
                                    str(passage['pdf_page']) in row['locator'] for row in by_tag[tag]),
                                (tag, passage['id']))

    def test_definitions_candidates_and_existing_links(self):
        by_situation = defaultdict(set)
        observed_links = set()
        for row in self.rows:
            code = row['candidate_code']
            if not code:
                continue
            self.assertIn(code, self.table)
            self.assertEqual(row['table_2_definition'], self.table[code])
            if row['basis'] == 'existing_app_link':
                observed_links.add((row['tag'], code))
            else:
                by_situation[(row['tag'], row['locator'], row['verbatim_situation'])].add(code)
            if row['matched_norc_scenario']:
                self.assertEqual(row['scenario_answer_code'], code)
                self.assertTrue(row['scenario_locator'])
                source, locator = row['scenario_locator'].split('; ', 1)
                self.assertTrue('quiz-answers' in source.lower() or 'faqs.pdf' in source.lower())
                self.assertIn(source, self.lock)
                path = ROOT / source
                if source not in self.pdf_pages:
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.lock[source]['sha256'])
                    self.pdf_pages[source] = [p.extract_text() or '' for p in PdfReader(str(path)).pages]
                page_no = int(re.search(r'PDF page (\d+)', locator).group(1))
                page = re.sub(r'\s+', ' ', self.pdf_pages[source][page_no - 1]).strip()
                scenario = re.sub(r'\s+', ' ', row['matched_norc_scenario']).strip()
                self.assertIn(scenario, page, row['scenario_locator'])
                # An answer is printed beside the scenario or explicitly within it.
                offset = page.index(scenario)
                near = page[max(0, offset - 50):offset + len(scenario)]
                code_pattern = re.escape(code).replace('0', '[0O]')
                self.assertRegex(near, r'\b' + code_pattern + r'\b', row['scenario_locator'])
        for key, candidates in by_situation.items():
            self.assertLessEqual(len(candidates), 3, key)
        catalog = read_json(ROOT / 'crosswalk_catalog.json')['records']
        expected = set()
        for record in catalog:
            links = record.get('appendix_pp_tags', [])
            if isinstance(links, dict):
                links = [links]
            for link in links:
                tag = str(link.get('citation', '') if isinstance(link, dict) else link).upper().strip()
                if tag in self.selected:
                    expected.add((tag, record['nors_minor_code']))
        self.assertTrue(expected <= observed_links, sorted(expected - observed_links))


if __name__ == '__main__':
    unittest.main()
