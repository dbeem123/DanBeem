"""Extract source-quoted coding distinctions for later human review.

No questions or code decisions are inferred. Table 2 outranks NORC guidance.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
USE = re.compile(r'\bUse\b.*?(?:\.(?=\s+[A-Z]|\s*$)|$)')
CODE = re.compile(r'(?<![A-Z0-9])([A-L])\s*0?([1-9]|1[0-3])(?![0-9])', re.I)
CONDITION = re.compile(r'\b(?:if|when|for)\b\s+.+', re.I)


def extract(records):
    out = []
    sources = {'nors_table_2_definition', 'norc_nors_handout', 'nors_training_or_faq'}
    for source in records:
        if source['authority_type'] not in sources:
            continue
        for match in USE.finditer(source['text']):
            quote = match.group(0).strip()
            # In explanatory training pages, keep only actual code contrasts.
            referenced = sorted({f'{m.group(1).upper()}{int(m.group(2)):02d}' for m in CODE.finditer(quote)})
            if source['authority_type'] == 'nors_training_or_faq' and len(referenced) < 2:
                continue
            from_code = source.get('code')
            condition = CONDITION.search(quote)
            # 'Use for/when/if' applies to the current definition; a named code
            # is assigned only when there is exactly one unambiguous code.
            leading = re.match(r'Use\s+(?:code\s+)?([A-L]\s*0?\d{1,2})\b', quote, re.I)
            if leading:
                parsed = CODE.search(leading.group(1))
                to_code = f'{parsed.group(1).upper()}{int(parsed.group(2)):02d}' if parsed and len(referenced) == 1 and not re.search(r'\b(?:or|and)\s+[A-L]\s*0?\d', quote, re.I) else None
            elif re.match(r'Use\s+(?:for|if|when|this code)\b', quote, re.I):
                to_code = from_code
            else:
                to_code = None
            out.append({
                'id': f"{source['id']}-use-{len([r for r in out if r['authority_id'] == source['id']]) + 1}",
                'from_code': from_code, 'to_code': to_code, 'referenced_codes': referenced,
                'verbatim_rule': quote, 'locator': source['locator'],
                'source_file': source['source_file'], 'source_sha256': source['source_sha256'],
                'source_priority': 'controlling_table_2' if source['authority_type'] == 'nors_table_2_definition' else 'companion_guidance',
                'authority_id': source['id'],
                'distinguishing_fact': condition.group(0) if condition else None,
                'question': None, 'question_label': 'App wording; pending Daniel review',
                'status': 'draft', 'controls_coding': False,
            })
    return out


def main():
    records = json.loads((DATA / 'nors_primary_authority.json').read_text(encoding='utf-8'))['authority_records']
    items = extract(records)
    all_codes = {r['code'] for r in records if r['authority_type'] == 'nors_table_2_definition'}
    counts = Counter(r['from_code'] for r in items if r['from_code'])
    payload = {'version': '1.0', 'status': 'draft', 'controls_coding': False,
               'method': 'Verbatim Use sentences from Table 2 and NORC handout; explicit training contrasts only. Null fields require human review.',
               'rules': items, 'counts_by_code': {code: counts[code] for code in sorted(all_codes)},
               'codes_without_rules': sorted(all_codes - set(counts))}
    (DATA / 'nors_distinctions.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f"{len(items)} rules; {len(payload['codes_without_rules'])} codes without rules; {sum(r['to_code'] is None for r in items)} unresolved target codes")


if __name__ == '__main__':
    main()
