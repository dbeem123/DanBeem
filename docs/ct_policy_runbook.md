# Public policy layer: runbook

Roadmap: Legislative tracker / Now (Phase 1, foundation).

The policy layer is **independent research by the site author**. It is not produced by, affiliated with or endorsed by the Connecticut Long Term Care Ombudsman Program or any State agency. Published Program positions appear only in `data/ct_ltcop_positions.json`, quoted verbatim (see `docs/ct_ltcop_positions_runbook.md`).

## The one rule

Working drafts never enter this repository: not in files, branches, PRs, issues, commit messages, Actions logs or the API. They live in the author's private workspace. The public files below are **generated** from that workspace by a fail-closed export and are never edited by hand.

## Files

| File | What it holds | How it changes |
|---|---|---|
| `data/ct_policy_rules.json` | Which fields may be public, which need approval first, which are internal; id pattern; forbidden content patterns; allowed source hosts | Reviewed edit |
| `data/ct_policy_public.json` | Public policy research records | `scripts/export_public_policy.py` only |
| `data/ct_policy_priority_areas.json` | Priority areas, once their public titles are approved | export only |
| `data/ct_regulatory_actions.json` | Neutral, sourced agency rulemaking and actions | Hand-maintained research |
| `data/ct_implementation.json` | Enacted provisions, agency, deadline, evidence, status | Hand-maintained research |
| `data/ct_ltc_authorities.json` | CT and federal law used by the records: exact quote, source, verified date | Hand-maintained research |

All six start empty. Empty pages and files are the correct state until records are reviewed.

## Field classes (from `ct_policy_rules.json`)

- **public**: identity, neutral question, current law (exact quotes), sources, links to existing bills, acts, threads, topics and stats.
- **public_if_approved**: gaps, coverage, outcome measures, agenda rank, packages. Written only when the private record has `approval_status: "approved"`, non-empty `approval_evidence`, and the field is listed in `approved_fields`. The public file's `approved` map records which gated fields were released.
- **internal**: problem statements, remedies, draft text, owners, notes, fiscal and strategy material, approval evidence. Never written.
- Any key not classified stops the export. Classify it in the rules file first.

## Publishing records

1. Export the reviewed records from the private workspace to a JSON file **outside** this repo:
   `{"policies": [...], "areas": [...]}`.
2. Dry run (shows what becomes public, writes nothing):
   `python scripts/export_public_policy.py <file> --source-version v2027-01-05`
3. Read every `+`, `-` and `~` line. Held-back fields and left-out records are listed as `note` lines.
4. Write: add `--write`. Then `git diff data/` and read it again.
5. Run `python scripts/validate_ct_policy.py` and `python scripts/test_ct_policy.py`. Commit only when both pass.

The export refuses to write when the result fails validation, including the content scan.

## What fails the build

Checked by `scripts/validate_ct_policy.py` locally and by `.github/workflows/legislation-validate.yml` on every push and PR touching legislative files:

- an internal, draft or unknown key; a changed public label;
- an email address, phone number, Windows path, or a "confidential", "do not publish", "internal only" or "draft language" marker anywhere in the public legislative data or `legislation/` pages (exceptions only by exact string in `scan_allowlist`);
- a gated field without approval; a position id that is not a published position;
- a dangling or duplicate id, or an id that collides with an existing bill, act, thread or topic id;
- a quote without `verified_date`, or with a source that is not https on an allowed host; a gap without a published basis;
- an implementation item marked `overdue_verified` before its deadline has passed, or `not_due` after it. `unverified` never means overdue.

## Ids

`AREA-NNN` (pattern in the rules file). Permanent: a retired record keeps its id with `status: "retired"`. Never reuse an id.

## Decided

- 2026-11-23 (Daniel): the policy work is his own independent research; AI tools may work on the private drafts. Drafts still never enter this repo.

## Not decided yet

- Whether Legislation joins the top navigation; regulatory tracker scope; implementation scope (linked acts only, or all 58).
