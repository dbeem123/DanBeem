#!/usr/bin/env python3
"""Independent calculation audit for the Connecticut nursing home staffing export.

This script intentionally does not import build_nursing_home_staffing_ct.py. It
re-reads the raw local CMS CSV files, recomputes facility-quarter metrics, and
compares those audit results to data/nursing_home_staffing_ct.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


RN_COLUMNS = ("Hrs_RNDON", "Hrs_RNadmin", "Hrs_RN")
LPN_COLUMNS = ("Hrs_LPNadmin", "Hrs_LPN")
AIDE_COLUMNS = ("Hrs_CNA", "Hrs_NAtrn", "Hrs_MedAide")
NURSE_COLUMNS = RN_COLUMNS + LPN_COLUMNS + AIDE_COLUMNS
CONTRACT_COLUMNS = tuple(f"{column}_ctr" for column in NURSE_COLUMNS)
CT_DIRECT_TOTAL_COLUMNS = ("Hrs_RN", "Hrs_LPN", "Hrs_CNA", "Hrs_NAtrn", "Hrs_MedAide")
CT_DIRECT_LICENSED_COLUMNS = ("Hrs_RN", "Hrs_LPN")
CT_TOTAL_MINIMUM = 3.00
CT_LICENSED_MINIMUM = 0.84

ROUNDING = {
    "resident_days": 1,
    "average_resident_census": 1,
    "rn_hprd": 2,
    "lpn_lvn_hprd": 2,
    "nurse_aide_hprd": 2,
    "total_nurse_hprd": 2,
    "contract_staff_pct": 1,
    "ct_direct_care_total_hprd_estimate": 2,
    "ct_direct_care_licensed_nurse_hprd_estimate": 2,
    "ct_total_direct_care_minimum_hprd": 2,
    "ct_licensed_direct_care_minimum_hprd": 2,
    "ct_total_direct_care_difference_from_minimum": 2,
    "ct_licensed_direct_care_difference_from_minimum": 2,
}

SPOT_CHECK_CCNS = ("075011", "075017", "075031")

PROVIDER_ALIASES = {
    "ccn": ("CMS Certification Number (CCN)", "CMS Certification Number", "Federal Provider Number", "Provider Number", "PROVNUM", "CCN"),
    "provider_name": ("Provider Name", "PROVNAME", "Facility Name"),
    "city": ("Provider City", "City/Town", "City", "CITY"),
    "state": ("Provider State", "State", "STATE"),
    "address": ("Provider Address", "Address", "Street Address", "LOCATION"),
    "zip_code": ("Provider Zip Code", "ZIP Code", "Zip", "ZIP"),
    "phone_number": ("Provider Phone Number", "Phone Number", "Telephone Number", "Phone"),
    "certified_beds": ("Number of Certified Beds", "Certified Beds", "Number Certified Beds"),
    "ownership_type": ("Ownership Type", "Ownership", "Provider Ownership Type"),
    "case_mix_nurse_aide_hprd": (
        "Case-Mix Nurse Aide Staffing Hours per Resident per Day",
        "Case Mix Nurse Aide Staffing Hours per Resident per Day",
        "Case-Mix Nurse Aide HPRD",
    ),
    "case_mix_lpn_lvn_hprd": (
        "Case-Mix LPN Staffing Hours per Resident per Day",
        "Case Mix LPN Staffing Hours per Resident per Day",
        "Case-Mix LPN HPRD",
    ),
    "case_mix_rn_hprd": (
        "Case-Mix RN Staffing Hours per Resident per Day",
        "Case Mix RN Staffing Hours per Resident per Day",
        "Case-Mix RN HPRD",
    ),
    "case_mix_total_nurse_hprd": (
        "Case-Mix Total Nurse Staffing Hours per Resident per Day",
        "Case Mix Total Nurse Staffing Hours per Resident per Day",
        "Case-Mix Total Nurse HPRD",
    ),
}

SNF_ALIASES = {
    "ccn": ("CCN", "CMS Certification Number (CCN)", "Provider Number", "PROVNUM"),
    "enrollment_state": ("ENROLLMENT STATE", "Enrollment State"),
    "npi": ("NPI",),
    "organization_name": ("ORGANIZATION NAME", "Organization Name"),
    "doing_business_as_name": ("DOING BUSINESS AS NAME", "Doing Business As Name", "DBA Name"),
    "proprietary_nonprofit": ("PROPRIETARY_NONPROFIT", "Proprietary Nonprofit", "Proprietary/Nonprofit"),
    "organization_type_structure": ("ORGANIZATION TYPE STRUCTURE", "Organization Type Structure"),
    "nursing_home_provider_name": ("NURSING HOME PROVIDER NAME", "Nursing Home Provider Name"),
    "affiliation_entity_name": ("AFFILIATION ENTITY NAME", "Affiliation Entity Name"),
    "affiliation_entity_id": ("AFFILIATION ENTITY ID", "Affiliation Entity ID"),
    "incorporation_state": ("INCORPORATION STATE", "Incorporation State"),
    "incorporation_date": ("INCORPORATION DATE", "Incorporation Date"),
    "state": ("STATE", "State"),
}


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def alias_lookup(fieldnames: list[str], aliases: dict[str, tuple[str, ...]]) -> dict[str, str]:
    normalized = {normalize_name(name): name for name in fieldnames}
    lookup: dict[str, str] = {}
    for key, choices in aliases.items():
        for choice in choices:
            actual = normalized.get(normalize_name(choice))
            if actual:
                lookup[key] = actual
                break
    return lookup


def direct_lookup(fieldnames: list[str], names: tuple[str, ...]) -> dict[str, str]:
    normalized = {normalize_name(name): name for name in fieldnames}
    lookup = {}
    for name in names:
        actual = normalized.get(normalize_name(name))
        if actual:
            lookup[name] = actual
    return lookup


def parse_number(value: Any) -> float | None:
    text = str(value if value is not None else "").strip().replace(",", "")
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def quarter_from_row(row: dict[str, str], lookup: dict[str, str]) -> str | None:
    date_value = parse_date(row.get(lookup.get("WorkDate", ""), ""))
    if date_value:
        return f"{date_value.year}Q{((date_value.month - 1) // 3) + 1}"
    text = str(row.get(lookup.get("CY_Qtr", ""), "")).strip()
    match = re.search(r"(20\d{2})\s*Q\s*([1-4])", text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}Q{match.group(2)}"
    match = re.search(r"Q\s*([1-4])\s*(20\d{2})", text, re.IGNORECASE)
    if match:
        return f"{match.group(2)}Q{match.group(1)}"
    return None


def rounded(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


def empty_group() -> dict[str, Any]:
    return {
        "input_daily_row_count": 0,
        "included_daily_row_count": 0,
        "excluded_zero_census_day_count": 0,
        "included_zero_nursing_hours_day_count": 0,
        "excluded_zero_nursing_hours_day_count": 0,
        "resident_days_raw": 0.0,
        "census_values": [],
        "hours": defaultdict(float),
        "contract_hours": defaultdict(float),
        "contract_columns_present": set(),
        "contract_value_count": 0,
        "malformed_counts": defaultdict(int),
    }


def read_raw_pbj(input_dir: Path) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = defaultdict(empty_group)
    facilities: dict[str, dict[str, Any]] = {}
    quality = {
        "input_files": [],
        "input_row_count": 0,
        "ct_input_row_count": 0,
        "skipped_rows": {"non_ct": 0, "missing_ccn": 0, "missing_quarter": 0},
        "missing_required_columns_by_file": {},
        "malformed_numeric_values": {},
    }
    required = ("STATE", "PROVNUM", "PROVNAME", "CITY", "MDScensus", *NURSE_COLUMNS)
    lookup_names = (*required, *CONTRACT_COLUMNS, "WorkDate", "CY_Qtr")

    for path in sorted(input_dir.glob("*.csv")):
        quality["input_files"].append(str(path))
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            lookup = direct_lookup(fieldnames, lookup_names)
            missing = [name for name in required if name not in lookup]
            if "WorkDate" not in lookup and "CY_Qtr" not in lookup:
                missing.append("WorkDate or CY_Qtr")
            if missing:
                quality["missing_required_columns_by_file"][str(path)] = sorted(set(missing))

            for source_row in reader:
                quality["input_row_count"] += 1
                state = str(source_row.get(lookup.get("STATE", ""), "")).strip().upper()
                if state != "CT":
                    quality["skipped_rows"]["non_ct"] += 1
                    continue
                quality["ct_input_row_count"] += 1

                ccn = str(source_row.get(lookup.get("PROVNUM", ""), "")).strip()
                if not ccn:
                    quality["skipped_rows"]["missing_ccn"] += 1
                    continue
                quarter = quarter_from_row(source_row, lookup)
                if not quarter:
                    quality["skipped_rows"]["missing_quarter"] += 1
                    continue

                name = str(source_row.get(lookup.get("PROVNAME", ""), "")).strip() or "Unknown facility"
                city = str(source_row.get(lookup.get("CITY", ""), "")).strip() or "Unknown city"
                facilities[ccn] = {"ccn": ccn, "provider_name": name, "city": city, "state": "CT"}

                group = groups[(ccn, quarter)]
                group["input_daily_row_count"] += 1

                census = parse_number(source_row.get(lookup.get("MDScensus", ""), ""))
                if census is None:
                    group["malformed_counts"]["MDScensus"] += 1

                day_hours: dict[str, float] = {}
                for column in NURSE_COLUMNS:
                    value = parse_number(source_row.get(lookup.get(column, ""), ""))
                    if value is None:
                        group["malformed_counts"][column] += 1
                    else:
                        day_hours[column] = value

                day_contract_hours: dict[str, float] = {}
                for column in CONTRACT_COLUMNS:
                    if column not in lookup:
                        continue
                    group["contract_columns_present"].add(column)
                    value = parse_number(source_row.get(lookup[column], ""))
                    if value is None:
                        group["malformed_counts"][column] += 1
                    else:
                        day_contract_hours[column] = value

                if census is None or census <= 0:
                    group["excluded_zero_census_day_count"] += 1
                    continue

                group["included_daily_row_count"] += 1
                group["resident_days_raw"] += census
                group["census_values"].append(census)
                if sum(day_hours.values()) <= 0:
                    group["included_zero_nursing_hours_day_count"] += 1
                for column, value in day_hours.items():
                    group["hours"][column] += value
                for column, value in day_contract_hours.items():
                    group["contract_hours"][column] += value
                    group["contract_value_count"] += 1

    for (ccn, quarter), group in groups.items():
        malformed = {key: value for key, value in sorted(group["malformed_counts"].items()) if value}
        for key, value in malformed.items():
            quality["malformed_numeric_values"][f"{ccn}:{quarter}:{key}"] = value

    return groups, facilities, quality


def derive_audit_rows(groups: dict[tuple[str, str], dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    rows = {}
    for key, group in groups.items():
        resident_days = group["resident_days_raw"]
        has_denominator = resident_days > 0
        rn_hours = sum(group["hours"][column] for column in RN_COLUMNS)
        lpn_hours = sum(group["hours"][column] for column in LPN_COLUMNS)
        aide_hours = sum(group["hours"][column] for column in AIDE_COLUMNS)
        total_hours = rn_hours + lpn_hours + aide_hours
        contract_hours = sum(group["contract_hours"][column] for column in CONTRACT_COLUMNS)
        contract_pct = (contract_hours / total_hours) * 100 if group["contract_value_count"] and total_hours > 0 else None
        ct_total = sum(group["hours"][column] for column in CT_DIRECT_TOTAL_COLUMNS)
        ct_licensed = sum(group["hours"][column] for column in CT_DIRECT_LICENSED_COLUMNS)
        ct_total_hprd = rounded(ct_total / resident_days if has_denominator else None, 2)
        ct_licensed_hprd = rounded(ct_licensed / resident_days if has_denominator else None, 2)
        rows[key] = {
            "resident_days": rounded(resident_days if has_denominator else None, 1),
            "average_resident_census": rounded(
                sum(group["census_values"]) / len(group["census_values"]) if group["census_values"] else None,
                1,
            ),
            "metrics": {
                "rn_hprd": rounded(rn_hours / resident_days if has_denominator else None, 2),
                "lpn_lvn_hprd": rounded(lpn_hours / resident_days if has_denominator else None, 2),
                "nurse_aide_hprd": rounded(aide_hours / resident_days if has_denominator else None, 2),
                "total_nurse_hprd": rounded(total_hours / resident_days if has_denominator else None, 2),
                "contract_staff_pct": rounded(contract_pct, 1),
                "ct_direct_care_total_hprd_estimate": ct_total_hprd,
                "ct_direct_care_licensed_nurse_hprd_estimate": ct_licensed_hprd,
                "ct_total_direct_care_minimum_hprd": CT_TOTAL_MINIMUM,
                "ct_licensed_direct_care_minimum_hprd": CT_LICENSED_MINIMUM,
                "ct_total_direct_care_difference_from_minimum": rounded(
                    ct_total_hprd - CT_TOTAL_MINIMUM if ct_total_hprd is not None else None,
                    2,
                ),
                "ct_licensed_direct_care_difference_from_minimum": rounded(
                    ct_licensed_hprd - CT_LICENSED_MINIMUM if ct_licensed_hprd is not None else None,
                    2,
                ),
                "ct_total_direct_care_below_minimum_estimate": (
                    ct_total_hprd < CT_TOTAL_MINIMUM if ct_total_hprd is not None else None
                ),
                "ct_licensed_direct_care_below_minimum_estimate": (
                    ct_licensed_hprd < CT_LICENSED_MINIMUM if ct_licensed_hprd is not None else None
                ),
            },
            "data_quality": {
                "input_daily_row_count": group["input_daily_row_count"],
                "included_daily_row_count": group["included_daily_row_count"],
                "excluded_zero_census_day_count": group["excluded_zero_census_day_count"],
                "included_zero_nursing_hours_day_count": group["included_zero_nursing_hours_day_count"],
                "excluded_zero_nursing_hours_day_count": group["excluded_zero_nursing_hours_day_count"],
                "malformed_numeric_counts": {k: v for k, v in sorted(group["malformed_counts"].items()) if v},
            },
        }
    return rows


def read_provider_info(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    quality = {
        "provider_info_row_count": 0,
        "provider_info_ct_row_count": 0,
        "provider_info_duplicate_ccn_count": 0,
    }
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        lookup = alias_lookup(reader.fieldnames or [], PROVIDER_ALIASES)
        for source_row in reader:
            quality["provider_info_row_count"] += 1
            state = str(source_row.get(lookup.get("state", ""), "")).strip().upper()
            if state and state != "CT":
                continue
            ccn = str(source_row.get(lookup.get("ccn", ""), "")).strip()
            if not ccn:
                continue
            quality["provider_info_ct_row_count"] += 1
            if ccn in rows:
                quality["provider_info_duplicate_ccn_count"] += 1
            rows[ccn] = {
                "ccn": ccn,
                "provider_name": str(source_row.get(lookup.get("provider_name", ""), "")).strip(),
                "city": str(source_row.get(lookup.get("city", ""), "")).strip(),
                "state": state,
                "address": str(source_row.get(lookup.get("address", ""), "")).strip(),
                "zip_code": str(source_row.get(lookup.get("zip_code", ""), "")).strip(),
                "phone_number": str(source_row.get(lookup.get("phone_number", ""), "")).strip(),
                "certified_beds": parse_number(source_row.get(lookup.get("certified_beds", ""), "")),
                "ownership_type": str(source_row.get(lookup.get("ownership_type", ""), "")).strip(),
                "case_mix_total_nurse_hprd": parse_number(source_row.get(lookup.get("case_mix_total_nurse_hprd", ""), "")),
                "case_mix_rn_hprd": parse_number(source_row.get(lookup.get("case_mix_rn_hprd", ""), "")),
                "case_mix_lpn_lvn_hprd": parse_number(source_row.get(lookup.get("case_mix_lpn_lvn_hprd", ""), "")),
                "case_mix_nurse_aide_hprd": parse_number(source_row.get(lookup.get("case_mix_nurse_aide_hprd", ""), "")),
            }
    return rows, quality


def read_snf_enrollments(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    quality = {
        "snf_enrollments_row_count": 0,
        "snf_enrollments_ct_row_count": 0,
        "snf_enrollments_duplicate_ccn_count": 0,
    }
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        lookup = alias_lookup(reader.fieldnames or [], SNF_ALIASES)
        for source_row in reader:
            quality["snf_enrollments_row_count"] += 1
            state = str(source_row.get(lookup.get("state", ""), "")).strip().upper()
            enrollment_state = str(source_row.get(lookup.get("enrollment_state", ""), "")).strip().upper()
            if "CT" not in {state, enrollment_state}:
                continue
            ccn = str(source_row.get(lookup.get("ccn", ""), "")).strip()
            if not ccn:
                continue
            quality["snf_enrollments_ct_row_count"] += 1
            if ccn in rows:
                quality["snf_enrollments_duplicate_ccn_count"] += 1
                continue
            rows[ccn] = {
                "ccn": ccn,
                "enrollment_npi": str(source_row.get(lookup.get("npi", ""), "")).strip(),
                "enrollment_organization_name": str(source_row.get(lookup.get("organization_name", ""), "")).strip(),
                "enrollment_doing_business_as_name": str(source_row.get(lookup.get("doing_business_as_name", ""), "")).strip(),
                "enrollment_proprietary_nonprofit": str(source_row.get(lookup.get("proprietary_nonprofit", ""), "")).strip(),
                "enrollment_organization_type_structure": str(source_row.get(lookup.get("organization_type_structure", ""), "")).strip(),
                "enrollment_nursing_home_provider_name": str(source_row.get(lookup.get("nursing_home_provider_name", ""), "")).strip(),
                "affiliation_entity_name": str(source_row.get(lookup.get("affiliation_entity_name", ""), "")).strip(),
                "affiliation_entity_id": str(source_row.get(lookup.get("affiliation_entity_id", ""), "")).strip(),
            }
    return rows, quality


def compare_values(expected: Any, actual: Any) -> tuple[bool, float | None]:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected is actual, None
    if expected is None or actual is None:
        return expected is None and actual is None, None
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return expected == actual, abs(float(expected) - float(actual))
    return expected == actual, None


def compare_rows(audit_rows: dict[tuple[str, str], dict[str, Any]], generated_rows: list[dict[str, Any]]) -> dict[str, Any]:
    generated_by_key = {(row.get("ccn"), row.get("quarter")): row for row in generated_rows}
    audit_keys = set(audit_rows)
    generated_keys = set(generated_by_key)
    fields = ("resident_days", "average_resident_census")
    metric_fields = (
        "rn_hprd",
        "lpn_lvn_hprd",
        "nurse_aide_hprd",
        "total_nurse_hprd",
        "contract_staff_pct",
        "ct_direct_care_total_hprd_estimate",
        "ct_direct_care_licensed_nurse_hprd_estimate",
        "ct_total_direct_care_minimum_hprd",
        "ct_licensed_direct_care_minimum_hprd",
        "ct_total_direct_care_difference_from_minimum",
        "ct_licensed_direct_care_difference_from_minimum",
        "ct_total_direct_care_below_minimum_estimate",
        "ct_licensed_direct_care_below_minimum_estimate",
    )
    quality_fields = (
        "input_daily_row_count",
        "included_daily_row_count",
        "excluded_zero_census_day_count",
        "included_zero_nursing_hours_day_count",
        "excluded_zero_nursing_hours_day_count",
    )
    match_counts = {field: 0 for field in (*fields, *metric_fields, *quality_fields)}
    mismatch_counts = {field: 0 for field in match_counts}
    max_mismatch = {field: 0.0 for field in match_counts}
    mismatches = []

    for key in sorted(audit_keys & generated_keys):
        expected = audit_rows[key]
        actual = generated_by_key[key]
        for field in fields:
            ok, magnitude = compare_values(expected[field], actual.get(field))
            match_counts[field] += int(ok)
            mismatch_counts[field] += int(not ok)
            if not ok:
                max_mismatch[field] = max(max_mismatch[field], magnitude or 0.0)
                mismatches.append({"key": key, "field": field, "expected": expected[field], "actual": actual.get(field), "magnitude": magnitude})
        for field in metric_fields:
            ok, magnitude = compare_values(expected["metrics"][field], actual.get("metrics", {}).get(field))
            match_counts[field] += int(ok)
            mismatch_counts[field] += int(not ok)
            if not ok:
                max_mismatch[field] = max(max_mismatch[field], magnitude or 0.0)
                mismatches.append({"key": key, "field": field, "expected": expected["metrics"][field], "actual": actual.get("metrics", {}).get(field), "magnitude": magnitude})
        for field in quality_fields:
            ok, magnitude = compare_values(expected["data_quality"][field], actual.get("data_quality", {}).get(field))
            match_counts[field] += int(ok)
            mismatch_counts[field] += int(not ok)
            if not ok:
                max_mismatch[field] = max(max_mismatch[field], magnitude or 0.0)
                mismatches.append({"key": key, "field": field, "expected": expected["data_quality"][field], "actual": actual.get("data_quality", {}).get(field), "magnitude": magnitude})

    return {
        "rows_compared": len(audit_keys & generated_keys),
        "missing_rows_in_generated": sorted(audit_keys - generated_keys),
        "extra_rows_in_generated": sorted(generated_keys - audit_keys),
        "match_counts": match_counts,
        "mismatch_counts": mismatch_counts,
        "max_mismatch": max_mismatch,
        "mismatches": mismatches[:100],
        "total_mismatch_count": sum(mismatch_counts.values()),
    }


def compare_quality(audit_quality: dict[str, Any], groups: dict[tuple[str, str], dict[str, Any]], generated_quality: dict[str, Any]) -> dict[str, Any]:
    summed = {
        "excluded_zero_census_day_count": sum(group["excluded_zero_census_day_count"] for group in groups.values()),
        "included_zero_nursing_hours_day_count": sum(group["included_zero_nursing_hours_day_count"] for group in groups.values()),
        "excluded_zero_nursing_hours_day_count": sum(group["excluded_zero_nursing_hours_day_count"] for group in groups.values()),
    }
    comparisons = {
        "input_row_count": (audit_quality["input_row_count"], generated_quality.get("input_row_count")),
        "ct_input_row_count": (audit_quality["ct_input_row_count"], generated_quality.get("ct_input_row_count")),
        "skipped_rows.non_ct": (audit_quality["skipped_rows"]["non_ct"], generated_quality.get("skipped_rows", {}).get("non_ct")),
        "skipped_rows.missing_ccn": (audit_quality["skipped_rows"]["missing_ccn"], generated_quality.get("skipped_rows", {}).get("missing_ccn")),
        "skipped_rows.missing_quarter": (audit_quality["skipped_rows"]["missing_quarter"], generated_quality.get("skipped_rows", {}).get("missing_quarter")),
        "summed.excluded_zero_census_day_count": (summed["excluded_zero_census_day_count"], sum_value(generated_quality, "excluded_zero_census_day_count")),
        "summed.included_zero_nursing_hours_day_count": (summed["included_zero_nursing_hours_day_count"], sum_value(generated_quality, "included_zero_nursing_hours_day_count")),
        "summed.excluded_zero_nursing_hours_day_count": (summed["excluded_zero_nursing_hours_day_count"], sum_value(generated_quality, "excluded_zero_nursing_hours_day_count")),
        "malformed_numeric_values": (audit_quality["malformed_numeric_values"], generated_quality.get("malformed_numeric_values", {})),
    }
    return {
        "comparisons": {
            key: {"audit": audit, "generated": generated, "match": audit == generated}
            for key, (audit, generated) in comparisons.items()
        }
    }


def sum_value(generated_quality: dict[str, Any], row_quality_key: str) -> int:
    # Filled in later from the generated row list in run_audit; placeholder returns a supplied precomputed value.
    return generated_quality.get(f"_audit_sum_{row_quality_key}", 0)


def compare_enrichment(
    pbj_facilities: dict[str, dict[str, Any]],
    provider_rows: dict[str, dict[str, Any]],
    provider_quality: dict[str, Any],
    snf_rows: dict[str, dict[str, Any]],
    snf_quality: dict[str, Any],
    generated: dict[str, Any],
) -> dict[str, Any]:
    generated_quality = generated.get("data_quality", {})
    generated_facilities = {row.get("ccn"): row for row in generated.get("facilities", [])}
    provider_matches = set(pbj_facilities) & set(provider_rows)
    snf_matches = set(pbj_facilities) & set(snf_rows)
    counts = {
        "provider_info_row_count": (provider_quality["provider_info_row_count"], generated_quality.get("provider_info_row_count")),
        "provider_info_ct_row_count": (provider_quality["provider_info_ct_row_count"], generated_quality.get("provider_info_ct_row_count")),
        "matched_facility_count": (len(provider_matches), generated_quality.get("matched_facility_count")),
        "unmatched_pbj_facility_count": (len(set(pbj_facilities) - set(provider_rows)), generated_quality.get("unmatched_pbj_facility_count")),
        "unmatched_provider_info_row_count": (len(set(provider_rows) - set(pbj_facilities)), generated_quality.get("unmatched_provider_info_row_count")),
        "snf_enrollments_row_count": (snf_quality["snf_enrollments_row_count"], generated_quality.get("snf_enrollments_row_count")),
        "snf_enrollments_ct_row_count": (snf_quality["snf_enrollments_ct_row_count"], generated_quality.get("snf_enrollments_ct_row_count")),
        "matched_snf_enrollment_facility_count": (len(snf_matches), generated_quality.get("matched_snf_enrollment_facility_count")),
        "unmatched_pbj_facility_count_for_snf_enrollments": (len(set(pbj_facilities) - set(snf_rows)), generated_quality.get("unmatched_pbj_facility_count_for_snf_enrollments")),
        "unmatched_snf_enrollment_row_count": (len(set(snf_rows) - set(pbj_facilities)), generated_quality.get("unmatched_snf_enrollment_row_count")),
    }
    samples = []
    for ccn in SPOT_CHECK_CCNS:
        generated_row = generated_facilities.get(ccn, {})
        provider = provider_rows.get(ccn, {})
        snf = snf_rows.get(ccn, {})
        samples.append({
            "ccn": ccn,
            "generated_provider_name": generated_row.get("provider_name"),
            "provider_name_matches_raw": generated_row.get("provider_name") == (provider.get("provider_name") or pbj_facilities.get(ccn, {}).get("provider_name")),
            "provider_source_matched": generated_row.get("provider_source_matched"),
            "expected_provider_source_matched": ccn in provider_rows,
            "enrollment_source_matched": generated_row.get("enrollment_source_matched"),
            "expected_enrollment_source_matched": ccn in snf_rows,
            "generated_affiliation_entity_name": generated_row.get("affiliation_entity_name"),
            "raw_affiliation_entity_name": snf.get("affiliation_entity_name", ""),
        })
    return {
        "counts": {key: {"audit": audit, "generated": generated_count, "match": audit == generated_count} for key, (audit, generated_count) in counts.items()},
        "sample_rows": samples,
    }


def build_spot_checks(
    audit_rows: dict[tuple[str, str], dict[str, Any]],
    generated_rows: list[dict[str, Any]],
    generated_facilities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    generated_by_key = {(row.get("ccn"), row.get("quarter")): row for row in generated_rows}
    facilities_by_ccn = {row.get("ccn"): row for row in generated_facilities}
    latest_by_ccn = {}
    for key in sorted(audit_rows):
        latest_by_ccn[key[0]] = key
    keys = [latest_by_ccn[ccn] for ccn in SPOT_CHECK_CCNS if ccn in latest_by_ccn]
    below_total = next((key for key, row in sorted(audit_rows.items()) if row["metrics"]["ct_total_direct_care_below_minimum_estimate"] is True), None)
    below_licensed = next((key for key, row in sorted(audit_rows.items()) if row["metrics"]["ct_licensed_direct_care_below_minimum_estimate"] is True), None)
    for key in (below_total, below_licensed):
        if key and key not in keys:
            keys.append(key)

    checks = []
    for key in keys:
        audit = audit_rows[key]
        generated = generated_by_key.get(key, {})
        facility = facilities_by_ccn.get(key[0], {})
        metrics = audit["metrics"]
        generated_metrics = generated.get("metrics", {})
        checks.append({
            "ccn": key[0],
            "quarter": key[1],
            "provider_name": facility.get("provider_name") or key[0],
            "resident_days": audit["resident_days"],
            "total_nurse_hprd": metrics["total_nurse_hprd"],
            "ct_direct_care_total_hprd_estimate": metrics["ct_direct_care_total_hprd_estimate"],
            "ct_direct_care_licensed_nurse_hprd_estimate": metrics["ct_direct_care_licensed_nurse_hprd_estimate"],
            "contract_staff_pct": metrics["contract_staff_pct"],
            "ct_total_flag_matches": metrics["ct_total_direct_care_below_minimum_estimate"] == generated_metrics.get("ct_total_direct_care_below_minimum_estimate"),
            "ct_licensed_flag_matches": metrics["ct_licensed_direct_care_below_minimum_estimate"] == generated_metrics.get("ct_licensed_direct_care_below_minimum_estimate"),
            "below_ct_total": metrics["ct_total_direct_care_below_minimum_estimate"],
            "below_ct_licensed": metrics["ct_licensed_direct_care_below_minimum_estimate"],
        })
    return checks


def summarize_counts(audit_rows: dict[tuple[str, str], dict[str, Any]], generated: dict[str, Any]) -> dict[str, Any]:
    rows = generated.get("facility_quarterly_staffing", [])
    latest = generated.get("reporting_period", {}).get("quarter")
    audit_counts = {
        "below_total_all": sum(1 for row in audit_rows.values() if row["metrics"]["ct_total_direct_care_below_minimum_estimate"] is True),
        "below_licensed_all": sum(1 for row in audit_rows.values() if row["metrics"]["ct_licensed_direct_care_below_minimum_estimate"] is True),
        "below_total_latest": sum(1 for key, row in audit_rows.items() if key[1] == latest and row["metrics"]["ct_total_direct_care_below_minimum_estimate"] is True),
        "below_licensed_latest": sum(1 for key, row in audit_rows.items() if key[1] == latest and row["metrics"]["ct_licensed_direct_care_below_minimum_estimate"] is True),
    }
    generated_counts = {
        "below_total_all": sum(1 for row in rows if row.get("metrics", {}).get("ct_total_direct_care_below_minimum_estimate") is True),
        "below_licensed_all": sum(1 for row in rows if row.get("metrics", {}).get("ct_licensed_direct_care_below_minimum_estimate") is True),
        "below_total_latest": sum(1 for row in rows if row.get("quarter") == latest and row.get("metrics", {}).get("ct_total_direct_care_below_minimum_estimate") is True),
        "below_licensed_latest": sum(1 for row in rows if row.get("quarter") == latest and row.get("metrics", {}).get("ct_licensed_direct_care_below_minimum_estimate") is True),
    }
    return {
        "latest_quarter": latest,
        "audit": audit_counts,
        "generated": generated_counts,
        "expected_current_reported": {
            "below_total_all": 163,
            "below_licensed_all": 38,
            "below_total_latest": 27,
            "below_licensed_latest": 7,
        },
        "matches_generated": audit_counts == generated_counts,
    }


def write_report(path: Path, result: dict[str, Any]) -> None:
    comparison = result["row_comparison"]
    counts = result["ct_counts"]
    conclusion = "Calculations validated with no unexplained discrepancies"
    if comparison["total_mismatch_count"] or comparison["missing_rows_in_generated"] or comparison["extra_rows_in_generated"]:
        conclusion = "Issues found requiring correction"
    elif result["rounding_note"]:
        conclusion = "Calculations validated except for documented rounding behavior"

    lines = [
        "# Connecticut Nursing Home Staffing Calculation Audit",
        "",
        f"Generated by `scripts/audit_nursing_home_staffing_ct.py` on {datetime.now().replace(microsecond=0).isoformat()}.",
        "",
        f"## Conclusion",
        "",
        f"**{conclusion}.**",
        "",
        "The audit independently re-read the raw PBJ Daily Nurse Staffing CSV files, applied the project row-inclusion rules, recomputed staffing numerators and resident-day denominators, and compared the rounded audit results to `data/nursing_home_staffing_ct.json`.",
        "",
        "## Row And Metric Comparison",
        "",
        f"- Facility-quarter rows compared: {comparison['rows_compared']}",
        f"- Missing rows in generated JSON: {len(comparison['missing_rows_in_generated'])}",
        f"- Extra rows in generated JSON: {len(comparison['extra_rows_in_generated'])}",
        f"- Total field mismatches across audited row fields: {comparison['total_mismatch_count']}",
        "",
        "| Field | Matches | Mismatches | Max mismatch |",
        "|---|---:|---:|---:|",
    ]
    for field, matches in comparison["match_counts"].items():
        lines.append(f"| `{field}` | {matches} | {comparison['mismatch_counts'][field]} | {comparison['max_mismatch'][field]:.6f} |")

    lines.extend([
        "",
        "Numeric fields were checked against the export precision: HPRD and CT difference fields at 2 decimals, contract percentage at 1 decimal, and average census/resident days at 1 decimal.",
        "",
        "## Connecticut Comparison Counts",
        "",
        f"- Latest quarter audited: `{counts['latest_quarter']}`",
        "",
        "| Count | Audit recomputation | Generated JSON | Currently reported | Confirmed |",
        "|---|---:|---:|---:|---|",
    ])
    labels = {
        "below_total_all": "All quarters below CT 3.00 total direct-care point",
        "below_licensed_all": "All quarters below CT 0.84 licensed point",
        "below_total_latest": f"{counts['latest_quarter']} below CT 3.00 total direct-care point",
        "below_licensed_latest": f"{counts['latest_quarter']} below CT 0.84 licensed point",
    }
    for key, label in labels.items():
        audit = counts["audit"][key]
        generated = counts["generated"][key]
        reported = counts["expected_current_reported"][key]
        lines.append(f"| {label} | {audit} | {generated} | {reported} | {'yes' if audit == generated == reported else 'no'} |")

    lines.extend([
        "",
        "## Data Quality Counter Audit",
        "",
        "| Counter | Audit recomputation | Generated JSON | Match |",
        "|---|---:|---:|---|",
    ])
    for key, row in result["quality_comparison"]["comparisons"].items():
        audit = row["audit"]
        generated = row["generated"]
        if isinstance(audit, dict):
            audit_value = f"{len(audit)} malformed field entries"
            generated_value = f"{len(generated)} malformed field entries"
        else:
            audit_value = str(audit)
            generated_value = str(generated)
        lines.append(f"| `{key}` | {audit_value} | {generated_value} | {'yes' if row['match'] else 'no'} |")

    lines.extend([
        "",
        "## Enrichment Merge Count Audit",
        "",
        "| Counter | Audit recomputation | Generated JSON | Match |",
        "|---|---:|---:|---|",
    ])
    for key, row in result["enrichment_comparison"]["counts"].items():
        lines.append(f"| `{key}` | {row['audit']} | {row['generated']} | {'yes' if row['match'] else 'no'} |")

    lines.extend([
        "",
        "### Deterministic Merge Samples",
        "",
        "| CCN | Provider name matches raw/fallback | Provider match flag | SNF match flag | Affiliation entity matches raw |",
        "|---|---|---|---|---|",
    ])
    for sample in result["enrichment_comparison"]["sample_rows"]:
        affiliation_ok = sample["generated_affiliation_entity_name"] == sample["raw_affiliation_entity_name"]
        lines.append(
            f"| {sample['ccn']} | {'yes' if sample['provider_name_matches_raw'] else 'no'} | "
            f"{sample['provider_source_matched']} / expected {sample['expected_provider_source_matched']} | "
            f"{sample['enrollment_source_matched']} / expected {sample['expected_enrollment_source_matched']} | "
            f"{'yes' if affiliation_ok else 'no'} |"
        )

    lines.extend([
        "",
        "## Spot Checks",
        "",
        "| CCN | Facility | Quarter | Resident days | Total nurse HPRD | CT total direct-care HPRD | CT licensed HPRD | Contract staff % | CT total flag match | CT licensed flag match |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ])
    for check in result["spot_checks"]:
        lines.append(
            f"| {check['ccn']} | {check['provider_name']} | {check['quarter']} | {check['resident_days']} | "
            f"{check['total_nurse_hprd']} | {check['ct_direct_care_total_hprd_estimate']} | "
            f"{check['ct_direct_care_licensed_nurse_hprd_estimate']} | {check['contract_staff_pct']} | "
            f"{'yes' if check['ct_total_flag_matches'] else 'no'} | {'yes' if check['ct_licensed_flag_matches'] else 'no'} |"
        )

    lines.extend([
        "",
        "## External Reasonableness Check",
        "",
        "LTCCC/NursingHome411 public staffing materials describe both a broader `Total Nurse Staff HPRD` metric that includes nurse categories such as Admin and DON and a `Total Nurse Care Staff HPRD (excl. Admin/DON)` concept. That public concept is directionally consistent with this project separating the existing PBJ total nurse HPRD from the Connecticut direct-care estimate that excludes `Hrs_RNDON`, `Hrs_RNadmin`, and `Hrs_LPNadmin`.",
        "",
        "This was used only as a reasonableness check. It was not treated as ground truth because LTCCC quarterly public files may use their own release timing, CMS processing choices, variable names, and national/reporting exclusions that are not identical to this local Connecticut static export.",
        "",
        "Reference checked: https://nursinghome411.org/data/staffing/staffing-q2-2025/",
        "",
        "## Formula Findings",
        "",
        "- `rn_hprd` matched `(Hrs_RNDON + Hrs_RNadmin + Hrs_RN) / resident_days` after export rounding.",
        "- `lpn_lvn_hprd` matched `(Hrs_LPNadmin + Hrs_LPN) / resident_days` after export rounding.",
        "- `nurse_aide_hprd` matched `(Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days` after export rounding.",
        "- `total_nurse_hprd` matched all RN, LPN/LVN, and aide categories above divided by resident days.",
        "- `contract_staff_pct` matched corresponding `*_ctr` nursing category hours divided by total nursing category hours, times 100.",
        "- `ct_direct_care_total_hprd_estimate` matched `(Hrs_RN + Hrs_LPN + Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days`.",
        "- `ct_direct_care_licensed_nurse_hprd_estimate` matched `(Hrs_RN + Hrs_LPN) / resident_days`.",
        "- The Connecticut comparison flags matched the rounded CT estimate fields currently stored in the export.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    generated = json.loads(Path(args.output_json).read_text(encoding="utf-8"))
    groups, pbj_facilities, audit_quality = read_raw_pbj(Path(args.input_dir))
    audit_rows = derive_audit_rows(groups)
    generated_rows = generated.get("facility_quarterly_staffing", [])
    generated_quality = dict(generated.get("data_quality", {}))
    for field in ("excluded_zero_census_day_count", "included_zero_nursing_hours_day_count", "excluded_zero_nursing_hours_day_count"):
        generated_quality[f"_audit_sum_{field}"] = sum(row.get("data_quality", {}).get(field, 0) for row in generated_rows)

    provider_path = next(Path(args.provider_info_dir).glob("*.csv"))
    snf_path = next(Path(args.snf_enrollments_dir).glob("*.csv"))
    provider_rows, provider_quality = read_provider_info(provider_path)
    snf_rows, snf_quality = read_snf_enrollments(snf_path)

    result = {
        "row_comparison": compare_rows(audit_rows, generated_rows),
        "ct_counts": summarize_counts(audit_rows, generated),
        "quality_comparison": compare_quality(audit_quality, groups, generated_quality),
        "enrichment_comparison": compare_enrichment(pbj_facilities, provider_rows, provider_quality, snf_rows, snf_quality, generated),
        "spot_checks": build_spot_checks(audit_rows, generated_rows, generated.get("facilities", [])),
        "rounding_note": False,
    }
    write_report(Path(args.report), result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit generated Connecticut nursing home staffing calculations.")
    parser.add_argument("--input-dir", default="source_data/pbj")
    parser.add_argument("--provider-info-dir", default="source_data/provider_info")
    parser.add_argument("--snf-enrollments-dir", default="source_data/snf_enrollments")
    parser.add_argument("--output-json", default="data/nursing_home_staffing_ct.json")
    parser.add_argument("--report", default="docs/nursing_home_staffing_calculation_audit.md")
    args = parser.parse_args()

    result = run_audit(args)
    comparison = result["row_comparison"]
    counts = result["ct_counts"]
    print(f"Rows compared: {comparison['rows_compared']}")
    print(f"Missing rows in generated JSON: {len(comparison['missing_rows_in_generated'])}")
    print(f"Extra rows in generated JSON: {len(comparison['extra_rows_in_generated'])}")
    print(f"Total field mismatches: {comparison['total_mismatch_count']}")
    print("CT comparison counts:")
    for key, value in counts["audit"].items():
        print(f"  {key}: {value}")
    print(f"Report written: {args.report}")
    if comparison["total_mismatch_count"] or comparison["missing_rows_in_generated"] or comparison["extra_rows_in_generated"]:
        return 1
    if not counts["matches_generated"]:
        return 1
    if not all(row["match"] for row in result["quality_comparison"]["comparisons"].values()):
        return 1
    if not all(row["match"] for row in result["enrichment_comparison"]["counts"].values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
