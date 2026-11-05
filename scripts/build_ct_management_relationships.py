"""Turn monthly Connecticut organization ownership rows into management periods.

Usage: python scripts/build_ct_management_relationships.py <dir with ct_org_ownership_*.csv> <out.json>

A management relationship is an organization listed with OPERATIONAL/MANAGERIAL CONTROL or as a
CONTRACTED MANAGING EMPLOYEE at a home (CCN). Its presence across releases forms periods; a gap of up
to GAP missing releases is treated as a reporting gap, not an ended relationship. Association dates
are kept per period. The output is private input for scripts/build_ct_management_companies.py.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROLES = {"OPERATIONAL/MANAGERIAL CONTROL", "CONTRACTED MANAGING EMPLOYEE"}
GAP = 2
ASSOC = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def norm(name: str) -> str:
    return " ".join(re.sub(r"[.,]", " ", (name or "").upper()).split())


def build(release_rows: dict[str, list[dict]]) -> dict:
    releases = sorted(release_rows)
    idx = {r: i for i, r in enumerate(releases)}
    present: dict[tuple, set] = defaultdict(set)
    assoc: dict[tuple, set] = defaultdict(set)
    roles: dict[tuple, set] = defaultdict(set)
    variants: dict[str, Counter] = defaultdict(Counter)
    provider: dict[str, str] = {}
    for release in releases:
        for row in release_rows[release]:
            role = (row["role"] or "").upper()
            if role not in ROLES:
                continue
            key = (row["ccn"].zfill(6), norm(row["owner_name"]))
            present[key].add(idx[release])
            roles[key].add(role)
            variants[key[1]][row["owner_name"]] += 1
            provider[key[0]] = row["provider_name"]
            m = ASSOC.search(row.get("association") or "")
            if m:
                assoc[(key, idx[release])].add(f"{m.group(3)}-{m.group(1)}-{m.group(2)}")
    relationships = []
    for key, seen in present.items():
        seen = sorted(seen)
        spans = [[seen[0], seen[0]]]
        for i in seen[1:]:
            if i - spans[-1][1] <= GAP + 1:
                spans[-1][1] = i
            else:
                spans.append([i, i])
        for a, b in spans:
            relationships.append({
                "ccn": key[0], "org": key[1],
                "first_seen": releases[a], "last_seen": releases[b],
                "ended_by": releases[b + 1] if b + 1 < len(releases) else None,
                "current": b == len(releases) - 1, "releases": b - a + 1,
                "association_dates": sorted({d for i in range(a, b + 1) for d in assoc.get((key, i), ())}),
                "roles": sorted(roles[key]),
            })
    relationships.sort(key=lambda r: (r["org"], r["ccn"], r["first_seen"]))
    return {"releases": releases, "relationships": relationships,
            "name_variants": {k: dict(v) for k, v in variants.items()}, "provider_names": provider}


def main(src: Path, out: Path) -> None:
    rows = {}
    for path in sorted(src.glob("ct_org_ownership_*.csv")):
        release = re.search(r"(\d{4}-\d{2}-\d{2})", path.name).group(1)
        with path.open(newline="") as handle:
            rows[release] = list(csv.DictReader(handle))
    result = build(rows)
    out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    r = result["relationships"]
    print(f"{len(result['releases'])} releases, {len(r)} periods, {len({x['org'] for x in r})} organizations, "
          f"{len({x['ccn'] for x in r})} homes")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
