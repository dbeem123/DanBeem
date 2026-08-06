# Nursing Home Survey and Enforcement Feature Closeout

## 1. Feature status

The current survey and enforcement feature-development sequence is complete. The repository now implements:

- CMS Health Deficiencies and F-tag source validation;
- CMS Fire Safety and K-tag source validation;
- CMS Emergency Preparedness and E-tag source validation;
- CMS Penalties and Enforcement source validation;
- documented runtime data contracts;
- validation-only dry-run builders and explicit production-write modes;
- production statewide runtime datasets;
- a compact one-record-per-facility summary;
- CCN-specific per-facility detail datasets;
- a compact Facility Explorer Survey & Enforcement Snapshot;
- detailed findings that load only after explicit user activation;
- public methodology and source disclosures;
- an automated 12-section release consistency audit; and
- a GitHub Actions release gate.

## 2. Current production data files

The May 2026 source release produced the following current files. Sizes are exact audit measurements, shown with approximate human-scale equivalents.

| File or file set | Current count | Size |
| --- | ---: | ---: |
| `data/nursing_home_health_deficiencies_ct.json` | 6,761 rows; 191 CCNs | 8,920,771 bytes (8.9 MB) |
| `data/nursing_home_fire_safety_deficiencies_ct.json` | 2,135 rows; 178 CCNs | 2,657,540 bytes (2.7 MB) |
| `data/nursing_home_penalties_ct.json` | 179 rows; 102 CCNs | 159,521 bytes (160 KB) |
| `data/nursing_home_survey_enforcement_summary_ct.json` | 196 facility rows | 322,951 bytes (323 KB) |
| `data/nursing_home_survey_enforcement_details_ct/index.json` | index for 196 facility files | 81,237 bytes (81 KB) |
| `data/nursing_home_survey_enforcement_details_ct/{CCN}.json` | 196 files | 10,063,431 bytes combined (10.1 MB) |

The three statewide detail files total 11,737,832 bytes. The complete per-facility directory, including its index, totals 10,144,668 bytes. Individual facility files range from 991 to 138,900 bytes; the median is 50,545.5 bytes.

## 3. Current source coverage

The compact summary represents all 196 current facilities. Within the included rolling CMS source files:

- 191 facilities have Health citation records;
- 178 facilities have Fire Safety or Emergency Preparedness records;
- 102 facilities have Penalties or Enforcement records; and
- 5 current facilities have no records in any included survey/enforcement detail source.

The absence of source rows is not proof that a facility has never had deficiencies, penalties, or other enforcement actions. The available CMS files have defined and differing coverage windows and are not lifetime histories.

## 4. Current UI behavior

The Facility Explorer loads the compact summary by default. It does not load any of the three statewide detailed files during normal page load. Detailed findings require explicit activation of **View detailed findings**, after which only the selected facility's CCN-specific JSON file is fetched.

Successfully loaded facility details are cached in an in-memory `Map` for the browser session. Request-token checks provide stale-response protection so a delayed response for a prior selection cannot render beneath a newly selected facility. Survey and enforcement context remains separate from staffing classifications and is not an input to them.

## 5. Known caveats

- Source windows differ across the Health, Fire Safety/Emergency Preparedness, and Penalties datasets.
- The current recent window is March 31, 2023 through March 31, 2026, inclusive.
- `K-0211` and `K-0133` are official CMS Citation Descriptions lookup gaps in the current release.
- Source-provided descriptions are preserved when official lookup text is absent.
- Three duplicate penalty full-row signatures are preserved and flagged rather than silently removed.
- Fine amounts are enforcement values, not quality scores.
- Citation counts provide historical context; they are not standalone facility quality ratings.
- These files are not an exhaustive record of every state or federal survey, finding, or enforcement action.

## 6. Release verification

The automated release audit covers 12 sections and checks JSON structure, current-facility coverage, runtime-to-summary reconciliation, runtime-to-per-facility reconciliation, and exact cross-layer counts and values. It checks every one of the 196 CCN detail files, along with metadata and public-methodology semantics and the Facility Explorer's loading architecture.

The release process also includes all 18 staffing regression tests, Facility Explorer JavaScript syntax checking, source-manifest and tool-context-registry JSON parsing, and whitespace-error checks.

The initial GitHub Actions release gate for commit `f74c4f3d7692804d522ebe523cc3bde7cb9ad7ea` completed successfully on August 6, 2026. Run 31117326830 (`Nursing Home Survey Enforcement Audit`, run number 1) passed without requiring a workflow change: <https://github.com/dbeem123/DanBeem/actions/runs/31117326830>.

## 7. Current release conclusion

The current feature is internally consistent, publicly documented, and protected by both a local automated audit and a passing CI release gate. It is ready for continued public use and for routine, carefully controlled source refreshes using the companion monthly refresh runbook.
