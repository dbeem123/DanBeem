# Nursing Home Historical Data Backfill Plan

Phase 10A planning only. No data was downloaded or integrated.

| Data domain | Official source | Earliest period confirmed | Latest period available / observed | Archive availability | Format | Workload | Longitudinal value | Interpretive limitations | Priority | Recommended local directory |
|---|---|---:|---:|---|---|---|---|---|---|---|
| PBJ Daily Nurse Staffing | CMS PBJ public use file / data.cms.gov | Public posting began Nov. 1, 2017; use 2017Q4 as first backfill target | Current local latest 2025Q4; future quarterly | CMS public data / archived snapshots | CSV | Medium-high due file size and schema checks | Very high | Schema/header changes, facility closures, pandemic-era comparability, missing quarters | Highest | `source_data/pbj/historical/YYYY/` |
| Provider Information / Care Compare ratings | CMS nursing homes Provider Information | Confirm via archived snapshots | Local April 2026 | PDC archived data snapshots | CSV | Medium | High for rating/status history | Ratings are point-in-time context, not current after a later snapshot | High | `source_data/provider_info/snapshots/YYYY-MM/` |
| Quality Measures Claims | CMS Nursing Home Quality Measures Claims | Confirm via PDC archives | Local April 2026 | PDC archives | CSV | Medium | Medium-high | Measure definitions and periods can change | High | `source_data/quality_measures/claims/YYYY-MM/` |
| Quality Measures MDS | CMS MDS Quality Measures | Confirm via PDC archives | Not local | PDC archives | CSV | Medium | Medium-high | Measure changes and footnotes matter | Medium | `source_data/quality_measures/mds/YYYY-MM/` |
| SNF Enrollment / affiliation | CMS Skilled Nursing Facility Enrollments | Catalog shows snapshots from 2023-03-31 | Local 2026-05-01 | Catalog lists many historical snapshots | CSV/API | Medium | High for affiliation changes | Affiliation entity does not prove operational control | High | `source_data/snf_enrollments/snapshots/YYYY-MM-DD/` |
| Detailed Ownership | CMS Ownership | Confirm via PDC archives; local April 2026 in Downloads | April 2026 local | PDC archives likely | CSV | Medium | Very high for owner/entity lookup and change tracking | Current active records; history requires snapshots or CHOW | High | `source_data/ownership/cms/YYYY-MM/` |
| SNF Change of Ownership | CMS SNF CHOW | Catalog indicates CHOW events on/after Jan. 1, 2016 | Catalog observed latest 2026-era resources | Catalog/resources | CSV/API | Medium | Very high | Transaction semantics and buyer/seller roles need careful definitions | High | `source_data/ownership/chow/YYYY-MM-DD/` |
| SNF CHOW Owner Information | CMS SNF CHOW Owner Information | Catalog observed resources back to 2022-06-30 | Latest observed 2026-03-01 | Catalog/resources | CSV/API | Medium | High | Must be linked to CHOW and facility records | High | `source_data/ownership/chow_owner_info/YYYY-MM-DD/` |
| Deficiencies/citations | CMS Health and Fire Safety Deficiencies | Current files cover last three years; historical snapshots may be archived | April 2026 PDC observed | PDC archived snapshots | CSV | Medium-high | High | Only last-three-years window per snapshot; correction and IDR/IIDR context matter | Medium | `source_data/deficiencies/cms/YYYY-MM/` |
| Citation descriptions | CMS Citation Code Look-up | Confirm via PDC archives | April 2026 local in Downloads | PDC archives | CSV | Low | Reference only | Not facility findings without citation files | Medium | `source_data/deficiencies/reference/YYYY-MM/` |
| Penalties/enforcement | CMS Penalties | File covers last three years per data dictionary | Not local | PDC archives | CSV | Medium | High | Historic enforcement does not indicate current condition | Medium | `source_data/enforcement/cms/YYYY-MM/` |
| SFF/Candidate status | CMS Provider Information / official CMS fields | Snapshot history via Provider Info archives | April 2026 local Provider Info has `Special Focus Status` | Archive Provider Info | CSV | Low | Medium | Factual status only; no LTCOP risk score | Medium-high | `source_data/provider_info/snapshots/YYYY-MM/` |
| Abuse Icon | CMS Provider Information field | Snapshot history via Provider Info archives | April 2026 local Provider Info has `Abuse Icon` | Archive Provider Info | CSV | Low | Medium | Must explain CMS definition and avoid inference | Medium | `source_data/provider_info/snapshots/YYYY-MM/` |
| CT DSS rates | CT DSS Nursing Facility Rates | SFY 2012-2015 combined link observed | SFY 2026 | CT DSS webpage links | PDF / possibly spreadsheet | High | High | DSS provider identifiers; no CCN observed in sample | Medium | `source_data/ct_dss/rates/SFYYYYY/` |
| CT DSS census | CT DSS Nursing Facility Census | 2019 partial through 2026 observed | 2026 April observed on page | CT DSS monthly links | PDF | High | High for capacity/access | Crosswalk and extraction needed | Medium | `source_data/ct_dss/census/YYYY/MM/` |
| CT DSS case-mix rate calculation | CT DSS Case Mix Quarterly Rate Calculation | Q1 2024 observed | Q3 2025 observed | CT DSS links | To verify | Medium-high | Medium-high | Distinct from CMS case-mix staffing comparison | Medium | `source_data/ct_dss/case_mix_rate/YYYYQ#/` |
| CT DSS cost report / rate computation data | CT DSS Quarterly Cost Report Data | Q1 2019 observed | Q4 2024 observed | CT DSS quarterly links | To verify | High | Very high | Crosswalk and field dictionary needed | Medium-later | `source_data/ct_dss/cost_report_data/YYYYQ#/` |
| CT DSS individual cost reports | CT DSS Nursing Facility Cost Reports | Facility pages show many 2015-2024 reports | 2024 reports and summaries observed | CT DSS facility report links | PDF-heavy | Very high | Very high for financial/related-party context | Extraction and interpretation risk | Later | `source_data/ct_dss/cost_reports/facility_slug/YYYY/` |
| CMS Chain Performance | CMS Chain Performance Measures | Current release family only confirmed locally | Local 2026-05-15 file in Downloads | CMS resources | CSV/XLSX/PDF | Medium | Medium | CMS chain is a separate network-analysis concept | Later | `source_data/chain_performance/cms/YYYY-MM-DD/` |
| CT DPH facility master | CT DPH Chronic and Convalescent Nursing Home file | Current file in hand; older snapshots not researched | Current download | Archive future snapshots | CSV | Low | High as crosswalk input | Current-state facility rows unless historical snapshots are found | Near-term enabling | `source_data/ct_dph/facilities/` |
| CT DPH management history | CT DPH Nursing Home Management History | Dates in file begin in 1997 | Current download | Archive future snapshots | CSV | Medium | High for governance timeline context | Requires cleaning, role-period rules, and CMS CCN crosswalk | Medium-term | `source_data/ct_dph/leadership_history/` |
| CT DPH administrator registry | CT DPH Nursing Home Administrator file | Current registry; issue dates vary | Current download | Archive future snapshots | CSV | Low | Medium validation support | Current registry cannot validate all historical role records | Support source | `source_data/ct_dph/administrator_registry/` |
| CT DPH management-company registry | CT DPH Nursing Home Management Company file | Current registry | Current download | Archive future snapshots | CSV | Low | Low until assignment source found | No facility assignment periods in current file | Defer display | `source_data/ct_dph/management_companies/` |

