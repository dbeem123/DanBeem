# PBJ Q3 2024 Compatibility Test

Phase 10C.1 tested `PBJ_Daily_Nurse_Staffing_Q3_2024.zip` as the first historical CMS Payroll-Based Journal Daily Nurse Staffing backfill candidate.

This was a compatibility test only. The public `data/nursing_home_staffing_ct.json` file was not replaced.

## Source File

| Item | Value |
|---|---|
| Uploaded file | `C:/Users/Dan/Downloads/PBJ_Daily_Nurse_Staffing_Q3_2024.zip` |
| Historical intake location | `source_data/pbj/historical/2024/PBJ_Daily_Nurse_Staffing_Q3_2024.zip` |
| ZIP entry | `PBJ_Daily_Nurse_Staffing_Q3_2024.csv` |
| CSV rows | 1,338,416 |
| Connecticut daily rows | 17,848 |
| Connecticut facilities in Q3 2024 | 194 |

## Schema Check

The Q3 2024 CSV has the same 33-column schema as the currently integrated PBJ Daily Nurse Staffing files.

Required fields present:

- `PROVNUM`
- `PROVNAME`
- `CITY`
- `STATE`
- `CY_Qtr`
- `WorkDate`
- `MDScensus`
- `Hrs_RNDON`
- `Hrs_RNadmin`
- `Hrs_RN`
- `Hrs_LPNadmin`
- `Hrs_LPN`
- `Hrs_CNA`
- `Hrs_NAtrn`
- `Hrs_MedAide`

Contract-hour fields present:

- `Hrs_RNDON_ctr`
- `Hrs_RNadmin_ctr`
- `Hrs_RN_ctr`
- `Hrs_LPNadmin_ctr`
- `Hrs_LPN_ctr`
- `Hrs_CNA_ctr`
- `Hrs_NAtrn_ctr`
- `Hrs_MedAide_ctr`

Conclusion: no formula changes or new header aliases are required for Q3 2024. The current generator reads CSV files, not ZIP files directly, so the ZIP must be extracted or staged as a CSV before a future build.

## Temporary Six-Quarter Build

Temporary build input:

- Extracted Q3 2024 CSV
- Current live PBJ files for 2024Q4, 2025Q1, 2025Q2, 2025Q3, 2025Q4
- Current Provider Information, SNF Enrollments, and Quality Measures Claims files

Temporary output:

- `C:/Users/Dan/AppData/Local/Temp/pbj-q3-2024-compat-51633213edfa4bbf8e7d0fb862700ddc/nursing_home_staffing_ct_q3_2024_compat.json`

Build result:

| Measure | Value |
|---|---:|
| Total source rows processed | 7,965,697 |
| Connecticut daily rows | 106,139 |
| Facilities in output | 196 |
| Facility-quarter rows | 1,160 |
| Q3 2024 facility-quarter rows | 194 |
| Missing required columns | 0 files |
| Malformed numeric values | 0 |
| Q3 2024 excluded zero-census days | 0 |
| Q3 2024 included zero-nursing-hours days | 13 |

Quarter sequence expanded as expected:

- Before: 2024Q4 through 2025Q4
- Temporary compatibility build: 2024Q3 through 2025Q4

Rows by quarter:

| Quarter | Facility-quarter rows |
|---|---:|
| 2024Q3 | 194 |
| 2024Q4 | 196 |
| 2025Q1 | 195 |
| 2025Q2 | 191 |
| 2025Q3 | 192 |
| 2025Q4 | 192 |

Facilities by available-quarter count in the temporary build:

| Available quarters | Facility count |
|---:|---:|
| 2 | 1 |
| 3 | 2 |
| 4 | 1 |
| 5 | 4 |
| 6 | 188 |

## Enrichment Check

Facility-level enrichment continued to attach cleanly using existing CCN merge logic.

Overall output enrichment:

| Enrichment | Value |
|---|---:|
| Provider Information matched facilities | 191 |
| PBJ facilities unmatched to Provider Information | 5 |
| Facilities with overall rating | 190 |
| Facilities with QM rating | 185 |
| Facilities with staffing rating | 188 |
| SNF Enrollment matched facilities | 186 |
| PBJ facilities unmatched to SNF Enrollments | 10 |
| Facilities with Quality Measures Claims | 191 |
| Unmatched quality-measure CCNs | 0 |

Q3 2024 facility subset:

| Enrichment | Q3 2024 facility count |
|---|---:|
| Provider Information matched | 189 |
| SNF Enrollment matched | 184 |
| Quality Measures Claims present | 189 |

Q3 2024 provider-unmatched examples:

- `075001`
- `075351`
- `075415`
- `075432`
- `075441`

These are consistent with existing unmatched PBJ facility behavior and do not indicate a Q3 schema problem.

## Independent Audit

The independent audit script was run against the temporary six-quarter output and temporary input directory.

Audit result:

- Rows compared: 1,160
- Missing rows in generated JSON: 0
- Extra rows in generated JSON: 0
- Total field mismatches: 0
- Exit code: 0

Temporary audit report:

- `C:/Users/Dan/AppData/Local/Temp/pbj-q3-2024-compat-51633213edfa4bbf8e7d0fb862700ddc/q3_2024_compat_audit.md`

## UI Assumption Review

No data-contract failure was found, but several current UI labels assume a five-quarter live window:

- Facility Explorer CSV status says "Facility five-quarter trend CSV prepared."
- Change Over Time print caveat says "full five-quarter context."
- Persistent Patterns has a filter label for "complete five-quarter history only."
- Persistent Patterns CSV field is named `complete_five_quarter_history`.
- Ownership / Affiliation captions and action text refer to "five-quarter" and "5-quarter" trend summaries.
- Persistent-pattern thresholds currently support 2, 3, 4, and 5 quarters, not 6+.

Functional assumptions that appear compatible with six quarters:

- Facility trend chart plots the available facility-quarter rows dynamically.
- Facility quarterly staffing table uses the dataset quarter list dynamically.
- Change Over Time endpoint logic uses earliest and latest available quarters dynamically.
- Ownership / Affiliation trend table uses dataset quarters dynamically.
- Source-currency text still identifies the latest PBJ quarter; it does not claim the full quarter window.

Before a public longer-history release, wording and threshold controls should be generalized from "five-quarter" to "available-quarter" or "selected-window" language.

## Recommendation

Q3 2024 is fully schema-compatible with the current PBJ formulas, aliases, generator output contract, and audit approach. It is safe to proceed to a one-year historical PBJ test, preferably adding 2024Q1 and 2024Q2 next before moving further back.

Do not publish the six-quarter data yet without first deciding whether to update the UI wording and persistent-pattern threshold model for longer history.
