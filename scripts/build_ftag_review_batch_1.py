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


STOP = set('request requests follow staff resident residents facility facilities care planning ability defined ensure consider timing practice the and for from with that this their they have has was were are into than then when where which what would could should must shall may include includes including example examples such also other each any all use used under section requirements requirement information provided provide upon person persons program code codes complaint complaints does not but its you your about'.split())


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
    fields = ['tag', 'cms_title', 'section_label', 'display_label', 'verbatim_situation', 'locator', 'candidate_code', 'table_2_definition', 'matched_norc_scenario', 'scenario_answer_code', 'scenario_locator', 'shared_terms', 'basis', 'score', 'decision', 'added_code', 'reviewer_note']
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
        for n, situation in enumerate(situations):
            source_terms = terms(situation['text'])
            scored = []
            for code, definition in definitions.items():
                shared = source_terms & terms(definition['text'])
                score = sum(weights[w] for w in shared if w in weights)
                matching = []
                for scode, scenario in scenarios:
                    if scode != code:
                        continue
                    overlap = source_terms & terms(scenario['text'])
                    scenario_score = sum(weights.get(w, 1) for w in overlap)
                    if scenario_score >= 3:
                        matching.append((scenario_score, scenario, overlap))
                best = max(matching, key=lambda x: x[0], default=None)
                if score < 3 and not best:
                    continue
                scored.append((bool(best), best[0] if best else 0, score, code, shared, best))
            scored.sort(key=lambda x: (-int(x[0]), -x[1], -x[2], x[3]))
            selected = scored[:3]
            label = ('Regulation (42 CFR)' if situation['section_label'] == 'Regulation' else
                     'CMS example of noncompliance (context)' if situation.get('is_example') or situation['section_label'] == 'Deficiency categorization' else
                     'CMS interpretive guidance')
            base = {'tag': tag['tag'], 'cms_title': tag['cms_short_title'], 'section_label': situation['section_label'], 'display_label': label, 'verbatim_situation': situation['text'], 'locator': f"{tag['source_file']}; PDF page {situation['pdf_page']}; {situation['section_label']}; {situation['id']}", 'decision': '', 'added_code': '', 'reviewer_note': ''}
            for _, _, score, code, shared, best in selected:
                scenario = best[1] if best else None
                rows.append({**base, 'candidate_code': code, 'table_2_definition': definitions[code]['text'], 'matched_norc_scenario': scenario['text'] if scenario else '', 'scenario_answer_code': code if scenario else '', 'scenario_locator': f"{scenario['source_file']}; {scenario['locator']}" if scenario else '', 'shared_terms': ', '.join(sorted(shared | (best[2] if best else set()))), 'basis': 'norc_scenario' if scenario else 'nors_definition', 'score': f'{score + (best[0] if best else 0):.3f}'})
            if not selected:
                rows.append(base)
            # Existing links are separate provenance rows; never silently drop a link
            # to satisfy the three generated-candidate limit.
            if n == 0:
                for code in sorted(existing[tag['tag']]):
                    if code in definitions:
                        rows.append({**base, 'candidate_code': code, 'table_2_definition': definitions[code]['text'], 'basis': 'existing_app_link'})
    out = ROOT / 'docs' / 'nors_ftag_review_batch_1.csv'
    with out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print('rows', len(rows), 'scenarios', len(scenarios))
    print('rows_per_tag', dict(sorted(Counter(r['tag'] for r in rows).items())))
    print('F554', [(r.get('candidate_code', ''), r.get('basis', ''), r['locator']) for r in rows if r['tag'] == 'F554'])


if __name__ == '__main__':
    main()
