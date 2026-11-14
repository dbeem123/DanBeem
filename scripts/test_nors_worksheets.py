import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_nors_distinction_review import build_rows as build_distinction_rows  # noqa: E402
from build_nors_example_worksheet import build_rows as build_example_rows, extract_use_phrases  # noqa: E402
from validate_nors_example_worksheet import validate_entry, validate_rows  # noqa: E402


class NorsWorksheetTests(unittest.TestCase):
    def test_example_worksheet_has_one_blank_row_per_table2_code(self):
        rows = build_example_rows()
        self.assertEqual(len(rows), 60)
        self.assertEqual(len({row['code'] for row in rows}), 60)
        self.assertTrue(all(not row['example_complaints'] and not row['near_miss_complaints']
                            and not row['daniel_review'] for row in rows))
        self.assertFalse(validate_rows(rows, allow_empty=True))
        self.assertTrue(validate_rows(rows, allow_empty=False))

    def test_use_phrases_are_exact_source_substrings(self):
        text = 'X02 Sample definition. Use D03 (Dignity) for one case. Use if the facility does this.'
        phrases = extract_use_phrases(text)
        self.assertEqual(phrases, ['Use D03 (Dignity) for one case.', 'Use if the facility does this.'])
        self.assertTrue(all(phrase in text for phrase in phrases))

    def test_validator_requires_5_to_6_examples_and_1_to_2_near_misses(self):
        row = {'code': 'A01', 'table_2_definition': 'A01 Sample physical force that results in acute or chronic illness.',
               'example_complaints': '\n'.join(['TEST: "physical force that results in acute or chronic illness"'] * 5),
               'example_voice_labels': '\n'.join(['Resident'] * 5),
               'example_markings': '\n'.join(['illustrative, project-written'] * 5),
               'near_miss_complaints': 'TEST: "physical force that results in acute or chronic illness"',
               'near_miss_voice_labels': 'Staff', 'near_miss_markings': 'illustrative, project-written'}
        self.assertFalse(validate_entry(row))
        row['example_voice_labels'] = '\n'.join(['Resident'] * 4)
        self.assertTrue(any('voice label' in error for error in validate_entry(row)))
        row['example_voice_labels'] = '\n'.join(['Resident'] * 5)
        row['example_markings'] = '\n'.join(['project-written'] * 5)
        self.assertTrue(any('marked illustrative' in error for error in validate_entry(row)))
        row['example_markings'] = '\n'.join(['illustrative, project-written'] * 5)
        row['example_complaints'] = '\n'.join(['TEST: generic wording'] * 5)
        self.assertTrue(any('quoted Table 2 phrase' in error for error in validate_entry(row)))

    def test_distinction_review_sheet_is_separate_and_decisions_are_blank(self):
        rules = json.loads((ROOT / 'data/nors_distinctions.json').read_text(encoding='utf-8'))['rules']
        rows = build_distinction_rows(rules)
        self.assertEqual(len(rows), 139)
        self.assertTrue(all(row['proposed_question'].startswith('Proposed: ') and not row['daniel_decision']
                            for row in rows))
        self.assertTrue(all(rule['question'] is None for rule in rules))
        with (ROOT / 'docs/nors_distinctions_review.csv').open(encoding='utf-8-sig', newline='') as stream:
            sheet = list(csv.DictReader(stream))
        self.assertEqual(len(sheet), 139)
        self.assertTrue(all(not row['daniel_decision'] for row in sheet))


if __name__ == '__main__':
    unittest.main()
