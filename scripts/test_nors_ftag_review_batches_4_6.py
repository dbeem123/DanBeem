import csv
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_ftag_review_batches_4_6 import CONFIG, major_section, proposed_rule, selected_tags  # noqa: E402


class Batch456Tests(unittest.TestCase):
    def test_sections_select_expected_tag_counts(self):
        index = json.loads((ROOT / 'data/appendix_pp/index.json').read_text(encoding='utf-8'))['tags']
        expected = {4: 23, 5: 27, 6: 44}
        for batch, count in expected.items():
            with self.subTest(batch=batch):
                self.assertEqual(len(selected_tags(batch, index)), count)
        self.assertEqual(major_section('§483.24(a)(2)'), '483.24')

    def test_every_generated_row_names_a_rubric_rule(self):
        for batch in (4, 5, 6):
            proposed_file = ROOT / f'docs/nors_ftag_review_batch_{batch}_codex_proposed_triage.csv'
            review_file = ROOT / f'docs/nors_ftag_review_batch_{batch}.csv'
            with proposed_file.open(encoding='utf-8-sig', newline='') as stream:
                proposed = list(csv.DictReader(stream))
            with review_file.open(encoding='utf-8-sig', newline='') as stream:
                review = list(csv.DictReader(stream))
            self.assertEqual(len(proposed), len(review))
            self.assertTrue(proposed)
            for row in proposed:
                self.assertIn(row['rubric_rule'], {'R2_keyword_only_drop', 'R3_specific_phrase_check',
                                                   'R4_existing_link_check', 'R5_title_or_regulation_phrase_check',
                                                   'R6_no_clean_fit'})
                if row['proposed_decision'] == 'needs_claude':
                    self.assertFalse(row['candidate_code'])
                if row['proposed_decision'] == 'check':
                    self.assertIn(row['rubric_rule'], {'R3_specific_phrase_check', 'R4_existing_link_check',
                                                       'R5_title_or_regulation_phrase_check'})
            self.assertLessEqual(max(Counter(row['tag'] for row in review).values()), 5)

    def test_all_draft_maps_are_pending_and_do_not_control_coding(self):
        for batch in (4, 5, 6):
            payload = json.loads((ROOT / f'data/nors_section_prior_batch_{batch}_draft.json').read_text(encoding='utf-8'))
            self.assertEqual(payload['status'], 'draft')
            self.assertEqual(payload['approval_status'], 'pending_Daniel')
            self.assertFalse(payload['controls_coding'])
            self.assertTrue(payload['sections'])

    def test_no_unreviewed_batch_data_is_loaded_by_the_ui(self):
        source = (ROOT / 'Assets/nors-crosswalk-page.js').read_text(encoding='utf-8')
        self.assertNotIn('nors_ftag_review_batch_4', source)
        self.assertNotIn('nors_section_prior_batch_4_draft', source)
        self.assertIn("x.status === 'reviewed'", source)
        self.assertIn("x.basis === 'coded_by_reviewer'", source)


if __name__ == '__main__':
    unittest.main()
