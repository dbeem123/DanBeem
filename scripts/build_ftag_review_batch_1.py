"""Create the Revision 6 human-review sheet from locked source extracts."""
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from pypdf import PdfReader
import hashlib

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


STOP = set('request requests follow staff resident residents facility facilities care planning ability defined ensure consider timing practice will some can level limited medical during needs harm immediate report others based making failure risk appropriate may must also other including the and for from with that this their they have has was were are into than then when where which what would could should shall include includes example examples such each any all use used under section requirements requirement information provided provide upon person persons program code codes complaint complaints does not but its you your about'.split())


def terms(text):
    return {w for w in re.findall(r"[a-z][a-z0-9'-]{2,}", text.lower()) if w not in STOP}


def main():
    authority = load(DATA / 'nors_primary_authority.json')['authority_records']
    definitions = {r['code']: r for r in authority if r['authority_type'] == 'nors_table_2_definition'}
    # Only answer-sheet/FAQ excerpts containing a single explicit answer code
    # are eligible. An answer cannot be inferred from a separate question.
    scenarios = []
    for r in authority:
        source = r.get('source_file', '').lower()
        codes = r.get('codes_mentioned', [])
        if ('quiz-answers' in source or 'faqs.pdf' in source) and len(codes) == 1 and codes[0] in definitions:
            # Require an explicit code attached to a complaint in one sentence;
            # code mentions elsewhere on a page do not establish an answer.
            code = codes[0]
            for sentence in re.split(r'(?<=[.!?])\s+', r['text']):
                if (re.search(r'\bcomplaint\b', sentence, re.I)
                        and re.search(r'\b' + re.escape(code) + r'\b', sentence, re.I)
                        and re.search(r'\b(?:because|based on|since|circumstances)\b', sentence, re.I)
                        and not re.search(r'\b(?:number of cases|complaint code for each)\b', sentence, re.I)):
                    scenarios.append((code, {**r, 'text': sentence}))
    # The Part II answer sheet prints the answer and scenario together on many
    # lines. Only accept rows whose code and question number share the same
    # printed line; multi-column or page-spanning rows need manual review.
    quiz_name = 'nors-training-part-II-quiz-answers.pdf'
    lock = load(DATA / 'nors_source_pack_lock.json')['revision4_source_inventory']['files']
    locked = next(r for r in lock if r['name'] == quiz_name)
    quiz_path = ROOT / locked['source_file']
    if hashlib.sha256(quiz_path.read_bytes()).hexdigest() != locked['sha256']:
        raise ValueError('quiz-answer source hash mismatch')
    for page_no, page in enumerate(PdfReader(str(quiz_path)).pages, 1):
        text = page.extract_text() or ''
        pattern = r'(?m)^([A-L][0O][1-9])[ \t]+(?:(?:Family|Staff)[ \t]+)?\d+\)[ \t]+([^\n]+(?:\n(?!\s*\n)[^\n]+)*)'
        for match in re.finditer(pattern, text):
            code = match.group(1).replace('O', '0')
            if code not in definitions:
                continue
            raw_situation = re.split(r'(?m)^\s*[A-L][0O][1-9]\s+\d+\)', match.group(2))[0]
            situation = ' '.join(raw_situation.split())
            if not 35 <= len(situation) <= 1500:
                continue
            scenarios.append((code, {'text': situation, 'source_file': locked['source_file'], 'locator': f'PDF page {page_no}; answer {code}'}))
    frequencies = Counter(w for r in definitions.values() for w in terms(r['text']))
    weights = {w: math.log((len(definitions) + 1) / (n + 1)) + 1 for w, n in frequencies.items()}
    existing = defaultdict(set)
    for row in load(ROOT / 'crosswalk_catalog.json')['records']:
        items = row.get('appendix_pp_tags', [])
        if isinstance(items, dict):
            items = [items]
        for item in items:
            tag = str(item.get('citation', '') if isinstance(item, dict) else item).upper().strip()
            if re.fullmatch(r'F\d{3,4}', tag):
                existing[tag].add(row['nors_minor_code'])
    # A proposed context filter only. Approval is deliberately not presumed.
    table_path = ROOT / 'source_data' / 'NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf'
    locked_table = next(r for r in lock if r['name'] == table_path.name)
    if hashlib.sha256(table_path.read_bytes()).hexdigest() != locked_table['sha256']:
        raise ValueError('Table 2 source hash mismatch')
    headings = {}
    for page_no, page in enumerate(PdfReader(str(table_path)).pages, 1):
        text = page.extract_text() or ''
        for match in re.finditer(r'(?m)^([^\n]*(?:\n[^\n]*)?\(Code ([A-L])\))', text):
            heading = re.sub(r'^\d+\s*\n', '', match.group(1).strip())
            # The PDF splits "Gross" across lines; preserve the extracted spelling.
            headings[match.group(2)] = {'letter': match.group(2), 'heading': heading,
                                        'locator': f'PDF page {page_no}; Table 2 category heading'}
    if not set('ABCDEFGHIJ') <= set(headings):
        raise ValueError('Missing Table 2 category heading')
    prior = {'status': 'draft_pending_approval', 'label': 'Proposed app guidance; awaiting Daniel approval',
             'approved_by': None, 'approved_date': None, 'controls_coding': False,
             'source_file': locked_table['source_file'], 'source_sha256': locked_table['sha256'],
             'sections': {section: {'categories': [headings[x] for x in letters]}
                          for section, letters in [('483.10', 'BCDEFGHIJ'), ('483.12', 'ABDFJ')]}}
    (DATA / 'nors_section_prior.json').write_text(json.dumps(prior, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    fields = ['tag', 'cms_title', 'regulation_sentence', 'candidate_code', 'table_2_definition',
              'evidence_1_text', 'evidence_1_locator', 'evidence_2_text', 'evidence_2_locator',
              'evidence_3_text', 'evidence_3_locator', 'shared_terms', 'basis', 'score',
              'matched_norc_scenario', 'scenario_answer_code', 'scenario_locator',
              'decision', 'added_code', 'reviewer_note']
    rows = []
    index = load(DATA / 'appendix_pp' / 'index.json')['tags']
    # The extract's first CFR mention can be an incidental cross-reference.
    # The document order is bounded by the verified F550 (§483.10) and F620
    # (§483.15) anchors in the locked Appendix PP.
    anchors = {item['tag']: item['pdf_page_start'] for item in index}
    for idx in index:
        if not anchors['F550'] <= idx['pdf_page_start'] < anchors['F620']:
            continue
        tag = load(DATA / 'appendix_pp' / (idx['tag'] + '.json'))
        situations = [p for p in tag['passages'] if p.get('is_example') or p['section_label'] in ('Deficiency categorization', 'Key elements of noncompliance')]
        if not situations:
            situations = next(([p] for p in tag['passages'] if p['section_label'] == 'Regulation'), [])
        if not situations:
            # Flag shared/low-text extracts explicitly rather than inventing regulation.
            continue
        situations = [p for p in situations if not re.search(r'severity level\s*1\s+does not apply', p['text'], re.I)]
        if not situations:
            situations = next(([p] for p in tag['passages'] if p['section_label'] == 'Regulation'), [])
        regulation = next((p['text'] for p in tag['passages'] if p['section_label'] == 'Regulation'), '')
        section = '483.10' if idx['pdf_page_start'] < anchors['F600'] else '483.12'
        allowed = {r['letter'] for r in prior['sections'][section]['categories']}
        scored = []
        for code, definition in definitions.items():
            is_existing = code in existing[tag['tag']]
            if code[0] not in allowed and not is_existing:
                continue
            matches = []
            for passage in situations:
                shared = terms(passage['text']) & terms(definition['text'])
                score = sum(weights.get(w, 0) for w in shared)
                if score >= 3:
                    matches.append((score, passage, shared))
            matches.sort(key=lambda item: (-item[0], item[1]['id']))
            if not matches and not is_existing:
                continue
            if not matches:
                # Preserve an existing app link, clearly marked, without invented overlap.
                matches = [(0, p, set()) for p in situations[:1]]
            if not matches:
                continue
            best_scenarios = []
            for scode, scenario in scenarios:
                if scode == code:
                    overlap = terms(matches[0][1]['text']) & terms(scenario['text'])
                    scenario_score = sum(weights.get(w, 1) for w in overlap)
                    if scenario_score >= 12 and len(overlap) >= 3:
                        best_scenarios.append((scenario_score, scenario))
            scenario = max(best_scenarios, key=lambda x: x[0])[1] if best_scenarios else None
            scored.append((is_existing, matches[0][0], code, matches, scenario))
        if sum(item[0] for item in scored) > 5:
            raise ValueError(f"{tag['tag']} has more than five existing links; manual review required")
        scored.sort(key=lambda item: (-int(item[0]), -item[1], item[2]))
        if not scored:
            passage = situations[0] if situations else next((p for p in tag['passages'] if p['section_label'] == 'Regulation'), None)
            row = {'tag': tag['tag'], 'cms_title': tag['cms_short_title'], 'regulation_sentence': regulation,
                   'candidate_code': '', 'basis': 'no_candidate_for_review', 'decision': '', 'added_code': '', 'reviewer_note': ''}
            if passage:
                row['evidence_1_text'] = passage['text']
                row['evidence_1_locator'] = f"{tag['source_file']}; PDF page {passage['pdf_page']}; {passage['section_label']}; {passage['id']}"
            rows.append(row)
        for is_existing, score, code, matches, scenario in scored[:5]:
            row = {'tag': tag['tag'], 'cms_title': tag['cms_short_title'], 'regulation_sentence': regulation,
                   'candidate_code': code, 'table_2_definition': definitions[code]['text'],
                   'shared_terms': ', '.join(sorted(set().union(*(item[2] for item in matches[:3])))),
                   'basis': 'existing_app_link' if is_existing else 'keyword_match', 'score': f'{score:.3f}',
                   'matched_norc_scenario': scenario['text'] if scenario else '',
                   'scenario_answer_code': code if scenario else '',
                   'scenario_locator': f"{scenario['source_file']}; {scenario['locator']}" if scenario else '',
                   'decision': '', 'added_code': '', 'reviewer_note': ''}
            for n, (_, passage, _) in enumerate(matches[:3], 1):
                row[f'evidence_{n}_text'] = passage['text']
                row[f'evidence_{n}_locator'] = f"{tag['source_file']}; PDF page {passage['pdf_page']}; {passage['section_label']}; {passage['id']}"
            rows.append(row)
    out = ROOT / 'docs' / 'nors_ftag_review_batch_1.csv'
    with out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print('rows', len(rows), 'scenarios', len(scenarios))
    print('rows_per_tag', dict(sorted(Counter(r['tag'] for r in rows).items())))
    print('F554', [(r.get('candidate_code', ''), r.get('basis', ''), r['score']) for r in rows if r['tag'] == 'F554'])


if __name__ == '__main__':
    main()
