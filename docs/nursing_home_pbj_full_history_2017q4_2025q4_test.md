# PBJ Full-History Temporary Compatibility Test, 2017Q4-2025Q4

Phase 10C.4 tested a complete temporary CMS PBJ Daily Nurse Staffing archive build for Connecticut nursing homes from `2017Q4` through `2025Q4`.

This was a technical compatibility and publication-readiness test only. It did not replace `data/nursing_home_staffing_ct.json`, did not change public source-currency wording, and did not publish historical data in the live application.

## Source Files And Quarter Coverage

Target public-history test window: `2017Q4` through `2025Q4`.

- Expected target quarters: 33
- Target quarters found and staged: 33
- Missing target quarters: 0
- Duplicate target quarters: 0
- Incorrect file types found in the target window: 0
- Temporary build input directory: `%TEMP%/pbj-full-history-2017q4-2025q4-input`
- Temporary output: `data/testing/nursing_home_staffing_ct_2017q4_2025q4_full_history_test.json`

The 2017Q1, 2017Q2, and 2017Q3 ZIPs are preserved in `source_data/pbj/historical/2017/` because they were supplied, but they were outside the planned 2017Q4-2025Q4 test window and were not included in this build.

Current live PBJ paths for 2024Q4 through 2025Q4 were preserved.

## Schema Compatibility

All 33 target quarters contain the required PBJ Daily Nurse Staffing facility-level fields and contract-hour fields. No Employee Detail files were included.

| Schema family | Quarters | Result |
|---|---:|---|
| Current title/camel-case 33-column PBJ daily staffing schema | 25 | Compatible |
| Older/lowercase 33-column PBJ daily staffing schema | 8 | Compatible through existing normalized lookup |

Older/lowercase schema quarters were: `2017Q4`, `2018Q4`, `2019Q1`, `2019Q2`, `2019Q3`, `2019Q4`, `2020Q2`, and `2020Q3`.

`2017Q4` also used older underscore variants such as `hrs_lpn_admin` and `hrs_na_trn`. The existing generator normalization resolved these without formula, alias, parsing, extraction, or encoding changes.

The full quarter-by-quarter schema inspection is saved in `data/testing/nursing_home_pbj_full_history_schema_summary.json`.

## Temporary Build Counts

| Measure | Count |
|---|---:|
| Total national PBJ daily rows processed | 44,040,864 |
| Connecticut PBJ daily rows processed | 599,930 |
| Unique Connecticut CCNs represented | 216 |
| Generated Connecticut facility-quarter rows | 6,569 |
| Expected quarters | 33 |
| Actual quarters | 33 |

### Rows By Quarter

| Quarter | Facility-quarter rows |
|---|---:|
| 2017Q4 | 188 |
| 2018Q1 | 203 |
| 2018Q2 | 181 |
| 2018Q3 | 210 |
| 2018Q4 | 211 |
| 2019Q1 | 211 |
| 2019Q2 | 211 |
| 2019Q3 | 211 |
| 2019Q4 | 210 |
| 2020Q1 | 154 |
| 2020Q2 | 203 |
| 2020Q3 | 204 |
| 2020Q4 | 205 |
| 2021Q1 | 208 |
| 2021Q2 | 204 |
| 2021Q3 | 203 |
| 2021Q4 | 201 |
| 2022Q1 | 202 |
| 2022Q2 | 200 |
| 2022Q3 | 200 |
| 2022Q4 | 202 |
| 2023Q1 | 202 |
| 2023Q2 | 198 |
| 2023Q3 | 197 |
| 2023Q4 | 198 |
| 2024Q1 | 196 |
| 2024Q2 | 196 |
| 2024Q3 | 194 |
| 2024Q4 | 196 |
| 2025Q1 | 195 |
| 2025Q2 | 191 |
| 2025Q3 | 192 |
| 2025Q4 | 192 |

## Data Quality Observations

