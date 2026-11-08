"""Build data/ct_cost_report_insights.json: one compact table of every home's cost-report figures by year,
with statewide bands, peer groups, events (ownership, management, administrator changes) and an inflation index,
for the Cost Report Insights page (trends, comparisons, peer groups, pivot, scatter, money flow).

Inputs (all already published or committed): data/ct_nursing_home_cost_reports.json, data/cost_reports/<ccn>.json,
data/nursing_home_staffing_ct.json (beds, ownership type, affiliation), data/nursing_home_facility_geography_ct.json
(county, LTCOP region), data/reference/cpi_u_us_city_average.json (CPI-U, for constant dollars).
"""
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ct_cost_report_insights.json"
SCHEMA = "ct-cost-report-insights-1.0"

# key, label, unit, group, definition. Order = column order of each home-year's value array.
METRICS = [
    ("expenses", "Total costs", "money", "Totals", "Total nursing-home costs (page 27, line 15) per resident day."),
    ("revenue", "Total revenue", "money", "Totals", "Total nursing-home revenue (page 30) per resident day."),
    ("margin", "Operating margin", "pct", "Totals", "(Revenue - costs) / revenue, nursing home only."),
    ("nursing", "Nursing care (direct care)", "money", "Categories", "Nursing and aide salaries, nursing agency and their benefits, per resident day."),
    ("dietary", "Dietary, all-in", "money", "Categories", "Kitchen staff and benefits, food, supplies and contracts, per resident day."),
    ("housekeeping", "Housekeeping, all-in", "money", "Categories", "Housekeeping staff and benefits, supplies and contracts, per resident day."),
    ("laundry", "Laundry, all-in", "money", "Categories", "Laundry staff and benefits, supplies and contracts, per resident day."),
    ("other_staff", "All other staff and benefits", "money", "Categories", "Remaining salaries and benefits (administration, maintenance, activities, therapy staff, etc.), per resident day."),
    ("other_fees", "Other professional fees", "money", "Categories", "Fees in lieu of salaries other than nursing agency (therapy, medical director, consultants), per resident day."),
    ("admin", "Administrative and general", "money", "Categories", "Administrative and general costs other than salaries and benefits, including management fees, per resident day."),
    ("resident_care", "Resident care supplies", "money", "Categories", "Drugs, medical supplies, oxygen, lab, recreation and other resident care costs, per resident day."),
    ("plant", "Plant operation and utilities", "money", "Categories", "Repairs, heat, light and power, water and equipment leases, per resident day."),
    ("property", "Building and property", "money", "Categories", "Rent, depreciation, amortization and property taxes, per resident day."),
    ("interest", "Interest", "money", "Categories", "Interest expense, per resident day."),
    ("insurance", "Insurance", "money", "Categories", "Insurance, per resident day."),
    ("raw_food", "Raw food (homes that buy their own)", "money", "Details", "Raw food line (page 18, 2a1) per resident day, only when the home buys its own food."),
    ("management_fees", "Management fees", "money", "Details", "Administrative management services (page 16, line m12) per resident day."),
    ("rent", "Rent on leased real property", "money", "Details", "Page 22, line 9, per resident day."),
    ("rent_related", "Rent or lease paid to related parties", "money", "Details", "Page 4 related-party lines for rent, lease or real estate, per resident day."),
    ("related_parties", "All payments to related parties", "money", "Details", "Every related-party cost on page 4 except loans and balances, per resident day."),
    ("agency", "Nursing agency (pool)", "money", "Details", "Nursing pool fees for RNs, LPNs and aides (page 13), per resident day."),
    ("utilities", "Utilities", "money", "Details", "Heat, light and power, and water (page 22, 6b-6d), per resident day."),
    ("direct_share", "Direct care share of costs", "pct", "Staffing and payers", "Direct care as a share of total costs."),
    ("hours", "Nursing hours per resident day (cost report)", "hours", "Staffing and payers", "Paid nursing and aide hours (pages 10 and 13) per resident day."),
    ("pbj_hours", "Nursing hours per resident day (PBJ, same months)", "hours", "Staffing and payers", "CMS Payroll-Based Journal hours worked for the same months."),
    ("medicaid_share", "Medicaid share of days", "pct", "Staffing and payers", "Connecticut Medicaid days as a share of all care days."),
]
KEYS = [m[0] for m in METRICS]
# Eight groups for "share of every dollar" and the money-flow chart (keeps the chart at <= 8 colors).
GROUPS = [
    ("nursing", "Nursing care", ["nursing"]),
    ("support", "Dietary, housekeeping and laundry", ["dietary", "housekeeping", "laundry"]),
    ("staff", "Other staff and professional fees", ["other_staff", "other_fees"]),
    ("admin", "Administrative and general", ["admin"]),
    ("property", "Building and property", ["property"]),
    ("plant", "Plant operation and utilities", ["plant"]),
    ("care", "Resident care supplies", ["resident_care"]),
    ("finance", "Interest and insurance", ["interest", "insurance"]),
]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def size_bucket(beds):
    if not beds:
        return None
    return "Under 90 beds" if beds < 90 else "90 to 129 beds" if beds < 130 else "130 to 179 beds" if beds < 180 else "180 beds or more"


