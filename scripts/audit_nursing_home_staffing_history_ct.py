#!/usr/bin/env python3
"""Audit PBJ-only Connecticut nursing home staffing history export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import audit_nursing_home_staffing_ct as base_audit


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
    groups, _facilities, audit_quality = base_audit.read_raw_pbj(Path(args.input_dir))
    audit_rows = base_audit.derive_audit_rows(groups)
    generated_rows = adapt_history_for_base_compare(history)
    row_comparison = base_audit.compare_rows(audit_rows, generated_rows)

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
        comparison["total_mismatch_count"]
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
    parser.add_argument("--input-dir", default="source_data/pbj_history_audit_input")
    parser.add_argument("--history-json", default="data/nursing_home_staffing_history_ct.json")
    parser.add_argument("--report", default="docs/nursing_home_staffing_history_calculation_audit.md")
    args = parser.parse_args()

    result = audit_history(args)
    write_report(Path(args.report), result)
    print(f"Rows compared: {result['row_comparison']['rows_compared']}")
    print(f"Missing rows in generated JSON: {len(result['row_comparison']['missing_rows_in_generated'])}")
    print(f"Extra rows in generated JSON: {len(result['row_comparison']['extra_rows_in_generated'])}")
    print(f"Total field mismatches: {result['row_comparison']['total_mismatch_count']}")
    print(f"CT applicability mismatches: {result['ct_comparison_status_mismatch_count']}")
    print(f"Forbidden current-context field hits: {result['forbidden_current_context_key_hit_count']}")
    print(f"Report written: {args.report}")
    return 1 if (
        result["row_comparison"]["total_mismatch_count"]
        or result["row_comparison"]["missing_rows_in_generated"]
        or result["row_comparison"]["extra_rows_in_generated"]
        or result["ct_comparison_status_mismatch_count"]
        or result["forbidden_current_context_key_hit_count"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
