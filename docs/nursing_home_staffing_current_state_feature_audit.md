# Connecticut Nursing Home Staffing / Ownership Current-State Feature Audit

Generated: 2026-05-19

## Executive Summary

The Connecticut Nursing Home Staffing Explorer and Ownership/Affiliation Staffing Explorer are present and working in the current repository state. The current implementation includes the generated five-quarter Connecticut PBJ export, Provider Information enrichment, SNF Enrollment affiliation enrichment, CT direct-care comparison metrics, front-end facility and affiliation explorers, generator unit tests, and an independent calculation audit.

Current audit conclusion: **feature-complete relative to the work completed so far, with no observed calculation or route regressions.**

Important caveat: this audit verifies source code, generated data shape, command checks, static routes, and current documentation. It does not replace manual browser review for layout, readability, keyboard ergonomics, or visual regression across screen sizes.

## Evidence Sources

- Git commit history:
  - `ed22513 Add Nursing Home Staffing Explorer tool with mock data and metrics display`
  - `a3846a0 Add unit tests for nursing home staffing generator and create ownership & staffing explorer HTML`
- Current repository files and generated data:
  - `data/nursing_home_staffing_ct.json`
  - `data/nursing_home_staffing_mock.json`
  - `scripts/build_nursing_home_staffing_ct.py`
  - `scripts/test_build_nursing_home_staffing_ct.py`
  - `scripts/audit_nursing_home_staffing_ct.py`
  - `Assets/nursing-home-staffing.js`
  - `Assets/nursing-home-ownership-staffing.js`
  - `tools/nursing-home-staffing-explorer.html`
  - `tools/nursing-home-ownership-staffing-explorer.html`
  - `docs/nursing_home_staffing_data_contract.md`
  - `docs/nursing_home_staffing_calculation_audit.md`
  - `README.md`
  - `index.html`
  - `data/current_tool_context_registry.json`
- Verification commands and static HTTP checks run during this audit.

## Feature History Reconstructed From Git And Current Diff State

The committed history has two major staffing-specific commits. Later phases are present in the current repository state and are covered by current-file evidence and successful checks.

| Phase / Feature | Evidence From History Or Current State | Status |
|---|---|---|
| Phase 1 facility staffing explorer shell | Commit `ed22513`; files `tools/nursing-home-staffing-explorer.html`, `Assets/nursing-home-staffing.js`, `data/nursing_home_staffing_mock.json`, README/index/context registry updates | PASS |
| Normalized JSON contract | Commit `ed22513` began mock contract; current `docs/nursing_home_staffing_data_contract.md` documents generated contract and field map | PASS |
| Live PBJ CSV generator | Commit `a3846a0`; current `scripts/build_nursing_home_staffing_ct.py` reads `source_data/pbj/*.csv` and emits `data/nursing_home_staffing_ct.json` | PASS |
| Zero-census / zero-hours methodology alignment | Current generator `load_pbj_rows`; tests `test_zero_census_days_are_excluded_from_denominator_and_numerator` and `test_zero_nursing_hours_days_are_included_when_census_is_nonzero`; audit report confirms counters | PASS |
| Provider Information merge | Current `load_provider_info` and `merge_provider_metadata`; generated `data_quality.matched_facility_count = 191` | PASS |
| Case-mix benchmark enrichment | Current generator copies case-mix benchmark fields into each row's `benchmarks`; 933 facility-quarter rows have benchmark availability | PASS |
| Five-quarter PBJ trend expansion | Generated rows include `2024Q4`, `2025Q1`, `2025Q2`, `2025Q3`, `2025Q4`; current facility explorer builds dataset quarter sequence | PASS |
| Missing-quarter display handling | `Assets/nursing-home-staffing.js` `renderQuarterlyTable` creates placeholder rows and missing-quarter note | PASS |
| Benchmark explanation / actual-vs-benchmark comparison | Facility explorer `getBenchmarkComparison`, `renderBenchmarkExplainer`; ownership explorer aggregate benchmark comparison | PASS |
| SNF Enrollments ownership / affiliation merge | Current `load_snf_enrollments`, `merge_snf_enrollment_metadata`; generated `matched_snf_enrollment_facility_count = 186` | PASS |
| Ownership / affiliation staffing explorer page | Current `tools/nursing-home-ownership-staffing-explorer.html` and `Assets/nursing-home-ownership-staffing.js`; route check returned 200 | PASS |
| Facility deep links via `'ccn=` | `Assets/nursing-home-staffing.js` `getFacilityIdFromUrl`; ownership facility links use `nursing-home-staffing-explorer.html'ccn=...` | PASS |
| Connecticut direct-care comparison metrics and flags | Current generator constants/formulas, generated metric fields, facility/ownership UI sections, data contract docs | PASS |
| Independent calculation audit script and audit report | Current `scripts/audit_nursing_home_staffing_ct.py`; `docs/nursing_home_staffing_calculation_audit.md`; command run passed with 0 discrepancies | PASS |

