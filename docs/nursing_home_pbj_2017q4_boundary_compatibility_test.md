# PBJ 2017Q4 Boundary Compatibility Test

Phase 10C.3 tested `PBJ_Daily_Nurse_Staffing_Q4_2017.zip` as the oldest targeted CMS Payroll-Based Journal Daily Nurse Staffing boundary quarter before a full historical archive build.

This was a compatibility test only. The public `data/nursing_home_staffing_ct.json` file was not replaced.

## Source File

| Item | Value |
|---|---|
| Uploaded file | `C:/Users/Dan/Downloads/PBJ_Daily_Nurse_Staffing_Q4_2017.zip` |
| Historical intake location | `source_data/pbj/historical/2017/PBJ_Daily_Nurse_Staffing_Q4_2017.zip` |
| ZIP entry | `PBJ_Daily_Nurse_Staffing_Q4_2017.csv` |
| SHA-256 | `86D89BF76FEC5E169492D7D8C38570F11BF4D4F6392A847486EB3D227B437AFE` |
| ZIP content assessment | Facility-level PBJ Daily Nurse Staffing file, not Employee Detail |

## Schema Compatibility

Q4 2017 uses the same 33-column daily staffing layout concept as the current PBJ files, but with older lowercase and underscore header variants.

Examples:

| Current header pattern | Q4 2017 header |
|---|---|
| `PROVNUM` | `provnum` |
| `PROVNAME` | `provname` |
| `CY_Qtr` | `cy_qtr` |
| `WorkDate` | `workdate` |
| `MDScensus` | `mdscensus` |
| `Hrs_LPNadmin` | `hrs_lpn_admin` |
| `Hrs_NAtrn` | `hrs_na_trn` |

Required fields are compatible with the generator because the generator normalizes header names before matching. All required nurse-hour, census, quarter/date, and contract-hour fields were available after normalized matching.

Contract-hour fields are also available after normalized matching, including RNDON, RN admin, RN, LPN admin, LPN, CNA, nurse aide trainee, and medication aide contract hours.

No formula, alias, extraction, encoding, or parsing changes were needed.

## Q4 2017 Connecticut Profile

| Measure | Value |
|---|---:|
| National source rows | 1,301,064 |
| Connecticut daily rows | 17,296 |
| Unique Connecticut facilities | 188 |
| Missing CT CCN rows | 0 |
| Missing CT quarter rows | 0 |
| Connecticut facility-quarter rows | 188 |
| Excluded zero-census days | 0 |
| Included nonzero-census zero-nursing-hours days | 4 |
| Malformed numeric values in boundary build | 0 |

Q4 2017 had fewer CT facilities than the current 196-facility universe. This is expected historical facility-universe movement, not a data error.

Coverage compared with the current facility universe:

| Coverage comparison | Count |
|---|---:|
| Facilities present in 2017Q4 but not current live facility set | 15 |
| Current live facilities absent in 2017Q4 | 23 |

Examples present in 2017Q4 but not current live set:

- `075013` - CRESTFIELD REHABILITATION CENTER & FENWOOD MANOR, Manchester
- `075028` - CHESTERFIELDS HEALTH CARE CENTER, Chester
- `075082` - HUGHES HEALTH AND REHABILITATION, West Hartford
- `075096` - GROVE MANOR NURSING HOME, INC, Waterbury
- `075205` - WESTFIELD CARE & REHAB CENTER, Meriden
- `075210` - WATERBURY GARDENS NURSING AND REHAB, Waterbury
- `075234` - QUINNIPAC VALLEY CENTER, Wallingford
- `075251` - TOUCHPOINTS AT FARMINGTON, Farmington
- `075280` - WESTPORT REHABILITATION COMPLEX, Westport
- `075282` - WOLCOTT VIEW MANOR, Wolcott

Examples current in the live facility set but absent in 2017Q4:

- `075011` - AUTUMN LAKE HEALTHCARE AT WINDSOR, Windsor
- `075105` - Torrington Center For Nursing & Rehabilitation LLC, Torrington
- `075135` - MASONICARE HEALTH CENTER, Wallingford
- `075159` - NORWALK CARE CENTER, Norwalk
- `075200` - Southport Center For Nursing & Rehabilitation Llc, Southport
- `075201` - WEST HAVEN CENTER FOR NURSING & REHABILITATION, West Haven
- `075219` - Waterbury Center For Nursing & Rehabilitation Llc, Waterbury
- `075235` - GUILFORD HOUSE, THE, Guilford
- `075244` - AVON HEALTH CENTER, Avon
- `075246` - WHITNEY REHABILITATION CARE CENTER, Hamden

