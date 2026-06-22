"""Validate the CMS nursing home Fire Safety Deficiencies source file.

This script reads ignored raw CMS source files from source_data/cms_survey and
prints validation results only. It does not write runtime JSON or alter app data.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path


SOURCE_DIR = Path("source_data/cms_survey")
STAFFING_PATH = Path("data/nursing_home_staffing_ct.json")
CITATION_LOOKUP_PATTERN = "NH_CitationDescriptions_*.csv"
FIRE_PATTERN = "NH_FireSafetyCitations_*.csv"

REQUIRED_COLUMNS = [
    "CMS Certification Number (CCN)",
    "Provider Name",
    "State",
    "Survey Date",
    "Survey Type",
    "Deficiency Prefix",
    "Deficiency Category",
    "Deficiency Tag Number",
    "Tag Version",
    "Deficiency Description",
    "Scope Severity Code",
    "Deficiency Corrected",
    "Correction Date",
    "Inspection Cycle",
    "Standard Deficiency",
    "Complaint Deficiency",
    "Infection Control Inspection Deficiency",
    "Citation under IDR",
    "Citation under IIDR",
    "Processing Date",
]


def find_latest(pattern: str) -> Path:
    matches = sorted(SOURCE_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No {pattern} file found in {SOURCE_DIR.as_posix()}")
    if len(matches) > 1:
        print(f"Multiple files match {pattern}; validating latest by filename:")
        for path in matches:
            print(f"  - {path.as_posix()}")
    return matches[-1]


def normalize_ccn(value: str) -> str:
    digits = "".join(ch for ch in str(value or "").strip() if ch.isdigit())
    return digits.zfill(6) if digits else ""


def parse_date(value: str) -> date | None:
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def citation_code(prefix: str, tag_number: str) -> str:
    prefix = str(prefix or "").strip().upper()
    tag = str(tag_number or "").strip()
    if not prefix or not tag:
        return ""
    tag_digits = "".join(ch for ch in tag if ch.isdigit())
    return f"{prefix}-{tag_digits.zfill(4)}" if tag_digits else ""


def load_current_staffing_ccns() -> dict[str, str]:
    with STAFFING_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        normalize_ccn(row.get("ccn")): row.get("provider_name") or row.get("facility_name") or ""
        for row in data.get("facilities", [])
        if normalize_ccn(row.get("ccn"))
    }


def load_citation_lookup_codes() -> set[str]:
    matches = sorted(SOURCE_DIR.glob(CITATION_LOOKUP_PATTERN))
    if not matches:
        return set()
    lookup_path = matches[-1]
    with lookup_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return {
            str(row.get("Deficiency Prefix and Number", "")).strip().upper()
            for row in reader
            if str(row.get("Deficiency Prefix and Number", "")).strip()
        }


def main() -> None:
    source_path = find_latest(FIRE_PATTERN)
    source_size = source_path.stat().st_size
    staffing_ccns = load_current_staffing_ccns()
    citation_lookup_codes = load_citation_lookup_codes()

    all_rows = 0
    ct_rows = 0
    ct_ccns: dict[str, str] = {}
    missing_required_values = Counter()
    malformed_tag_count = 0
    citation_lookup_miss_count = 0
    citation_lookup_misses = Counter()
    missing_survey_dates = 0
    invalid_survey_dates = 0
    min_survey_date: date | None = None
    max_survey_date: date | None = None
    survey_year_counts = Counter()
    prefix_counts = Counter()
    tag_counts = Counter()
    tag_version_counts = Counter()
    scope_counts = Counter()
    survey_type_counts = Counter()
    standard_counts = Counter()
    complaint_counts = Counter()
    infection_control_counts = Counter()
    corrected_counts = Counter()
    missing_correction_dates = 0
    deficiency_description_lengths: list[int] = []

    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            raise SystemExit(f"Missing required columns: {', '.join(missing_columns)}")

        for row in reader:
            all_rows += 1
            if str(row.get("State", "")).strip().upper() != "CT":
                continue

            ct_rows += 1
            ccn = normalize_ccn(row.get("CMS Certification Number (CCN)"))
            provider_name = str(row.get("Provider Name", "")).strip()
            if ccn:
                ct_ccns.setdefault(ccn, provider_name)

            for column in REQUIRED_COLUMNS:
                if column == "Correction Date":
                    continue
                if not str(row.get(column, "")).strip():
                    missing_required_values[column] += 1

            survey_date_raw = row.get("Survey Date", "")
            if not str(survey_date_raw or "").strip():
                missing_survey_dates += 1
            else:
                parsed = parse_date(survey_date_raw)
                if parsed is None:
                    invalid_survey_dates += 1
                else:
                    min_survey_date = parsed if min_survey_date is None else min(min_survey_date, parsed)
                    max_survey_date = parsed if max_survey_date is None else max(max_survey_date, parsed)
                    survey_year_counts[parsed.year] += 1

            prefix = str(row.get("Deficiency Prefix", "")).strip().upper()
            tag_number = str(row.get("Deficiency Tag Number", "")).strip()
            code = citation_code(prefix, tag_number)
            prefix_counts[prefix or "(blank)"] += 1
            if code:
                tag_counts[code] += 1
                if citation_lookup_codes and code not in citation_lookup_codes:
                    citation_lookup_miss_count += 1
                    citation_lookup_misses[code] += 1
            else:
                malformed_tag_count += 1

            tag_version_counts[str(row.get("Tag Version", "")).strip() or "(blank)"] += 1
            scope = str(row.get("Scope Severity Code", "")).strip().upper()
            scope_counts[scope or "(blank)"] += 1
            survey_type_counts[str(row.get("Survey Type", "")).strip() or "(blank)"] += 1
            standard_counts[str(row.get("Standard Deficiency", "")).strip() or "(blank)"] += 1
            complaint_counts[str(row.get("Complaint Deficiency", "")).strip() or "(blank)"] += 1
            infection_control_counts[
                str(row.get("Infection Control Inspection Deficiency", "")).strip() or "(blank)"
            ] += 1
            corrected_counts[str(row.get("Deficiency Corrected", "")).strip() or "(blank)"] += 1
            if not str(row.get("Correction Date", "")).strip():
                missing_correction_dates += 1
            deficiency_description_lengths.append(
                len(str(row.get("Deficiency Description", "")).strip())
            )

    joined_ccns = sorted(set(ct_ccns).intersection(staffing_ccns))
    unmatched_ccns = sorted(set(ct_ccns).difference(staffing_ccns))

    print(f"Source file: {source_path.as_posix()}")
    print(f"Source file size bytes: {source_size}")
    print(f"Columns ({len(fieldnames)}): {', '.join(fieldnames)}")
    print(f"All source rows: {all_rows}")
    print(f"Connecticut rows: {ct_rows}")
    print(f"Unique CT CCNs: {len(ct_ccns)}")
    print(f"Current staffing CCNs: {len(staffing_ccns)}")
    print(f"Joined CT fire safety deficiency CCNs to current staffing: {len(joined_ccns)}")
    print(f"Unmatched CT fire safety deficiency CCNs: {len(unmatched_ccns)}")
    print("Sample unmatched CT CCNs:")
    for ccn in unmatched_ccns[:15]:
        print(f"  {ccn}: {ct_ccns.get(ccn, '')}")
    print(f"Missing survey dates: {missing_survey_dates}")
    print(f"Invalid survey dates: {invalid_survey_dates}")
    print(f"Survey date min: {min_survey_date.isoformat() if min_survey_date else ''}")
    print(f"Survey date max: {max_survey_date.isoformat() if max_survey_date else ''}")
    print("Survey year counts:")
    for year, count in sorted(survey_year_counts.items()):
        print(f"  {year}: {count}")
    print(f"Distinct citation codes: {len(tag_counts)}")
    print(f"Malformed citation codes: {malformed_tag_count}")
    print(f"Citation lookup misses: {citation_lookup_miss_count}")
    if citation_lookup_misses:
        print("Citation lookup miss samples:")
        for code, count in citation_lookup_misses.most_common(15):
            print(f"  {code}: {count}")
    print("Prefix counts:")
    for prefix, count in sorted(prefix_counts.items()):
        print(f"  {prefix}: {count}")
    print("Tag version counts:")
    for version, count in sorted(tag_version_counts.items()):
        print(f"  {version}: {count}")
    print("Scope/severity counts:")
    for scope, count in sorted(scope_counts.items()):
        print(f"  {scope}: {count}")
    print("Survey type counts:")
    for value, count in sorted(survey_type_counts.items()):
        print(f"  {value}: {count}")
    print("Standard deficiency indicator counts:")
    for value, count in sorted(standard_counts.items()):
        print(f"  {value}: {count}")
    print("Complaint deficiency indicator counts:")
    for value, count in sorted(complaint_counts.items()):
        print(f"  {value}: {count}")
    print("Infection control inspection deficiency indicator counts:")
    for value, count in sorted(infection_control_counts.items()):
        print(f"  {value}: {count}")
    print("Deficiency corrected counts:")
    for value, count in sorted(corrected_counts.items()):
        print(f"  {value}: {count}")
    print(f"Missing correction dates: {missing_correction_dates}")
    if deficiency_description_lengths:
        print(f"Description length min: {min(deficiency_description_lengths)}")
        print(f"Description length max: {max(deficiency_description_lengths)}")
    print("Missing required values among CT rows:")
    for column in REQUIRED_COLUMNS:
        print(f"  {column}: {missing_required_values[column]}")

    if invalid_survey_dates or malformed_tag_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
