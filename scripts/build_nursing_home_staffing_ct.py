#!/usr/bin/env python3
"""Build Connecticut Nursing Home Staffing Explorer JSON from local CMS PBJ CSVs.

This is an offline preprocessing utility. It reads manually downloaded CMS
Payroll Based Journal Daily Nurse Staffing CSV files and emits a small static
JSON file for the browser to consume.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


RN_HOUR_COLUMNS = ["Hrs_RNDON", "Hrs_RNadmin", "Hrs_RN"]
LPN_HOUR_COLUMNS = ["Hrs_LPNadmin", "Hrs_LPN"]
NURSE_AIDE_HOUR_COLUMNS = ["Hrs_CNA", "Hrs_NAtrn", "Hrs_MedAide"]
NURSE_HOUR_COLUMNS = RN_HOUR_COLUMNS + LPN_HOUR_COLUMNS + NURSE_AIDE_HOUR_COLUMNS
CONTRACT_HOUR_COLUMNS = [f"{column}_ctr" for column in NURSE_HOUR_COLUMNS]
CT_DIRECT_CARE_RN_COLUMNS = ["Hrs_RN"]
CT_DIRECT_CARE_LPN_COLUMNS = ["Hrs_LPN"]
CT_DIRECT_CARE_AIDE_COLUMNS = NURSE_AIDE_HOUR_COLUMNS
CT_DIRECT_CARE_TOTAL_HOUR_COLUMNS = CT_DIRECT_CARE_RN_COLUMNS + CT_DIRECT_CARE_LPN_COLUMNS + CT_DIRECT_CARE_AIDE_COLUMNS
CT_DIRECT_CARE_LICENSED_NURSE_HOUR_COLUMNS = CT_DIRECT_CARE_RN_COLUMNS + CT_DIRECT_CARE_LPN_COLUMNS
CT_TOTAL_DIRECT_CARE_MINIMUM_HPRD = 3.00
CT_LICENSED_DIRECT_CARE_MINIMUM_HPRD = 0.84

REQUIRED_CANONICAL_COLUMNS = [
    "STATE",
    "PROVNUM",
    "PROVNAME",
    "CITY",
    "MDScensus",
    *NURSE_HOUR_COLUMNS,
]

COLUMN_ALIASES = {
    "STATE": ["STATE", "State", "state"],
    "PROVNUM": [
        "PROVNUM",
        "Provider Number",
        "Provider_Number",
        "CMS Certification Number (CCN)",
        "CCN",
    ],
    "PROVNAME": ["PROVNAME", "Provider Name", "Provider_Name", "Facility Name"],
    "CITY": ["CITY", "City"],
    "WorkDate": ["WorkDate", "WORKDATE", "Work Date", "Date"],
    "CY_Qtr": ["CY_Qtr", "CY_QTR", "Calendar Quarter", "Quarter"],
    "MDScensus": ["MDScensus", "MDS Census", "MDS_Census"],
}

PROVIDER_INFO_ALIASES = {
    "ccn": [
        "CMS Certification Number (CCN)",
        "CMS Certification Number",
        "Federal Provider Number",
        "Provider Number",
        "PROVNUM",
        "CCN",
    ],
    "provider_name": ["Provider Name", "PROVNAME", "Facility Name"],
    "address": ["Provider Address", "Address", "Street Address", "LOCATION"],
    "city": ["Provider City", "City/Town", "City", "CITY"],
    "state": ["Provider State", "State", "STATE"],
    "zip_code": ["Provider Zip Code", "ZIP Code", "Zip", "ZIP"],
    "phone_number": ["Provider Phone Number", "Phone Number", "Telephone Number", "Phone"],
    "certified_beds": ["Number of Certified Beds", "Certified Beds", "Number Certified Beds"],
    "ownership_type": ["Ownership Type", "Ownership", "Provider Ownership Type"],
    "case_mix_nurse_aide_hprd": [
        "Case-Mix Nurse Aide Staffing Hours per Resident per Day",
        "Case Mix Nurse Aide Staffing Hours per Resident per Day",
        "Case-Mix Nurse Aide HPRD",
    ],
    "case_mix_lpn_lvn_hprd": [
        "Case-Mix LPN Staffing Hours per Resident per Day",
        "Case Mix LPN Staffing Hours per Resident per Day",
        "Case-Mix LPN HPRD",
    ],
    "case_mix_rn_hprd": [
        "Case-Mix RN Staffing Hours per Resident per Day",
        "Case Mix RN Staffing Hours per Resident per Day",
        "Case-Mix RN HPRD",
    ],
    "case_mix_total_nurse_hprd": [
        "Case-Mix Total Nurse Staffing Hours per Resident per Day",
        "Case Mix Total Nurse Staffing Hours per Resident per Day",
        "Case-Mix Total Nurse HPRD",
    ],
    "cms_overall_rating": ["Overall Rating", "Overall Star Rating", "CMS Overall Rating"],
    "cms_health_inspection_rating": [
        "Health Inspection Rating",
        "Health Inspection Star Rating",
        "CMS Health Inspection Rating",
    ],
    "cms_staffing_rating": ["Staffing Rating", "Staffing Star Rating", "CMS Staffing Rating"],
    "cms_rn_staffing_rating": ["RN Staffing Rating", "RN Staffing Star Rating", "CMS RN Staffing Rating"],
    "cms_qm_rating": ["QM Rating", "Quality Measure Rating", "Quality Measures Rating"],
    "cms_long_stay_qm_rating": ["Long-Stay QM Rating", "Long Stay QM Rating", "Long-Stay Quality Measure Rating"],
    "cms_short_stay_qm_rating": ["Short-Stay QM Rating", "Short Stay QM Rating", "Short-Stay Quality Measure Rating"],
    "participation_date": ["Provider SSA County Code", "Participation Date"],
    "processing_date": ["Processing Date", "File Date"],
}

PROVIDER_RATING_FIELDS = (
    "cms_overall_rating",
    "cms_health_inspection_rating",
    "cms_staffing_rating",
    "cms_rn_staffing_rating",
    "cms_qm_rating",
    "cms_long_stay_qm_rating",
    "cms_short_stay_qm_rating",
)


SNF_ENROLLMENT_ALIASES = {
    "ccn": ["CCN", "CMS Certification Number (CCN)", "Provider Number", "PROVNUM"],
    "enrollment_state": ["ENROLLMENT STATE", "Enrollment State"],
    "npi": ["NPI"],
    "organization_name": ["ORGANIZATION NAME", "Organization Name"],
    "doing_business_as_name": ["DOING BUSINESS AS NAME", "Doing Business As Name", "DBA Name"],
    "proprietary_nonprofit": ["PROPRIETARY_NONPROFIT", "Proprietary Nonprofit", "Proprietary/Nonprofit"],
    "organization_type_structure": ["ORGANIZATION TYPE STRUCTURE", "Organization Type Structure"],
    "nursing_home_provider_name": ["NURSING HOME PROVIDER NAME", "Nursing Home Provider Name"],
    "affiliation_entity_name": ["AFFILIATION ENTITY NAME", "Affiliation Entity Name"],
    "affiliation_entity_id": ["AFFILIATION ENTITY ID", "Affiliation Entity ID"],
    "incorporation_state": ["INCORPORATION STATE", "Incorporation State"],
    "incorporation_date": ["INCORPORATION DATE", "Incorporation Date"],
    "state": ["STATE", "State"],
}

QUALITY_MEASURES_CLAIMS_ALIASES = {
    "ccn": ["CMS Certification Number (CCN)", "CMS Certification Number", "Provider Number", "PROVNUM", "CCN"],
    "provider_name": ["Provider Name", "PROVNAME", "Facility Name"],
    "state": ["State", "Provider State", "STATE"],
    "measure_code": ["Measure Code", "Measure ID"],
    "measure_description": ["Measure Description", "Measure Name"],
    "resident_type": ["Resident type", "Resident Type"],
    "adjusted_score": ["Adjusted Score"],
    "observed_score": ["Observed Score"],
    "expected_score": ["Expected Score"],
    "footnote_for_score": ["Footnote for Score", "Score Footnote"],
    "used_in_qm_five_star_rating": ["Used in Quality Measure Five Star Rating"],
    "measure_period": ["Measure Period"],
    "processing_date": ["Processing Date", "File Date"],
}

REQUIRED_QUALITY_MEASURES_CLAIMS_FIELDS = (
    "ccn",
    "state",
    "measure_code",
    "measure_description",
    "resident_type",
    "adjusted_score",
    "observed_score",
    "expected_score",
    "footnote_for_score",
    "used_in_qm_five_star_rating",
    "measure_period",
    "processing_date",
)


def normalize_column_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def build_column_lookup(fieldnames: list[str]) -> dict[str, str]:
    normalized = {normalize_column_name(name): name for name in fieldnames}
    lookup: dict[str, str] = {}

    for canonical in REQUIRED_CANONICAL_COLUMNS + CONTRACT_HOUR_COLUMNS + ["WorkDate", "CY_Qtr"]:
        aliases = COLUMN_ALIASES.get(canonical, [canonical])
        if canonical not in aliases:
            aliases = [canonical, *aliases]
        for alias in aliases:
            actual = normalized.get(normalize_column_name(alias))
            if actual:
                lookup[canonical] = actual
                break

    return lookup


def build_alias_lookup(fieldnames: list[str], aliases_by_key: dict[str, list[str]]) -> dict[str, str]:
    normalized = {normalize_column_name(name): name for name in fieldnames}
    lookup: dict[str, str] = {}
    for canonical, aliases in aliases_by_key.items():
        for alias in aliases:
            actual = normalized.get(normalize_column_name(alias))
            if actual:
                lookup[canonical] = actual
                break
    return lookup


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if text == "":
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def parse_rating(value: Any) -> int | float | None:
    parsed = parse_number(value)
    if parsed is None:
        return None
    return int(parsed) if parsed.is_integer() else parsed


def parse_yes_no(value: Any) -> bool | None:
    text = str(value if value is not None else "").strip().upper()
    if text in {"Y", "YES", "TRUE", "1"}:
        return True
    if text in {"N", "NO", "FALSE", "0"}:
        return False
    return None


def parse_work_date(value: str) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def quarter_from_date(day: date) -> str:
    quarter = ((day.month - 1) // 3) + 1
    return f"{day.year}Q{quarter}"


def parse_quarter(value: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"(20\d{2})\s*Q\s*([1-4])", text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}Q{match.group(2)}"
    match = re.search(r"Q\s*([1-4])\s*(20\d{2})", text, re.IGNORECASE)
    if match:
        return f"{match.group(2)}Q{match.group(1)}"
    return None


def quarter_label(quarter: str) -> str:
    return f"Q{quarter[-1]} {quarter[:4]}"


def quarter_bounds(quarter: str) -> tuple[str, str]:
    year = int(quarter[:4])
    q = int(quarter[-1])
    starts = {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)}
    ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    start_month, start_day = starts[q]
    end_month, end_day = ends[q]
    return date(year, start_month, start_day).isoformat(), date(year, end_month, end_day).isoformat()


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback.lower()


def round_metric(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def empty_group() -> dict[str, Any]:
    return {
        "input_daily_row_count": 0,
        "included_daily_row_count": 0,
        "excluded_zero_census_day_count": 0,
        "included_zero_nursing_hours_day_count": 0,
        "excluded_zero_nursing_hours_day_count": 0,
        "resident_days": 0.0,
        "census_day_values": [],
        "hours": defaultdict(float),
        "contract_hours": defaultdict(float),
        "contract_columns_present": set(),
        "contract_value_count": 0,
        "malformed_counts": defaultdict(int),
        "incomplete_values": set(),
    }


def get_value(row: dict[str, str], lookup: dict[str, str], canonical: str) -> str:
    actual = lookup.get(canonical)
    return row.get(actual, "") if actual else ""


def first_present(*values: str | None) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def find_incomplete_columns(fieldnames: list[str]) -> list[str]:
    return [name for name in fieldnames if "incomplete" in name.lower()]


def load_pbj_rows(input_dir: Path) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, str]], dict[str, Any]]:
    csv_paths = sorted(input_dir.glob("*.csv"))
    if not csv_paths:
      raise FileNotFoundError(f"No CSV files found in {input_dir}")

    groups: dict[tuple[str, str], dict[str, Any]] = defaultdict(empty_group)
    facilities: dict[str, dict[str, str]] = {}
    quality = {
        "input_files": [str(path) for path in csv_paths],
        "input_row_count": 0,
        "ct_input_row_count": 0,
        "skipped_rows": {
            "non_ct": 0,
            "missing_ccn": 0,
            "missing_quarter": 0,
        },
        "missing_required_columns_by_file": {},
        "malformed_numeric_values": {},
    }

    for path in csv_paths:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            lookup = build_column_lookup(fieldnames)
            missing_required = [column for column in REQUIRED_CANONICAL_COLUMNS if column not in lookup]
            if "WorkDate" not in lookup and "CY_Qtr" not in lookup:
                missing_required.append("WorkDate or CY_Qtr")
            if missing_required:
                quality["missing_required_columns_by_file"][str(path)] = sorted(set(missing_required))

            incomplete_columns = find_incomplete_columns(fieldnames)

            for row in reader:
                quality["input_row_count"] += 1
                state = get_value(row, lookup, "STATE").strip().upper()
                if state != "CT":
                    quality["skipped_rows"]["non_ct"] += 1
                    continue

                quality["ct_input_row_count"] += 1
                ccn = get_value(row, lookup, "PROVNUM").strip()
                if not ccn:
                    quality["skipped_rows"]["missing_ccn"] += 1
                    continue

                quarter = None
                work_date = parse_work_date(get_value(row, lookup, "WorkDate"))
                if work_date:
                    quarter = quarter_from_date(work_date)
                if not quarter:
                    quarter = parse_quarter(get_value(row, lookup, "CY_Qtr"))
                if not quarter:
                    quality["skipped_rows"]["missing_quarter"] += 1
                    continue

                name = get_value(row, lookup, "PROVNAME").strip() or "Unknown facility"
                city = get_value(row, lookup, "CITY").strip() or "Unknown city"
                facilities[ccn] = {
                    "facility_id": slugify(f"{name}-{ccn}", ccn),
                    "ccn": ccn,
                    "provider_name": name,
                    "city": city,
                    "state": "CT",
                }

                group = groups[(ccn, quarter)]
                group["input_daily_row_count"] += 1

                census = parse_number(get_value(row, lookup, "MDScensus"))
                if census is None:
                    group["malformed_counts"]["MDScensus"] += 1

                daily_hours: dict[str, float] = {}
                daily_contract_hours: dict[str, float] = {}

                for column in NURSE_HOUR_COLUMNS:
                    value = parse_number(get_value(row, lookup, column))
                    if value is None:
                        group["malformed_counts"][column] += 1
                    else:
                        daily_hours[column] = value

                for column in CONTRACT_HOUR_COLUMNS:
                    if column not in lookup:
                        continue
                    group["contract_columns_present"].add(column)
                    value = parse_number(get_value(row, lookup, column))
                    if value is None:
                        group["malformed_counts"][column] += 1
                    else:
                        daily_contract_hours[column] = value

                for column in incomplete_columns:
                    value = str(row.get(column, "")).strip()
                    if value:
                        group["incomplete_values"].add(value)

                if census is None or census <= 0:
                    group["excluded_zero_census_day_count"] += 1
                    continue

                group["included_daily_row_count"] += 1
                group["resident_days"] += census
                group["census_day_values"].append(census)

                daily_total_nursing_hours = sum(daily_hours.values())
                if daily_total_nursing_hours <= 0:
                    group["included_zero_nursing_hours_day_count"] += 1

                for column, value in daily_hours.items():
                    group["hours"][column] += value
                for column, value in daily_contract_hours.items():
                    group["contract_hours"][column] += value
                    group["contract_value_count"] += 1

    return groups, facilities, quality


def load_provider_info(provider_info_path: Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    quality = {
        "provider_info_file_supplied": bool(provider_info_path),
        "provider_info_file": str(provider_info_path) if provider_info_path else None,
        "provider_info_row_count": 0,
        "provider_info_ct_row_count": 0,
        "provider_info_missing_columns": [],
        "provider_info_duplicate_ccn_count": 0,
        "provider_rating_fields_available": False,
        "provider_rating_missing_columns": list(PROVIDER_RATING_FIELDS),
    }
    if not provider_info_path:
        return {}, quality
    if not provider_info_path.exists():
        raise FileNotFoundError(f"Provider Information file not found: {provider_info_path}")

    rows_by_ccn: dict[str, dict[str, Any]] = {}
    with provider_info_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        lookup = build_alias_lookup(fieldnames, PROVIDER_INFO_ALIASES)
        required = ["ccn"]
        quality["provider_info_missing_columns"] = [key for key in required if key not in lookup]
        quality["provider_rating_missing_columns"] = [key for key in PROVIDER_RATING_FIELDS if key not in lookup]
        quality["provider_rating_fields_available"] = any(key in lookup for key in PROVIDER_RATING_FIELDS)
        if "ccn" not in lookup:
            return {}, quality

        for row in reader:
            quality["provider_info_row_count"] += 1
            state = get_value(row, lookup, "state").strip().upper()
            if state and state != "CT":
                continue
            ccn = get_value(row, lookup, "ccn").strip()
            if not ccn:
                continue
            quality["provider_info_ct_row_count"] += 1
            if ccn in rows_by_ccn:
                quality["provider_info_duplicate_ccn_count"] += 1

            ratings = {key: parse_rating(get_value(row, lookup, key)) for key in PROVIDER_RATING_FIELDS}
            has_rating = any(value is not None for value in ratings.values())
            rows_by_ccn[ccn] = {
                "ccn": ccn,
                "provider_name": get_value(row, lookup, "provider_name").strip(),
                "address": get_value(row, lookup, "address").strip(),
                "city": get_value(row, lookup, "city").strip(),
                "state": state,
                "zip_code": get_value(row, lookup, "zip_code").strip(),
                "phone_number": get_value(row, lookup, "phone_number").strip(),
                "certified_beds": parse_number(get_value(row, lookup, "certified_beds")),
                "ownership_type": get_value(row, lookup, "ownership_type").strip(),
                "case_mix_nurse_aide_hprd": parse_number(get_value(row, lookup, "case_mix_nurse_aide_hprd")),
                "case_mix_lpn_lvn_hprd": parse_number(get_value(row, lookup, "case_mix_lpn_lvn_hprd")),
                "case_mix_rn_hprd": parse_number(get_value(row, lookup, "case_mix_rn_hprd")),
                "case_mix_total_nurse_hprd": parse_number(get_value(row, lookup, "case_mix_total_nurse_hprd")),
                **ratings,
                "cms_rating_source": "CMS Nursing Home Provider Information" if has_rating else None,
                "cms_rating_source_note": (
                    "CMS Care Compare star ratings imported from Provider Information; not calculated by this tool."
                    if has_rating
                    else None
                ),
                "participation_date": get_value(row, lookup, "participation_date").strip(),
                "processing_date": get_value(row, lookup, "processing_date").strip(),
            }

    return rows_by_ccn, quality


def load_snf_enrollments(snf_enrollments_path: Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    quality = {
        "snf_enrollments_file_supplied": bool(snf_enrollments_path),
        "snf_enrollments_file": str(snf_enrollments_path) if snf_enrollments_path else None,
        "snf_enrollments_row_count": 0,
        "snf_enrollments_ct_row_count": 0,
        "snf_enrollments_missing_columns": [],
        "snf_enrollments_duplicate_ccn_count": 0,
    }
    if not snf_enrollments_path:
        return {}, quality
    if not snf_enrollments_path.exists():
        raise FileNotFoundError(f"SNF Enrollments file not found: {snf_enrollments_path}")

    rows_by_ccn: dict[str, dict[str, Any]] = {}
    with snf_enrollments_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        lookup = build_alias_lookup(fieldnames, SNF_ENROLLMENT_ALIASES)
        required = ["ccn"]
        quality["snf_enrollments_missing_columns"] = [key for key in required if key not in lookup]
        if "ccn" not in lookup:
            return {}, quality

        for row in reader:
            quality["snf_enrollments_row_count"] += 1
            state = get_value(row, lookup, "state").strip().upper()
            enrollment_state = get_value(row, lookup, "enrollment_state").strip().upper()
            if "CT" not in {state, enrollment_state}:
                continue
            ccn = get_value(row, lookup, "ccn").strip()
            if not ccn:
                continue
            quality["snf_enrollments_ct_row_count"] += 1
            if ccn in rows_by_ccn:
                quality["snf_enrollments_duplicate_ccn_count"] += 1
                continue

            rows_by_ccn[ccn] = {
                "ccn": ccn,
                "enrollment_npi": get_value(row, lookup, "npi").strip(),
                "enrollment_organization_name": get_value(row, lookup, "organization_name").strip(),
                "enrollment_doing_business_as_name": get_value(row, lookup, "doing_business_as_name").strip(),
                "enrollment_proprietary_nonprofit": get_value(row, lookup, "proprietary_nonprofit").strip(),
                "enrollment_organization_type_structure": get_value(row, lookup, "organization_type_structure").strip(),
                "enrollment_nursing_home_provider_name": get_value(row, lookup, "nursing_home_provider_name").strip(),
                "affiliation_entity_name": get_value(row, lookup, "affiliation_entity_name").strip(),
                "affiliation_entity_id": get_value(row, lookup, "affiliation_entity_id").strip(),
                "incorporation_state": get_value(row, lookup, "incorporation_state").strip(),
                "incorporation_date": get_value(row, lookup, "incorporation_date").strip(),
            }

    return rows_by_ccn, quality


def load_quality_measures_claims(
    quality_measures_claims_path: Path | None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    quality = {
        "quality_measures_claims_file_supplied": bool(quality_measures_claims_path),
        "quality_measures_claims_file": str(quality_measures_claims_path) if quality_measures_claims_path else None,
        "quality_measures_claims_row_count": 0,
        "quality_measures_claims_ct_row_count": 0,
        "quality_measures_claims_missing_columns": list(REQUIRED_QUALITY_MEASURES_CLAIMS_FIELDS),
        "quality_measures_claims_measure_count": 0,
    }
    if not quality_measures_claims_path:
        return {}, quality
    if not quality_measures_claims_path.exists():
        raise FileNotFoundError(f"Quality Measures Claims file not found: {quality_measures_claims_path}")

    rows_by_ccn: dict[str, list[dict[str, Any]]] = defaultdict(list)
    measure_codes: set[str] = set()
    with quality_measures_claims_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        lookup = build_alias_lookup(fieldnames, QUALITY_MEASURES_CLAIMS_ALIASES)
        quality["quality_measures_claims_missing_columns"] = [
            key for key in REQUIRED_QUALITY_MEASURES_CLAIMS_FIELDS if key not in lookup
        ]
        if "ccn" not in lookup:
            return {}, quality

        for row in reader:
            quality["quality_measures_claims_row_count"] += 1
            state = get_value(row, lookup, "state").strip().upper()
            if state and state != "CT":
                continue
            ccn = get_value(row, lookup, "ccn").strip()
            if not ccn:
                continue
            quality["quality_measures_claims_ct_row_count"] += 1
            measure_code = get_value(row, lookup, "measure_code").strip()
            if measure_code:
                measure_codes.add(measure_code)
            rows_by_ccn[ccn].append({
                "measure_code": measure_code,
                "measure_description": get_value(row, lookup, "measure_description").strip(),
                "resident_type": get_value(row, lookup, "resident_type").strip(),
                "adjusted_score": parse_number(get_value(row, lookup, "adjusted_score")),
                "observed_score": parse_number(get_value(row, lookup, "observed_score")),
                "expected_score": parse_number(get_value(row, lookup, "expected_score")),
                "footnote_for_score": get_value(row, lookup, "footnote_for_score").strip(),
                "used_in_qm_five_star_rating": parse_yes_no(get_value(row, lookup, "used_in_qm_five_star_rating")),
                "measure_period": get_value(row, lookup, "measure_period").strip(),
                "processing_date": get_value(row, lookup, "processing_date").strip(),
                "quality_measure_source": "CMS Nursing Home Quality Measures Claims",
            })

    quality["quality_measures_claims_measure_count"] = len(measure_codes)
    for ccn, rows in rows_by_ccn.items():
        rows_by_ccn[ccn] = sorted(rows, key=lambda row: (row.get("resident_type") or "", row.get("measure_code") or ""))
    return dict(rows_by_ccn), quality


def merge_quality_measures_claims(
    facilities_by_ccn: dict[str, dict[str, Any]],
    quality_measures_by_ccn: dict[str, list[dict[str, Any]]],
    quality_measures_quality: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    facilities_with_measures = 0
    for ccn, facility in facilities_by_ccn.items():
        measures = quality_measures_by_ccn.get(ccn, [])
        if measures:
            facilities_with_measures += 1
        merged[ccn] = {
            **facility,
            "quality_measures_claims": measures,
        }

    merge_quality = {
        **quality_measures_quality,
        "facilities_with_quality_measures_claims_count": facilities_with_measures,
        "unmatched_quality_measure_ccn_count": len(set(quality_measures_by_ccn) - set(facilities_by_ccn)),
    }
    return merged, merge_quality


def merge_snf_enrollment_metadata(
    facilities_by_ccn: dict[str, dict[str, Any]],
    snf_rows_by_ccn: dict[str, dict[str, Any]],
    snf_quality: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    matched = 0
    for ccn, facility in facilities_by_ccn.items():
        snf = snf_rows_by_ccn.get(ccn)
        matched_snf = snf is not None
        if matched_snf:
            matched += 1
        snf = snf or {}
        merged[ccn] = {
            **facility,
            "enrollment_source_matched": matched_snf,
            "enrollment_npi": first_present(snf.get("enrollment_npi")),
            "enrollment_organization_name": first_present(snf.get("enrollment_organization_name")),
            "enrollment_doing_business_as_name": first_present(snf.get("enrollment_doing_business_as_name")),
            "enrollment_proprietary_nonprofit": first_present(snf.get("enrollment_proprietary_nonprofit")),
            "enrollment_organization_type_structure": first_present(snf.get("enrollment_organization_type_structure")),
            "enrollment_nursing_home_provider_name": first_present(snf.get("enrollment_nursing_home_provider_name")),
            "affiliation_entity_name": first_present(snf.get("affiliation_entity_name")),
            "affiliation_entity_id": first_present(snf.get("affiliation_entity_id")),
            "incorporation_state": first_present(snf.get("incorporation_state")),
            "incorporation_date": first_present(snf.get("incorporation_date")),
        }

    merge_quality = {
        **snf_quality,
        "matched_snf_enrollment_facility_count": matched,
        "unmatched_pbj_facility_count_for_snf_enrollments": len(facilities_by_ccn) - matched,
        "unmatched_snf_enrollment_row_count": len(set(snf_rows_by_ccn) - set(facilities_by_ccn)),
    }
    return merged, merge_quality


def merge_provider_metadata(
    facilities_by_ccn: dict[str, dict[str, str]],
    provider_rows_by_ccn: dict[str, dict[str, Any]],
    provider_quality: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    matched = 0
    for ccn, pbj_facility in facilities_by_ccn.items():
        provider = provider_rows_by_ccn.get(ccn)
        matched_provider = provider is not None
        if matched_provider:
            matched += 1
        provider = provider or {}
        name = first_present(provider.get("provider_name"), pbj_facility.get("provider_name"))
        city = first_present(provider.get("city"), pbj_facility.get("city"))
        state = first_present(provider.get("state"), pbj_facility.get("state"), "CT")
        merged[ccn] = {
            "facility_id": pbj_facility.get("facility_id") or slugify(f"{name}-{ccn}", ccn),
            "ccn": ccn,
            "provider_name": name or "Unknown facility",
            "pbj_provider_name": pbj_facility.get("provider_name", ""),
            "provider_info_provider_name": provider.get("provider_name", ""),
            "provider_source_matched": matched_provider,
            "address": first_present(provider.get("address")),
            "city": city or "Unknown city",
            "state": state,
            "zip_code": first_present(provider.get("zip_code")),
            "phone_number": first_present(provider.get("phone_number")),
            "certified_beds": provider.get("certified_beds"),
            "ownership_type": first_present(provider.get("ownership_type")),
            "cms_overall_rating": provider.get("cms_overall_rating"),
            "cms_health_inspection_rating": provider.get("cms_health_inspection_rating"),
            "cms_staffing_rating": provider.get("cms_staffing_rating"),
            "cms_rn_staffing_rating": provider.get("cms_rn_staffing_rating"),
            "cms_qm_rating": provider.get("cms_qm_rating"),
            "cms_long_stay_qm_rating": provider.get("cms_long_stay_qm_rating"),
            "cms_short_stay_qm_rating": provider.get("cms_short_stay_qm_rating"),
            "cms_rating_source": provider.get("cms_rating_source"),
            "cms_rating_source_note": provider.get("cms_rating_source_note"),
            "case_mix_benchmarks": {
                "case_mix_total_nurse_hprd": provider.get("case_mix_total_nurse_hprd"),
                "case_mix_rn_hprd": provider.get("case_mix_rn_hprd"),
                "case_mix_lpn_lvn_hprd": provider.get("case_mix_lpn_lvn_hprd"),
                "case_mix_nurse_aide_hprd": provider.get("case_mix_nurse_aide_hprd"),
            },
            "active_participation_indicator": first_present(provider.get("participation_date")),
            "provider_info_processing_date": first_present(provider.get("processing_date")),
            "metadata_source": "provider_info" if matched_provider else "pbj",
        }

    merge_quality = {
        **provider_quality,
        "pbj_facility_count": len(facilities_by_ccn),
        "matched_facility_count": matched,
        "unmatched_pbj_facility_count": len(facilities_by_ccn) - matched,
        "unmatched_provider_info_row_count": len(set(provider_rows_by_ccn) - set(facilities_by_ccn)),
    }
    return merged, merge_quality


def build_interpretation(metrics: dict[str, float | None], has_contract: bool) -> dict[str, str]:
    total = metrics["total_nurse_hprd"]
    contract = metrics["contract_staff_pct"]
    ct_total_below = metrics.get("ct_total_direct_care_below_minimum_estimate") is True
    ct_licensed_below = metrics.get("ct_licensed_direct_care_below_minimum_estimate") is True
    total_text = f"{total:.2f}" if total is not None else "an unavailable total nurse HPRD"
    contract_text = (
        f" and contract staff represented {contract:.1f}% of reported nursing hours"
        if has_contract and contract is not None
        else ""
    )
    ct_comparison_text = ""
    if ct_total_below or ct_licensed_below:
        below_points = []
        if ct_total_below:
            below_points.append("the CT 3.00 total direct-care comparison point")
        if ct_licensed_below:
            below_points.append("the CT 0.84 licensed-nursing comparison point")
        ct_comparison_text = f" The PBJ-derived CT screening estimate is below {' and '.join(below_points)}."
    return {
        "shows": f"The selected quarter reports {total_text} total nurse hours per resident day{contract_text}.{ct_comparison_text}",
        "suggests": "Use this quarterly pattern as a screening signal for resident-centered questions about staffing, continuity, response times, and shift-level context.",
        "cannot_prove": "Quarterly PBJ HPRD and CT direct-care comparison estimates do not prove harm, neglect, noncompliance, causation, or staffing levels for a specific resident, day, unit, or shift.",
    }


def build_output(
    groups: dict[tuple[str, str], dict[str, Any]],
    facilities_by_ccn: dict[str, dict[str, str]],
    quality: dict[str, Any],
    output_path: Path,
    source_release: str,
    freshness_date: str,
    provider_rows_by_ccn: dict[str, dict[str, Any]] | None = None,
    provider_quality: dict[str, Any] | None = None,
    snf_rows_by_ccn: dict[str, dict[str, Any]] | None = None,
    snf_quality: dict[str, Any] | None = None,
    quality_measures_by_ccn: dict[str, list[dict[str, Any]]] | None = None,
    quality_measures_quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provider_rows_by_ccn = provider_rows_by_ccn or {}
    provider_quality = provider_quality or {
        "provider_info_file_supplied": False,
        "provider_info_file": None,
        "provider_info_row_count": 0,
        "provider_info_ct_row_count": 0,
        "provider_info_missing_columns": [],
        "provider_info_duplicate_ccn_count": 0,
        "provider_rating_fields_available": False,
        "provider_rating_missing_columns": list(PROVIDER_RATING_FIELDS),
    }
    snf_rows_by_ccn = snf_rows_by_ccn or {}
    snf_quality = snf_quality or {
        "snf_enrollments_file_supplied": False,
        "snf_enrollments_file": None,
        "snf_enrollments_row_count": 0,
        "snf_enrollments_ct_row_count": 0,
        "snf_enrollments_missing_columns": [],
        "snf_enrollments_duplicate_ccn_count": 0,
    }
    quality_measures_by_ccn = quality_measures_by_ccn or {}
    quality_measures_quality = quality_measures_quality or {
        "quality_measures_claims_file_supplied": False,
        "quality_measures_claims_file": None,
        "quality_measures_claims_row_count": 0,
        "quality_measures_claims_ct_row_count": 0,
        "quality_measures_claims_missing_columns": list(REQUIRED_QUALITY_MEASURES_CLAIMS_FIELDS),
        "quality_measures_claims_measure_count": 0,
    }
    facilities_by_ccn, merge_quality = merge_provider_metadata(facilities_by_ccn, provider_rows_by_ccn, provider_quality)
    facilities_by_ccn, snf_merge_quality = merge_snf_enrollment_metadata(facilities_by_ccn, snf_rows_by_ccn, snf_quality)
    facilities_by_ccn, qm_merge_quality = merge_quality_measures_claims(
        facilities_by_ccn,
        quality_measures_by_ccn,
        quality_measures_quality,
    )
    quarters = sorted({quarter for _, quarter in groups})
    reporting_quarter = quarters[-1] if quarters else ""
    start_date, end_date = quarter_bounds(reporting_quarter) if reporting_quarter else ("", "")
    facility_rows = sorted(facilities_by_ccn.values(), key=lambda row: (row["provider_name"], row["ccn"]))
    staffing_rows = []
    sources = [
        {
            "source_dataset_name": "CMS Payroll-Based Journal Daily Nurse Staffing",
            "source_release": source_release,
            "freshness_date": freshness_date,
            "source_level": "official CMS PBJ local CSV export",
            "notes": "Generated offline from manually supplied PBJ CSV files. PBJ-calculated staffing metrics remain the actual staffing values in this export.",
        }
    ]
    if provider_quality.get("provider_info_file_supplied"):
        sources.append({
            "source_dataset_name": "CMS Nursing Home Provider Information",
            "source_release": provider_quality.get("provider_info_file") or "manual local Provider Information CSV",
            "freshness_date": freshness_date,
            "source_level": "official CMS Provider Information local CSV export",
            "notes": "Optional facility metadata, case-mix comparison, and CMS Care Compare rating context merged by CCN. PBJ-derived facility and staffing values are retained when Provider Information values are blank or unmatched.",
        })
    if snf_quality.get("snf_enrollments_file_supplied"):
        sources.append({
            "source_dataset_name": "CMS Skilled Nursing Facility Enrollments",
            "source_release": snf_quality.get("snf_enrollments_file") or "manual local SNF Enrollments CSV",
            "freshness_date": freshness_date,
            "source_level": "official CMS SNF Enrollments local CSV export",
            "notes": "Optional legal organization and affiliation context merged by CCN. These fields do not replace Provider Information display metadata.",
        })
    if quality_measures_quality.get("quality_measures_claims_file_supplied"):
        sources.append({
            "source_dataset_name": "CMS Nursing Home Quality Measures Claims",
            "source_release": quality_measures_quality.get("quality_measures_claims_file") or "manual local Quality Measures Claims CSV",
            "freshness_date": freshness_date,
            "source_level": "official CMS Quality Measures Claims local CSV export",
            "notes": "Optional facility-level claims-based quality-measure context merged by CCN. These measures are imported from CMS and are not calculated by this staffing tool.",
        })

    for (ccn, quarter), group in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1])):
        resident_days = group["resident_days"]
        has_resident_days = resident_days > 0
        rn_hours = sum(group["hours"][column] for column in RN_HOUR_COLUMNS)
        lpn_hours = sum(group["hours"][column] for column in LPN_HOUR_COLUMNS)
        aide_hours = sum(group["hours"][column] for column in NURSE_AIDE_HOUR_COLUMNS)
        total_hours = rn_hours + lpn_hours + aide_hours
        ct_direct_care_total_hours = sum(group["hours"][column] for column in CT_DIRECT_CARE_TOTAL_HOUR_COLUMNS)
        ct_direct_care_licensed_hours = sum(
            group["hours"][column] for column in CT_DIRECT_CARE_LICENSED_NURSE_HOUR_COLUMNS
        )
        contract_hours = sum(group["contract_hours"][column] for column in CONTRACT_HOUR_COLUMNS)
        has_contract_columns = bool(group["contract_columns_present"])
        has_contract_values = group["contract_value_count"] > 0
        facility = facilities_by_ccn.get(ccn, {})
        case_mix_benchmarks = facility.get("case_mix_benchmarks", {})
        benchmark_values = {
            "case_mix_total_nurse_hprd": case_mix_benchmarks.get("case_mix_total_nurse_hprd"),
            "case_mix_rn_hprd": case_mix_benchmarks.get("case_mix_rn_hprd"),
            "case_mix_lpn_lvn_hprd": case_mix_benchmarks.get("case_mix_lpn_lvn_hprd"),
            "case_mix_nurse_aide_hprd": case_mix_benchmarks.get("case_mix_nurse_aide_hprd"),
        }
        benchmark_available = any(value is not None for value in benchmark_values.values())
        contract_pct = None
        if has_contract_values and total_hours > 0:
            contract_pct = (contract_hours / total_hours) * 100

        ct_total_direct_care_hprd = round_metric(
            ct_direct_care_total_hours / resident_days if has_resident_days else None
        )
        ct_licensed_direct_care_hprd = round_metric(
            ct_direct_care_licensed_hours / resident_days if has_resident_days else None
        )
        ct_total_direct_care_difference = round_metric(
            ct_total_direct_care_hprd - CT_TOTAL_DIRECT_CARE_MINIMUM_HPRD
            if ct_total_direct_care_hprd is not None
            else None
        )
        ct_licensed_direct_care_difference = round_metric(
            ct_licensed_direct_care_hprd - CT_LICENSED_DIRECT_CARE_MINIMUM_HPRD
            if ct_licensed_direct_care_hprd is not None
            else None
        )

        metrics = {
            "total_nurse_hprd": round_metric(total_hours / resident_days if has_resident_days else None),
            "rn_hprd": round_metric(rn_hours / resident_days if has_resident_days else None),
            "lpn_lvn_hprd": round_metric(lpn_hours / resident_days if has_resident_days else None),
            "nurse_aide_hprd": round_metric(aide_hours / resident_days if has_resident_days else None),
            "contract_staff_pct": round_metric(contract_pct, 1),
            "ct_direct_care_total_hprd_estimate": ct_total_direct_care_hprd,
            "ct_direct_care_licensed_nurse_hprd_estimate": ct_licensed_direct_care_hprd,
            "ct_total_direct_care_minimum_hprd": CT_TOTAL_DIRECT_CARE_MINIMUM_HPRD,
            "ct_licensed_direct_care_minimum_hprd": CT_LICENSED_DIRECT_CARE_MINIMUM_HPRD,
            "ct_total_direct_care_difference_from_minimum": ct_total_direct_care_difference,
            "ct_licensed_direct_care_difference_from_minimum": ct_licensed_direct_care_difference,
            "ct_total_direct_care_below_minimum_estimate": (
                ct_total_direct_care_hprd < CT_TOTAL_DIRECT_CARE_MINIMUM_HPRD
                if ct_total_direct_care_hprd is not None
                else None
            ),
            "ct_licensed_direct_care_below_minimum_estimate": (
                ct_licensed_direct_care_hprd < CT_LICENSED_DIRECT_CARE_MINIMUM_HPRD
                if ct_licensed_direct_care_hprd is not None
                else None
            ),
        }
        missing_fields = [key for key, value in metrics.items() if value is None]
        if not has_resident_days:
            missing_fields.append("resident_days")
        if not has_contract_columns:
            missing_fields.append("contract_staff_pct")

        malformed_counts = {key: value for key, value in sorted(group["malformed_counts"].items()) if value}
        if malformed_counts:
            for key, value in malformed_counts.items():
                quality["malformed_numeric_values"][f"{ccn}:{quarter}:{key}"] = value

        notes = []
        if not has_resident_days:
            notes.append("Resident-day denominator is zero or unavailable; HPRD metrics are null.")
        if not has_contract_columns:
            notes.append("Contract-hour source columns were not found; contract percentage is null.")
        elif not has_contract_values:
            notes.append("Contract-hour source columns were present but values were unavailable or malformed; contract percentage is null.")
        if malformed_counts:
            notes.append("One or more numeric source values were blank or malformed; see malformed_numeric_values in data_quality.")
        if group["incomplete_values"]:
            notes.append("CMS incomplete indicator appeared for this facility-quarter.")
        if facility.get("provider_source_matched") and not benchmark_available:
            notes.append("Provider Information matched, but case-mix benchmark staffing fields were unavailable or blank.")

        quarter_start, quarter_end = quarter_bounds(quarter)
        row = {
            "ccn": ccn,
            "quarter": quarter,
            "quarter_label": quarter_label(quarter),
            "quarter_start_date": quarter_start,
            "quarter_end_date": quarter_end,
            "average_resident_census": round_metric(
                sum(group["census_day_values"]) / len(group["census_day_values"]) if group["census_day_values"] else None,
                1,
            ),
            "resident_days": round_metric(resident_days, 1) if has_resident_days else None,
            "metrics": metrics,
            "benchmarks": {
                **benchmark_values,
                "case_mix_benchmark_available": benchmark_available,
                "benchmark_source": "CMS Nursing Home Provider Information" if benchmark_available else None,
                "benchmark_source_note": (
                    "Contextual provider-file case-mix staffing benchmark; not a replacement for PBJ-calculated actual staffing HPRD and not guaranteed to align exactly with the PBJ quarter."
                    if benchmark_available
                    else None
                ),
            },
            "data_quality": {
                "input_row_count": group["input_daily_row_count"],
                "input_daily_row_count": group["input_daily_row_count"],
                "included_daily_row_count": group["included_daily_row_count"],
                "excluded_zero_census_day_count": group["excluded_zero_census_day_count"],
                "excluded_zero_nursing_hours_day_count": group["excluded_zero_nursing_hours_day_count"],
                "included_zero_nursing_hours_day_count": group["included_zero_nursing_hours_day_count"],
                "cms_incomplete_indicator_present": bool(group["incomplete_values"]),
                "cms_incomplete_indicator_values": sorted(group["incomplete_values"]),
                "missing_fields": sorted(set(missing_fields)),
                "malformed_numeric_counts": malformed_counts,
                "notes": notes,
            },
        }
        if quarter == reporting_quarter:
            row["interpretation"] = build_interpretation(metrics, has_contract_columns)
        staffing_rows.append(row)

    return {
        "schema_version": "2.0-phase4a",
        "dataset_type": "nursing_home_staffing_explorer",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "reporting_period": {
            "quarter": reporting_quarter,
            "label": quarter_label(reporting_quarter) if reporting_quarter else "",
            "start_date": start_date,
            "end_date": end_date,
        },
        "sources": sources,
        "facilities": facility_rows,
        "facility_quarterly_staffing": staffing_rows,
        "data_quality": {
            **quality,
            **merge_quality,
            **snf_merge_quality,
            **qm_merge_quality,
            "output_path": str(output_path),
            "facility_count": len(facility_rows),
            "quarterly_row_count": len(staffing_rows),
            "case_mix_benchmark_available_count": sum(
                1
                for row in staffing_rows
                if row["benchmarks"].get("case_mix_benchmark_available")
            ),
            "facilities_with_overall_rating_count": sum(
                1 for facility in facility_rows if facility.get("cms_overall_rating") is not None
            ),
            "facilities_with_qm_rating_count": sum(
                1 for facility in facility_rows if facility.get("cms_qm_rating") is not None
            ),
            "facilities_with_staffing_rating_count": sum(
                1 for facility in facility_rows if facility.get("cms_staffing_rating") is not None
            ),
            "ct_total_direct_care_below_minimum_estimate_count": sum(
                1
                for row in staffing_rows
                if row["metrics"].get("ct_total_direct_care_below_minimum_estimate") is True
            ),
            "ct_licensed_direct_care_below_minimum_estimate_count": sum(
                1
                for row in staffing_rows
                if row["metrics"].get("ct_licensed_direct_care_below_minimum_estimate") is True
            ),
            "metric_precision": {
                "hprd_decimal_places": 2,
                "contract_staff_pct_decimal_places": 1,
                "average_resident_census_decimal_places": 1,
            },
            "average_census_method": "Simple average of daily MDScensus source values for the facility-quarter.",
            "ct_direct_care_comparison_note": "PBJ-derived Connecticut screening estimates use Title 19 Sec. 19-13-D8t(m)(6) comparison points and exclude Hrs_RNDON, Hrs_RNadmin, and Hrs_LPNadmin. They are not formal compliance determinations.",
        },
        "field_map": {
            "ccn": "PROVNUM",
            "provider_name": "Provider Information Provider Name when matched and nonblank; otherwise PBJ PROVNAME",
            "city": "Provider Information Provider City when matched and nonblank; otherwise PBJ CITY",
            "state": "Provider Information Provider State when matched and nonblank; otherwise PBJ STATE",
            "address": "Provider Information address when matched",
            "zip_code": "Provider Information ZIP code when matched",
            "phone_number": "Provider Information phone number when matched",
            "certified_beds": "Provider Information number of certified beds when matched",
            "ownership_type": "Provider Information ownership type when matched",
            "cms_overall_rating": "CMS Care Compare Overall Rating from Nursing Home Provider Information; contextual rating, not calculated by this tool",
            "cms_health_inspection_rating": "CMS Care Compare Health Inspection Rating from Nursing Home Provider Information; contextual rating, not calculated by this tool",
            "cms_staffing_rating": "CMS Care Compare Staffing Rating from Nursing Home Provider Information; contextual rating, not a replacement for PBJ HPRD metrics",
            "cms_rn_staffing_rating": "CMS Care Compare RN Staffing Rating from Nursing Home Provider Information when present; contextual rating, not a replacement for PBJ RN HPRD",
            "cms_qm_rating": "CMS Care Compare Quality Measures Rating from Nursing Home Provider Information; contextual rating, not calculated by this tool",
            "cms_long_stay_qm_rating": "CMS Care Compare Long-Stay Quality Measures Rating from Nursing Home Provider Information; contextual rating, not calculated by this tool",
            "cms_short_stay_qm_rating": "CMS Care Compare Short-Stay Quality Measures Rating from Nursing Home Provider Information; contextual rating, not calculated by this tool",
            "cms_rating_source": "Source label for imported CMS Care Compare rating context",
            "cms_rating_source_note": "Caveat for imported CMS Care Compare rating context",
            "quality_measures_claims": "Facility-level CMS Nursing Home Quality Measures Claims rows merged by CCN; contextual Care Compare quality-measure data, not calculated by this tool",
            "measure_code": "CMS Quality Measures Claims measure code",
            "measure_description": "CMS Quality Measures Claims measure description",
            "resident_type": "CMS Quality Measures Claims resident type",
            "adjusted_score": "CMS Quality Measures Claims adjusted score, parsed as numeric when available",
            "observed_score": "CMS Quality Measures Claims observed score, parsed as numeric when available",
            "expected_score": "CMS Quality Measures Claims expected score, parsed as numeric when available",
            "footnote_for_score": "CMS Quality Measures Claims score footnote",
            "used_in_qm_five_star_rating": "Whether CMS marks the quality measure as used in the Quality Measure Five-Star Rating",
            "measure_period": "CMS Quality Measures Claims measure period",
            "quality_measure_source": "Source label for imported CMS Quality Measures Claims row",
            "enrollment_npi": "SNF Enrollments NPI when matched by CCN; enrollment context only",
            "enrollment_organization_name": "SNF Enrollments legal organization name when matched by CCN",
            "enrollment_doing_business_as_name": "SNF Enrollments doing-business-as name when matched by CCN",
            "enrollment_proprietary_nonprofit": "SNF Enrollments proprietary/nonprofit flag when matched by CCN",
            "enrollment_organization_type_structure": "SNF Enrollments organization type/structure when matched by CCN",
            "enrollment_nursing_home_provider_name": "SNF Enrollments nursing home provider name when matched by CCN",
            "affiliation_entity_name": "SNF Enrollments affiliation entity name for future chain/affiliation analysis",
            "affiliation_entity_id": "SNF Enrollments affiliation entity ID for future chain/affiliation linkage",
            "incorporation_state": "SNF Enrollments incorporation state when matched by CCN",
            "incorporation_date": "SNF Enrollments incorporation date when matched by CCN",
            "case_mix_total_nurse_hprd": "Provider Information Case-Mix Total Nurse Staffing Hours per Resident per Day, contextual benchmark only",
            "case_mix_rn_hprd": "Provider Information Case-Mix RN Staffing Hours per Resident per Day, contextual benchmark only",
            "case_mix_lpn_lvn_hprd": "Provider Information Case-Mix LPN Staffing Hours per Resident per Day, contextual benchmark only",
            "case_mix_nurse_aide_hprd": "Provider Information Case-Mix Nurse Aide Staffing Hours per Resident per Day, contextual benchmark only",
            "quarter": "WorkDate calendar quarter, falling back to CY_Qtr when WorkDate is unavailable",
            "average_resident_census": "simple average of daily MDScensus values for the facility-quarter",
            "resident_days": "sum(MDScensus)",
            "total_nurse_hprd": "(Hrs_RNDON + Hrs_RNadmin + Hrs_RN + Hrs_LPNadmin + Hrs_LPN + Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days",
            "rn_hprd": "(Hrs_RNDON + Hrs_RNadmin + Hrs_RN) / resident_days",
            "lpn_lvn_hprd": "(Hrs_LPNadmin + Hrs_LPN) / resident_days",
            "nurse_aide_hprd": "(Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days",
            "ct_direct_care_total_hprd_estimate": "PBJ-derived CT screening estimate: (Hrs_RN + Hrs_LPN + Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days; excludes Hrs_RNDON, Hrs_RNadmin, and Hrs_LPNadmin.",
            "ct_direct_care_licensed_nurse_hprd_estimate": "PBJ-derived CT screening estimate: (Hrs_RN + Hrs_LPN) / resident_days; excludes Hrs_RNDON, Hrs_RNadmin, and Hrs_LPNadmin.",
            "ct_total_direct_care_minimum_hprd": "Connecticut Title 19 Sec. 19-13-D8t(m)(6) total nursing and nurse's aide personnel comparison point: 3.00 HPRD.",
            "ct_licensed_direct_care_minimum_hprd": "Connecticut Title 19 Sec. 19-13-D8t(m)(6) licensed nursing personnel comparison point: 0.84 HPRD.",
            "ct_total_direct_care_difference_from_minimum": "ct_direct_care_total_hprd_estimate minus 3.00; PBJ-derived screening estimate only.",
            "ct_licensed_direct_care_difference_from_minimum": "ct_direct_care_licensed_nurse_hprd_estimate minus 0.84; PBJ-derived screening estimate only.",
            "ct_total_direct_care_below_minimum_estimate": "True when the PBJ-derived CT total direct-care estimate is below 3.00 HPRD; not a formal compliance determination.",
            "ct_licensed_direct_care_below_minimum_estimate": "True when the PBJ-derived CT licensed direct-care estimate is below 0.84 HPRD; not a formal compliance determination.",
            "contract_staff_pct": "sum nurse category _ctr columns / total nurse category hours * 100",
        },
    }


def validate_output(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_top = [
        "schema_version",
        "dataset_type",
        "generated_at",
        "reporting_period",
        "sources",
        "facilities",
        "facility_quarterly_staffing",
        "data_quality",
        "field_map",
    ]
    for key in required_top:
        if key not in data:
            errors.append(f"Missing top-level key: {key}")
    if not data.get("facilities"):
        errors.append("No CT facilities in output.")
    if not data.get("facility_quarterly_staffing"):
        errors.append("No quarterly staffing rows in output.")

    for row in data.get("facility_quarterly_staffing", []):
        metrics = row.get("metrics", {})
        for key in (
            "total_nurse_hprd",
            "rn_hprd",
            "lpn_lvn_hprd",
            "nurse_aide_hprd",
            "ct_direct_care_total_hprd_estimate",
            "ct_direct_care_licensed_nurse_hprd_estimate",
        ):
            value = metrics.get(key)
            if value is not None and value < 0:
                errors.append(f"Negative HPRD value for {row.get('ccn')} {row.get('quarter')} {key}: {value}")
        contract_pct = metrics.get("contract_staff_pct")
        if contract_pct is not None and not (0 <= contract_pct <= 100):
            errors.append(f"Contract percentage outside 0-100 for {row.get('ccn')} {row.get('quarter')}: {contract_pct}")
    return errors


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CT staffing explorer JSON from local CMS PBJ CSV files.")
    parser.add_argument("--input-dir", default="source_data/pbj", help="Folder containing manually downloaded PBJ CSV files.")
    parser.add_argument("--output", default="data/nursing_home_staffing_ct.json", help="Output JSON path.")
    parser.add_argument("--provider-info", default=None, help="Optional CMS Nursing Home Provider Information CSV path.")
    parser.add_argument("--snf-enrollments", default=None, help="Optional CMS Skilled Nursing Facility Enrollments CSV path.")
    parser.add_argument("--quality-measures-claims", default=None, help="Optional CMS Nursing Home Quality Measures Claims CSV path.")
    parser.add_argument("--source-release", default="manual local PBJ CSV export", help="Source release label to store in output metadata.")
    parser.add_argument("--freshness-date", default=date.today().isoformat(), help="Source freshness/export date to store in output metadata.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)
    try:
        groups, facilities, quality = load_pbj_rows(input_dir)
        provider_rows, provider_quality = load_provider_info(Path(args.provider_info) if args.provider_info else None)
        snf_rows, snf_quality = load_snf_enrollments(Path(args.snf_enrollments) if args.snf_enrollments else None)
        quality_measures_rows, quality_measures_quality = load_quality_measures_claims(
            Path(args.quality_measures_claims) if args.quality_measures_claims else None
        )
        data = build_output(
            groups,
            facilities,
            quality,
            output_path,
            args.source_release,
            args.freshness_date,
            provider_rows,
            provider_quality,
            snf_rows,
            snf_quality,
            quality_measures_rows,
            quality_measures_quality,
        )
        errors = validate_output(data)
        if errors:
            for error in errors:
                print(f"VALIDATION ERROR: {error}", file=sys.stderr)
            return 1
        write_json(output_path, data)
        print(f"Wrote {output_path}")
        print(f"Facilities: {len(data['facilities'])}")
        print(f"Quarterly rows: {len(data['facility_quarterly_staffing'])}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
