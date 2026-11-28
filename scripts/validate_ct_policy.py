"""Validate the public policy layer and scan public legislative content (fail closed).

Rules come from data/ct_policy_rules.json. Checks:
- every public file has only known keys (no internal, draft or unknown keys);
- policy ids match the id pattern, are unique and never collide with bill/thread/topic ids;
- every reference (bills, acts, threads, topics, stats, positions, see_also, parent) resolves;
- a public_if_approved field (gaps, coverage, ...) appears only when the file-level `approved`
  map lists it for that policy id (the export fills that map from recorded approvals);
- every quote has an https source on an allowed host and a verified_date; every gap has a basis;
- implementation "overdue_verified" only when deadline < checked_date;
- no email, phone number, Windows path, confidential or do-not-publish marker anywhere in the
  public legislative files or pages (scan).

Run: python scripts/validate_ct_policy.py   (exit 1 on any problem)
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

POLICY_FILE_KEYS = {"schema_version", "exported_at", "source_version", "label", "limitations", "approved", "policies"}
AREA_FILE_KEYS = {"schema_version", "exported_at", "source_version", "limitations", "areas"}
AREA_KEYS = {"id", "title", "summary", "topic_ids", "thread_ids"}
REG_FILE_KEYS = {"schema_version", "last_updated", "limitations", "actions"}
REG_KEYS = {"id", "agency", "title", "stage", "docket", "comment_open", "comment_close", "url", "checked_date", "policy_ids", "summary"}
IMPL_FILE_KEYS = {"schema_version", "last_updated", "limitations", "items"}
IMPL_KEYS = {"id", "act_id", "provision", "agency", "deadline", "status", "evidence_url", "source_url", "checked_date", "policy_ids", "note"}
AUTH_FILE_KEYS = {"schema_version", "last_updated", "limitations", "authorities"}
AUTH_KEYS = {"id", "kind", "citation", "title", "quote", "source_url", "verified_date"}
QUOTE_KEYS = {"authority_id", "citation", "quote", "source_url", "verified_date"}
SOURCE_KEYS = {"label", "url", "as_of", "period", "caveat"}
GAP_KEYS = {"text", "basis_label", "basis_url"}
COVERAGE_KEYS = {"target", "value", "basis_url"}

SCAN_FILES = [
    "ct_policy_public.json", "ct_policy_priority_areas.json", "ct_regulatory_actions.json",
    "ct_implementation.json", "ct_ltc_authorities.json", "ct_ltcop_positions.json",
    "ct_ltcop_legislative_tracker.json", "ct_ltcop_legislative_threads.json",
    "ct_ltcop_bill_tracker_2026.json", "ct_ltcop_bill_tracker_2027.json",
    "ct_ltcop_act_reference.json", "ct_legislative_research_stats.json",
]
SCAN_PAGE_GLOB = "legislation/**/*.html"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def is_iso(value) -> bool:
    try:
        date.fromisoformat(value)
        return isinstance(value, str) and len(value) == 10
    except (TypeError, ValueError):
        return False


class Checker:
    def __init__(self, rules: dict):
        self.rules = rules
        self.out: list[str] = []
        self.patterns = [(p["name"], re.compile(p["regex"])) for p in rules["forbidden_patterns"]]
        self.hosts = set(rules["allowed_source_hosts"])

    def add(self, msg: str) -> None:
        self.out.append(msg)

    def keys(self, where: str, obj, allowed: set) -> bool:
        if not isinstance(obj, dict):
            self.add(f"{where}: must be an object")
            return False
        for k in obj:
            low = k.lower()
            if any(low.startswith(p) for p in self.rules["forbidden_key_prefixes"]):
                self.add(f"{where}: forbidden key {k!r}")
            elif k not in allowed:
                self.add(f"{where}: unknown key {k!r}")
        return True

    def url(self, where: str, value, required: bool = True) -> None:
        if value is None and not required:
            return
        p = urlparse(value) if isinstance(value, str) else None
        if not p or p.scheme != "https" or not p.netloc:
            self.add(f"{where}: needs an https URL")
        elif p.netloc not in self.hosts:
            self.add(f"{where}: source host {p.netloc} is not on the allowed list")

    def text(self, where: str, value, required: bool = True) -> None:
        if not isinstance(value, str) or (required and not value.strip()):
            self.add(f"{where}: needs text")

    def ids(self, where: str, values, known: set, label: str) -> None:
        if not isinstance(values, list):
            self.add(f"{where}: {label} must be a list")
            return
        if len(set(values)) != len(values):
            self.add(f"{where}: duplicate {label}")
        for v in values:
            if v not in known:
                self.add(f"{where}: dangling {label} {v!r}")

    def scan_text(self, where: str, raw: str) -> None:
        allow = self.rules["scan_allowlist"]["strings"]
        for s in allow:
            raw = raw.replace(s, "")
        for name, rx in self.patterns:
            m = rx.search(raw)
            if m:
                self.add(f"{where}: contains {name} ({m.group(0)[:40]!r})")


def references(rules: dict) -> dict:
    tracker = load("ct_ltcop_legislative_tracker.json")
    bills = {b["id"] for b in tracker["bills_current"] + tracker["bills_past"]}
    for year in (2026, 2027):
        f = DATA / f"ct_ltcop_bill_tracker_{year}.json"
        if f.exists():
            bills |= {b["id"] for b in json.loads(f.read_text(encoding="utf-8")).get("bills", [])}
    stats = load("ct_legislative_research_stats.json")["stats"]
    return {
        "bills": bills,
        "acts": {a["id"] for a in load("ct_ltcop_act_reference.json")["acts"]},
        "threads": {t["id"] for t in load("ct_ltcop_legislative_threads.json")["threads"]},
        "topics": {t["id"] for t in tracker["topics"]},
        "stats": {s["key"] for s in stats} if isinstance(stats, list) else set(stats),
        "positions": {p.get("id") for p in load("ct_ltcop_positions.json")["positions"]},
    }


def check_policies(c: Checker, doc: dict, refs: dict, authorities: set) -> set:
    rules = c.rules
    c.keys("ct_policy_public.json", doc, POLICY_FILE_KEYS)
    public = set(rules["policy_fields"]["public"])
    gated = set(rules["policy_fields"]["public_if_approved"])
    approved = doc.get("approved", {}) or {}
    if not isinstance(approved, dict):
        c.add("ct_policy_public.json: approved must map policy id -> approved field list")
        approved = {}
    if doc.get("label") != rules["public_label"]:
        c.add("ct_policy_public.json: label must equal the rules file's public_label")
    pid_re = re.compile(rules["id_pattern"])
    seen: set = set()
    policies = doc.get("policies", [])
    all_ids = {p.get("id") for p in policies if isinstance(p, dict)}
    taken = refs["bills"] | refs["threads"] | refs["topics"] | refs["acts"]
    for i, p in enumerate(policies):
        where = f"policy[{i}] {p.get('id') if isinstance(p, dict) else ''}"
        if not c.keys(where, p, public | gated):
            continue
        for f in rules["required_policy_fields"]:
            if f not in p:
                c.add(f"{where}: missing {f}")
        pid = p.get("id")
        if not isinstance(pid, str) or not pid_re.match(pid):
            c.add(f"{where}: id must match {rules['id_pattern']}")
        if pid in seen:
            c.add(f"{where}: duplicate id")
        if pid in taken:
            c.add(f"{where}: id collides with an existing bill/act/thread/topic id")
        seen.add(pid)
        allowed_gated = set(approved.get(pid, []))
        for f in gated & set(p):
            if f not in allowed_gated:
                c.add(f"{where}: {f} needs approval before it can be public")
        if p.get("status") not in rules["record_statuses"]:
            c.add(f"{where}: invalid status")
        c.text(f"{where} title", p.get("title"))
        c.text(f"{where} question", p.get("question"))
        if not is_iso(p.get("last_verified")):
            c.add(f"{where}: last_verified must be an ISO date")
        for f, allowed in (("population", rules["populations"]), ("pathway", rules["pathways"])):
            for v in p.get(f, []):
                if v not in allowed:
                    c.add(f"{where}: invalid {f} {v!r}")
        if not isinstance(p.get("priority_areas"), list) or not p.get("priority_areas"):
            c.add(f"{where}: needs at least one priority area")
        elif not all(isinstance(v, str) and re.fullmatch(r"[a-z0-9_]{2,40}", v) for v in p["priority_areas"]):
            c.add(f"{where}: priority area ids must be short lowercase ids")
        for j, q in enumerate(p.get("current_law", [])):
            w = f"{where} current_law[{j}]"
            c.keys(w, q, QUOTE_KEYS)
            c.text(w + " quote", q.get("quote"))
            c.text(w + " citation", q.get("citation"))
            c.url(w, q.get("source_url"))
            if not is_iso(q.get("verified_date")):
                c.add(f"{w}: quote without verified_date")
            if "authority_id" in q and q["authority_id"] not in authorities:
                c.add(f"{w}: dangling authority_id {q['authority_id']!r}")
        if not p.get("sources"):
            c.add(f"{where}: needs at least one source")
        for j, s in enumerate(p.get("sources", [])):
            w = f"{where} sources[{j}]"
            c.keys(w, s, SOURCE_KEYS)
            c.text(w + " label", s.get("label"))
            c.url(w, s.get("url"))
            if "as_of" in s and not is_iso(s["as_of"]):
                c.add(f"{w}: as_of must be an ISO date")
        for j, g in enumerate(p.get("gaps", [])):
            w = f"{where} gaps[{j}]"
            c.keys(w, g, GAP_KEYS)
            c.text(w + " text", g.get("text"))
            c.text(w + " basis_label", g.get("basis_label"))
            c.url(w + " (gap without a published basis)", g.get("basis_url"))
        for j, cv in enumerate(p.get("coverage", [])):
            w = f"{where} coverage[{j}]"
            c.keys(w, cv, COVERAGE_KEYS)
            if cv.get("value") not in rules["coverage_values"]:
                c.add(f"{w}: invalid value")
        c.ids(where, p.get("bill_ids", []), refs["bills"], "bill id")
        c.ids(where, p.get("act_ids", []), refs["acts"], "act id")
        c.ids(where, p.get("thread_ids", []), refs["threads"], "thread id")
        c.ids(where, p.get("topic_ids", []), refs["topics"], "topic id")
        c.ids(where, p.get("stat_keys", []), refs["stats"], "stat key")
        c.ids(where, p.get("see_also", []), all_ids - {pid}, "see_also id")
        if "parent" in p and p["parent"] not in all_ids - {pid}:
            c.add(f"{where}: dangling parent {p['parent']!r}")
        if "position_id" in p and p["position_id"] not in refs["positions"]:
            c.add(f"{where}: position_id is not a published position")
    for pid in approved:
        if pid not in all_ids:
            c.add(f"ct_policy_public.json approved: dangling id {pid!r}")
    return all_ids


def check_areas(c: Checker, doc: dict, refs: dict) -> None:
    c.keys("ct_policy_priority_areas.json", doc, AREA_FILE_KEYS)
    seen = set()
    for i, a in enumerate(doc.get("areas", [])):
        where = f"area[{i}]"
        if not c.keys(where, a, AREA_KEYS):
            continue
        if not isinstance(a.get("id"), str) or not re.fullmatch(r"[a-z0-9_]{2,40}", a["id"]) or a["id"] in seen:
            c.add(f"{where}: invalid or duplicate id")
        seen.add(a.get("id"))
        c.text(where + " title", a.get("title"))
        c.text(where + " summary", a.get("summary"))
        c.ids(where, a.get("topic_ids", []), refs["topics"], "topic id")
        c.ids(where, a.get("thread_ids", []), refs["threads"], "thread id")


def check_regulatory(c: Checker, doc: dict, policy_ids: set) -> None:
    c.keys("ct_regulatory_actions.json", doc, REG_FILE_KEYS)
    seen = set()
    for i, a in enumerate(doc.get("actions", [])):
        where = f"regulatory[{i}]"
        if not c.keys(where, a, REG_KEYS):
            continue
        if not a.get("id") or a["id"] in seen:
            c.add(f"{where}: missing or duplicate id")
        seen.add(a.get("id"))
        if a.get("agency") not in c.rules["regulatory_agencies"]:
            c.add(f"{where}: invalid agency")
        if a.get("stage") not in c.rules["regulatory_stages"]:
            c.add(f"{where}: invalid stage")
        c.text(where + " title", a.get("title"))
        c.url(where, a.get("url"))
        for f in ("comment_open", "comment_close", "checked_date"):
            if f in a and not is_iso(a[f]):
                c.add(f"{where}: {f} must be an ISO date")
        if not is_iso(a.get("checked_date")):
            c.add(f"{where}: needs checked_date")
        if is_iso(a.get("comment_open")) and is_iso(a.get("comment_close")) and a["comment_open"] > a["comment_close"]:
            c.add(f"{where}: comment window ends before it opens")
        c.ids(where, a.get("policy_ids", []), policy_ids, "policy id")


def check_implementation(c: Checker, doc: dict, refs: dict, policy_ids: set) -> None:
    c.keys("ct_implementation.json", doc, IMPL_FILE_KEYS)
    seen = set()
    for i, it in enumerate(doc.get("items", [])):
        where = f"implementation[{i}]"
        if not c.keys(where, it, IMPL_KEYS):
            continue
        if not it.get("id") or it["id"] in seen:
            c.add(f"{where}: missing or duplicate id")
        seen.add(it.get("id"))
        if it.get("act_id") not in refs["acts"]:
            c.add(f"{where}: dangling act_id {it.get('act_id')!r}")
        status = it.get("status")
        if status not in c.rules["implementation_statuses"]:
            c.add(f"{where}: invalid status")
        c.text(where + " provision", it.get("provision"))
        c.url(where + " source", it.get("source_url"))
        c.text(where + " agency", it.get("agency"))
        if not is_iso(it.get("checked_date")):
            c.add(f"{where}: needs checked_date")
        if "deadline" in it and not is_iso(it["deadline"]):
            c.add(f"{where}: deadline must be an ISO date")
        if status in ("complete", "overdue_verified", "in_progress"):
            c.url(where + " evidence", it.get("evidence_url"))
        if status == "overdue_verified" and not (
            is_iso(it.get("deadline")) and is_iso(it.get("checked_date")) and it["deadline"] < it["checked_date"]
        ):
            c.add(f"{where}: overdue only when the deadline is before checked_date")
        if status == "not_due" and is_iso(it.get("deadline")) and is_iso(it.get("checked_date")) and it["deadline"] < it["checked_date"]:
            c.add(f"{where}: not_due but the deadline has passed")
        c.ids(where, it.get("policy_ids", []), policy_ids, "policy id")


def check_authorities(c: Checker, doc: dict) -> set:
    c.keys("ct_ltc_authorities.json", doc, AUTH_FILE_KEYS)
    seen = set()
    for i, a in enumerate(doc.get("authorities", [])):
        where = f"authority[{i}]"
        if not c.keys(where, a, AUTH_KEYS):
            continue
        if not a.get("id") or a["id"] in seen:
            c.add(f"{where}: missing or duplicate id")
        seen.add(a.get("id"))
        if a.get("kind") not in c.rules["authority_kinds"]:
            c.add(f"{where}: invalid kind")
        c.text(where + " citation", a.get("citation"))
        c.text(where + " quote", a.get("quote"))
        c.url(where, a.get("source_url"))
        if not is_iso(a.get("verified_date")):
            c.add(f"{where}: quote without verified_date")
    return seen


def scan(c: Checker) -> None:
    for name in SCAN_FILES:
        f = DATA / name
        if f.exists():
            c.scan_text(f"data/{name}", f.read_text(encoding="utf-8"))
    for page in sorted(ROOT.glob(SCAN_PAGE_GLOB)):
        c.scan_text(str(page.relative_to(ROOT)), page.read_text(encoding="utf-8"))


def problems(docs: dict | None = None, *, run_scan: bool = True) -> list[str]:
    rules = load("ct_policy_rules.json")
    docs = docs or {}
    get = lambda n: docs[n] if n in docs else load(n)  # noqa: E731
    c = Checker(rules)
    refs = references(rules)
    authorities = check_authorities(c, get("ct_ltc_authorities.json"))
    policy_ids = check_policies(c, get("ct_policy_public.json"), refs, authorities)
    check_areas(c, get("ct_policy_priority_areas.json"), refs)
    check_regulatory(c, get("ct_regulatory_actions.json"), policy_ids)
    check_implementation(c, get("ct_implementation.json"), refs, policy_ids)
    for name, doc in docs.items():  # injected content is scanned too
        c.scan_text(f"{name} (candidate)", json.dumps(doc, ensure_ascii=False))
    if run_scan:
        scan(c)
    return c.out


def main() -> int:
    found = problems()
    for p in found:
        print("PROBLEM", p)
    if found:
        print(f"{len(found)} problem(s). Nothing in the public policy layer may ship until they are fixed.")
        return 1
    pol = load("ct_policy_public.json")["policies"]
    print(f"OK: {len(pol)} public policy records; public legislative files and pages scanned clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
