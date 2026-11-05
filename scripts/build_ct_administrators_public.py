"""Build the public CT nursing home administrator search data.

Inputs (all but the last are private and git-ignored):
- data/testing/ct_administrator_history_review_<date>_v2.json: the privacy-filtered Phase A review
  written by scripts/build_ct_administrator_history.py (professional fields only).
- data/testing/ct_dph_ccn_crosswalk_decisions_<date>.json: reviewed DPH license -> CCN decisions.
- data/testing/ct_administrator_corrections.json (optional): reviewed corrections/suppressions.
- data/nursing_home_staffing_history_ct.json: public PBJ history used for tenure context.

Output: data/ct_nursing_home_administrators.json (public).

Display rules (Claude's Phase A review, 2026-11-05):
1. Exact duplicate roles (same license, facility, start, end) collapse to one.
2. Only overlaps longer than one day between different facilities are labelled.
3. The 1901-01-01 issue-date placeholder becomes "not recorded" (null).
4. Missing starts and ends stay null; open roles are "open as of the source date", never "current".
5. License status comes from the public CT license dataset, with its as-of date.
6. The license-record name is displayed; every recorded form is searchable.
7. Roles without a usable license appear only in their facility's list, never as people.
8. Tenure staffing context uses PBJ quarters (Q4 2017 onward) whose midpoint falls in the tenure.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = ROOT / "data" / "testing" / "ct_administrator_history_review_20261105_v2.json"
DEFAULT_DECISIONS = ROOT / "data" / "testing" / "ct_dph_ccn_crosswalk_decisions_20261105.json"
DEFAULT_CORRECTIONS = ROOT / "data" / "testing" / "ct_administrator_corrections.json"
DEFAULT_HISTORY = ROOT / "data" / "nursing_home_staffing_history_ct.json"
DEFAULT_STAFFING = ROOT / "data" / "nursing_home_staffing_ct.json"
DEFAULT_OUT = ROOT / "data" / "ct_nursing_home_administrators.json"

SCHEMA = "ct-nursing-home-administrators-1.0"
PLACEHOLDER_ISSUE = "1901-01-01"
PUBLIC_ROLE_FIELDS = ("id", "facility_license", "facility_name", "ccn", "start", "end", "open",
                      "overlap", "context")
CAVEATS = [
    "Records come from public Connecticut DPH license roster exports and the public CT license dataset. "
    "They show the administrator of record a facility reported to DPH, which can lag actual changes.",
    "Facility conditions during this period reflect many factors and are not a measure of the "
    "administrator's performance.",
    "Listing is not an allegation of wrongdoing.",
    "Open roles are open as of the source date; they do not confirm current employment.",
    "People are matched by license number only, never by name.",
    "Coverage: the DPH history covers the 188 chronic and convalescent nursing homes licensed when the "
    "data was downloaded. Service at homes that have since closed is not included.",
    "Staffing context comes from CMS Payroll-Based Journal data, which starts in Q4 2017.",
]
CORRECTIONS_NOTICE = ("Records come from public state and federal sources. To report an error, email "
                      "hello@danbeem.xyz.")


def title_name(raw: str) -> str:
    def fix(word: str) -> str:
        w = word.capitalize()
        w = re.sub(r"^(Mc|O')([a-z])", lambda m: m.group(1) + m.group(2).upper(), w)
        return re.sub(r"-([a-z])", lambda m: "-" + m.group(1).upper(), w)
    text = " ".join((raw or "").split())
    return " ".join(fix(w) if w.isupper() or w.islower() else w for w in text.split())


def parse(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def quarter_mid(row: dict) -> date:
    start, end = parse(row["quarter_start_date"]), parse(row["quarter_end_date"])
    return start + (end - start) / 2


def load_decisions(path: Path) -> dict[str, str]:
    decisions = json.loads(path.read_text(encoding="utf-8"))
    accepted: dict[str, str] = {}
    for d in decisions:
        if d.get("decision") not in ("accepted", "rejected") or not (d.get("note") or "").strip():
            raise ValueError(f"Invalid crosswalk decision for license {d.get('facility_license')}")
        if d["decision"] == "accepted":
            if d["ccn"] in accepted.values():
                raise ValueError(f"CCN {d['ccn']} accepted for more than one license")
            accepted[d["facility_license"]] = d["ccn"]
    return accepted


def context_index(history: dict) -> dict[str, list[dict]]:
    by_ccn: dict[str, list[dict]] = defaultdict(list)
    for row in history["facility_quarterly_staffing_history"]:
        by_ccn[row["ccn"]].append(row)
    return by_ccn


def tenure_context(ccn: str | None, start: str | None, end: str | None, as_of: str,
                   by_ccn: dict[str, list[dict]]) -> dict | None:
    if not ccn or not start:
        return None
    lo, hi = parse(start), parse(end) if end else parse(as_of)
    rows = sorted((r for r in by_ccn.get(ccn, []) if lo <= quarter_mid(r) <= hi),
                  key=lambda r: r["quarter"])
    if not rows:
        return {"quarters": 0}

    def weighted(metric: str) -> float | None:
        pairs = [(r["metrics"].get(metric), r.get("resident_days") or 0) for r in rows]
        pairs = [(v, w) for v, w in pairs if v is not None and w > 0]
        total = sum(w for _, w in pairs)
        return round(sum(v * w for v, w in pairs) / total, 2) if total else None

    return {
        "quarters": len(rows),
        "first_quarter": rows[0]["quarter"], "last_quarter": rows[-1]["quarter"],
        "ct_direct_care_hprd": weighted("ct_direct_care_total_hprd_estimate"),
        "total_nurse_hprd": weighted("total_nurse_hprd"),
        "rn_hprd": weighted("rn_hprd"),
    }


def overlap_days(a: dict, b: dict, as_of: str) -> int:
    if not a["start"] or not b["start"]:
        return 0
    a_end = parse(a["end"]) if a["end"] else (parse(as_of) if a["open"] else None)
    b_end = parse(b["end"]) if b["end"] else (parse(as_of) if b["open"] else None)
    if not a_end or not b_end:
        return 0
    return (min(a_end, b_end) - max(parse(a["start"]), parse(b["start"]))).days


def dedupe(roles: list[dict]) -> list[dict]:
    seen, kept = set(), []
    for r in sorted(roles, key=lambda r: r["id"]):
        key = (r.get("license_number"), r.get("name_raw") if not r.get("license_number") else None,
               r["facility_license"], r["start"], r["end"])
        if key not in seen:
            seen.add(key)
            kept.append(r)
    return kept


def build(review: dict, accepted: dict[str, str], history: dict, staffing: dict,
          corrections: list[dict] | None = None) -> dict:
    if review.get("privacy_check") != "passed":
        raise ValueError("Review privacy check did not pass")
    as_of = review["source_as_of"]
    by_ccn = context_index(history)
    corrections = corrections or []
    suppressed = {c["person_id"] for c in corrections if c.get("action") == "suppress_person"}
    facility_names = {c["facility_license"]: c["facility_name"] for c in review["crosswalk_review"]}

    people = []
    for person in review["people"]:
        if person["id"] in suppressed:
            continue
        observed = [o for o in person.get("license_observations", []) if o.get("name")]
        record_name = next((o["name"] for o in observed if o["source"] == "ct_open_data_ngch_56tr"),
                           observed[0]["name"] if observed else person["name"])
        names = {title_name(record_name)}
        names |= {title_name(o["name"]) for o in observed}
        names |= {r["name"] for r in person["roles"] if r.get("name")}
        roles = []
        for r in dedupe(person["roles"]):
            ccn = accepted.get(r["facility_license"])
            roles.append({
                "id": r["id"], "facility_license": r["facility_license"],
                "facility_name": facility_names.get(r["facility_license"], r["facility_name"]),
                "ccn": ccn, "start": r["start"], "end": r["end"], "open": bool(r["open"]),
                "overlap": False,
                "context": tenure_context(ccn, r["start"], r["end"], as_of, by_ccn),
            })
        for i, a in enumerate(roles):
            for b in roles[i + 1:]:
                if a["facility_license"] != b["facility_license"] and overlap_days(a, b, as_of) > 1:
                    a["overlap"] = b["overlap"] = True
        roles.sort(key=lambda r: (r["start"] or r["end"] or "", r["facility_name"]))
        issued = person.get("license_issued")
        people.append({
            "id": person["id"], "name": title_name(record_name),
            "other_names": sorted(n for n in names if n and n != title_name(record_name)),
            "license_number": person["license_number"],
            "license_status": person.get("license_status"),
            "license_status_as_of": (person.get("license_as_of") or as_of)[:10],
            "license_issued": None if issued == PLACEHOLDER_ISSUE else issued,
            "license_expires": person.get("license_expires"),
            "roles": roles,
        })
    people.sort(key=lambda p: (p["name"].split()[-1].lower() if p["name"] else "", p["name"].lower()))

    facilities: dict[str, dict] = {}
    for c in review["crosswalk_review"]:
        facilities[c["facility_license"]] = {
            "facility_license": c["facility_license"], "facility_name": c["facility_name"],
            "ccn": accepted.get(c["facility_license"]), "administrators": []}
    for p in people:
        for r in p["roles"]:
            facilities[r["facility_license"]]["administrators"].append({
                "person_id": p["id"], "name": p["name"], "license_number": p["license_number"],
                "start": r["start"], "end": r["end"], "open": r["open"]})
    # An unlinked row that repeats a linked row at the same facility exactly (same name,
    # start and end) is a duplicate export record, not a second administrator.
    linked = {(r["facility_license"], r["name"].lower(), r["start"], r["end"])
              for p in review["people"] for r in p["roles"] if p["id"] not in suppressed}
    for r in dedupe(review["unlinked_roles"]):
        if (r["facility_license"], (r["name"] or "").lower(), r["start"], r["end"]) in linked:
            continue
        facilities[r["facility_license"]]["administrators"].append({
            "person_id": None, "name": r["name"], "license_number": None,
            "start": r["start"], "end": r["end"], "open": bool(r["open"])})
    for f in facilities.values():
        f["administrators"].sort(key=lambda a: (a["start"] or a["end"] or ""), reverse=True)

    matched_ccns = {f["ccn"] for f in facilities.values() if f["ccn"]}
    not_covered = [{"ccn": f["ccn"], "name": f.get("provider_name") or f.get("pbj_provider_name")}
                   for f in staffing["facilities"]
                   if f["ccn"] not in matched_ccns and (f.get("address") or "").strip()]

    srcs = {s["id"]: s for s in review["sources"]}
    return {
        "schema_version": SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_as_of": as_of,
        "sources": [
            {"title": "Connecticut DPH nursing home management history (eLicense roster export)",
             "as_of": as_of, "note": "Administrator of record by facility license, 1997 onward."},
            {"title": "Connecticut DPH chronic and convalescent nursing home roster (eLicense export)",
             "as_of": as_of, "note": "Facility license numbers and names."},
            {"title": "State Licenses and Credentials, data.ct.gov (ngch-56tr), Nursing Home Administrator",
             "as_of": srcs.get("ct_open_data_ngch_56tr", {}).get("as_of", as_of)[:10],
             "url": "https://data.ct.gov/Business/State-Licenses-and-Credentials/ngch-56tr",
             "note": "License status, issue and expiration dates."},
            {"title": "CMS Payroll-Based Journal staffing history (Q4 2017 onward)",
             "as_of": history.get("history_window", {}).get("latest_quarter"),
             "note": "Facility staffing during each tenure, through the CCN match."},
        ],
        "caveats": CAVEATS,
        "corrections_notice": CORRECTIONS_NOTICE,
        "corrections_applied": len(corrections),
        "coverage": {
            "facilities": len(facilities),
            "facilities_with_ccn": len(matched_ccns),
            "cms_homes_not_in_dph_export": sorted(not_covered, key=lambda x: x["name"] or ""),
        },
        "summary": {
            "people": len(people),
            "roles": sum(len(p["roles"]) for p in people),
            "unlinked_roles": sum(1 for f in facilities.values() for a in f["administrators"]
                                  if a["person_id"] is None),
            "earliest_role_date": review["summary"]["earliest_role_date"],
            "latest_role_date": review["summary"]["latest_role_date"],
        },
        "people": people,
        "facilities": sorted(facilities.values(), key=lambda f: f["facility_name"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    ap.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    ap.add_argument("--corrections", type=Path, default=DEFAULT_CORRECTIONS)
    ap.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    ap.add_argument("--staffing", type=Path, default=DEFAULT_STAFFING)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    review = json.loads(args.review.read_text(encoding="utf-8"))
    corrections = (json.loads(args.corrections.read_text(encoding="utf-8"))
                   if args.corrections.exists() else [])
    result = build(review, load_decisions(args.decisions),
                   json.loads(args.history.read_text(encoding="utf-8")),
                   json.loads(args.staffing.read_text(encoding="utf-8")), corrections)
    args.out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                        newline="\n")
    s = result["summary"]
    print(f"Wrote {args.out.relative_to(ROOT)}: {s['people']} people, {s['roles']} roles, "
          f"{s['unlinked_roles']} unlinked roles, {result['coverage']['facilities_with_ccn']} facilities with CCN")


if __name__ == "__main__":
    main()
