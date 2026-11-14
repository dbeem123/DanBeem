"""Prepare Daniel's batch 3 decisions for an explicit, one-time import.

Safe by default: without --apply this only validates and previews. --apply also
requires --confirm-import. The review CSV itself is the source of decisions.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
TRIAGE = ROOT / 'docs/nors_ftag_review_batch_3_claude_triage.csv'
DATE = '2026-11-13'
METHOD = 'Daniel-directed triage 2026-11-13; not imported'


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def build_records(rows, tags, definitions):
    """Return append-only reviewed/rejected records without writing any file."""
    result = []
    seen = set()
    for row in rows:
        decision = row['decision'].strip().lower()
        if decision not in {'keep', 'add', 'drop'}:
            raise ValueError(f"Unresolved decision for {row['tag']}: {decision!r}")
        code = (row.get('added_code') or '').strip() if decision == 'add' else row['candidate_code'].strip()
        if not code:
            if decision != 'drop':
                raise ValueError(f"Missing candidate for {row['tag']} {decision}")
            continue
        pair = row['tag'], code
        if pair in seen:
            raise ValueError(f'Duplicate triage pair: {pair}')
        seen.add(pair)
        if row['tag'] not in tags or code not in definitions:
            raise ValueError(f'Unknown source pair: {pair}')
        triage_note = row.get('reviewer_note', '').strip()
        checked = bool(re.search(r'\bcheck\b', triage_note, re.I))
        common = {
            'f_tag': row['tag'], 'nors_code': code,
            'reviewed_by': 'Daniel', 'reviewer': 'Daniel',
            'reviewed_date': DATE,
            'review_method': 'approved Claude first-pass triage',
            'reviewer_note': triage_note,
        }
        if decision == 'drop':
            result.append({'status': 'rejected', 'basis': row.get('basis') or 'keyword_match', **common})
            continue

        tag = tags[row['tag']]
        evidence_passages = [
            row.get(f'evidence_{n}_text', '').strip()
            for n in range(1, 4) if row.get(f'evidence_{n}_text', '').strip()
        ]
        # Pick a quoted Appendix PP passage from the candidate row when possible.
        cited_pp = next((text for text in evidence_passages
                         if any(text in p['text'] or p['text'] in text for p in tag['passages'])), None)
        # F646 is an explicitly requested manual add whose evidence is title + Table 2.
        # Preserve a real, exact regulation passage as the app's source excerpt.
        source_passage = next((p for p in tag['passages']
                               if cited_pp and (cited_pp in p['text'] or p['text'] in cited_pp)), None)
        manual_f646 = row['tag'] == 'F646' and code == 'F03'
        if source_passage is None:
            source_passage = next((p for p in tag['passages']
                                   if p.get('section_label') == 'Regulation'
                                   and p['text'].strip()
                                   and (p['text'].strip() in row.get('regulation_sentence', '')
                                        or row.get('regulation_sentence', '').strip() in p['text'])), None)
        if source_passage is None:
            raise ValueError(f'No exact Appendix PP passage can support {pair}')
        definition = definitions[code]
        manual = manual_f646 or checked or 'title-only' in triage_note.lower()
        result.append({
            'status': 'reviewed', 'basis': 'coded_by_reviewer', **common,
            'nors_authority_id': definition['id'],
            'nors_excerpt': definition['text'],
            'appendix_passage_id': source_passage['id'],
            'appendix_excerpt': source_passage['text'],
            **({'link_strength': 'weak', 'evidence_basis': 'title_only'} if manual else {}),
            **({'reviewer_note': (triage_note + ' ' if triage_note else '') +
                'Manual F646/F03 addition; check; title and Table 2 evidence.'} if manual_f646 else {}),
        })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='append the validated records to the live review data')
    parser.add_argument('--confirm-import', action='store_true', help='required together with --apply')
    args = parser.parse_args()
    if args.apply != args.confirm_import:
        parser.error('--apply and --confirm-import must be supplied together')
    with TRIAGE.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    review = load_json(DATA / 'nors_reviewed_links.json')
    tags = {row['tag']: load_json(DATA / f"appendix_pp/{row['tag']}.json")
            for row in load_json(DATA / 'appendix_pp/index.json')['tags']}
    definitions = {row['code']: row for row in load_json(DATA / 'nors_primary_authority.json')['authority_records']
                   if row['authority_type'] == 'nors_table_2_definition'}
    additions = build_records(rows, tags, definitions)
    existing_pairs = {(item.get('f_tag'), item.get('nors_code')) for item in review['links']}
    duplicates = existing_pairs & {(item['f_tag'], item['nors_code']) for item in additions}
    if duplicates:
        raise ValueError(f'Review data already contains batch 3 pairs: {sorted(duplicates)}')
    reviewed = sum(item['status'] == 'reviewed' for item in additions)
    rejected = sum(item['status'] == 'rejected' for item in additions)
    print(f'Validated batch 3: {reviewed} reviewed/add records, {rejected} rejected records; no writes.')
    print('F646/F03 is included as weak/title-only/check.')
    if args.apply:
        review['links'].extend(additions)
        target = DATA / 'nors_reviewed_links.json'
        target.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(f'Imported {len(additions)} records into {target}')


if __name__ == '__main__':
    main()