| Observation | Count |
|---|---:|
| Missing required columns by file | 0 |
| Malformed numeric values | 0 |
| Skipped CT rows with missing CCN | 0 |
| Skipped CT rows with missing quarter | 0 |
| Facilities present in all 33 quarters | 77 |
| Facilities appearing historically but not in the latest quarter | 24 |
| Latest-quarter facilities absent from 2017Q4 | 23 |
| Facilities with missing quarters inside apparent active PBJ span | 121 |
| CCNs with raw PBJ provider name or city changes | 112 |

Facility-universe changes, missing historical quarters, and name changes are expected continuity issues for a long public history. They should not be treated as calculation errors.

Examples of raw PBJ provider-name changes include:

- `075334`: VERNON MANOR HEALTH CARE CENTER; VERNON MANOR HEALTH CARE CENTER, LLC; VERNON REHABILITATION AND HEALTHCARE CENTER; VERNON  REHABILITATION AND HEALTHCARE CENTER
- `075031`: GLEN HILL CENTER; GLEN HILL REHABILITATION & NURSING CENTER; AUTUMN LAKE HEALTHCARE AT GLEN HILL
- `075060`: SALMON BROOK CENTER; SALMON BROOK REHAB AND NURSING; CIVITA CARE CENTER AT SALMON BROOK

## Enrichment Compatibility And Interpretation

The temporary build continued attaching current contextual CMS files for pipeline compatibility:

- Provider Information: April 2026
- Quality Measures Claims: April 2026
- SNF Enrollments: May 2026

Technical merge behavior remained stable:

| Enrichment measure | Count |
|---|---:|
| PBJ facilities matched to Provider Information | 191 |
| PBJ facilities unmatched to Provider Information | 25 |
| PBJ facilities matched to SNF Enrollments | 186 |
| PBJ facilities unmatched to SNF Enrollments | 30 |
| Facilities with Quality Measures Claims | 191 |
| Facilities with CMS Overall Rating | 190 |
| Facilities with CMS QM Rating | 185 |
| Facilities with CMS Staffing Rating | 188 |

Interpretation warning: these contextual files are current CMS snapshots and are not historically aligned to every PBJ staffing quarter. A public long-history release should distinguish historical PBJ-derived staffing metrics from current contextual facility, rating, quality-measure, and affiliation snapshots.

## Independent Audit Results

The independent calculation audit recomputed staffing metrics from the temporary PBJ input directory and compared them to the temporary full-history output.

| Audit item | Result |
|---|---:|
| Rows compared | 6,569 |
| Missing generated rows | 0 |
| Extra generated rows | 0 |
| Total field mismatches | 0 |
| Audit exit code | 0 |

The audit validated resident days, RN/LPN/aide HPRD, total nurse HPRD, contract staff percentage, CT direct-care HPRD estimate, CT licensed HPRD estimate, and CT comparison flags for the temporary output.

The temporary audit report is saved as `data/testing/nursing_home_pbj_full_history_2017q4_2025q4_audit.md`.

## Test-Only PBJ Screening Counts

These counts are test-only and PBJ-derived. They should not be shown publicly until the long-history product behavior and methodology language are updated.

| Year | Facility-quarter rows | Unique facilities | Below CT 3.00 direct-care point | Below CT 0.84 licensed point | Contract staff >= 10% | Contract staff >= 20% |
|---|---:|---:|---:|---:|---:|---:|
| 2017 | 188 | 188 | 25 | 12 | 3 | 0 |
| 2018 | 805 | 215 | 133 | 60 | 11 | 2 |
| 2019 | 843 | 214 | 175 | 59 | 19 | 0 |
| 2020 | 766 | 213 | 120 | 28 | 26 | 1 |
| 2021 | 816 | 209 | 238 | 79 | 91 | 21 |
| 2022 | 804 | 205 | 241 | 78 | 203 | 67 |
| 2023 | 795 | 203 | 194 | 57 | 226 | 70 |
| 2024 | 782 | 196 | 164 | 43 | 165 | 53 |
| 2025 | 770 | 195 | 127 | 28 | 146 | 50 |
| All available quarters | 6,569 | 216 | 1,417 | 444 | 890 | 264 |

