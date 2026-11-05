"""Validate the public CT nursing home administrator search data.

Checks the schema, that no private field or value is present, ISO dates, unique ids,
facility and CCN integrity, the required caveats, and the display rules.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORBIDDEN_KEYS = re.compile(r"(?i)^(address\d?|street|city|state|zip(code)?|postal|phone|email|"
                            r"salary|compensation|wage|dob|birth.*|home.*|residence.*|ssn)$")
PRIVATE_VALUES = [
    ("ZIP code", re.compile(r"\b0[6-9]\d{3}(?:-\d{4})?\b")),
    ("email", re.compile(r"[\w.+-]+@(?!danbeem\.xyz)[\w-]+\.\w+")),
    ("phone", re.compile(r"\(?\b\d{3}\)?[ .-]\d{3}-\d{4}\b")),
    ("street address", re.compile(r"\b\d{1,5} [A-Za-z]+(?: [A-Za-z]+)? (?:St|Street|Rd|Road|Ave|Avenue|"
                                  r"Dr|Drive|Ln|Lane|Blvd|Way|Ct|Court|Tpke|Turnpike)\b", re.I)),
]
REQUIRED_CAVEAT = "not a measure of the administrator's performance"
TOP_KEYS = {"schema_version", "generated_at", "source_as_of", "sources", "caveats",
            "corrections_notice", "corrections_applied", "coverage", "summary", "people", "facilities"}
PERSON_KEYS = {"id", "name", "other_names", "license_number", "license_status", "license_status_as_of",
               "license_issued", "license_expires", "roles"}
ROLE_KEYS = {"id", "facility_license", "facility_name", "ccn", "start", "end", "open", "overlap", "context"}
ADMIN_KEYS = {"person_id", "name", "license_number", "start", "end", "open"}


def walk(value, path="$"):
    if isinstance(value, dict):
        for k, v in value.items():
            yield path, k, None
            yield from walk(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(value, str):
        yield path, None, value


def problems(data: dict, known_ccns: set[str] | None = None) -> list[str]:
    found: list[str] = []
    if data.get("schema_version") != "ct-nursing-home-administrators-1.0":
        found.append("unexpected schema_version")
    if set(data) != TOP_KEYS:
        found.append(f"top-level keys differ: {sorted(set(data) ^ TOP_KEYS)}")
        return found
    for path, key, text in walk(data):
        if key is not None and FORBIDDEN_KEYS.match(key):
            found.append(f"forbidden field {key!r} at {path}")
        if text is not None:
            for label, pattern in PRIVATE_VALUES:
                if pattern.search(text):
                    found.append(f"{label} pattern in {path}: {text[:60]!r}")
    if not any(REQUIRED_CAVEAT in c for c in data["caveats"]):
        found.append("performance caveat missing")
    if "hello@danbeem.xyz" not in data["corrections_notice"]:
        found.append("corrections notice missing contact")

    facilities = {f["facility_license"]: f for f in data["facilities"]}
    ccns = [f["ccn"] for f in data["facilities"] if f["ccn"]]
    if len(ccns) != len(set(ccns)):
        found.append("a CCN is assigned to more than one facility license")
    if known_ccns is not None:
        found += [f"CCN {c} not in the CMS staffing data" for c in ccns if c not in known_ccns]

    ids = set()
    for p in data["people"]:
        if set(p) != PERSON_KEYS:
            found.append(f"{p.get('id')}: person keys differ")
            continue
        if p["id"] in ids:
            found.append(f"duplicate person id {p['id']}")
        ids.add(p["id"])
        if not p["license_number"] or p["id"] != f"nha-{p['license_number']}":
            found.append(f"{p['id']}: person without a matching license number")
        if p["license_issued"] == "1901-01-01":
            found.append(f"{p['id']}: placeholder issue date published")
        for field in ("license_issued", "license_expires", "license_status_as_of"):
            if p[field] and not ISO.match(p[field]):
                found.append(f"{p['id']}: {field} not ISO")
        role_ids = set()
        for r in p["roles"]:
            if set(r) != ROLE_KEYS:
                found.append(f"{p['id']}: role keys differ")
                continue
            if r["id"] in role_ids:
                found.append(f"{p['id']}: duplicate role {r['id']}")
            role_ids.add(r["id"])
            for field in ("start", "end"):
                if r[field] and not ISO.match(r[field]):
                    found.append(f"{r['id']}: {field} not ISO")
            if r["start"] and r["end"] and r["end"] < r["start"]:
                found.append(f"{r['id']}: end before start")
            f = facilities.get(r["facility_license"])
            if not f:
                found.append(f"{r['id']}: unknown facility {r['facility_license']}")
            elif r["ccn"] != f["ccn"]:
                found.append(f"{r['id']}: CCN differs from its facility")
            ctx = r["context"]
            if ctx is not None and ctx.get("quarters", 0) and not r["ccn"]:
                found.append(f"{r['id']}: staffing context without a CCN")
        if not any(a["person_id"] == p["id"] for f in data["facilities"] for a in f["administrators"]):
            found.append(f"{p['id']}: not listed under any facility")
    for f in data["facilities"]:
        for a in f["administrators"]:
            if set(a) != ADMIN_KEYS:
                found.append(f"{f['facility_license']}: administrator keys differ")
            elif a["person_id"] and a["person_id"] not in ids:
                found.append(f"{f['facility_license']}: unknown person {a['person_id']}")
            elif not a["person_id"] and a["license_number"]:
                found.append(f"{f['facility_license']}: unlinked entry carries a license number")
    s = data["summary"]
    if s["people"] != len(data["people"]) or s["roles"] != sum(len(p["roles"]) for p in data["people"]):
        found.append("summary counts do not match")
    return found


def main() -> int:
    data = json.loads((DATA / "ct_nursing_home_administrators.json").read_text(encoding="utf-8"))
    staffing = json.loads((DATA / "nursing_home_staffing_ct.json").read_text(encoding="utf-8"))
    found = problems(data, {f["ccn"] for f in staffing["facilities"]})
    if found:
        print("Administrator data validation failed:")
        for p in found[:50]:
            print(" -", p)
        return 1
    s = data["summary"]
    print(f"Administrators OK: {s['people']} people, {s['roles']} roles, {s['unlinked_roles']} unlinked roles, "
          f"{data['coverage']['facilities_with_ccn']} of {data['coverage']['facilities']} facilities with CCN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
