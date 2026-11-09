"""Build public Connecticut nursing home cost-report data (DSS annual cost reports) linked to CMS data.

Private inputs (git-ignored, data/testing/cost_reports/):
  extract_all.json          figures + entities read from each DSS 'Annual Report of Long-Term Care Facility'
                            (see docs/nursing_home_cost_reports_runbook.md for how it is produced)
  cost_report_index.json    each PDF matched to a CMS CCN, with match evidence
  all_owners/<YYYY-MM>/     CT rows of CMS 'Skilled Nursing Facility All Owners' monthly releases
  providerinfo/<release>.csv CT rows of CMS Care Compare Provider Information (legal business name -> CCN)
  SNF_CHOW_<date>.csv       CMS 'Skilled Nursing Facility Change of Ownership' (cumulative)
Public inputs: data/nursing_home_staffing_history_ct.json, data/ct_nursing_home_management_companies.json,
               data/ct_nursing_home_administrators.json, data/nursing_home_staffing_ct.json

Outputs:
  data/ct_nursing_home_cost_reports.json        statewide index: per home, per cost year headline figures
  data/cost_reports/<ccn>.json                  per home detail (every year, related parties, owners, CHOW)
"""
from __future__ import annotations

import argparse
import csv
import glob
import datetime as dt
import json
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from cost_reports.cr_entities import RELATED_PARTY_METHOD, included_related, is_related_rent

ROOT = Path(__file__).resolve().parents[1]
PRIV = ROOT / "data" / "testing" / "cost_reports"
OUT_INDEX = ROOT / "data" / "ct_nursing_home_cost_reports.json"
OUT_DIR = ROOT / "data" / "cost_reports"
SCHEMA = "ct-nursing-home-cost-reports-1.0"

CAVEATS = [
    "Figures are as reported by each nursing home on its Connecticut DSS 'Annual Report of Long-Term Care "
    "Facility' for the cost year ending September 30. They are the home's own filing, before DSS audit or "
    "rate-setting adjustments, and are not Medicaid-allowable costs.",
    "Figures were read from the published PDFs by software. Scanned reports were read with OCR. Each figure "
    "is checked against the totals printed on the same report; figures that fail a check are marked.",
    "Direct care follows the DSS rate-setting definition: nursing and nurse-aide salaries, related fringe "
    "benefits, and nursing pool (agency) costs. Fringe benefits are not reported by job, so the direct-care "
    "share of fringe is allocated in proportion to nursing salaries.",
    "Owner, officer and related-party names, addresses and amounts are shown as written on the report and in "
    "CMS ownership data. Addresses may be business or personal addresses as filed.",
    "Being listed as an owner or related party is not an allegation of wrongdoing. Spending figures are not a "
    "measure of care quality.",
]
CORRECTIONS = "Records come from public state and federal sources. To report an error, email hello@danbeem.xyz."


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def norm(s):
    return " ".join(re.sub(r"[^A-Z0-9 ]+", " ", (s or "").upper().replace("&", " AND ")).split())


def r0(x, n=0):
    return None if x is None else (round(x, n) if n else int(round(x)))


