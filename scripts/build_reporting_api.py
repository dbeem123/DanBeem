#!/usr/bin/env python3
"""Build the static, read-only CT nursing home reporting API under /api.

Inputs: the committed site datasets in /data (no new sources, no network).
Output: /api/v1/**.json plus /api/v1/schema/report.schema.json. OpenAPI, docs
and llms.txt are hand-maintained files next to the output.

The host (GitHub Pages) is static, so every "endpoint" is a precomputed JSON
file. Parameters live in the path and every URL ends in .json.

Determinism: generated_at is the newest source build date, never the wall
clock, so an unchanged /data produces byte-identical output.

Evidence rules (see docs/reporting_api_plan.md):
  kind = confirmed_fact | calculated | possible_association | investigative_question
  Missing data is null plus a missing_data entry, never a guessed value.
  Shared people/organizations are possible associations, never conflicts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = "https://danbeem.xyz"
API_VERSION = "v1"
SCHEMA_VERSION = "reporting-api-1.0"

REPORT_TYPES = [
    "facility-comprehensive",
    "ownership-network",
    "staffing-analysis",
    "financial-transparency",
    "regulatory-history",
    "related-party-screening",
]
COMPANY_REPORT_TYPES = ["management-company-portfolio"]


# --------------------------------------------------------------------------- io

def load(name: str):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


def dump(path: Path, obj) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    path.write_text(text + "\n", encoding="utf-8")
    return len(text)


def norm_name(s: str | None) -> str:
    s = (s or "").upper()
    s = re.sub(r"[.,'’`\"()]", " ", s)
    s = re.sub(r"\b(INC|LLC|LLP|LP|L L C|CORP|CORPORATION|CO|COMPANY|LTD|D/B/A|DBA|THE)\b", " ", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def r2(x, n=2):
    return None if x is None else round(float(x), n)


def median(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return round(statistics.median(vals), 3) if vals else None


# ------------------------------------------------------------------- sources

def build_source_registry(d) -> dict:
    """One entry per public source. Evidence items point at these keys."""
    hd = d["health"]["metadata"]
    fs = d["fire"]["metadata"]
    pen = d["penalties"]["metadata"]
    cr_src = {s["title"]: s for s in d["cost_index"]["sources"]}
    owners = next((s for t, s in cr_src.items() if "All Owners" in t), {})
    chow = next((s for t, s in cr_src.items() if "Change of Ownership" in t), {})
    dss = next((s for t, s in cr_src.items() if "DSS" in t), {})
    stf = d["staffing"]
    pi_date = next((f.get("provider_info_processing_date") for f in stf["facilities"] if f.get("provider_info_processing_date")), None)
    return {
        "cms_pbj": {
            "agency": "Centers for Medicare & Medicaid Services (CMS)",
            "dataset": "Payroll-Based Journal Daily Nurse Staffing",
            "url": "https://data.cms.gov/quality-of-care/payroll-based-journal-daily-nurse-staffing",
            "as_of": d["history"]["history_window"]["latest_quarter"],
            "site_file": "/data/nursing_home_staffing_history_ct.json",
        },
        "cms_provider_info": {
            "agency": "CMS",
            "dataset": "Nursing Home Provider Information (Care Compare)",
            "url": "https://data.cms.gov/provider-data/dataset/4pq5-n9py",
            "as_of": pi_date,
            "site_file": "/data/nursing_home_staffing_ct.json",
        },
        "cms_enrollment": {
            "agency": "CMS",
            "dataset": "Skilled Nursing Facility Enrollments",
            "url": "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-enrollments",
            "as_of": pi_date,
            "site_file": "/data/nursing_home_staffing_ct.json",
        },
        "cms_all_owners": {
            "agency": "CMS",
            "dataset": "Skilled Nursing Facility All Owners (monthly releases)",
            "url": owners.get("url"),
            "as_of": owners.get("as_of"),
            "site_file": "/data/cost_reports/{ccn}.json",
        },
        "cms_chow": {
            "agency": "CMS",
            "dataset": "Skilled Nursing Facility Change of Ownership",
            "url": chow.get("url"),
            "as_of": chow.get("as_of"),
            "site_file": "/data/cost_reports/{ccn}.json",
        },
        "cms_health_citations": {
            "agency": "CMS",
            "dataset": "Health Deficiencies (" + hd.get("source_file", "") + ")",
            "url": "https://data.cms.gov/provider-data/dataset/" + hd.get("cms_dataset_id", "r5ix-sfxw"),
            "as_of": hd.get("acquired_date"),
            "site_file": "/data/nursing_home_health_deficiencies_ct.json",
        },
        "cms_fire_safety": {
            "agency": "CMS",
            "dataset": "Fire Safety Deficiencies (" + fs.get("source_file", "") + ")",
            "url": "https://data.cms.gov/provider-data/dataset/" + fs.get("cms_dataset_id", "ifjz-ge4w"),
            "as_of": fs.get("acquired_date"),
            "site_file": "/data/nursing_home_fire_safety_deficiencies_ct.json",
        },
        "cms_penalties": {
            "agency": "CMS",
            "dataset": "Penalties (" + pen.get("source_file", "") + ")",
            "url": "https://data.cms.gov/provider-data/dataset/" + pen.get("cms_dataset_id", "g6vv-u9sr"),
            "as_of": pen.get("acquired_date"),
            "site_file": "/data/nursing_home_penalties_ct.json",
        },
        "dss_cost_reports": {
            "agency": "Connecticut Department of Social Services (DSS)",
            "dataset": "Annual Report of Long-Term Care Facility (nursing facility cost reports)",
            "url": dss.get("url"),
            "as_of": d["cost_index"].get("generated_at", "")[:10] or None,
            "site_file": "/data/cost_reports/{ccn}.json",
        },
        "dss_review": {
            "agency": "Connecticut Department of Social Services (DSS)",
            "dataset": "Nursing facility cost report data with DSS review adjustments (quarterly data pulls)",
            "url": (d.get("dss_review") or {}).get("source_page"),
            "as_of": (d.get("dss_review") or {}).get("generated_at"),
            "site_file": "/data/ct_dss_review.json",
        },
        "dss_rates": {
            "agency": "Connecticut Department of Social Services (DSS)",
            "dataset": "Nursing facility Medicaid rate letters (per diem by state fiscal year)",
            "url": (d.get("dss_review") or {}).get("source_page"),
            "as_of": (d.get("dss_review") or {}).get("generated_at"),
            "site_file": "/data/ct_dss_review.json",
        },
        "dph_administrators": {
            "agency": "Connecticut Department of Public Health (DPH)",
            "dataset": "Nursing home administrator of record history (eLicense roster export)",
            "url": "https://data.ct.gov/Business/State-Licenses-and-Credentials/ngch-56tr",
            "as_of": d["admins"].get("source_as_of"),
            "site_file": "/data/ct_nursing_home_administrators.json",
        },
        "management_companies": {
            "agency": "CMS (ownership archives) and Connecticut DPH (management company roster)",
            "dataset": "Management company relationships compiled by danbeem.xyz",
            "url": "https://data.cms.gov/provider-data/topics/nursing-homes",
            "as_of": d["mgmt"].get("source_as_of"),
            "site_file": "/data/ct_nursing_home_management_companies.json",
        },
        "site_roster": {
            "agency": "danbeem.xyz (compiled from CMS and DSS)",
            "dataset": "Connecticut nursing home facility roster",
            "url": SITE + "/data/nursing_home_facility_roster_ct.json",
            "as_of": d["roster"]["metadata"].get("build_date"),
            "site_file": "/data/nursing_home_facility_roster_ct.json",
        },
    }


class Ev:
    """Evidence builder bound to the source registry."""

    def __init__(self, registry):
        self.reg = registry

    def __call__(self, key, *, period=None, record=None, verification="source_record", ccn=None, note=None):
        s = self.reg[key]
        out = {
            "source_key": key,
            "agency": s["agency"],
            "dataset": s["dataset"],
            "url": s["url"],
            "site_file": (s["site_file"] or "").replace("{ccn}", ccn or "{ccn}"),
            "reporting_period": period,
            "as_of": s["as_of"],
            "record_id": record,
            "verification": verification,
        }
        if note:
            out["note"] = note
        return out


def finding(fid, kind, statement, evidence, *, value=None, formula=None, severity="info"):
    assert kind in ("confirmed_fact", "calculated", "possible_association", "investigative_question"), kind
    f = {"id": fid, "kind": kind, "severity": severity, "statement": statement, "evidence": evidence}
    if value is not None:
        f["value"] = value
    if formula:
        f["formula"] = formula
    return f


def chart(cid, title, ctype, unit, x, series, *, source_key, note=None):
    """Ready-to-plot chart data. Values are the report's own numbers; null means not in the data (draw a gap)."""
    assert ctype in ("line", "bar")
    c = {"id": cid, "title": title, "type": ctype, "unit": unit, "x": [str(v) for v in x],
         "series": [{"name": n, "role": r, "values": v} for n, r, v in series], "source_key": source_key}
    if note:
        c["note"] = note
    return c


# --------------------------------------------------------------- CMS roles

def relationship_type(role: str) -> str:
    r = (role or "").lower()
    if "security interest" in r or "mortgage interest" in r:
        return "lender_or_security_interest"
    if "ownership interest" in r or "partnership interest" in r:
        return "ownership_interest"
    if "operational/managerial control" in r or "managing control" in r or "contracted managing employee" in r:
        return "operational_or_managerial_control"
    if "director" in r or "officer" in r or "trustee" in r:
        return "officer_director_trustee"
    if "managing employee" in r:
        return "managing_employee"
    return "other_cms_role"


REL_LABEL = {
    "ownership_interest": "Ownership interest reported to CMS",
    "lender_or_security_interest": "Security or mortgage interest reported to CMS (lender, not owner)",
    "operational_or_managerial_control": "Operational or managerial control reported to CMS",
    "officer_director_trustee": "Officer, director or trustee reported to CMS",
    "managing_employee": "Managing employee reported to CMS",
    "other_cms_role": "Other role reported to CMS (role text kept verbatim)",
}


# ------------------------------------------------------------- data quality

# Per-resident-day ranges for figures the cost-report build does not range-check itself.
# Outside these the figure is almost always a misread total (e.g. revenue read as $8,847).
FIN_PRD_RANGE = {"revenue_total": (100, 1500), "expenses_total": (100, 1500), "direct_care": (40, 700)}
SUPPORT_DEPTS = ("dietary", "housekeeping", "laundry")
DEPT_LABEL = {"dietary": "Dietary", "housekeeping": "Housekeeping", "laundry": "Laundry"}


