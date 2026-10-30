"""Build the small Connecticut statewide staffing context export.

Reads the public PBJ history export and the hand-maintained CT policy reference and writes
data/nursing_home_ct_statewide_context.json for the "Connecticut Staffing Rules & Context" page.

Rules (same as the rest of the staffing suite):
- Below-3.00 / below-0.84 counts use the existing public flags, which are populated only for
  quarters where ct_comparison_applicable_for_public_status is true (2023Q2 onward).
- Earlier quarters carry statewide medians only; no CT threshold status is computed for them.
- Hypothetical-level counts are computed for the latest quarter only and are labeled as scenarios.
All values are PBJ-derived screening estimates, not DPH compliance findings.
"""
from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HISTORY = ROOT / "data" / "nursing_home_staffing_history_ct.json"
DEFAULT_REFERENCE = ROOT / "data" / "ct_staffing_policy_reference.json"
DEFAULT_OUTPUT = ROOT / "data" / "nursing_home_ct_statewide_context.json"


def _median(values: list[float]) -> float | None:
    return round(statistics.median(values), 2) if values else None


def build(history: dict, reference: dict) -> dict:
    rows = history["facility_quarterly_staffing_history"]
    quarters = history["history_window"]["quarters"]
    by_quarter: dict[str, list[dict]] = {q: [] for q in quarters}
    for row in rows:
        by_quarter.setdefault(row["quarter"], []).append(row)

    series = []
    for quarter in quarters:
        qrows = by_quarter.get(quarter, [])
        total = [r["metrics"]["ct_direct_care_total_hprd_estimate"] for r in qrows
                 if r["metrics"].get("ct_direct_care_total_hprd_estimate") is not None]
        licensed = [r["metrics"]["ct_direct_care_licensed_nurse_hprd_estimate"] for r in qrows
                    if r["metrics"].get("ct_direct_care_licensed_nurse_hprd_estimate") is not None]
        statuses = sorted({r.get("ct_comparison_period_status") for r in qrows if r.get("ct_comparison_period_status")})
        applicable = bool(qrows) and all(r.get("ct_comparison_applicable_for_public_status") is True for r in qrows)
        entry = {
            "quarter": quarter,
            "quarter_label": qrows[0]["quarter_label"] if qrows else quarter,
            "facilities_reporting": len(qrows),
            "median_ct_direct_care_total_hprd": _median(total),
            "median_ct_direct_care_licensed_hprd": _median(licensed),
            "ct_comparison_period_status": statuses[0] if len(statuses) == 1 else ("mixed" if statuses else None),
            "ct_comparison_applicable_for_public_status": applicable,
            "below_total_3_00_count": None,
            "below_licensed_0_84_count": None,
            "below_total_3_00_share": None,
        }
        if applicable:
            below_total = sum(1 for r in qrows if r.get("ct_total_direct_care_below_comparison_point") is True)
            below_licensed = sum(1 for r in qrows if r.get("ct_licensed_below_comparison_point") is True)
            entry["below_total_3_00_count"] = below_total
            entry["below_licensed_0_84_count"] = below_licensed
            entry["below_total_3_00_share"] = round(below_total / len(qrows), 4) if qrows else None
        series.append(entry)

    latest_quarter = quarters[-1]
    latest_rows = by_quarter.get(latest_quarter, [])
    latest_values = [r["metrics"]["ct_direct_care_total_hprd_estimate"] for r in latest_rows
                     if r["metrics"].get("ct_direct_care_total_hprd_estimate") is not None]
    scenarios = []
    for level in reference.get("scenario_levels", []):
        hprd = float(level["hprd"])
        count = sum(1 for v in latest_values if v < hprd)
        scenarios.append({
            "hprd": hprd,
            "label": level["label"],
            "kind": level["kind"],
            "facilities_below": count,
            "facilities_with_estimate": len(latest_values),
            "share_below": round(count / len(latest_values), 4) if latest_values else None,
        })

    return {
        "schema_version": "ct-statewide-context-1.0",
        "dataset_type": "nursing_home_ct_statewide_context",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_history_generated_at": history.get("generated_at"),
        "history_window": {"first_quarter": quarters[0], "latest_quarter": latest_quarter, "quarter_count": len(quarters)},
        "screening_note": "PBJ-derived screening estimates, not formal Connecticut DPH compliance findings.",
        "statewide_quarterly": series,
        "latest_quarter_scenarios": {"quarter": latest_quarter, "levels": scenarios},
        "policy_reference": reference,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    history = json.loads(args.history.read_text(encoding="utf-8"))
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    result = build(history, reference)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    latest = result["statewide_quarterly"][-1]
    print(f"Wrote {args.output} ({latest['quarter']}: {latest['facilities_reporting']} facilities, "
          f"{latest['below_total_3_00_count']} below 3.00, {latest['below_licensed_0_84_count']} below 0.84)")


if __name__ == "__main__":
    main()
