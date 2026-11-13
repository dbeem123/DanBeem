"""Build a review-only regression corpus from the locked NORC answer sheet."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
SOURCE = 'nors-training-part-II-quiz-answers.pdf'


def normal(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def extract() -> list[dict]:
    lock = json.loads((DATA / 'nors_source_pack_lock.json').read_text(encoding='utf-8'))
    meta = next(x for x in lock['revision4_source_inventory']['files'] if x['name'] == SOURCE)
    path = ROOT / meta['source_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
        raise ValueError('NORC quiz source hash mismatch')
    # Only source rows with the code and question number on the same line.
    # A second answer marker or a paragraph break ends the excerpt. Rows
    # needing multi-column inference remain out pending human confirmation.
    pattern = re.compile(r'(?m)^([A-L][0O][1-9])[ \t]+(?:(?:Family|Staff)[ \t]+)?(\d+)\)[ \t]+([^\n]+(?:\n(?!\s*\n)[^\n]+)*)')
    next_marker = re.compile(r'(?m)^\s*[A-L][0O][1-9]\s+(?:[^\n]{0,40}?\s+)?\d+\)')
    rows = []
    for page_no, page in enumerate(PdfReader(str(path)).pages, 1):
        for match in pattern.finditer(page.extract_text() or ''):
            code = match.group(1).replace('O', '0')
            body = next_marker.split(match.group(3), maxsplit=1)[0]
            text = normal(body)
            if not 35 <= len(text) <= 1500:
                continue
            if re.search(r'\bresidential care community\b', text, re.I):
                continue  # This project is scoped to nursing facilities.
            rows.append({'id': f'norc-part-ii-p{page_no}-q{match.group(2)}-{code.lower()}',
                         'kind': 'official_training', 'scenario_text': text,
                         'expected_codes': [code], 'answer_status': 'printed_official_answer',
                         'source_file': meta['source_file'], 'source_sha256': meta['sha256'],
                         'locator': f'PDF page {page_no}; question {match.group(2)}; printed answer {code}'})
    return rows


def main() -> None:
    rows = extract()
    synthetic = [
        ('self-administer-denied', 'A resident asks to manage their own medications. The resident says the facility refused the request.'),
        ('self-administer-assessment', 'A resident asks to self-administer medication and says no interdisciplinary assessment has been discussed.'),
        ('wrong-medication', 'A resident says a different medication was given to them in error.'),
    ]
    rows.extend({'id': 'synthetic-' + key, 'kind': 'synthetic_draft', 'scenario_text': text,
                 'expected_codes': [], 'answer_status': 'pending_daniel_review',
                 'source_file': None, 'source_sha256': None, 'locator': None}
                for key, text in synthetic)
    payload = {'version': '1.0', 'status': 'draft', 'controls_coding': False,
               'note': 'Only unambiguous printed quiz rows are included; explicit residential care examples are excluded. Other quizzes and uncertain answers require review. Synthetic answers require Daniel review. This is not a coding decision tool.',
               'scenarios': rows}
    (DATA / 'nors_coding_scenarios.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(rows) - len(synthetic)} official scenarios; {len(synthetic)} synthetic scenarios pending answer review')


if __name__ == '__main__':
    main()
