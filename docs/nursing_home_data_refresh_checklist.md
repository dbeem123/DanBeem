# Nursing Home Data Refresh Checklist

Operational checklist for future CMS and Connecticut DSS source updates. Phase 10A did not download or integrate new files.

Phase 10B added a public source-currency component that reads only from the live generated staffing export, `data/nursing_home_staffing_ct.json`. The planning manifest remains maintenance-only. Current integrated source dates shown publicly are derived from the PBJ reporting period, source release filenames, and export generation timestamp already present in the generated JSON.

Phase 10C.5 long-history planning recommends separate refresh metadata for any future PBJ-only historical staffing export, current/recent dashboard export, current contextual CMS snapshots, and historically aligned contextual snapshots added later. Do not publish historical Provider Information, Quality Measures, affiliation, ownership, SFF, DPH, or DSS context as quarter-specific history unless the corresponding archived snapshot or event source has been acquired and validated.

Phase 10C.6 adds `data/nursing_home_staffing_history_ct.json` as the production PBJ-only historical staffing export. Rebuild and independently audit that file whenever PBJ source quarters are added or replaced.

| Dataset | Official source page | Expected cadence | Current local file/date | Release handling | Generator impact | Validation / audit | Tools affected | Public freshness metadata |
|---|---|---|---|---|---|---|---|---|
| PBJ Daily Nurse Staffing | CMS PBJ / data.cms.gov | Quarterly reporting deadlines listed by CMS; confirm each public release | 2024Q4-2025Q4 | Append as immutable quarter | High if included in build | Re-run calculation audit and row-count checks | All staffing tools | Latest PBJ quarter, quarters included |
| Provider Information | CMS nursing homes topic | Confirm each official release | `NH_ProviderInfo_Apr2026.csv` | Archive snapshot and designate latest | Medium | Validate rating/status fields and merge counts | Facility, statewide, methodology | Provider Info snapshot / processing date |
| SNF Enrollments | CMS SNF Enrollments | Monthly-style snapshots observed; confirm each release | `SNF_Enrollments_2026.05.01.csv` | Archive snapshot and designate latest | Medium | Validate CCN matches, affiliation counts, duplicates | Facility, ownership/affiliation | Enrollment snapshot date |
| Quality Measures Claims | CMS nursing homes topic | Confirm each release | `NH_QualityMsr_Claims_Apr2026.csv` | Archive snapshot and designate latest | Medium | Validate measure counts, CT rows, score parsing | Facility | QM Claims processing date / measure period |
| MDS Quality Measures | CMS nursing homes topic | Confirm each release | Not local | Archive for later analysis first | Future | Validate measure definitions and footnotes | Future QM displays | MDS QM snapshot date |
| Ownership | CMS nursing homes topic | Confirm each release | `NH_Ownership_Apr2026.csv` in Downloads | Archive every release | Future | Validate CCN, owner names, roles, percentages, association dates | Future owner/entity explorer | Ownership processing date |
| SNF CHOW | CMS SNF Change of Ownership | Catalog indicates quarterly (`R/P3M`); confirm release | Not local | Archive every release | Future | Validate transaction keys, CCNs, buyer/seller fields | Future ownership-change context | CHOW snapshot/effective dates |
| SNF CHOW Owner Information | CMS SNF CHOW Owner Information | Confirm official release | Not local | Archive with CHOW | Future | Validate linkage to CHOW and owner roles | Future owner/entity explorer | CHOW owner info snapshot |
| Health Deficiencies | CMS Health Deficiencies | PDC planned monthly-style update observed | Not local | Archive snapshot; current display uses latest | Future | Validate CT rows, tags, survey dates, scope/severity, correction status | Future facility citations | Deficiency processing date / survey window |
| Fire Safety Deficiencies | CMS Fire Safety Deficiencies | Confirm release | Not local | Archive snapshot | Future | Same as health deficiencies | Future facility citations | Deficiency processing date |
| Citation Code Look-up | CMS Citation Descriptions | Confirm release | `NH_CitationDescriptions_Apr2026.csv` in Downloads | Archive with deficiencies | Future | Validate tag lookup coverage | Future citations | Lookup snapshot |
| Penalties | CMS Penalties | Confirm release | Not local | Archive snapshot | Future | Validate fines/payment denials, amounts, dates | Future enforcement context | Penalty processing date / lookback |
| SFF/Candidate status | CMS Provider Information field | Same as Provider Info | Present in Provider Info | Archive Provider Info | Future small field merge | Validate official values and nulls | Facility/statewide context | Provider Info snapshot date |
| Abuse Icon | CMS Provider Information field | Same as Provider Info | Present in Provider Info | Archive Provider Info | Future small field merge | Validate official values and wording | Facility/statewide context | Provider Info snapshot date |
| Chain Performance | CMS Chain Performance resources | Confirm release | `Chain_performance_20260515.csv` in Downloads | Archive for research | None until mapping validated | Validate chain methodology and mappings before use | Future chain context only | Chain file date |
| CT DSS rates | CT DSS Rates & Census page | Annual SFY and updates; confirm page | Not in repo | Archive by SFY | Future after crosswalk | Extract provider number/name/rate; crosswalk to CCN | Future CT DSS context | SFY/rate period |
| CT DSS census | CT DSS Rates & Census page | Monthly links observed; confirm each month | Not in repo | Archive monthly | Future after crosswalk | Extract tables, validate provider name/town, crosswalk to CCN | Future capacity/access context | Census month / data-as-of date |
| CT DSS case-mix rate calculations | CT DSS Rates & Census page | Quarterly links observed | Not in repo | Archive quarterly | Future after crosswalk | Validate fields and distinguish from CMS case-mix staffing point | Future Medicaid acuity/rate context | DSS case-mix quarter |
| CT DSS cost report/rate computation data | CT DSS Quarterly Cost Report Data | Quarterly files observed through Q4 2024 | Not in repo | Archive quarterly | Future | Validate structure, field meanings, crosswalk | Future financial context | Cost-report quarter |
| CT DSS individual cost reports | CT DSS Cost Reports page | Annual facility reports/summaries | Not in repo | Index PDFs by facility/year | Future separate project | Build document index before extraction | Future financial/related-party module | Cost report year |
| CT DPH facility master | CT DPH Chronic and Convalescent Nursing Home file | Confirm each official release | `Chronic_and_Convalescent_Nursing_Home.csv` in Downloads | Archive snapshot; do not overwrite without recording | Future crosswalk | Validate license normalization, active/closed statuses, name/address fields | Future DPH-to-CCN crosswalk | DPH facility snapshot date |
| CT DPH management history | CT DPH Nursing Home Management History | Confirm each official release | `Nursing_Home_Management_History.csv` in Downloads | Archive snapshot | Future governance timeline | Validate role counts, dates, TEMP licenses, overlaps, active/open-ended rows | Future governance timeline | DPH leadership snapshot date |
| CT DPH administrator registry | CT DPH Nursing Home Administrator file | Confirm each official release | `Nursing_Home_Administrator.csv` in Downloads | Archive snapshot | Validation support only | Validate normalized license matching; do not invalidate historical nonmatches | Future governance validation | Administrator registry snapshot date |
| CT DPH management-company registry | CT DPH Nursing Home Management Company file | Confirm each official release | Canonical file in Downloads; duplicate `(1)` file ignored | Archive canonical snapshot only | Future only if assignment source found | Validate duplicate files and absence/presence of facility assignment fields | Deferred management-company context | Registry snapshot date |

## Refresh Workflow

1. Download into a dated staging directory.
2. Record source URL, release date, processing date, and file hash in the source manifest.
3. Keep previous snapshots; do not overwrite historical source files.
4. Run schema/header diff before any generator change.
5. Run targeted merge validation for CCN-keyed CMS files.
6. For CT DSS files, do not merge until crosswalk confidence and manual review are complete.
7. Regenerate and audit only in an implementation phase, not during source-acquisition-only phases.

## Intake Directory Reminder

Use `source_data/README.md` for local file-placement guidance. Current integrated files remain in their existing paths until a later migration is planned and tested. Historical PBJ files should go under `source_data/pbj/historical/YYYY/` and should not be mixed into the live generator input directory until staged compatibility testing is complete.

For CT DPH sources, preserve raw license values and normalized `state_facility_license_id` values. Do not merge DPH leadership records into CMS CCN-keyed displays until the crosswalk is separately validated and manually reviewed.
