# Health Deficiencies Builder Dry Run Report

Phase 11D.6 dry-run and testing preview report. This phase created a builder script for Connecticut CMS Health Deficiencies and ran it in validation-only and testing-preview modes. It did not create public runtime JSON, build public UI, modify runtime JS/HTML, change staffing formulas, change current or historical staffing JSON, change CT applicability logic, modify geography JSON, or modify facility status review JSON.

## 1. Script Behavior

Builder script:

- `scripts/build_nursing_home_health_deficiencies_ct.py`

Default behavior:

- reads the local ignored CMS Health Deficiencies source;
- reads current staffing data for join validation;
- reads Citation Descriptions lookup when available;
- filters to Connecticut rows;
- validates required fields, dates, F-tags, CCNs, lookup joins, and source row hashes;
- prints a validation summary;
- writes no output.

Testing-preview behavior:

- `python scripts/build_nursing_home_health_deficiencies_ct.py --write-testing-preview`
- writes only `data/testing/nursing_home_health_deficiencies_ct_preview.json`;
- never writes `data/nursing_home_health_deficiencies_ct.json`.

The script refuses to continue if `data/nursing_home_health_deficiencies_ct.json` already exists.

## 2. Source Files Used

| Source | Local file | Role |
|---|---|---|
| CMS Health Deficiencies | `source_data/cms_survey/NH_HealthCitations_May2026.csv` | Citation-level health deficiency source rows. |
| Current staffing data | `data/nursing_home_staffing_ct.json` | Current app CCN join validation only. |
| CMS Citation Code Look-up | `source_data/cms_survey/NH_CitationDescriptions_May2026.csv` | F-tag description/category lookup. |

Raw CMS source files remain ignored under `source_data/`.

## 3. Dry-Run Validation Summary

| Measure | Result |
|---|---:|
| Source rows | 418,177 |
| Connecticut rows | 6,761 |
| Unique CT CCNs | 191 |
| Joined current CCNs | 191 |
| Unmatched current CCNs | 0 |
| Survey date minimum | 2018-11-08 |
| Survey date maximum | 2026-03-31 |
| F-tag row count | 6,761 |
| Distinct F-tags | 164 |
| Citation description lookup misses | 0 |

All Connecticut rows use deficiency prefix `F`.

## 4. Harm/IJ Grouping Counts

The builder applies validation-only grouping from structured `Scope Severity Code` while preserving the original code.

| Harm/IJ group | Count |
|---|---:|
| `actual_harm_not_ij` | 172 |
| `immediate_jeopardy` | 73 |
| `no_actual_harm_minimal` | 463 |
| `no_actual_harm_more_than_minimal` | 6,053 |

Scope/severity counts:

| Code | Count |
|---|---:|
| `B` | 372 |
| `C` | 91 |
| `D` | 4,838 |
| `E` | 1,105 |
| `F` | 110 |
| `G` | 167 |
| `H` | 3 |
| `I` | 2 |
| `J` | 66 |
| `K` | 5 |
| `L` | 2 |

This grouping is a screening classification for testing only. It is not a legal conclusion and should be validated against official CMS scope/severity definitions before public display.

## 5. Survey Year Counts

| Year | Citation rows |
|---|---:|
| 2018 | 3 |
| 2019 | 554 |
| 2020 | 175 |
| 2021 | 545 |
| 2022 | 567 |
| 2023 | 1,280 |
| 2024 | 1,815 |
| 2025 | 1,591 |
| 2026 | 231 |

Survey date, correction date, and processing date are preserved separately in the preview records.

## 6. Testing Preview Output

Preview output:

- `data/testing/nursing_home_health_deficiencies_ct_preview.json`

Preview file size:

- 8,920,774 bytes

Preview row count:

- 6,761 deficiency records

Preview status:

- non-runtime;
- ignored/uncommitted;
- should not be committed as public app output;
- should not be wired into public UI.

## 7. Readiness Recommendation

The builder dry run is ready for a future reviewed build phase. The script reproduced the Phase 11D.4 validation counts, joined all 191 CT Health Deficiency CCNs to current staffing data, joined all F-tags to Citation Descriptions, and produced a testing preview with the expected 6,761 records.

Recommended next phase:

**Phase 11D.7: Health Deficiencies Runtime Readiness Review**

Suggested scope:

1. Review preview JSON shape against `docs/nursing_home_health_deficiencies_data_contract.md`.
2. Decide whether to create `data/nursing_home_health_deficiencies_ct.json` as a non-UI runtime/reference dataset.
3. Add a data contract validation step for the generated JSON.
4. Decide whether derived `harm_ij_group` should be stored or computed at display time.
5. Do not wire the data into public UI until methodology and denominator language are approved.

Alternative next source phase:

**Phase 11D.7: CMS Fire Safety Deficiencies Source Acquisition Validation**

This would validate K-tag/life-safety rows before designing broader survey/enforcement UI architecture.

## 8. Runtime Guardrail Confirmation

No public runtime output was created. `data/nursing_home_health_deficiencies_ct.json` was not created. The only generated data output is the ignored testing preview under `data/testing/`.
