"""Report how current each data source on the staffing tools is, from the published data files alone.

Offline: reads data/data_sources.json (each source's update schedule) and the version each public data file
says it was built from. Prints one line per source and a final summary line.

  python scripts/validate_data_freshness.py            # warns about overdue sources, exits 0
  python scripts/validate_data_freshness.py --strict   # exits 1 if any source is overdue
  python scripts/validate_data_freshness.py --json out.json

A source is OVERDUE when the version on the site is older than its 'max_age_days'. That means a newer
release is probably out; the refresh runbook (docs/data_refresh_runbook.md) says how to pull it in.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def load(rel):
    p = ROOT / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def month_from_name(text):
    """'NH_ProviderInfo_Aug2026.csv' -> date(2026, 8, 1); 'SNF_Enrollments_2026.05.01.csv' -> date(2026, 5, 1)."""
    if not text:
        return None
    m = re.search(r"_(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*_?(\d{4})", text)
    if m:
        return dt.date(int(m.group(2)), MONTHS[m.group(1).lower()], 1)
    m = re.search(r"(\d{4})[.\-_](\d{2})[.\-_](\d{2})", text)
    if m:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"(\d{4})-(\d{2})(?!-)", text)
    if m:
        return dt.date(int(m.group(1)), int(m.group(2)), 1)
    return None


def quarter_end(q):
    """'2026Q1' -> date(2026, 3, 31)."""
    y, n = int(q[:4]), int(q[-1])
    return dt.date(y + (n == 4), 1 if n == 4 else 3 * n + 1, 1) - dt.timedelta(days=1)


def on_site_versions():
    """{source_id: (label, date the version represents)} from the published data files."""
    out = {}
    staffing = load("data/nursing_home_staffing_ct.json") or {}
    q = (staffing.get("reporting_period") or {}).get("quarter")
    if q:
        out["cms_pbj"] = (q, quarter_end(q))
    for src in staffing.get("sources", []):
        name, rel = src.get("source_dataset_name", ""), src.get("source_release", "")
        key = {"CMS Nursing Home Provider Information": "cms_provider_info",
               "CMS Skilled Nursing Facility Enrollments": "cms_snf_enrollments",
               "CMS Nursing Home Quality Measures Claims": "cms_quality_claims"}.get(name)
        d = month_from_name(rel)
        if key and d:
            out[key] = (Path(rel.replace("\\", "/")).name, d)
    for key, rel in (("cms_health_deficiencies", "data/nursing_home_health_deficiencies_ct.json"),
                     ("cms_fire_safety_deficiencies", "data/nursing_home_fire_safety_deficiencies_ct.json"),
                     ("cms_penalties", "data/nursing_home_penalties_ct.json")):
        md = (load(rel) or {}).get("metadata") or {}
        d = month_from_name(md.get("source_file"))
        if d:
            out[key] = (md["source_file"], d)
        if key == "cms_health_deficiencies":
            c = md.get("citation_descriptions_source_file")
            if month_from_name(c):
                out["cms_citation_lookup"] = (c, month_from_name(c))
    mgmt = load("data/ct_nursing_home_management_companies.json") or {}
    latest = (mgmt.get("window") or {}).get("latest_release")
    if latest:
        out["cms_ownership"] = (latest, dt.date.fromisoformat(latest))
    for s in mgmt.get("sources", []):
        if "DPH" in s.get("title", "") and s.get("as_of"):
            out["ct_dph_rosters"] = (s["as_of"], dt.date.fromisoformat(s["as_of"]))
    cost = load("data/ct_nursing_home_cost_reports.json") or {}
    for s in cost.get("sources", []):
        t, a = s.get("title", ""), s.get("as_of")
        if "All Owners" in t and month_from_name(a):
            out["cms_snf_all_owners"] = (a, month_from_name(a))
        elif "Change of Ownership" in t and month_from_name(a):
            out["cms_snf_chow"] = (a, month_from_name(a))
        elif "Skilled Nursing Facility Cost Report" in t and a:
            out["cms_snf_cost_report"] = (a, dt.date.fromisoformat(a))
    years = sorted({int(y) for f in cost.get("facilities", []) for y in f.get("years", {})})
    if years:
        out["ct_dss_cost_reports"] = (f"cost year {years[-1]}", dt.date(years[-1], 9, 30))
    admins = load("data/ct_nursing_home_administrators.json") or {}
    for s in admins.get("sources", []):
        if "State Licenses" in s.get("title", "") and s.get("as_of"):
            out["ct_licenses"] = (s["as_of"], dt.date.fromisoformat(s["as_of"]))
    return out


def report(today=None):
    today = today or dt.date.today()
    reg = load("data/data_sources.json")
    have = on_site_versions()
    rows = []
    for s in reg["sources"]:
        label, d = have.get(s["id"], (None, None))
        if d is None:
            status, age = "UNKNOWN", None
        else:
            age = (today - d).days
            status = "OVERDUE" if age > s["max_age_days"] else "OK"
        rows.append({"id": s["id"], "name": s["name"], "frequency": s["frequency"], "on_site": label,
                     "version_date": d.isoformat() if d else None, "age_days": age,
                     "max_age_days": s["max_age_days"], "status": status, "page": s["page"]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="exit 1 if any source is overdue or unknown")
    ap.add_argument("--json", type=Path, help="also write the report as JSON")
    ap.add_argument("--today", help="YYYY-MM-DD, for testing")
    a = ap.parse_args()
    rows = report(dt.date.fromisoformat(a.today) if a.today else None)
    for r in rows:
        age = f"{r['age_days']} days old" if r["age_days"] is not None else "version not found"
        print(f"{r['status']:8s} {r['name'][:58]:58s} {str(r['on_site'])[:34]:34s} {age} (limit {r['max_age_days']}; {r['frequency']})")
    if a.json:
        a.json.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    over = [r for r in rows if r["status"] != "OK"]
    print(f"Data freshness: {len(rows) - len(over)} of {len(rows)} sources current"
          + (f"; {len(over)} need a refresh: {', '.join(r['id'] for r in over)}." if over else "."))
    return 1 if (a.strict and over) else 0


if __name__ == "__main__":
    sys.exit(main())
