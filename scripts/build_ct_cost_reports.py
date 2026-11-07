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
    rec["related_parties"] = [{k: x.get(k) for k in ("name_guess", "text", "category", "where", "cost_reported",
                                                       "actual_cost_to_related_party", "pct_revenue_from_non_related")}
                              for x in e.get("related_parties", [])]
    rec["management_services"] = [{k: x.get(k) for k in ("name", "cost", "description")} for x in e.get("management_services", [])]
    rec["related_party_total_reported"] = r0(sum(x["cost_reported"] or 0 for x in rec["related_parties"]
                                                 if (x.get("category") or "") not in ("loans / interest / receivables",)
                                                 and not re.match(r"^(See attached|Various)", x.get("name_guess") or "", re.I)))
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
                p["company_id"] = match_company(p.get("text"), companies)
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
        detail = {"schema_version": SCHEMA, "ccn": ccn, "facility_name": name,
                  "cost_years": [years[y] for y in sorted(years)],
                  "cms_owners": owners.get(ccn, []),
                  "cms_owners_window": {"first_release": owner_releases[0], "latest_release": owner_releases[-1]},
                  "changes_of_ownership": chow.get(ccn, []),
                  # CMS listing status: a home missing from CMS Provider Information, or whose PBJ staffing stopped,
                  # is usually closed or decertified. Stated as what CMS lists, not as a closure.
                  "cms_status": {"in_provider_information": bool((current.get(ccn) or {}).get("provider_source_matched")),
                                 "provider_information_release": prov_release,
                                 "last_pbj_quarter": last_pbj.get(ccn), "latest_pbj_quarter": latest_pbj,
                                 "staffing_footnote": (current.get(ccn) or {}).get("cms_staffing_rating_footnote")},
                  "caveats": CAVEATS, "corrections_notice": CORRECTIONS}
        if years or owners.get(ccn) or chow.get(ccn):
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
                               "medicaid_share_of_days": (r.get("payer_mix") or {}).get("medicaid_ct")}
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
        ],
        "method": {
            "direct_care": "Director/assistant directors of nursing + RN + LPN (direct and administrative) + nurse aide "
                           "salaries (page 10), plus nursing pool fees for RN, LPN and aides (page 13), plus fringe "
                           "benefits (page 15, lines 1a) allocated by nursing salaries' share of total salaries.",
            "nursing_hours": "Paid hours reported for the same staff on pages 10 and 13, divided by total resident days (page 8).",
            "pbj_same_period": "PBJ total nurse hours per resident day for the PBJ quarters that overlap the report period (a full cost year is Q4 through Q3), resident-day weighted.",
            "validated": "Core figures present, payer days add up to the printed total, and no figure outside a plausible range.",
            "part_year": "The report covers fewer than 360 days (the home opened, closed or changed owner). Dates come from the report's certification page. Part-year filings are left out of the statewide medians.",
        },
        "caveats": CAVEATS, "corrections_notice": CORRECTIONS,
        "summary": {"homes_with_reports": len(homes), "home_years": n_reports,
                    "validated_home_years": sum(1 for h in homes.values() for r in h.values() if r["checks"]["validated"]),
                    "homes_with_cms_owners": len(owners), "chow_events": sum(len(v) for v in chow.values())},
        "statewide_medians": {str(y): v for y, v in state.items()},
        "facilities": index_rows,
        "management_fees_by_company": fees_out,
    }
    OUT_INDEX.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = out["summary"]
    print(f"Wrote {OUT_INDEX.relative_to(ROOT)} and {sum(1 for _ in OUT_DIR.glob('*.json'))} detail files: "
          f"{s['homes_with_reports']} homes, {s['home_years']} home-years ({s['validated_home_years']} validated), "
          f"{s['homes_with_cms_owners']} homes with CMS owners, {s['chow_events']} CHOW events")


if __name__ == "__main__":
    main()