def year_quality(y: dict, raw_checks: dict | None, support_flags: list | None) -> dict:
    """Grade one cost-report year and list fields that must not be used.

    status: validated (core figures present, payer days add up, nothing out of range),
    unvalidated (read, but printed totals did not fully reconcile), or check_failed
    (core figures missing or out of a plausible range). Figures stay in financials.json
    as read; reports leave out unusable fields and check_failed years.
    """
    ch = raw_checks or {}
    pt = ch.get("printed_totals") or {}
    out_of_range = list(ch.get("out_of_range") or [])
    if ch.get("validated"):
        status = "validated"
    elif out_of_range or not pt.get("has_core"):
        status = "check_failed"
    else:
        status = "unvalidated"
    issues = [f"{x} outside the plausible range" for x in out_of_range]
    if not pt.get("has_core"):
        issues.append("core figures (days, revenue or expenses) could not be read")
    for k, label in (("days_sum", "payer days do not add up to the printed total"),
                     ("revenue_sum", "revenue lines do not add up to the printed total"),
                     ("liabilities_sum", "balance sheet does not add up")):
        if pt.get(k) is False:
            issues.append(label)
    unusable = {}
    rd = y.get("resident_days")
    if not rd or rd <= 0:
        unusable["resident_days"] = "resident days missing"
    for f in ("revenue_total", "expenses_total"):
        v = y.get(f)
        lo, hi = FIN_PRD_RANGE[f]
        if v is None or not rd or not (lo <= v / rd <= hi):
            unusable[f] = "missing" if v is None else "outside the plausible per-resident-day range (likely a misread total)"
    sane = [y[f] for f in ("revenue_total", "expenses_total") if f not in unusable]
    n = y.get("net_income")
    if n is None:
        unusable["net_income"] = "missing"
    elif not sane or abs(n) > 0.6 * max(sane):
        unusable["net_income"] = "not checkable against revenue or expenses" if not sane else "implausibly large next to revenue and expenses"
    dc = y.get("direct_care") or {}
    lo, hi = FIN_PRD_RANGE["direct_care"]
    if not dc.get("total") or dc.get("per_resident_day") is None or not (lo <= dc["per_resident_day"] <= hi):
        unusable["direct_care"] = "missing, zero or outside the plausible range"
    for d in SUPPORT_DEPTS:
        dep = y.get(d) or {}
        if dep.get("per_resident_day") is None:
            unusable[d] = ("outside the plausible range" if f"{d} per resident day" in (support_flags or [])
                           else "dietary lines do not add up to the printed total" if d == "dietary" and "dietary lines do not add up" in (support_flags or [])
                           else "missing")
    if y.get("raw_food_per_resident_day") is None:
        unusable["raw_food"] = "not comparable (food bought by a contractor, lines do not add up, or missing)"
    if status == "check_failed" or "resident_days" in unusable:
        use = False
    else:
        use = True
    return {"status": status, "use_in_reports": use, "issues": issues, "unusable_fields": unusable}


# ------------------------------------------------------------------ builder

