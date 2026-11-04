"""Validate the legislative storylines, the act reference list and the topic backgrounds.

Files checked:
  data/ct_ltcop_legislative_threads.json   storylines (threads)
  data/ct_ltcop_act_reference.json         every long-term care act, 2021-2026
  data/ct_ltcop_legislative_tracker.json   topic background entries (pre-2021)
  data/ct_ltcop_positions.json             approved Program positions (normally empty)

Exit code 1 with a list of problems if anything fails.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ACT_ID = re.compile(r"^20\d\d-(hb|sb)\d{1,4}$")
ACT_NO = re.compile(r"^(PA|SA) \d{2}-\d{1,3}( \(June Special Session\))?$")
NON_POSITION = "Listing is not a position of the Long Term Care Ombudsman Program."
LIMITS = {"summary": 60, "label": 12, "what": 30, "act_summary": 30, "background": 40, "position": 80, "comparison": 40}


def words(text: str) -> int:
    return len((text or "").split())


def https(url: object) -> bool:
    return isinstance(url, str) and url.startswith("https://")


def act_problems(acts: dict, topics: set[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for a in acts.get("acts", []):
        where = f"act {a.get('id')}"
        if not ACT_ID.match(a.get("id", "")):
            out.append(f"{where}: id must look like 2021-sb1030")
        if a.get("id") in seen:
            out.append(f"{where}: duplicate id")
        seen.add(a.get("id"))
        if not ACT_NO.match(a.get("public_act", "")):
            out.append(f"{where}: public_act must look like 'PA 21-185' or 'SA 22-12'")
        if not isinstance(a.get("session"), int) or not 2021 <= a["session"] <= 2026:
            out.append(f"{where}: session must be 2021-2026")
        elif not a.get("id", "").startswith(str(a["session"])):
            out.append(f"{where}: id does not match session")
        if not a.get("title") or not a.get("summary"):
            out.append(f"{where}: needs title and summary")
        if words(a.get("summary", "")) > LIMITS["act_summary"]:
            out.append(f"{where}: summary over {LIMITS['act_summary']} words")
        if not a.get("topics"):
            out.append(f"{where}: needs at least one topic")
        for t in a.get("topics", []):
            if t not in topics:
                out.append(f"{where}: unknown topic {t}")
        url = a.get("source_url", "")
        if not (https(url) and "cga.ct.gov" in url):
            out.append(f"{where}: source_url must be a cga.ct.gov https link to the act or OLR summary")
    return out


def background_problems(tracker: dict) -> list[str]:
    out: list[str] = []
    for t in tracker["topics"]:
        entries = t.get("background")
        if entries is None:
            out.append(f"topic {t['id']}: missing background")
            continue
        if not 2 <= len(entries) <= 6:
            out.append(f"topic {t['id']}: background needs 2 to 6 entries")
        years = [b.get("year") for b in entries]
        if years != sorted(years):
            out.append(f"topic {t['id']}: background entries out of year order")
        for b in entries:
            where = f"topic {t['id']} background {b.get('year')}"
            if not isinstance(b.get("year"), int) or b["year"] >= 2021:
                out.append(f"{where}: year must be an integer before 2021")
            if not b.get("label") or not b.get("summary"):
                out.append(f"{where}: needs label and summary")
            if words(b.get("summary", "")) > LIMITS["background"]:
                out.append(f"{where}: summary over {LIMITS['background']} words")
            if not https(b.get("source_url")):
                out.append(f"{where}: needs an https source_url")
    return out


def thread_problems(threads: dict, topics: set[str], refs: set[str], watch_ids: set[str]) -> list[str]:
    out: list[str] = []
    kinds = set(threads.get("kinds", []))
    statuses = set(threads.get("statuses", []))
    series = set((threads.get("data_series") or {}).keys())
    if threads.get("schema_version") != "ct-ltcop-threads-1.0":
        out.append("threads: unexpected schema_version")
    if not ISO.match(threads.get("last_updated", "")):
        out.append("threads: last_updated is not YYYY-MM-DD")
    seen: set[str] = set()
    for th in threads.get("threads", []):
        tid = th.get("id", "")
        where = f"thread {tid}"
        if not ID.match(tid):
            out.append(f"{where}: id must be lowercase words joined by hyphens")
        if tid in seen:
            out.append(f"{where}: duplicate id")
        seen.add(tid)
        for key in ("title", "question", "summary"):
            if not th.get(key):
                out.append(f"{where}: needs {key}")
        if words(th.get("summary", "")) > LIMITS["summary"]:
            out.append(f"{where}: summary over {LIMITS['summary']} words")
        if th.get("status") not in statuses:
            out.append(f"{where}: unknown status {th.get('status')}")
        if not th.get("topics"):
            out.append(f"{where}: needs at least one topic")
        for t in th.get("topics", []):
            if t not in topics:
                out.append(f"{where}: unknown topic {t}")
        if th.get("data_series") is not None and th["data_series"] not in series:
            out.append(f"{where}: unknown data_series {th['data_series']}")
        for w in th.get("watch", []):
            if w not in watch_ids:
                out.append(f"{where}: watch id {w} not in bills_current")
        events = th.get("events", [])
        if len(events) < 2:
            out.append(f"{where}: needs at least two events")
        dates = [e.get("date", "") for e in events]
        if dates != sorted(dates):
            out.append(f"{where}: events are not in date order")
        for i, e in enumerate(events):
            ew = f"{where} event {i + 1} ({e.get('date')})"
            if not ISO.match(e.get("date", "")):
                out.append(f"{ew}: date is not YYYY-MM-DD")
            if e.get("kind") not in kinds:
                out.append(f"{ew}: unknown kind {e.get('kind')}")
            ref = e.get("ref")
            if ref is not None and ref not in refs:
                out.append(f"{ew}: ref {ref} not found in any bill or act file")
            if not https(e.get("source_url")):
                out.append(f"{ew}: needs an https source_url")
            if not e.get("label") or words(e["label"]) > LIMITS["label"]:
                out.append(f"{ew}: label missing or over {LIMITS['label']} words")
            if not e.get("what") or words(e["what"]) > LIMITS["what"]:
                out.append(f"{ew}: what missing or over {LIMITS['what']} words")
        for q in th.get("open_questions", []):
            if not isinstance(q, str) or not q.strip():
                out.append(f"{where}: empty open question")
    if NON_POSITION not in threads.get("disclaimer", ""):
        out.append("threads: disclaimer must include the non-position line")
    return out


def comparison_problems(threads: dict, topics: set[str]) -> list[str]:
    out: list[str] = []
    thread_ids = {t["id"] for t in threads.get("threads", [])}
    seen: set[str] = set()
    for c in threads.get("comparisons", []):
        where = f"comparison {c.get('id')}"
        if not c.get("id") or c["id"] in seen:
            out.append(f"{where}: missing or duplicate id")
        seen.add(c.get("id"))
        if c.get("topic") not in topics:
            out.append(f"{where}: unknown topic {c.get('topic')}")
        if not c.get("title") or not c.get("rows"):
            out.append(f"{where}: needs title and rows")
        for i, r in enumerate(c.get("rows", [])):
            rw = f"{where} row {i + 1}"
            if r.get("thread") not in thread_ids:
                out.append(f"{rw}: unknown thread {r.get('thread')}")
            for key in ("approach", "how", "proposals", "outcome", "now"):
                if not r.get(key):
                    out.append(f"{rw}: needs {key}")
                elif words(r[key]) > LIMITS["comparison"]:
                    out.append(f"{rw}: {key} over {LIMITS['comparison']} words")
            if not https(r.get("now_source")):
                out.append(f"{rw}: needs an https now_source")
            if not r.get("reasons"):
                out.append(f"{rw}: needs at least one sourced reason")
            for reason in r.get("reasons", []) + ([r["elsewhere"]] if r.get("elsewhere") else []):
                if not reason.get("text") or words(reason["text"]) > LIMITS["comparison"]:
                    out.append(f"{rw}: reason text missing or over {LIMITS['comparison']} words")
                if not https(reason.get("source_url")):
                    out.append(f"{rw}: reason needs an https source_url")
    return out


def position_problems(positions: dict, topics: set[str], thread_ids: set[str]) -> list[str]:
    out: list[str] = []
    if positions.get("schema_version") != "ct-ltcop-positions-1.0":
        out.append("positions: unexpected schema_version")
    if positions.get("approval_required") is not True:
        out.append("positions: approval_required must be true")

    def has_draft(node: object) -> bool:
        if isinstance(node, dict):
            return any(k.lower().startswith("draft") or has_draft(v) for k, v in node.items())
        if isinstance(node, list):
            return any(has_draft(v) for v in node)
        return False

    if has_draft(positions):
        out.append("positions: draft keys are not allowed in the public repo")
    seen: set[str] = set()
    for p in positions.get("positions", []):
        where = f"position {p.get('id')}"
        if not p.get("id") or p["id"] in seen:
            out.append(f"{where}: missing or duplicate id")
        seen.add(p.get("id"))
        if p.get("topic") not in topics:
            out.append(f"{where}: unknown topic {p.get('topic')}")
        for th in p.get("threads", []) or []:
            if th not in thread_ids:
                out.append(f"{where}: unknown thread {th}")
        if not p.get("text") or words(p["text"]) > LIMITS["position"]:
            out.append(f"{where}: text missing or over {LIMITS['position']} words")
        for key in ("approved_by", "approved_date", "basis_url", "basis_label"):
            if not p.get(key):
                out.append(f"{where}: needs {key}")
        if p.get("approved_date") and not ISO.match(p["approved_date"]):
            out.append(f"{where}: approved_date is not YYYY-MM-DD")
        if p.get("basis_url") and not https(p["basis_url"]):
            out.append(f"{where}: basis_url must be https")
    return out


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def all_refs(tracker: dict, acts: dict) -> set[str]:
    refs = {b["id"] for b in tracker["bills_past"]} | {b["id"] for b in tracker["bills_current"]}
    refs |= {a["id"] for a in acts.get("acts", [])}
    for name in ("ct_ltcop_bill_tracker_2026.json", "ct_ltcop_bill_tracker_2027.json"):
        path = DATA / name
        if path.exists():
            refs |= {b["id"] for b in load(name).get("bills", [])}
    return refs


def main() -> int:
    tracker = load("ct_ltcop_legislative_tracker.json")
    acts = load("ct_ltcop_act_reference.json")
    threads = load("ct_ltcop_legislative_threads.json")
    positions = load("ct_ltcop_positions.json")
    topics = {t["id"] for t in tracker["topics"]}
    watch_ids = {b["id"] for b in tracker["bills_current"]}
    found = act_problems(acts, topics) + background_problems(tracker)
    found += thread_problems(threads, topics, all_refs(tracker, acts), watch_ids)
    found += comparison_problems(threads, topics)
    found += position_problems(positions, topics, {t["id"] for t in threads["threads"]})
    if found:
        print("Threads validation failed:")
        for p in found:
            print(" -", p)
        return 1
    n_events = sum(len(t["events"]) for t in threads["threads"])
    n_bg = sum(len(t["background"]) for t in tracker["topics"])
    print(f"Threads OK: {len(threads['threads'])} storylines, {n_events} events, {len(threads.get('comparisons', []))} comparison, {len(acts['acts'])} acts, "
          f"{n_bg} background entries, {len(positions['positions'])} approved positions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
