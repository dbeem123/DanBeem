"""Create the separate Daniel review sheet; live distinction questions stay blank."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/nors_distinctions.json'
OUTPUT = ROOT / 'docs/nors_distinctions_review.csv'
FIELDS = ['code', 'verbatim_rule', 'locator', 'proposed_question', 'daniel_decision']


def proposed_question(rule):
    fact = (rule.get('distinguishing_fact') or '').strip().rstrip(' .;')
    if not fact:
        match = re.search(r'\b(?:if|when|for)\b\s+(.+?)(?:[.;]|$)', rule['verbatim_rule'], re.I)
        fact = match.group(1).strip() if match else 'the situation described by the rule'
    # Some extracted Use sentences have a matched parenthetical ending just
    # before the actual condition (for example, “for assistance) if staff…”).
    if re.search(r'\)\s*(?:if|when)\s+', fact, re.I):
        fact = re.split(r'\)\s*(?:if|when)\s+', fact, maxsplit=1, flags=re.I)[1]
    fact = re.sub(r'^(?:if|when|for)\s+', '', fact, flags=re.I)
    fact = fact.strip(' )')
    return f'Proposed: Do the facts fit this condition: "{fact}"?'


def build_rows(rules):
    return [{'code': row.get('from_code') or '', 'verbatim_rule': row['verbatim_rule'],
             'locator': row['locator'], 'proposed_question': proposed_question(row),
             'daniel_decision': ''} for row in rules]


def main():
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    rows = build_rows(data['rules'])
    with OUTPUT.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {OUTPUT.relative_to(ROOT)}: {len(rows)} proposed questions; live questions were not changed.')


if __name__ == '__main__':
    main()
