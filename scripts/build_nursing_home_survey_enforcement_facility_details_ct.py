"""Build per-facility Connecticut survey and enforcement detail JSON files.

Default behavior validates inputs and reports planned outputs without writing.
Use --write-runtime to create or update the scoped production detail directory.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Callable


STAFFING_PATH = Path("data/nursing_home_staffing_ct.json")
HEALTH_PATH = Path("data/nursing_home_health_deficiencies_ct.json")
FIRE_PATH = Path("data/nursing_home_fire_safety_deficiencies_ct.json")
PENALTIES_PATH = Path("data/nursing_home_penalties_ct.json")
SUMMARY_PATH = Path("data/nursing_home_survey_enforcement_summary_ct.json")
OUTPUT_DIR = Path("data/nursing_home_survey_enforcement_details_ct")
INDEX_PATH = OUTPUT_DIR / "index.json"

INPUT_PATHS = [STAFFING_PATH, HEALTH_PATH, FIRE_PATH, PENALTIES_PATH]
GENERATED_FACILITY_FILE_PATTERN = re.compile(r"^\d{6}\.json$")

FACILITY_LIMITATIONS = [
    "available_source_windows_only",
    "citation_counts_are_context_only",
    "enforcement_values_are_not_quality_scores",
    "no_composite_quality_score_or_ranking",
    "health_harm_grouping_not_applied_to_fire_or_emergency_records",
    "cms_lookup_gaps_documented_for_K-0211_and_K-0133",
]

INDEX_LIMITATIONS = [
    "Facility files reflect available rolling CMS runtime sources, not complete lifetime histories.",
    "Citation records provide context and are not a standalone quality score.",
    "Fine amounts and payment denials are enforcement values and are not ranking measures.",
    "Health harm/immediate-jeopardy grouping applies only to health deficiency records.",
    "Known CMS citation-description lookup gaps for K-0211 and K-0133 remain preserved and documented.",
    "Duplicate penalty source rows remain preserved and transparently flagged.",
    "These files are not automatically wired into the public UI.",
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
    if not re.fullmatch(r"\d{6}", ccn):
        raise ValueError(f"Invalid CCN {value!r} in {source}; expected a six-digit string")
    return ccn


def require_metadata_count(
    data: dict[str, Any],
    key: str,
    actual: int,
    *,
    source: Path,
) -> None:
    metadata = data.get("metadata")
    if not isinstance(metadata, dict) or not isinstance(metadata.get(key), int):
        raise ValueError(f"Missing integer metadata.{key} in {source.as_posix()}")
    if metadata[key] != actual:
        raise ValueError(
            f"{source.as_posix()} metadata.{key} is {metadata[key]}, but records total {actual}"
        )


def group_by_ccn(
    rows: list[dict[str, Any]],
    *,
    source: Path,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[validate_ccn(row.get("ccn"), source=source.as_posix())].append(row)
    return dict(grouped)


def require_fields(row: dict[str, Any], fields: list[str], *, source: str) -> None:
    missing = [field for field in fields if field not in row]
    if missing:
        raise ValueError(f"Missing fields in {source}: {', '.join(missing)}")


def select_fields(row: dict[str, Any], fields: list[str], *, source: str) -> dict[str, Any]:
    require_fields(row, fields, source=source)
    return {field: row[field] for field in fields}


def numeric_or_none(value: Any, *, field: str, source: str) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"Invalid numeric {field} {value!r} in {source}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric {field} {value!r} in {source}") from exc


def integer_or_none(value: Any, *, field: str, source: str) -> int | None:
    number = numeric_or_none(value, field=field, source=source)
    if number is None:
        return None
    if not number.is_integer():
        raise ValueError(f"Expected integer {field}, found {value!r} in {source}")
    return int(number)


HEALTH_FIELDS = [
    "survey_date",
    "survey_year",
    "survey_type",
    "deficiency_code",
    "deficiency_description",
    "deficiency_category",
    "scope_severity_code",
    "harm_ij_group",
    "standard_deficiency",
    "complaint_deficiency",
    "infection_control_inspection_deficiency",
    "correction_date",
    "citation_under_idr",
    "citation_under_iidr",
    "processing_date",
    "citation_description_lookup_matched",
    "citation_description_category",
    "citation_description_text",
    "source_row_hash",
]

FIRE_FIELDS = [
    "survey_date",
    "survey_year",
    "survey_type",
    "deficiency_code",
    "deficiency_description",
    "deficiency_category",
    "tag_version",
    "scope_severity_code",
    "deficiency_corrected",
    "standard_deficiency",
    "complaint_deficiency",
    "correction_date",
    "citation_under_idr",
    "citation_under_iidr",
    "processing_date",
    "citation_description_lookup_matched",
    "citation_description_category",
    "citation_description_text",
    "citation_description_lookup_gap_reason",
    "source_row_hash",
]

PENALTY_FIELDS = [
    "penalty_date",
    "penalty_year",
    "penalty_type",
    "enforcement_category",
    "payment_denial_start_date",
    "processing_date",
    "duplicate_full_row_signature",
    "source_row_hash",
]


def compact_health_row(row: dict[str, Any]) -> dict[str, Any]:
    compact = select_fields(row, HEALTH_FIELDS, source=HEALTH_PATH.as_posix())
    if not str(compact["deficiency_code"]).startswith("F-"):
        raise ValueError(f"Unexpected non-F health code: {compact['deficiency_code']}")
    return compact


def compact_fire_row(row: dict[str, Any]) -> dict[str, Any]:
    compact = select_fields(row, FIRE_FIELDS, source=FIRE_PATH.as_posix())
    if "harm_ij_group" in compact:
        raise ValueError("Health harm/IJ grouping must not be copied into fire or emergency records")
    return compact


def compact_penalty_row(row: dict[str, Any]) -> dict[str, Any]:
    compact = select_fields(row, PENALTY_FIELDS, source=PENALTIES_PATH.as_posix())
    category = compact["enforcement_category"]
    if category not in {"fine", "payment_denial"}:
        raise ValueError(f"Unexpected enforcement category: {category!r}")
    compact["fine_amount"] = numeric_or_none(
        row.get("normalized_fine_amount"),
        field="normalized_fine_amount",
        source=PENALTIES_PATH.as_posix(),
    )
    compact["payment_denial_length_days"] = integer_or_none(
        row.get("payment_denial_length_days"),
        field="payment_denial_length_days",
        source=PENALTIES_PATH.as_posix(),
    )
    return compact


def newest_first_key(date_field: str, stable_fields: list[str]) -> Callable[[dict[str, Any]], tuple[Any, ...]]:
    def key(row: dict[str, Any]) -> tuple[Any, ...]:
        value = str(row.get(date_field) or "")
        try:
            ordinal = date.fromisoformat(value).toordinal()
        except ValueError as exc:
            raise ValueError(f"Invalid {date_field} {value!r} in generated record") from exc
        return (-ordinal, *(str(row.get(field) or "") for field in stable_fields))

    return key


def json_bytes(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def validate_summary_cross_check(
    summary_data: dict[str, Any],
    current_ccns: set[str],
    per_facility_counts: dict[str, dict[str, int]],
) -> None:
    summary_rows = require_rows(summary_data, "facilities", SUMMARY_PATH)
    summary_by_ccn: dict[str, dict[str, Any]] = {}
    for row in summary_rows:
        ccn = validate_ccn(row.get("ccn"), source=SUMMARY_PATH.as_posix())
        if ccn in summary_by_ccn:
            raise ValueError(f"Duplicate compact summary CCN: {ccn}")
        summary_by_ccn[ccn] = row
    if set(summary_by_ccn) != current_ccns:
        raise ValueError("Compact summary CCNs do not exactly match current staffing CCNs")

    field_map = {
        "health": "all_time_health_deficiency_count",
        "fire_safety": "all_time_fire_safety_citation_count",
        "emergency_preparedness": "all_time_emergency_preparedness_citation_count",
        "penalties": "all_time_enforcement_event_count",
    }
    for ccn, counts in per_facility_counts.items():
        summary = summary_by_ccn[ccn]
        for detail_key, summary_key in field_map.items():
            if summary.get(summary_key) != counts[detail_key]:
                raise ValueError(
                    f"Compact summary mismatch for {ccn} {summary_key}: "
                    f"{summary.get(summary_key)!r} != {counts[detail_key]}"
                )


def build_outputs() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    staffing_data = load_json(STAFFING_PATH)
    health_data = load_json(HEALTH_PATH)
    fire_data = load_json(FIRE_PATH)
    penalties_data = load_json(PENALTIES_PATH)
    summary_data = load_json(SUMMARY_PATH) if SUMMARY_PATH.is_file() else None

    staffing_rows = require_rows(staffing_data, "facilities", STAFFING_PATH)
    health_rows = require_rows(health_data, "deficiencies", HEALTH_PATH)
    fire_rows = require_rows(fire_data, "deficiencies", FIRE_PATH)
    penalty_rows = require_rows(penalties_data, "penalties", PENALTIES_PATH)

    staffing_by_ccn: dict[str, dict[str, Any]] = {}
    for row in staffing_rows:
        ccn = validate_ccn(row.get("ccn"), source=STAFFING_PATH.as_posix())
        if ccn in staffing_by_ccn:
            raise ValueError(f"Duplicate current staffing CCN: {ccn}")
        provider_name = str(row.get("provider_name") or "").strip()
        if not provider_name:
            raise ValueError(f"Missing current provider name for CCN {ccn}")
        staffing_by_ccn[ccn] = row

    health_by_ccn = group_by_ccn(health_rows, source=HEALTH_PATH)
    fire_all_by_ccn = group_by_ccn(fire_rows, source=FIRE_PATH)
    penalty_by_ccn = group_by_ccn(penalty_rows, source=PENALTIES_PATH)
    current_ccns = set(staffing_by_ccn)

    for source_name, source_ccns in {
        "health": set(health_by_ccn),
        "fire_safety_and_emergency_preparedness": set(fire_all_by_ccn),
        "penalties": set(penalty_by_ccn),
    }.items():
        unexpected = sorted(source_ccns - current_ccns)
        if unexpected:
            raise ValueError(f"Unexpected non-current CCNs in {source_name}: {', '.join(unexpected)}")

    fire_k_rows = [row for row in fire_rows if row.get("deficiency_prefix") == "K"]
    fire_e_rows = [row for row in fire_rows if row.get("deficiency_prefix") == "E"]
    if len(fire_k_rows) + len(fire_e_rows) != len(fire_rows):
        raise ValueError("Fire runtime contains prefixes other than K and E")
    fire_k_by_ccn = group_by_ccn(fire_k_rows, source=FIRE_PATH)
    fire_e_by_ccn = group_by_ccn(fire_e_rows, source=FIRE_PATH)

    require_metadata_count(health_data, "ct_row_count", len(health_rows), source=HEALTH_PATH)
    require_metadata_count(fire_data, "ct_row_count", len(fire_rows), source=FIRE_PATH)
    require_metadata_count(fire_data, "k_tag_count", len(fire_k_rows), source=FIRE_PATH)
    require_metadata_count(fire_data, "e_tag_count", len(fire_e_rows), source=FIRE_PATH)
    require_metadata_count(penalties_data, "ct_row_count", len(penalty_rows), source=PENALTIES_PATH)

    source_files = [path.as_posix() for path in INPUT_PATHS[1:]]
    facility_bytes_by_name: dict[str, bytes] = {}
    facility_entries: list[dict[str, Any]] = []
    per_facility_counts: dict[str, dict[str, int]] = {}

    for ccn, staffing in staffing_by_ccn.items():
        health = sorted(
            (compact_health_row(row) for row in health_by_ccn.get(ccn, [])),
            key=newest_first_key("survey_date", ["deficiency_code", "source_row_hash"]),
        )
        fire_k = sorted(
            (compact_fire_row(row) for row in fire_k_by_ccn.get(ccn, [])),
            key=newest_first_key("survey_date", ["deficiency_code", "source_row_hash"]),
        )
        fire_e = sorted(
            (compact_fire_row(row) for row in fire_e_by_ccn.get(ccn, [])),
            key=newest_first_key("survey_date", ["deficiency_code", "source_row_hash"]),
        )
        penalties = sorted(
            (compact_penalty_row(row) for row in penalty_by_ccn.get(ccn, [])),
            key=newest_first_key("penalty_date", ["penalty_type", "source_row_hash"]),
        )
        counts = {
            "health": len(health),
            "fire_safety": len(fire_k),
            "emergency_preparedness": len(fire_e),
            "penalties": len(penalties),
        }
        per_facility_counts[ccn] = counts
        total_count = sum(counts.values())
        detail = {
            "metadata": {
                "ccn": ccn,
                "provider_name": str(staffing["provider_name"]).strip(),
                "build_date": date.today().isoformat(),
                "source_files": source_files,
                "health_record_count": counts["health"],
                "fire_safety_record_count": counts["fire_safety"],
                "emergency_preparedness_record_count": counts["emergency_preparedness"],
                "penalty_record_count": counts["penalties"],
                "fire_lookup_gap_record_count": sum(
                    not row["citation_description_lookup_matched"] for row in fire_k + fire_e
                ),
                "duplicate_penalty_record_count": sum(
                    bool(row["duplicate_full_row_signature"]) for row in penalties
                ),
                "limitations": FACILITY_LIMITATIONS,
            },
            "health_deficiencies": health,
            "fire_safety_deficiencies": fire_k,
            "emergency_preparedness_deficiencies": fire_e,
            "penalties": penalties,
        }
        filename = f"{ccn}.json"
        payload = json_bytes(detail)
        facility_bytes_by_name[filename] = payload
        facility_entries.append(
            {
                "ccn": ccn,
                "provider_name": str(staffing["provider_name"]).strip(),
                "relative_file_path": f"{OUTPUT_DIR.as_posix()}/{filename}",
                "total_detail_record_count": total_count,
                "health_record_count": counts["health"],
                "fire_safety_record_count": counts["fire_safety"],
                "emergency_preparedness_record_count": counts["emergency_preparedness"],
                "penalty_record_count": counts["penalties"],
                "file_size_bytes": len(payload),
            }
        )

    if len(facility_bytes_by_name) != len(staffing_by_ccn):
        raise ValueError("Generated facility file count does not match current facility count")
    generated_ccns = {name.removesuffix(".json") for name in facility_bytes_by_name}
    if generated_ccns != current_ccns:
        raise ValueError("Generated facility filenames do not exactly match current staffing CCNs")

    totals = {
        "health_records": sum(counts["health"] for counts in per_facility_counts.values()),
        "fire_safety_records": sum(counts["fire_safety"] for counts in per_facility_counts.values()),
        "emergency_preparedness_records": sum(
            counts["emergency_preparedness"] for counts in per_facility_counts.values()
        ),
        "penalty_records": sum(counts["penalties"] for counts in per_facility_counts.values()),
    }
    expected_totals = {
        "health_records": len(health_rows),
        "fire_safety_records": len(fire_k_rows),
        "emergency_preparedness_records": len(fire_e_rows),
        "penalty_records": len(penalty_rows),
    }
    if totals != expected_totals:
        raise ValueError(f"Per-facility totals do not reconcile: {totals} != {expected_totals}")

    if summary_data is not None:
        validate_summary_cross_check(summary_data, current_ccns, per_facility_counts)

    facility_entries.sort(key=lambda row: (row["provider_name"].casefold(), row["ccn"]))
    source_ccn_coverage = {
        "health_unique_ccn_count": len(health_by_ccn),
        "fire_safety_and_emergency_preparedness_unique_ccn_count": len(fire_all_by_ccn),
        "penalties_unique_ccn_count": len(penalty_by_ccn),
    }
    zero_record_count = sum(entry["total_detail_record_count"] == 0 for entry in facility_entries)
    index = {
        "build_date": date.today().isoformat(),
        "facility_file_count": len(facility_entries),
        "expected_current_facility_count": len(staffing_rows),
        "total_health_records": totals["health_records"],
        "total_fire_safety_records": totals["fire_safety_records"],
        "total_emergency_preparedness_records": totals["emergency_preparedness_records"],
        "total_penalty_records": totals["penalty_records"],
        "facilities_with_no_detail_records": zero_record_count,
        "source_ccn_coverage": source_ccn_coverage,
        "source_files": [path.as_posix() for path in INPUT_PATHS],
        "summary_cross_check_file": SUMMARY_PATH.as_posix() if summary_data is not None else None,
        "limitations": INDEX_LIMITATIONS,
        "facilities": facility_entries,
    }
    index_payload = json_bytes(index)

    facility_sizes = [len(payload) for payload in facility_bytes_by_name.values()]
    largest_by_count = sorted(
        facility_entries,
        key=lambda row: (-row["total_detail_record_count"], row["provider_name"].casefold(), row["ccn"]),
    )[:10]
    smallest_file = min(facility_entries, key=lambda row: (row["file_size_bytes"], row["ccn"]))
    largest_file = max(facility_entries, key=lambda row: (row["file_size_bytes"], row["ccn"]))
    source_runtime_size = sum(path.stat().st_size for path in [HEALTH_PATH, FIRE_PATH, PENALTIES_PATH])
    validation = {
        "facility_file_count": len(facility_entries),
        "current_facility_count": len(staffing_rows),
        "totals": totals,
        "source_ccn_coverage": source_ccn_coverage,
        "zero_record_file_count": zero_record_count,
        "facility_files_size_bytes": sum(facility_sizes),
        "index_size_bytes": len(index_payload),
        "total_directory_size_bytes": sum(facility_sizes) + len(index_payload),
        "minimum_facility_file_size_bytes": min(facility_sizes),
        "maximum_facility_file_size_bytes": max(facility_sizes),
        "median_facility_file_size_bytes": statistics.median(facility_sizes),
        "average_facility_file_size_bytes": statistics.mean(facility_sizes),
        "smallest_facility_file": smallest_file,
        "largest_facility_file": largest_file,
        "largest_facilities_by_record_count": largest_by_count,
        "statewide_detailed_runtime_size_bytes": source_runtime_size,
    }
    return facility_bytes_by_name, index_payload, validation


def ensure_scoped_output_directory() -> None:
    expected = (Path.cwd() / OUTPUT_DIR).resolve()
    actual = OUTPUT_DIR.resolve()
    if actual != expected:
        raise RuntimeError(
            f"Refusing output because resolved directory is outside expected scope: {actual}"
        )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_atomic(path: Path, payload: bytes) -> None:
    temporary_path = path.with_name(f".{path.name}.tmp")
    with temporary_path.open("wb") as handle:
        handle.write(payload)
    temporary_path.replace(path)


def write_runtime(facility_payloads: dict[str, bytes], index_payload: bytes) -> list[str]:
    ensure_scoped_output_directory()
    expected_names = set(facility_payloads)
    for filename in sorted(expected_names):
        write_atomic(OUTPUT_DIR / filename, facility_payloads[filename])
    write_atomic(INDEX_PATH, index_payload)

    stale_removed: list[str] = []
    for path in sorted(OUTPUT_DIR.iterdir()):
        if not path.is_file():
            continue
        if GENERATED_FACILITY_FILE_PATTERN.fullmatch(path.name) and path.name not in expected_names:
            path.unlink()
            stale_removed.append(path.name)
    return stale_removed


def print_validation(validation: dict[str, Any], *, wrote_runtime: bool, stale_removed: list[str]) -> None:
    print(f"Current facilities: {validation['current_facility_count']}")
    print(f"Facility detail files: {validation['facility_file_count']}")
    print("Reconciliation totals:")
    for key, value in validation["totals"].items():
        print(f"  {key}: {value}")
    print("Source CCN coverage:")
    for key, value in validation["source_ccn_coverage"].items():
        print(f"  {key}: {value}")
    print(f"Zero-record facility files: {validation['zero_record_file_count']}")
    print(f"Facility files size bytes: {validation['facility_files_size_bytes']}")
    print(f"Index size bytes: {validation['index_size_bytes']}")
    print(f"Total generated directory size bytes: {validation['total_directory_size_bytes']}")
    print(f"Minimum facility file size bytes: {validation['minimum_facility_file_size_bytes']}")
    print(f"Maximum facility file size bytes: {validation['maximum_facility_file_size_bytes']}")
    print(f"Median facility file size bytes: {validation['median_facility_file_size_bytes']}")
    print(f"Average facility file size bytes: {validation['average_facility_file_size_bytes']:.2f}")
    print(
        "Smallest facility file: "
        f"{validation['smallest_facility_file']['ccn']}.json "
        f"({validation['smallest_facility_file']['file_size_bytes']} bytes)"
    )
    print(
        "Largest facility file: "
        f"{validation['largest_facility_file']['ccn']}.json "
        f"({validation['largest_facility_file']['file_size_bytes']} bytes)"
    )
    print("Largest facilities by detail record count:")
    for row in validation["largest_facilities_by_record_count"]:
        print(
            f"  {row['ccn']} {row['provider_name']}: "
            f"{row['total_detail_record_count']} records, {row['file_size_bytes']} bytes"
        )
    print(
        "Three statewide detailed runtime files size bytes: "
        f"{validation['statewide_detailed_runtime_size_bytes']}"
    )
    if wrote_runtime:
        print(f"Runtime output written: {OUTPUT_DIR.as_posix()}")
        print(f"Stale generated facility files removed: {len(stale_removed)}")
    else:
        print("Validation only: no output written.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-runtime",
        action="store_true",
        help=f"Write production facility detail files under {OUTPUT_DIR.as_posix()}",
    )
    args = parser.parse_args()

    facility_payloads, index_payload, validation = build_outputs()
    stale_removed: list[str] = []
    if args.write_runtime:
        stale_removed = write_runtime(facility_payloads, index_payload)
    print_validation(validation, wrote_runtime=args.write_runtime, stale_removed=stale_removed)


if __name__ == "__main__":
    main()