def medicaid_bucket(share):
    if share is None:
        return None
    return "Under 60% Medicaid" if share < 0.6 else "60% to 74% Medicaid" if share < 0.75 else "75% to 84% Medicaid" if share < 0.85 else "85% or more Medicaid"


def cost_year_cpi(cpi):
    """Average CPI-U over each cost year (October of the prior year to September)."""
    out = {}
    for y in range(2015, 2026):
        months = [f"{y - 1}-{m:02d}" for m in (10, 11, 12)] + [f"{y}-{m:02d}" for m in range(1, 10)]
        vals = [cpi["monthly"][k] for k in months if k in cpi["monthly"]]
        if len(vals) == 12:
            out[y] = sum(vals) / 12
    return out


def year_values(y):
    """Per-resident-day figures for one cost year of one home (detail record). None where withheld."""
    d = y.get("direct_care") or {}
    rd = y.get("resident_days") or {}
    days = rd.get("resident_days_total") or rd.get("days_total_care")
    bad = set(y["checks"].get("out_of_range") or [])
    if not days or "resident days vs beds" in bad:
        return None
    cb = y.get("cost_breakdown") or {}
    cats = cb.get("categories") or {} if cb.get("adds_up") else {}
    det = cb.get("details") or {} if cb.get("adds_up") else {}
    food = ((y.get("support_services") or {}).get("food") or {})
    v = {
        "expenses": d.get("expenses_per_resident_day"),
        "revenue": d.get("revenue_per_resident_day"),
        "margin": d.get("operating_margin_nh"),
        "raw_food": food.get("raw_food_per_resident_day"),
        "management_fees": (det.get("management_fees") or {}).get("per_resident_day"),
        "rent": (det.get("rent") or {}).get("per_resident_day"),
        "rent_related": (det.get("rent_or_lease_paid_to_related_parties") or {}).get("per_resident_day"),
        "utilities": (det.get("utilities") or {}).get("per_resident_day"),
        "related_parties": round(y["related_party_total_reported"] / days, 2) if y.get("related_party_total_reported") else None,
        "agency": round(d["nursing_pool"] / days, 2) if d.get("nursing_pool") is not None else None,
        "direct_share": d.get("direct_care_share_of_expenses"),
        "hours": d.get("nursing_hours_per_resident_day"),
        "pbj_hours": (y.get("pbj_same_period") or {}).get("total_nurse_hprd"),
        "medicaid_share": (y.get("payer_mix") or {}).get("medicaid_ct"),
    }
    for k in ("nursing", "dietary", "housekeeping", "laundry", "other_staff", "other_fees", "admin", "resident_care",
              "plant", "property", "interest", "insurance"):
        v[k] = (cats.get(k) or {}).get("per_resident_day")
    # direct-care range withholding, as on the Cost Reports page
    if bad & {"direct care per resident day", "direct care share of expenses"}:
        v["direct_share"] = None
    if "nursing hours per resident day" in bad:
        v["hours"] = None
    return v


