"""Build the public Connecticut nursing home management company data.

Inputs:
- data/testing/ct_management_relationships_<date>.json (private, git-ignored): management periods built
  from the Connecticut organization rows of the CMS Nursing Home Ownership file in each monthly Care
  Compare archive (roles OPERATIONAL/MANAGERIAL CONTROL and CONTRACTED MANAGING EMPLOYEE).
  Individual owners and officers are dropped when the archives are read.
- data/testing/ct_dph_management_companies.csv (optional, private copy of the DPH eLicense roster
  "Nursing Home Management Company"): company license number, status and dates. Addresses are not used.
- data/nursing_home_staffing_history_ct.json and data/ct_nursing_home_administrators.json (public).

Output: data/ct_nursing_home_management_companies.json (public).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import build_ct_administrators_public as admins_pub

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELATIONSHIPS = ROOT / "data" / "testing" / "ct_management_relationships_20261028.json"
DEFAULT_DPH = ROOT / "data" / "testing" / "ct_dph_management_companies.csv"
DEFAULT_HISTORY = ROOT / "data" / "nursing_home_staffing_history_ct.json"
DEFAULT_STAFFING = ROOT / "data" / "nursing_home_staffing_ct.json"
DEFAULT_ADMINS = ROOT / "data" / "ct_nursing_home_administrators.json"
DEFAULT_OUT = ROOT / "data" / "ct_nursing_home_management_companies.json"
DEFAULT_ALIASES = ROOT / "data" / "ct_management_company_aliases.json"
SCHEMA = "ct-nursing-home-management-companies-1.0"

CAVEATS = [
    "Management relationships are the organizations a nursing home reported to CMS with operational or "
    "managerial control (or as a contracted managing employee). CMS publishes what facilities report, and "
    "reports can lag actual changes.",
    "Operational or managerial control is not the same as ownership or legal responsibility. A home's own "
    "parent or sponsoring organization can hold this role, as can an outside management company.",
    "Periods are observed in monthly CMS releases from January 2020 to the latest release. A relationship "
    "already in place in January 2020 starts at the association date CMS reports. An ended relationship "
    "ended between the last release that listed it and the next release.",
    "Facility conditions during a management period reflect many factors and are not a measure of the "
    "management company's performance.",
    "Listing is not an allegation of wrongdoing.",
    "Staffing context comes from CMS Payroll-Based Journal data, which starts in Q4 2017.",
]
CORRECTIONS_NOTICE = ("Records come from public state and federal sources. To report an error, email "
                      "hello@danbeem.xyz.")


def identity(name: str) -> str:
    """Same legal name up to punctuation and "&"/"AND". Different suffixes (LLC, INC) stay separate."""
    text = re.sub(r"[^A-Z0-9 ]+", " ", (name or "").upper().replace("&", " AND "))
    return " ".join(text.split())


def slug(name: str) -> str:
    return "mc-" + re.sub(r"[^a-z0-9]+", "-", identity(name).lower()).strip("-")


def load_dph(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("FACILITY NAME") or "").strip()
            if not name:
                continue
            out[identity(name)] = {
                "name": name, "license_number": (row.get("LICENSE NO.") or "").strip(),
                "status": (row.get("STATUS") or "").strip(),
                "effective": iso_date(row.get("EFFECTIVE DATE")),
                "expires": iso_date(row.get("EXPIRATION DATE")),
            }
    return out


def iso_date(value: str | None) -> str | None:
    value = (value or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y%m%d", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def overlaps(a_start, a_end, b_start, b_end, as_of) -> bool:
    """True when two date ranges overlap by more than one day; open ends run to as_of."""
    if not a_start and not a_end:
        return False
    lo = max(a_start or a_end, b_start)
    hi = min(a_end or as_of, b_end or as_of)
    return (date.fromisoformat(hi) - date.fromisoformat(lo)).days > 1


def build(rel: dict, dph: dict[str, dict], history: dict, staffing: dict, admins: dict,
          aliases: list[dict] | None = None) -> dict:
    releases = rel["releases"]
    first_release, latest = releases[0], releases[-1]
    by_ccn = admins_pub.context_index(history)
    facility_names = {f["ccn"]: f.get("provider_name") for f in staffing["facilities"]}
    admin_fac = {f["ccn"]: f for f in admins["facilities"] if f["ccn"]}
    variants = rel["name_variants"]

    # Reviewed links between a CMS-reported name and a DPH license name (e.g. spacing differences).
    alias_map = {identity(a["cms_name"]): identity(a["dph_name"]) for a in (aliases or [])
                 if a.get("reviewed") and a.get("note")}
    groups: dict[str, list[dict]] = defaultdict(list)
    display: dict[str, Counter] = defaultdict(Counter)
    for r in rel["relationships"]:
        cid = slug(r["org"])
        groups[cid].append(r)
        display[cid].update(variants.get(r["org"], {r["org"]: 1}))

    companies = []
    for cid, rels in groups.items():
        name = display[cid].most_common(1)[0][0]
        homes = []
        for r in sorted(rels, key=lambda r: (r["first_seen"], r["ccn"])):
            dates = r["association_dates"]
            in_first = r["first_seen"] == first_release
            if dates:
                start, start_basis = dates[0], "association date reported to CMS"
            else:
                start = r["first_seen"]
                start_basis = ("listed in the first CMS release in this data" if in_first
                               else "first CMS release listing this relationship")
            end = None if r["current"] else r["last_seen"]
            admin_rows = []
            fac = admin_fac.get(r["ccn"])
            for a in (fac or {}).get("administrators", []):
                if overlaps(a["start"], a["end"], start, end, latest):
                    admin_rows.append({k: a[k] for k in ("person_id", "name", "license_number", "start", "end", "open")})
            homes.append({
                "ccn": r["ccn"],
                "facility_name": (fac or {}).get("facility_name") or facility_names.get(r["ccn"])
                                 or rel["provider_names"].get(r["ccn"]) or r["ccn"],
                "role": r["roles"][0].title().replace("/", " / ") if len(r["roles"]) == 1 else "; ".join(x.title() for x in r["roles"]),
                "start": start, "start_basis": start_basis,
                "later_association_dates": dates[1:],
                "end": end, "ended_before": r["ended_by"], "current": r["current"],
                "context": admins_pub.tenure_context(r["ccn"], start, end, latest, by_ccn),
                "administrators": admin_rows,
            })
        lic = dph.get(identity(name)) or dph.get(alias_map.get(identity(name), ""))
        current = {h["ccn"] for h in homes if h["current"]}
        companies.append({
            "id": cid, "name": name,
            "other_names": sorted(n for n in display[cid] if n != name),
            "dph_license": lic,
            "homes_total": len({h["ccn"] for h in homes}), "homes_current": len(current),
            "homes": homes,
        })
    # DPH-licensed companies with no CMS management listing are shown too, with no homes.
    used = {identity(c["dph_license"]["name"]) for c in companies if c["dph_license"]}
    for key, lic in dph.items():
        if key in used:
            continue
        companies.append({"id": slug(lic["name"]), "name": lic["name"], "other_names": [],
                          "dph_license": lic, "homes_total": 0, "homes_current": 0, "homes": []})
    companies.sort(key=lambda c: (-c["homes_current"], -c["homes_total"], c["name"]))

    facilities = defaultdict(list)
    for c in companies:
        for h in c["homes"]:
            facilities[h["ccn"]].append({"company_id": c["id"], "name": c["name"], "start": h["start"],
                                         "start_basis": h["start_basis"], "end": h["end"],
                                         "ended_before": h["ended_before"], "current": h["current"]})
    for rows in facilities.values():
        rows.sort(key=lambda x: (not x["current"], x["end"] or "9999", x["start"]), reverse=False)

    return {
        "schema_version": SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_as_of": latest,
        "window": {"first_release": first_release, "latest_release": latest, "releases": len(releases)},
        "sources": [
            {"title": "CMS Nursing Home Ownership (Care Compare monthly archives), Connecticut organizations",
             "as_of": latest, "url": "https://data.cms.gov/provider-data/topics/nursing-homes",
             "note": f"{len(releases)} monthly releases, {first_release} to {latest}. Roles: operational/managerial control, contracted managing employee."},
            {"title": "Connecticut DPH Nursing Home Management Company roster (eLicense export)",
             "as_of": "2026-11-05" if dph else None,
             "note": "Licensed management companies, license status and dates." if dph else
                     "Not yet loaded; DPH license badges are not shown."},
            {"title": "CMS Payroll-Based Journal staffing history (Q4 2017 onward)",
             "as_of": history.get("history_window", {}).get("latest_quarter"),
             "note": "Each home's staffing during the management period."},
        ],
        "caveats": CAVEATS,
        "corrections_notice": CORRECTIONS_NOTICE,
        "summary": {
            "companies": len(companies),
            "homes": len({h["ccn"] for c in companies for h in c["homes"]}),
            "periods": sum(len(c["homes"]) for c in companies),
            "current_periods": sum(1 for c in companies for h in c["homes"] if h["current"]),
            "dph_licensed_companies_matched": sum(1 for c in companies if c["dph_license"] and c["homes"]),
            "dph_licensed_without_cms_listing": sum(1 for c in companies if c["dph_license"] and not c["homes"]),
        },
        "companies": companies,
        "facilities": [{"ccn": k, "management": v} for k, v in sorted(facilities.items())],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--relationships", type=Path, default=DEFAULT_RELATIONSHIPS)
    ap.add_argument("--dph", type=Path, default=DEFAULT_DPH)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    aliases = load(DEFAULT_ALIASES)["aliases"] if DEFAULT_ALIASES.exists() else []
    result = build(load(args.relationships), load_dph(args.dph), load(DEFAULT_HISTORY),
                   load(DEFAULT_STAFFING), load(DEFAULT_ADMINS), aliases)
    args.out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    s = result["summary"]
    print(f"Wrote {args.out.relative_to(ROOT)}: {s['companies']} companies, {s['homes']} homes, "
          f"{s['periods']} periods ({s['current_periods']} current), {s['dph_licensed_companies_matched']} DPH-licensed matched, "
          f"{s['dph_licensed_without_cms_listing']} DPH-licensed without a CMS listing")


if __name__ == "__main__":
    main()
