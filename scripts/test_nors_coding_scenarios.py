import hashlib
import json
import re
import unittest
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


class CodingScenariosTests(unittest.TestCase):
    def test_official_scenarios_and_answers_are_on_locked_source_page(self):
        payload = json.loads((DATA / 'nors_coding_scenarios.json').read_text(encoding='utf-8'))
        self.assertFalse(payload['controls_coding'])
        official = [r for r in payload['scenarios'] if r['kind'] == 'official_training']
        self.assertGreater(len(official), 0)
        self.assertEqual(len({r['id'] for r in official}), len(official))
        for row in official:
            path = ROOT / row['source_file']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['source_sha256'])
            match = re.fullmatch(r'PDF page (\d+); question (\d+); printed answer ([A-L]\d\d)', row['locator'])
            self.assertIsNotNone(match)
            page = PdfReader(str(path)).pages[int(match.group(1)) - 1].extract_text() or ''
            self.assertIn(norm(row['scenario_text']), norm(page))
            self.assertRegex(page, rf'(?m)^{match.group(3)}[ \t]+(?:(?:Family|Staff)[ \t]+)?{match.group(2)}\)')
            self.assertEqual(row['expected_codes'], [match.group(3)])
            self.assertNotRegex(row['scenario_text'].lower(), r'\bresidential care community\b')

    def test_synthetic_medication_answers_are_not_asserted(self):
        rows = json.loads((DATA / 'nors_coding_scenarios.json').read_text(encoding='utf-8'))['scenarios']
        synthetic = [r for r in rows if r['kind'] == 'synthetic_draft']
        self.assertGreaterEqual(len(synthetic), 2)
        for row in synthetic:
            self.assertEqual(row['expected_codes'], [])
            self.assertEqual(row['answer_status'], 'pending_daniel_review')
            self.assertIsNone(row['source_file'])


if __name__ == '__main__':
    unittest.main()
