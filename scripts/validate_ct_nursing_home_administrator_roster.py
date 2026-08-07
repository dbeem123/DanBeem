#!/usr/bin/env python3
"""Validate the ignored Connecticut DPH nursing home administrator roster.

This script is intentionally read-only: it prints source-validation findings and
does not create a runtime dataset or modify the source CSV.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    REPO_ROOT
    / "source_data"
    / "ct_dph"
    / "Nursing_Home_Administrator_2026-05-22.csv"
)
ROSTER_DATE = date(2026, 5, 22)
LEGACY_ISSUE_DATE = date(1901, 1, 1)

EXPECTED_COLUMNS = [
    "LICENSE NO.",
    "FIRST NAME",
    "LAST NAME",
    "ADDRESS1",
    "ADDRESS2",
    "CITY",
    "STATE",
    "ZIP",
    "COUNTY",
    "STATUS",
    "REASON",
    "ISSUE DATE",
    "EXPIRATION DATE",
]

FACILITY_AFFILIATION_COLUMN_TERMS = {
    "facility name",
    "nursing home name",
    "employer",
    "work address",
    "facility license number",
    "cms certification number",
    "ccn",
    "national provider identifier",
    "npi",
    "connecticut facility identifier",
}

DATE_FORMATS = ("%m/%d/%Y", "%m/%d/%y")
ZIP_WITH_O_RE = re.compile(r"^[0-9O]{5}(?:-[0-9O]{4})?$", re.IGNORECASE)
VALID_US_ZIP_RE = re.compile(r"^\d{5}(?:-\d{4})?$")
LICENSE_FORMULA_RE = re.compile(r"^=\s*([\"'])(.*?)\1\s*$")


def clean_text(value: str | None) -> str:
    """Trim leading/trailing whitespace and collapse repeated whitespace."""

    return re.sub(r"\s+", " ", (value or "").strip())


def normalize_license_number(raw_value: str | None) -> tuple[str, list[str]]:
    """Normalize a license identifier without numeric conversion.

    Spreadsheet formula-style wrappers and unnecessary matching quote pairs are
    removed. Leading zeros remain intact because the value always stays a string.
    """

    raw = clean_text(raw_value)
    value = raw
    flags: list[str] = []

    formula_match = LICENSE_FORMULA_RE.fullmatch(value)
    if formula_match:
        value = clean_text(formula_match.group(2))
        flags.append("spreadsheet_formula_wrapper_removed")

    while len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = clean_text(value[1:-1])
        flags.append("surrounding_quotes_removed")

    if value and not value.isdigit():
        flags.append("unexpected_license_number_format")

    return value, flags


def normalized_match_name(parts: Iterable[str]) -> str:
    """Create a conservative comparison key; never use it as a person ID."""

    display = " ".join(clean_text(part) for part in parts if clean_text(part))
    decomposed = unicodedata.normalize("NFKD", display)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    alphanumeric_tokens = re.sub(r"[^0-9A-Za-z]+", " ", without_marks)
    return clean_text(alphanumeric_tokens).upper()


def normalize_name_fields(row: dict[str, str]) -> dict[str, str]:
    """Create validation-only normalized name fields from available columns."""

    first_name = clean_text(row.get("FIRST NAME"))
    last_name = clean_text(row.get("LAST NAME"))
    middle_name = ""  # No source column in the May 22, 2026 roster.
    suffix = ""  # No source column in the May 22, 2026 roster.
    display_name = clean_text(" ".join((first_name, middle_name, last_name, suffix)))
    return {
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "suffix": suffix,
        "display_name": display_name,
        "normalized_match_name": normalized_match_name(
            (first_name, middle_name, last_name, suffix)
        ),
    }


def normalize_zip(raw_value: str | None) -> tuple[str, bool, list[str]]:
    """Normalize a ZIP conservatively while preserving the raw value elsewhere."""

    raw = clean_text(raw_value)
    value = raw.upper().replace(" ", "")
    corrected = False
    flags: list[str] = []

    if not value:
        return "", corrected, flags

    if "O" in value and ZIP_WITH_O_RE.fullmatch(value):
        candidate = value.replace("O", "0")
        if VALID_US_ZIP_RE.fullmatch(candidate):
            value = candidate
            corrected = True
            flags.append("zip_letter_o_corrected_to_zero")

    if not VALID_US_ZIP_RE.fullmatch(value):
        flags.append("unexpected_zip_format")

    return value, corrected, flags


def parse_source_date(raw_value: str | None) -> tuple[date | None, str | None]:
    """Parse a source date using explicit roster formats."""

    value = clean_text(raw_value)
    if not value:
        return None, None
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date(), None
        except ValueError:
            continue
    return None, "invalid_date"


def count_duplicate_values(values: Iterable[str]) -> tuple[int, dict[str, int]]:
    counts = Counter(value for value in values if value)
    duplicates = {value: count for value, count in counts.items() if count > 1}
    return sum(count - 1 for count in duplicates.values()), duplicates


def analyze(source_path: Path) -> dict[str, object]:
    if not source_path.is_file():
        raise FileNotFoundError(f"Source roster not found: {source_path}")

    with source_path.open("r", encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        columns = reader.fieldnames
        if columns is None:
            raise ValueError("The source CSV does not contain a header row.")
        missing_columns = [column for column in EXPECTED_COLUMNS if column not in columns]
        unexpected_columns = [column for column in columns if column not in EXPECTED_COLUMNS]
        if missing_columns:
            raise ValueError(
                "Required source columns are missing: " + ", ".join(missing_columns)
            )
        rows = list(reader)

    completely_blank_rows = [
        index
        for index, row in enumerate(rows, start=2)
        if not any(clean_text(row.get(column)) for column in columns)
    ]
    entirely_blank_columns = [
        column
        for column in columns
        if not any(clean_text(row.get(column)) for row in rows)
    ]
    column_blank_counts = {
        column: sum(not clean_text(row.get(column)) for row in rows)
        for column in columns
    }

    license_numbers: list[str] = []
    license_examples: list[dict[str, object]] = []
    license_samples: list[dict[str, object]] = []
    malformed_licenses: list[dict[str, object]] = []
    name_keys: list[str] = []
    name_examples: list[dict[str, str]] = []
    zip_o_examples: list[dict[str, object]] = []
    unexpected_zip_examples: list[dict[str, object]] = []
    invalid_date_examples: list[dict[str, object]] = []
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    status_reason_counts: Counter[tuple[str, str]] = Counter()
    state_counts: Counter[str] = Counter()
    issue_dates: list[date] = []
    expiration_dates: list[date] = []
    expiration_windows = {days: 0 for days in (30, 60, 90, 180, 365)}

    metrics: Counter[str] = Counter()
    normalized_rows: list[dict[str, object]] = []

    for source_row_number, row in enumerate(rows, start=2):
        if source_row_number in completely_blank_rows:
            continue

        raw_license = clean_text(row.get("LICENSE NO."))
        license_number, license_flags = normalize_license_number(raw_license)
        if raw_license:
            metrics["rows_with_license_number"] += 1
        if license_number:
            license_numbers.append(license_number)
        if len(license_samples) < 5:
            license_samples.append(
                {
                    "source_row_number": source_row_number,
                    "raw": raw_license,
                    "normalized": license_number,
                }
            )
        if license_flags and len(license_examples) < 10:
            license_examples.append(
                {
                    "source_row_number": source_row_number,
                    "raw": raw_license,
                    "normalized": license_number,
                    "flags": license_flags,
                }
            )
        if "unexpected_license_number_format" in license_flags:
            metrics["malformed_license_numbers"] += 1
            if len(malformed_licenses) < 10:
                malformed_licenses.append(license_examples[-1])

        names = normalize_name_fields(row)
        if not names["first_name"] or not names["last_name"]:
            metrics["rows_missing_names"] += 1
        if names["normalized_match_name"]:
            name_keys.append(names["normalized_match_name"])
        if len(name_examples) < 5:
            name_examples.append(names)

        address_line_1 = clean_text(row.get("ADDRESS1"))
        address_line_2 = clean_text(row.get("ADDRESS2"))
        city = clean_text(row.get("CITY"))
        state = clean_text(row.get("STATE")).upper()
        zip_raw = clean_text(row.get("ZIP"))
        zip_normalized, zip_corrected, zip_flags = normalize_zip(zip_raw)

        if not state:
            metrics["rows_missing_mailing_state"] += 1
        else:
            state_counts[state] += 1
            if state == "CT":
                metrics["ct_mailing_address_count"] += 1
            else:
                metrics["non_ct_mailing_address_count"] += 1
        if not address_line_1 and not address_line_2:
            metrics["rows_missing_address"] += 1
        if not city:
            metrics["rows_missing_city"] += 1
        if not zip_raw:
            metrics["rows_missing_zip"] += 1
        if "O" in zip_raw.upper():
            metrics["zip_values_containing_o"] += 1
            if state == "CT":
                metrics["ct_zip_values_containing_o"] += 1
        if zip_corrected:
            metrics["zip_correction_count"] += 1
            if state == "CT":
                metrics["ct_zip_correction_count"] += 1
            if len(zip_o_examples) < 10:
                zip_o_examples.append(
                    {
                        "source_row_number": source_row_number,
                        "state": state,
                        "raw": zip_raw,
                        "normalized": zip_normalized,
                    }
                )
        if "unexpected_zip_format" in zip_flags:
            metrics["unexpected_zip_formats"] += 1
            if len(unexpected_zip_examples) < 10:
                unexpected_zip_examples.append(
                    {
                        "source_row_number": source_row_number,
                        "state": state,
                        "raw": zip_raw,
                        "normalized": zip_normalized,
                    }
                )
        if state == "CT" and VALID_US_ZIP_RE.fullmatch(zip_normalized):
            metrics["ct_zip_values_with_valid_format"] += 1
            if zip_normalized.startswith("06"):
                metrics["ct_zip_values_with_06_prefix"] += 1

        status = clean_text(row.get("STATUS"))
        reason = clean_text(row.get("REASON"))
        status_counts[status or "(blank)"] += 1
        reason_counts[reason or "(blank)"] += 1
        status_reason_counts[(status or "(blank)", reason or "(blank)")] += 1

        issue_raw = clean_text(row.get("ISSUE DATE"))
        expiration_raw = clean_text(row.get("EXPIRATION DATE"))
        issue_date, issue_error = parse_source_date(issue_raw)
        expiration_date, expiration_error = parse_source_date(expiration_raw)

        if not issue_raw:
            metrics["rows_missing_original_issue_date"] += 1
        elif issue_error:
            metrics["invalid_original_issue_dates"] += 1
            if len(invalid_date_examples) < 10:
                invalid_date_examples.append(
                    {
                        "source_row_number": source_row_number,
                        "field": "ISSUE DATE",
                        "value": issue_raw,
                    }
                )
        elif issue_date:
            issue_dates.append(issue_date)
            if issue_date == LEGACY_ISSUE_DATE:
                metrics["legacy_issue_date_count"] += 1

        if not expiration_raw:
            metrics["rows_missing_expiration_date"] += 1
        elif expiration_error:
            metrics["invalid_expiration_dates"] += 1
            if len(invalid_date_examples) < 10:
                invalid_date_examples.append(
                    {
                        "source_row_number": source_row_number,
                        "field": "EXPIRATION DATE",
                        "value": expiration_raw,
                    }
                )
        elif expiration_date:
            expiration_dates.append(expiration_date)
            if expiration_date < ROSTER_DATE:
                metrics["expired_as_of_roster_date"] += 1
            else:
                for days in expiration_windows:
                    if expiration_date <= ROSTER_DATE + timedelta(days=days):
                        expiration_windows[days] += 1

        if issue_date and expiration_date and expiration_date < issue_date:
            metrics["expiration_before_issue_date"] += 1

        normalized_rows.append(
            {
                "source_row_number": source_row_number,
                "license_number_raw": raw_license,
                "license_number": license_number,
                **names,
                "address_line_1": address_line_1,
                "address_line_2": address_line_2,
                "city": city,
                "state": state,
                "zip_code_raw": zip_raw,
                "zip_code_normalized": zip_normalized,
                "zip_code_corrected": zip_corrected,
                "country": "",
                "license_status": status,
                "status_reason": reason,
                "original_issue_date": issue_date.isoformat() if issue_date else "",
                "expiration_date": expiration_date.isoformat() if expiration_date else "",
                "possible_legacy_issue_date": issue_date == LEGACY_ISSUE_DATE,
                "expired_as_of_roster_date": bool(
                    expiration_date and expiration_date < ROSTER_DATE
                ),
                "expires_within_90_days_of_roster_date": bool(
                    expiration_date
                    and ROSTER_DATE <= expiration_date <= ROSTER_DATE + timedelta(days=90)
                ),
                "validation_flags": license_flags + zip_flags,
            }
        )

    duplicate_license_row_count, duplicate_license_values = count_duplicate_values(
        license_numbers
    )
    duplicate_name_row_count, duplicate_name_values = count_duplicate_values(name_keys)
    duplicate_name_details: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in normalized_rows:
        match_name = str(row["normalized_match_name"])
        if match_name in duplicate_name_values:
            duplicate_name_details[match_name].append(
                {
                    "source_row_number": row["source_row_number"],
                    "license_number": row["license_number"],
                    "display_name": row["display_name"],
                    "state": row["state"],
                }
            )

    normalized_column_names = {clean_text(column).casefold() for column in columns}
    affiliation_columns_present = sorted(
        term for term in FACILITY_AFFILIATION_COLUMN_TERMS if term in normalized_column_names
    )

    results: dict[str, object] = {
        "source_path": str(source_path),
        "source_file_size_bytes": source_path.stat().st_size,
        "has_utf8_bom": source_path.read_bytes().startswith(b"\xef\xbb\xbf"),
        "roster_date": ROSTER_DATE.isoformat(),
        "columns": columns,
        "unexpected_columns": unexpected_columns,
        "unnamed_columns": [
            column for column in columns if not clean_text(column) or column.startswith("Unnamed:")
        ],
        "total_source_rows": len(rows),
        "normalized_record_count": len(normalized_rows),
        "completely_blank_row_count": len(completely_blank_rows),
        "completely_blank_row_numbers": completely_blank_rows,
        "entirely_blank_columns": entirely_blank_columns,
        "column_blank_counts": column_blank_counts,
        "affiliation_columns_present": affiliation_columns_present,
        "unique_license_count": len(set(license_numbers)),
        "duplicate_license_row_count": duplicate_license_row_count,
        "duplicate_license_value_count": len(duplicate_license_values),
        "duplicate_license_values": duplicate_license_values,
        "duplicate_name_row_count": duplicate_name_row_count,
        "duplicate_name_value_count": len(duplicate_name_values),
        "duplicate_name_values": duplicate_name_values,
        "duplicate_name_details": dict(duplicate_name_details),
        "license_length_counts": dict(
            sorted(Counter(len(value) for value in license_numbers).items())
        ),
        "status_counts": dict(sorted(status_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "status_reason_counts": {
            f"{status} | {reason}": count
            for (status, reason), count in sorted(status_reason_counts.items())
        },
        "state_counts": dict(sorted(state_counts.items())),
        "minimum_original_issue_date": min(issue_dates).isoformat() if issue_dates else None,
        "maximum_original_issue_date": max(issue_dates).isoformat() if issue_dates else None,
        "minimum_expiration_date": min(expiration_dates).isoformat()
        if expiration_dates
        else None,
        "maximum_expiration_date": max(expiration_dates).isoformat()
        if expiration_dates
        else None,
        "expiration_windows": expiration_windows,
        "metrics": dict(metrics),
        "examples": {
            "license_samples": license_samples,
            "license_normalizations": license_examples,
            "malformed_license_numbers": malformed_licenses,
            "normalized_names": name_examples,
            "zip_o_corrections": zip_o_examples,
            "unexpected_zip_formats": unexpected_zip_examples,
            "invalid_dates": invalid_date_examples,
        },
    }
    return results


def metric(results: dict[str, object], name: str) -> int:
    metrics = results["metrics"]
    assert isinstance(metrics, dict)
    return int(metrics.get(name, 0))


def print_mapping(title: str, mapping: dict[str, object]) -> None:
    print(title)
    for key, value in mapping.items():
        print(f"  {key}: {value}")


def print_summary(results: dict[str, object], verbose: bool = False) -> None:
    print("Connecticut Nursing Home Administrator roster validation")
    print(f"Source: {results['source_path']}")
    print(f"Source file size: {results['source_file_size_bytes']:,} bytes")
    print(f"UTF-8 BOM present: {results['has_utf8_bom']}")
    print(f"Roster reference date: {results['roster_date']}")
    print(f"Columns ({len(results['columns'])}): {', '.join(results['columns'])}")
    print(f"Unexpected columns: {results['unexpected_columns'] or 'none'}")
    print(f"Unnamed columns: {results['unnamed_columns'] or 'none'}")
    print(f"Entirely blank columns: {results['entirely_blank_columns'] or 'none'}")
    print(f"Facility-affiliation columns present: {results['affiliation_columns_present'] or 'none'}")
    print()

    print("Records and identifiers")
    print(f"  Total source rows: {results['total_source_rows']}")
    print(f"  Completely blank rows: {results['completely_blank_row_count']}")
    print(f"  Normalized validation records: {results['normalized_record_count']}")
    print(f"  Rows with license number: {metric(results, 'rows_with_license_number')}")
    print(f"  Unique normalized license numbers: {results['unique_license_count']}")
    print(f"  Duplicate normalized license values: {results['duplicate_license_value_count']}")
    print(f"  Excess rows from duplicate license values: {results['duplicate_license_row_count']}")
    print(f"  Malformed license numbers: {metric(results, 'malformed_license_numbers')}")
    print(f"  Normalized license length counts: {results['license_length_counts']}")
    print(f"  Rows missing first or last name: {metric(results, 'rows_missing_names')}")
    print(f"  Duplicate normalized name values: {results['duplicate_name_value_count']}")
    print(f"  Excess rows from duplicate normalized names: {results['duplicate_name_row_count']}")
    print()

    print("Addresses and ZIP codes")
    print(f"  Connecticut mailing states: {metric(results, 'ct_mailing_address_count')}")
    print(f"  Non-Connecticut mailing states: {metric(results, 'non_ct_mailing_address_count')}")
    print(f"  Missing mailing states: {metric(results, 'rows_missing_mailing_state')}")
    print(f"  Missing street addresses: {metric(results, 'rows_missing_address')}")
    print(f"  Missing cities: {metric(results, 'rows_missing_city')}")
    print(f"  Missing ZIP codes: {metric(results, 'rows_missing_zip')}")
    print(f"  ZIP values containing O: {metric(results, 'zip_values_containing_o')}")
    print(f"  Safely corrected ZIP values: {metric(results, 'zip_correction_count')}")
    print(f"  Unexpected ZIP formats after safe correction: {metric(results, 'unexpected_zip_formats')}")
    print(f"  CT ZIP values containing O: {metric(results, 'ct_zip_values_containing_o')}")
    print(f"  CT ZIP values with valid normalized format: {metric(results, 'ct_zip_values_with_valid_format')}")
    print(f"  CT ZIP values with normalized 06 prefix: {metric(results, 'ct_zip_values_with_06_prefix')}")
    print_mapping("  State counts:", results["state_counts"])
    print()

    print_mapping("License status counts:", results["status_counts"])
    print_mapping("Status reason counts:", results["reason_counts"])
    print_mapping("Status and reason combinations:", results["status_reason_counts"])
    print()

    print("Dates")
    print(f"  Original issue date range: {results['minimum_original_issue_date']} to {results['maximum_original_issue_date']}")
    print(f"  Expiration date range: {results['minimum_expiration_date']} to {results['maximum_expiration_date']}")
    print(f"  Missing original issue dates: {metric(results, 'rows_missing_original_issue_date')}")
    print(f"  Invalid original issue dates: {metric(results, 'invalid_original_issue_dates')}")
    print(f"  Missing expiration dates: {metric(results, 'rows_missing_expiration_date')}")
    print(f"  Invalid expiration dates: {metric(results, 'invalid_expiration_dates')}")
    print(f"  Expiration dates before issue dates: {metric(results, 'expiration_before_issue_date')}")
    print(f"  Records expired as of roster date: {metric(results, 'expired_as_of_roster_date')}")
    print(f"  Possible legacy issue date (1901-01-01): {metric(results, 'legacy_issue_date_count')}")
    print_mapping("  Future expiration windows:", results["expiration_windows"])

    if verbose:
        print()
        print("Verbose diagnostics")
        examples = results["examples"]
        for category, values in examples.items():
            print(f"  {category}: {values or 'none'}")
        print(f"  Duplicate license values: {results['duplicate_license_values'] or 'none'}")
        print(f"  Duplicate normalized name values: {results['duplicate_name_values'] or 'none'}")
        print(f"  Duplicate normalized name details: {results['duplicate_name_details'] or 'none'}")
        print(f"  Completely blank row numbers: {results['completely_blank_row_numbers'] or 'none'}")
        print(f"  Blank values by source column: {results['column_blank_counts']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Source CSV path (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print normalization examples and duplicate-value diagnostics.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        results = analyze(args.source.resolve())
    except (FileNotFoundError, OSError, csv.Error, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print_summary(results, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
