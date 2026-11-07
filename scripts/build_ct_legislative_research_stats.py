"""Build data/ct_legislative_research_stats.json for the CT legislative tracker.

Every statistic is computed from data files already published on this site, so the
numbers refresh whenever those files refresh. Each stat carries its source, period and
caveat so advocates can cite it as-is.

Inputs: nursing_home_staffing_ct.json, nursing_home_ct_statewide_context.json,
nursing_home_survey_enforcement_summary_ct.json, impact-2025.json.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEFAULT_OUT = DATA / "ct_legislative_research_stats.json"

STAFFING_TOOL = "/staffing/tools/nursing-home-statewide-staffing-comparison.html"
CT_RULES = "/staffing/tools/nursing-home-ct-staffing-rules.html"
EXPLORER = "/staffing/tools/nursing-home-staffing-explorer.html"
IMPACT = "/dashboards/impact-2025.html"


def stat(key, value, label, period, source, link, caveat, display=None):
    return {"key": key, "value": value, "display": display if display is not None else f"{value:,}" if isinstance(value, int) else str(value),
            "label": label, "period": period, "source": source, "link": link, "caveat": caveat}


def nice_date(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d:%b} {d.day}, {d.year}"  # portable: Windows strftime has no %-d


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def build() -> dict:
    staffing = load("nursing_home_staffing_ct.json")
    context = load("nursing_home_ct_statewide_context.json")
    survey = load("nursing_home_survey_enforcement_summary_ct.json")
    impact = load("impact-2025.json")

    q = staffing["reporting_period"]["quarter"]
    qlabel = staffing["reporting_period"]["label"]
    rows = [r for r in staffing["facility_quarterly_staffing"] if r["quarter"] == q]
    pbj = "CMS Payroll-Based Journal, PBJ-derived screening estimate"
    screening = "Screening estimate from payroll data, not a DPH compliance finding."
    latest = context["statewide_quarterly"][-1]
    first = next(r for r in context["statewide_quarterly"] if r["ct_comparison_applicable_for_public_status"])
    scen = {lv["hprd"]: lv for lv in context["latest_quarter_scenarios"]["levels"]}
    rn = [r["metrics"]["rn_hprd"] for r in rows if r["metrics"].get("rn_hprd") is not None]
    contract = [r["metrics"]["contract_staff_pct"] for r in rows if r["metrics"].get("contract_staff_pct") is not None]
    census = sum(r["average_resident_census"] for r in rows if r.get("average_resident_census"))

    stats = [
        stat("homes_below_300", latest["below_total_3_00_count"],
             f"of {latest['facilities_reporting']} Connecticut nursing homes had an estimated direct-care staffing level below the state's 3.00 hours per resident day",
             qlabel, pbj, CT_RULES, screening),
        stat("homes_below_300_first", first["below_total_3_00_count"],
             f"of {first['facilities_reporting']} homes were below 3.00 in {first['quarter_label']}, the first full quarter the standard applied",
             first["quarter_label"], pbj, CT_RULES, screening),
        stat("homes_below_084", latest["below_licensed_0_84_count"],
             f"of {latest['facilities_reporting']} homes had an estimated licensed-nurse level below the state's 0.84 hours per resident day",
             qlabel, pbj, CT_RULES, screening),
        stat("median_direct_care", latest["median_ct_direct_care_total_hprd"],
             "hours of direct care per resident per day at the median Connecticut home",
             qlabel, pbj, CT_RULES, screening, display=f"{latest['median_ct_direct_care_total_hprd']:.2f}"),
        stat("homes_below_360", scen[3.6]["facilities_below"],
             f"of {scen[3.6]['facilities_with_estimate']} homes would be below 3.60 hours, the level proposed in 2025 SB 1279 (not enacted)",
             qlabel, pbj, CT_RULES, "Scenario only; 3.60 is not law. " + screening),
        stat("homes_below_410", scen[4.1]["facilities_below"],
             f"of {scen[4.1]['facilities_with_estimate']} homes would be below 4.10 hours, the level proposed in 2023 SB 1026 (not enacted)",
             qlabel, pbj, CT_RULES, "Scenario only; 4.10 is not law. " + screening),
        stat("median_rn_hprd", round(statistics.median(rn), 2), "registered nurse hours per resident per day at the median home",
             qlabel, "CMS Payroll-Based Journal", STAFFING_TOOL, "Quarterly payroll data.", display=f"{statistics.median(rn):.2f}"),
        stat("contract_median", round(statistics.median(contract), 1), "percent of nursing hours worked by contract (agency) staff at the median home",
             qlabel, "CMS Payroll-Based Journal", STAFFING_TOOL, "Quarterly payroll data.", display=f"{statistics.median(contract):.1f}%"),
        stat("contract_10pct_homes", sum(1 for c in contract if c >= 10),
             f"of {len(contract)} homes used contract staff for 10% or more of nursing hours",
             qlabel, "CMS Payroll-Based Journal", STAFFING_TOOL, "Quarterly payroll data."),
        stat("avg_daily_residents", int(round(census, -2)), "residents in Connecticut nursing homes on an average day",
             qlabel, "CMS Payroll-Based Journal resident census", STAFFING_TOOL,
             "Sum of each reporting home's average daily census, rounded to the nearest hundred.", display=f"About {int(round(census, -2)):,}"),
    ]

    # A quarter where many homes did not submit PBJ undercounts statewide totals: say so on every stat for it.
    prev = context["statewide_quarterly"][-2] if len(context["statewide_quarterly"]) > 1 else None
    missing = [f for f in staffing["facilities"] if f["ccn"] not in {r["ccn"] for r in rows}]
    not_submitted = sum(1 for f in missing if str(f.get("cms_staffing_rating_footnote") or "") == "23")
    if prev and latest["facilities_reporting"] < 0.95 * prev["facilities_reporting"]:
        gap = (f" Only {latest['facilities_reporting']} homes reported PBJ for {qlabel}, against {prev['facilities_reporting']} in {prev['quarter_label']}"
               + (f"; CMS lists {not_submitted} as not submitting staffing data" if not_submitted else "")
               + ". Totals for this quarter are not comparable with earlier quarters.")
        for st in stats:
            if st["period"] == qlabel:
                st["caveat"] = (st["caveat"] + gap).strip()

    fac = staffing["facilities"]
    owner = {"For profit": 0, "Non profit": 0, "Government": 0}
    for f in fac:
        kind = (f.get("ownership_type") or "").split(" - ")[0]
        if kind in owner:
            owner[kind] += 1
    rated = [f.get("cms_overall_rating") for f in fac if f.get("cms_overall_rating")]
    prov = next((x for x in staffing["sources"] if "Provider Information" in x.get("source_dataset_name", "")), {})
    m = re.search(r"_([A-Z][a-z]{2})(\d{4})", prov.get("source_release", ""))
    prov_label = f"CMS Provider Information, {m.group(1)} {m.group(2)}" if m else "CMS Provider Information"
    stats += [
        stat("for_profit_homes", owner["For profit"], f"of {len(fac)} Connecticut nursing homes are for-profit",
             prov_label, "CMS Nursing Home Provider Information", EXPLORER, "Ownership type as reported to CMS."),
        stat("low_star_homes", sum(1 for r in rated if r <= 2), f"of {len(rated)} rated homes have a 1- or 2-star CMS overall rating",
             prov_label, "CMS Care Compare star ratings", EXPLORER, "CMS ratings, not calculated by these tools."),
    ]

    sf = survey["facilities"]
    meta = survey["metadata"]
    window = meta["recent_window_definition"]
    period = f"{nice_date(window['start_date'])} to {nice_date(window['end_date'])}"
    s = lambda k: int(sum(f.get(k) or 0 for f in sf))
    stats += [
        stat("health_citations_3yr", s("recent_health_deficiency_count"), "federal health inspection citations at Connecticut nursing homes",
             period, "CMS Health Deficiencies", EXPLORER, "Citation counts are context, not a quality score."),
        stat("harm_citations_3yr", s("recent_actual_harm_count"), "citations where inspectors found actual harm to a resident",
             period, "CMS Health Deficiencies", EXPLORER, "Scope and severity as recorded by CMS."),
        stat("ij_citations_3yr", s("recent_immediate_jeopardy_count"), "immediate jeopardy citations (risk of serious injury or death)",
             period, "CMS Health Deficiencies", EXPLORER, "Scope and severity as recorded by CMS."),
        stat("federal_fines_3yr", s("recent_fine_count"),
             f"federal fines, totaling ${int(sum(f.get('recent_fine_total') or 0 for f in sf)):,}, at {sum(1 for f in sf if f.get('recent_fine_count'))} homes",
             f"{nice_date(meta['source_date_ranges']['penalty_dates']['min'])} to {nice_date(meta['source_date_ranges']['penalty_dates']['max'])}",
             "CMS Penalties", EXPLORER, "Fines are enforcement values, not quality scores; files may not be exhaustive."),
    ]

    pm = {m["label"]: m["value"] for m in impact["primaryMetrics"]}
    cap = {c["label"]: c.get("value", c.get("displayValue")) for c in impact["facilityAccess"]["capacity"]}
    cats = {c["label"]: c for c in impact["complaints"]["categories"]}
    details = {d["label"]: d["count"] for c in impact["complaints"]["categories"] for d in c.get("details", [])}
    clos = {m["label"]: m["value"] for m in impact["closures"]["metrics"]}
    src = impact["source"]["title"]
    fy = impact["meta"]["fiscalYear"]
    stats += [
        stat("ltcop_complaints", pm["Complaints received"], "complaints received by the Long Term Care Ombudsman Program", fy, src, IMPACT, "Program-reported counts."),
        stat("ltcop_discharge_complaints", details["Discharge or eviction"], "complaints about discharge or eviction", fy, src, IMPACT, "Program-reported counts."),
        stat("ltcop_transfer_category", cats["Admission, Transfer, Discharge, and Eviction"]["count"],
             f"complaints about admission, transfer, discharge and eviction ({cats['Admission, Transfer, Discharge, and Eviction']['percent']}% of all)", fy, src, IMPACT, "Program-reported counts."),
        stat("ltcop_rights_category", cats["Autonomy, Choice, and Rights"]["count"],
             f"complaints about autonomy, choice and rights ({cats['Autonomy, Choice, and Rights']['percent']}% of all)", fy, src, IMPACT, "Program-reported counts."),
        stat("ltcop_care_category", cats["Care"]["count"], f"complaints about care ({cats['Care']['percent']}% of all), the largest category", fy, src, IMPACT, "Program-reported counts."),
        stat("ltcop_visits", pm["Total facility visits"], f"Ombudsman facility visits, reaching {pm['Facilities visited']} facilities", fy, src, IMPACT, "Program-reported counts."),
        stat("ltcop_volunteers", pm["Certified Volunteer Resident Advocates"], "certified volunteer resident advocates (as of Sept. 30, 2025)", fy, src, IMPACT, "Program-reported counts."),
        stat("ltcop_funding", impact["funding"]["totalDisplay"], "total operating budget", fy, src, IMPACT, "As reported in the annual report.", display="$2.42 million"),
        stat("snf_count", cap["Skilled nursing facilities"], f"skilled nursing facilities with {cap['Skilled nursing facility beds']:,} beds", fy, src, IMPACT, "Statewide capacity as reported."),
        stat("rch_count", cap["Residential care homes"], f"residential care homes with {cap['Residential care home beds']:,} beds", fy, src, IMPACT, "Statewide capacity as reported."),
        stat("al_units", cap["Assisted living units or apartments"], "assisted living units or apartments", fy, src, IMPACT, "Statewide capacity as reported.", display=str(cap["Assisted living units or apartments"])),
        stat("nf_closures", clos["Nursing facility closures"],
             f"nursing facility closures, plus {clos['Residential care home closure']} residential care home closure and {clos['Evacuation events']} evacuations", fy, src, IMPACT, "Program-reported events."),
    ]
    keys = [x["key"] for x in stats]
    assert len(keys) == len(set(keys)), "duplicate stat keys"
    return {
        "schema_version": "ct-legislative-research-stats-1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "note": "Computed from data files published on this site. Each stat lists its source, period and caveat.",
        "stats": stats,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = build()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} ({len(result['stats'])} stats)")


if __name__ == "__main__":
    main()
