"""Validate data/ct_ltcop_legislative_tracker.json before publishing.

Checks: allowed statuses and topics, unique ids, related-bill ids exist, ISO dates, https
links, stat keys exist in data/ct_legislative_research_stats.json, and that every real
bill in the current session has a bill status link and a dated last action.
Exit code 1 with a list of problems if anything fails.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "data" / "ct_ltcop_legislative_tracker.json"
STATS = ROOT / "data" / "ct_legislative_research_stats.json"
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BILL = re.compile(r"^(SB|HB) \d{1,4}$")


def problems(tracker: dict, stats: dict) -> list[str]:
    out: list[str] = []
    statuses = {s["id"] for s in tracker["statuses"]}
    topics = {t["id"] for t in tracker["topics"]}
    stat_keys = {s["key"] for s in stats["stats"]}
    ids: set[str] = set()

    def url_ok(where: str, url: str | None) -> None:
        if url and not (url.startswith("https://") or url.startswith("/")):
            out.append(f"{where}: link must be https or site-relative: {url}")

    for key in ("convenes", "adjourns"):
        if not ISO.match(tracker["session"][key]):
            out.append(f"session.{key} is not YYYY-MM-DD")
    if not ISO.match(tracker.get("last_updated", "")):
        out.append("last_updated is not YYYY-MM-DD")

    for group in ("bills_current", "bills_past"):
        for b in tracker[group]:
            where = f"{group}:{b.get('id')}"
            if not b.get("id"):
                out.append(f"{group}: entry without id")
            elif b["id"] in ids:
                out.append(f"{where}: duplicate id")
            ids.add(b.get("id"))
            for t in b.get("topics", []):
                if t not in topics:
                    out.append(f"{where}: unknown topic {t}")
            if not b.get("topics"):
                out.append(f"{where}: needs at least one topic")
            if b.get("bill") and not BILL.match(b["bill"]):
                out.append(f"{where}: bill must look like 'SB 123' or 'HB 5142'")
            for k in b.get("key_dates", []) or []:
                if not ISO.match(k.get("date", "")):
                    out.append(f"{where}: key date {k.get('date')} is not YYYY-MM-DD")
            url_ok(where, b.get("bill_status_url"))
            for s in b.get("sources", []) or []:
                url_ok(where, s.get("url"))
            if group == "bills_current":
                if b.get("status") not in statuses:
                    out.append(f"{where}: unknown status {b.get('status')}")
                if b.get("bill"):
                    if not b.get("bill_status_url"):
                        out.append(f"{where}: real bill needs bill_status_url")
                    if not ISO.match(b.get("last_action_date", "") or ""):
                        out.append(f"{where}: real bill needs last_action_date YYYY-MM-DD")
                elif b.get("status") != "watch":
                    out.append(f"{where}: an entry without a bill number must have status 'watch'")
            else:
                if not isinstance(b.get("enacted"), bool):
                    out.append(f"{where}: past bill needs enacted true/false")
                if b.get("enacted") and not b.get("public_act"):
                    out.append(f"{where}: enacted bill needs public_act")

    for group in ("bills_current", "bills_past"):
        for b in tracker[group]:
            for rel in b.get("related", []) or []:
                if rel not in ids:
                    out.append(f"{group}:{b['id']}: related id {rel} not found")

    for t in tracker["topics"]:
        for k in t.get("stat_keys", []):
            if k not in stat_keys:
                out.append(f"topic {t['id']}: stat key {k} not in research stats")
        for f in t.get("context_facts", []):
            url_ok(f"topic {t['id']}", f.get("source_url"))
            if not f.get("source_url"):
                out.append(f"topic {t['id']}: context fact needs a source_url")
    for d in tracker.get("deadlines", []):
        if not ISO.match(d.get("date", "")):
            out.append(f"deadline {d.get('what')}: date not YYYY-MM-DD")
        url_ok("deadline", d.get("source_url"))
    return out


def main() -> int:
    tracker = json.loads(TRACKER.read_text(encoding="utf-8"))
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    found = problems(tracker, stats)
    if found:
        print("Tracker validation failed:")
        for p in found:
            print(" -", p)
        return 1
    print(f"Tracker OK: {len(tracker['bills_current'])} current entries, {len(tracker['bills_past'])} past bills, "
          f"{len(tracker['topics'])} topics, {len(tracker['deadlines'])} deadlines.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