### Repeated Pattern Test Counts

Latest 4 quarters (`2025Q1`-`2025Q4`), requiring all four quarters present:

| Pattern | Eligible facilities | At least 1 match | At least 2 matches | All 4 quarters |
|---|---:|---:|---:|---:|
| Below CT 3.00 direct-care point | 190 | 56 | 32 | 15 |
| Below CT 0.84 licensed point | 190 | 13 | 7 | 2 |
| Contract staff >= 10% | 190 | 53 | 44 | 18 |
| Contract staff >= 20% | 190 | 21 | 15 | 6 |

Latest 8 quarters (`2024Q1`-`2025Q4`), requiring all eight quarters present:

| Pattern | Eligible facilities | At least 1 match | At least 2 matches | At least 4 matches | All 8 quarters |
|---|---:|---:|---:|---:|---:|
| Below CT 3.00 direct-care point | 188 | 76 | 50 | 33 | 9 |
| Below CT 0.84 licensed point | 188 | 26 | 13 | 5 | 1 |
| Contract staff >= 10% | 188 | 77 | 59 | 39 | 10 |
| Contract staff >= 20% | 188 | 29 | 21 | 15 | 2 |

All available quarters, with a variable denominator by facility:

| Pattern | Eligible facilities | At least 4 matching quarters | At least half of available quarters | At least 75% of available quarters | All available quarters |
|---|---:|---:|---:|---:|---:|
| Below CT 3.00 direct-care point | 216 | 98 | 39 | 18 | 2 |
| Below CT 0.84 licensed point | 216 | 37 | 7 | 2 | 1 |
| Contract staff >= 10% | 216 | 87 | 12 | 1 | 0 |
| Contract staff >= 20% | 216 | 29 | 0 | 0 | 0 |

### Long-Range Endpoint Changes

For facilities with both 2017Q4 and 2025Q4 present, the largest CT direct-care HPRD declines were:

| CCN | Facility | 2017Q4 | 2025Q4 | Change |
|---|---|---:|---:|---:|
| 075416 | CANDLEWOOD REHABILITATION AND HEALTHCARE CENTER | 4.35 | 2.97 | -1.38 |
| 075439 | BRADLEY HOME INFIRMARY/PAVILION | 4.75 | 3.49 | -1.26 |
| 075084 | VILLA MARIA NURSING AND REHABILITATION COMMUNITY | 4.26 | 3.05 | -1.21 |
| 075317 | WILTON MEADOWS HEALTH CARE CENTER | 4.54 | 3.34 | -1.20 |
| 075034 | CAROLTON CHRONIC & CONVALESCENT HOSPITAL INC | 4.73 | 3.54 | -1.19 |

The largest endpoint increases were:

| CCN | Facility | 2017Q4 | 2025Q4 | Change |
|---|---|---:|---:|---:|
| 075343 | JEROME HOME | 1.50 | 5.26 | 3.76 |
| 075441 | SPRINGS AT EAST HILL, THE | 4.90 | 8.24 | 3.34 |
| 075383 | SEABURY | 2.41 | 4.31 | 1.90 |
| 075362 | EVERGREEN WOODS | 3.28 | 5.18 | 1.90 |
| 075113 | GREENTREE MANOR NURSING AND REHABILITATION CENTER | 2.13 | 3.92 | 1.79 |

Endpoint changes are descriptive screening context only. They do not explain why staffing changed.

## Historical Context Methodology Recommendation

Future long-history publication should separate three categories:

1. Quarter-specific historical measures currently supported:
   - PBJ staffing hours and resident days
   - PBJ-derived HPRD metrics
   - PBJ-derived contract staffing percentage
   - PBJ-derived CT direct-care and licensed HPRD comparison estimates

