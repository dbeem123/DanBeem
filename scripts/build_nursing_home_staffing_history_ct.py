#!/usr/bin/env python3
"""Build PBJ-only Connecticut nursing home staffing history JSON.

This script intentionally keeps current CMS contextual snapshots out of the
historical export. It reuses the validated PBJ aggregation/formula path from
build_nursing_home_staffing_ct.py, then emits a slimmer longitudinal file for
public historical staffing views.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

import build_nursing_home_staffing_ct as current_builder


DEFAULT_HISTORY_START = "2017Q4"
DEFAULT_HISTORY_END = "2025Q4"


def quarter_key(year: int, quarter: int) -> str:
    return f"{year}Q{quarter}"


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
            quarters.append(quarter_key(year, quarter))
    return quarters


def source_for_quarter(source_root: Path, quarter: str) -> Path:
    year = int(quarter[:4])
    q = int(quarter[-1])
    if year < 2024 or (year == 2024 and q <= 3):
        return source_root / "historical" / str(year) / f"PBJ_Daily_Nurse_Staffing_Q{q}_{year}.zip"
    if year == 2025 and q == 4:
        return source_root / "PBJ_dailynursestaffing_CY2025Q4.csv"
    return source_root / f"PBJ_Daily_Nurse_Staffing_Q{q}_{year}.csv"


def stage_quarter_sources(source_root: Path, temp_input: Path, quarters: list[str]) -> list[dict[str, Any]]:
    inventory = []
    for quarter in quarters:
        source = source_for_quarter(source_root, quarter)
        if not source.exists():
            raise FileNotFoundError(f"Missing PBJ source for {quarter}: {source}")
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
                inventory.append({
                    "quarter": quarter,
                    "source_file": str(source),
                    "zip_entry": entry,
                    "staged_csv": str(target),
                })
        else:
            target = temp_input / source.name
            shutil.copy2(source, target)
            inventory.append({
                "quarter": quarter,
                "source_file": str(source),
                "zip_entry": None,
                "staged_csv": str(target),
            })
    return inventory


def ct_comparison_status(quarter: str) -> tuple[str, bool, str]:
    if quarter <= "2021Q4":
        return (
            "reference_only",
            False,
            "3.00/0.84 CT comparison points are shown only as retrospective reference context for this quarter.",
        )
    if quarter.startswith("2022"):
        return (
            "unresolved_no_public_status",
            False,
            "Conservative publication method does not assign public CT comparison status for 2022 quarters pending legal/DPH confirmation.",
        )
    if quarter == "2023Q1":
        return (
            "transitional_partial_period",
            False,
            "Q1 2023 is treated as partial-period context because the former 3.0 staffing policies were effective March 1, 2023.",
        )
    return (
        "applicable_full_quarter",
        True,
        "Full-quarter PBJ-derived CT comparison screening status may be displayed with caveats.",
    )


def build_history_export(
    input_dir: Path,
    output_path: Path,
    source_inventory: list[dict[str, Any]],
    source_release: str,
    freshness_date: str,
) -> dict[str, Any]:
    groups, facilities, quality = current_builder.load_pbj_rows(input_dir)
    base = current_builder.build_output(
        groups,
        facilities,
        quality,
        output_path,
        source_release,
        freshness_date,
    )
    rows = []
    for row in base["facility_quarterly_staffing"]:
        status, applicable, note = ct_comparison_status(row["quarter"])
        metrics = dict(row["metrics"])
        total_below = metrics.get("ct_total_direct_care_below_minimum_estimate") if applicable else None
        licensed_below = metrics.get("ct_licensed_direct_care_below_minimum_estimate") if applicable else None
        rows.append({
            "ccn": row["ccn"],
            "provider_name_from_pbj": facilities.get(row["ccn"], {}).get("provider_name") or row["ccn"],
            "city_from_pbj": facilities.get(row["ccn"], {}).get("city") or "",
            "state": "CT",
            "quarter": row["quarter"],
            "quarter_label": row["quarter_label"],
            "quarter_start_date": row["quarter_start_date"],
            "quarter_end_date": row["quarter_end_date"],
            "average_resident_census": row["average_resident_census"],
            "resident_days": row["resident_days"],
            "metrics": metrics,
            "ct_comparison_period_status": status,
            "ct_comparison_applicable_for_public_status": applicable,
            "ct_comparison_status_note": note,
            "ct_total_direct_care_below_comparison_point": total_below,
            "ct_licensed_below_comparison_point": licensed_below,
            "data_quality": row["data_quality"],
        })
    quarters = sorted({row["quarter"] for row in rows}, key=quarter_sort_key)
    facilities_out = sorted(
        {
            row["ccn"]: {
                "ccn": row["ccn"],
                "latest_pbj_provider_name": row["provider_name_from_pbj"],
                "latest_pbj_city": row["city_from_pbj"],
                "state": "CT",
            }
            for row in rows
        }.values(),
        key=lambda row: (row["latest_pbj_provider_name"], row["ccn"]),
    )
    return {
        "schema_version": "history-1.0",
        "dataset_type": "nursing_home_staffing_history_pbj_only",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "publication_status": "public_pbj_history",
        "history_window": {
            "first_quarter": quarters[0] if quarters else "",
            "latest_quarter": quarters[-1] if quarters else "",
            "quarter_count": len(quarters),
            "quarters": quarters,
        },
        "sources": [
            {
                "source_dataset_name": "CMS Payroll-Based Journal Daily Nurse Staffing",
                "source_release": source_release,
                "freshness_date": freshness_date,
                "source_level": "official CMS PBJ source files processed offline",
                "notes": "PBJ-only historical staffing export. Current CMS Provider Information, ratings, Quality Measures Claims, case-mix comparison points, and SNF Enrollment affiliation snapshots are intentionally not embedded as historical quarter values.",
            }
        ],
        "pbj_source_inventory": source_inventory,
        "facilities": facilities_out,
        "facility_quarterly_staffing_history": rows,
        "data_quality": {
            **base["data_quality"],
            "output_path": str(output_path),
            "history_quarter_count": len(quarters),
            "history_facility_count": len(facilities_out),
            "history_facility_quarter_row_count": len(rows),
            "ct_comparison_applicable_full_quarter_row_count": sum(
                1 for row in rows if row["ct_comparison_applicable_for_public_status"]
            ),
            "ct_total_direct_care_below_comparison_point_count": sum(
                1 for row in rows if row["ct_total_direct_care_below_comparison_point"] is True
            ),
            "ct_licensed_below_comparison_point_count": sum(
                1 for row in rows if row["ct_licensed_below_comparison_point"] is True
            ),
        },
        "field_map": {
            "provider_name_from_pbj": "Facility name from PBJ source identity for historical continuity review.",
            "ct_comparison_period_status": "Historical applicability category controlling public CT comparison display.",
            "ct_total_direct_care_below_comparison_point": "Public below-CT-3.00 flag populated only when ct_comparison_applicable_for_public_status is true.",
            "ct_licensed_below_comparison_point": "Public below-CT-0.84 flag populated only when ct_comparison_applicable_for_public_status is true.",
        },
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PBJ-only Connecticut nursing home staffing history JSON.")
    parser.add_argument("--source-root", default="source_data/pbj")
    parser.add_argument("--output", default="data/nursing_home_staffing_history_ct.json")
    parser.add_argument("--start-quarter", default=DEFAULT_HISTORY_START)
    parser.add_argument("--end-quarter", default=DEFAULT_HISTORY_END)
    parser.add_argument("--source-release", default="CMS PBJ Daily Nurse Staffing historical archive, 2017Q4-2025Q4")
    parser.add_argument("--freshness-date", default=date.today().isoformat())
    args = parser.parse_args()

    quarters = quarter_range(args.start_quarter, args.end_quarter)
    with tempfile.TemporaryDirectory(prefix="pbj-history-build-") as temp_name:
        temp_input = Path(temp_name)
        inventory = stage_quarter_sources(Path(args.source_root), temp_input, quarters)
        data = build_history_export(
            temp_input,
            Path(args.output),
            inventory,
            args.source_release,
            args.freshness_date,
        )
        write_json(Path(args.output), data)

    print(f"Wrote {args.output}")
    print(f"Quarters: {data['history_window']['quarter_count']}")
    print(f"Facilities: {data['data_quality']['history_facility_count']}")
    print(f"Facility-quarter rows: {data['data_quality']['history_facility_quarter_row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
