import csv
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_ftag_review_batch_2 import evidence_for, existing_links, load  # noqa: E402


class Batch3ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / 'docs/nors_ftag_review_batch_3.csv').open(encoding='utf-8-sig', newline='') as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.index = load(ROOT / 'data/appendix_pp/index.json')['tags']
        cls.tags = [row for row in cls.index if '483.20' in row.get('cfr_section', '') or '483.21' in row.get('cfr_section', '')]
        cls.catalog = load(ROOT / 'crosswalk_catalog.json')['records']
        cls.existing = existing_links(cls.catalog)

    def test_section_maps_are_draft_and_pending(self):
        draft = load(ROOT / 'data/nors_section_prior_483_20_21_draft.json')
        self.assertEqual(draft['status'], 'draft')
        self.assertEqual(draft['approval_status'], 'pending_Daniel')
        self.assertFalse(draft['controls_coding'])
        self.assertEqual({section: [c['letter'] for c in data['categories']]
                          for section, data in draft['sections'].items()},
                         {'483.20': ['F'], '483.21': ['F']})

    def test_all_tags_have_at_most_five_candidate_rows(self):
        counts = Counter(row['tag'] for row in self.rows)
        self.assertEqual(set(counts), {row['tag'] for row in self.tags})
        self.assertTrue(all(count <= 5 for count in counts.values()), counts)
        self.assertTrue(all(not row['decision'] and not row['added_code'] for row in self.rows))
        pairs = [(row['tag'], row['candidate_code']) for row in self.rows if row['candidate_code']]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_candidates_are_category_f_or_existing_app_links(self):
        for row in self.rows:
            code = row['candidate_code']
            if not code:
                self.assertEqual(row['basis'], 'no_candidate_for_review')
            elif row['basis'] == 'existing_app_link':
                self.assertIn(code, self.existing[row['tag']])
            else:
                self.assertEqual(code[0], 'F')

    def test_evidence_comes_from_examples_or_key_and_severity_sections(self):
        for row in self.rows:
            if not row['candidate_code']:
                continue
            source = load(ROOT / 'data/appendix_pp' / f"{row['tag']}.json")
            eligible = evidence_for(source)
            eligible_ids = {fragment.rsplit('; ', 1)[-1].strip()
                            for passage in eligible for fragment in passage['evidence_locator'].split(' | ')}
            locators = [row[f'evidence_{n}_locator'] for n in range(1, 4) if row.get(f'evidence_{n}_locator')]
            self.assertTrue(locators)
            used_ids = {fragment.rsplit('; ', 1)[-1].strip()
                        for locator in locators for fragment in locator.split(' | ')}
            self.assertTrue(used_ids <= eligible_ids, (row['tag'], used_ids - eligible_ids))

    def test_existing_links_are_preserved(self):
        by_tag = {}
        for row in self.rows:
            if row['candidate_code']:
                by_tag.setdefault(row['tag'], set()).add(row['candidate_code'])
        for tag, codes in self.existing.items():
            if any(row['tag'] == tag for row in self.tags):
                self.assertTrue(codes <= by_tag[tag], (tag, codes - by_tag.get(tag, set())))


if __name__ == '__main__':
    unittest.main()