2. Current contextual snapshots, not historically aligned:
   - April 2026 Provider Information facility/rating fields
   - April 2026 CMS case-mix comparison point
   - April 2026 Quality Measures Claims values
   - May 2026 SNF Enrollment affiliation context

3. Historically aligned future context requiring archived snapshots or event data:
   - historic ratings
   - historic case-mix benchmark comparisons
   - historic QMs
   - historic ownership/affiliation periods
   - SFF/Candidate status over time
   - CHOW/ownership changes
   - CT DPH leadership timeline
   - CT DSS rates, census, and financial context

The future data contract should consider separating `facility_current_context`, `facility_quarterly_staffing`, and `historically_aligned_events_or_snapshots`. That separation would reduce the risk that current 2026 context appears to describe older PBJ quarters.

Do not calculate long-range historical persistence against CMS case-mix comparison points until historically aligned Provider Information snapshots are available.

## Recommended Public UI Behavior For Full History

Facility Explorer:

- Default the chart to the latest 8 quarters.
- Offer an explicit full-history view or full-history CSV.
- Keep current CMS ratings, QMs, affiliation, and case-mix context in a clearly labeled current-context panel.
- Do not imply current CMS context applied to older PBJ staffing quarters.

Statewide Facility Staffing Comparison:

- Keep the default as a latest-quarter tool.
- Consider a future quarter selector for past-quarter statewide comparison.
- Clearly distinguish the selected PBJ quarter from current contextual snapshot fields.

Staffing Change Over Time:

- Replace automatic earliest-to-latest behavior with user-selected start and end quarters before publishing full history.
- Offer presets such as latest year, latest two years, and full available history.

Persistent Multi-Quarter Staffing Patterns:

- Add selectable windows such as latest 4 quarters, latest 8 quarters, and full available history.
- Add threshold options based on both count of quarters and share of eligible quarters.
- Retain 2+/3+/4+/5 logic only when the selected window is short enough for that framing to remain clear.

Ownership / Affiliation Staffing Explorer:

- Default to latest-quarter/current-view analysis until historic affiliation snapshots exist.
- If historical PBJ is shown by affiliation, label it as historical PBJ staffing among facilities currently associated with that CMS affiliation entity based on the May 2026 enrollment snapshot.

Print and export:

- Keep printed reports concise by default.
- Include source-period and current-context caveats in any report using historical PBJ.
- Make full-history CSV export available separately from shorter on-screen default views.

Homepage and methodology:

- Replace "five-quarter" wording with flexible language such as "available PBJ quarters" or "selected reporting window."
- Disclose the PBJ historical coverage and current contextual snapshot limits.

## Minimum Work Before Publishing Full History

| Item | Classification |
|---|---|
| Replace hard-coded "five-quarter" wording | Required before public publish |
| Update source-currency language for PBJ coverage | Required before public publish |
| Add methodology disclosure distinguishing historical PBJ from current CMS snapshots | Required before public publish |
| Default facility chart to recent quarters with optional full-history view | Required before public publish |
| Review detailed table and print readability for 33 quarters | Required before public publish |
| Add change-over-time start/end quarter or preset-window selection | Required before public publish |
| Add persistent-pattern selected-window logic and threshold redesign | Required before public publish |
| Label affiliation analyses as current-affiliation context unless historic affiliation snapshots exist | Required before public publish |
| Separate current facility context from historical quarter rows in the data contract | Strongly recommended before public publish |
| Add quarter selector to statewide comparison | Strongly recommended before public publish |
| Acquire historically aligned Provider Information, QMs, and affiliation snapshots | May be deferred if current-context limits are clear |

## Readiness Decision

Historical PBJ is technically ready for a later public integration phase. The full archive is schema-compatible, generator-compatible, and audit-compatible without calculation changes.

It should not be published until the UI, methodology, source-currency language, and data-contract framing are updated for long-history use.
