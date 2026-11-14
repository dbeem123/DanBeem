from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


class DistinctionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((DATA / 'nors_distinctions.json').read_text(encoding='utf-8'))
        cls.sources = {r['id']: r for r in json.loads((DATA / 'nors_primary_authority.json').read_text(encoding='utf-8'))['authority_records']}

    def test_all_rules_trace_to_source_without_invented_questions(self):
        self.assertTrue(self.data['rules'])
        for rule in self.data['rules']:
            source = self.sources[rule['authority_id']]
            self.assertIn(rule['verbatim_rule'], source['text'])
            self.assertEqual(rule['locator'], source['locator'])
            self.assertEqual(rule['source_sha256'], source['source_sha256'])
            if rule['distinguishing_fact']:
                self.assertIn(rule['distinguishing_fact'], rule['verbatim_rule'])
            self.assertIsNone(rule['question'])
            self.assertEqual(rule['status'], 'draft')
            self.assertFalse(rule['controls_coding'])
            path = ROOT / rule['source_file']
            if path.is_file():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), rule['source_sha256'])

    def test_financial_exploitation_rule_and_code_coverage(self):
        expected = 'Use A04 (Financial exploitation) if improper use of property or money is for the benefit of others.'
        rows = [r for r in self.data['rules'] if r['from_code'] == 'E02' and r['to_code'] == 'A04']
        self.assertTrue(any(r['verbatim_rule'] == expected and r['distinguishing_fact'] == 'if improper use of property or money is for the benefit of others.' for r in rows))
        self.assertEqual(len(self.data['counts_by_code']), 60)
        self.assertEqual(self.data['codes_without_rules'], sorted(c for c, n in self.data['counts_by_code'].items() if n == 0))


if __name__ == '__main__':
    unittest.main()
