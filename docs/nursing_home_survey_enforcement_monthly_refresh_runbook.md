# Nursing Home Survey and Enforcement Monthly Refresh Runbook

## 1. Refresh scope

A routine refresh covers four CMS Provider Data source types:

- Health Deficiencies;
- Fire Safety Deficiencies, including K-tag and E-tag rows;
- Citation Descriptions; and
- Penalties / Enforcement.

Publication-month filenames, download URLs, resource identifiers, and acquisition dates will change. Treat each monthly release as one coordinated source set.

## 2. Pre-refresh preparation

1. Start from a clean `main` synchronized with `origin/main`; create a dedicated refresh branch unless an established release procedure requires otherwise.
2. Run `python scripts/audit_nursing_home_survey_enforcement_release.py` and stop if the current release does not pass.
3. Record the current known-good commit and, when useful, hashes for the three statewide runtimes, compact summary, index, and facility files.
4. Confirm `source_data/cms_survey/` and `source_data/cms_enforcement/` remain ignored raw-source directories.
5. Confirm raw CMS files are not tracked or staged.

## 3. Source acquisition

Use official CMS Provider Data sources only. For every download, record its official URL, original filename, acquisition date, and byte size. Store raw files only in the appropriate ignored `source_data/` directory and keep them uncommitted.

Preserve the publication month in the filename:

- `NH_HealthCitations_<MonthYear>.csv`
- `NH_FireSafetyCitations_<MonthYear>.csv`
- `NH_CitationDescriptions_<MonthYear>.csv`
- `NH_Penalties_<MonthYear>.csv`

Do not overwrite prior raw files before validating the new release. If multiple releases are retained together, explicitly inspect which file the current discovery logic selects.

## 4. Builder source filename handling

The validators and three detailed builders are not fixed to the literal May 2026 source filenames. They glob the patterns above, sort matching paths by filename, and select the lexicographically last match. Multiple matching files are reported by the validators, but the builders do not warn about the ambiguity. This is filename ordering, not publication-date or file-modification-time detection; an unexpected filename can therefore select the wrong source.

The Health and Fire builders independently select the lexicographically last `NH_CitationDescriptions_*.csv`. The source month and year written to runtime metadata are parsed from the selected detailed source filename.

However, each detailed builder currently hardcodes its May 2026 `SOURCE_URL` and the acquisition date `2026-06-22`. Before a new release is built, those constants must be deliberately updated and reviewed together with the selected source filenames. Until explicit `--source-file`, `--source-url`, and acquisition-date arguments or an unambiguous release selector are implemented, operators must verify all selected paths and metadata before writing runtime files.

## 5. Validation order

Run from the repository root in this order:

1. Validate Citation Descriptions:
   `python scripts/validate_nursing_home_citation_descriptions.py`
2. Validate Health Deficiencies:
   `python scripts/validate_nursing_home_health_deficiencies.py`
3. Validate Fire Safety and Emergency Preparedness:
   `python scripts/validate_nursing_home_fire_safety_deficiencies.py`
4. Review every citation-description lookup gap.
5. Validate Penalties / Enforcement:
   `python scripts/validate_nursing_home_penalties_enforcement.py`
6. Run all detailed builders without a write flag:
   `python scripts/build_nursing_home_health_deficiencies_ct.py`
   `python scripts/build_nursing_home_fire_safety_deficiencies_ct.py`
   `python scripts/build_nursing_home_penalties_ct.py`
7. Write ignored testing previews with each command's `--write-testing-preview` flag.
8. Compare counts, ranges, lookup behavior, and file sizes with the prior release.
9. Investigate and document material changes before using `--write-runtime`.

Default detailed-builder runs are validation-only. `--write-testing-preview` and `--write-runtime` are mutually exclusive.

## 6. Required comparison checks

Compare old and new releases for:

- source and Connecticut row counts;
- unique and unmatched CCNs;
- survey, penalty, processing, and payment-denial date ranges;
- distinct F, K, and E tags;
- citation-description lookup misses by code and row count;
- Health harm/immediate-jeopardy group counts;
- penalty-type counts, fine total, and payment-denial days;
- duplicate full-row signatures; and
- raw, preview, runtime, summary, and detail file sizes.

Count changes can be valid in a rolling monthly source, but they must be understood and documented. Stop on unexplained schema changes, large discontinuities, malformed dates/tags, new unmatched current CCNs, or unexpected lookup gaps.

## 7. Runtime rebuild sequence

After validation and comparison approval, rebuild in this dependency order:

1. `python scripts/build_nursing_home_health_deficiencies_ct.py --write-runtime`
2. `python scripts/build_nursing_home_fire_safety_deficiencies_ct.py --write-runtime`
3. `python scripts/build_nursing_home_penalties_ct.py --write-runtime`
4. Re-run the detailed validators and validation-only builders as detailed runtime audits; compare the written JSON metadata, counts, hashes, dates, and sizes with the approved previews.
5. `python scripts/build_nursing_home_survey_enforcement_summary_ct.py`
6. First dry-run `python scripts/build_nursing_home_survey_enforcement_facility_details_ct.py`, then write all facility files and the index with `python scripts/build_nursing_home_survey_enforcement_facility_details_ct.py --write-runtime`.
7. `python scripts/audit_nursing_home_survey_enforcement_release.py`
8. Confirm every runtime-to-summary and runtime-to-facility reconciliation passes.
9. Review and update public methodology and source metadata for the new month, dates, and results.
10. Run all CI-equivalent local checks in section 11.
11. Commit generated data and its release documentation in clearly scoped commits.

