# PBJ 2024 Full-Year Compatibility Test

Phase 10C.2 tested Q1, Q2, and Q3 2024 historical CMS Payroll-Based Journal Daily Nurse Staffing files together with the current live PBJ files. This produced a temporary eight-quarter dataset from 2024Q1 through 2025Q4.

This was a compatibility test only. The public `data/nursing_home_staffing_ct.json` file was not replaced.

## Source Files

| Uploaded file | Historical intake location | ZIP entry | SHA-256 |
|---|---|---|---|
| `C:/Users/Dan/Downloads/PBJ_Daily_Nurse_Staffing_Q1_2024.zip` | `source_data/pbj/historical/2024/PBJ_Daily_Nurse_Staffing_Q1_2024.zip` | `PBJ_Daily_Nurse_Staffing_Q1_2024.csv` | `F5D...` |
| `C:/Users/Dan/Downloads/PBJ_Daily_Nurse_Staffing_Q2_2024.zip` | `source_data/pbj/historical/2024/PBJ_Daily_Nurse_Staffing_Q2_2024.zip` | `PBJ_Daily_Nurse_Staffing_Q2_2024.csv` | `6B1...` |
| `C:/Users/Dan/Downloads/PBJ_Daily_Nurse_Staffing_Q3_2024.zip` | `source_data/pbj/historical/2024/PBJ_Daily_Nurse_Staffing_Q3_2024.zip` | `PBJ_Daily_Nurse_Staffing_Q3_2024.csv` | `A98...` |

## Schema Compatibility

Q1 2024 and Q2 2024 both use the same 33-column PBJ Daily Nurse Staffing schema as the current live PBJ files and the previously tested Q3 2024 file.

Required fields were present in both Q1 and Q2:

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

Contract-hour fields were present in both Q1 and Q2:

- `Hrs_RNDON_ctr`
- `Hrs_RNadmin_ctr`
- `Hrs_RN_ctr`
- `Hrs_LPNadmin_ctr`
- `Hrs_LPN_ctr`
- `Hrs_CNA_ctr`
- `Hrs_NAtrn_ctr`
- `Hrs_MedAide_ctr`

No new header aliases, formula changes, encoding changes, or parsing changes were required.

Source file counts:

| Quarter | Total CSV rows | CT daily rows | CT facilities |
|---|---:|---:|---:|
| 2024Q1 | 1,330,966 | 17,836 | 196 |
| 2024Q2 | 1,325,324 | 17,836 | 196 |
| 2024Q3 | 1,338,416 | 17,848 | 194 |

## Temporary Eight-Quarter Build

Temporary build input:

- Historical Q1, Q2, and Q3 2024 CSVs extracted from ZIP files
- Current live PBJ files for 2024Q4, 2025Q1, 2025Q2, 2025Q3, and 2025Q4
- Current Provider Information, SNF Enrollments, and Quality Measures Claims files

Temporary output:

- `C:/Users/Dan/AppData/Local/Temp/pbj-2024-full-compat-5743fa4003cb41a29f071764518522f5/nursing_home_staffing_ct_2024_full_compat.json`

Build result:

| Measure | Value |
|---|---:|
| Total source rows processed | 10,621,987 |
| Connecticut daily rows | 141,811 |
| Facilities in output | 196 |
| Facility-quarter rows | 1,552 |
| Missing required columns | 0 files |
| Malformed numeric values | 0 |
| Non-CT rows skipped | 10,480,176 |
| Missing CCNs skipped | 0 |
| Missing quarters skipped | 0 |

Quarter sequence:

- 2024Q1
- 2024Q2
- 2024Q3
- 2024Q4
- 2025Q1
- 2025Q2
- 2025Q3
- 2025Q4

Rows by quarter:

| Quarter | Facility-quarter rows |
|---|---:|
| 2024Q1 | 196 |
| 2024Q2 | 196 |
| 2024Q3 | 194 |
| 2024Q4 | 196 |
| 2025Q1 | 195 |
| 2025Q2 | 191 |
| 2025Q3 | 192 |
| 2025Q4 | 192 |

Facilities by available-quarter count:

| Available quarters | Facility count |
|---:|---:|
| 4 | 1 |
| 5 | 2 |
| 6 | 1 |
| 7 | 4 |
| 8 | 188 |

## Data Quality Observations

| Quarter | Excluded zero-census days | Included zero-nursing-hours days |
|---|---:|---:|
| 2024Q1 | 0 | 0 |
| 2024Q2 | 0 | 61 |
| 2024Q3 | 0 | 13 |
| 2024Q4 | 0 | 150 |
| 2025Q1 | 11 | 1 |
| 2025Q2 | 15 | 47 |
| 2025Q3 | 0 | 0 |
| 2025Q4 | 15 | 5 |

The historical Q1-Q3 2024 files introduced no missing required columns and no malformed numeric values.

## Enrichment Check

Existing enrichment continued to attach cleanly.

| Enrichment | Count |
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

## Independent Audit

The independent audit script was run against the temporary eight-quarter output and temporary input directory.

Audit result:

- Rows compared: 1,552
- Missing rows in generated JSON: 0
- Extra rows in generated JSON: 0
- Total field mismatches: 0
- Exit code: 0

Temporary audit report:

- `C:/Users/Dan/AppData/Local/Temp/pbj-2024-full-compat-5743fa4003cb41a29f071764518522f5/pbj_2024_full_compat_audit.md`

## UI Assumption Review

No generator or data-contract break was found. Longer-history publication should still wait for a light UI wording and controls pass.

Items to update before publishing longer history:

- Replace remaining "five-quarter" labels with "available-quarter," "selected-window," or dynamic quarter-window wording.
- Facility trend chart and quarterly table are data-driven and should handle eight quarters, but chart width and label density should be browser-reviewed.
- Persistent-pattern threshold controls currently support 2, 3, 4, and 5 quarters. Longer history needs either a dynamic threshold range or explicit "recent 5" versus "full available history" behavior.
- Change-over-time endpoint logic uses earliest-to-latest dynamically and handled the eight-quarter temporary output conceptually.
- Ownership / Affiliation trend tables use available quarters dynamically but captions/action text still say five-quarter in places.
- Print/export outputs should be checked for readability when eight-quarter tables print or export.
- Source-currency text still shows the latest PBJ quarter and contextual CMS snapshots; it does not claim the full data window.

## Recommendation

Q1, Q2, and Q3 2024 are compatible with the current generator, formulas, audit approach, and data contract. It is safe to proceed to an oldest-boundary compatibility test using `PBJ_Daily_Nurse_Staffing_Q4_2017.zip`.

Do not publish the eight-quarter temporary output until UI wording and persistent-pattern threshold behavior are adjusted for longer history.
