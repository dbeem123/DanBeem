"""Build a draft §483.15 F-tag to NORS review sheet; no links are approved here."""
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from build_ftag_review_batch_1 import DATA, ROOT, linked_evidence, load, terms


FIELDS = [
    'tag', 'cms_title', 'regulation_sentence', 'candidate_code', 'table_2_definition',
    'evidence_1_text', 'evidence_1_locator', 'evidence_2_text', 'evidence_2_locator',
    'evidence_3_text', 'evidence_3_locator', 'shared_terms', 'basis', 'score',
    'matched_norc_scenario', 'scenario_answer_code', 'scenario_locator',
    'decision', 'added_code', 'reviewer_note',
]


def existing_links(catalog):
    result = defaultdict(set)
    for row in catalog:
        values = row.get('appendix_pp_tags', [])
        if isinstance(values, dict):
            values = [values]
        for value in values:
            tag = str(value.get('citation', '') if isinstance(value, dict) else value).upper().strip()
            if re.fullmatch(r'F\d{3,4}', tag):
                result[tag].add(row['nors_minor_code'])
    return result


def evidence_for(tag):
    passage_map = {p['id']: p for p in tag['passages']}
    grouped = [linked_evidence(p, passage_map, tag['source_file']) for p in tag['passages']
               if not p.get('continued_from_passage_id')]
    # CMS severity examples are within Deficiency categorization in these extracts.
    return [p for p in grouped if p.get('is_example') or p['section_label'] in
            ('Key elements of noncompliance', 'Deficiency categorization') or
            'severity' in p['section_label'].lower()]


def main():
    authority = load(DATA / 'nors_primary_authority.json')['authority_records']
    definitions = {r['code']: r for r in authority if r['authority_type'] == 'nors_table_2_definition'}
    catalog = load(ROOT / 'crosswalk_catalog.json')['records']
    existing = existing_links(catalog)
    frequencies = Counter(term for row in definitions.values() for term in terms(row['text']))
    weights = {term: math.log((len(definitions) + 1) / (count + 1)) + 1
               for term, count in frequencies.items()}
    scenarios = [row for row in load(DATA / 'nors_coding_scenarios.json')['scenarios']
                 if row.get('kind') == 'official_training' and row.get('answer_status') == 'printed_official_answer']

    prior = load(DATA / 'nors_section_prior.json')
    category_c = next(item for item in prior['sections']['483.10']['categories'] if item['letter'] == 'C')
    lock = load(DATA / 'nors_source_pack_lock.json')['revision4_source_inventory']['files']
    table_lock = next(item for item in lock if item['name'] == 'NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf')
    table_path = ROOT / table_lock['source_file']
    if hashlib.sha256(table_path.read_bytes()).hexdigest() != table_lock['sha256']:
        raise ValueError('Table 2 source hash mismatch')
    draft_map = {
        'status': 'draft',
        'label': 'Proposed App guidance category filter for §483.15; Daniel approval pending',
        'approval_status': 'pending_Daniel',
        'controls_coding': False,
        'source_file': table_lock['source_file'],
        'source_sha256': table_lock['sha256'],
        'rationale': 'Table 2 labels category C “Admission, Transfer, Discharge, Eviction”. Existing app links remain visible as candidates even when outside category C.',
        'sections': {'483.15': {'categories': [category_c]}},
    }
    draft_path = DATA / 'nors_section_prior_483_15_draft.json'
    draft_path.write_text(json.dumps(draft_map, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

    all_tags = load(DATA / 'appendix_pp' / 'index.json')['tags']
    tags = [item for item in all_tags if '483.15' in item.get('cfr_section', '')]
    rows = []
    allowed = {'C'}
    for index_item in tags:
        tag = load(DATA / 'appendix_pp' / (index_item['tag'] + '.json'))
        evidence = evidence_for(tag)
        regulation = next((p['text'] for p in tag['passages'] if p['section_label'] == 'Regulation'), '')
        scored = []
        for code, definition in definitions.items():
            is_existing = code in existing[tag['tag']]
            if code[0] not in allowed and not is_existing:
                continue
            matches = []
            for passage in evidence:
                shared = terms(passage['text']) & terms(definition['text'])
                score = sum(weights.get(word, 0) for word in shared)
                if score >= 3:
                    matches.append((score, passage, shared))
            matches.sort(key=lambda item: (-item[0], item[1]['id']))
            if not matches and not is_existing:
                continue
            if not matches and is_existing and evidence:
                matches = [(0, evidence[0], set())]
            if matches:
                scenario_matches = []
                for scenario in scenarios:
                    if code not in scenario.get('expected_codes', []):
                        continue
                    overlap = terms(matches[0][1]['text']) & terms(scenario['scenario_text'])
                    scenario_score = sum(weights.get(word, 1) for word in overlap)
                    if scenario_score >= 12 and len(overlap) >= 3:
                        scenario_matches.append((scenario_score, scenario))
                scenario = max(scenario_matches, key=lambda item: item[0])[1] if scenario_matches else None
                scored.append((is_existing, matches[0][0], code, matches, scenario))
        if len(existing[tag['tag']]) > 5:
            raise ValueError(f"{tag['tag']} has more than five existing app links; manual review needed")
        scored.sort(key=lambda item: (-int(item[0]), -item[1], item[2]))
        if not scored:
            rows.append({'tag': tag['tag'], 'cms_title': tag['cms_short_title'],
                         'regulation_sentence': regulation, 'candidate_code': '',
                         'basis': 'no_candidate_for_review', 'decision': '', 'added_code': '',
                         'reviewer_note': 'No matching category C definition found in extracted example, key-element, or severity evidence.'})
            continue
        if len(scored) > 5:
            # Keep every current app link, then the strongest suggestions to a five-row ceiling.
            existing_rows = [item for item in scored if item[0]]
            scored = existing_rows + [item for item in scored if not item[0]][:5 - len(existing_rows)]
        for is_existing, score, code, matches, scenario in scored:
            row = {'tag': tag['tag'], 'cms_title': tag['cms_short_title'],
                   'regulation_sentence': regulation, 'candidate_code': code,
                   'table_2_definition': definitions[code]['text'],
                   'shared_terms': ', '.join(sorted(set().union(*(item[2] for item in matches[:3])))),
                   'basis': 'existing_app_link' if is_existing else 'keyword_match',
                   'score': f'{score:.3f}',
                   'matched_norc_scenario': scenario['scenario_text'] if scenario else '',
                   'scenario_answer_code': code if scenario else '',
                   'scenario_locator': f"{scenario['source_file']}; {scenario['locator']}" if scenario else '',
                   'decision': '', 'added_code': '', 'reviewer_note': ''}
            for number, (_, passage, _) in enumerate(matches[:3], 1):
                row[f'evidence_{number}_text'] = passage['text']
                row[f'evidence_{number}_locator'] = passage.get('evidence_locator') or (
                    f"{tag['source_file']}; PDF page {passage['pdf_page']}; "
                    f"{passage['section_label']}; {passage['id']}")
            rows.append(row)

    out = ROOT / 'docs' / 'nors_ftag_review_batch_2.csv'
    with out.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    per_tag = Counter(row['tag'] for row in rows)
    print('tags', len(tags), 'rows', len(rows))
    print('rows_per_tag', dict(sorted(per_tag.items())))
    print('existing_links', {tag['tag']: sorted(existing[tag['tag']]) for tag in tags if existing[tag['tag']]})
    print('draft_section_map', draft_path.relative_to(ROOT))
    print('review_csv', out.relative_to(ROOT))


if __name__ == '__main__':
    main()