## Current Generated Data Snapshot

| Item | Current Value | Status |
|---|---:|---|
| `data/nursing_home_staffing_ct.json` exists | yes | PASS |
| Facilities | 196 | PASS |
| Facility-quarter rows | 966 | PASS |
| Quarters represented | `2024Q4`, `2025Q1`, `2025Q2`, `2025Q3`, `2025Q4` | PASS |
| Latest quarter | `2025Q4` | PASS |
| Source datasets listed | 3 | PASS |
| Provider Information matches | 191 | PASS |
| SNF Enrollment matches | 186 | PASS |
| Rows with case-mix benchmark availability | 933 | PASS |
| Facilities with nonblank affiliation name | 108 | PASS |
| Unique affiliation entities | 19 | PASS |
| Facility-quarter rows below CT 3.00 total direct-care point | 163 | PASS |
| Facility-quarter rows below CT 0.84 licensed point | 38 | PASS |
| `2025Q4` rows below CT 3.00 total direct-care point | 27 | PASS |
| `2025Q4` rows below CT 0.84 licensed point | 7 | PASS |

Note: 190 facilities have all five quarters represented; 6 facilities have fewer than five facility-quarter rows in the generated PBJ history. The UI intentionally displays missing-quarter placeholders rather than treating missing data as zero.

## Feature Inventory

