# Nursing Home Survey / Enforcement Runtime Build Audit Plan

Phase 11D.14 documentation-only audit plan. This plan defines the checks required before dry-run/testing previews are promoted to production runtime JSON files.

This phase does not generate runtime JSON, build public UI, modify runtime JS/HTML, modify current staffing JSON, modify historical PBJ JSON, modify geography JSON, modify facility status review JSON, change formulas, change CT applicability logic, modify builder scripts, or commit raw CMS source files.

## 1. Purpose

The validated builders for Health Deficiencies, Fire Safety Deficiencies, and Penalties / Enforcement can produce ignored testing previews. Before any production runtime JSON is created, the project needs a repeatable audit plan that proves source counts, joins, dates, category counts, metadata, file sizes, and caveats are correct.

This plan covers required checks before creating:

- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_penalties_ct.json`
- later `data/nursing_home_survey_enforcement_summary_ct.json`

The production runtime build phase should remain separate from public UI wiring unless explicitly approved.

## 2. Required Source Files

Expected ignored local CMS source files:

| Source lane | Required local source file |
|---|---|
| Health Deficiencies | `source_data/cms_survey/NH_HealthCitations_May2026.csv` |
| Fire Safety / Emergency Preparedness Deficiencies | `source_data/cms_survey/NH_FireSafetyCitations_May2026.csv` |
| Citation Descriptions lookup | `source_data/cms_survey/NH_CitationDescriptions_May2026.csv` |
| Penalties / Enforcement | `source_data/cms_enforcement/NH_Penalties_May2026.csv` |

These source files must remain ignored under `source_data/` unless the user explicitly approves committing raw CMS source files.

Required committed app files:

| Category | Required files |
|---|---|
| Current/context facility data | `data/nursing_home_staffing_ct.json` |
| Health source validation | `docs/nursing_home_health_deficiencies_source_validation.md` |
| Health data contract | `docs/nursing_home_health_deficiencies_data_contract.md` |
| Health builder dry-run report | `docs/nursing_home_health_deficiencies_builder_dry_run_report.md` |
| Health builder | `scripts/build_nursing_home_health_deficiencies_ct.py` |
| Fire source validation | `docs/nursing_home_fire_safety_deficiencies_source_validation.md` |
| Fire data contract | `docs/nursing_home_fire_safety_deficiencies_data_contract.md` |
| Fire lookup gap review | `docs/nursing_home_fire_safety_citation_lookup_gap_review.md` |
| Fire builder dry-run report | `docs/nursing_home_fire_safety_deficiencies_builder_dry_run_report.md` |
| Fire builder | `scripts/build_nursing_home_fire_safety_deficiencies_ct.py` |
| Penalties source validation | `docs/nursing_home_penalties_enforcement_source_validation.md` |
| Penalties data contract | `docs/nursing_home_penalties_enforcement_data_contract.md` |
| Penalties builder dry-run report | `docs/nursing_home_penalties_enforcement_builder_dry_run_report.md` |
| Penalties builder | `scripts/build_nursing_home_penalties_ct.py` |
| Runtime integration roadmap | `docs/nursing_home_survey_enforcement_runtime_integration_roadmap.md` |

## 3. Pre-Build Checks

Run these checks before any production runtime output is created.

### Health Deficiencies Builder

```powershell
python -m py_compile scripts/build_nursing_home_health_deficiencies_ct.py
python scripts/build_nursing_home_health_deficiencies_ct.py
python scripts/build_nursing_home_health_deficiencies_ct.py --write-testing-preview
```

Required pre-build assertions:

- dry run writes no output;
- testing preview writes only `data/testing/nursing_home_health_deficiencies_ct_preview.json`;
- `data/nursing_home_health_deficiencies_ct.json` is not created during dry run or preview;
- row counts match validation docs;
- unique CT CCN count matches validation docs;
- join count matches validation docs;
- unmatched current CCNs are zero or documented;
- metadata matches source counts;
- date range matches validation docs;
- Citation Descriptions lookup miss count matches validation docs.

### Fire Safety / Emergency Preparedness Builder

```powershell
python -m py_compile scripts/build_nursing_home_fire_safety_deficiencies_ct.py
python scripts/build_nursing_home_fire_safety_deficiencies_ct.py
python scripts/build_nursing_home_fire_safety_deficiencies_ct.py --write-testing-preview
```

Required pre-build assertions:

- dry run writes no output;
- testing preview writes only `data/testing/nursing_home_fire_safety_deficiencies_ct_preview.json`;
- `data/nursing_home_fire_safety_deficiencies_ct.json` is not created during dry run or preview;
- row counts match validation docs;
- unique CT CCN count matches validation docs;
- join count matches validation docs;
- unmatched current CCNs are zero or documented;
- metadata matches source counts;
- date range matches validation docs;
- K/E prefix counts match validation docs;
- Citation Descriptions lookup misses are limited to documented `K-0211` and `K-0133` gaps;
- no health F-tag harm/IJ grouping is applied.

### Penalties / Enforcement Builder

```powershell
python -m py_compile scripts/build_nursing_home_penalties_ct.py
python scripts/build_nursing_home_penalties_ct.py
python scripts/build_nursing_home_penalties_ct.py --write-testing-preview
```

Required pre-build assertions:

- dry run writes no output;
- testing preview writes only `data/testing/nursing_home_penalties_ct_preview.json`;
- `data/nursing_home_penalties_ct.json` is not created during dry run or preview;
- row counts match validation docs;
- unique CT CCN count matches validation docs;
- join count matches validation docs;
- unmatched current CCNs are zero or documented;
- metadata matches source counts;
- date ranges match validation docs;
- fine and payment-denial counts match validation docs;
- duplicate full-row signature count matches validation docs.

## 4. Dataset-Specific Audit Checks

### Health Deficiencies

Expected audit values:

| Check | Expected value |
|---|---:|
| CT rows | 6,761 |
| Unique CT CCNs | 191 |
| Joined current CCNs | 191 |
| Unmatched current CCNs | 0 |
| Survey date minimum | 2018-11-08 |
| Survey date maximum | 2026-03-31 |
| Distinct F-tags | 164 |
| Citation description lookup misses | 0 |

Health harm/IJ grouping counts:

| Group | Expected count |
|---|---:|
| `actual_harm_not_ij` | 172 |
| `immediate_jeopardy` | 73 |
| `no_actual_harm_minimal` | 463 |
| `no_actual_harm_more_than_minimal` | 6,053 |

Audit requirements:

- confirm all CT rows use deficiency prefix `F`;
- preserve original `Scope Severity Code`;
- confirm harm/IJ grouping is derived from structured `Scope Severity Code`;
- confirm grouping remains labeled as screening context, not a legal conclusion;
- confirm Citation Descriptions lookup joins all F-tags.

### Fire Safety / Emergency Preparedness

Expected audit values:

| Check | Expected value |
|---|---:|
| CT rows | 2,135 |
| Unique CT CCNs | 178 |
| Joined current CCNs | 178 |
| Unmatched current CCNs | 0 |
| Survey date minimum | 2018-11-08 |
| Survey date maximum | 2026-02-27 |
| K rows | 2,007 |
| E rows | 128 |
| Distinct citation codes | 84 |
| Citation description lookup misses | 145 |

Expected lookup miss codes:

| Code | Expected missed rows |
|---|---:|
| `K-0211` | 143 |
| `K-0133` | 2 |

Expected scope/severity counts:

| Scope/severity code | Expected count |
|---|---:|
| `D` | 1,556 |
| `E` | 338 |
| `F` | 238 |
| `J` | 2 |
| `K` | 1 |

Audit requirements:

- confirm K-tags and E-tags remain separate from health F-tags;
- confirm source `Deficiency Description` is preserved for all rows;
- confirm lookup text/category are null only when no official Citation Descriptions row exists;
- confirm `K-0211` and `K-0133` are flagged as documented CMS lookup-source gaps;
- confirm no unexpected lookup misses are present;
- confirm no health F-tag harm/IJ grouping is applied to fire safety rows.

### Penalties / Enforcement

Expected audit values:

| Check | Expected value |
|---|---:|
| CT rows | 179 |
| Unique CT CCNs | 102 |
| Joined current CCNs | 102 |
| Unmatched current CCNs | 0 |
| Duplicate CT full-row signatures | 3 |
| Penalty date minimum | 2023-05-17 |
| Penalty date maximum | 2026-03-17 |
| Processing date minimum | 2026-05-01 |
| Processing date maximum | 2026-05-01 |
| Payment denial start date minimum | 2024-01-17 |
| Payment denial start date maximum | 2024-12-03 |
| Fine rows | 167 |
| Payment Denial rows | 12 |
| CT fine amount total | 3,925,517.00 |
| Payment denial length total | 368 days |

Audit requirements:

- confirm fine rows and payment-denial rows remain separate enforcement types;
- confirm duplicate rows are preserved and flagged;
- confirm `source_row_hash` is present;
- confirm fine amounts parse as numeric values;
- confirm payment denial length parses as integer days;
- confirm fine amount is not used as a quality score;
- confirm penalty date, payment denial start date, and processing date remain separate.

## 5. Production Runtime Build Rules

Production runtime JSON creation must be explicit. Builders should not create production runtime JSON unless run with a future approved flag or in a separately scoped production build phase.

Rules:

1. Generated runtime JSON files should be reviewed before commit.
2. Raw CMS source files must remain ignored under `source_data/`.
3. Generated runtime JSON files may be committed only after the audit checks pass.
4. Large file sizes must be reported before commit.
5. Runtime files must include metadata and limitations.
6. Runtime files must preserve source date fields separately.
7. Runtime files must include enough metadata to reproduce row counts and source-window caveats.
8. Do not wire UI in the same phase unless explicitly approved.
9. Do not merge survey/enforcement data into staffing scores.
10. Do not alter current/context staffing data, historical PBJ data, geography data, facility status review data, or CT applicability logic.

Recommended production build behavior:

- default remains dry run;
- explicit production flag or separate production build script writes runtime JSON;
- production run fails loudly on missing required source files, missing required fields, unexpected unmatched CCNs, unexpected lookup misses, invalid dates, invalid amounts, or metadata mismatches;
- production run prints file size before commit.

## 6. Source-To-Runtime Audit Report

Each production build phase should create or update an audit document for the generated runtime file.

Recommended audit document fields:

- source file name and official URL;
- source row count;
- CT source row count;
- output row count;
- unique CT CCN count;
- current staffing join count;
- unmatched CCN list, if any;
- date ranges;
- key category counts;
- lookup miss counts and codes;
- duplicate source row counts;
- generated file path;
- generated file size;
- generated file hash, if useful;
- validation command output summary;
- whether public UI behavior changed;
- confirmation that raw source files remain ignored;
- confirmation that protected data files were not modified.

Suggested future audit docs:

- `docs/nursing_home_health_deficiencies_runtime_build_audit.md`
- `docs/nursing_home_fire_safety_deficiencies_runtime_build_audit.md`
- `docs/nursing_home_penalties_runtime_build_audit.md`
- `docs/nursing_home_survey_enforcement_summary_runtime_build_audit.md`

## 7. Static-Site Performance Review

Detailed runtime files may be large:

| Lane | Preview size | Preview rows |
|---|---:|---:|
| Health Deficiencies | about 8.9 MB | 6,761 |
| Fire Safety / Emergency Preparedness | about 2.66 MB | 2,135 |
| Penalties / Enforcement | about 160 KB | 179 |

Performance recommendations:

- avoid loading detailed citation/event files on the initial Facility Explorer page load;
- use compact summary JSON for default display;
- lazy-load detailed files only when a user opens a detail section;
- measure total payload impact before UI wiring;
- test mobile performance before public release;
- consider file splitting only if performance testing shows it is necessary.

The compact summary file should be the first public runtime integration target for Facility Explorer.

## 8. Recommended Next Phases

Recommended sequence:

1. **Phase 11D.15: Create Production Runtime JSON Files, No UI Wiring**
   Create the three detailed runtime JSON files after running the audit checks in this plan. Report file sizes before commit.

2. **Phase 11D.16: Audit Production Runtime JSON Files And File Sizes**
   Create audit docs showing source-to-runtime row counts, joins, dates, category counts, file sizes, and hashes if useful.

3. **Phase 11D.17: Create Compact Facility-Level Survey / Enforcement Summary JSON**
   Build `data/nursing_home_survey_enforcement_summary_ct.json` from audited detailed runtime files. Validate one row per current facility CCN.

4. **Phase 11D.18: Prototype Facility Explorer Survey & Enforcement Snapshot Using Summary JSON Only**
   Wire a cautious summary card into the Facility Explorer / Advanced Facility Dossier without loading detailed citation/event rows by default.

5. **Phase 11D.19: Add Optional Lazy-Loaded Detailed Dossier Sections**
   Add detailed health, fire safety, emergency preparedness, and enforcement sections only after static-site performance review.

6. **Phase 11D.20: Public Methodology And Wording Review**
   Review public labels, source windows, denominator language, lookup gaps, duplicate penalty handling, and non-score caveats.

## 9. Explicit Non-Goals

This audit plan does not:

- generate runtime JSON;
- change public UI;
- modify runtime JS/HTML;
- change staffing formulas;
- merge survey/enforcement data into staffing scores;
- create facility rankings based on penalties or fines;
- alter current staffing data;
- alter historical PBJ data;
- alter geography data;
- alter facility status review data;
- change CT applicability logic;
- commit raw CMS source files;
- make legal conclusions from citations or penalties.

## 10. Guardrails

- Citation rows are source-backed context, not simple current performance scores.
- Penalties are enforcement records, not quality scores.
- Fine totals need explicit time-window and duplicate-row context.
- Fire safety lookup gaps for `K-0211` and `K-0133` must remain transparent.
- Health harm/IJ grouping must remain tied to structured scope/severity and public wording review.
- Public UI should not imply survey/enforcement data is exhaustive or definitive.
- Static-site performance must be reviewed before detailed files are loaded by public pages.