def main():
    idx = load(ROOT / "data" / "ct_nursing_home_cost_reports.json")
    staffing = {f["ccn"]: f for f in load(ROOT / "data" / "nursing_home_staffing_ct.json")["facilities"]}
    geo = {f["ccn"]: f for f in load(ROOT / "data" / "nursing_home_facility_geography_ct.json")["facilities"]}
    cpi = load(ROOT / "data" / "reference" / "cpi_u_us_city_average.json")
    cy_cpi = cost_year_cpi(cpi)
    latest_cpi_year = max(cy_cpi)
    years = sorted(int(y) for y in idx["statewide_medians"])

    homes, mgmt_groups, aff_groups = [], {}, {}
    pool = {k: {y: [] for y in years} for k in KEYS}
    for row in idx["facilities"]:
        ccn = row["ccn"]
        path = ROOT / "data" / "cost_reports" / f"{ccn}.json"
        if not path.exists():
            continue
        det = load(path)
        if not det["cost_years"]:
            continue
        st, g = staffing.get(ccn) or {}, geo.get(ccn) or {}
        yrs, events, mgmt_seen, admin_seen = {}, [], {}, {}
        for y in det["cost_years"]:
            vals = year_values(y)
            if vals is None:
                continue
            cy = y["cost_year"]
            arr = [vals.get(k) for k in KEYS]
            yrs[str(cy)] = {"ok": bool(y["checks"]["validated"]), "part": bool(y["part_year"]), "v": arr}
            if y["checks"]["validated"] and not y["part_year"]:
                for k, x in zip(KEYS, arr):
                    if x is not None:
                        pool[k][cy].append(x)
            for m in y.get("cms_management_during_year") or []:
                key = m.get("company_id") or m.get("name")
                if key not in mgmt_seen or (m.get("start") or "9999") < (mgmt_seen[key].get("start") or "9999"):
                    mgmt_seen[key] = m
                grp = mgmt_groups.setdefault(m.get("company_id") or m.get("name"), {"name": m.get("name"), "homes": {}})
                grp["homes"].setdefault(ccn, set()).add(cy)
            for a in y.get("administrators_during_year") or []:
                key = a.get("license_number") or a.get("name")
                if key not in admin_seen:
                    admin_seen[key] = a
        if not yrs:
            continue
        first, last = min(yrs), max(yrs)
        for e in det.get("changes_of_ownership") or []:
            events.append({"date": e.get("effective_date"), "type": "ownership",
                           "label": f"Change of ownership: {e.get('seller') or '?'} to {e.get('buyer') or '?'}"})
        for m in mgmt_seen.values():
            if m.get("start"):
                events.append({"date": m["start"], "type": "management", "label": f"Management of record (CMS): {m.get('name')}"})
        for a in admin_seen.values():
            if a.get("start"):
                events.append({"date": a["start"], "type": "administrator", "label": f"Administrator of record (DPH): {a.get('name')}"})
        # keep events inside the window the charts show (cost year 'first' starts the October before)
        lo, hi = f"{int(first) - 1}-10-01", f"{last}-09-30"
        events = sorted((e for e in events if e["date"] and lo <= e["date"] <= hi), key=lambda e: e["date"])
        aff = st.get("affiliation_entity_name")
        if aff:
            aff_groups.setdefault(aff, set()).add(ccn)
        latest_ms = next((yrs[y]["v"][KEYS.index("medicaid_share")] for y in sorted(yrs, reverse=True)
                          if yrs[y]["v"][KEYS.index("medicaid_share")] is not None), None)
        beds = st.get("certified_beds")
        homes.append({"ccn": ccn, "name": row["facility_name"], "current": row["current"],
                      "city": (g.get("municipality") or st.get("city") or "").title() or None,
                      "county": g.get("county_name"), "region": g.get("ltcop_region"),
                      "beds": int(beds) if beds else None, "size": size_bucket(beds),
                      "ownership": st.get("ownership_type"), "affiliation": aff,
                      "medicaid_band": medicaid_bucket(latest_ms),
                      "management": sorted({m.get("company_id") or m.get("name") for m in mgmt_seen.values()}),
                      "years": yrs, "events": events})

    def q(vals, p):
        s = sorted(vals)
        i = (len(s) - 1) * p
        lo = int(i)
        return s[lo] + (s[min(lo + 1, len(s) - 1)] - s[lo]) * (i - lo)

    bands = {}
    for k in KEYS:
        bands[k] = {}
        for y in years:
            v = pool[k][y]
            if len(v) >= 10:
                nd = 4 if METRICS[KEYS.index(k)][2] == "pct" else 2
                bands[k][str(y)] = [round(q(v, 0.25), nd), round(statistics.median(v), nd), round(q(v, 0.75), nd), len(v)]

    out = {
        "schema_version": SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_index": "data/ct_nursing_home_cost_reports.json",
        "years": years,
        "metrics": [{"key": k, "label": l, "unit": u, "group": g, "definition": d} for k, l, u, g, d in METRICS],
        "groups": [{"key": k, "label": l, "metrics": m} for k, l, m in GROUPS],
        "cpi": {"title": cpi["title"], "url": cpi["url"], "base_year": latest_cpi_year,
                "factor_to_base": {str(y): round(cy_cpi[latest_cpi_year] / v, 5) for y, v in cy_cpi.items()}},
        "bands": bands,
        "management_companies": {k: {"name": v["name"], "homes": sorted(v["homes"])} for k, v in mgmt_groups.items()},
        "affiliations": {k: sorted(v) for k, v in sorted(aff_groups.items())},
        "homes": homes,
        "method": {
            "values": "Every figure comes from the home's DSS cost report as published on the Cost Reports page, per "
                      "resident day of the nursing home. Figures that failed a range check there are left out here.",
            "bands": "The shaded band is the middle half of Connecticut homes that year (25th to 75th percentile) and "
                     "the line inside it the median, from full-year filings that passed every check.",
            "constant_dollars": f"Constant dollars multiply each cost year by the ratio of CPI-U (all urban consumers, "
                                f"US city average) for cost year {latest_cpi_year} to CPI-U for that cost year, each "
                                f"averaged over October to September. It removes general inflation only.",
            "events": "Ownership changes are CMS change-of-ownership records; management companies are CMS management of "
                      "record (with DPH); administrators are DPH records. They show what changed and when, not why.",
            "peer_groups": "Peer groups: management company of record in any cost year, CMS affiliated entity (chain), "
                           "county and LTCOP region, certified beds, CMS ownership type, and Medicaid share of days in "
                           "the home's latest report.",
            "not_quality": "These are the homes' own reported costs. They are not a measure of care quality and are not "
                           "rankings.",
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(homes)} homes, {sum(len(h['years']) for h in homes)} home-years, "
          f"{len(out['management_companies'])} management companies, {len(aff_groups)} affiliations, "
          f"{OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