| Feature Area | Intended Purpose | Status | Current Evidence | Notes / Risks |
|---|---|---|---|---|
| PBJ multi-file support | Read multiple CMS PBJ Daily Nurse Staffing CSVs into one Connecticut export | PASS | `scripts/build_nursing_home_staffing_ct.py` `load_pbj_rows`; generated `data_quality.input_files` lists five PBJ files | Source CSVs are local/manual inputs; refresh process remains manual |
| Provider Information CSV support | Add standardized facility metadata and case-mix benchmark fields by CCN | PASS | `load_provider_info`, `merge_provider_metadata`; fields in `facilities[]` and `benchmarks` | Provider Info reporting date may not align perfectly with every PBJ quarter; documented as contextual |
| SNF Enrollments CSV support | Add legal organization and affiliation context by CCN | PASS | `load_snf_enrollments`, `merge_snf_enrollment_metadata`; facility fields `enrollment_*`, `affiliation_entity_*` | Affiliation entity is screening context, not proof of common day-to-day control |
| Source metadata | Preserve source names/releases/freshness in generated output | PASS | `data/nursing_home_staffing_ct.json` `sources[]` contains PBJ, Provider Information, SNF Enrollments | Source freshness currently reflects generated/local file metadata, not live CMS polling |
| Top-level data contract | Provide stable static JSON for browser tools | PASS | Generated keys: `schema_version`, `dataset_type`, `generated_at`, `reporting_period`, `sources`, `facilities`, `facility_quarterly_staffing`, `data_quality`, `field_map` | Contract is static-file oriented by design |
| Facilities populated | Browser can build facility directory and summaries | PASS | `facilities[]` count 196; required provider/enrollment keys present | Some facilities lack Provider Info or SNF Enrollment matches |
| Quarterly staffing rows populated | Browser can render trends and selected quarter metrics | PASS | `facility_quarterly_staffing[]` count 966 | Missing rows are real missing source rows, not zeroes |
| Data quality block | Track source counts and row-inclusion counters | PASS | `data_quality` includes row counts, skipped rows, precision, match counts, malformed numeric values | Dataset-level zero-census counts are available through row-level sums and verified by audit report |
| Field map | Explain output fields and formulas | PASS | `field_map` includes staffing, benchmark, ownership, and CT comparison fields | Keep updated if new metrics are added |
| RN HPRD | PBJ RN categories divided by resident days | PASS | Generator formula uses `Hrs_RNDON + Hrs_RNadmin + Hrs_RN`; audit compared all 966 rows | Includes RN admin/DON by design for general PBJ RN metric |
| LPN/LVN HPRD | PBJ LPN categories divided by resident days | PASS | Generator formula uses `Hrs_LPNadmin + Hrs_LPN`; audit compared all 966 rows | Includes LPN admin by design for general PBJ LPN metric |
| Nurse aide HPRD | PBJ aide categories divided by resident days | PASS | Generator formula uses `Hrs_CNA + Hrs_NAtrn + Hrs_MedAide`; audit compared all 966 rows | None observed |
| Total nurse HPRD | General PBJ total nurse staffing metric | PASS | Generator sums RN, LPN/LVN, and aide categories; audit confirmed all rows | Not replaced by CT direct-care metric |
| Contract staff percent | Contract nurse category hours divided by total nurse category hours | PASS | `contract_staff_pct`; audit confirmed all rows | Null behavior depends on contract columns/values |
| Average resident census | Simple average of included daily `MDScensus` values | PASS | Generator and audit confirm; output precision 1 decimal | It is not `resident_days / calendar days`; docs identify method |
| Resident-day inclusion logic | Exclude missing/malformed/nonpositive census days; include zero-hour days when census positive | PASS | Generator, tests, audit report | Verified counts: 41 excluded zero-census days, 203 included zero-nursing-hours days |
| Case-mix benchmark fields | Provide contextual Provider Information benchmark values | PASS | `benchmarks.case_mix_*`, `case_mix_benchmark_available`, source note | Contextual only; not legal minimum and not proof of staffing sufficiency |
| Facility explorer route | Static facility-level staffing explorer | PASS | `tools/nursing-home-staffing-explorer.html`; HTTP 200 | Manual browser review still recommended |
| CT JSON before mock fallback | Prefer generated CT export but allow development mock fallback | PASS | `Assets/nursing-home-staffing.js` `dataPaths` lists CT JSON before mock | Mock copy may be stale relative to CT export; acceptable fallback only |
| Dataset hero / scope copy | Explain screening scope and source | PASS | `renderDatasetSummary`; page warning copy | `index.html` card still says "mock quarterly PBJ" for staffing explorer, which is slightly stale |
| Facility search/filter | Search facilities by name/city/state/CCN | PASS | `filterFacilities`, `populateFacilitySelect` | Browser interaction not manually exercised during this audit |
| Facility selection | Update summary, metrics, table, interpretation | PASS | `renderFacility`; select change listener | Browser interaction not manually exercised during this audit |
| Provider metadata summary | Show CCN, census, resident days, beds, ownership | PASS | `renderFacilitySummary` | Provider fields depend on successful Provider Info match |
| Ownership / affiliation context block | Show legal organization, DBA, affiliation entity, enrollment type | PASS | `renderOwnershipContext` | Only appears when fields exist |
| Five-quarter comparison table | Display all dataset quarters for selected facility | PASS | `getDatasetQuarters`, `renderQuarterlyTable` | Some facilities have missing quarters; placeholders are present |
| Missing-quarter placeholders | Prevent false continuity in trends | PASS | `missing-quarter-row`, missing-quarter note in `renderQuarterlyTable` | None observed |
| Metric cards | Show total/RN/LPN/nurse aide/contract metrics | PASS | `metricDefinitions`, `renderMetricCards` | LPN card present through metric definitions |
| Case-mix benchmark card | Show benchmark only when available | PASS | `benchmark.case_mix_benchmark_available` branch | Facilities without benchmark do not show card |
| Actual-vs-benchmark text | Explain difference from case-mix benchmark | PASS | `getBenchmarkComparison`; ownership `averageActualMinusBenchmark` | Uses total nurse HPRD vs Provider Info benchmark |
| Benchmark caution language | Avoid overclaiming legal/care findings | PASS | `benchmark-explainer`; source note section; interpretation language | Keep this language if design changes |
| CT Direct-Care Staffing Comparison card | Show CT screening estimate and comparison points | PASS | `renderCtDirectCareComparison`; `.ct-comparison-card` styles | Browser layout should be manually reviewed on mobile/wide tables |
| Below CT comparison wording | Neutral notation, not "violation" | PASS | `formatCtComparisonStatus`; ownership table text | Some ownership compact text says `At/above CT ... point`; acceptable but should remain cautious |
| Interpretation copy | "Shows / may suggest / cannot prove" framing | PASS | `buildInterpretation`; HTML interpretation sections | No compliance finding language observed |
| Facility deep links | Allow `'ccn=` from ownership explorer | PASS | `getFacilityIdFromUrl`; ownership links | Route checked, but query-specific browser rendering not manually clicked |
| Ownership explorer route | Static affiliation-level staffing explorer | PASS | `tools/nursing-home-ownership-staffing-explorer.html`; HTTP 200 | Manual browser review still recommended |
| Affiliation grouping | Group facilities by nonblank `affiliation_entity_name` | PASS | `normalizeDataset`; 108 facilities with affiliation names, 19 groups | Facilities without affiliation are excluded from selector by design |
| Affiliation search/selector | Search/select affiliation entities | PASS | `filterAffiliations`, `populateAffiliationSelect` | Browser interaction not manually exercised during this audit |
| Ownership summary facts | Show CT facility counts, affiliation counts, sources | PASS | `renderDatasetSummary`, `renderAffiliationSummary` | None observed |
| Latest-quarter group cards | Show latest group averages | PASS | `renderGroupMetricCards` | Simple averages across linked facilities with latest-quarter rows |
| Five-quarter group trend | Multi-quarter affiliation trend table | PASS | `renderTrendTable`; all five quarters in data | Tables are wide; manual responsive review recommended |
| Facility comparison table | Facility-by-facility latest-quarter comparison | PASS | `renderFacilityComparison` | Wide table; manual browser review recommended |
| Group-level CT direct-care metrics | Average CT estimates and below counts/shares | PASS | `calculateQuarterAggregate`, group metric cards, trend/facility columns | Uses simple facility-level averages, not resident-day weighted averages |
| Case-mix context in ownership view | Show aggregate benchmark context where available | PASS | `averageBenchmarkTotalHprd`, `averageActualMinusBenchmark` | Contextual only |
| Links back to facility explorer | Open selected facility by `'ccn=` | PASS | Facility links in affiliation summary and comparison table | Browser click not manually exercised |
| CT direct-care total estimate | PBJ-derived direct-care total estimate | PASS | Field `ct_direct_care_total_hprd_estimate`; generator/audit formulas | Excludes DON/admin categories |
| CT licensed direct-care estimate | PBJ-derived licensed direct-care estimate | PASS | Field `ct_direct_care_licensed_nurse_hprd_estimate`; generator/audit formulas | Excludes DON/admin categories |
| CT comparison constants | 3.00 total, 0.84 licensed | PASS | Generated fields and field map | Not formal compliance determination |
| CT difference fields | Store amount above/below comparison point | PASS | `ct_total_direct_care_difference_from_minimum`, `ct_licensed_direct_care_difference_from_minimum` | Computed from rounded CT estimate fields in current implementation |
| CT below booleans | Flag below-comparison rows | PASS | `ct_total_direct_care_below_minimum_estimate`, `ct_licensed_direct_care_below_minimum_estimate` | Audit confirms counts |
| Calculation audit script | Independently recompute and compare metrics | PASS | `scripts/audit_nursing_home_staffing_ct.py` ran successfully | Keep independent from generator helpers |
| Calculation audit report | Persistent calculation audit documentation | PASS | `docs/nursing_home_staffing_calculation_audit.md` | Generated timestamp updates each audit run |
| Generator tests | Synthetic tests for row logic, merges, CT estimates | PASS | `scripts/test_build_nursing_home_staffing_ct.py`; 13 tests passed | Good coverage for core logic; no browser tests yet |
| Navigation | Discover both tools from landing page and docs | PARTIAL | `index.html` links both tools; README lists routes; context registry lists both | Landing-page staffing card still says "mock quarterly PBJ," stale relative to CT-first export |
| Documentation currency | README/data contract/context registry explain workflow | PASS | README commands, data contract CT formulas, context registry references | Minor wording refresh recommended for index card only |

