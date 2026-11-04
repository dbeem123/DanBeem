"""Weekly report helper for a session bill tracker (data/ct_ltcop_bill_tracker_<year>.json).

Prints Markdown with:
  1. What changed since the previous report: new bills, status moves, new public acts.
  2. Counts by status.
  3. A checklist of every bill still in progress, with its status page link and the
     days since its last recorded action, so the weekly CGA check goes quickly.
  4. Untagged bills: bills with no `topics` or in no storyline (once bills carry topics).
  5. Moves by storyline: this week's status changes grouped by storyline
     (data/ct_ltcop_legislative_threads.json; storylines point to bills, not the reverse).

Usage:
  python scripts/ct_session_weekly_report.py 2027
  python scripts/ct_session_weekly_report.py 2027 --since HEAD~1        (compare to a git version)
  python scripts/ct_session_weekly_report.py 2027 --since old_copy.json (compare to a saved file)
  python scripts/ct_session_weekly_report.py 2027 --out report.md

Without --since, the comparison is against the last committed version (HEAD).
The output is a working draft for the person updating the tracker, not a public page.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL_STATUSES = {"signed", "vetoed", "hearing_only", "no_action"}


def data_path(year: int | str) -> Path:
    return ROOT / "data" / f"ct_ltcop_bill_tracker_{year}.json"


def load_previous(year: int | str, since: str | None) -> dict | None:
    if since and Path(since).is_file():
        return json.loads(Path(since).read_text(encoding="utf-8"))
    ref = since or "HEAD"
    rel = data_path(year).relative_to(ROOT).as_posix()
    try:
        raw = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return json.loads(raw.decode("utf-8"))


THREADS = ROOT / "data" / "ct_ltcop_legislative_threads.json"


def load_threads() -> dict | None:
    try:
        return json.loads(THREADS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def threads_by_bill(threads: dict | None) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for th in (threads or {}).get("threads", []):
        ids = {e.get("ref") for e in th.get("events", []) if e.get("ref")} | set(th.get("watch", []))
        for i in ids:
            out.setdefault(i, []).append(th)
    return out


def iso(d: str | None) -> date | None:
    return date.fromisoformat(d) if d else None


def changes(prev: dict | None, cur: dict) -> dict:
    before = {b["id"]: b for b in (prev or {}).get("bills", [])}
    added, moved, new_acts = [], [], []
    for b in cur["bills"]:
        old = before.get(b["id"])
        if old is None:
            added.append(b)
            continue
        if old.get("status") != b.get("status"):
            moved.append((b, old.get("status")))
        if b.get("public_act") and not old.get("public_act"):
            new_acts.append(b)
    removed = [b for i, b in before.items() if i not in {x["id"] for x in cur["bills"]}]
    return {"added": added, "moved": moved, "new_acts": new_acts, "removed": removed}


def render(cur: dict, prev: dict | None, stale_days: int = 14, threads: dict | None = None) -> str:
    labels = {s["id"]: s["label"] for s in cur["statuses"]}
    stage = {s["id"]: s.get("stage", -1) for s in cur["statuses"]}
    lab = lambda sid: labels.get(sid, sid or "none")  # noqa: E731
    s, r = cur["session"], cur["report"]
    as_of = iso(r.get("status_as_of")) or date.today()
    out = [f"# {s['year']} LTCOP bill tracker: weekly report draft",
           "",
           f"Report: {r.get('label')} · statuses as of {as_of.isoformat()} · {len(cur['bills'])} bills tracked.",
           ""]

    ch = changes(prev, cur)
    out.append("## Changes since the previous report")
    if prev is None:
        out.append("No previous version found to compare against.")
    elif not any(ch.values()):
        out.append("No changes.")
    for b in ch["added"]:
        out.append(f"- **New:** {b['bill']} ({lab(b['status'])}): {b['summary']}")
    for b, old in sorted(ch["moved"], key=lambda x: -stage.get(x[0]["status"], -1)):
        out.append(f"- **Moved:** {b['bill']}: {lab(old)} → {lab(b['status'])} ({b.get('latest_action', '')}, {b.get('latest_action_date', '')})")
    for b in ch["new_acts"]:
        out.append(f"- **Became law:** {b['bill']} is {b['public_act']}")
    for b in ch["removed"]:
        out.append(f"- **Removed from the list:** {b['bill']}")
    out.append("")

    out.append("## Counts by status")
    counts: dict[str, int] = {}
    for b in cur["bills"]:
        counts[b["status"]] = counts.get(b["status"], 0) + 1
    for st in cur["statuses"]:
        if counts.get(st["id"]):
            out.append(f"- {st['label']}: {counts[st['id']]}")
    if not counts:
        out.append("- No bills yet.")
    out.append("")

    final = r.get("final") is True or "final" in (r.get("label") or "").lower()
    open_bills = [] if final else [b for b in cur["bills"] if b["status"] not in FINAL_STATUSES]
    open_bills.sort(key=lambda b: (iso(b.get("latest_action_date")) or date.min, b["bill"]))
    out.append(f"## Check this week ({len(open_bills)} bills still moving)")
    out.append(f"Oldest recorded action first. ⚠ marks bills with no recorded action in {stale_days}+ days.")
    out.append("")
    if open_bills:
        out.append("| Bill | List | Status | Latest recorded action | Days | Status page |")
        out.append("|---|---|---|---|---|---|")
        for b in open_bills:
            d = iso(b.get("latest_action_date"))
            days = (as_of - d).days if d else None
            flag = " ⚠" if days is not None and days >= stale_days else ""
            action = (b.get("latest_action") or "").replace("|", "/")
            out.append(f"| {b['bill']} | {b['list']} | {lab(b['status'])} | {action} | "
                       f"{'' if days is None else days}{flag} | [link]({b['bill_status_url']}) |")
    else:
        out.append("Final report: the session is over." if final else "Nothing to check.")
    out.append("")

    by_bill = threads_by_bill(threads)
    out.append("## Untagged bills")
    if not any("topics" in b for b in cur["bills"]):
        out.append("No bill carries `topics` yet. Add topic ids to each bill as it is reviewed; this list then shows what still needs tagging." if cur["bills"] else "No bills yet.")
    else:
        no_topic = [b for b in cur["bills"] if not b.get("topics")]
        no_thread = [b for b in cur["bills"] if b.get("topics") and b["id"] not in by_bill]
        if not no_topic and not no_thread:
            out.append("Every bill has topics and belongs to a storyline.")
        for b in no_topic:
            out.append(f"- **No topic:** {b['bill']}: {b['summary']}")
        for b in no_thread:
            out.append(f"- **In no storyline:** {b['bill']} ({', '.join(b['topics'])}): add it to a storyline's events if it belongs to one.")
    out.append("")

    out.append("## Moves by storyline")
    if prev is None or not ch["moved"]:
        out.append("No status changes to group." if prev is not None else "No previous version found to compare against.")
    else:
        groups: dict[str, list[str]] = {}
        for b, old in ch["moved"]:
            line = f"- {b['bill']}: {lab(old)} → {lab(b['status'])}"
            for th in by_bill.get(b["id"], []) or [{"title": "Not in a storyline"}]:
                groups.setdefault(th["title"], []).append(line)
        for title in sorted(groups, key=lambda t: (t == "Not in a storyline", t)):
            out.append(f"### {title}")
            out.extend(groups[title])
    out.append("")
    out.append("Draft for the person updating the tracker. Listing a bill is not an LTCOP position.")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("year")
    ap.add_argument("--since", help="git ref or path to an earlier copy of the data file (default HEAD)")
    ap.add_argument("--out", help="write the Markdown here instead of printing it")
    ap.add_argument("--stale-days", type=int, default=14)
    args = ap.parse_args(argv)
    cur = json.loads(data_path(args.year).read_text(encoding="utf-8"))
    text = render(cur, load_previous(args.year, args.since), args.stale_days, load_threads())
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
