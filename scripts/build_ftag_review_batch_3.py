"""Build draft F-tag to NORS candidates for §§483.20–483.21."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from build_ftag_review_batch_1 import DATA, ROOT, load, terms, title_regulation_fallback
from build_ftag_review_batch_2 import FIELDS, evidence_for, existing_links


def main():
    authority = load(DATA / 'nors_primary_authority.json')['authority_records']
    definitions = {row['code']: row for row in authority if row['authority_type'] == 'nors_table_2_definition'}
    frequencies = Counter(term for row in definitions.values() for term in terms(row['text']))
    weights = {term: math.log((len(definitions) + 1) / (count + 1)) + 1
               for term, count in frequencies.items()}
    catalog = load(ROOT / 'crosswalk_catalog.json')['records']
    existing = existing_links(catalog)
    lock = load(DATA / 'nors_source_pack_lock.json')['revision4_source_inventory']['files']
    table_lock = next(row for row in lock if row['name'] == 'NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf')
    table_path = ROOT / table_lock['source_file']
    if hashlib.sha256(table_path.read_bytes()).hexdigest() != table_lock['sha256']:
        raise ValueError('Table 2 source hash mismatch')
    table2_c = next(row for row in load(DATA / 'nors_section_prior.json')['sections']['483.10']['categories'] if row['letter'] == 'F')
    draft = {
        'status': 'draft',
        'label': 'Proposed App guidance category filter for §§483.20–483.21; Daniel approval pending',
        'approval_status': 'pending_Daniel',
        'controls_coding': False,
        'source_file': table_lock['source_file'],
        'source_sha256': table_lock['sha256'],
        'rationale': 'Table 2 category F is “Care”; existing app links remain candidates even when outside category F.',
        'sections': {section: {'categories': [table2_c]} for section in ('483.20', '483.21')},
    }
    draft_path = DATA / 'nors_section_prior_483_20_21_draft.json'
    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

    index = load(DATA / 'appendix_pp' / 'index.json')['tags']
    selected = [row for row in index if '483.20' in row.get('cfr_section', '') or '483.21' in row.get('cfr_section', '')]
    rows = []
    allowed = {'F'}
    scenarios = [row for row in load(DATA / 'nors_coding_scenarios.json')['scenarios']
                 if row.get('kind') == 'official_training' and row.get('answer_status') == 'printed_official_answer']
    for index_item in selected:
        tag = load(DATA / 'appendix_pp' / f"{index_item['tag']}.json")
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
                score = sum(weights.get(term, 0) for term in shared)
                if score >= 3:
                    matches.append((score, passage, shared))
            matches.sort(key=lambda item: (-item[0], item[1]['id']))
            fallback_matches = title_regulation_fallback(tag, definition['text'])
            if fallback_matches and not is_existing:
                matches = fallback_matches + matches
            if not matches and not is_existing:
                continue
            if not matches and is_existing and evidence:
                matches = [(0, evidence[0], set())]
            if not matches:
                continue
            scenario_matches = []
            for scenario in scenarios:
                if code not in scenario.get('expected_codes', []):
                    continue
                overlap = terms(matches[0][1]['text']) & terms(scenario['scenario_text'])
                score = sum(weights.get(term, 1) for term in overlap)
                if score >= 12 and len(overlap) >= 3:
                    scenario_matches.append((score, scenario))
            scenario = max(scenario_matches, key=lambda item: item[0])[1] if scenario_matches else None
            scored.append((is_existing, matches[0][0], code, matches, scenario))
        if len(existing[tag['tag']]) > 5:
            raise ValueError(f"{tag['tag']} has more than five existing app links; manual review needed")
        scored.sort(key=lambda item: (-int(item[0]), -item[1], item[2]))
        if len(scored) > 5:
            existing_rows = [item for item in scored if item[0]]
            scored = existing_rows + [item for item in scored if not item[0]][:5 - len(existing_rows)]
        if not scored:
            rows.append({'tag': tag['tag'], 'cms_title': tag['cms_short_title'],
                         'regulation_sentence': regulation, 'candidate_code': '',
                         'basis': 'no_candidate_for_review', 'decision': '', 'added_code': '',
                         'reviewer_note': 'No matching category F definition found in extracted example, key-element, or severity evidence.'})
            continue
        for is_existing, score, code, matches, scenario in scored:
            row = {'tag': tag['tag'], 'cms_title': tag['cms_short_title'],
                   'regulation_sentence': regulation, 'candidate_code': code,
                   'table_2_definition': definitions[code]['text'],
                   'shared_terms': ', '.join(sorted(set().union(*(match[2] for match in matches[:3])))),
                   'basis': ('existing_app_link' if is_existing else
                             'title_regulation_fallback' if matches[0][1].get('title_regulation_fallback') else 'keyword_match'),
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

    out = ROOT / 'docs' / 'nors_ftag_review_batch_3.csv'
    with out.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row['tag'] for row in rows)
    print('tags', len(selected), 'rows', len(rows), 'candidate_rows', sum(bool(row['candidate_code']) for row in rows))
    print('rows_per_tag', dict(sorted(counts.items())))
    print('draft_section_map', draft_path.relative_to(ROOT))
    print('review_csv', out.relative_to(ROOT))


if __name__ == '__main__':
    main()