## Verification Results

All requested checks passed during this audit.

| Check | Result |
|---|---|
| `python scripts/audit_nursing_home_staffing_ct.py` | PASS: 966 rows compared, 0 discrepancies, 0 missing, 0 extra; CT counts 163 / 38 / 27 / 7 confirmed |
| `python -m unittest scripts.test_build_nursing_home_staffing_ct` | PASS: 13 tests |
| `python -m py_compile scripts/build_nursing_home_staffing_ct.py scripts/test_build_nursing_home_staffing_ct.py scripts/audit_nursing_home_staffing_ct.py` | PASS |
| `node --check Assets/nursing-home-staffing.js` | PASS |
| `node --check Assets/nursing-home-ownership-staffing.js` | PASS |
| `python -m json.tool data/nursing_home_staffing_ct.json` | PASS |
| `python -m json.tool data/current_tool_context_registry.json` | PASS |
| HTTP `tools/nursing-home-staffing-explorer.html` | PASS: 200 |
| HTTP `tools/nursing-home-ownership-staffing-explorer.html` | PASS: 200 |
| HTTP `data/nursing_home_staffing_ct.json` | PASS: 200 |
| HTTP `Assets/nursing-home-staffing.js` | PASS: 200 |
| HTTP `Assets/nursing-home-ownership-staffing.js` | PASS: 200 |

