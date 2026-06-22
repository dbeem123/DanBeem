"""Build or dry-run a Connecticut Health Deficiencies preview.

Default behavior is validation-only: read CMS source files, validate joins and
derived fields, and print a summary. Use --write-testing-preview to write an
ignored preview under data/testing/. This script never writes the public runtime
file data/nursing_home_health_deficiencies_ct.json.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any


SOURCE_DIR = Path("source_data/cms_survey")
STAFFING_PATH = Path("data/nursing_home_staffing_ct.json")
TESTING_OUTPUT_PATH = Path("data/testing/nursing_home_health_deficiencies_ct_preview.json")
RUNTIME_OUTPUT_PATH = Path("data/nursing_home_health_deficiencies_ct.json")

HEALTH_PATTERN = "NH_HealthCitations_*.csv"
CITATION_LOOKUP_PATTERN = "NH_CitationDescriptions_*.csv"

SOURCE_URL = (
    "https://data.cms.gov/provider-data/sites/default/files/resources/"
    "e269c04e82fe86040cd70b7ba3dd4853_1778861752/"
    "NH_HealthCitations_May2026.csv"
)
CMS_DATASET_ID = "r5ix-sfxw"
SOURCE_NAME = "CMS Provider Data Catalog Health Deficiencies"
ACQUIRED_DATE = "2026-06-22"

REQUIRED_COLUMNS = [
    "CMS Certification Number (CCN)",
    "Provider Name",
    "State",
    "Survey Date",
    "Survey Type",
    "Deficiency Prefix",
    "Deficiency Category",
    "Deficiency Tag Number",
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
    return matches[-1]


def normalize_ccn(value: str) -> str:
    digits = "".join(ch for ch in str(value or "").strip() if ch.isdigit())
    return digits.zfill(6) if digits else ""


def parse_date(value: str, *, required: bool = False, field_name: str = "date") -> str | None:
    value = str(value or "").strip()
    if not value:
        if required:
            raise ValueError(f"Missing required {field_name}")
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Invalid {field_name}: {value}")


def citation_code(prefix: str, tag_number: str) -> str:
    prefix = str(prefix or "").strip().upper()
    tag_digits = "".join(ch for ch in str(tag_number or "").strip() if ch.isdigit())
    if not prefix or not tag_digits:
        return ""
    return f"{prefix}-{tag_digits.zfill(4)}"


def yn_to_bool(value: str, field_name: str) -> bool:
    normalized = str(value or "").strip().upper()
    if normalized == "Y":
        return True
    if normalized == "N":
        return False
    raise ValueError(f"Unexpected {field_name} value: {value!r}")


def harm_ij_group(scope_severity: str) -> str:
    code = str(scope_severity or "").strip().upper()
    if code in {"J", "K", "L"}:
        return "immediate_jeopardy"
    if code in {"G", "H", "I"}:
        return "actual_harm_not_ij"
    if code in {"D", "E", "F"}:
        return "no_actual_harm_more_than_minimal"
    if code in {"A", "B", "C"}:
        return "no_actual_harm_minimal"
    return "unknown_or_unmapped"


def parse_source_month_year(source_path: Path) -> tuple[str, int]:
    stem = source_path.stem
    suffix = stem.rsplit("_", 1)[-1]
    month = "".join(ch for ch in suffix if ch.isalpha())
    year_text = "".join(ch for ch in suffix if ch.isdigit())
    if not month or not year_text:
        raise ValueError(f"Could not parse source month/year from {source_path.name}")
    return month, int(year_text)


def load_current_staffing_ccns() -> dict[str, str]:
    with STAFFING_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        normalize_ccn(row.get("ccn")): row.get("provider_name") or ""
        for row in data.get("facilities", [])
        if normalize_ccn(row.get("ccn"))
    }


def load_citation_lookup() -> tuple[Path | None, dict[str, dict[str, str]]]:
    matches = sorted(SOURCE_DIR.glob(CITATION_LOOKUP_PATTERN))
    if not matches:
        return None, {}
    lookup_path = matches[-1]
    lookup: dict[str, dict[str, str]] = {}
    with lookup_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code = str(row.get("Deficiency Prefix and Number", "")).strip().upper()
            if not code:
                continue
            lookup[code] = {
                "description": str(row.get("Deficiency Description", "")).strip(),
                "category": str(row.get("Deficiency Category", "")).strip(),
            }
    return lookup_path, lookup


def source_row_hash(row: dict[str, str]) -> str:
    payload = "\x1f".join(str(row.get(column, "")).strip() for column in sorted(row))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_deficiency_record(
    row: dict[str, str],
    citation_lookup: dict[str, dict[str, str]],
) -> dict[str, Any]:
    ccn = normalize_ccn(row.get("CMS Certification Number (CCN)", ""))
    provider_name = str(row.get("Provider Name", "")).strip()
    state = str(row.get("State", "")).strip().upper()
    survey_date = parse_date(row.get("Survey Date", ""), required=True, field_name="Survey Date")
    correction_date = parse_date(row.get("Correction Date", ""), field_name="Correction Date")
    processing_date = parse_date(row.get("Processing Date", ""), required=True, field_name="Processing Date")
    prefix = str(row.get("Deficiency Prefix", "")).strip().upper()
    tag_number = "".join(
        ch for ch in str(row.get("Deficiency Tag Number", "")).strip() if ch.isdigit()
    ).zfill(4)
    code = citation_code(prefix, tag_number)
    scope_severity = str(row.get("Scope Severity Code", "")).strip().upper()

    if not ccn:
        raise ValueError("Missing required CCN")
    if not provider_name:
        raise ValueError(f"Missing Provider Name for {ccn}")
    if state != "CT":
        raise ValueError(f"Unexpected state in CT build: {state}")
    if prefix != "F":
        raise ValueError(f"Unexpected Health Deficiencies prefix for {ccn}: {prefix}")
    if not code:
        raise ValueError(f"Malformed deficiency code for {ccn}")
    if not scope_severity:
        raise ValueError(f"Missing Scope Severity Code for {ccn} {code}")

    lookup = citation_lookup.get(code)
    source_description = str(row.get("Deficiency Description", "")).strip()
    source_category = str(row.get("Deficiency Category", "")).strip()
    if not source_description:
        raise ValueError(f"Missing Deficiency Description for {ccn} {code}")
    if not source_category:
        raise ValueError(f"Missing Deficiency Category for {ccn} {code}")

    return {
        "ccn": ccn,
        "provider_name": provider_name,
        "state": state,
        "survey_date": survey_date,
        "survey_year": int(survey_date[:4]),
        "survey_type": str(row.get("Survey Type", "")).strip(),
        "deficiency_prefix": prefix,
        "deficiency_tag_number": tag_number,
        "deficiency_code": code,
        "deficiency_description": source_description,
        "deficiency_category": source_category,
        "scope_severity_code": scope_severity,
        "harm_ij_group": harm_ij_group(scope_severity),
        "standard_deficiency": yn_to_bool(row.get("Standard Deficiency", ""), "Standard Deficiency"),
        "complaint_deficiency": yn_to_bool(row.get("Complaint Deficiency", ""), "Complaint Deficiency"),
        "infection_control_inspection_deficiency": yn_to_bool(
            row.get("Infection Control Inspection Deficiency", ""),
            "Infection Control Inspection Deficiency",
        ),
        "correction_date": correction_date,
        "citation_under_idr": yn_to_bool(row.get("Citation under IDR", ""), "Citation under IDR"),
        "citation_under_iidr": yn_to_bool(row.get("Citation under IIDR", ""), "Citation under IIDR"),
        "processing_date": processing_date,
        "source_row_hash": source_row_hash(row),
        "citation_description_lookup_matched": lookup is not None,
        "citation_description_category": lookup["category"] if lookup else None,
        "citation_description_text": lookup["description"] if lookup else None,
    }


def build_preview() -> tuple[dict[str, Any], dict[str, Any]]:
    health_path = find_latest(HEALTH_PATTERN)
    lookup_path, citation_lookup = load_citation_lookup()
    staffing_ccns = load_current_staffing_ccns()
    source_month, source_year = parse_source_month_year(health_path)

    source_row_count = 0
    deficiencies: list[dict[str, Any]] = []
    ct_ccns: set[str] = set()
    source_hashes: set[str] = set()
    lookup_miss_count = 0
    survey_dates: list[str] = []
    f_tag_count = 0

    with health_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        for row in reader:
            source_row_count += 1
            if str(row.get("State", "")).strip().upper() != "CT":
                continue
            record = build_deficiency_record(row, citation_lookup)
            if record["source_row_hash"] in source_hashes:
                raise ValueError(f"Duplicate source row hash: {record['source_row_hash']}")
            source_hashes.add(record["source_row_hash"])
            deficiencies.append(record)
            ct_ccns.add(record["ccn"])
            survey_dates.append(record["survey_date"])
            if record["deficiency_prefix"] == "F":
                f_tag_count += 1
            if not record["citation_description_lookup_matched"]:
                lookup_miss_count += 1

    joined_current_ccns = set(ct_ccns).intersection(staffing_ccns)
    unmatched_current_ccns = set(ct_ccns).difference(staffing_ccns)
    group_counts = Counter(record["harm_ij_group"] for record in deficiencies)
    scope_counts = Counter(record["scope_severity_code"] for record in deficiencies)
    tag_counts = Counter(record["deficiency_code"] for record in deficiencies)
    survey_year_counts = Counter(record["survey_year"] for record in deficiencies)

    metadata = {
        "source_name": SOURCE_NAME,
        "source_file": health_path.name,
        "source_url_or_endpoint": SOURCE_URL,
        "cms_dataset_id": CMS_DATASET_ID,
        "source_month": source_month,
        "source_year": source_year,
        "acquired_date": ACQUIRED_DATE,
        "build_date": date.today().isoformat(),
        "state_filter": "CT",
        "source_row_count": source_row_count,
        "ct_row_count": len(deficiencies),
        "unique_ct_ccn_count": len(ct_ccns),
        "joined_current_ccn_count": len(joined_current_ccns),
        "unmatched_current_ccn_count": len(unmatched_current_ccns),
        "survey_date_min": min(survey_dates) if survey_dates else None,
        "survey_date_max": max(survey_dates) if survey_dates else None,
        "f_tag_count": f_tag_count,
        "citation_description_lookup_miss_count": lookup_miss_count,
        "citation_descriptions_source_file": lookup_path.name if lookup_path else None,
        "limitations": [
            "Health deficiencies are citation-level records.",
            "One facility may have many citation rows.",
            "Survey date and processing date are not the same.",
            "Citation descriptions are lookup/reference text, not proof of a facility finding by themselves.",
            "Scope/severity grouping is a derived screening classification, not a legal conclusion.",
            "This testing preview is non-runtime and should not be committed.",
        ],
    }

    summary = {
        "source_file": health_path.as_posix(),
        "source_file_size_bytes": health_path.stat().st_size,
        "citation_lookup_file": lookup_path.as_posix() if lookup_path else "",
        "source_row_count": source_row_count,
        "ct_row_count": len(deficiencies),
        "unique_ct_ccn_count": len(ct_ccns),
        "joined_current_ccn_count": len(joined_current_ccns),
        "unmatched_current_ccn_count": len(unmatched_current_ccns),
        "survey_date_min": metadata["survey_date_min"],
        "survey_date_max": metadata["survey_date_max"],
        "f_tag_count": f_tag_count,
        "distinct_f_tag_count": len(tag_counts),
        "citation_description_lookup_miss_count": lookup_miss_count,
        "harm_ij_group_counts": dict(sorted(group_counts.items())),
        "scope_severity_counts": dict(sorted(scope_counts.items())),
        "survey_year_counts": dict(sorted(survey_year_counts.items())),
    }

    return {"metadata": metadata, "deficiencies": deficiencies}, summary


def print_summary(summary: dict[str, Any], *, wrote_preview: bool) -> None:
    print(f"Source file: {summary['source_file']}")
    print(f"Source file size bytes: {summary['source_file_size_bytes']}")
    print(f"Citation lookup file: {summary['citation_lookup_file']}")
    print(f"Source rows: {summary['source_row_count']}")
    print(f"Connecticut rows: {summary['ct_row_count']}")
    print(f"Unique CT CCNs: {summary['unique_ct_ccn_count']}")
    print(f"Joined current CCNs: {summary['joined_current_ccn_count']}")
    print(f"Unmatched current CCNs: {summary['unmatched_current_ccn_count']}")
    print(f"Survey date min: {summary['survey_date_min']}")
    print(f"Survey date max: {summary['survey_date_max']}")
    print(f"F-tag row count: {summary['f_tag_count']}")
    print(f"Distinct F-tags: {summary['distinct_f_tag_count']}")
    print(f"Citation description lookup misses: {summary['citation_description_lookup_miss_count']}")
    print("Harm/IJ group counts:")
    for key, value in summary["harm_ij_group_counts"].items():
        print(f"  {key}: {value}")
    print("Scope/severity counts:")
    for key, value in summary["scope_severity_counts"].items():
        print(f"  {key}: {value}")
    print("Survey year counts:")
    for key, value in summary["survey_year_counts"].items():
        print(f"  {key}: {value}")
    if wrote_preview:
        print(f"Testing preview written: {TESTING_OUTPUT_PATH.as_posix()}")
    else:
        print("Dry run only: no output written.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dry-run/build a Connecticut Health Deficiencies testing preview."
    )
    parser.add_argument(
        "--write-testing-preview",
        action="store_true",
        help="Write data/testing/nursing_home_health_deficiencies_ct_preview.json",
    )
    args = parser.parse_args()

    if RUNTIME_OUTPUT_PATH.exists():
        raise SystemExit(
            f"Refusing to continue because runtime output exists: {RUNTIME_OUTPUT_PATH.as_posix()}"
        )

    preview, summary = build_preview()
    if args.write_testing_preview:
        TESTING_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TESTING_OUTPUT_PATH.open("w", encoding="utf-8") as handle:
            json.dump(preview, handle, indent=2)
            handle.write("\n")
        print_summary(summary, wrote_preview=True)
    else:
        print_summary(summary, wrote_preview=False)


if __name__ == "__main__":
    main()
