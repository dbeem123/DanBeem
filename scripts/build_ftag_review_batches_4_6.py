"""Build non-operative review sheets and proposed triage for NORS batches 4–6."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from build_ftag_review_batch_1 import DATA, ROOT, load, stemmed_phrase_match, terms, title_regulation_fallback
from build_ftag_review_batch_2 import FIELDS, evidence_for, existing_links

CONFIG = {
    4: {'label': 'quality of care', 'lo': 24, 'hi': 25,
        'map': {'483.24': 'FG', '483.25': 'F'}},
    5: {'label': 'services', 'lo': 30, 'hi': 45,
        'map': {'483.30': 'F', '483.35': 'F', '483.40': 'F', '483.45': 'F'}},
    6: {'label': 'administration and environment', 'lo': 70, 'hi': 90,
        'map': {'483.70': 'J', '483.71': 'J', '483.75': 'J',
                '483.80': 'FJ', '483.85': 'J', '483.90': 'I'}},
}


def major_section(citation):
    match = re.search(r'483\.(\d+)', citation or '')
    return f'483.{int(match.group(1))}' if match else None


def selected_tags(batch, index):
    cfg = CONFIG[batch]
    result = []
    for item in index:
        section = major_section(item.get('cfr_section'))
        if section and cfg['lo'] <= int(section.split('.')[1]) <= cfg['hi']:
            result.append((section, item))
    return result


def draft_section_map(batch, sections, category_by_letter, table_lock):
    cfg = CONFIG[batch]
    payload_sections = {}
    for section in sections:
        letters = cfg['map'].get(section, '')
        payload_sections[section] = {'categories': [category_by_letter[x] for x in letters]}
    return {
        'status': 'draft', 'approval_status': 'pending_Daniel',
        'label': f'Proposed App guidance category filter for §§{cfg["lo"]}–{cfg["hi"]} ({cfg["label"]}); Daniel approval pending',
        'controls_coding': False, 'source_file': table_lock['source_file'],
        'source_sha256': table_lock['sha256'],
        'rationale': 'Draft category filters organize possible context links only; they do not rank or select complaint codes. Every association remains subject to source review.',
        'sections': payload_sections,
    }


def proposed_rule(row):
    if not row.get('candidate_code'):
        return 'needs_claude', 'R6_no_clean_fit', 'No clean candidate was generated; Claude review needed.'
    if row['basis'] == 'existing_app_link':
        return 'check', 'R4_existing_link_check', 'Existing app link retained for review; prior presence is not substantive evidence.'
    if row['basis'] == 'title_regulation_fallback':
        return 'check', 'R5_title_or_regulation_phrase_check', 'Phrase fallback is a review lead; verify the full source context.'
    phrase = stemmed_phrase_match(row.get('evidence_1_text', ''), row.get('table_2_definition', ''))
    if phrase:
        return 'check', 'R3_specific_phrase_check', f'Specific phrase overlap ({" ".join(phrase)}) merits review, not an automatic link.'
    return 'check', 'R3_specific_phrase_check', 'Specific phrase overlap merits review, not an automatic link.'


def build(batch):
    cfg = CONFIG[batch]
    authority = load(DATA / 'nors_primary_authority.json')['authority_records']
    definitions = {r['code']: r for r in authority if r['authority_type'] == 'nors_table_2_definition'}
    catalog = load(ROOT / 'crosswalk_catalog.json')['records']
    existing = existing_links(catalog)
    prior = load(DATA / 'nors_section_prior.json')
    category_by_letter = {r['letter']: r for section in prior['sections'].values()
                          for r in section['categories']}
    table_lock = next(row for row in load(DATA / 'nors_source_pack_lock.json')['revision4_source_inventory']['files']
                      if row['name'] == 'NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf')
    table_path = ROOT / table_lock['source_file']
    if hashlib.sha256(table_path.read_bytes()).hexdigest() != table_lock['sha256']:
        raise ValueError('Table 2 source hash mismatch')
    index = load(DATA / 'appendix_pp/index.json')['tags']
    chosen = selected_tags(batch, index)
    sections = sorted({section for section, _ in chosen}, key=lambda value: int(value.split('.')[1]))
    draft = draft_section_map(batch, sections, category_by_letter, table_lock)
    map_path = DATA / f'nors_section_prior_batch_{batch}_draft.json'
    map_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

    frequencies = Counter(term for row in definitions.values() for term in terms(row['text']))
    weights = {term: math.log((len(definitions) + 1) / (count + 1)) + 1
               for term, count in frequencies.items()}
    rows = []
    needs_claude = []
    for section, item in chosen:
        tag = load(DATA / f"appendix_pp/{item['tag']}.json")
        evidence = evidence_for(tag)
        regulation = next((p['text'] for p in tag['passages'] if p['section_label'] == 'Regulation'), '')
        allowed = {category['letter'] for category in draft['sections'][section]['categories']}
        scored = []
        for code, definition in definitions.items():
            is_existing = code in existing[tag['tag']]
            if code[0] not in allowed and not is_existing:
                continue
            matches = []
            for passage in evidence:
                shared = terms(passage['text']) & terms(definition['text'])
                score = sum(weights.get(term, 0) for term in shared)
                # A weighted one-word collision is not a clean NORS fit. Keep
                # lexical candidates only when the deterministic phrase
                # matcher finds a specific shared phrase.
                if score >= 3 and stemmed_phrase_match(passage['text'], definition['text']):
                    matches.append((score, passage, shared))
            matches.sort(key=lambda result: (-result[0], result[1]['id']))
            fallback = title_regulation_fallback(tag, definition['text'])
            if fallback and not is_existing:
                matches = fallback + matches
            if not matches and is_existing and evidence:
                matches = [(0, evidence[0], set())]
            if matches:
                scored.append((is_existing, matches[0][0], code, matches))
        if len(existing[tag['tag']]) > 5:
            raise ValueError(f"{tag['tag']} has more than five existing app links; manual review needed")
        scored.sort(key=lambda result: (-int(result[0]), -result[1], result[2]))
        if len(scored) > 5:
            old = [result for result in scored if result[0]]
            scored = old + [result for result in scored if not result[0]][:5-len(old)]
        if not scored:
            row = {'tag': tag['tag'], 'cms_title': tag['cms_short_title'],
                   'regulation_sentence': regulation, 'candidate_code': '',
                   'basis': 'no_candidate_for_review', 'decision': '', 'added_code': '',
                   'reviewer_note': 'No clean candidate generated; needs Claude.'}
            decision, rule, note = proposed_rule(row)
            rows.append({**row, 'proposed_decision': decision, 'rubric_rule': rule, 'proposal_note': note})
            needs_claude.append(tag['tag'])
            continue
        for is_existing, score, code, matches in scored:
            definition = definitions[code]
            row = {'tag': tag['tag'], 'cms_title': tag['cms_short_title'],
                   'regulation_sentence': regulation, 'candidate_code': code,
                   'table_2_definition': definition['text'],
                   'shared_terms': ', '.join(sorted(set().union(*(m[2] for m in matches[:3])))),
                   'basis': ('existing_app_link' if is_existing else
                             'title_regulation_fallback' if matches[0][1].get('title_regulation_fallback') else 'keyword_match'),
                   'score': f'{score:.3f}', 'matched_norc_scenario': '', 'scenario_answer_code': '',
                   'scenario_locator': '', 'decision': '', 'added_code': '', 'reviewer_note': ''}
            for n, (_, passage, _) in enumerate(matches[:3], 1):
                row[f'evidence_{n}_text'] = passage['text']
                row[f'evidence_{n}_locator'] = passage.get('evidence_locator') or (
                    f"{tag['source_file']}; PDF page {passage['pdf_page']}; {passage['section_label']}; {passage['id']}")
            decision, rule, note = proposed_rule(row)
            rows.append({**row, 'proposed_decision': decision, 'rubric_rule': rule, 'proposal_note': note})

    stem = f'nors_ftag_review_batch_{batch}'
    review_path = ROOT / 'docs' / f'{stem}.csv'
    proposed_path = ROOT / 'docs' / f'{stem}_codex_proposed_triage.csv'
    report_path = ROOT / 'docs' / f'{stem}_report_20261113.md'
    with review_path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n'); writer.writeheader()
        writer.writerows([{key: value for key, value in row.items() if key in FIELDS} for row in rows])
    proposed_fields = FIELDS + ['proposed_decision', 'rubric_rule', 'proposal_note']
    with proposed_path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=proposed_fields, lineterminator='\n'); writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row['tag'] for row in rows)
    proposals = Counter(row['proposed_decision'] for row in rows)
    report = [f"# Batch {batch}: §483.{cfg['lo']}–{cfg['hi']} — {cfg['label']}", '',
              '**Status: draft for Daniel and Claude review. No proposed links were imported.**', '',
              f'- Tags: {len(chosen)}; review rows: {len(rows)}.',
              f'- Proposed outcomes: {dict(sorted(proposals.items()))}.',
              f'- Section map: `{map_path.relative_to(ROOT).as_posix()}` (`draft`, `pending_Daniel`, `controls_coding: false`).',
              f'- Review sheet: `{review_path.relative_to(ROOT).as_posix()}`.',
              f'- Proposed triage: `{proposed_path.relative_to(ROOT).as_posix()}`.',
              f'- Needs Claude (no clean generated candidate): {", ".join(needs_claude) if needs_claude else "none"}.', '',
              'Each proposed row names a rule in `docs/nors_triage_rubric.md`; all uncertain matches are `check`. `needs_claude` means the builder produced no candidate and no code was invented. Existing app links are retained as checks. The draft section map filters review candidates only and has no coding effect.', '',
              '## Rows per tag', '', '| Tag | Rows |', '|---|---:|']
    report.extend(f'| {tag} | {count} |' for tag, count in sorted(counts.items()))
    report_path.write_text('\n'.join(report) + '\n', encoding='utf-8', newline='\n')
    return {'batch': batch, 'tags': len(chosen), 'rows': len(rows), 'counts': counts,
            'proposals': proposals, 'needs_claude': needs_claude,
            'paths': [review_path, proposed_path, report_path, map_path]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=int, choices=(4, 5, 6), required=True)
    args = parser.parse_args()
    result = build(args.batch)
    print(f"batch {result['batch']}: {result['tags']} tags, {result['rows']} rows, proposals={dict(result['proposals'])}")
    print('needs_claude:', ', '.join(result['needs_claude']) or 'none')
    for path in result['paths']:
        print(path.relative_to(ROOT))


if __name__ == '__main__':
    main()
