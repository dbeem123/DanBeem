#!/usr/bin/env python3
"""Audit PBJ-only Connecticut nursing home staffing history export."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import audit_nursing_home_staffing_ct as base_audit

DEFAULT_HISTORY_START = "2017Q4"
DEFAULT_HISTORY_END = "2025Q4"
EXPECTED_HISTORY_QUARTER_COUNT = 33


FORBIDDEN_HISTORY_KEYS = {
    "cms_overall_rating",
    "cms_health_inspection_rating",
    "cms_staffing_rating",
    "cms_rn_staffing_rating",
    "cms_qm_rating",
    "cms_long_stay_qm_rating",
    "cms_short_stay_qm_rating",
    "quality_measures_claims",
    "affiliation_entity_name",
    "affiliation_entity_id",
    "case_mix_total_nurse_hprd",
    "case_mix_rn_hprd",
    "case_mix_lpn_lvn_hprd",
    "case_mix_nurse_aide_hprd",
}


def quarter_sort_key(quarter: str) -> tuple[int, int]:
    return int(quarter[:4]), int(quarter[-1])


def quarter_range(start: str, end: str) -> list[str]:
    quarters = []
    start_year, start_q = quarter_sort_key(start)
    end_year, end_q = quarter_sort_key(end)
    for year in range(start_year, end_year + 1):
        first_q = start_q if year == start_year else 1
        last_q = end_q if year == end_year else 4
        for quarter in range(first_q, last_q + 1):
            quarters.append(f"{year}Q{quarter}")
    return quarters


def quarter_from_source_path(path: Path) -> str | None:
    name = path.name
    patterns = (
        re.compile(r"Q([1-4])_(20\d{2})", re.IGNORECASE),
        re.compile(r"(20\d{2})Q([1-4])", re.IGNORECASE),
        re.compile(r"CY(20\d{2})Q([1-4])", re.IGNORECASE),
    )
    for pattern in patterns:
        match = pattern.search(name)
        if not match:
            continue
        first, second = match.groups()
        if first.startswith("20"):
            return f"{first}Q{second}"
        return f"{second}Q{first}"
    return None


def discover_source_inventory(source_root: Path, target_quarters: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target_set = set(target_quarters)
    candidates = [
        *source_root.glob("PBJ_Daily_Nurse_Staffing_*.csv"),
        *source_root.glob("PBJ_dailynursestaffing_*.csv"),
        *source_root.glob("historical/**/*.zip"),
    ]
    by_quarter: dict[str, list[Path]] = {}
    excluded = []
    unrecognized = []
    for path in sorted(candidates):
        quarter = quarter_from_source_path(path)
        if not quarter:
            unrecognized.append(str(path))
            continue
        if quarter not in target_set:
            excluded.append({"quarter": quarter, "source_file": str(path)})
            continue
        by_quarter.setdefault(quarter, []).append(path)

    missing = [quarter for quarter in target_quarters if quarter not in by_quarter]
    duplicates = {
        quarter: [str(path) for path in paths]
        for quarter, paths in sorted(by_quarter.items())
        if len(paths) > 1
    }
    inventory = [
        {
            "quarter": quarter,
            "source_file": str(by_quarter[quarter][0]),
            "source_format": by_quarter[quarter][0].suffix.lower().lstrip("."),
        }
        for quarter in target_quarters
        if quarter in by_quarter and quarter not in duplicates
    ]
    return inventory, {
        "source_root": str(source_root),
        "target_first_quarter": target_quarters[0],
        "target_latest_quarter": target_quarters[-1],
        "target_quarter_count": len(target_quarters),
        "discovered_target_quarter_count": len(by_quarter),
        "missing_target_quarters": missing,
        "duplicate_target_quarters": duplicates,
        "excluded_out_of_window_sources": excluded,
        "unrecognized_sources": unrecognized,
    }


def stage_source_inventory(inventory: list[dict[str, Any]], temp_input: Path) -> list[dict[str, Any]]:
    staged = []
    for item in inventory:
        source = Path(item["source_file"])
        quarter = item["quarter"]
        if source.suffix.lower() == ".zip":
            with zipfile.ZipFile(source) as zf:
                entries = [name for name in zf.namelist() if name.lower().endswith(".csv")]
                if len(entries) != 1:
                    raise ValueError(f"Expected one CSV in {source}, found {len(entries)}")
                entry = entries[0]
                if "employee" in entry.lower():
                    raise ValueError(f"Expected Daily Nurse Staffing file, found Employee Detail-like entry: {entry}")
                target = temp_input / f"PBJ_Daily_Nurse_Staffing_{quarter}.csv"
                with zf.open(entry) as raw, target.open("wb") as out:
                    shutil.copyfileobj(raw, out)
                staged.append({**item, "zip_entry": entry, "staged_csv": str(target)})
        else:
            target = temp_input / source.name
            shutil.copy2(source, target)
            staged.append({**item, "zip_entry": None, "staged_csv": str(target)})
    return staged


def expected_period_status(quarter: str) -> tuple[str, bool]:
    if quarter <= "2021Q4":
        return "reference_only", False
    if quarter.startswith("2022"):
        return "unresolved_no_public_status", False
    if quarter == "2023Q1":
        return "transitional_partial_period", False
    return "applicable_full_quarter", True


def adapt_history_for_base_compare(history: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "ccn": row.get("ccn"),
            "quarter": row.get("quarter"),
            "resident_days": row.get("resident_days"),
            "average_resident_census": row.get("average_resident_census"),
            "metrics": row.get("metrics", {}),
            "data_quality": row.get("data_quality", {}),
        }
        for row in history.get("facility_quarterly_staffing_history", [])
    ]


def audit_history(args: argparse.Namespace) -> dict[str, Any]:
    history = json.loads(Path(args.history_json).read_text(encoding="utf-8"))
    target_quarters = quarter_range(args.start_quarter, args.end_quarter)
    source_inventory, source_discovery = discover_source_inventory(Path(args.source_root), target_quarters)
    source_discovery["expected_quarter_count"] = args.expected_quarter_count
    source_inventory_errors = []
    if len(target_quarters) != args.expected_quarter_count:
        source_inventory_errors.append(
            f"Configured target range contains {len(target_quarters)} quarters, expected {args.expected_quarter_count}."
        )
    if source_discovery["missing_target_quarters"]:
        source_inventory_errors.append(
            "Missing target quarters: " + ", ".join(source_discovery["missing_target_quarters"])
        )
    if source_discovery["duplicate_target_quarters"]:
        duplicate_text = ", ".join(
            f"{quarter} ({len(paths)} sources)" for quarter, paths in source_discovery["duplicate_target_quarters"].items()
        )
        source_inventory_errors.append("Duplicate target quarters: " + duplicate_text)
    if source_inventory_errors:
        audit_quality = {"ct_input_row_count": 0}
        audit_rows = {}
        row_comparison = base_audit.compare_rows(audit_rows, adapt_history_for_base_compare(history))
    else:
        with tempfile.TemporaryDirectory(prefix="pbj-history-audit-") as temp_name:
            staged_inventory = stage_source_inventory(source_inventory, Path(temp_name))
            groups, _facilities, audit_quality = base_audit.read_raw_pbj(Path(temp_name))
        audit_rows = base_audit.derive_audit_rows(groups)
        row_comparison = base_audit.compare_rows(audit_rows, adapt_history_for_base_compare(history))
        source_discovery["staged_target_quarter_count"] = len(staged_inventory)

    rows = history.get("facility_quarterly_staffing_history", [])
    quarters = sorted({row.get("quarter") for row in rows if row.get("quarter")})
    status_mismatches = []
    forbidden_key_hits = []
    for row in rows:
      quarter = row.get("quarter", "")
      expected_status, expected_applicable = expected_period_status(quarter)
      actual_status = row.get("ct_comparison_period_status")
      actual_applicable = row.get("ct_comparison_applicable_for_public_status")
      if actual_status != expected_status or actual_applicable is not expected_applicable:
          status_mismatches.append({
              "ccn": row.get("ccn"),
              "quarter": quarter,
              "expected_status": expected_status,
              "actual_status": actual_status,
              "expected_applicable": expected_applicable,
              "actual_applicable": actual_applicable,
          })
      total_public = row.get("ct_total_direct_care_below_comparison_point")
      licensed_public = row.get("ct_licensed_below_comparison_point")
      if not expected_applicable and (total_public is not None or licensed_public is not None):
          status_mismatches.append({
              "ccn": row.get("ccn"),
              "quarter": quarter,
              "issue": "below-comparison field populated for non-applicable quarter",
              "total": total_public,
              "licensed": licensed_public,
          })
      if expected_applicable:
          metrics = row.get("metrics", {})
          if total_public != metrics.get("ct_total_direct_care_below_minimum_estimate"):
              status_mismatches.append({"ccn": row.get("ccn"), "quarter": quarter, "issue": "total public flag mismatch"})
          if licensed_public != metrics.get("ct_licensed_direct_care_below_minimum_estimate"):
              status_mismatches.append({"ccn": row.get("ccn"), "quarter": quarter, "issue": "licensed public flag mismatch"})
      for key in FORBIDDEN_HISTORY_KEYS:
          if key in row or key in row.get("metrics", {}) or key in row.get("data_quality", {}):
              forbidden_key_hits.append({"ccn": row.get("ccn"), "quarter": quarter, "key": key})

    return {
        "history_file": args.history_json,
        "quarter_count": len(quarters),
        "quarters": quarters,
        "facility_count": len({row.get("ccn") for row in rows}),
        "facility_quarter_row_count": len(rows),
        "raw_pbj_ct_input_row_count": audit_quality.get("ct_input_row_count"),
        "source_discovery": source_discovery,
        "source_inventory_error_count": len(source_inventory_errors),
        "source_inventory_errors": source_inventory_errors,
        "row_comparison": row_comparison,
        "ct_comparison_status_mismatch_count": len(status_mismatches),
        "ct_comparison_status_mismatches": status_mismatches[:100],
        "forbidden_current_context_key_hit_count": len(forbidden_key_hits),
        "forbidden_current_context_key_hits": forbidden_key_hits[:100],
        "applicable_full_quarter_rows": sum(
            1 for row in rows if row.get("ct_comparison_applicable_for_public_status") is True
        ),
        "non_applicable_rows": sum(
            1 for row in rows if row.get("ct_comparison_applicable_for_public_status") is False
        ),
    }


def write_report(path: Path, result: dict[str, Any]) -> None:
    comparison = result["row_comparison"]
    conclusion = "Historical PBJ calculations and CT applicability fields validated"
    if (
        result["source_inventory_error_count"]
        or result["quarter_count"] != result["source_discovery"]["expected_quarter_count"]
        or comparison["total_mismatch_count"]
        or comparison["missing_rows_in_generated"]
        or comparison["extra_rows_in_generated"]
        or result["ct_comparison_status_mismatch_count"]
        or result["forbidden_current_context_key_hit_count"]
    ):
        conclusion = "Issues found requiring correction"

    lines = [
        "# Nursing Home Staffing History Calculation Audit",
        "",
        f"## Conclusion",
        "",
        f"**{conclusion}.**",
        "",
        f"- History file: `{result['history_file']}`",
        f"- Quarters: {result['quarter_count']} ({result['quarters'][0]} through {result['quarters'][-1]})",
        f"- Facilities: {result['facility_count']}",
        f"- Facility-quarter rows: {result['facility_quarter_row_count']}",
        f"- Raw Connecticut PBJ daily rows re-read: {result['raw_pbj_ct_input_row_count']}",
        "",
        "## Source Discovery",
        "",
        f"- Source root: `{result['source_discovery']['source_root']}`",
        f"- Target window: {result['source_discovery']['target_first_quarter']} through {result['source_discovery']['target_latest_quarter']}",
        f"- Expected target quarters: {result['source_discovery']['expected_quarter_count']}",
        f"- Discovered target quarters: {result['source_discovery']['discovered_target_quarter_count']}",
        f"- Missing target quarters: {len(result['source_discovery']['missing_target_quarters'])}",
        f"- Duplicate target quarters: {len(result['source_discovery']['duplicate_target_quarters'])}",
        f"- Excluded out-of-window sources: {len(result['source_discovery']['excluded_out_of_window_sources'])}",
        f"- Source inventory errors: {result['source_inventory_error_count']}",
        "",
        "## Independent Calculation Comparison",
        "",
        f"- Rows compared: {comparison['rows_compared']}",
        f"- Missing generated rows: {len(comparison['missing_rows_in_generated'])}",
        f"- Extra generated rows: {len(comparison['extra_rows_in_generated'])}",
        f"- Total field mismatches: {comparison['total_mismatch_count']}",
        "",
        "## CT Applicability Field Audit",
        "",
        f"- Full-quarter applicable rows: {result['applicable_full_quarter_rows']}",
        f"- Non-applicable/reference/transitional rows: {result['non_applicable_rows']}",
        f"- Status mismatches: {result['ct_comparison_status_mismatch_count']}",
        "",
        "## Current Context Separation Audit",
        "",
        f"- Forbidden current-context field hits in history rows: {result['forbidden_current_context_key_hit_count']}",
        "",
        "The historical export is PBJ-only and does not embed CMS ratings, Quality Measures Claims, case-mix benchmark fields, or SNF Enrollment affiliation fields as quarter-specific historical values.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Connecticut PBJ-only staffing history export.")
    parser.add_argument("--source-root", default="source_data/pbj")
    parser.add_argument("--start-quarter", default=DEFAULT_HISTORY_START)
    parser.add_argument("--end-quarter", default=DEFAULT_HISTORY_END)
    parser.add_argument("--expected-quarter-count", type=int, default=EXPECTED_HISTORY_QUARTER_COUNT)
    parser.add_argument("--history-json", default="data/nursing_home_staffing_history_ct.json")
    parser.add_argument("--report", default="docs/nursing_home_staffing_history_calculation_audit.md")
    args = parser.parse_args()

    result = audit_history(args)
    write_report(Path(args.report), result)
    print(f"Rows compared: {result['row_comparison']['rows_compared']}")
    print(f"Source target quarters discovered: {result['source_discovery']['discovered_target_quarter_count']}")
    print(f"Source inventory errors: {result['source_inventory_error_count']}")
    print(f"Missing rows in generated JSON: {len(result['row_comparison']['missing_rows_in_generated'])}")
    print(f"Extra rows in generated JSON: {len(result['row_comparison']['extra_rows_in_generated'])}")
    print(f"Total field mismatches: {result['row_comparison']['total_mismatch_count']}")
    print(f"CT applicability mismatches: {result['ct_comparison_status_mismatch_count']}")
    print(f"Forbidden current-context field hits: {result['forbidden_current_context_key_hit_count']}")
    print(f"Report written: {args.report}")
    return 1 if (
        result["source_inventory_error_count"]
        or result["quarter_count"] != result["source_discovery"]["expected_quarter_count"]
        or result["source_discovery"]["discovered_target_quarter_count"] != result["source_discovery"]["expected_quarter_count"]
        or result["row_comparison"]["total_mismatch_count"]
        or result["row_comparison"]["missing_rows_in_generated"]
        or result["row_comparison"]["extra_rows_in_generated"]
        or result["ct_comparison_status_mismatch_count"]
        or result["forbidden_current_context_key_hit_count"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