# ---------------------------------------------------------------- CMS: legal name -> CCN, owners, CHOW
def provider_maps():
    by_name, names = {}, defaultdict(set)
    for f in sorted(glob.glob(str(PRIV / "providerinfo" / "*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            k = {c.lower(): c for c in r}
            ccn = r.get(k.get("cms certification number (ccn)") or k.get("federal provider number") or k.get("provnum"), "").zfill(6)
            ln = r.get(k.get("legal business name", ""), "") if "legal business name" in k else ""
            if ln and "NOT AVAILABLE" not in ln.upper():
                by_name[norm(ln)] = ccn
            names[ccn].add(r.get(k.get("provider name") or k.get("provname"), ""))
    return by_name, names


def cms_owners(by_name):
    """CMS SNF All Owners: per CCN, every owner seen with first/last release; latest snapshot in full."""
    releases = sorted(d for d in os.listdir(PRIV / "all_owners") if (PRIV / "all_owners" / d).is_dir())
    seen = defaultdict(dict)   # ccn -> key -> record
    enr_ccn = {}
    for rel in releases:
        fs = glob.glob(str(PRIV / "all_owners" / rel / "SNF_All_Owners*.csv"))
        if not fs:
            continue
        for r in csv.DictReader(open(fs[0], encoding="utf-8")):
            ccn = by_name.get(norm(r["ORGANIZATION NAME"]))
            if not ccn:
                continue
            enr_ccn.setdefault(r["ENROLLMENT ID"], set()).add(ccn)
            person = r["TYPE - OWNER"] == "I"
            name = (" ".join(x for x in (r["FIRST NAME - OWNER"], r["MIDDLE NAME - OWNER"], r["LAST NAME - OWNER"]) if x)
                    if person else r["ORGANIZATION NAME - OWNER"])
            key = (r["ASSOCIATE ID - OWNER"], r["ROLE CODE - OWNER"], r["ENROLLMENT ID"])
            rec = seen[ccn].get(key)
            flags = [c.replace(" - OWNER", "").title() for c in (
                "CREATED FOR ACQUISITION - OWNER", "CORPORATION - OWNER", "LLC - OWNER", "MEDICAL PROVIDER SUPPLIER - OWNER",
                "MANAGEMENT SERVICES COMPANY - OWNER", "MEDICAL STAFFING COMPANY - OWNER", "HOLDING COMPANY - OWNER",
                "INVESTMENT FIRM - OWNER", "FINANCIAL INSTITUTION - OWNER", "CONSULTING FIRM - OWNER", "FOR PROFIT - OWNER",
                "NON PROFIT - OWNER", "PRIVATE EQUITY COMPANY - OWNER", "REIT - OWNER", "CHAIN HOME OFFICE - OWNER",
                "TRUST OR TRUSTEE - OWNER", "OTHER TYPE - OWNER", "PARENT COMPANY - OWNER",
                "OWNED BY ANOTHER ORG OR IND - OWNER") if r.get(c) == "Y"]
            addr = ", ".join(x for x in (r["ADDRESS LINE 1 - OWNER"], r["ADDRESS LINE 2 - OWNER"], r["CITY - OWNER"],
                                         r["STATE - OWNER"], r["ZIP CODE - OWNER"][:5]) if x) or None
            if rec is None:
                seen[ccn][key] = rec = {
                    "associate_id": r["ASSOCIATE ID - OWNER"], "type": "Individual" if person else "Organization",
                    "name": " ".join(name.split()), "title": r["TITLE - OWNER"] or None,
                    "role": r["ROLE TEXT - OWNER"].title(), "association_date": r["ASSOCIATION DATE - OWNER"] or None,
                    "percent": float(r["PERCENTAGE OWNERSHIP"]) if r["PERCENTAGE OWNERSHIP"] else None,
                    "address": addr, "flags": flags, "first_release": rel, "last_release": rel,
                    "enrollment_id": r["ENROLLMENT ID"]}
            rec["last_release"] = rel
            rec["percent"] = float(r["PERCENTAGE OWNERSHIP"]) if r["PERCENTAGE OWNERSHIP"] else rec["percent"]
            rec["address"] = addr or rec["address"]
            rec["flags"] = flags or rec["flags"]
    latest = releases[-1]
    out = {}
    for ccn, recs in seen.items():
        rows = sorted(recs.values(), key=lambda x: (x["last_release"] != latest, x["role"], -(x["percent"] or 0), x["name"]))
        for x in rows:
            x["current"] = x["last_release"] == latest
        out[ccn] = rows
    return out, releases


def chow_events():
    f = sorted(glob.glob(str(PRIV / "SNF_CHOW_*.csv")))[-1]
    ev = defaultdict(list)
    for r in csv.DictReader(open(f, encoding="utf-8-sig", errors="replace")):
        for ccn in {r["CCN - BUYER"], r["CCN - SELLER"]}:
            if ccn.startswith("07"):
                d = datetime.strptime(r["EFFECTIVE DATE"], "%m/%d/%Y").date().isoformat()
                ev[ccn].append({"effective_date": d, "type": r["CHOW TYPE TEXT"].title(),
                                "seller": r["ORGANIZATION NAME - SELLER"], "seller_dba": r["DOING BUSINESS AS NAME - SELLER"] or None,
                                "seller_associate_id": r["ASSOCIATE ID - SELLER"],
                                "buyer": r["ORGANIZATION NAME - BUYER"], "buyer_dba": r["DOING BUSINESS AS NAME - BUYER"] or None,
                                "buyer_associate_id": r["ASSOCIATE ID - BUYER"]})
    for v in ev.values():
        v.sort(key=lambda x: x["effective_date"])
        uniq, seen = [], set()
        for x in v:
            k = (x["effective_date"], x["buyer_associate_id"], x["seller_associate_id"])
            if k not in seen:
                seen.add(k); uniq.append(x)
        v[:] = uniq
    return ev, os.path.basename(f)


# ---------------------------------------------------------------- PBJ comparison for a DSS cost year
def pbj_quarters(history):
    """PBJ rows keyed by CCN: [(quarter_start, quarter_end, resident_days, metrics)]."""
    out = defaultdict(list)
    for r in history["facility_quarterly_staffing_history"]:
        days = r.get("resident_days") or 0
        m = r.get("metrics") or {}
        if not days or m.get("total_nurse_hprd") is None:
            continue
        y, q = int(r["quarter"][:4]), int(r["quarter"][-1])
        qs = dt.date(y, 3 * q - 2, 1)
        qe = dt.date(y + (q == 4), 1 if q == 4 else 3 * q + 1, 1) - dt.timedelta(days=1)
        out[r["ccn"]].append((qs, qe, days, m))
    return out


def pbj_for_period(rows, start, end):
    """Resident-day-weighted PBJ for the quarters that overlap the report period.
    A full cost year (Oct 1 - Sep 30) is PBJ quarters Q4 of the prior year through Q3."""
    a = {"days": 0.0, "hrs": 0.0, "rn": 0.0, "lpn": 0.0, "aide": 0.0, "q": 0, "contract": 0.0}
    for qs, qe, days, m in rows:
        if qe < start or qs > end:
            continue
        a["days"] += days; a["q"] += 1
        a["hrs"] += m["total_nurse_hprd"] * days
        a["rn"] += (m.get("rn_hprd") or 0) * days
        a["lpn"] += (m.get("lpn_lvn_hprd") or 0) * days
        a["aide"] += (m.get("nurse_aide_hprd") or 0) * days
        a["contract"] += (m.get("contract_staff_pct") or 0) * days
    if not a["days"]:
        return None
    return {"quarters": a["q"], "resident_days": r0(a["days"]),
            "total_nurse_hprd": round(a["hrs"] / a["days"], 2), "rn_hprd": round(a["rn"] / a["days"], 2),
            "lpn_hprd": round(a["lpn"] / a["days"], 2), "aide_hprd": round(a["aide"] / a["days"], 2),
            "contract_staff_pct": round(a["contract"] / a["days"], 1)}


def report_period(o):
    """(start, end, read_from_report) for one extracted report; defaults to the standard DSS cost year."""
    p = o.get("period")
    if p:
        return dt.date.fromisoformat(p["start"]), dt.date.fromisoformat(p["end"]), True
    return dt.date(o["year"] - 1, 10, 1), dt.date(o["year"], 9, 30), False


# ---------------------------------------------------------------- per-report public record
FIELDS = {
    "capacity": ["beds_certified", "residents_end"],
    "resident_days": ["days_medicaid_ct", "days_medicaid_other_states", "days_medicare", "days_private",
                      "days_other_payer", "days_total_care", "days_bed_reserve_medicaid", "resident_days_total"],
    "salaries": ["sal_owners", "sal_administrator", "sal_asst_administrator", "sal_don", "sal_rn_direct", "sal_rn_admin",
                 "sal_lpn_direct", "sal_lpn_admin", "sal_aides", "sal_total"],
    "hours": ["hrs_don", "hrs_rn_direct", "hrs_rn_admin", "hrs_lpn_direct", "hrs_lpn_admin", "hrs_aides", "hrs_total"],
    "nursing_pool": ["pool_rn_direct", "pool_rn_admin", "pool_lpn_direct", "pool_lpn_admin", "pool_aides",
                     "pool_hrs_rn_direct", "pool_hrs_lpn_direct", "pool_hrs_aides", "prof_fees_total"],
    "fringe": ["fringe_workers_comp", "fringe_disability", "fringe_unemployment", "fringe_fica", "fringe_health",
               "fringe_life", "fringe_pension", "fringe_uniform", "fringe_other", "fringe_total"],
    "expenses": ["ag_total", "mgmt_fee_m12", "dietary_total", "laundry_total", "housekeeping_total", "resident_care_total",
                 "maint_operating_total", "property_total", "interest_total", "insurance_total", "expenses_total_ccnh",
                 "expenses_total_all", "expenses_total_p36"],
    "revenue": ["rev_medicaid_ct", "rev_medicare", "rev_private", "rev_resident_total", "rev_other_total", "rev_total",
                "rev_total_all", "revenue_total_p36"],
    "support": ["sal_head_dietitian", "sal_food_supervisor", "sal_dietary_workers", "diet_raw_food",
                "diet_nonfood_supplies", "diet_other_inhouse", "diet_purchased_services", "diet_other",
                "sal_head_housekeeper", "sal_housekeeping_workers", "hk_supplies", "hk_purchased_services",
                "sal_laundry_supervisor", "sal_laundry_workers", "laundry_purchased_services"],
    "plant_and_property": ["plant_repairs", "plant_heat", "plant_light_power", "plant_water", "plant_equipment_lease",
                           "property_depreciation", "property_amortization", "property_rent", "property_tax_owner",
                           "property_tax_lessor", "property_tax_personal"],
    "balance_sheet": ["assets_current", "assets_total", "liabilities_current", "liabilities_long_term",
                      "liabilities_total", "net_worth", "net_income_p36"],
}


def plausible(f, d):
    """Flag figures outside plausible ranges (usually an OCR or layout misread)."""
    bad = []
    days = f.get("resident_days_total") or f.get("days_total_care")
    beds = f.get("beds_certified")
    if days and beds and not (0.2 * beds * 365 <= days <= 1.05 * beds * 366):
        bad.append("resident days vs beds")
    v = d.get("direct_care_per_resident_day")
    if v is not None and not (40 <= v <= 900):
        bad.append("direct care per resident day")
    h = d.get("nursing_hours_per_resident_day")
    if h is not None and not (1.5 <= h <= 12):
        bad.append("nursing hours per resident day")
    s = d.get("direct_care_share_of_expenses")
    if s is not None and not (0.15 <= s <= 0.85):
        bad.append("direct care share of expenses")
    return bad


# Support services per resident day. Ranges outside these are almost always a misread line.
SUPPORT_RANGES = {"raw_food": (2, 40), "dietary": (5, 120), "housekeeping": (1, 60), "laundry": (0.5, 40)}
RAW_FOOD_MIN_PRD = 3.0       # below this the home is not buying most of its own food
CONTRACT_SHARE_MAX = 0.5     # contract dietary services at or above this share of (raw food + contract) = food by contractor


def support_services(f, days):
    """Food, dietary, housekeeping and laundry cost per resident day, with how each was reached.
    Department cost = its salaries (page 10) + their share of fringe benefits (page 15, by share of all salaries)
    + the department's non-salary total (pages 18, 19, 20: supplies, contracts, other)."""
    if not days:
        return None
    g = lambda k: f.get(k) or 0
    sal_total, fringe = f.get("sal_total"), f.get("fringe_total")
    fr_rate = fringe / sal_total if fringe and sal_total else 0
    out, flags = {"fringe_rate": round(fr_rate, 4)}, []

    def dept(name, sal_keys, nonsal_key):
        sal = sum(g(k) for k in sal_keys)
        nonsal = f.get(nonsal_key)
        if not sal and not nonsal:
            return None
        fr = sal * fr_rate
        total = sal + fr + (nonsal or 0)
        prd = round(total / days, 2)
        lo, hi = SUPPORT_RANGES[name]
        if not (lo <= prd <= hi):
            flags.append(f"{name} per resident day")
            return {"salaries": r0(sal), "fringe_allocated": r0(fr), "non_salary": r0(nonsal), "total": r0(total),
                    "per_resident_day": None}
        return {"salaries": r0(sal), "fringe_allocated": r0(fr), "non_salary": r0(nonsal), "total": r0(total),
                "per_resident_day": prd}

    out["dietary"] = dept("dietary", ("sal_head_dietitian", "sal_food_supervisor", "sal_dietary_workers"), "dietary_total")
    out["housekeeping"] = dept("housekeeping", ("sal_head_housekeeper", "sal_housekeeping_workers"), "housekeeping_total")
    out["laundry"] = dept("laundry", ("sal_laundry_supervisor", "sal_laundry_workers"), "laundry_total")

    # dietary lines must add up to the printed dietary total before any part of it is shown
    parts = [g(k) for k in ("diet_raw_food", "diet_nonfood_supplies", "diet_other_inhouse", "diet_purchased_services", "diet_other")]
    dt = f.get("dietary_total")
    close = lambda v: bool(dt) and abs(v - dt) <= max(5, 0.005 * dt)
    # a negative "Other" that is an adjustment printed only in the Total column (e.g. meals sold outside
    # the home) is not part of the nursing-home column: accept the lines if they add up without it
    parts_ok = close(sum(parts)) or close(sum(x for x in parts if x > 0))
    raw, contract = g("diet_raw_food"), g("diet_purchased_services")
    food = {"raw_food": r0(raw) if f.get("diet_raw_food") is not None else None,
            "nonfood_supplies": f.get("diet_nonfood_supplies"), "other_in_house": f.get("diet_other_inhouse"),
            "contract_services": f.get("diet_purchased_services"), "other": f.get("diet_other"),
            "lines_add_up": parts_ok, "raw_food_per_resident_day": None}
    if not parts_ok:
        food["purchasing"] = "unclear"
        flags.append("dietary lines do not add up")
        if out["dietary"]:
            out["dietary"]["per_resident_day"] = None
    else:
        raw_prd = raw / days
        share = contract / (raw + contract) if raw + contract else None
        food["contract_share"] = round(share, 4) if share is not None else None
        if raw_prd >= RAW_FOOD_MIN_PRD and (share or 0) < CONTRACT_SHARE_MAX:
            lo, hi = SUPPORT_RANGES["raw_food"]
            if lo <= raw_prd <= hi:
                food["purchasing"] = "home"
                food["raw_food_per_resident_day"] = round(raw_prd, 2)
            else:
                food["purchasing"] = "unclear"
                flags.append("raw food per resident day")
        elif contract and (share or 0) >= CONTRACT_SHARE_MAX:
            food["purchasing"] = "contractor"
        else:
            food["purchasing"] = "unclear"
    out["food"] = food
    out["dietary_staff_on_payroll"] = bool(g("sal_head_dietitian") + g("sal_food_supervisor") + g("sal_dietary_workers"))
    out["flags"] = flags
    return out


# Every dollar of the nursing home's costs, by category. The categories add back to page 27's printed total.
COST_CATEGORIES = [
    ("nursing", "Nursing care (nursing and aide staff, agency, their benefits)"),
    ("dietary", "Dietary (kitchen staff, benefits, food, supplies, contracts)"),
    ("housekeeping", "Housekeeping (staff, benefits, supplies, contracts)"),
    ("laundry", "Laundry (staff, benefits, supplies, contracts)"),
    ("other_staff", "All other staff and their benefits (administration, maintenance, activities, social work, therapy staff, etc.)"),
    ("other_fees", "Other professional fees (therapy, medical director, consultants and other fees in lieu of salaries)"),
    ("admin", "Administrative and general, non-salary (management fees, legal, accounting, office, advertising, etc.)"),
    ("resident_care", "Resident care supplies and services (drugs, medical supplies, oxygen, lab, recreation)"),
    ("plant", "Plant operation and utilities (repairs, heat, light and power, water, equipment leases)"),
    ("property", "Building and property (rent, depreciation, amortization, property taxes)"),
    ("interest", "Interest"),
    ("insurance", "Insurance"),
]


def cost_breakdown(f, dc, ss, days, related_parties):
    """Split total nursing-home costs into categories per resident day. Withheld unless the categories add up
    to the printed total (page 27, line 15) and none is negative."""
    total = f.get("expenses_total_ccnh")
    if not days or not total or not ss:
        return None
    g = lambda k: f.get(k) or 0
    dept = {k: (ss.get(k) or {}) for k in ("dietary", "housekeeping", "laundry")}
    fringe = g("fringe_total")
    sal_rest = g("sal_total") - (dc.get("direct_salaries") or 0) - sum(d.get("salaries") or 0 for d in dept.values())
    fr_rest = fringe - (dc.get("direct_fringe_allocated") or 0) - sum(d.get("fringe_allocated") or 0 for d in dept.values())
    amounts = {
        "nursing": dc.get("direct_care_total") or 0,
        "dietary": (dept["dietary"].get("salaries") or 0) + (dept["dietary"].get("fringe_allocated") or 0) + g("dietary_total"),
        "housekeeping": (dept["housekeeping"].get("salaries") or 0) + (dept["housekeeping"].get("fringe_allocated") or 0) + g("housekeeping_total"),
        "laundry": (dept["laundry"].get("salaries") or 0) + (dept["laundry"].get("fringe_allocated") or 0) + g("laundry_total"),
        "other_staff": sal_rest + fr_rest,
        "other_fees": g("prof_fees_total") - (dc.get("nursing_pool") or 0),
        "admin": g("ag_total") - fringe,
        "resident_care": g("resident_care_total"),
        "plant": g("maint_operating_total"),
        "property": g("property_total"),
        "interest": g("interest_total"),
        "insurance": g("insurance_total"),
    }
    added = sum(amounts.values())
    ok = abs(added - total) <= max(50, 0.002 * total) and all(v >= -days for v in amounts.values())
    out = {"adds_up": ok, "categories_total": r0(added), "printed_total": r0(total)}
    if not ok:
        return out
    out["categories"] = {k: {"amount": r0(v), "per_resident_day": round(v / days, 2), "share": round(v / total, 4)}
                         for k, v in amounts.items()}
    # detail lines inside the categories
    det = {}
    if f.get("mgmt_fee_m12"):
        det["management_fees"] = f["mgmt_fee_m12"]
    util = g("plant_heat") + g("plant_light_power") + g("plant_water")
    if util and util <= g("maint_operating_total") + 1:
        det["utilities"] = util
    if f.get("plant_equipment_lease"):
        det["equipment_leases"] = f["plant_equipment_lease"]
    prop_parts = {"rent": g("property_rent"), "depreciation": g("property_depreciation"), "amortization": g("property_amortization"),
                  "property_taxes": g("property_tax_owner") + g("property_tax_lessor") + g("property_tax_personal")}
    if abs(sum(prop_parts.values()) - g("property_total")) <= max(50, 0.005 * (g("property_total") or 1)):
        det.update({k: v for k, v in prop_parts.items() if v})
    out["details"] = {k: {"amount": r0(v), "per_resident_day": round(v / days, 2)} for k, v in det.items()}
    apply_related_rent(out, days, related_parties)
    return out


RELATED_RENT = "rent_or_lease_paid_to_related_parties"
RENT_WITHHELD = "rent or lease paid to related parties is larger than building and property"
RELATED_RENT_METHOD = (
    "Rent or lease paid to related parties uses the printed service description to identify rent or lease. "
    "The amount belongs within building and property, and is withheld when it exceeds that category. "
    + RELATED_PARTY_METHOD
)


def apply_related_rent(breakdown, days, rows):
    if not breakdown or not breakdown.get("adds_up") or not days:
        return
    details = breakdown["details"]
    details.pop(RELATED_RENT, None)
    flags = [flag for flag in breakdown.pop("withheld_details", []) if flag != RENT_WITHHELD]
    rent = sum((x.get("cost_reported") or 0) for x in rows if is_related_rent(x))
    property_cost = breakdown["categories"]["property"]["amount"]
    if rent and rent <= property_cost * 1.02 + 50:
        details[RELATED_RENT] = {"amount": r0(rent), "per_resident_day": round(rent / days, 2)}
    elif rent:
        flags.append(RENT_WITHHELD)
    if flags:
        breakdown["withheld_details"] = flags


def set_related_parties(record, entities, companies=None):
    keys = ("name_guess", "text", "description", "category", "where", "cost_reported",
            "actual_cost_to_related_party", "pct_revenue_from_non_related", "row_status")
    rows = [{key: row.get(key) for key in keys} for row in entities.get("related_parties", [])]
    if companies is not None:
        for row in rows:
            row["company_id"] = match_company(row["name_guess"], companies) if not row["row_status"] else None
    record["related_parties"] = rows
    record["related_party_total_reported"] = r0(sum(x["cost_reported"] or 0 for x in rows if included_related(x)))
    unreadable = sum(row["row_status"] == "unreadable" for row in rows)
    if unreadable:
        record["related_party_unreadable_rows"] = unreadable
    else:
        record.pop("related_party_unreadable_rows", None)
    if not entities.get("related_party_page_found"):
        record["related_party_page_found"] = False
    else:
        record.pop("related_party_page_found", None)


# ---------------------------------------------------------------- CMS Medicare cost reports (HCRIS public use file)
CMS_COST_DIR = ROOT / "source_data" / "cms_snf_cost_report"


def _num(v):
    try:
        return float(str(v).replace(",", "")) if str(v).strip() not in ("", "NA") else None
    except ValueError:
        return None


def _mdy(v):
    try:
        return datetime.strptime(v.strip(), "%m/%d/%Y").date()
    except (ValueError, AttributeError):
        return None


def cms_cost_reports():
    """Medicare SNF cost reports (form CMS-2540-10), every US home and fiscal year in the public use file.
    Returns (CT rows by CCN, national and CT medians by fiscal-year-end year, file manifest)."""
    import csv
    manifest = json.loads((CMS_COST_DIR / "manifest.json").read_text(encoding="utf-8")) if (CMS_COST_DIR / "manifest.json").exists() else []
    seen, ct = set(), defaultdict(list)
    pools = defaultdict(lambda: defaultdict(list))   # (scope, year) -> metric -> values
    for path in sorted(CMS_COST_DIR.glob("CostReportsnf_Final_*.csv")):
        with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("rpt_rec_num") in seen:
                    continue
                seen.add(r.get("rpt_rec_num"))
                b, e = _mdy(r.get("Fiscal Year Begin Date")), _mdy(r.get("Fiscal Year End Date"))
                days = _num(r.get("Total Days Total"))
                if not b or not e or not days or days <= 0:
                    continue
                n = lambda k: _num(r.get(k))
                opex, npr = n("Less Total Operating Expense"), n("Net Patient Revenue")
                m = {"operating_expense_per_day": opex / days if opex else None,
                     "salaries_per_day": (n("Total Salaries (adjusted)") or 0) / days if n("Total Salaries (adjusted)") else None,
                     "benefits_per_day": n("Wage-related Costs (core)") / days if n("Wage-related Costs (core)") else None,
                     "contract_labor_per_day": (n("Contract Labor") or 0) / days,
                     "net_patient_revenue_per_day": npr / days if npr else None,
                     "operating_margin": (npr - opex) / npr if npr and opex and npr > 0 else None,
                     "occupancy": days / n("Total Bed Days Available") if n("Total Bed Days Available") else None,
                     "medicaid_share_of_days": (n("Total Days Title XIX") or 0) / days}
                # implausible values are left out (usually a filing error)
                ok = {"operating_expense_per_day": (50, 2500), "salaries_per_day": (10, 1500), "benefits_per_day": (1, 600),
                      "contract_labor_per_day": (0, 800), "net_patient_revenue_per_day": (50, 2500), "operating_margin": (-1, 0.6),
                      "occupancy": (0.05, 1.05), "medicaid_share_of_days": (0, 1)}
                m = {k: (round(v, 4) if k in ("operating_margin", "occupancy", "medicaid_share_of_days") else round(v, 2))
                     for k, v in m.items() if v is not None and ok[k][0] <= v <= ok[k][1]}
                full = 360 <= (e - b).days + 1 <= 371
                if full:
                    for scope in ("US", r.get("State Code")) if r.get("State Code") == "CT" else ("US",):
                        for k, v in m.items():
                            pools[(scope, e.year)][k].append(v)
                if r.get("State Code") == "CT":
                    ccn = (r.get("Provider CCN") or "").strip().zfill(6)
                    ct[ccn].append({"period_start": b.isoformat(), "period_end": e.isoformat(), "full_year": full,
                                    "report_id": r.get("rpt_rec_num"), "name": (r.get("Facility Name") or "").strip(),
                                    "beds": n("Number of Beds"), "total_days": days,
                                    "operating_expense": n("Less Total Operating Expense"),
                                    "total_salaries": n("Total Salaries (adjusted)"), "benefits": n("Wage-related Costs (core)"),
                                    "contract_labor": n("Contract Labor"), "net_patient_revenue": npr,
                                    "net_income": n("Net Income"), **m})
    med = {}
    for (scope, y), vals in pools.items():
        med.setdefault(str(y), {})[scope] = {"reports": len(vals.get("operating_expense_per_day", [])),
                                             # a year still being filed has far fewer reports: flagged on the page
                                             "complete": len(vals.get("operating_expense_per_day", [])) >= (10000 if scope == "US" else 120),
                                             **{k: round(statistics.median(v), 4 if k in ("operating_margin", "occupancy", "medicaid_share_of_days") else 2)
                                                for k, v in vals.items() if len(v) >= 5}}
    for lst in ct.values():
        lst.sort(key=lambda x: x["period_end"])
    return ct, dict(sorted(med.items())), manifest


def cms_match(cms_rows, start, end):
    """The Medicare report covering most of the DSS report period (at least 6 months)."""
    from datetime import date
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    best, best_days = None, 0
    for r in cms_rows:
        rs, re_ = date.fromisoformat(r["period_start"]), date.fromisoformat(r["period_end"])
        overlap = (min(e, re_) - max(s, rs)).days + 1
        if overlap > best_days:
            best, best_days = r, overlap
    if not best or best_days < 183:
        return None
    return {"report_id": best["report_id"], "period_start": best["period_start"], "period_end": best["period_end"],
            "same_period": best["period_start"] == start and best["period_end"] == end, "overlap_days": best_days}


def year_record(o, idx_row, pbj):
    f, d, c = o["fields"], o["derived"], o["checks"]
    p_start, p_end, p_read = report_period(o)
    p_days = (p_end - p_start).days + 1
    rec = {"cost_year": o["year"], "period_start": p_start.isoformat(), "period_end": p_end.isoformat(),
           "period_days": p_days, "period_read_from_report": p_read, "part_year": p_days < 360,
           "source_file": o["file"] + ".pdf",
           "read_method": {"text": "PDF text", "ocr_layout": "OCR (scanned report)", "ocr_full": "OCR (scanned report)"}.get(o["text_source"], o["text_source"]),
           "match": o.get("match"), "match_evidence": idx_row.get("evidence"),
           "name_on_report": idx_row.get("name"), "address_on_report": idx_row.get("address"),
           "medicare_number_on_report": idx_row.get("medicare"), "license_on_report": idx_row.get("licenses")}
    for group, keys in FIELDS.items():
        rec[group] = {k: f.get(k) for k in keys if f.get(k) is not None}
    dc = {k: d.get(k) for k in ("direct_salaries", "hands_on_salaries", "nursing_pool", "direct_fringe_allocated",
                                "direct_care_total", "direct_care_per_resident_day", "direct_care_share_of_expenses",
                                "expenses_per_resident_day", "nursing_hours_reported", "nursing_hours_per_resident_day",
                                "direct_care_cost_per_nursing_hour") if d.get(k) is not None}
    days = f.get("resident_days_total") or f.get("days_total_care")
    if days and f.get("rev_total"):
        dc["revenue_per_resident_day"] = round(f["rev_total"] / days, 2)
    if f.get("rev_total") and f.get("expenses_total_ccnh"):
        dc["operating_margin_nh"] = round((f["rev_total"] - f["expenses_total_ccnh"]) / f["rev_total"], 4)
    # Costs, revenue and margin outside these ranges are almost always a misread total: flag the year
    # and don't publish the derived figure.
    money_flags = []
    for key, label in (("expenses_per_resident_day", "costs per resident day"),
                       ("revenue_per_resident_day", "revenue per resident day")):
        v = dc.get(key)
        if v is not None and not (100 <= v <= 1500):
            money_flags.append(label)
            dc.pop(key)
            dc.pop("operating_margin_nh", None)
    m = dc.get("operating_margin_nh")
    if m is not None and not (-1 <= m <= 0.5):
        money_flags.append("operating margin")
        dc.pop("operating_margin_nh")
    rec["direct_care"] = dc
    rec["support_services"] = support_services(f, days)
    rec["payer_mix"] = d.get("payer_mix")
    rec["pbj_same_period"] = pbj
    if pbj and d.get("nursing_hours_per_resident_day"):
        rec["pbj_same_period"]["cost_report_minus_pbj_hprd"] = round(d["nursing_hours_per_resident_day"] - pbj["total_nurse_hprd"], 2)
    flags = plausible(f, d) + money_flags
    rec["checks"] = {"printed_totals": c, "out_of_range": flags,
                     "validated": bool(c.get("has_core")) and c.get("days_sum", True) and not flags}
    e = o.get("entities") or {}
    rec["owners_on_report"] = {
        "partnership_legal_name": e.get("partnership_legal_name") if e.get("partnership_legal_name") not in ("N/A", "NA") else None,
        "corporation_legal_name": e.get("corporation_legal_name"),
        "partners_members": [{k: x.get(k) for k in ("name", "address", "percent")} for x in e.get("partners_members", [])],
        "directors_officers": [{k: x.get(k) for k in ("name", "address", "percent")} for x in e.get("directors_officers", [])],
        "stockholders_10pct": [{k: x.get(k) for k in ("name", "address", "percent")} for x in e.get("stockholders_10pct", [])],
    }
    set_related_parties(rec, e)
    rec["management_services"] = [{k: x.get(k) for k in ("name", "cost", "description")} for x in e.get("management_services", [])]
    rec["cost_breakdown"] = None if "resident days vs beds" in flags else \
        cost_breakdown(f, d, rec["support_services"], days, rec["related_parties"])
    return rec


def match_company(name, companies):
    n = norm(name)
    if not n:
        return None
    for c in companies:
        for alias in [c["name"]] + c.get("other_names", []):
            a = norm(alias)
            core = re.sub(r"\b(INC|LLC|CORP|CORPORATION|CO|LTD|THE)\b", "", a).strip()
            if len(core) >= 6 and core in n:
                return c["id"]
    return None


def rebuild_related_parties(extract_path):
    """Rebuild only page-4 fields, using the filings already selected in the published snapshot."""
    extracted = {(o.get("ccn"), o.get("year"), o["file"] + ".pdf"): o["entities"]
                 for o in load(extract_path) if "entities" in o}
    index = load(OUT_INDEX)
    companies = load(ROOT / "data" / "ct_nursing_home_management_companies.json")["companies"]
    reports = {}
    year_count = 0
    for facility in index["facilities"]:
        if not facility["has_detail"]:
            continue
        ccn = facility["ccn"]
        path = OUT_DIR / f"{ccn}.json"
        detail = load(path)
        if set(facility["years"]) != {str(y["cost_year"]) for y in detail["cost_years"]}:
            raise ValueError(f"Cost-report index and detail disagree for {ccn}")
        for year in detail["cost_years"]:
            y = year["cost_year"]
            source = extracted[(ccn, y, year["source_file"])]
            set_related_parties(year, source, companies)
            days = year["resident_days"].get("resident_days_total") or year["resident_days"].get("days_total_care")
            cb = year["cost_breakdown"]
            apply_related_rent(cb, days, year["related_parties"])
            indexed = facility["years"][str(y)]
            indexed["related_party_total_reported"] = year["related_party_total_reported"]
            rent = ((cb or {}).get("details") or {}).get(RELATED_RENT)
            key = f"{RELATED_RENT}_per_resident_day"
            if rent:
                indexed[key] = rent["per_resident_day"]
            else:
                indexed.pop(key, None)
            year_count += 1
        reports[path] = detail
    # Validate the entire filing mapping before writing any output.
    if year_count != index["summary"]["home_years"]:
        raise ValueError("Scoped rebuild did not cover all published home-years")
    index["method"]["related_party_rent"] = RELATED_RENT_METHOD
    for path, detail in reports.items():
        path.write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n",
                        encoding="utf-8", newline="\n")
    OUT_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8", newline="\n")
    print(f"Rebuilt page-4 fields for {year_count} published home-years")


def main():
    extract = [o for o in load(PRIV / "extract_all.json") if "fields" in o and o.get("ccn") and o.get("year")]
    idx = {d["file"]: d for d in load(PRIV / "cost_report_index.json")}
    history = load(ROOT / "data" / "nursing_home_staffing_history_ct.json")
    mgmt = load(ROOT / "data" / "ct_nursing_home_management_companies.json")
    admins = load(ROOT / "data" / "ct_nursing_home_administrators.json")
    staffing = load(ROOT / "data" / "nursing_home_staffing_ct.json")
    by_name, names = provider_maps()
    owners, owner_releases = cms_owners(by_name)
    chow, chow_file = chow_events()
    cms_ct, cms_medians, cms_manifest = cms_cost_reports()
    pbj_rows = pbj_quarters(history)
    last_pbj = {}
    for r in history["facility_quarterly_staffing_history"]:
        last_pbj[r["ccn"]] = max(last_pbj.get(r["ccn"], ""), r["quarter"])
    latest_pbj = max(last_pbj.values())
    prov_src = next((x for x in staffing["sources"] if "Provider Information" in x.get("source_dataset_name", "")), {})
    m_rel = re.search(r"ProviderInfo_([A-Za-z]{3})(\d{4})", prov_src.get("source_release", ""))
    prov_release = f"{m_rel.group(1)} {m_rel.group(2)}" if m_rel else None
    mgmt_fac = {f["ccn"]: f["management"] for f in mgmt["facilities"]}
    admin_fac = {f["ccn"]: f for f in admins["facilities"] if f.get("ccn")}
    current = {f["ccn"]: f for f in staffing["facilities"]}

    # choose one report per home-year: validated first, then text over OCR, then larger file name (amended)
    by = defaultdict(list)
    for o in extract:
        if o.get("match") not in ("confirmed", "probable"):
            continue
        by[(o["ccn"], o["year"])].append(o)
    homes = defaultdict(dict)
    dup_notes = defaultdict(list)
    for (ccn, y), lst in by.items():
        # an owner change can split a year into two filings: show the longer period, note the other
        lst.sort(key=lambda o: (not o["checks"].get("has_core"), -((lambda p: (p[1] - p[0]).days)(report_period(o))),
                                o["text_source"] != "text", o["file"]))
        ps, pe, _ = report_period(lst[0])
        homes[ccn][y] = year_record(lst[0], idx.get(lst[0]["file"], {}), pbj_for_period(pbj_rows.get(ccn, []), ps, pe))
        if len(lst) > 1:
            homes[ccn][y]["other_filings_same_year"] = [x["file"] + ".pdf" for x in lst[1:]]

    # statewide medians per cost year (validated reports only)
    state = {}
    for y in sorted({y for h in homes.values() for y in h}):
        vals = defaultdict(list)
        for h in homes.values():
            r = h.get(y)
            if not r or not r["checks"]["validated"] or r["part_year"]:
                continue
            for k in ("direct_care_per_resident_day", "direct_care_share_of_expenses", "expenses_per_resident_day",
                      "nursing_hours_per_resident_day", "direct_care_cost_per_nursing_hour", "revenue_per_resident_day",
                      "operating_margin_nh"):
                if r["direct_care"].get(k) is not None:
                    vals[k].append(r["direct_care"][k])
            if r["payer_mix"]:
                vals["medicaid_share_of_days"].append(r["payer_mix"].get("medicaid_ct") or 0)
            ss = r.get("support_services") or {}
            if (ss.get("food") or {}).get("raw_food_per_resident_day") is not None:
                vals["raw_food_per_resident_day"].append(ss["food"]["raw_food_per_resident_day"])
            for dept in ("dietary", "housekeeping", "laundry"):
                if (ss.get(dept) or {}).get("per_resident_day") is not None:
                    vals[f"{dept}_per_resident_day"].append(ss[dept]["per_resident_day"])
            cb = r.get("cost_breakdown") or {}
            for k, v in (cb.get("categories") or {}).items():
                if k not in ("nursing", "dietary", "housekeeping", "laundry"):
                    vals[f"{k}_per_resident_day"].append(v["per_resident_day"])
                vals[f"{k}_share"].append(v["share"])
            for k in ("management_fees", "utilities", "rent"):
                if k in (cb.get("details") or {}):
                    vals[f"{k}_per_resident_day"].append(cb["details"][k]["per_resident_day"])
        state[y] = {"reports": len(vals["direct_care_per_resident_day"]),
                    **{k: round(statistics.median(v), 4 if "share" in k or "margin" in k else 2) for k, v in vals.items() if v}}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.json"):
        old.unlink()
    index_rows = []
    all_ccns = sorted(set(homes) | set(current))
    companies = mgmt["companies"]
    for ccn in all_ccns:
        years = homes.get(ccn, {})
        name = (current.get(ccn) or {}).get("provider_name") or sorted(names.get(ccn) or {ccn})[0]
        for y, r in years.items():
            for m in r["management_services"]:
                m["company_id"] = match_company(m.get("name"), companies)
            for p in r["related_parties"]:
                p["company_id"] = match_company(p["name_guess"], companies) if not p["row_status"] else None
            # management of record during the cost year (CMS)
            start, end = r["period_start"], r["period_end"]
            r["cms_management_during_year"] = [
                {k: m[k] for k in ("company_id", "name", "start", "end", "current")}
                for m in mgmt_fac.get(ccn, []) if m["start"] <= end and (m["end"] or "9999") >= start]
            r["administrators_during_year"] = [
                {k: a[k] for k in ("person_id", "name", "license_number", "start", "end")}
                for a in (admin_fac.get(ccn) or {}).get("administrators", [])
                if (a.get("start") or "0000") <= end and (a.get("end") or "9999") >= start]
            r["chow_during_year"] = [e for e in chow.get(ccn, []) if start <= e["effective_date"] <= end]
            r["medicare_cost_report_same_year"] = cms_match(cms_ct.get(ccn, []), start, end)
        detail = {"schema_version": SCHEMA, "ccn": ccn, "facility_name": name,
                  "cost_years": [years[y] for y in sorted(years)],
                  "cms_owners": owners.get(ccn, []),
                  "cms_owners_window": {"first_release": owner_releases[0], "latest_release": owner_releases[-1]},
                  "changes_of_ownership": chow.get(ccn, []),
                  "medicare_cost_reports": cms_ct.get(ccn, []),
                  # CMS listing status: a home missing from CMS Provider Information, or whose PBJ staffing stopped,
                  # is usually closed or decertified. Stated as what CMS lists, not as a closure.
                  "cms_status": {"in_provider_information": bool((current.get(ccn) or {}).get("provider_source_matched")),
                                 "provider_information_release": prov_release,
                                 "last_pbj_quarter": last_pbj.get(ccn), "latest_pbj_quarter": latest_pbj,
                                 "staffing_footnote": (current.get(ccn) or {}).get("cms_staffing_rating_footnote")},
                  "caveats": CAVEATS, "corrections_notice": CORRECTIONS}
        if years or owners.get(ccn) or chow.get(ccn) or cms_ct.get(ccn):
            (OUT_DIR / f"{ccn}.json").write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        index_rows.append({
            "ccn": ccn, "facility_name": name, "current": ccn in current,
            "years": {str(y): {"validated": r["checks"]["validated"], "part_year": r["part_year"],
                               "period_start": r["period_start"], "period_end": r["period_end"],
                               "direct_care_per_resident_day": r["direct_care"].get("direct_care_per_resident_day"),
                               "direct_care_share_of_expenses": r["direct_care"].get("direct_care_share_of_expenses"),
                               "nursing_hours_per_resident_day": r["direct_care"].get("nursing_hours_per_resident_day"),
                               "pbj_total_nurse_hprd": (r.get("pbj_same_period") or {}).get("total_nurse_hprd"),
                               "expenses_per_resident_day": r["direct_care"].get("expenses_per_resident_day"),
                               "operating_margin_nh": r["direct_care"].get("operating_margin_nh"),
                               "management_fee": r["expenses"].get("mgmt_fee_m12"),
                               "related_party_total_reported": r.get("related_party_total_reported"),
                               "medicaid_share_of_days": (r.get("payer_mix") or {}).get("medicaid_ct"),
                               "raw_food_per_resident_day": ((r.get("support_services") or {}).get("food") or {}).get("raw_food_per_resident_day"),
                               "food_purchasing": ((r.get("support_services") or {}).get("food") or {}).get("purchasing"),
                               "dietary_per_resident_day": ((r.get("support_services") or {}).get("dietary") or {}).get("per_resident_day"),
                               "housekeeping_per_resident_day": ((r.get("support_services") or {}).get("housekeeping") or {}).get("per_resident_day"),
                               "laundry_per_resident_day": ((r.get("support_services") or {}).get("laundry") or {}).get("per_resident_day"),
                               **{f"{k}_per_resident_day": v["per_resident_day"] for k, v in
                                  ((r.get("cost_breakdown") or {}).get("categories") or {}).items()
                                  if k not in ("nursing", "dietary", "housekeeping", "laundry")},
                               **{f"{k}_per_resident_day": v["per_resident_day"] for k, v in
                                  ((r.get("cost_breakdown") or {}).get("details") or {}).items()
                                  if k in ("management_fees", "utilities", "rent", "rent_or_lease_paid_to_related_parties")}}
                      for y, r in sorted(years.items())},
            "cms_current_owner_count": sum(1 for x in owners.get(ccn, []) if x["current"]),
            "changes_of_ownership": len(chow.get(ccn, [])),
            "has_detail": (OUT_DIR / f"{ccn}.json").exists()})

    # management fees by company (Schedule C-1 lines matched to a CMS/DPH management company)
    fees = defaultdict(lambda: defaultdict(lambda: {"total": 0, "homes": []}))
    for ccn, years in homes.items():
        for y, r in years.items():
            for m in r["management_services"]:
                if m.get("company_id") and m.get("cost"):
                    slot = fees[m["company_id"]][str(y)]
                    slot["total"] += m["cost"]
                    slot["homes"].append({"ccn": ccn, "amount": m["cost"]})
    fees_out = {cid: {y: {"total": r0(v["total"]), "homes": v["homes"]} for y, v in sorted(ys.items())}
                for cid, ys in fees.items()}

    n_reports = sum(len(h) for h in homes.values())
    out = {
        "schema_version": SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sources": [
            {"title": "Connecticut DSS Annual Report of Long-Term Care Facility (nursing facility cost reports)",
             "url": "https://portal.ct.gov/dss/health-and-home-care/medicaid-nursing-home-reimbursement/nursing-facility-cost-reports",
             "note": f"{n_reports} home-years, cost years {min(state)}-{max(state)}."},
            {"title": "CMS Skilled Nursing Facility All Owners", "as_of": owner_releases[-1],
             "url": "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-all-owners",
             "note": f"{len(owner_releases)} monthly releases, {owner_releases[0]} to {owner_releases[-1]}."},
            {"title": "CMS Skilled Nursing Facility Change of Ownership", "as_of": chow_file,
             "url": "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-change-of-ownership"},
            {"title": "CMS Payroll-Based Journal staffing (same months as each cost year)",
             "as_of": history.get("history_window", {}).get("latest_quarter")},
            {"title": "DSS Nursing Home Rate Setting Guide Book (2024), direct-care definition"},
            {"title": "CMS Skilled Nursing Facility Cost Report (Medicare cost reports, form CMS-2540-10, public use file)",
             "url": "https://data.cms.gov/provider-compliance/cost-report/skilled-nursing-facility-cost-report",
             # when CMS last re-released the series (catalog "modified"); the freshness check ages it yearly
             "as_of": (max(m[1] for m in cms_manifest) if cms_manifest else None),
             "note": f"Every US skilled nursing facility, fiscal years ending {min(cms_medians) if cms_medians else ''}-{max(cms_medians) if cms_medians else ''}; used for the national comparison and each home's Medicare cost report."},
        ],
        "method": {
            "direct_care": "Director/assistant directors of nursing + RN + LPN (direct and administrative) + nurse aide "
                           "salaries (page 10), plus nursing pool fees for RN, LPN and aides (page 13), plus fringe "
                           "benefits (page 15, lines 1a) allocated by nursing salaries' share of total salaries.",
            "nursing_hours": "Paid hours reported for the same staff on pages 10 and 13, divided by total resident days (page 8).",
            "pbj_same_period": "PBJ total nurse hours per resident day for the PBJ quarters that overlap the report period (a full cost year is Q4 through Q3), resident-day weighted.",
            "validated": "Core figures present, payer days add up to the printed total, and no figure outside a plausible range.",
            "raw_food": "Raw food cost per resident day = the Raw Food line (page 18, line 2a1, nursing home column) "
                        "divided by total resident days (page 8). Shown only when the home buys its own food: raw food "
                        "is at least $3.00 per resident day and contract dietary services (line 2b) are under half of raw "
                        "food plus contract services. When a food-service company supplies the food, its cost is inside the "
                        "contract fee and cannot be separated, so only the all-in dietary cost is shown. Raw food may "
                        "include staff or guest meals where the home reports them in the dietary total (questions G and J "
                        "on page 18).",
            "dietary": "All-in dietary cost per resident day = dietary salaries (page 10, lines 5a-5c: dietitian, food "
                       "service supervisor, dietary workers) + their share of fringe benefits (page 15, allocated by "
                       "dietary salaries' share of all salaries) + total dietary expenditures (page 18, line 2D: raw food, "
                       "non-food supplies, other, contract services), divided by total resident days. This compares homes "
                       "that run their own kitchen with homes that contract it out. Shown only when page 18's lines add "
                       "up to its printed total.",
            "housekeeping": "All-in housekeeping cost per resident day = housekeeping salaries (page 10, lines 6a-6b) + "
                            "their share of fringe benefits + total housekeeping expenditures (page 20, line 4D: supplies "
                            "and contract services), divided by total resident days.",
            "laundry": "All-in laundry cost per resident day = laundry salaries (page 10, lines 8a-8b) + their share of "
                       "fringe benefits + total laundry expenditures (page 19, line 3D: in-house costs and linen or "
                       "laundry contracts), divided by total resident days.",
            "cost_breakdown": "Costs by category split the nursing home's total costs (page 27, line 15, nursing-home "
                              "column) into twelve categories, each divided by total resident days. Fringe benefits "
                              "(page 15) are part of administrative and general on the form; here they are moved to the "
                              "staff they belong to, allocated by each group's share of all salaries. Nursing care uses "
                              "the direct-care definition above. 'All other staff' is the remaining salaries and benefits. "
                              "'Other professional fees' is page 13's total less nursing agency. Administrative and "
                              "general is page 16's total less fringe benefits; management fees (line m12) are part of it. "
                              "Plant operation is page 22 line 6g (utilities = heat, light and power, water). Building "
                              "and property is page 22 line 11: rent on leased real property (line 9), depreciation, "
                              "amortization and property taxes. Interest and insurance are page 27. Shown only when the "
                              "categories add back to the printed total within 0.2%.",
            "medicare_cost_reports": "Medicare cost reports (CMS) are filed by each home for its own fiscal year and "
                                     "cover the whole facility (all units), so they do not match the DSS nursing-home "
                                     "column exactly. Figures are per total day on the Medicare report: operating "
                                     "expense, salaries, wage-related costs (benefits), contract labor and net patient "
                                     "revenue. Operating margin = (net patient revenue - operating expense) / net patient "
                                     "revenue. National and Connecticut medians use full-year reports only (360-371 days), "
                                     "grouped by the year the fiscal year ends, and leave out implausible values.",
            "related_party_rent": RELATED_RENT_METHOD,
            "support_costs_exclude": "None of the support figures include management-company charges reported on page 16, "
                                     "kitchen or laundry equipment depreciation and building costs (property), or "
                                     "utilities; a contractor's fee includes its own overhead and profit.",
            "part_year": "The report covers fewer than 360 days (the home opened, closed or changed owner). Dates come from the report's certification page. Part-year filings are left out of the statewide medians.",
        },
        "caveats": CAVEATS, "corrections_notice": CORRECTIONS,
        "summary": {"homes_with_reports": len(homes), "home_years": n_reports,
                    "validated_home_years": sum(1 for h in homes.values() for r in h.values() if r["checks"]["validated"]),
                    "homes_with_cms_owners": len(owners), "chow_events": sum(len(v) for v in chow.values())},
        "statewide_medians": {str(y): v for y, v in state.items()},
        "cost_categories": COST_CATEGORIES,
        "medicare_cost_report_medians": cms_medians,
        "facilities": index_rows,
        "management_fees_by_company": fees_out,
    }
    OUT_INDEX.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = out["summary"]
    print(f"Wrote {OUT_INDEX.relative_to(ROOT)} and {sum(1 for _ in OUT_DIR.glob('*.json'))} detail files: "
          f"{s['homes_with_reports']} homes, {s['home_years']} home-years ({s['validated_home_years']} validated), "
          f"{s['homes_with_cms_owners']} homes with CMS owners, {s['chow_events']} CHOW events")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--related-parties-only", type=Path, metavar="EXTRACT",
                        help="Rebuild only page-4 fields from run_all.py --related-parties-only.")
    args = parser.parse_args()
    if args.related_parties_only:
        rebuild_related_parties(args.related_parties_only)
    else:
        main()
