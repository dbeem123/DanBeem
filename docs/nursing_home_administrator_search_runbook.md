# Connecticut administrator search — private review pipeline

Phase A only. There is no public data file or new search page in this change.
Do not publish a roster, attach facilities to people by name, or treat a license
as proof of employment. Public UI work follows Claude's source/match review.

## Source intake

The three authoritative DPH export hashes are in
`data/ct_dph_source_profile.json`. Find files by those hashes, not filenames.
Copy verified originals into ignored `source_data/ct_dph/`; retain their exact
bytes. Never stage raw files, contact fields or generated review artifacts.
The old roster data-contract document describes mailing fields for validation;
this pipeline intentionally does **not** use that proposed record shape.

The official roster download page is
<https://www.elicense.ct.gov/lookup/GenerateRoster.aspx>. The relevant exports
are Nursing Home Management History, Chronic and Convalescent Nursing Home,
and Nursing Home Administrator. CT warns that the management history includes
converted historical records with incomplete fields. A newer download is a new
snapshot: record its provenance, profile it and obtain source review before
changing the pinned hashes. Do not label it the original snapshot.

Get the optional current license cross-check explicitly:

```powershell
python scripts/fetch_ct_administrator_license_status.py --output source_data/ct_dph/state_licenses_nha_YYYYMMDD.json
```

The query selects only `name,credentialnumber,status,issuedate,expirationdate`
where `credentialtype = '36'` from the official public dataset
<https://data.ct.gov/Business/State-Licenses-and-Credentials/ngch-56tr>.
It has bounded pagination, a 30-second request deadline and no retries.
Unnumbered applications are counted and excluded; they cannot validate an
administrator license. Intake rejects extra response fields, incomplete
pagination and empty results. No credential or API token is needed.

The resulting snapshot stays under `source_data/ct_dph/`. Existing snapshots
are never overwritten. Dates reflect retrieval, not an asserted history of
employment. This source can confirm professional-license status; it cannot
replace the DPH administrator/facility relationship file.

## Build the private review

```powershell
python scripts/build_ct_administrator_history.py --source-as-of 2026-05-22 --crosscheck source_data/ct_dph/state_licenses_nha_YYYYMMDD.json
```

Use the **verified snapshot date**, not today's date or a filesystem mtime.
All three hashes must match the profile before any rows are parsed or any
review is written. A renamed exact copy works; a same-named changed file fails.
No source substitution or network download takes place inside the builder.

Default outputs, both ignored:

- `data/testing/ct_administrator_history_review.json`
- `data/testing/ct_administrator_history_review.md`

For a second review, preserve the first and pass a new `--output` filename
under `data/testing/`. The command refuses public or existing destinations.
It does not implement `--publish`: that belongs to Phase B after review.

## Identity, time and facility rules

- Only `Position == "Administrator"` is included. Directors of Nurses,
  Medical Directors and all other positions are excluded.
- Person keys use professional license digits without leading zeroes. Raw
  names and identifiers stay available for review. Same-name/different-license
  records remain separate. Same-license name variants are flagged.
- Temporary and blank-license tenures remain unlinked. Temporary digits do not
  merge into a permanent license. They remain visible as facility-role evidence.
- Empty start dates stay unknown. An empty end is open only for an active
  relationship, through the snapshot date. Invalid dates are flagged. An
  inactive relationship without an end is **not** treated as current.
- Overlap pairs require known, usable starts and ends (or active open ends
  bounded by the snapshot). Unknown dates are flagged, not filled in. Multiple
  active records at a facility are flagged without deciding which is correct.
- Registry and newer public status observations are retained separately.
  Conflicts and duplicate observations are flagged; ambiguous statuses are
  not arbitrarily selected. A missing registry match does not invalidate a role.
- The existing `build_ct_dph_ccn_crosswalk.py` performs facility matching in
  memory. Only the safe projection is written: license, facility names,
  proposed CCN, score, evidence booleans and review decision. Business addresses
  used for matching are also omitted from review outputs.

The source profile's 173 overlaps, 26 multiple-active groups, 141 temporary
licenses and 250 missing-start rows describe the broader management-history
profile; they must **not** be pinned as administrator-only totals. The 97
registry nonmatches were role rows, not necessarily 97 distinct people.
Recalculate every count for the administrator subset and report both rows and
distinct license counts. Sampling is deterministic (20 people, seed 20261103).

## Match review gate

Review every non-`auto_high` facility match and at least 10% of `auto_high`
matches against source records. No guessed CCN is treated as confirmed.

The existing crosswalk runbook requires accepted rows for public use, while the
new prompt permits `auto_high` candidates. This Phase A implementation uses
the stricter rule: candidates remain separately labelled, and role `ccn` stays
null until an explicit decision with a note. Resolve policy at match review.

An ignored `--crosswalk-review` JSON file may contain:

```json
[
  {"facility_license":"10","ccn":"075001","decision":"accepted","note":"Reviewed against official facility records."}
]
```

This is a fabricated format example, not a real accepted match. A decision must
match the actual proposed CCN; only `auto_high` or `likely` can be accepted;
duplicate, stale, weak or conflicting accepted CCNs fail. Rejected matches
remain unlinked. Do not infer historical CCN continuity solely from the current
facility master; closures, relocations and license changes need review.

Reviewed corrections/suppressions and their reason/date belong in Phase B's
publication validator. Phase A emits an empty `corrections` list and no public
file, so it cannot accidentally publish an unapplied correction.

## Privacy and tests

The registry reader projects the approved fields immediately, discarding
contact columns before accumulating records. Review output checks reject
forbidden field names and suspicious contact information in values, including
street-plus-five-digit-postal patterns. Errors do not dump source records.
All tests use fictional identities; the mock HTTP intake reads no live data.

```powershell
New-Item -ItemType Directory -Force .\.test-tmp | Out-Null
$env:TMPDIR = (Resolve-Path .\.test-tmp).Path
$env:TEMP = $env:TMPDIR
$env:TMP = $env:TMPDIR
python scripts/test_build_ct_administrator_history.py
python scripts/test_build_ct_dph_ccn_crosswalk.py
```

Never serve the worktree root while private inputs/reviews are present:
git-ignore prevents commits, **not** access through a general static server.
Phase B previews must serve a tracked-public-files-only copy with mock data
until the real public-data review is accepted.

Future source only, not implemented: CT DSS annual cost-report administrator
sections may provide additional professional-role cross-checks. Compensation
or other personal information must never be copied into the public dataset.