class Builder:
    def __init__(self, out_dir: Path):
        self.out = out_dir
        self.d = {
            "roster": load("nursing_home_facility_roster_ct.json"),
            "staffing": load("nursing_home_staffing_ct.json"),
            "history": load("nursing_home_staffing_history_ct.json"),
            "health": load("nursing_home_health_deficiencies_ct.json"),
            "fire": load("nursing_home_fire_safety_deficiencies_ct.json"),
            "penalties": load("nursing_home_penalties_ct.json"),
            "survey": load("nursing_home_survey_enforcement_summary_ct.json"),
            "cost_index": load("ct_nursing_home_cost_reports.json"),
            "mgmt": load("ct_nursing_home_management_companies.json"),
            "aliases": load("ct_management_company_aliases.json"),
            "admins": load("ct_nursing_home_administrators.json"),
            "dss_review": load("ct_dss_review.json") if (DATA / "ct_dss_review.json").exists() else {"facilities": {}, "unmatched": {}},
        }
        self.reg = build_source_registry(self.d)
        self.ev = Ev(self.reg)
        d = self.d
        self.roster = {r["ccn"]: r for r in d["roster"]["records"]}
        self.fac_meta = {f["ccn"]: f for f in d["staffing"]["facilities"]}
        self.hist = defaultdict(list)
        for r in d["history"]["facility_quarterly_staffing_history"]:
            self.hist[r["ccn"]].append(r)
        for v in self.hist.values():
            v.sort(key=lambda r: r["quarter"])
        self.recent = defaultdict(list)
        for r in d["staffing"]["facility_quarterly_staffing"]:
            self.recent[r["ccn"]].append(r)
        self.health = defaultdict(list)
        for r in d["health"]["deficiencies"]:
            self.health[r["ccn"]].append(r)
        self.fire = defaultdict(list)
        for r in d["fire"]["deficiencies"]:
            self.fire[r["ccn"]].append(r)
        self.pen = defaultdict(list)
        for r in d["penalties"]["penalties"]:
            self.pen[r["ccn"]].append(r)
        self.survey = {r["ccn"]: r for r in d["survey"]["facilities"]}
        self.cost = {}
        for p in sorted((DATA / "cost_reports").glob("*.json")):
            c = json.loads(p.read_text(encoding="utf-8"))
            self.cost[c["ccn"]] = c
        self.mgmt_by_ccn = {f["ccn"]: f["management"] for f in d["mgmt"]["facilities"]}
        companies = d["mgmt"]["companies"]
        self.companies = {c["id"]: c for c in (companies if isinstance(companies, list) else companies.values())}
        afac = d["admins"]["facilities"]
        self.admins_by_ccn = defaultdict(list)
        for f in afac if isinstance(afac, list) else afac.values():
            if f.get("ccn"):
                self.admins_by_ccn[f["ccn"]].extend(f.get("administrators") or [])
        self.statewide_cost_medians = d["cost_index"].get("statewide_medians", {})
        self.ccns = sorted(set(self.roster) | set(self.fac_meta) | set(self.cost))
        # CMS associate id -> homes (for shared-principal screening)
        self.assoc_homes = defaultdict(set)
        self.assoc_names = defaultdict(set)
        self.assoc_type = {}
        for ccn, c in self.cost.items():
            for o in c.get("cms_owners") or []:
                self.assoc_homes[o["associate_id"]].add(ccn)
                self.assoc_names[o["associate_id"]].add(o["name"])
                self.assoc_type[o["associate_id"]] = o["type"]
        self.statewide_q = self._statewide_quarter_medians()
        dates = [
            d["staffing"].get("generated_at", "")[:10],
            d["history"].get("generated_at", "")[:10],
            d["cost_index"].get("generated_at", "")[:10],
            d["mgmt"].get("generated_at", "")[:10],
            d["admins"].get("generated_at", "")[:10],
            d["roster"]["metadata"].get("build_date", ""),
            d["health"]["metadata"].get("build_date", ""),
        ]
        self.generated_at = max(x for x in dates if x) + "T00:00:00Z"
        self.data_as_of = {k: v["as_of"] for k, v in self.reg.items()}
        self.bytes = 0
        self.files = 0

    # ---------------------------------------------------------------- utils
    def write(self, rel: str, obj):
        self.bytes += dump(self.out / rel, obj)
        self.files += 1

    def name(self, ccn):
        m = self.fac_meta.get(ccn) or {}
        r = self.roster.get(ccn) or {}
        c = self.cost.get(ccn) or {}
        return m.get("provider_name") or r.get("name") or c.get("facility_name")

    def links(self, ccn):
        return {
            "profile": f"{SITE}/api/v1/facilities/{ccn}/profile.json",
            "ownership": f"{SITE}/api/v1/facilities/{ccn}/ownership.json",
            "staffing": f"{SITE}/api/v1/facilities/{ccn}/staffing.json",
            "financials": f"{SITE}/api/v1/facilities/{ccn}/financials.json",
            "inspections": f"{SITE}/api/v1/facilities/{ccn}/inspections.json",
            "reports": {t: f"{SITE}/api/v1/reports/{t}/{ccn}.json" for t in REPORT_TYPES},
            "site_pages": {
                "staffing_explorer": f"{SITE}/staffing/tools/nursing-home-staffing-explorer.html?ccn={ccn}",
                "daily_minimums": f"{SITE}/staffing/tools/nursing-home-daily-minimums.html?ccn={ccn}",
                "inspections": f"{SITE}/staffing/tools/nursing-home-inspections.html?ccn={ccn}",
                "cost_reports": f"{SITE}/staffing/tools/nursing-home-cost-reports.html?ccn={ccn}",
                "report_builder": f"{SITE}/staffing/reports/?ccn={ccn}",
            },
        }

    def _statewide_quarter_medians(self):
        by_q = defaultdict(lambda: defaultdict(list))
        for rows in self.hist.values():
            for r in rows:
                m = r.get("metrics") or {}
                for k in ("total_nurse_hprd", "rn_hprd", "lpn_lvn_hprd", "nurse_aide_hprd", "contract_staff_pct", "ct_direct_care_total_hprd_estimate"):
                    if m.get(k) is not None:
                        by_q[r["quarter"]][k].append(m[k])
        return {q: {k: median(v) for k, v in ks.items()} | {"homes": len(ks.get("total_nurse_hprd", []))} for q, ks in by_q.items()}

    # ------------------------------------------------------------- sections
    def identity(self, ccn):
        m = self.fac_meta.get(ccn) or {}
        r = self.roster.get(ccn) or {}
        c = self.cost.get(ccn) or {}
        last = (c.get("cost_years") or [{}])[-1] if c.get("cost_years") else {}
        missing = []
        out = {
            "ccn": ccn,
            "facility_name": self.name(ccn),
            "address": m.get("address"),
            "city": m.get("city") or r.get("city"),
            "state": "CT",
            "zip_code": m.get("zip_code"),
            "phone_number": m.get("phone_number"),
            "certified_beds_cms": m.get("certified_beds"),
            "certified_beds_cost_report": (last.get("capacity") or {}).get("beds_certified"),
            "ownership_type_cms": m.get("ownership_type"),
            "legal_entity_cms_enrollment": m.get("enrollment_organization_name") or None,
            "doing_business_as_cms_enrollment": m.get("enrollment_doing_business_as_name") or None,
            "npi": m.get("enrollment_npi") or None,
            "cms_affiliated_entity": m.get("affiliation_entity_name") or None,
            "operating_status": r.get("official_status") or ("in_current_cms_provider_info" if r.get("in_provider_info") else None),
            "operating_status_date": r.get("official_status_date"),
            "roster_notes": r.get("notes") or [],
            "cms_ratings": {
                "overall": m.get("cms_overall_rating"),
                "health_inspection": m.get("cms_health_inspection_rating"),
                "staffing": m.get("cms_staffing_rating"),
                "quality_measures": m.get("cms_qm_rating"),
                "as_of": self.reg["cms_provider_info"]["as_of"],
                "note": "CMS Care Compare star ratings, imported as published. Not calculated by danbeem.xyz.",
            } if m else None,
        }
        if not m:
            missing.append({"field": "cms_provider_info", "reason": "CCN not in the current CMS Provider Information release (closed, merged or not yet listed)."})
        if not c:
            missing.append({"field": "dss_cost_reports", "reason": "No DSS cost report matched to this CCN."})
        return out, missing

    def ownership(self, ccn):
        c = self.cost.get(ccn) or {}
        rels = []
        for o in c.get("cms_owners") or []:
            rt = relationship_type(o["role"])
            others = sorted(self.assoc_homes[o["associate_id"]] - {ccn})
            rels.append({
                "entity_name": o["name"],
                "entity_type": o["type"].lower(),
                "cms_associate_id": o["associate_id"],
                "relationship_type": rt,
                "relationship_label": REL_LABEL[rt],
                "cms_role_verbatim": o["role"],
                "title": o.get("title"),
                "percent": o.get("percent"),
                "association_date": o.get("association_date"),
                "first_seen_release": o.get("first_release"),
                "last_seen_release": o.get("last_release"),
                "current": bool(o.get("current")),
                "also_listed_at_ccns": others,
                "verification": "source_record",
                "source_key": "cms_all_owners",
            })
        mgmt = []
        for m in self.mgmt_by_ccn.get(ccn) or []:
            mgmt.append({
                "company_id": m.get("company_id"),
                "company_name": m.get("name"),
                "relationship_type": "management_company",
                "start": m.get("start"),
                "start_basis": m.get("start_basis"),
                "end": m.get("end"),
                "ended_before": m.get("ended_before"),
                "current": m.get("current"),
                "company_url": f"{SITE}/api/v1/management-companies/{m.get('company_id')}.json" if m.get("company_id") else None,
                "verification": "source_record",
                "source_key": "management_companies",
            })
        admins = []
        for a in self.admins_by_ccn.get(ccn) or []:
            admins.append({
                "person_id": a.get("person_id"),
                "name": a.get("name"),
                "license_number": a.get("license_number"),
                "relationship_type": "administrator_of_record",
                "start": a.get("start"),
                "end": a.get("end"),
                "current": a.get("open"),
                "verification": "source_record",
                "source_key": "dph_administrators",
            })
        admins.sort(key=lambda a: a.get("start") or "", reverse=True)
        on_reports = []
        for y in c.get("cost_years") or []:
            o = y.get("owners_on_report") or {}
            if any(o.values()):
                on_reports.append({"cost_year": y["cost_year"], **o, "source_key": "dss_cost_reports",
                                   "record_id": f"DSS cost report {y['cost_year']} ({y.get('source_file')})"})
        chow = [{**x, "source_key": "cms_chow"} for x in (c.get("changes_of_ownership") or [])]
        return {
            "cms_owners_window": c.get("cms_owners_window"),
            "cms_ownership_and_control": rels,
            "management_companies": mgmt,
            "administrators_of_record": admins,
            "owners_named_on_dss_cost_reports": on_reports,
            "changes_of_ownership": chow,
        }

    def staffing(self, ccn):
        rows = self.hist.get(ccn) or []
        q = []
        for r in rows:
            m = r.get("metrics") or {}
            sw = self.statewide_q.get(r["quarter"], {})
            q.append({
                "quarter": r["quarter"],
                "average_resident_census": r.get("average_resident_census"),
                "total_nurse_hprd": m.get("total_nurse_hprd"),
                "rn_hprd": m.get("rn_hprd"),
                "lpn_hprd": m.get("lpn_lvn_hprd"),
                "aide_hprd": m.get("nurse_aide_hprd"),
                "contract_staff_pct": m.get("contract_staff_pct"),
                "ct_direct_care_hprd_estimate": m.get("ct_direct_care_total_hprd_estimate"),
                "ct_licensed_direct_care_hprd_estimate": m.get("ct_direct_care_licensed_nurse_hprd_estimate"),
                "ct_minimum_total_hprd": m.get("ct_total_direct_care_minimum_hprd"),
                "ct_minimum_licensed_hprd": m.get("ct_licensed_direct_care_minimum_hprd"),
                "ct_below_total_minimum_estimate": m.get("ct_total_direct_care_below_minimum_estimate"),
                "ct_comparison_status": r.get("ct_comparison_period_status"),
                "statewide_median_total_nurse_hprd": sw.get("total_nurse_hprd"),
                "statewide_median_contract_staff_pct": sw.get("contract_staff_pct"),
            })
        meta = self.fac_meta.get(ccn) or {}
        return {
            "period_definition": "Calendar quarters. Hours per resident day (HPRD) = PBJ paid nursing hours / resident days. Zero-census days excluded as in the site's PBJ build.",
            "coverage": {"first_quarter": q[0]["quarter"] if q else None, "last_quarter": q[-1]["quarter"] if q else None, "quarters": len(q)},
            "case_mix_expected_hprd_cms": meta.get("case_mix_benchmarks"),
            "benchmark_note": "Statewide medians are calculated by this API across all CT homes reporting PBJ in the same quarter. CMS case-mix values are CMS's own expected staffing, current release only.",
            "ct_minimum_note": "CT comparison points are screening estimates from PBJ, which does not show shifts or day/night split. A quarter below a point is a reason to ask questions, not a finding of a violation.",
            "quarters": q,
        }

    def financials(self, ccn):
        c = self.cost.get(ccn) or {}
        years = []
        for y in c.get("cost_years") or []:
            rev = y.get("revenue") or {}
            exp = y.get("expenses") or {}
            dc = y.get("direct_care") or {}
            ss = y.get("support_services") or {}
            pool = y.get("nursing_pool") or {}
            bal = y.get("balance_sheet") or {}
            med = self.statewide_cost_medians.get(str(y["cost_year"])) or {}

            def sup(k):
                s = ss.get(k) or {}
                return {"wages_reported": s.get("salaries"), "fringe_allocated": s.get("fringe_allocated"),
                        "non_salary": s.get("non_salary"), "total_department_cost": s.get("total"),
                        "per_resident_day": s.get("per_resident_day")}
            years.append({
                "cost_year": y["cost_year"],
                "period_start": y.get("period_start"),
                "period_end": y.get("period_end"),
                "part_year": y.get("part_year"),
                "validated_against_printed_totals": (y.get("checks") or {}).get("validated"),
                "match_to_ccn": y.get("match"),
                "source_file": y.get("source_file"),
                "name_on_report": y.get("name_on_report"),
                "resident_days": (y.get("resident_days") or {}).get("resident_days_total"),
                "payer_mix": y.get("payer_mix"),
                "revenue_total": rev.get("rev_total_all"),
                "expenses_total": exp.get("expenses_total_all"),
                "net_income": bal.get("net_income_p36"),
                "operating_margin_nursing_home": dc.get("operating_margin_nh"),
                "expenses_per_resident_day": dc.get("expenses_per_resident_day"),
                "management_fee_reported": exp.get("mgmt_fee_m12"),
                "related_party_total_reported": y.get("related_party_total_reported"),
                "direct_care": {
                    "salaries": dc.get("direct_salaries"),
                    "nursing_pool_agency": dc.get("nursing_pool"),
                    "fringe_allocated": dc.get("direct_fringe_allocated"),
                    "total": dc.get("direct_care_total"),
                    "per_resident_day": dc.get("direct_care_per_resident_day"),
                    "share_of_expenses": dc.get("direct_care_share_of_expenses"),
                },
                "nursing_pool_agency_cost": pool.get("prof_fees_total"),
                "dietary": sup("dietary"),
                "housekeeping": sup("housekeeping"),
                "laundry": sup("laundry"),
                "raw_food_per_resident_day": ((ss.get("food") or {}).get("raw_food_per_resident_day")),
                "food": {k: (ss.get("food") or {}).get(k) for k in
                         ("raw_food", "nonfood_supplies", "contract_services", "purchasing", "contract_share", "lines_add_up")},
                "dietary_staff_on_payroll": ss.get("dietary_staff_on_payroll"),
                "pbj_same_period": y.get("pbj_same_period"),
                "statewide_median_same_year": {
                    "direct_care_per_resident_day": med.get("direct_care_per_resident_day"),
                    "expenses_per_resident_day": med.get("expenses_per_resident_day"),
                    "operating_margin_nh": med.get("operating_margin_nh"),
                    "dietary_per_resident_day": med.get("dietary_per_resident_day"),
                    "housekeeping_per_resident_day": med.get("housekeeping_per_resident_day"),
                    "laundry_per_resident_day": med.get("laundry_per_resident_day"),
                    "raw_food_per_resident_day": med.get("raw_food_per_resident_day"),
                    "management_fees_per_resident_day": med.get("management_fees_per_resident_day"),
                    "reports": med.get("reports"),
                } if med else None,
                "related_parties": [
                    {"name_as_printed": r.get("name_guess"), "description": r.get("description"), "category": r.get("category"),
                     "cost_reported": r.get("cost_reported"), "actual_cost_to_related_party": r.get("actual_cost_to_related_party"),
                     "where_on_report": r.get("where"), "site_company_id": r.get("company_id")}
                    for r in (y.get("related_parties") or [])
                ],
                "management_services": y.get("management_services") or [],
                "management_company_on_file_during_year": y.get("cms_management_during_year") or [],
            })
            years[-1]["data_quality"] = year_quality(years[-1], y.get("checks"), ss.get("flags"))
        return {
            "definitions": {
                "wages_reported": "Salaries and wages printed on the cost report for that department. Not total department spending.",
                "total_department_cost": "Wages + allocated fringe + non-salary costs for the department, as computed by the site's cost-report build.",
                "direct_care": "DSS rate-setting definition: nursing and aide salaries, related fringe (allocated), and nursing pool (agency) cost.",
                "figures": "As filed by the home before DSS audit. Not Medicaid-allowable costs.",
                "data_quality": "Per year: status validated (core figures present, payer days add up, nothing out of range), unvalidated (read, but printed totals did not fully reconcile: treat as provisional) or check_failed (core figures missing or implausible: not used in reports). unusable_fields lists figures in that year that should not be quoted, with the reason.",
                "raw_food_per_resident_day": "Raw food cost / resident days. Only shown when the home buys its own food; when a contractor supplies meals the raw-food line is not comparable.",
            },
            "caveats": c.get("caveats") or self.d["cost_index"].get("caveats"),
            "years": years,
            "dss_review": self.d["dss_review"]["facilities"].get(ccn),
            "dss_review_definitions": self.d["dss_review"].get("definitions"),
        }

    def inspections(self, ccn):
        h = sorted(self.health.get(ccn) or [], key=lambda r: r["survey_date"], reverse=True)
        f = sorted(self.fire.get(ccn) or [], key=lambda r: r["survey_date"], reverse=True)
        p = sorted(self.pen.get(ccn) or [], key=lambda r: r["penalty_date"], reverse=True)
        s = self.survey.get(ccn)
        return {
            "summary": s,
            "health_citations": [{
                "survey_date": r["survey_date"], "tag": r["deficiency_code"], "description": r["deficiency_description"],
                "category": r.get("deficiency_category"), "scope_severity": r.get("scope_severity_code"),
                "harm_level": r.get("harm_ij_group"), "complaint": r.get("complaint_deficiency"), "standard": r.get("standard_deficiency"),
                "correction_date": r.get("correction_date"), "under_idr": r.get("citation_under_idr"),
                "record_id": r.get("source_row_hash", "")[:16]} for r in h],
            "fire_safety_citations": [{
                "survey_date": r["survey_date"], "tag": r["deficiency_code"], "description": r["deficiency_description"],
                "scope_severity": r.get("scope_severity_code"), "correction_date": r.get("correction_date")} for r in f],
            "penalties": [{
                "date": r["penalty_date"], "type": r.get("penalty_type"), "fine_amount": r.get("normalized_fine_amount"),
                "payment_denial_start": r.get("payment_denial_start_date"), "payment_denial_days": r.get("payment_denial_length_days"),
                "record_id": r.get("source_row_hash", "")[:16]} for r in p],
            "scope_severity_key": "A-C no actual harm, potential for minimal harm; D-F potential for more than minimal harm; G-I actual harm; J-L immediate jeopardy. Letters within each group rise from isolated to pattern to widespread.",
            "window": {"health": [self.d["health"]["metadata"].get("survey_date_min"), self.d["health"]["metadata"].get("survey_date_max")]},
        }

    # --------------------------------------------------------------- reports
    def base_report(self, rtype, ccn, ident):
        return {
            "schema_version": SCHEMA_VERSION,
            "report_type": rtype,
            "subject": {"facility_name": ident["facility_name"], "ccn": ccn, "city": ident["city"]},
            "generated_at": self.generated_at,
            "data_as_of": self.data_as_of,
            "executive_summary": [],
            "findings": [],
            "metrics": {},
            "historical_trends": {},
            "relationships": [],
            "sources": [],
            "limitations": [],
            "missing_data": [],
            "recommended_follow_up": [],
            "links": self.links(ccn),
        }

    def finish(self, rep):
        keys = []
        for f in rep["findings"]:
            for e in f["evidence"]:
                if e["source_key"] not in keys:
                    keys.append(e["source_key"])
        for r in rep["relationships"]:
            k = r.get("source_key")
            if k and k not in keys:
                keys.append(k)
        rep["sources"] = [{"source_key": k, **{kk: vv for kk, vv in self.reg[k].items()}} for k in keys]
        rep["limitations"].append("Built only from public datasets published on danbeem.xyz. Absence of a record means it is not in these datasets, not that it did not happen.")
        rep["limitations"].append("Every finding is labeled confirmed_fact, calculated, possible_association or investigative_question. Possible associations are not evidence of ownership, control or a conflict of interest.")
        return rep

    def staffing_findings(self, ccn, rep, staff):
        ev = self.ev
        qs = [q for q in staff["quarters"] if q["total_nurse_hprd"] is not None]
        if not qs:
            rep["missing_data"].append({"field": "staffing", "reason": "No PBJ staffing quarters for this CCN."})
            return
        last = qs[-1]
        rep["metrics"]["latest_quarter"] = last["quarter"]
        rep["metrics"]["total_nurse_hprd"] = last["total_nurse_hprd"]
        rep["metrics"]["rn_hprd"] = last["rn_hprd"]
        rep["metrics"]["contract_staff_pct"] = last["contract_staff_pct"]
        rep["metrics"]["statewide_median_total_nurse_hprd"] = last["statewide_median_total_nurse_hprd"]
        e = [ev("cms_pbj", period=last["quarter"], record=f"CCN {ccn}, {last['quarter']}", ccn=ccn)]
        rep["findings"].append(finding(
            "staffing-latest", "calculated",
            f"In {last['quarter']}, total nurse staffing was {last['total_nurse_hprd']} hours per resident day "
            f"(RN {last['rn_hprd']}, LPN {last['lpn_hprd']}, aides {last['aide_hprd']}); the Connecticut median that quarter was {last['statewide_median_total_nurse_hprd']}.",
            e, value=last["total_nurse_hprd"], formula="PBJ paid nursing hours / resident days"))
        if last["contract_staff_pct"] is not None and last["statewide_median_contract_staff_pct"] is not None:
            hi = last["contract_staff_pct"] >= 2 * max(last["statewide_median_contract_staff_pct"], 1)
            rep["findings"].append(finding(
                "staffing-contract", "calculated",
                f"Contract (agency) staff made up {last['contract_staff_pct']}% of nursing hours in {last['quarter']} "
                f"(Connecticut median {last['statewide_median_contract_staff_pct']}%).",
                e, value=last["contract_staff_pct"], formula="PBJ contract hours / all nursing hours x 100",
                severity="attention" if hi else "info"))
        below = [q["quarter"] for q in qs if q.get("ct_below_total_minimum_estimate") and q.get("ct_comparison_status") != "reference_only"]
        if below:
            rep["findings"].append(finding(
                "staffing-ct-minimum", "calculated",
                f"PBJ-based estimate was below the Connecticut total direct-care comparison point in {len(below)} quarter(s): {', '.join(below[-8:])}.",
                [ev("cms_pbj", period=f"{below[0]}-{below[-1]}", record=f"CCN {ccn}", ccn=ccn, note="Screening estimate; PBJ does not show shifts.")],
                value=len(below), severity="attention",
                formula="quarterly PBJ direct-care HPRD estimate < CT total direct-care comparison point (3.00 since 2022)"))
            rep["recommended_follow_up"].append("Check daily staffing for the flagged quarters on the Daily vs. CT Minimums page, then ask the facility for posted daily staffing records.")
        first = qs[0]
        xq = [q["quarter"] for q in qs]
        rep.setdefault("charts", []).extend([
            chart("staffing-total-hprd", "Total nurse staffing vs. Connecticut median", "line", "hours per resident day", xq,
                  [("This home", "home", [q["total_nurse_hprd"] for q in qs]),
                   ("Connecticut median", "benchmark", [q.get("statewide_median_total_nurse_hprd") for q in qs])],
                  source_key="cms_pbj", note="CMS Payroll-Based Journal, paid nursing hours per resident day by quarter."),
            chart("staffing-contract-pct", "Agency (contract) share of nursing hours", "line", "% of nursing hours", xq,
                  [("This home", "home", [q.get("contract_staff_pct") for q in qs]),
                   ("Connecticut median", "benchmark", [q.get("statewide_median_contract_staff_pct") for q in qs])],
                  source_key="cms_pbj"),
        ])
        rep["historical_trends"]["total_nurse_hprd"] = {q["quarter"]: q["total_nurse_hprd"] for q in qs}
        rep["historical_trends"]["contract_staff_pct"] = {q["quarter"]: q["contract_staff_pct"] for q in qs}
        if len(qs) >= 8:
            chg = round(last["total_nurse_hprd"] - first["total_nurse_hprd"], 2)
            rep["findings"].append(finding(
                "staffing-trend", "calculated",
                f"Total nurse staffing changed by {chg:+} hours per resident day from {first['quarter']} ({first['total_nurse_hprd']}) to {last['quarter']} ({last['total_nurse_hprd']}).",
                [ev("cms_pbj", period=f"{first['quarter']}-{last['quarter']}", record=f"CCN {ccn}", ccn=ccn)], value=chg,
                formula="latest quarter HPRD - first quarter HPRD"))

    def financial_findings(self, ccn, rep, fin):
        ev = self.ev
        rep["definitions"] = dict(fin["definitions"])
        rep["links"]["underlying_data"] = rep["links"]["financials"]
        full = [y for y in fin["years"] if not y.get("part_year")]
        if not full:
            rep["missing_data"].append({"field": "dss_cost_reports", "reason": "No full-year DSS cost report for this CCN."})
            return
        usable_years = [y for y in full if y["data_quality"]["use_in_reports"]]
        for y in full:
            q = y["data_quality"]
            if not q["use_in_reports"]:
                rep["missing_data"].append({
                    "field": f"dss_cost_report_{y['cost_year']}",
                    "reason": f"Cost year {y['cost_year']} is left out of this report: its figures failed the site's checks ("
                              + ("; ".join(q["issues"] + [f"{k}: {v}" for k, v in q["unusable_fields"].items() if k == "resident_days"]) or "core figures missing")
                              + "). The filing is still listed in financials.json."})
        if not usable_years:
            rep["missing_data"].append({"field": "dss_cost_reports", "reason": "No cost-report year for this CCN passed the site's checks."})
            return
        y = usable_years[-1]
        cy = y["cost_year"]
        q = y["data_quality"]
        bad = q["unusable_fields"]
        if full[-1] is not y:
            rep["limitations"].append(f"The latest filed cost year ({full[-1]['cost_year']}) failed the site's checks, so this report uses cost year {cy}.")
        rec = f"DSS cost report {cy}, {y.get('source_file')}"
        period = f"{y['period_start']} to {y['period_end']}"
        note = None
        if q["status"] == "unvalidated":
            note = "Printed totals on this report did not fully reconcile (" + "; ".join(q["issues"]) + "). Treat figures as provisional."
            rep["limitations"].append(f"Cost year {cy} figures are provisional: " + "; ".join(q["issues"]) + ".")
        e = [ev("dss_cost_reports", period=period, record=rec, ccn=ccn, note=note,
                verification="source_record" if q["status"] == "validated" else "source_record_unvalidated")]
        dc = y["direct_care"]
        med = y.get("statewide_median_same_year") or {}
        money = lambda v: f"-${-v:,.0f}" if v < 0 else f"${v:,.0f}"  # noqa: E731
        months = lambda d: dt.date.fromisoformat(d).strftime("%B %Y")  # noqa: E731
        m = rep["metrics"]
        m["latest_cost_year"] = cy
        m["cost_report_check_status"] = q["status"]
        m["resident_days"] = y.get("resident_days")
        for k, v in bad.items():
            if k in ("revenue_total", "expenses_total", "net_income"):
                continue  # whole-home totals are not used in reports; see financials.json
            rep["missing_data"].append({"field": f"{k}_{cy}", "reason": f"Cost year {cy} {k.replace('_', ' ')} is not used: {v}."})

        if "direct_care" not in bad:
            m["direct_care_per_resident_day"] = dc.get("per_resident_day")
            m["statewide_median_direct_care_per_resident_day"] = med.get("direct_care_per_resident_day")
            rep["findings"].append(finding(
                "fin-direct-care", "calculated",
                f"Cost year {cy}: direct care cost was ${dc['per_resident_day']} per resident day "
                f"({round((dc.get('share_of_expenses') or 0) * 100, 1)}% of expenses); Connecticut median ${med.get('direct_care_per_resident_day')}.",
                e, value=dc["per_resident_day"], formula="(nursing + aide salaries + allocated fringe + nursing pool) / resident days"))
            pool = dc.get("nursing_pool_agency") or 0
            if pool and dc.get("total"):
                share = round(pool / dc["total"] * 100, 1)
                m["agency_share_of_direct_care_pct"] = share
                rep["findings"].append(finding(
                    "fin-agency-share", "calculated",
                    f"Cost year {cy}: nursing pool (agency) staff counted in direct care cost {money(pool)}, {share}% of the {money(dc['total'])} direct care cost.",
                    e, value=share, formula="nursing pool direct-care cost / direct care total x 100"))
        if y.get("management_fee_reported"):
            m["management_fee_reported"] = y["management_fee_reported"]
            mf_prd = round(y["management_fee_reported"] / y["resident_days"], 2)
            m["management_fee_per_resident_day"] = mf_prd
            m["statewide_median_management_fee_per_resident_day"] = med.get("management_fees_per_resident_day")
            rep["findings"].append(finding(
                "fin-mgmt-fee", "confirmed_fact",
                f"Cost year {cy}: the home reported {money(y['management_fee_reported'])} in management fees (cost report line m12), "
                f"${mf_prd} per resident day" + (f" (Connecticut median ${med['management_fees_per_resident_day']} among homes reporting a fee)." if med.get("management_fees_per_resident_day") else "."),
                e, value=y["management_fee_reported"]))
        if y.get("related_party_total_reported") is not None:
            m["related_party_total_reported"] = y["related_party_total_reported"]
        if y.get("nursing_pool_agency_cost"):
            m["nursing_pool_agency_cost"] = y["nursing_pool_agency_cost"]
            rep["findings"].append(finding(
                "fin-agency", "confirmed_fact",
                f"Cost year {cy}: total nursing pool (agency) fees on the report were {money(y['nursing_pool_agency_cost'])}"
                + (f", of which {money(dc['nursing_pool_agency'])} is counted in direct care." if dc.get("nursing_pool_agency") and dc["nursing_pool_agency"] != y["nursing_pool_agency_cost"] else "."),
                e, value=y["nursing_pool_agency_cost"]))
        if y.get("operating_margin_nursing_home") is not None:
            m["operating_margin_nursing_home"] = y["operating_margin_nursing_home"]
            m["statewide_median_operating_margin_nursing_home"] = med.get("operating_margin_nh")
            rep["findings"].append(finding(
                "fin-margin", "calculated",
                f"Cost year {cy}: nursing home operating margin was {round(y['operating_margin_nursing_home'] * 100, 1)}% "
                f"(Connecticut median {round((med.get('operating_margin_nh') or 0) * 100, 1)}%).",
                e, value=y["operating_margin_nursing_home"], formula="(nursing home revenue - nursing home expenses) / revenue"))

        # What DSS's review changed and what Medicaid pays: separate layers, never blended with reported spending.
        dss = fin.get("dss_review") or {}
        dy = (dss.get("years") or {}).get(str(cy))
        rates = dss.get("rates") or {}
        if not dss:
            rep["missing_data"].append({"field": "dss_review", "reason": "DSS review adjustments and Medicaid rates are not matched to this home (DSS provider name not tied to its CCN, or not in DSS's published files)."})
        dss_ev = lambda rec: [ev("dss_review", period=f"cost year {cy}", record=rec, ccn=ccn,  # noqa: E731
                                 note="DSS's published cost-report data; review adjustments can still change after audit.")]
        if dy:
            net = dy.get("review_adjustments_total") or 0
            real = [x for x in dy.get("largest_review_adjustments") or [] if not x.get("moved_between_lines")]
            m["dss_review_net_adjustment"] = net
            m["home_self_adjustments"] = dy.get("home_adjustments_total")
            top = "; ".join(f"{x['name']} (page {x['page']} line {x['line']}), {'removed' if x['review_adjustment'] < 0 else 'added'} {money(abs(x['review_adjustment']))}" for x in real[:3])
            rep["findings"].append(finding(
                "fin-dss-review", "confirmed_fact",
                f"Cost year {cy}: DSS's review changed {dy['review_adjusted_lines']} line(s) of the report, a net {'reduction' if net < 0 else 'increase'} of {money(abs(net))} in the costs DSS counts"
                + (f". Largest: {top}." if top else ".")
                + (f" Separately, the home itself removed {money(abs(dy['home_adjustments_total']))} from the costs it claimed (for example bad debt, pharmacy or therapy that the daily rate does not cover)." if dy.get("home_adjustments_total") else "")
                + " The data shows each change, not the reason.",
                dss_ev(f"{dy.get('source')}, cost year {cy}"), value=net))
            mf, mfa = dy.get("management_fee_reported"), dy.get("management_fee_review_adjustment")
            if mf and mfa:
                m["management_fee_after_dss_review"] = mf + (dy.get("management_fee_home_adjustment") or 0) + mfa
                rep["findings"].append(finding(
                    "fin-dss-mgmt", "confirmed_fact",
                    f"Cost year {cy}: DSS's review {'removed' if mfa < 0 else 'added'} {money(abs(mfa))} of the {money(mf)} management fee (page 16, line m12), leaving "
                    f"{money(m['management_fee_after_dss_review'])} in the costs DSS counts. The data shows the change, not the reason; "
                    "DSS caps management fees and can remove related-party charges.",
                    dss_ev(f"{dy.get('source')}, page 16 line m12"), value=mfa))
            per = dy.get("medicaid_revenue_net_per_medicaid_day")
            if per and dy.get("medicaid_revenue_net"):
                m["medicaid_revenue_per_medicaid_day"] = per
                m["medicaid_days"] = dy.get("medicaid_ct_days")
                if y.get("resident_days"):
                    m["medicaid_share_of_resident_days_pct"] = round(dy["medicaid_ct_days"] / y["resident_days"] * 100, 1)
                rate_txt = " and ".join(f"${v['per_diem']:,.2f} for {months(v['rate_period'][:10])} to {months(v['rate_period'][-10:])}" for k, v in sorted(rates.items()))
                rep["findings"].append(finding(
                    "fin-medicaid-paid", "calculated",
                    f"Cost year {cy}: the home recorded {money(dy['medicaid_revenue_net'])} in Connecticut Medicaid revenue (after its Medicaid contractual allowance) "
                    f"for {dy['medicaid_ct_days']:,} Medicaid days, ${per} per Medicaid day."
                    + (f" DSS's Medicaid daily rate was {rate_txt}." if rate_txt else ""),
                    dss_ev(f"{dy.get('source')}, page 30 lines I1a and I1b; page 8 line 3B")
                    + ([ev("dss_rates", period=", ".join(v["rate_period"] for v in rates.values()), record="rate letters, provider " + next(iter(rates.values()))["provider_number"], ccn=ccn)] if rates else []),
                    value=per, formula="(Medicaid CT revenue + Medicaid contractual allowance) / Medicaid CT days"))
                exp = y.get("expenses_per_resident_day")
                if exp:
                    m["reported_cost_per_resident_day"] = exp
                    rep["findings"].append(finding(
                        "fin-cost-vs-medicaid", "calculated",
                        f"Cost year {cy}: reported cost was ${exp} per resident day (all payers, before DSS review) and Medicaid revenue was ${per} per Medicaid day. "
                        "Reported cost includes items Medicaid does not pay for in the daily rate (for example pharmacy and therapy), so the difference is not a Medicaid shortfall.",
                        dss_ev(f"{dy.get('source')}") + e, value=round(exp - per, 2),
                        formula="reported nursing-home cost / all resident days, compared with net Medicaid revenue / Medicaid days"))
            rows = [{"page": x["page"], "line": x["line"], "item": x["name"], "reported": x["reported"], "home_adjustment": x.get("home_adjustment"),
                     "dss_review_adjustment": x["review_adjustment"], "after_dss_review": x["after_review"],
                     "moved_between_lines": x.get("moved_between_lines", False)} for x in dy.get("largest_review_adjustments") or []]
            if rows:
                rep.setdefault("tables", []).append({
                    "id": "dss-review-adjustments", "title": f"Largest changes in DSS's review, cost year {cy}",
                    "description": "What the home reported, what it removed itself, and what DSS's review changed. 'Moved between lines' means the cost was reclassified, not removed. The data does not give reasons.",
                    "source_key": "dss_review", "reporting_period": f"cost year {cy}", "rows": rows})
        dyears = sorted((dss.get("years") or {}).items())
        if dyears:
            by_cost = {str(r["cost_year"]): r for r in fin["years"] if r["data_quality"]["use_in_reports"]}
            xs2 = [k for k, v in dyears if v.get("medicaid_revenue_net_per_medicaid_day")]
            if xs2:
                rep.setdefault("charts", []).append(chart(
                    "fin-cost-vs-medicaid", "Reported cost per resident day vs. Medicaid revenue per Medicaid day", "bar", "$ per resident day", xs2,
                    [("Reported cost per resident day (all payers, before review)", "home", [(by_cost.get(k) or {}).get("expenses_per_resident_day") for k in xs2]),
                     ("Medicaid revenue per Medicaid day", "home_secondary", [dict(dyears)[k]["medicaid_revenue_net_per_medicaid_day"] for k in xs2])],
                    source_key="dss_review", note="Not a Medicaid shortfall: reported cost includes items the daily rate does not cover. Cost years end September 30."))

        # Support departments: wages, fringe and non-wage costs side by side, never wages alone.
        dept_rows = []
        for d in SUPPORT_DEPTS:
            dep = y.get(d) or {}
            if not dep.get("total_department_cost") and not dep.get("wages_reported"):
                rep["missing_data"].append({"field": f"{d}_{cy}", "reason": f"Cost year {cy}: no {d} costs were read from the report."})
                continue
            tot = dep.get("total_department_cost") or 0
            wages, fr, other = dep.get("wages_reported") or 0, dep.get("fringe_allocated") or 0, dep.get("non_salary") or 0
            prd, mprd = dep.get("per_resident_day"), med.get(f"{d}_per_resident_day")
            row = {"department": DEPT_LABEL[d], "wages_reported": dep.get("wages_reported"), "fringe_allocated": dep.get("fringe_allocated"),
                   "non_wage_costs": dep.get("non_salary"), "total_department_cost": dep.get("total_department_cost"),
                   "wage_share_pct": round(wages / tot * 100, 1) if tot else None,
                   "non_wage_share_pct": round(other / tot * 100, 1) if tot else None,
                   "per_resident_day": prd if d not in bad else None, "statewide_median_per_resident_day": mprd,
                   "usable": d not in bad, "note": bad.get(d)}
            dept_rows.append(row)
            if d in bad:
                continue
            m[f"{d}_per_resident_day"] = prd
            m[f"statewide_median_{d}_per_resident_day"] = mprd
            extra = ""
            if d == "dietary":
                food = y.get("food") or {}
                if y.get("raw_food_per_resident_day") is not None:
                    m["raw_food_per_resident_day"] = y["raw_food_per_resident_day"]
                    m["statewide_median_raw_food_per_resident_day"] = med.get("raw_food_per_resident_day")
                    extra = (f" Raw food was {money(food.get('raw_food') or 0)} (${y['raw_food_per_resident_day']} per resident day; "
                             f"Connecticut median ${med.get('raw_food_per_resident_day')})")
                    extra += f" and purchased dietary services {money(food['contract_services'])}." if food.get("contract_services") else "."
                elif food.get("purchasing") == "contractor":
                    extra = (" Most food spending was a purchased (contracted) service"
                             + (f" ({money(food['contract_services'])})" if food.get("contract_services") else "")
                             + ", so raw food per resident day is not comparable with homes that buy their own food.")
            rep["findings"].append(finding(
                f"fin-dept-{d}", "calculated",
                f"Cost year {cy}: {d} cost {money(tot)}, ${prd} per resident day (Connecticut median ${mprd}). "
                f"Wages {money(wages)} ({row['wage_share_pct']}%), allocated fringe {money(fr)} ({round(fr / tot * 100, 1) if tot else 0}%), "
                f"non-wage costs {money(other)} ({row['non_wage_share_pct']}%).{extra}",
                e, value=prd, formula=f"({d} wages + their share of fringe benefits + {d} non-salary costs) / resident days"))
            if mprd and prd is not None and (prd < 0.5 * mprd or prd > 1.75 * mprd):
                low = prd < mprd
                rep["findings"].append(finding(
                    f"fin-dept-{d}-question", "investigative_question",
                    f"Cost year {cy}: {d} cost per resident day (${prd}) was {round(prd / mprd * 100)}% of the Connecticut median (${mprd}). "
                    + (f"Ask how {d} is handled: by the home's own staff, by a contracted service, or with costs reported in another department."
                       if low else f"Ask what drove the higher {d} cost (contracts, supplies, staffing or a one-time expense)."),
                    e, value=round(prd / mprd, 2), severity="attention"))
                rep["recommended_follow_up"].append(
                    f"Ask the home or DSS how {d} costs are reported on the cost report (in-house staff, purchased services or another department).")
            if not wages and other:
                rep["findings"].append(finding(
                    f"fin-dept-{d}-no-wages", "investigative_question",
                    f"Cost year {cy}: no {d} wages were reported but {money(other)} in non-wage {d} costs was. This often means the service is contracted; the cost report alone does not name the contractor.",
                    e, value=other))

        # Who the home paid, as disclosed on the cost report, and who CMS listed as manager that year.
        rels = []
        ms_used = set()
        for i, rp in enumerate(y["related_parties"]):
            if not rp.get("name_as_printed") and not rp.get("cost_reported"):
                continue
            also = None
            for j, ms in enumerate(y["management_services"]):
                if norm_name(rp.get("name_as_printed")) and norm_name(ms.get("name") or "").startswith(norm_name(rp["name_as_printed"])) and ms.get("cost") == rp.get("cost_reported"):
                    also = "management services line"
                    ms_used.add(j)
            rels.append({"relationship_type": "cost_report_related_party", "entity_name": rp.get("name_as_printed"),
                         "description": rp.get("description"), "category": rp.get("category"),
                         "cost_reported": rp.get("cost_reported"), "actual_cost_to_related_party": rp.get("actual_cost_to_related_party"),
                         "where_on_report": rp.get("where_on_report"), "also_reported_on": also, "cost_year": cy,
                         "start": y["period_start"], "end": y["period_end"], "source_key": "dss_cost_reports"})
            what = rp.get("description") or rp.get("category") or "an unspecified purpose"
            cost = money(rp["cost_reported"]) if rp.get("cost_reported") is not None else "an amount not read from the report"
            who = f"\"{rp['name_as_printed']}\"" if rp.get("name_as_printed") else "a party whose name was not read from the report"
            rep["findings"].append(finding(
                f"rp-{cy}-{i}", "confirmed_fact",
                f"Cost year {cy}: related party disclosed as {who} for {what}, cost reported {cost}"
                + (f" ({rp['where_on_report']})" if rp.get("where_on_report") else "") + ".",
                [ev("dss_cost_reports", period=period, record=f"DSS cost report {cy} {rp.get('where_on_report') or ''}".strip(), ccn=ccn,
                    note="Name text is read from the PDF by software and may be truncated.")],
                value=rp.get("cost_reported")))
        for j, ms in enumerate(y["management_services"]):
            if j in ms_used or not (ms.get("name") or ms.get("cost")):
                continue
            rels.append({"relationship_type": "cost_report_management_services", "entity_name": (ms.get("name") or "")[:120] or None,
                         "description": ms.get("description"), "cost_reported": ms.get("cost"), "cost_year": cy,
                         "start": y["period_start"], "end": y["period_end"], "source_key": "dss_cost_reports"})
        for mc in y.get("management_company_on_file_during_year") or []:
            rels.append({"relationship_type": "management_company_on_file", "company_id": mc.get("company_id"), "company_name": mc.get("name"),
                         "start": mc.get("start"), "end": mc.get("end"), "current": mc.get("current"), "source_key": "management_companies"})
            rep["findings"].append(finding(
                f"fin-mgmt-on-file-{mc.get('company_id')}-{mc.get('start')}-{mc.get('end') or 'present'}", "confirmed_fact",
                f"During cost year {cy}, {mc.get('name')} was on file as a management company for this home ({mc.get('start')} to {mc.get('end') or 'present'}).",
                [ev("management_companies", period=f"{mc.get('start')} to {mc.get('end') or 'present'}", record=mc.get("company_id"), ccn=ccn)]))
        rep["relationships"] = rels
        if rels and not y["related_parties"] and not y["management_services"]:
            pass
        elif not rels:
            rep["missing_data"].append({"field": f"related_parties_{cy}", "reason": f"No related parties or management-service payees were read from the cost year {cy} report. That means none were read, not that none exist."})

        # Year-by-year table and trends, from years that passed the checks.
        def val(yr, field, getter):
            return None if field in yr["data_quality"]["unusable_fields"] else getter(yr)
        by_year = []
        for yr in usable_years:
            md = yr.get("statewide_median_same_year") or {}
            by_year.append({
                "cost_year": yr["cost_year"], "check_status": yr["data_quality"]["status"],
                "resident_days": yr.get("resident_days"),
                "direct_care_per_resident_day": val(yr, "direct_care", lambda z: z["direct_care"]["per_resident_day"]),
                "statewide_median_direct_care_per_resident_day": md.get("direct_care_per_resident_day"),
                "nursing_pool_agency_cost": yr.get("nursing_pool_agency_cost"),
                "operating_margin_nursing_home": yr.get("operating_margin_nursing_home"),
                "statewide_median_operating_margin_nursing_home": md.get("operating_margin_nh"),
                "management_fee_reported": yr.get("management_fee_reported"),
                "related_party_total_reported": yr.get("related_party_total_reported"),
                **{f"{d}_per_resident_day": val(yr, d, lambda z, d=d: z[d]["per_resident_day"]) for d in SUPPORT_DEPTS},
                **{f"statewide_median_{d}_per_resident_day": md.get(f"{d}_per_resident_day") for d in SUPPORT_DEPTS},
                "raw_food_per_resident_day": val(yr, "raw_food", lambda z: z.get("raw_food_per_resident_day")),
            })
        ht = rep["historical_trends"]
        for k in ("direct_care_per_resident_day", "nursing_pool_agency_cost", "operating_margin_nursing_home", "management_fee_reported",
                  "related_party_total_reported", "dietary_per_resident_day", "housekeeping_per_resident_day", "laundry_per_resident_day",
                  "raw_food_per_resident_day"):
            ht[k] = {r["cost_year"]: r[k] for r in by_year}
        rep.setdefault("tables", [])[:0] = [
            {"id": "support-departments", "title": f"Support department costs, cost year {cy}",
             "description": "Wages alone are not department spending: each department's total is wages + its share of fringe benefits + non-wage costs (supplies, purchased services, other).",
             "source_key": "dss_cost_reports", "reporting_period": period, "rows": dept_rows},
            {"id": "financials-by-year", "title": "Cost-report figures by year",
             "description": "Only years that passed the site's checks. check_status 'unvalidated' means the printed totals did not fully reconcile; treat those figures as provisional. Statewide medians use validated reports only.",
             "source_key": "dss_cost_reports", "rows": by_year},
        ]
        xs = [r["cost_year"] for r in by_year]
        dept_x = [r["department"] for r in dept_rows if r["usable"]]
        dept_home = [r["per_resident_day"] for r in dept_rows if r["usable"]]
        dept_med = [r["statewide_median_per_resident_day"] for r in dept_rows if r["usable"]]
        if "raw_food" not in bad and y.get("raw_food_per_resident_day") is not None:
            dept_x.append("Raw food"); dept_home.append(y["raw_food_per_resident_day"]); dept_med.append(med.get("raw_food_per_resident_day"))
        charts = [
            chart("fin-direct-care-trend", "Direct care cost per resident day vs. Connecticut median", "line", "$ per resident day", xs,
                  [("This home", "home", [r["direct_care_per_resident_day"] for r in by_year]),
                   ("Connecticut median", "benchmark", [r["statewide_median_direct_care_per_resident_day"] for r in by_year])],
                  source_key="dss_cost_reports", note="Cost years ending September 30. Years that failed the site's checks are left out. Not adjusted for inflation."),
        ]
        if dept_x:
            charts.append(chart("fin-departments", f"Support departments per resident day, cost year {cy}", "bar", "$ per resident day", dept_x,
                                [("This home", "home", dept_home), ("Connecticut median", "benchmark", dept_med)],
                                source_key="dss_cost_reports", note="Department cost = wages + their share of fringe benefits + non-wage costs."))
        if any(r["nursing_pool_agency_cost"] for r in by_year):
            charts.append(chart("fin-agency-cost", "Nursing pool (agency) cost by cost year", "bar", "$", xs,
                                [("This home", "home", [r["nursing_pool_agency_cost"] for r in by_year])],
                                source_key="dss_cost_reports", note="As filed; not adjusted for inflation."))
        if any(r["management_fee_reported"] or r["related_party_total_reported"] for r in by_year):
            charts.append(chart("fin-mgmt-related", "Management fees and related-party costs by cost year", "bar", "$", xs,
                                [("Management fees", "home", [r["management_fee_reported"] for r in by_year]),
                                 ("Related-party costs reported", "home_secondary", [r["related_party_total_reported"] for r in by_year])],
                                source_key="dss_cost_reports", note="The two can overlap: a management fee paid to a related party is counted in both."))
        rep.setdefault("charts", []).extend(charts)
        trend = [r for r in by_year if r["direct_care_per_resident_day"] is not None]
        if len([r for r in trend if r["check_status"] == "validated"]) >= 3:
            trend = [r for r in trend if r["check_status"] == "validated"]  # endpoints from reconciled reports only
        if len(trend) >= 3:
            a, b_ = trend[0], trend[-1]
            ma, mb = a["statewide_median_direct_care_per_resident_day"], b_["statewide_median_direct_care_per_resident_day"]
            rep["findings"].append(finding(
                "fin-direct-care-trend", "calculated",
                f"Direct care cost per resident day went from ${a['direct_care_per_resident_day']} (cost year {a['cost_year']}) to "
                f"${b_['direct_care_per_resident_day']} (cost year {b_['cost_year']})"
                + (f"; over the same years the Connecticut median went from ${ma} to ${mb}." if ma and mb else "."),
                [ev("dss_cost_reports", period=f"{a['cost_year']}-{b_['cost_year']}", record=f"CCN {ccn}, {len(trend)} cost years", ccn=ccn,
                    verification="derived", note="Endpoints use validated reports when at least three are on file; years that failed the site's checks are always left out.")],
                value=round(b_["direct_care_per_resident_day"] - a["direct_care_per_resident_day"], 2),
                formula="latest usable year direct care per resident day - earliest usable year"))
        ag = [r for r in by_year if r["nursing_pool_agency_cost"] is not None]
        if len([r for r in ag if r["check_status"] == "validated"]) >= 3:
            ag = [r for r in ag if r["check_status"] == "validated"]
        if len(ag) >= 3 and ag[-1]["nursing_pool_agency_cost"]:
            peak = max(ag, key=lambda r: r["nursing_pool_agency_cost"])
            rep["findings"].append(finding(
                "fin-agency-trend", "calculated",
                f"Nursing pool (agency) cost was {money(ag[0]['nursing_pool_agency_cost'])} in cost year {ag[0]['cost_year']} and "
                f"{money(ag[-1]['nursing_pool_agency_cost'])} in cost year {ag[-1]['cost_year']}"
                + (f"; the highest year was {peak['cost_year']} ({money(peak['nursing_pool_agency_cost'])})." if peak is not ag[-1] else ", the highest year on file."),
                [ev("dss_cost_reports", period=f"{ag[0]['cost_year']}-{ag[-1]['cost_year']}", record=f"CCN {ccn}, {len(ag)} cost years", ccn=ccn,
                    verification="derived", note="Not adjusted for inflation.")],
                value=ag[-1]["nursing_pool_agency_cost"], formula="nursing pool professional fees as reported each year"))
        rep["limitations"].append("Dollar figures are as filed, before DSS audit, and are not adjusted for inflation. Compare per-resident-day figures with the Connecticut median for the same year.")
        rep["limitations"].append(f"Every year's full detail, including years left out here and the reason, is in {rep['links']['financials']}.")

    def regulatory_findings(self, ccn, rep, insp):
        ev = self.ev
        h = insp["health_citations"]
        s = insp["summary"] or {}
        if not h and not insp["penalties"]:
            rep["missing_data"].append({"field": "inspections", "reason": "No health citations or penalties for this CCN in the CMS window."})
        harm = [c for c in h if c["harm_level"] and ("harm" in c["harm_level"] and "no_actual" not in c["harm_level"] or "jeopardy" in c["harm_level"])]
        ij = [c for c in h if (c["scope_severity"] or "") in ("J", "K", "L")]
        per_year = defaultdict(int)
        for c in h:
            per_year[c["survey_date"][:4]] += 1
        rep["historical_trends"]["health_citations_per_year"] = dict(sorted(per_year.items()))
        rep["metrics"].update({
            "health_citations_total": len(h),
            "actual_harm_or_ij_citations": len(harm),
            "immediate_jeopardy_citations": len(ij),
            "fines_total": round(sum(p["fine_amount"] or 0 for p in insp["penalties"]), 2),
            "penalty_count": len(insp["penalties"]),
            "latest_health_survey": s.get("latest_health_survey_date"),
        })
        win = insp["window"]["health"]
        e = [ev("cms_health_citations", period=f"{win[0]} to {win[1]}", record=f"CCN {ccn}", ccn=ccn)]
        rep["findings"].append(finding(
            "reg-count", "confirmed_fact",
            f"CMS lists {len(h)} health citations for this home between {win[0]} and {win[1]}, including {len(harm)} at actual harm or immediate jeopardy level ({len(ij)} immediate jeopardy).",
            e, value=len(h), severity="attention" if ij else "info"))
        for c in ij[:5]:
            rep["findings"].append(finding(
                f"reg-ij-{c['survey_date']}-{c['tag']}", "confirmed_fact",
                f"{c['survey_date']}: {c['tag']} ({c['scope_severity']}) {c['description']}",
                [ev("cms_health_citations", period=c["survey_date"], record=f"CCN {ccn} {c['tag']} {c['survey_date']} row {c['record_id']}", ccn=ccn)],
                severity="attention"))
        if insp["penalties"]:
            pe = [ev("cms_penalties", period=f"{insp['penalties'][-1]['date']} to {insp['penalties'][0]['date']}", record=f"CCN {ccn}", ccn=ccn)]
            rep["findings"].append(finding(
                "reg-penalties", "confirmed_fact",
                f"CMS lists {len(insp['penalties'])} penalties, with fines totaling ${rep['metrics']['fines_total']:,.2f}.",
                pe, value=rep["metrics"]["fines_total"]))
        tags = defaultdict(int)
        for c in h:
            tags[c["tag"]] += 1
        rep["metrics"]["most_cited_tags"] = [{"tag": t, "count": n} for t, n in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))[:8]]

    def relationship_findings(self, ccn, rep, own, fin, screening=False):
        ev = self.ev
        cur = [r for r in own["cms_ownership_and_control"] if r["current"]]
        # Reports carry current CMS records, all management periods and recent
        # administrators; the full history lives in ownership.json (linked).
        keep = ("entity_name", "entity_type", "cms_associate_id", "relationship_type", "cms_role_verbatim",
                "association_date", "current", "also_listed_at_ccns", "verification", "source_key")
        rep["relationships"] = (
            [{k: r[k] for k in keep} for r in cur]
            + [dict(m) for m in own["management_companies"]]
            + [dict(a) for a in own["administrators_of_record"][:5]]
        )
        rep["metrics"]["cms_records_all_releases"] = len(own["cms_ownership_and_control"])
        rep["links"]["full_relationship_history"] = rep["links"]["ownership"]
        ident_ev = [ev("cms_all_owners", period=(own.get("cms_owners_window") or {}).get("latest_release"), record=f"CCN {ccn}", ccn=ccn)]
        owners = [r for r in cur if r["relationship_type"] == "ownership_interest"]
        control = [r for r in cur if r["relationship_type"] == "operational_or_managerial_control"]
        rep["metrics"]["current_cms_owner_records"] = len(owners)
        rep["metrics"]["current_cms_control_records"] = len(control)
        if owners:
            rep["findings"].append(finding(
                "own-current", "confirmed_fact",
                "Current ownership interests reported to CMS: " + "; ".join(f"{r['entity_name']} ({r['cms_role_verbatim']})" for r in owners[:8]) + ".",
                ident_ev))
        else:
            rep["findings"].append(finding(
                "own-none-listed", "investigative_question",
                "No current ownership-interest records are listed for this home in CMS All Owners (common for nonprofits, which list directors and officers instead). Confirm the licensee with DPH.",
                ident_ev))
        if control:
            rep["findings"].append(finding(
                "own-control", "confirmed_fact",
                "Current operational/managerial control reported to CMS: " + "; ".join(f"{r['entity_name']} (since {r['association_date']})" for r in control) + ".",
                ident_ev))
        for m in own["management_companies"]:
            rep["findings"].append(finding(
                f"mgmt-{m['company_id']}-{m['start']}-{m['end'] or 'present'}", "confirmed_fact",
                f"{m['company_name']} is listed as management company from {m['start']} to {m['end'] or 'present'}.",
                [ev("management_companies", period=f"{m['start']} to {m['end'] or 'present'}", record=m["company_id"], ccn=ccn)]))
        # shared principals by CMS associate id (strong id), current or past
        shared = {}
        for r in own["cms_ownership_and_control"]:
            if r["also_listed_at_ccns"] and r["relationship_type"] in ("ownership_interest", "operational_or_managerial_control", "officer_director_trustee"):
                shared.setdefault(r["cms_associate_id"], r)
        rep["metrics"]["shared_principals_with_other_ct_homes"] = len(shared)
        for aid, r in list(shared.items())[: (25 if screening else 8)]:
            homes = r["also_listed_at_ccns"]
            names = [f"{self.name(h)} ({h})" for h in homes[:6]]
            rep["findings"].append(finding(
                f"assoc-{aid}", "possible_association",
                f"{r['entity_name']} (CMS associate ID {aid}, {r['cms_role_verbatim']} at this home, "
                f"{'current' if r['current'] else 'past: last listed ' + str(r['last_seen_release'])}) also appears in CMS ownership records "
                f"for {len(homes)} other CT home(s) at some point in the {(own.get('cms_owners_window') or {}).get('first_release')} to "
                f"{(own.get('cms_owners_window') or {}).get('latest_release')} releases: {', '.join(names)}{'...' if len(homes) > 6 else ''}. "
                "Same CMS ID means the same reported entity; it does not by itself show common ownership, control or any financial conflict.",
                [ev("cms_all_owners", record=f"associate {aid}", ccn=ccn, verification="source_record",
                    note="Matched on CMS associate ID, not on name.")]))
        # cost report related parties
        ys = [y for y in fin["years"] if y["data_quality"]["use_in_reports"]] or fin["years"]
        if ys:
            y = ys[-1]
            for i, rp in enumerate(y["related_parties"]):
                if not rp.get("name_as_printed") and not rp.get("cost_reported"):
                    continue
                what = rp.get("description") or rp.get("category") or "an unspecified purpose"
                cost = f"${rp['cost_reported']:,.0f}" if rp.get("cost_reported") is not None else "an amount not read from the report"
                where = f" ({rp['where_on_report']})" if rp.get("where_on_report") else ""
                who = f"\"{rp['name_as_printed']}\"" if rp.get("name_as_printed") else "a party whose name was not read from the report"
                rep["findings"].append(finding(
                    f"rp-{y['cost_year']}-{i}", "confirmed_fact",
                    f"Cost year {y['cost_year']}: related party disclosed as {who} for {what}, cost reported {cost}{where}.",
                    [ev("dss_cost_reports", period=f"{y['period_start']} to {y['period_end']}", record=f"DSS cost report {y['cost_year']} {rp['where_on_report']}", ccn=ccn,
                        note="Name text is read from the PDF by software and may be truncated.")],
                    value=rp["cost_reported"]))
                # does the related party match a CMS-listed entity at this home (name only)?
                n = norm_name(rp["name_as_printed"])
                hits = [r for r in own["cms_ownership_and_control"] if n and len(n) > 4 and norm_name(r["entity_name"]) == n]
                if hits:
                    rep["findings"].append(finding(
                        f"rp-name-match-{y['cost_year']}-{i}", "possible_association",
                        f"The related party name \"{rp['name_as_printed']}\" matches a CMS-listed entity at this home ({hits[0]['entity_name']}, {hits[0]['cms_role_verbatim']}) by name only.",
                        [ev("dss_cost_reports", record=f"DSS cost report {y['cost_year']} {rp['where_on_report']}", ccn=ccn, verification="name_match_unverified"),
                         ev("cms_all_owners", record=f"associate {hits[0]['cms_associate_id']}", ccn=ccn, verification="name_match_unverified")]))
            legal = (self.fac_meta.get(ccn) or {}).get("enrollment_organization_name")
            mgmt_names = [norm_name(m["company_name"]) for m in own["management_companies"]]
            for ms in y["management_services"]:
                nm = ms.get("name") or ""
                if legal and norm_name(legal) and norm_name(legal) in norm_name(nm):
                    rep["findings"].append(finding(
                        f"rp-mgmt-self-{y['cost_year']}", "possible_association",
                        f"Cost year {y['cost_year']}: management services (${(ms.get('cost') or 0):,.0f}) are paid to \"{nm[:80]}\", whose name matches the home's CMS-enrolled legal entity ({legal}). "
                        "This can mean a parent or home-office charge; the cost report alone does not say what the fee covers.",
                        [ev("dss_cost_reports", record=f"DSS cost report {y['cost_year']} management services", ccn=ccn, verification="name_match_unverified"),
                         ev("cms_enrollment", record=f"CCN {ccn} enrollment", ccn=ccn)]))
                elif nm and not any(m and m in norm_name(nm) for m in mgmt_names):
                    rep["recommended_follow_up"].append(
                        f"Identify who \"{nm[:80]}\" is (paid ${(ms.get('cost') or 0):,.0f} for management services in cost year {y['cost_year']}); it does not match a management company on file for this home.")
        if screening:
            rep["findings"].append(finding(
                "screen-unlisted-names", "investigative_question",
                "Relationships reported elsewhere (news, complaints, word of mouth) but absent from these datasets cannot be confirmed here. "
                f"Check any such name against {SITE}/api/v1/search-index.json; if it is not there, it is not in any dataset on this site.",
                [ev("site_roster", record="search index")]))
            rep["recommended_follow_up"].extend([
                "Request the home's DSS cost report schedules for related-party transactions and management agreements for the same years.",
                "Compare CMS All Owners with the DPH license file and Secretary of the State business records for the legal entity and each organization listed.",
                "For any vendor named in complaints but not in these datasets, ask DSS whether it appears on the home's related-party schedule.",
            ])

    # -------------------------------------------------------------- per ccn
    def build_facility(self, ccn):
        ident, missing = self.identity(ccn)
        own = self.ownership(ccn)
        staff = self.staffing(ccn)
        fin = self.financials(ccn)
        insp = self.inspections(ccn)
        envelope = lambda kind, body: {  # noqa: E731
            "schema_version": SCHEMA_VERSION, "endpoint": kind, "ccn": ccn, "facility_name": ident["facility_name"],
            "generated_at": self.generated_at, "data_as_of": self.data_as_of, "links": self.links(ccn), **body}
        self.write(f"v1/facilities/{ccn}/profile.json", envelope("profile", {
            "identity": ident, "missing_data": missing,
            "ownership_summary": {
                "current_cms_records": sum(1 for r in own["cms_ownership_and_control"] if r["current"]),
                "management_companies": own["management_companies"],
                "current_administrator": next((a for a in own["administrators_of_record"] if a.get("current")), None),
            },
            "staffing_latest": staff["quarters"][-1] if staff["quarters"] else None,
            "financial_latest": ({k: v for k, v in fin["years"][-1].items() if k not in ("related_parties", "management_services")} if fin["years"] else None),
            "inspection_summary": insp["summary"],
        }))
        self.write(f"v1/facilities/{ccn}/ownership.json", envelope("ownership", own))
        self.write(f"v1/facilities/{ccn}/staffing.json", envelope("staffing", staff))
        self.write(f"v1/facilities/{ccn}/financials.json", envelope("financials", fin))
        self.write(f"v1/facilities/{ccn}/inspections.json", envelope("inspections", insp))

        reports = {}
        r = self.base_report("staffing-analysis", ccn, ident)
        self.staffing_findings(ccn, r, staff)
        reports[r["report_type"]] = r
        r = self.base_report("financial-transparency", ccn, ident)
        self.financial_findings(ccn, r, fin)
        reports[r["report_type"]] = r
        r = self.base_report("regulatory-history", ccn, ident)
        self.regulatory_findings(ccn, r, insp)
        reports[r["report_type"]] = r
        r = self.base_report("ownership-network", ccn, ident)
        self.relationship_findings(ccn, r, own, fin, screening=False)
        reports[r["report_type"]] = r
        r = self.base_report("related-party-screening", ccn, ident)
        self.relationship_findings(ccn, r, own, fin, screening=True)
        reports[r["report_type"]] = r
        comp = self.base_report("facility-comprehensive", ccn, ident)
        comp["tables"], comp["definitions"], comp["charts"] = [], {}, []
        for t in ("ownership-network", "staffing-analysis", "financial-transparency", "regulatory-history"):
            sub = reports[t]
            seen = {f["id"] for f in comp["findings"]}
            comp["findings"].extend(f for f in sub["findings"] if f["id"] not in seen)
            comp["tables"].extend(sub.get("tables") or [])
            comp["charts"].extend(sub.get("charts") or [])
            comp["definitions"].update(sub.get("definitions") or {})
            comp["metrics"].update(sub["metrics"])
            comp["historical_trends"].update(sub["historical_trends"])
            comp["missing_data"].extend(sub["missing_data"])
            comp["recommended_follow_up"].extend(sub["recommended_follow_up"])
            comp["limitations"].extend(x for x in sub["limitations"] if x not in comp["limitations"])
        comp["relationships"] = reports["ownership-network"]["relationships"] + [
            r for r in reports["financial-transparency"]["relationships"] if r["relationship_type"] != "management_company_on_file"]
        comp["identity"] = ident
        if ident.get("operating_status") and ident["operating_status"] != "in_current_cms_provider_info":
            comp["findings"].insert(0, finding(
                "status", "confirmed_fact",
                f"Operating status: {ident['operating_status'].replace('_', ' ')}"
                + (f" ({ident['operating_status_date']})" if ident.get("operating_status_date") else "") + ". Older data below may describe the home before it closed or changed.",
                [self.ev("site_roster", record=f"CCN {ccn}", ccn=ccn)], severity="attention"))
        comp["missing_data"] = missing + comp["missing_data"]
        reports["facility-comprehensive"] = comp
        for t, rep in reports.items():
            rep["missing_data"] = missing + [m for m in rep["missing_data"] if m not in missing] if t != "facility-comprehensive" else rep["missing_data"]
            rep["executive_summary"] = self.summarize(rep)
            self.finish(rep)
            self.write(f"v1/reports/{t}/{ccn}.json", rep)
        return ident, own, staff, fin, insp

    # Which findings lead the executive summary, per report type (attention items always come first).
    SUMMARY_PRIORITY = {
        "financial-transparency": ["fin-direct-care", "fin-medicaid-paid", "fin-dss-mgmt", "fin-margin", "fin-agency-share", "fin-dept-dietary", "fin-dept-housekeeping",
                                   "fin-dept-laundry", "fin-dss-review", "fin-mgmt-fee", "rp-", "fin-direct-care-trend"],
    }

    @staticmethod
    def summarize(rep):
        out = []
        order = {"attention": 0, "info": 1}
        prio = Builder.SUMMARY_PRIORITY.get(rep.get("report_type"), [])

        def rank(f):
            p = next((i for i, x in enumerate(prio) if f["id"] == x or (x.endswith("-") and f["id"].startswith(x))), len(prio))
            return (order.get(f["severity"], 2), p, ["confirmed_fact", "calculated", "possible_association", "investigative_question"].index(f["kind"]))
        fs = sorted(rep["findings"], key=rank)
        for f in fs[:6]:
            out.append({"text": f["statement"], "kind": f["kind"], "finding_id": f["id"]})
        if rep["missing_data"]:
            years = [m["field"].rsplit("_", 1)[1] for m in rep["missing_data"] if re.fullmatch(r"dss_cost_report_\d{4}", m["field"])]
            rest = [m for m in rep["missing_data"] if not re.fullmatch(r"dss_cost_report_\d{4}", m["field"])]
            bits = []
            if years:
                bits.append(f"cost year{'s' if len(years) > 1 else ''} {', '.join(years)} left out because the figures failed the site's checks (reasons under missing_data)")
            bits += [m["reason"] for m in rest[:3]]
            out.append({"text": "Missing data: " + "; ".join(bits), "kind": "missing_data", "finding_id": None})
        return out

    # ----------------------------------------------------------- companies
    def build_companies(self):
        alias_map = defaultdict(list)
        for a in self.d["aliases"].get("aliases") or []:
            alias_map[norm_name(a.get("dph_name"))].append(a.get("cms_name"))
        listing = []
        for cid, c in sorted(self.companies.items()):
            homes = c.get("homes") or []
            body = {
                "schema_version": SCHEMA_VERSION, "endpoint": "management-company", "id": cid, "name": c.get("name"),
                "other_names": sorted(set((c.get("other_names") or []) + alias_map.get(norm_name(c.get("name")), []))),
                "dph_license": c.get("dph_license"), "homes_total": c.get("homes_total"), "homes_current": c.get("homes_current"),
                "homes": homes, "generated_at": self.generated_at, "data_as_of": self.data_as_of,
                "source": {"source_key": "management_companies", **self.reg["management_companies"]},
                "links": {"portfolio_report": f"{SITE}/api/v1/reports/management-company-portfolio/{cid}.json",
                          "site_page": f"{SITE}/staffing/tools/nursing-home-management-companies.html?company={cid}"},
            }
            self.write(f"v1/management-companies/{cid}.json", body)
            listing.append({"id": cid, "name": c.get("name"), "other_names": body["other_names"],
                            "homes_total": c.get("homes_total"), "homes_current": c.get("homes_current"),
                            "url": f"{SITE}/api/v1/management-companies/{cid}.json"})
            # portfolio report
            rep = {
                "schema_version": SCHEMA_VERSION, "report_type": "management-company-portfolio",
                "subject": {"company_id": cid, "company_name": c.get("name")},
                "generated_at": self.generated_at, "data_as_of": self.data_as_of,
                "executive_summary": [], "findings": [], "metrics": {}, "historical_trends": {}, "relationships": [],
                "sources": [], "limitations": [], "missing_data": [], "recommended_follow_up": [],
                "links": body["links"],
            }
            fees = (self.d["cost_index"].get("management_fees_by_company") or {}).get(cid) or {}
            hp = []
            for h in homes:
                ctx = h.get("context") or {}
                hp.append(ctx.get("ct_direct_care_hprd"))
                rep["relationships"].append({"ccn": h["ccn"], "facility_name": h.get("facility_name"), "relationship_type": "management_company",
                                             "cms_role_verbatim": h.get("role"), "start": h.get("start"), "end": h.get("end"), "current": h.get("current"),
                                             "staffing_during_management": ctx, "source_key": "management_companies"})
                rep["findings"].append(finding(
                    f"home-{h['ccn']}-{h.get('start')}-{h.get('end') or 'present'}", "confirmed_fact",
                    f"{h.get('facility_name')} ({h['ccn']}): {h.get('role')} from {h.get('start')} to {h.get('end') or 'present'}"
                    + (f"; staffing during this period averaged {ctx.get('total_nurse_hprd')} total nurse HPRD over {ctx.get('quarters')} quarters." if ctx.get("total_nurse_hprd") is not None else "."),
                    [self.ev("management_companies", period=f"{h.get('start')} to {h.get('end') or 'present'}", record=f"{cid} / CCN {h['ccn']}")]))
            rep["metrics"] = {"homes_total": c.get("homes_total"), "homes_current": c.get("homes_current"),
                              "median_ct_direct_care_hprd_during_management": median(hp)}
            if fees:
                rep["historical_trends"]["management_fees_reported_by_year"] = {y: v.get("total") for y, v in sorted(fees.items())}
                ly = sorted(fees)[-1]
                rep["findings"].append(finding(
                    "fees-latest", "confirmed_fact",
                    f"In cost year {ly}, homes linked to this company reported ${fees[ly]['total']:,.0f} in management fees on DSS cost reports.",
                    [self.ev("dss_cost_reports", period=str(ly), record=f"management fees, {len(fees[ly].get('homes') or [])} line(s)")],
                    value=fees[ly]["total"]))
            else:
                rep["missing_data"].append({"field": "management_fees", "reason": "No DSS cost-report management fee lines are linked to this company id."})
            rep["executive_summary"] = self.summarize(rep)
            self.finish(rep)
            self.write(f"v1/reports/management-company-portfolio/{cid}.json", rep)
        self.write("v1/management-companies.json", {
            "schema_version": SCHEMA_VERSION, "endpoint": "management-companies", "generated_at": self.generated_at,
            "count": len(listing), "companies": listing})
        return listing

    # ----------------------------------------------------------------- run
    def run(self):
        if self.out.exists():
            shutil.rmtree(self.out / "v1", ignore_errors=True)
        facilities = []
        search = []
        rp_index = {}  # cost-report related-party names, one entry per normalized name
        for ccn in self.ccns:
            ident, own, staff, fin, insp = self.build_facility(ccn)
            facilities.append({
                "ccn": ccn, "facility_name": ident["facility_name"], "city": ident["city"],
                "operating_status": ident["operating_status"], "legal_entity": ident["legal_entity_cms_enrollment"],
                "management_current": [m["company_name"] for m in own["management_companies"] if m.get("current")],
                "profile": f"{SITE}/api/v1/facilities/{ccn}/profile.json",
            })
            search.append({"type": "facility", "id": ccn, "name": ident["facility_name"], "ccns": [ccn]})
            for alt in sorted({a for a in (ident.get("legal_entity_cms_enrollment"), ident.get("doing_business_as_cms_enrollment"), (self.cost.get(ccn) or {}).get("facility_name")) if a}):
                if alt and alt != ident["facility_name"]:
                    search.append({"type": "facility_alias", "id": ccn, "name": alt, "ccns": [ccn]})
            for y in (self.cost.get(ccn) or {}).get("cost_years") or []:
                for rp in y.get("related_parties") or []:
                    k = norm_name(rp.get("name_guess"))
                    if k:
                        e = rp_index.setdefault(k, {"type": "cost_report_related_party", "id": "rp:" + k, "name": rp["name_guess"],
                                                    "ccns": set(), "cost_years": set()})
                        e["ccns"].add(ccn)
                        e["cost_years"].add(y["cost_year"])
        for k in sorted(rp_index):
            e = rp_index[k]
            search.append({**e, "ccns": sorted(e["ccns"]), "cost_years": sorted(e["cost_years"])})
        for aid, homes in sorted(self.assoc_homes.items()):
            for n in sorted(self.assoc_names[aid]):
                search.append({"type": "cms_owner_" + self.assoc_type[aid].lower(), "id": aid, "name": n, "ccns": sorted(homes)})
        listing = self.build_companies()
        for c in listing:
            for n in [c["name"]] + c["other_names"]:
                search.append({"type": "management_company", "id": c["id"], "name": n,
                               "ccns": sorted({h["ccn"] for h in self.companies[c["id"]].get("homes") or []})})
        for p in self.d["admins"].get("people") or []:
            search.append({"type": "administrator", "id": p["id"], "name": p["name"],
                           "ccns": sorted({r.get("ccn") for r in p.get("roles") or [] if r.get("ccn")})})
        seen, dedup = set(), []
        for s in search:
            k = (s["type"], s["id"], s["name"])
            if k not in seen:
                seen.add(k)
                s["key"] = norm_name(s["name"])
                dedup.append(s)
        self.write("v1/search-index.json", {
            "schema_version": SCHEMA_VERSION, "endpoint": "search-index", "generated_at": self.generated_at,
            "how_to_search": "Normalize the query the same way as `key` (upper case, punctuation and suffixes like INC/LLC removed) and match substrings. "
                             "Entities are never merged on name: the same name under different ids stays separate. A name not in this index is not in any dataset on this site.",
            "count": len(dedup), "entries": dedup})
        self.write("v1/facilities.json", {
            "schema_version": SCHEMA_VERSION, "endpoint": "facilities", "generated_at": self.generated_at,
            "count": len(facilities), "facilities": facilities})
        self.write("v1/index.json", {
            "schema_version": SCHEMA_VERSION, "api": "Connecticut Nursing Home Reporting API (read-only, static)",
            "generated_at": self.generated_at, "data_as_of": self.data_as_of,
            "docs": f"{SITE}/api/docs/", "openapi": f"{SITE}/api/openapi.json", "llms": f"{SITE}/llms.txt",
            "report_schema": f"{SITE}/api/v1/schema/report.schema.json",
            "facility_report_types": REPORT_TYPES, "company_report_types": COMPANY_REPORT_TYPES,
            "url_templates": {
                "facility_list": f"{SITE}/api/v1/facilities.json",
                "profile": f"{SITE}/api/v1/facilities/{{ccn}}/profile.json",
                "ownership": f"{SITE}/api/v1/facilities/{{ccn}}/ownership.json",
                "staffing": f"{SITE}/api/v1/facilities/{{ccn}}/staffing.json",
                "financials": f"{SITE}/api/v1/facilities/{{ccn}}/financials.json",
                "inspections": f"{SITE}/api/v1/facilities/{{ccn}}/inspections.json",
                "report": f"{SITE}/api/v1/reports/{{report_type}}/{{ccn}}.json",
                "management_companies": f"{SITE}/api/v1/management-companies.json",
                "management_company": f"{SITE}/api/v1/management-companies/{{company_id}}.json",
                "management_company_report": f"{SITE}/api/v1/reports/management-company-portfolio/{{company_id}}.json",
                "search_index": f"{SITE}/api/v1/search-index.json",
            },
            "sources": self.reg,
            "evidence_kinds": {
                "confirmed_fact": "Value printed in a public source record.",
                "calculated": "Arithmetic on confirmed facts; formula given.",
                "possible_association": "Shared entity, name or principal. Not evidence of ownership, control or conflict of interest.",
                "investigative_question": "Something the data cannot answer that a person should check.",
            },
            "counts": {"facilities": len(facilities), "management_companies": len(listing)},
        })
        (self.out / "v1" / "schema").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "scripts" / "reporting_api_report.schema.json", self.out / "v1" / "schema" / "report.schema.json")
        return {"files": self.files, "bytes": self.bytes, "facilities": len(facilities), "companies": len(listing)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "api"))
    args = ap.parse_args()
    stats = Builder(Path(args.out)).run()
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
