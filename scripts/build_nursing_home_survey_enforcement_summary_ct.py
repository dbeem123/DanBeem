"""Build the compact Connecticut facility-level survey/enforcement summary.

This builder reads only current staffing and the three audited production runtime
JSON files. It does not read raw CMS source files or modify public UI assets.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


STAFFING_PATH = Path("data/nursing_home_staffing_ct.json")
HEALTH_PATH = Path("data/nursing_home_health_deficiencies_ct.json")
FIRE_PATH = Path("data/nursing_home_fire_safety_deficiencies_ct.json")
PENALTIES_PATH = Path("data/nursing_home_penalties_ct.json")
OUTPUT_PATH = Path("data/nursing_home_survey_enforcement_summary_ct.json")

SOURCE_PATHS = [STAFFING_PATH, HEALTH_PATH, FIRE_PATH, PENALTIES_PATH]

GLOBAL_LIMITATIONS = [
    "Summary counts reflect the available rolling source files and are not complete lifetime histories.",
    "Citation counts provide context and are not a complete quality measure.",
    "Fine amounts and payment denials are enforcement values, not quality scores.",
    "No composite quality score or facility ranking is calculated.",
    "Staffing measures remain separate from survey and enforcement measures.",
    "Health F-tag harm/immediate-jeopardy grouping is not applied to fire safety or emergency preparedness rows.",
    "The CMS citation-description lookup has documented gaps for K-0211 and K-0133.",
    "Duplicate penalty source rows are preserved and flagged in the detailed penalties runtime file.",
    "County name is unavailable in the current staffing facility records and is null in this summary.",
    "This summary is not automatically wired into the public UI.",
]

FACILITY_LIMITATION_CODES = [
    "available_source_windows_only",
    "citation_counts_are_context_only",
    "enforcement_values_are_not_quality_scores",
    "no_composite_quality_score",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required input file is missing: {path.as_posix()}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path.as_posix()}")
    return data


def require_rows(data: dict[str, Any], key: str, path: Path) -> list[dict[str, Any]]:
    rows = data.get(key)
    if not isinstance(rows, list):
        raise ValueError(f"Expected {key!r} array in {path.as_posix()}")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"Expected every {key!r} item to be an object in {path.as_posix()}")
    return rows


def validate_ccn(value: Any, *, source: str) -> str:
    ccn = str(value or "").strip()
    if len(ccn) != 6 or not ccn.isdigit():
        raise ValueError(f"Invalid CCN {value!r} in {source}; expected a six-digit string")
    return ccn


def validate_iso_date(value: Any, *, field: str, source: str) -> str:
    text = str(value or "").strip()
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Invalid required {field} {value!r} in {source}") from exc
    return text


def calendar_years_before(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)


def grouped_by_ccn(rows: list[dict[str, Any]], *, source: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[validate_ccn(row.get("ccn"), source=source)].append(row)
    return dict(grouped)


def date_range(rows: list[dict[str, Any]], field: str, *, source: str) -> dict[str, str | None]:
    values = [validate_iso_date(row[field], field=field, source=source) for row in rows if row.get(field)]
    return {
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def numeric_value(value: Any, *, field: str, source: str) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, bool):
        raise ValueError(f"Invalid numeric {field} {value!r} in {source}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric {field} {value!r} in {source}") from exc


def integer_value(value: Any, *, field: str, source: str) -> int:
    number = numeric_value(value, field=field, source=source)
    if not number.is_integer():
        raise ValueError(f"Expected integer {field}, found {value!r} in {source}")
    return int(number)


def recent_rows(rows: list[dict[str, Any]], field: str, start: str, end: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get(field) and start <= str(row[field]) <= end]


def sum_fines(rows: list[dict[str, Any]]) -> float:
    return round(
        sum(
            numeric_value(row.get("normalized_fine_amount"), field="normalized_fine_amount", source="penalties")
            for row in rows
            if row.get("enforcement_category") == "fine"
        ),
        2,
    )


def sum_denial_days(rows: list[dict[str, Any]]) -> int:
    return sum(
        integer_value(row.get("payment_denial_length_days"), field="payment_denial_length_days", source="penalties")
        for row in rows
        if row.get("enforcement_category") == "payment_denial"
    )


def build_summary() -> tuple[dict[str, Any], dict[str, Any]]:
    staffing_data = load_json(STAFFING_PATH)
    health_data = load_json(HEALTH_PATH)
    fire_data = load_json(FIRE_PATH)
    penalties_data = load_json(PENALTIES_PATH)

    staffing_rows = require_rows(staffing_data, "facilities", STAFFING_PATH)
    health_rows = require_rows(health_data, "deficiencies", HEALTH_PATH)
    fire_rows = require_rows(fire_data, "deficiencies", FIRE_PATH)
    penalty_rows = require_rows(penalties_data, "penalties", PENALTIES_PATH)

    staffing_by_ccn: dict[str, dict[str, Any]] = {}
    for row in staffing_rows:
        ccn = validate_ccn(row.get("ccn"), source=STAFFING_PATH.as_posix())
        if ccn in staffing_by_ccn:
            raise ValueError(f"Duplicate current staffing CCN: {ccn}")
        staffing_by_ccn[ccn] = row

    health_by_ccn = grouped_by_ccn(health_rows, source=HEALTH_PATH.as_posix())
    fire_by_ccn = grouped_by_ccn(fire_rows, source=FIRE_PATH.as_posix())
    penalty_by_ccn = grouped_by_ccn(penalty_rows, source=PENALTIES_PATH.as_posix())

    current_ccns = set(staffing_by_ccn)
    source_ccn_sets = {
        "health_deficiencies": set(health_by_ccn),
        "fire_safety_deficiencies": set(fire_by_ccn),
        "penalties": set(penalty_by_ccn),
    }
    join_coverage = {
        name: {
            "unique_source_ccn_count": len(ccns),
            "joined_current_ccn_count": len(ccns & current_ccns),
            "unmatched_source_ccn_count": len(ccns - current_ccns),
            "unmatched_source_ccns": sorted(ccns - current_ccns),
        }
        for name, ccns in source_ccn_sets.items()
    }

    health_range = date_range(health_rows, "survey_date", source=HEALTH_PATH.as_posix())
    fire_range = date_range(fire_rows, "survey_date", source=FIRE_PATH.as_posix())
    penalty_range = date_range(penalty_rows, "penalty_date", source=PENALTIES_PATH.as_posix())
    maximum_dates = [
        value
        for value in (health_range["max"], fire_range["max"], penalty_range["max"])
        if value is not None
    ]
    if not maximum_dates:
        raise ValueError("Cannot define recent window because all three source datasets have no dates")
    anchor_date = max(maximum_dates)
    recent_start = calendar_years_before(date.fromisoformat(anchor_date), 3).isoformat()

    facilities: list[dict[str, Any]] = []
    for ccn, staffing in staffing_by_ccn.items():
        health = health_by_ccn.get(ccn, [])
        fire = fire_by_ccn.get(ccn, [])
        penalties = penalty_by_ccn.get(ccn, [])
        health_recent = recent_rows(health, "survey_date", recent_start, anchor_date)
        fire_recent = recent_rows(fire, "survey_date", recent_start, anchor_date)
        penalties_recent = recent_rows(penalties, "penalty_date", recent_start, anchor_date)

        health_actual_harm = [row for row in health if row.get("harm_ij_group") == "actual_harm_not_ij"]
        health_ij = [row for row in health if row.get("harm_ij_group") == "immediate_jeopardy"]
        recent_actual_harm = [
            row for row in health_recent if row.get("harm_ij_group") == "actual_harm_not_ij"
        ]
        recent_ij = [row for row in health_recent if row.get("harm_ij_group") == "immediate_jeopardy"]
        fire_k = [row for row in fire if row.get("deficiency_prefix") == "K"]
        fire_e = [row for row in fire if row.get("deficiency_prefix") == "E"]
        recent_fire_k = [row for row in fire_recent if row.get("deficiency_prefix") == "K"]
        recent_fire_e = [row for row in fire_recent if row.get("deficiency_prefix") == "E"]
        fines = [row for row in penalties if row.get("enforcement_category") == "fine"]
        denials = [row for row in penalties if row.get("enforcement_category") == "payment_denial"]
        recent_fines = [row for row in penalties_recent if row.get("enforcement_category") == "fine"]
        recent_denials = [
            row for row in penalties_recent if row.get("enforcement_category") == "payment_denial"
        ]

        flags: list[str] = []
        if health_actual_harm:
            flags.append("health_actual_harm_records_present")
        if health_ij:
            flags.append("health_immediate_jeopardy_records_present")
        if any(not row.get("citation_description_lookup_matched") for row in fire):
            flags.append("fire_citation_description_lookup_gap_present")
        if any(row.get("duplicate_full_row_signature") for row in penalties):
            flags.append("duplicate_penalty_source_rows_preserved")
        if not health and not fire and not penalties:
            flags.append("no_survey_or_enforcement_records_in_available_sources")

        provider_name = str(staffing.get("provider_name") or "").strip()
        if not provider_name:
            raise ValueError(f"Missing current provider name for CCN {ccn}")

        facilities.append(
            {
                "ccn": ccn,
                "provider_name": provider_name,
                "city": str(staffing.get("city") or "").strip() or None,
                "county_name": str(staffing.get("county_name") or "").strip() or None,
                "has_health_deficiency_records": bool(health),
                "has_fire_safety_records": bool(fire),
                "has_penalty_records": bool(penalties),
                "latest_health_survey_date": max((row["survey_date"] for row in health), default=None),
                "latest_fire_safety_survey_date": max((row["survey_date"] for row in fire), default=None),
                "latest_penalty_date": max((row["penalty_date"] for row in penalties), default=None),
                "all_time_health_deficiency_count": len(health),
                "all_time_actual_harm_count": len(health_actual_harm),
                "all_time_immediate_jeopardy_count": len(health_ij),
                "all_time_fire_safety_citation_count": len(fire_k),
                "all_time_emergency_preparedness_citation_count": len(fire_e),
                "all_time_enforcement_event_count": len(penalties),
                "all_time_fine_count": len(fines),
                "all_time_fine_total": sum_fines(fines),
                "all_time_payment_denial_count": len(denials),
                "all_time_payment_denial_days": sum_denial_days(denials),
                "recent_health_deficiency_count": len(health_recent),
                "recent_actual_harm_count": len(recent_actual_harm),
                "recent_immediate_jeopardy_count": len(recent_ij),
                "recent_fire_safety_citation_count": len(recent_fire_k),
                "recent_emergency_preparedness_citation_count": len(recent_fire_e),
                "recent_enforcement_event_count": len(penalties_recent),
                "recent_fine_count": len(recent_fines),
                "recent_fine_total": sum_fines(recent_fines),
                "recent_payment_denial_count": len(recent_denials),
                "recent_payment_denial_days": sum_denial_days(recent_denials),
                "survey_enforcement_caution_flags": flags,
                "summary_limitations": FACILITY_LIMITATION_CODES,
            }
        )

    facilities.sort(key=lambda row: (row["provider_name"].casefold(), row["ccn"]))
    if len(facilities) != len(staffing_rows):
        raise ValueError(
            f"Summary row count {len(facilities)} does not match current facility count {len(staffing_rows)}"
        )
    summary_ccns = {row["ccn"] for row in facilities}
    if summary_ccns != current_ccns:
        raise ValueError("Summary CCNs do not exactly match current staffing CCNs")

    metadata = {
        "source_files": [path.as_posix() for path in SOURCE_PATHS],
        "build_date": date.today().isoformat(),
        "current_facility_count": len(staffing_rows),
        "summary_record_count": len(facilities),
        "health_deficiency_row_count": len(health_rows),
        "fire_safety_deficiency_row_count": len(fire_rows),
        "penalties_row_count": len(penalty_rows),
        "health_unique_ccn_count": len(health_by_ccn),
        "fire_safety_unique_ccn_count": len(fire_by_ccn),
        "penalties_unique_ccn_count": len(penalty_by_ccn),
        "source_date_ranges": {
            "health_survey_dates": health_range,
            "fire_safety_survey_dates": fire_range,
            "penalty_dates": penalty_range,
        },
        "recent_window_definition": {
            "anchor_date": anchor_date,
            "start_date": recent_start,
            "end_date": anchor_date,
            "inclusive": True,
            "duration": "three calendar years",
            "anchor_basis": "Maximum event or survey date across the three detailed runtime datasets.",
        },
        "source_join_coverage": join_coverage,
        "fire_safety_citation_lookup_gaps": {"K-0133": 2, "K-0211": 143},
        "limitations": GLOBAL_LIMITATIONS,
    }

    all_time_keys = [
        "all_time_health_deficiency_count",
        "all_time_actual_harm_count",
        "all_time_immediate_jeopardy_count",
        "all_time_fire_safety_citation_count",
        "all_time_emergency_preparedness_citation_count",
        "all_time_enforcement_event_count",
        "all_time_fine_count",
        "all_time_fine_total",
        "all_time_payment_denial_count",
        "all_time_payment_denial_days",
    ]
    recent_keys = [key.replace("all_time_", "recent_") for key in all_time_keys]
    validation = {
        "current_facility_count": len(staffing_rows),
        "summary_record_count": len(facilities),
        "join_coverage": join_coverage,
        "recent_window_start": recent_start,
        "recent_window_end": anchor_date,
        "all_time_totals": {
            key: round(sum(row[key] for row in facilities), 2) for key in all_time_keys
        },
        "recent_totals": {
            key: round(sum(row[key] for row in facilities), 2) for key in recent_keys
        },
        "facilities_with_health_records": sum(row["has_health_deficiency_records"] for row in facilities),
        "facilities_with_fire_safety_records": sum(row["has_fire_safety_records"] for row in facilities),
        "facilities_with_penalty_records": sum(row["has_penalty_records"] for row in facilities),
        "facilities_with_no_records": sum(
            not row["has_health_deficiency_records"]
            and not row["has_fire_safety_records"]
            and not row["has_penalty_records"]
            for row in facilities
        ),
    }
    return {"metadata": metadata, "facilities": facilities}, validation


def print_validation(validation: dict[str, Any]) -> None:
    print(f"Current facilities: {validation['current_facility_count']}")
    print(f"Summary records: {validation['summary_record_count']}")
    print(
        "Recent window: "
        f"{validation['recent_window_start']} through {validation['recent_window_end']} (inclusive)"
    )
    print("Join coverage:")
    for source, coverage in validation["join_coverage"].items():
        print(
            f"  {source}: {coverage['joined_current_ccn_count']} joined / "
            f"{coverage['unique_source_ccn_count']} unique; "
            f"{coverage['unmatched_source_ccn_count']} unmatched"
        )
    print("All-time totals:")
    for key, value in validation["all_time_totals"].items():
        print(f"  {key}: {value}")
    print("Recent totals:")
    for key, value in validation["recent_totals"].items():
        print(f"  {key}: {value}")
    print(f"Facilities with health records: {validation['facilities_with_health_records']}")
    print(f"Facilities with fire safety records: {validation['facilities_with_fire_safety_records']}")
    print(f"Facilities with penalty records: {validation['facilities_with_penalty_records']}")
    print(f"Facilities with no records: {validation['facilities_with_no_records']}")
    print(f"Output written: {OUTPUT_PATH.as_posix()} ({OUTPUT_PATH.stat().st_size} bytes)")


def main() -> None:
    output, validation = build_summary()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
    print_validation(validation)


if __name__ == "__main__":
    main()