These differences should be expected in a long historical dataset. They reinforce the need to treat facility appearance/absence as historical coverage, not as a missing-data defect.

## Temporary Boundary-Test Build

Temporary build included:

- 2017Q4
- 2024Q1
- 2024Q2
- 2024Q3
- 2024Q4
- 2025Q1
- 2025Q2
- 2025Q3
- 2025Q4

Temporary output:

- `C:/Users/Dan/AppData/Local/Temp/pbj-2017q4-boundary-12e4924aac9f4faeb997b258e5a83111/nursing_home_staffing_ct_2017q4_boundary_test.json`

Build result:

| Measure | Value |
|---|---:|
| Total source rows processed | 11,923,051 |
| Connecticut daily rows | 159,107 |
| Facilities in output | 211 |
| Facility-quarter rows | 1,740 |
| Missing required columns | 0 files |
| Malformed numeric values | 0 |
| Non-CT rows skipped | 11,763,944 |
| Missing CCNs skipped | 0 |
| Missing quarters skipped | 0 |

Rows by quarter:

| Quarter | Facility-quarter rows |
|---|---:|
| 2017Q4 | 188 |
| 2024Q1 | 196 |
| 2024Q2 | 196 |
| 2024Q3 | 194 |
| 2024Q4 | 196 |
| 2025Q1 | 195 |
| 2025Q2 | 191 |
| 2025Q3 | 192 |
| 2025Q4 | 192 |

## Enrichment Compatibility And Interpretation

Current enrichment sources attached technically by CCN:

| Enrichment | Boundary-test output count |
|---|---:|
| Provider Information matched facilities | 191 |
| PBJ facilities unmatched to Provider Information | 20 |
| Facilities with overall rating | 190 |
| Facilities with QM rating | 185 |
| Facilities with staffing rating | 188 |
| SNF Enrollment matched facilities | 186 |
| PBJ facilities unmatched to SNF Enrollments | 25 |
| Facilities with Quality Measures Claims | 191 |
| Unmatched quality-measure CCNs | 0 |

2017Q4 subset:

| Enrichment | 2017Q4 facility count |
|---|---:|
| Provider Information matched | 168 |
| SNF Enrollment matched | 166 |
| Quality Measures Claims present | 168 |

Interpretation risk: these current contextual enrichments are April/May 2026-era snapshots. They are useful for technical pipeline compatibility, but they should not be represented as historically contemporaneous with 2017Q4 staffing rows.

Future long-history data contract and UI should distinguish:

- historical quarter-specific PBJ staffing metrics
- latest/current contextual facility metadata
- historically aligned contextual data only where archived Provider Information, Quality Measures, SNF Enrollment, ownership, or other snapshots are available

Current CMS ratings, case-mix comparison points, quality measures, and affiliation fields should be labeled as current contextual CMS snapshots when displayed alongside historical PBJ staffing.

## Independent Audit

The independent calculation audit was run against the temporary boundary output and temporary input directory.

Audit result:

- Rows compared: 1,740
- Missing rows in generated JSON: 0
- Extra rows in generated JSON: 0
- Total field mismatches: 0
- CT direct-care calculations validated
- Contract staffing calculations validated
- Audit exit code: 0

Temporary audit report:

- `C:/Users/Dan/AppData/Local/Temp/pbj-2017q4-boundary-12e4924aac9f4faeb997b258e5a83111/pbj_2017q4_boundary_audit.md`

## Readiness Decision

Q4 2017 is compatible with the current generator, formulas, data contract, and audit method. It is safe to proceed to a temporary full-archive PBJ build using all available Daily Nurse Staffing files from 2017Q4 through 2025Q4.

Full-archive testing can proceed before public UI changes, as long as the output remains temporary and is not published. Before public historical release, the suite needs:

- replacement of remaining "five-quarter" wording
- persistent-pattern threshold controls that support longer windows or clearly define a recent-window mode
- trend chart/table and print readability review for many quarters
- change-over-time mode review when the endpoint gap spans many years
- methodology language distinguishing current contextual snapshots from historical PBJ quarter metrics
- possible acquisition of historical Provider Information, SNF Enrollment, Quality Measures, and ownership snapshots before making historical claims about contextual measures over time
