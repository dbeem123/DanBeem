"""Create a blank, one-row-per-code example complaint review worksheet."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUTPUT = ROOT / 'docs/nors_example_worksheet.csv'
FIELDS = ['code', 'table_2_definition', 'use_phrases', 'use_code_instead_rules',
          'reviewed_f_tags', 'example_complaints', 'example_voice_labels',
          'example_markings', 'near_miss_complaints', 'near_miss_voice_labels',
          'near_miss_markings', 'daniel_review']


def extract_use_phrases(text):
    starts = list(re.finditer(r'\bUse\b', text))
    phrases = []
    for index, match in enumerate(starts):
        next_use = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        period = text.find('.', match.start(), next_use)
        end = period + 1 if period >= 0 else next_use
        phrase = text[match.start():end].strip()
        if phrase:
            phrases.append(phrase)
    return phrases


def build_rows():
    authority = json.loads((DATA / 'nors_primary_authority.json').read_text(encoding='utf-8'))['authority_records']
    definitions = sorted((row for row in authority if row['authority_type'] == 'nors_table_2_definition'),
                         key=lambda row: row['code'])
    distinctions = json.loads((DATA / 'nors_distinctions.json').read_text(encoding='utf-8'))['rules']
    review = json.loads((DATA / 'nors_reviewed_links.json').read_text(encoding='utf-8'))['links']
    reviewed = {}
    for row in review:
        if row.get('status') == 'reviewed':
            reviewed.setdefault(row['nors_code'], set()).add(row['f_tag'])
    result = []
    for definition in definitions:
        code = definition['code']
        rules = [row for row in distinctions
                 if row.get('from_code') == code or code in row.get('referenced_codes', [])]
        result.append({
            'code': code,
            'table_2_definition': definition['text'],
            'use_phrases': '\n'.join(extract_use_phrases(definition['text'])),
            'use_code_instead_rules': '\n'.join(
                f"{row['verbatim_rule']} [{row['locator']}]" for row in rules),
            'reviewed_f_tags': ', '.join(sorted(reviewed.get(code, set()))),
            'example_complaints': '', 'example_voice_labels': '', 'example_markings': '',
            'near_miss_complaints': '', 'near_miss_voice_labels': '', 'near_miss_markings': '',
            'daniel_review': '',
        })
    return result


def main():
    rows = build_rows()
    with OUTPUT.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {OUTPUT.relative_to(ROOT)}: {len(rows)} codes; all complaint/review columns blank.')


if __name__ == '__main__':
    main()
