# Nursing Home Survey and Enforcement Runtime JSON Build Audit

## Scope

Phase 11D.15 created the three detailed Connecticut production runtime JSON files. No compact summary JSON or public UI wiring was created.

## Sources

- `source_data/cms_survey/NH_HealthCitations_May2026.csv` (164,917,215 bytes)
- `source_data/cms_survey/NH_FireSafetyCitations_May2026.csv` (69,121,738 bytes)
- `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`
- `source_data/cms_enforcement/NH_Penalties_May2026.csv` (2,768,010 bytes)
- `data/nursing_home_staffing_ct.json` was read only as the current-facility CCN join reference.

The raw CMS source files remain ignored and uncommitted.

## Commands Run

Compile checks:

```text
python -m py_compile scripts/build_nursing_home_health_deficiencies_ct.py
python -m py_compile scripts/build_nursing_home_fire_safety_deficiencies_ct.py
python -m py_compile scripts/build_nursing_home_penalties_ct.py
```

Validation-only dry runs:

```text
python scripts/build_nursing_home_health_deficiencies_ct.py
python scripts/build_nursing_home_fire_safety_deficiencies_ct.py
python scripts/build_nursing_home_penalties_ct.py
```

Explicit production builds:

```text
python scripts/build_nursing_home_health_deficiencies_ct.py --write-runtime
python scripts/build_nursing_home_fire_safety_deficiencies_ct.py --write-runtime
python scripts/build_nursing_home_penalties_ct.py --write-runtime
```

Final repository checks:

```text
git diff --check
git status --short --branch
```

## Runtime Outputs

| Runtime file | Rows | Unique CT CCNs | Joined current CCNs | Unmatched current CCNs | Exact size |
| --- | ---: | ---: | ---: | ---: | ---: |
| `data/nursing_home_health_deficiencies_ct.json` | 6,761 | 191 | 191 | 0 | 8,920,771 bytes |
| `data/nursing_home_fire_safety_deficiencies_ct.json` | 2,135 | 178 | 178 | 0 | 2,657,540 bytes |
| `data/nursing_home_penalties_ct.json` | 179 | 102 | 102 | 0 | 159,521 bytes |

## Health Deficiencies Validation

- Survey dates: 2018-11-08 through 2026-03-31.
- F-tag rows: 6,761; distinct F-tags: 164.
- Citation-description lookup misses: 0.
- Harm/IJ groups: 172 `actual_harm_not_ij`, 73 `immediate_jeopardy`, 463 `no_actual_harm_minimal`, and 6,053 `no_actual_harm_more_than_minimal`.
- Scope/severity counts: B 372, C 91, D 4,838, E 1,105, F 110, G 167, H 3, I 2, J 66, K 5, L 2.

## Fire Safety and Emergency Preparedness Validation

- Survey dates: 2018-11-08 through 2026-02-27.
- Prefix counts: 2,007 K rows and 128 E rows; 84 distinct citation codes.
- Citation-description lookup misses: 145. The documented official lookup gaps are K-0211 (143 rows) and K-0133 (2 rows).
- Scope/severity counts: D 1,556, E 338, F 238, J 2, K 1.
- Independent JSON inspection confirmed that no health F-tag harm/IJ grouping field is present on fire safety or emergency preparedness rows.

## Penalties and Enforcement Validation

- Penalty dates: 2023-05-17 through 2026-03-17.
- Processing dates: 2026-05-01 through 2026-05-01.
- Payment-denial start dates: 2024-01-17 through 2024-12-03.
- Types: 167 Fine rows and 12 Payment Denial rows.
- Fine amount total: $3,925,517.00.
- Payment-denial length total: 368 days.
- Three duplicate CT full-row signatures were found. All three rows remain in the runtime JSON and have `duplicate_full_row_signature` set to true.

## Builder and Runtime Behavior Review

All three builders were minimally changed to add mutually exclusive `--write-runtime` production output. Their default behavior remains validation-only, and `--write-testing-preview` continues to write only under `data/testing/`. Production output occurs only when `--write-runtime` is explicitly supplied.

No JavaScript, HTML, staffing JSON, historical PBJ JSON, geography JSON, facility-status review JSON, or staffing formulas were changed. `data/nursing_home_survey_enforcement_summary_ct.json` was not created.

**Warning:** These detailed runtime files are not yet wired into the public UI, so public runtime behavior is unchanged.

## Recommendation

Proceed to Phase 11D.17 and build the compact facility-level survey/enforcement summary JSON from these audited detailed files, validating one row per current facility CCN. Keep public UI wiring deferred until that compact summary has its own audit.
