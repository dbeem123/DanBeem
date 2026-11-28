"""Fail-closed export from the private policy workspace to the public repo.

Reads a JSON file exported from the private workspace (never kept in this repo):
    {"policies": [ {...record with public, gated and internal fields...} ],
     "areas":    [ {...area with release_eligible / approval fields...} ]}

Rules (data/ct_policy_rules.json):
- An unknown key anywhere in a record stops the whole export. Nothing is written.
- A record without release_eligible == true is left out (and listed).
- Internal fields are never written.
- A public_if_approved field is written only when the record has approval_status "approved",
  non-empty approval_evidence, and the field is named in approved_fields.
- The result must pass scripts/validate_ct_policy.py (including the content scan) or nothing is written.
- Nothing about the private source (its path, owner, comments) is written.

Shows what would become public. Writes only with --write.

Usage:
    python scripts/export_public_policy.py PRIVATE_EXPORT.json --source-version v2027-01-05 [--write]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_ct_policy as validator  # noqa: E402

DATA = validator.DATA
AREA_PUBLIC = ["id", "title", "summary", "topic_ids", "thread_ids"]
AREA_INTERNAL = {"release_eligible", "approval_status", "approval_evidence", "owner", "notes", "draft_summary"}


class ExportError(Exception):
    pass


def approved(record: dict) -> bool:
    return record.get("approval_status") == "approved" and bool(record.get("approval_evidence"))


def build(private: dict, rules: dict, *, source_version: str, today: str) -> tuple[dict, dict, list[str]]:
    fields = rules["policy_fields"]
    public, gated, internal = set(fields["public"]), set(fields["public_if_approved"]), set(fields["internal"])
    if not isinstance(private, dict) or set(private) - {"policies", "areas"}:
        raise ExportError("private export must be an object with only 'policies' and 'areas'")
    notes: list[str] = []
    out_policies, approved_map = [], {}
    for i, rec in enumerate(private.get("policies", [])):
        if not isinstance(rec, dict):
            raise ExportError(f"policy[{i}] is not an object")
        unknown = set(rec) - public - gated - internal
        if unknown:
            raise ExportError(f"policy[{i}] {rec.get('id')!r} has unclassified key(s) {sorted(unknown)}; classify them in ct_policy_rules.json first")
        if rec.get("release_eligible") is not True:
            notes.append(f"left out {rec.get('id')!r}: not release_eligible")
            continue
        row = {k: rec[k] for k in fields["public"] if k in rec}
        allowed = set(rec.get("approved_fields") or []) if approved(rec) else set()
        bad = allowed - gated
        if bad:
            raise ExportError(f"policy {rec.get('id')!r}: approved_fields names non-gated field(s) {sorted(bad)}")
        for k in fields["public_if_approved"]:
            if k in rec:
                if k in allowed:
                    row[k] = rec[k]
                else:
                    notes.append(f"held back {rec.get('id')}.{k}: not approved")
        kept = sorted(set(row) & gated)
        if kept:
            approved_map[row.get("id")] = kept
        out_policies.append(row)
    out_policies.sort(key=lambda r: str(r.get("id")))

    out_areas = []
    for i, a in enumerate(private.get("areas", [])):
        if not isinstance(a, dict):
            raise ExportError(f"area[{i}] is not an object")
        unknown = set(a) - set(AREA_PUBLIC) - AREA_INTERNAL
        if unknown:
            raise ExportError(f"area[{i}] has unclassified key(s) {sorted(unknown)}")
        if a.get("release_eligible") is not True or not approved(a):
            notes.append(f"left out area {a.get('id')!r}: not approved for release")
            continue
        out_areas.append({k: a[k] for k in AREA_PUBLIC if k in a})

    current_pol = json.loads((DATA / "ct_policy_public.json").read_text(encoding="utf-8"))
    current_areas = json.loads((DATA / "ct_policy_priority_areas.json").read_text(encoding="utf-8"))
    pol_doc = {k: current_pol[k] for k in ("schema_version", "label", "limitations")}
    pol_doc.update(exported_at=today, source_version=source_version, approved=approved_map, policies=out_policies)
    area_doc = {k: current_areas[k] for k in ("schema_version", "limitations")}
    area_doc.update(exported_at=today, source_version=source_version, areas=out_areas)
    return pol_doc, area_doc, notes


def diff(old: list, new: list, label: str) -> list[str]:
    o = {r.get("id"): r for r in old}
    n = {r.get("id"): r for r in new}
    lines = [f"+ {label} {k} (new, becomes public)" for k in sorted(n.keys() - o.keys())]
    lines += [f"- {label} {k} (removed from public)" for k in sorted(o.keys() - n.keys())]
    for k in sorted(o.keys() & n.keys()):
        changed = sorted(f for f in set(o[k]) | set(n[k]) if o[k].get(f) != n[k].get(f))
        if changed:
            lines.append(f"~ {label} {k}: {', '.join(changed)}")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("private_export")
    ap.add_argument("--source-version", required=True, help="short label such as v2027-01-05 (no paths)")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--write", action="store_true", help="write the public files after showing the changes")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,40}", a.source_version):
        print("STOP --source-version must be a short label, not a path")
        return 2
    rules = validator.load("ct_policy_rules.json")
    try:
        private = json.loads(Path(a.private_export).read_text(encoding="utf-8"))
        pol_doc, area_doc, notes = build(private, rules, source_version=a.source_version, today=a.date)
    except (ExportError, ValueError, OSError) as exc:
        print(f"STOP {exc}. Nothing written.")
        return 2
    found = validator.problems({"ct_policy_public.json": pol_doc, "ct_policy_priority_areas.json": area_doc})
    for n in notes:
        print("note", n)
    if found:
        for p in found:
            print("PROBLEM", p)
        print("STOP the export does not pass validation. Nothing written.")
        return 1
    current_pol = validator.load("ct_policy_public.json")
    current_areas = validator.load("ct_policy_priority_areas.json")
    changes = diff(current_pol["policies"], pol_doc["policies"], "policy") + diff(current_areas["areas"], area_doc["areas"], "area")
    print("\n".join(changes) if changes else "No changes to the public policy layer.")
    if not a.write:
        print("Dry run. Re-run with --write to publish these changes to data/.")
        return 0
    (DATA / "ct_policy_public.json").write_text(json.dumps(pol_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "ct_policy_priority_areas.json").write_text(json.dumps(area_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Written: data/ct_policy_public.json, data/ct_policy_priority_areas.json. Review the git diff before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