## Confirmed Features

The following areas are fully confirmed by code/data inspection and command checks:

- PBJ multi-file ingestion and generated CT static export
- Provider Information enrichment and case-mix benchmark fields
- SNF Enrollment enrichment and affiliation grouping fields
- Five-quarter trend support
- Missing-quarter display handling
- Facility explorer CT-first JSON loading with mock fallback
- Facility search, selection, metric cards, benchmark card, ownership context, interpretation copy, and `'ccn=` deep-link handling in code
- Ownership/affiliation explorer grouping, latest-quarter summaries, trend table, facility comparison, CT direct-care group summaries, and links back to facility pages in code
- CT direct-care metric fields, differences, and below-comparison booleans
- Independent calculation audit and generator unit tests
- Static routes and JSON/JS assets reachable from a local HTTP server

## Present But Deserving Manual Browser Review

These are present and appear structurally correct, but should be manually reviewed before public use:

- Facility explorer layout on mobile and wide desktop, especially the CT direct-care comparison card.
- Ownership explorer wide trend and facility comparison tables on mobile.
- Keyboard interaction and screen-reader experience for both selectors and wide tables.
- Actual `'ccn=` navigation by clicking an ownership table link in a browser.
- Visual emphasis of "Below CT comparison point" labels to ensure they are clear but not alarmist.

## Not Found / Incomplete

No previously built major feature was found missing or functionally broken in the current repository state.

One minor documentation/discoverability issue was found:

- `index.html` still describes the facility staffing card as reviewing "mock quarterly PBJ staffing metrics," while the current explorer attempts to load the generated Connecticut export first. This is a wording issue, not a data or calculation bug.

## Data And UX Risks Before Public Use

- The generated export is static and depends on manually refreshed local CMS source files.
- Provider Information benchmark fields are contextual and may not align exactly with each PBJ quarter.
- CT direct-care comparison fields are PBJ-derived screening estimates, not formal DPH compliance determinations.
- Ownership/affiliation fields come from CMS SNF Enrollments and do not prove common operations or day-to-day control.
- Group averages in the ownership explorer are simple facility averages, not resident-day weighted averages.
- Some facilities do not have all five facility-quarter rows; the UI handles this, but users may need plain-language reminders.
- The current automated checks do not include browser DOM assertions, screenshots, or accessibility testing.

## Recommended Next Development Steps

1. Fix the stale `index.html` staffing card wording so it no longer implies the primary facility explorer is mock-only.
2. Run manual browser review of both tools across desktop and mobile widths, focusing on wide tables and CT comparison labels.
3. Add a lightweight browser smoke test with Playwright or similar to verify CT JSON loads, selectors populate, `'ccn=` deep links render the expected facility, and ownership links route correctly.
4. Consider adding optional resident-day-weighted group averages in the ownership explorer, clearly labeled, while preserving current simple averages if useful.
5. Add a generated-export freshness note in the UI that displays the source freshness date and generated timestamp more visibly.
6. Keep `scripts/audit_nursing_home_staffing_ct.py` in the regular release checklist whenever source CSVs or generator formulas change.
