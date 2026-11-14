import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from import_nors_ftag_review_batch_3 import build_records  # noqa: E402


class Batch3ImportPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / 'docs/nors_ftag_review_batch_3_claude_triage.csv').open(encoding='utf-8-sig', newline='') as stream:
            cls.rows = list(csv.DictReader(stream))
        index = json.loads((ROOT / 'data/appendix_pp/index.json').read_text(encoding='utf-8'))['tags']
        cls.tags = {row['tag']: json.loads((ROOT / f"data/appendix_pp/{row['tag']}.json").read_text(encoding='utf-8'))
                    for row in index}
        authority = json.loads((ROOT / 'data/nors_primary_authority.json').read_text(encoding='utf-8'))['authority_records']
        cls.definitions = {row['code']: row for row in authority if row['authority_type'] == 'nors_table_2_definition'}

    def test_build_is_pure_and_does_not_mutate_the_source_file(self):
        source = ROOT / 'data/nors_reviewed_links.json'
        before = source.read_bytes()
        records = build_records(self.rows, self.tags, self.definitions)
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(len(records), 67)

    def test_batch3_rows_and_manual_f646_check_are_preserved(self):
        records = build_records(self.rows, self.tags, self.definitions)
        pairs = {(row['f_tag'], row['nors_code']): row for row in records}
        self.assertIn(('F646', 'F03'), pairs)
        manual = pairs[('F646', 'F03')]
        self.assertEqual(manual['status'], 'reviewed')
        self.assertEqual(manual['link_strength'], 'weak')
        self.assertEqual(manual['evidence_basis'], 'title_only')
        self.assertIn('check', manual['reviewer_note'])
        self.assertEqual(manual['review_method'], 'Daniel-directed triage approved 2026-11-13')
        self.assertEqual(manual['appendix_passage_id'], 'appendix-pp-f646-p2')
        for tag, code in [('F636', 'F03'), ('F637', 'F07'), ('F656', 'F01'), ('F658', 'F12')]:
            self.assertIn('check', pairs[(tag, code)]['reviewer_note'].lower())
        self.assertFalse(any(pair == ('F660', 'C03') for pair in pairs))
        self.assertEqual(sum(row['status'] == 'reviewed' for row in records), 11)
        self.assertEqual(sum(row['status'] == 'rejected' for row in records), 56)


if __name__ == '__main__':
    unittest.main()
