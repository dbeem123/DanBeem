"""Validate authored example complaints after humans populate the worksheet.

The checked-in worksheet is intentionally blank. Use --allow-empty to verify
that blank template; ordinary validation requires the complete per-code counts.
Complaint entries are newline-separated and their aligned metadata are too.
"""
import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSHEET = ROOT / 'docs/nors_example_worksheet.csv'
FIELDS = {'code', 'table_2_definition', 'use_phrases', 'use_code_instead_rules',
          'reviewed_f_tags', 'example_complaints', 'example_voice_labels',
          'example_markings', 'near_miss_complaints', 'near_miss_voice_labels',
          'near_miss_markings', 'daniel_review'}
SAMPLE_COLUMNS = ('example_complaints', 'example_voice_labels', 'example_markings',
                  'near_miss_complaints', 'near_miss_voice_labels', 'near_miss_markings')


def lines(value):
    return [part.strip() for part in (value or '').splitlines() if part.strip()]


def quote_matches_definition(complaint, definition):
    quoted = re.findall(r'["“]([^"”]+)["”]', complaint)
    return any(len(fragment.split()) >= 2 and fragment.casefold() in definition.casefold()
               for fragment in quoted)


def validate_entry(row, require_counts=True):
    errors = []
    for prefix, count_range in (('example', range(5, 7)), ('near_miss', range(1, 3))):
        complaints = lines(row.get(f'{prefix}_complaints', ''))
        voices = lines(row.get(f'{prefix}_voice_labels', ''))
        markings = lines(row.get(f'{prefix}_markings', ''))
        if not complaints and not voices and not markings and not require_counts:
            continue
        if len(complaints) not in count_range:
            errors.append(f'{prefix}: expected {count_range.start}–{count_range.stop - 1} entries, got {len(complaints)}')
        if len(voices) != len(complaints) or any(not voice for voice in voices):
            errors.append(f'{prefix}: each complaint needs one voice label')
        if len(markings) != len(complaints) or any(mark != 'illustrative, project-written' for mark in markings):
            errors.append(f'{prefix}: every entry must be marked illustrative, project-written')
        for number, complaint in enumerate(complaints, 1):
            if not quote_matches_definition(complaint, row.get('table_2_definition', '')):
                errors.append(f'{prefix} {number}: no quoted Table 2 phrase appears in this code definition')
    return errors


def validate_rows(rows, allow_empty=False):
    errors = []
    if not rows:
        return ['worksheet has no rows']
    if not FIELDS <= set(rows[0]):
        return [f'missing worksheet columns: {sorted(FIELDS - set(rows[0]))}']
    codes = [row['code'] for row in rows]
    if len(codes) != len(set(codes)):
        errors.append('duplicate NORS code rows')
    all_blank = all(not any((row.get(column) or '').strip() for column in SAMPLE_COLUMNS)
                    for row in rows)
    if all_blank and allow_empty:
        return errors
    if all_blank:
        return ['worksheet is blank; pass --allow-empty for a template check']
    for row in rows:
        errors.extend(f"{row.get('code')}: {error}" for error in validate_entry(row, require_counts=True))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-empty', action='store_true', help='validate the intentionally blank template')
    args = parser.parse_args()
    with WORKSHEET.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    errors = validate_rows(rows, allow_empty=args.allow_empty)
    if errors:
        for error in errors:
            print(f'FAIL: {error}')
        raise SystemExit(1)
    print(f'PASS: {len(rows)} code rows; ' + ('blank template' if args.allow_empty else 'complaint counts, quotations, voices, and labels'))


if __name__ == '__main__':
    main()
