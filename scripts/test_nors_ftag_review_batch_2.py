import csv
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_ftag_review_batch_2 import evidence_for, existing_links, load  # noqa: E402


class Batch2ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / 'docs/nors_ftag_review_batch_2.csv').open(encoding='utf-8-sig', newline='') as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.index = load(ROOT / 'data/appendix_pp/index.json')['tags']
        cls.tags = [row for row in cls.index if '483.15' in row.get('cfr_section', '')]
        cls.catalog = load(ROOT / 'crosswalk_catalog.json')['records']
        cls.existing = existing_links(cls.catalog)

    def test_draft_map_is_conservative_and_not_approved(self):
        draft = load(ROOT / 'data/nors_section_prior_483_15_draft.json')
        self.assertEqual(draft['status'], 'draft')
        self.assertEqual(draft['approval_status'], 'pending_Daniel')
        self.assertFalse(draft['controls_coding'])
        self.assertEqual([row['letter'] for row in draft['sections']['483.15']['categories']], ['C'])

    def test_every_section_tag_is_present_at_most_five_times(self):
        counts = Counter(row['tag'] for row in self.rows)
        self.assertEqual(set(counts), {row['tag'] for row in self.tags})
        self.assertTrue(all(count <= 5 for count in counts.values()), counts)
        self.assertTrue(all(not row['decision'] and not row['added_code'] for row in self.rows),
                        'batch 2 remains unreviewed')
        pairs = [(row['tag'], row['candidate_code']) for row in self.rows if row['candidate_code']]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_candidates_are_category_c_or_existing_app_links(self):
        allowed = {'C'}
        for row in self.rows:
            code = row['candidate_code']
            if not code:
                self.assertEqual(row['basis'], 'no_candidate_for_review')
                continue
            if row['basis'] == 'existing_app_link':
                self.assertIn(code, self.existing[row['tag']])
            else:
                self.assertIn(code[0], allowed)

    def test_evidence_uses_examples_key_elements_or_severity_categories(self):
        tags_by_id = {row['tag']: load(ROOT / 'data/appendix_pp' / f"{row['tag']}.json") for row in self.tags}
        for row in self.rows:
            if not row['candidate_code']:
                continue
            evidence = evidence_for(tags_by_id[row['tag']])
            allowed_ids = {fragment.rsplit('; ', 1)[-1].strip()
                           for passage in evidence
                           for fragment in passage['evidence_locator'].split(' | ')}
            locators = [row[f'evidence_{n}_locator'] for n in range(1, 4) if row.get(f'evidence_{n}_locator')]
            self.assertTrue(locators, row)
            locator_ids = {fragment.rsplit('; ', 1)[-1].strip()
                           for locator in locators for fragment in locator.split(' | ')}
            fallback_locators = {locator for locator in locators
                                 if locator.startswith('source_data/cms_survey/NH_CitationDescriptions_May2026.csv;') or
                                 '; Regulation;' in locator}
            if row['basis'] == 'title_regulation_fallback':
                self.assertTrue(fallback_locators, (row['tag'], locators))
                regular_locators = set(locators) - fallback_locators
                regular_ids = {fragment.rsplit('; ', 1)[-1].strip()
                               for locator in regular_locators for fragment in locator.split(' | ')}
                self.assertTrue(regular_ids <= allowed_ids, (row['tag'], regular_ids - allowed_ids))
            else:
                self.assertTrue(locator_ids <= allowed_ids, (row['tag'], locator_ids - allowed_ids))

    def test_all_existing_links_are_included(self):
        by_tag = {}
        for row in self.rows:
            if row['candidate_code']:
                by_tag.setdefault(row['tag'], set()).add(row['candidate_code'])
        for tag, codes in self.existing.items():
            if any(row['tag'] == tag for row in self.tags):
                self.assertTrue(codes <= by_tag[tag], (tag, codes - by_tag.get(tag, set())))

    def test_daniel_approved_links_and_undecided_f660_candidate(self):
        links = load(ROOT / 'data/nors_reviewed_links.json')['links']
        reviewed = {(row['f_tag'], row['nors_code']): row for row in links if row.get('status') == 'reviewed'}
        for tag in ['F622', 'F623', 'F624', 'F625', 'F626']:
            row = reviewed[(tag, 'C03')]
            self.assertEqual(row['basis'], 'coded_by_reviewer')
            self.assertEqual(row['reviewed_by'], 'Daniel')
            self.assertEqual(row['reviewed_date'], '2026-11-13')
            self.assertEqual(row['review_method'], 'approved Claude first-pass triage')
        row = reviewed[('F660', 'D02')]
        self.assertEqual(row['reviewed_by'], 'Daniel')
        self.assertEqual(row['reviewed_date'], '2026-11-13')
        self.assertEqual(row['review_method'], 'approved Claude first-pass triage')
        self.assertNotIn(('F660', 'C03'), reviewed)

    def test_batch_one_triage_records_daniels_approval_without_decision_changes(self):
        with (ROOT / 'docs/nors_ftag_review_batch_1_claude_triage.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 229)
        self.assertTrue(all('approved by Daniel 2026-11-13 without row changes' in row['triage'] for row in rows))
        self.assertEqual(Counter(row['decision'] for row in rows), {'drop': 140, 'keep': 79, 'add': 10})


if __name__ == '__main__':
    unittest.main()