## PBJ Backfill Recommendation

Download PBJ Daily Nurse Staffing quarterly files from 2017Q4 through 2024Q3 first, because 2024Q4 through 2025Q4 are already local. Test generator compatibility in batches:

1. 2024Q1-2024Q3 as a recent-schema dry run.
2. 2022Q1-2023Q4 to catch medium-range schema differences.
3. 2020Q1-2021Q4 with explicit pandemic-era caveats.
4. 2017Q4-2019Q4 for early-public-file compatibility.

The public UI should continue defaulting to recent quarters first. A full-history mode should be optional and clearly labeled to avoid overwhelming first-time users.

### Q3 2024 Compatibility Result

Phase 10C.1 tested `PBJ_Daily_Nurse_Staffing_Q3_2024.zip` as the first historical PBJ file. The file was schema-compatible with the current daily staffing generator and audit approach. A temporary six-quarter build covering 2024Q3 through 2025Q4 succeeded with 1,160 facility-quarter rows, 194 Q3 2024 Connecticut facility-quarter rows, no missing required columns, no malformed numeric values, and zero audit mismatches.

Before publishing longer history, update UI wording that currently says "five-quarter" and review persistent-pattern threshold controls for six or more available quarters.

### 2024 Full-Year Compatibility Result

Phase 10C.2 tested Q1, Q2, and Q3 2024 historical PBJ files together with the current live files. A temporary eight-quarter build covering 2024Q1 through 2025Q4 succeeded with 1,552 facility-quarter rows, no missing required columns, no malformed numeric values, and zero audit mismatches.