The summary builder always writes its production output; unlike the detailed builders, it has no validation-only mode. The facility-detail builder is validation-only unless `--write-runtime` is supplied.

Never rebuild only the three statewide files and leave the compact summary or per-facility derivatives stale. All generated layers must come from the same approved source release. Keep unrelated UI features out of a data-refresh commit.

## 8. Documentation and metadata updates

Review and update, as applicable:

- source-validation documents and build-audit documents;
- `data/nursing_home_source_manifest.json`;
- `data/current_tool_context_registry.json`;
- `tools/nursing-home-staffing-methodology.html`;
- `docs/nursing_home_survey_enforcement_release_audit.md`; and
- this closeout/status documentation if feature behavior or material limitations change.

Public source filenames, URLs, acquisition and source dates, recent-window dates, coverage counts, lookup gaps, duplicate counts, and reported file sizes must describe the new release. Update release-audit expectations intentionally when new valid totals replace the current baseline; never weaken reconciliation logic merely to obtain a pass.

## 9. Recent-window handling

The compact-summary builder anchors the recent window to the maximum dated event across the detailed datasets, then uses an inclusive three-year window. A rebuild can move that anchor and change recent counts even if older source rows remain unchanged. Verify the computed start and end dates and update methodology, manifest, registry, audit documentation, and audit expectations when the window changes.

## 10. Lookup-gap handling

For every new Citation Descriptions release:

- recheck `K-0211` and `K-0133`; do not assume current gaps persist;
- document gaps that become resolved;
- identify and document every new missing lookup code and its affected row count;
- never invent lookup descriptions; and
- preserve the source-row description when official lookup text is absent.

## 11. Release checks

Run and require success for:

```powershell
python -m py_compile scripts/validate_nursing_home_citation_descriptions.py scripts/validate_nursing_home_health_deficiencies.py scripts/validate_nursing_home_fire_safety_deficiencies.py scripts/validate_nursing_home_penalties_enforcement.py scripts/build_nursing_home_health_deficiencies_ct.py scripts/build_nursing_home_fire_safety_deficiencies_ct.py scripts/build_nursing_home_penalties_ct.py scripts/build_nursing_home_survey_enforcement_summary_ct.py scripts/build_nursing_home_survey_enforcement_facility_details_ct.py scripts/audit_nursing_home_survey_enforcement_release.py
python scripts/audit_nursing_home_survey_enforcement_release.py
node --check Assets/nursing-home-staffing.js
python -m unittest scripts.test_build_nursing_home_staffing_ct
python -m json.tool data/nursing_home_health_deficiencies_ct.json > $null
python -m json.tool data/nursing_home_fire_safety_deficiencies_ct.json > $null
python -m json.tool data/nursing_home_penalties_ct.json > $null
python -m json.tool data/nursing_home_survey_enforcement_summary_ct.json > $null
python -m json.tool data/nursing_home_survey_enforcement_details_ct/index.json > $null
python -m json.tool data/nursing_home_source_manifest.json > $null
python -m json.tool data/current_tool_context_registry.json > $null
git diff --check
```

The validator, validation-only builder, preview, explicit runtime, summary, and facility-detail commands from sections 5 and 7 are also mandatory. After push, confirm the GitHub Actions `Nursing Home Survey Enforcement Audit` release gate passes.

Remove or restore any generated `__pycache__` directories and `.pyc` files before staging.

## 12. Commit and push safeguards

1. Inspect `git status --short --branch`, `git diff --name-only`, `git diff --cached --name-only`, and the staged diff.
2. Exclude raw CMS sources, `data/testing/`, `__pycache__`, `.pyc`, and unrelated files.
3. Report the sizes of every generated runtime layer and investigate unexpected growth or shrinkage.
4. Avoid date-only rebuild commits. Regenerate and commit the complete dependency chain only as part of an intentional refresh.
5. Push only after local checks pass and the branch is not behind or diverged from `origin/main`.
6. After push, confirm a clean `## main...origin/main` (or the corresponding refresh branch) and a passing CI release gate.

## 13. Rollback procedure

Use Git history to identify the last known-good data release commit. Do not hand-edit generated JSON. Restore the complete related set from that commit together:

- all three statewide runtime files;
- the compact summary;
- every per-facility detail file and the index;
- the source manifest and tool-context registry; and
- methodology/source wording if it had changed for the rolled-back release.

Then run the full release audit and CI-equivalent checks. Commit the rollback as an explicit, reviewable rollback change.

## 14. Future maintenance improvements

Future maintenance work should consider:

- explicit builder command-line source-file, source-URL, and acquisition-date arguments;
- a coordinated refresh orchestrator;
- an automatic old-versus-new comparison report;
- source URL manifest generation;
- deterministic build-date handling that prevents date-only diffs;
- CI verification that generated layers are fresh relative to their inputs; and
- scheduled monitoring for new official CMS source releases.
