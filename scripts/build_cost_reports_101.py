#!/usr/bin/env python3
"""Build data/ct_cost_reports_101.json: the statewide figures behind the Cost Reports 101 page.

Inputs (committed site data, no network):
  data/cost_reports/*.json          per-home DSS cost reports as read by build_ct_cost_reports.py
  data/ct_nursing_home_cost_reports.json  statewide medians and category labels
  data/ct_dss_review.json           DSS review adjustments, Medicaid revenue, rate letters

Only full-year reports that passed the cost-report checks and whose category lines add up
to the printed total are pooled. Deterministic: no wall-clock values.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main():
    idx = json.loads((DATA / "ct_nursing_home_cost_reports.json").read_text(encoding="utf-8"))
    dss = json.loads((DATA / "ct_dss_review.json").read_text(encoding="utf-8"))
    labels = dict(idx["cost_categories"])
    years = sorted(int(y) for y in idx["statewide_medians"])
    year = max(y for y in years if (idx["statewide_medians"][str(y)].get("reports") or 0) >= 100)

    totals = {k: 0.0 for k in labels}
    days = 0.0
    homes = 0
    payer = {"medicaid_ct": 0.0, "medicare": 0.0, "private": 0.0, "other": 0.0}
    for p in sorted((DATA / "cost_reports").glob("*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        for y in c.get("cost_years") or []:
            cb = y.get("cost_breakdown") or {}
            rd = (y.get("resident_days") or {})
            if (y["cost_year"] != year or y.get("part_year") or not (y.get("checks") or {}).get("validated")
                    or not cb.get("adds_up") or not rd.get("resident_days_total")):
                continue
            homes += 1
            days += rd["resident_days_total"]
            for k, v in (cb.get("categories") or {}).items():
                if k in totals:
                    totals[k] += v.get("amount") or 0
            payer["medicaid_ct"] += rd.get("days_medicaid_ct") or 0
            payer["medicare"] += rd.get("days_medicare") or 0
            payer["private"] += rd.get("days_private") or 0
            payer["other"] += (rd.get("days_other_payer") or 0) + (rd.get("days_medicaid_other") or 0)
    pooled = [{"key": k, "label": labels[k], "per_resident_day": round(totals[k] / days, 2),
               "share": round(totals[k] / sum(totals.values()), 4)} for k in labels]
    pooled.sort(key=lambda r: -r["per_resident_day"])
    pdays = sum(payer.values())

    # DSS review and Medicaid revenue, same cost year
    review_prd, mgmt_changed, mgmt_removed, mgmt_homes, per_mcd, any_change = [], 0, 0, 0, [], 0
    for ccn, f in dss["facilities"].items():
        y = (f.get("years") or {}).get(str(year))
        if not y:
            continue
        if y.get("review_adjusted_lines"):
            any_change += 1
        if y.get("management_fee_reported"):
            mgmt_homes += 1
            a = y.get("management_fee_review_adjustment") or 0
            if a:
                mgmt_changed += 1
                if a <= -y["management_fee_reported"] + 1:
                    mgmt_removed += 1
        if y.get("medicaid_revenue_net_per_medicaid_day"):
            per_mcd.append(y["medicaid_revenue_net_per_medicaid_day"])
    rates = sorted(r["per_diem"] for f in dss["facilities"].values() for k, r in (f.get("rates") or {}).items() if k == "SFY2026")

    med = idx["statewide_medians"][str(year)]
    doc = {
        "schema_version": "ct-cost-reports-101-1",
        "cost_year": year,
        "cost_year_period": f"October 1, {year - 1} to September 30, {year}",
        "pooled_homes": homes,
        "pooled_resident_days": int(days),
        "pooled_cost_per_resident_day": round(sum(totals.values()) / days, 2),
        "categories": pooled,
        "payer_share_of_days": {k: round(v / pdays, 4) for k, v in payer.items()},
        "medians": {k: med.get(k) for k in ("expenses_per_resident_day", "direct_care_per_resident_day", "revenue_per_resident_day",
                                             "operating_margin_nh", "medicaid_share_of_days", "nursing_hours_per_resident_day", "reports")},
        "dss_review": {
            "homes_in_files": sum(1 for f in dss["facilities"].values() if str(year) in (f.get("years") or {})),
            "homes_with_review_changes": any_change,
            "homes_reporting_management_fee": mgmt_homes,
            "management_fee_changed": mgmt_changed,
            "management_fee_fully_removed": mgmt_removed,
            "median_medicaid_revenue_per_medicaid_day": round(statistics.median(per_mcd), 2) if per_mcd else None,
        },
        "medicaid_rates_sfy2026": {
            "rate_period": "July 1, 2025 to June 30, 2026",
            "homes": len(rates),
            "min": rates[0] if rates else None,
            "median": round(statistics.median(rates), 2) if rates else None,
            "max": rates[-1] if rates else None,
            "values": rates,
        },
        "rate_rules": {
            "source": "DSS 2024 Connecticut Medicaid Nursing Home Cost Report Guidebook; Conn. Gen. Stat. 17b-340d",
            "components": [
                {"key": "direct", "label": "Direct care", "what": "Nursing and nurse aide salaries, their fringe benefits, and nursing pool (agency) costs.", "cap": "135% of the peer-group median", "peer": "Fairfield County vs. the rest of the state"},
                {"key": "indirect", "label": "Indirect care", "what": "Professional fees, dietary, housekeeping and laundry staff and expenses, and supplies related to resident care.", "cap": "115% of the median", "peer": None},
                {"key": "admin", "label": "Administrative & general", "what": "Administration, maintenance and plant operation, including management fees.", "cap": "100% of the median", "peer": None},
                {"key": "fair_rent", "label": "Fair rent", "what": "A set yearly amount for the building and fixed equipment, paid instead of depreciation, interest or rent.", "cap": None, "peer": None},
                {"key": "capital", "label": "Capital-related", "what": "Property taxes, insurance, and leases and depreciation of movable equipment.", "cap": None, "peer": None},
            ],
            "adjustments": [
                "Costs are divided by the greater of actual resident days or 90% of licensed beds (\"imputed days\"), so empty beds do not raise the rate.",
                "Homes below the median in indirect or administrative costs get an efficiency incentive of 25% of the difference.",
                "Direct care is adjusted each quarter for how much care residents need (acuity, from MDS assessments).",
                "Rates are set each July and rebased on newer cost reports every two to four years; they can be revised after review or audit.",
            ],
            "not_allowed_examples": ["bad debt", "advertising (except help-wanted ads)", "management fees above the cap",
                                     "rent paid to a related party (replaced by fair rent)", "owner salaries above published limits",
                                     "pharmacy and therapy that Medicare covers"],
        },
    }
    out = DATA / "ct_cost_reports_101.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"cost_year": year, "homes": homes, "cost_per_day": doc["pooled_cost_per_resident_day"], "rates": len(rates)}))


if __name__ == "__main__":
    main()