Q1 2024 and Q2 2024 matched the current 33-column PBJ Daily Nurse Staffing schema, including all required nurse-hour, census, quarter/date, and contract-hour fields. No generator formula or alias changes were required.

It is safe to proceed to an oldest-boundary compatibility test with `PBJ_Daily_Nurse_Staffing_Q4_2017.zip`, while keeping longer-history publication blocked on a UI wording and persistent-pattern threshold pass.

### Q4 2017 Boundary Compatibility Result

Phase 10C.3 tested `PBJ_Daily_Nurse_Staffing_Q4_2017.zip` as the oldest targeted PBJ backfill boundary. The ZIP contained the expected facility-level PBJ Daily Nurse Staffing CSV, not an Employee Detail file.

The Q4 2017 file used the 33-column daily staffing structure with older/lowercase header spellings such as `provnum`, `cy_qtr`, `workdate`, `hrs_lpn_admin`, and `hrs_na_trn`. The current generator's normalized header lookup handled these names without formula, alias, parsing, extraction, or encoding changes.

A temporary boundary build covering `2017Q4` plus `2024Q1` through `2025Q4` succeeded with 1,740 Connecticut facility-quarter rows and zero independent audit mismatches. Q4 2017 contributed 188 Connecticut facility-quarter rows. Because Provider Information, SNF Enrollment, Quality Measures, ratings, and affiliation context are current CMS snapshots, any public long-history release should clearly distinguish historical PBJ staffing quarters from current contextual enrichment and should avoid implying that April/May 2026 context applied during 2017Q4.

It is safe to proceed to a temporary full-archive PBJ build from 2017Q4 through 2025Q4 before publishing any longer-history UI. Public release remains blocked on wording, persistent-pattern threshold, trend/table/print readability, and source-methodology updates for long-history context.

### Full-History 2017Q4-2025Q4 Compatibility Result

Phase 10C.4 tested the full planned PBJ Daily Nurse Staffing backfill window from `2017Q4` through `2025Q4`. All 33 target quarters were present, schema-compatible, and processable by the current generator with no formula, alias, parsing, extraction, or encoding changes.

The temporary full-history output contained 216 Connecticut CCNs and 6,569 facility-quarter rows from 599,930 Connecticut daily PBJ rows. The independent calculation audit compared all 6,569 generated rows and found zero missing rows, zero extra rows, and zero field mismatches.

This confirms that the PBJ historical archive is technically ready for a later public integration phase. Public release should still wait for long-history UI and methodology work, including flexible wording, selected trend windows, change-over-time endpoint controls, persistent-pattern window/threshold redesign, print/export review, and clearer separation between historical PBJ measures and current CMS contextual snapshots.

### Long-History Publication Architecture Note

Phase 10C.5 created a PBJ-only preview history export at `data/testing/nursing_home_staffing_history_ct_2017q4_2025q4_preview.json`. That preview intentionally separates quarter-specific PBJ staffing history from current April/May 2026 CMS contextual snapshots.

Before public cutover, CT comparison flags need effective-date-aware display logic. Current planning recommends reference-only handling before the confirmed 3.0 policy period, partial-period caution for `2023Q1`, and full-quarter applicable CT comparison display beginning no earlier than `2023Q2`.

The Phase 10C.6 public integration keeps the current/recent dashboard JSON fast and lazy-loads or directly loads PBJ-only long history only in views that need it. The production historical file is `data/nursing_home_staffing_history_ct.json`.

## Ownership History Planning

Ownership change history can come from two tracks:

- Direct event history: CMS SNF Change of Ownership and SNF CHOW Owner Information.
- Snapshot history: archive CMS Ownership and SNF Enrollment releases prospectively and, where available, retrieve archived snapshots.

Do not infer ownership changes solely from facility name changes. Use official CHOW data or validated snapshot comparison.

## CT DPH Governance History Planning

The DPH management-history file appears to contain leadership role dates from 1997 through 2026. It can eventually support Administrator, Director of Nurses, and Medical Director timeline context, but only after a validated CT DPH facility-license to CMS CCN crosswalk exists.

Archive future DPH facility master, leadership history, administrator registry, and management-company registry snapshots. If older DPH snapshots are available, retain them separately because current facility names and current registry status may not describe earlier periods.

Governance history should remain distinct from CMS ownership/CHOW records and CT DSS related-party or cost-report context. Snapshot archiving may help identify future changes prospectively, but the first enabling step is crosswalk construction.
