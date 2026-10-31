"""Validate a per-session bill tracker file, e.g. data/ct_ltcop_bill_tracker_2026.json.

Usage: python scripts/validate_ct_session_tracker.py [year ...]   (default: every
data/ct_ltcop_bill_tracker_*.json). Exit code 1 lists every problem found.
Copy the 2026 file's structure for 2027 and keep `bills` updated during the session.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BILL = re.compile(r"^(SB|HB) \d{1,4}$")
ACT = re.compile(r"^(PA|SA) \d{2}-\d{1,3}$")


def problems(data: dict) -> list[str]:
    out: list[str] = []
    year = data["session"]["year"]
    for key in ("convenes", "adjourns"):
        if not ISO.match(data["session"].get(key, "")):
            out.append(f"session.{key} is not YYYY-MM-DD")
    if not ISO.match(data["report"].get("status_as_of", "")):
        out.append("report.status_as_of is not YYYY-MM-DD")
    statuses = {s["id"] for s in data["statuses"]}
    lists = {l["id"] for l in data["lists"]}
    seen: set[str] = set()
    for b in data["bills"]:
        where = b.get("bill", "?")
        if not BILL.match(b.get("bill", "")):
            out.append(f"{where}: bill must look like 'SB 123' or 'HB 5142'")
        if b.get("id") != f"{year}-{b.get('bill', '').replace(' ', '').lower()}":
            out.append(f"{where}: id should be '{year}-{b.get('bill', '').replace(' ', '').lower()}'")
        if b.get("id") in seen:
            out.append(f"{where}: duplicate")
        seen.add(b.get("id"))
        if b.get("list") not in lists:
            out.append(f"{where}: unknown list {b.get('list')}")
        if b.get("status") not in statuses:
            out.append(f"{where}: unknown status {b.get('status')}")
        for field in ("summary", "latest_action", "committee", "bill_status_url"):
            if not b.get(field):
                out.append(f"{where}: missing {field}")
        if b.get("summary") and len(b["summary"].split()) > 35:
            out.append(f"{where}: summary over 35 words")
        if b.get("latest_action_date") and not ISO.match(b["latest_action_date"]):
            out.append(f"{where}: latest_action_date is not YYYY-MM-DD")
        if b.get("status") == "signed" and not ACT.match(b.get("public_act") or ""):
            out.append(f"{where}: signed bill needs public_act like 'PA {str(year)[2:]}-12'")
        if b.get("status") != "signed" and b.get("public_act"):
            out.append(f"{where}: public_act set but status is not signed")
        url = b.get("bill_status_url") or ""
        if not url.startswith("https://") or f"which_year={year}" not in url:
            out.append(f"{where}: bill_status_url should be the {year} CGA status link")
    for x in data.get("also_enacted", []):
        if not ACT.match(x.get("act", "")):
            out.append(f"also_enacted {x.get('bill')}: act must look like 'PA 26-68'")
    return out


def main(argv: list[str]) -> int:
    files = [ROOT / "data" / f"ct_ltcop_bill_tracker_{y}.json" for y in argv] or sorted((ROOT / "data").glob("ct_ltcop_bill_tracker_*.json"))
    failed = False
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        found = problems(data)
        if found:
            failed = True
            print(f"{path.name}: {len(found)} problems")
            for p in found:
                print(" -", p)
        else:
            counts: dict[str, int] = {}
            for b in data["bills"]:
                counts[b["status"]] = counts.get(b["status"], 0) + 1
            print(f"{path.name}: OK, {len(data['bills'])} bills {counts}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
