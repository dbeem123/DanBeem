"""Validate the public Connecticut nursing home management company data."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import validate_ct_administrators as admin_val

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CCN = re.compile(r"^07\d{4}$")
TOP = {"schema_version", "generated_at", "source_as_of", "window", "sources", "caveats", "corrections_notice",
       "summary", "companies", "facilities"}
COMPANY = {"id", "name", "other_names", "dph_license", "homes_total", "homes_current", "homes"}
# Same private-field rule as the administrator data, except "homes" here means nursing homes.
FORBIDDEN_KEYS = re.compile(r"(?i)^(address\d?|street|city|state|zip(code)?|postal|phone|email|"
                            r"salary|compensation|wage|dob|birth.*|home_?address|residence.*|ssn)$")
HOME = {"ccn", "facility_name", "role", "start", "start_basis", "later_association_dates", "end", "ended_before",
        "current", "context", "administrators"}


def problems(data: dict, admin_ids: set[str] | None = None) -> list[str]:
    found: list[str] = []
    if data.get("schema_version") != "ct-nursing-home-management-companies-1.0":
        found.append("unexpected schema_version")
    if set(data) != TOP:
        return found + [f"top-level keys differ: {sorted(set(data) ^ TOP)}"]
    for path, key, text in admin_val.walk(data):
        if key is not None and FORBIDDEN_KEYS.match(key):
            found.append(f"forbidden field {key!r} at {path}")
        if text is not None:
            for label, pattern in admin_val.PRIVATE_VALUES:
                if pattern.search(text):
                    found.append(f"{label} pattern in {path}: {text[:60]!r}")
    if not any("not a measure of the management company's performance" in c for c in data["caveats"]):
        found.append("performance caveat missing")
    if not any("not the same as ownership" in c for c in data["caveats"]):
        found.append("control-is-not-ownership caveat missing")
    latest = data["window"]["latest_release"]
    ids = set()
    for c in data["companies"]:
        if set(c) != COMPANY:
            found.append(f"{c.get('id')}: company keys differ")
            continue
        if c["id"] in ids:
            found.append(f"duplicate company id {c['id']}")
        ids.add(c["id"])
        if c["homes_total"] != len({h["ccn"] for h in c["homes"]}) or \
                c["homes_current"] != len({h["ccn"] for h in c["homes"] if h["current"]}):
            found.append(f"{c['id']}: home counts do not match")
        for h in c["homes"]:
            if set(h) != HOME:
                found.append(f"{c['id']}: home keys differ")
                continue
            if not CCN.match(h["ccn"]):
                found.append(f"{c['id']}: bad CCN {h['ccn']}")
            for field in ("start", "end", "ended_before"):
                if h[field] and not ISO.match(h[field]):
                    found.append(f"{c['id']} {h['ccn']}: {field} not ISO")
            if h["current"] != (h["end"] is None):
                found.append(f"{c['id']} {h['ccn']}: current flag and end disagree")
            if h["end"] and h["end"] > latest:
                found.append(f"{c['id']} {h['ccn']}: end after latest release")
            for a in h["administrators"]:
                if admin_ids is not None and a["person_id"] and a["person_id"] not in admin_ids:
                    found.append(f"{c['id']} {h['ccn']}: unknown administrator {a['person_id']}")
    fac_ids = {m["company_id"] for f in data["facilities"] for m in f["management"]}
    if fac_ids - ids:
        found.append(f"facility list names unknown companies: {sorted(fac_ids - ids)[:5]}")
    s = data["summary"]
    if s["companies"] != len(data["companies"]) or \
            s["periods"] != sum(len(c["homes"]) for c in data["companies"]):
        found.append("summary counts do not match")
    return found


def main() -> int:
    data = json.loads((DATA / "ct_nursing_home_management_companies.json").read_text(encoding="utf-8"))
    admins = json.loads((DATA / "ct_nursing_home_administrators.json").read_text(encoding="utf-8"))
    found = problems(data, {p["id"] for p in admins["people"]})
    if found:
        print("Management company data validation failed:")
        for p in found[:50]:
            print(" -", p)
        return 1
    s = data["summary"]
    print(f"Management companies OK: {s['companies']} companies, {s['homes']} homes, {s['periods']} periods "
          f"({s['current_periods']} current), {data['window']['releases']} CMS releases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
