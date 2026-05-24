# Nursing Home Data Download Homework

Plain-language acquisition checklist for future work. Do not integrate these files until a later implementation phase.

Phase 10B added `source_data/README.md` as the local intake guide. Place downloaded files in the planned archive folders first; do not replace current integrated files or add historical PBJ files to the live PBJ folder until compatibility testing is scheduled.

## 1. Download Now: Highest Priority Files

| Item | Official dataset | Source page | Why needed | Supports | Recommended local location | Integrate now? |
|---|---|---|---|---|---|---|
| Historical PBJ quarters | CMS Payroll-Based Journal Daily Nurse Staffing | https://data.cms.gov/ and CMS PBJ page | Extends staffing history beyond five quarters | Current staffing analytics | `source_data/pbj/historical/YYYY/` | No; archive and test later |
| MDS Quality Measures | `NH_QualityMsr_MDS_MonYYYY.csv` | CMS nursing homes Provider Data Catalog | Complements claims QMs already integrated | Future facility QM context | `source_data/quality_measures/mds/YYYY-MM/` | No |
| Health Deficiencies | `NH_HealthCitations_MonYYYY.csv` | CMS Health Deficiencies | Facility-level survey/citation context | Future facility citations | `source_data/deficiencies/cms/YYYY-MM/` | No |
| Fire Safety Deficiencies | Fire Safety Deficiencies file | CMS nursing homes Provider Data Catalog | Completes deficiency context | Future facility citations | `source_data/deficiencies/cms/YYYY-MM/` | No |
| Penalties | `NH_Penalties_MonYYYY.csv` | CMS nursing homes Provider Data Catalog | Fines and payment denials | Future enforcement context | `source_data/enforcement/cms/YYYY-MM/` | No |
| SNF Change of Ownership | Skilled Nursing Facility Change of Ownership | CMS provider-characteristics | Direct ownership-change event history | Future ownership-change module | `source_data/ownership/chow/YYYY-MM-DD/` | No |
| SNF CHOW Owner Information | SNF Change of Ownership - Owner Information | data.gov / CMS | Buyer/seller ownership and managerial-control detail | Future owner/entity explorer | `source_data/ownership/chow_owner_info/YYYY-MM-DD/` | No |

## 2. Download After Immediate Roadmap Confirmation

| Item | Why | Local location |
|---|---|---|
| Survey Summary | Useful bridge before detailed deficiencies; gives inspection dates and counts | `source_data/survey_summary/cms/YYYY-MM/` |
| Latest Provider Information snapshot | Needed for future source-freshness/status work | `source_data/provider_info/snapshots/YYYY-MM/` |
| Latest SNF Enrollment snapshot | Needed for affiliation refresh and ownership-change comparison | `source_data/snf_enrollments/snapshots/YYYY-MM-DD/` |
| Latest CMS Ownership file | Existing April 2026 file should be moved into repo source archive | `source_data/ownership/cms/2026-04/` |

## 3. Historical Backfill Files

- PBJ Daily Nurse Staffing: download 2017Q4 through 2024Q3.
- Place historical PBJ files in `source_data/pbj/historical/YYYY/` by calendar year.
- Keep historical PBJ files separate from `source_data/pbj/` until staged generator tests pass: one quarter, then one year, then the full archive.
- Provider Information: download archived monthly/periodic snapshots where available, starting with 2024-2026.
- SNF Enrollments: download archived snapshots visible in catalog from 2023-03-31 forward.
- Ownership: retrieve archived ownership snapshots if available; otherwise archive prospectively.
- Deficiencies/Penalties: archive snapshots prospectively because files often represent rolling lookback windows.

## 4. Archive Every Future Release

- PBJ Daily Nurse Staffing
- Provider Information
- SNF Enrollments
- Quality Measures Claims
- Quality Measures MDS
- CMS Ownership
- SNF CHOW and CHOW Owner Information
- Health and Fire Safety Deficiencies
- Penalties
- Chain Performance
- CT DSS rates
- CT DSS census
- CT DSS case-mix rate calculations
- CT DSS quarterly cost-report/rate-computation data

## 5. Already In Hand; Hold For Later Use

| File | Action |
|---|---|
| `NH_Ownership_Apr2026.csv` | Move to `source_data/ownership/cms/2026-04/`; sufficient for initial owner/entity parsing prototype, not public display yet |
| `NH_CitationDescriptions_Apr2026.csv` | Move to `source_data/deficiencies/reference/2026-04/`; use only after facility-level citation files are downloaded |
| `Chain_performance_20260515.csv` | Move to `source_data/chain_performance/cms/2026-05-15/`; do not merge until mapping is validated |

## 6. Connecticut DSS Practical Download List

Download first, because they look structured or high-value:

- SFY 2026 Nursing Facility Rates PDF, plus SFY 2025 and SFY 2024 for sampling.
- 2026 monthly census PDFs, starting January through latest available.
- Q1 2024 through Q3 2025 Case Mix Quarterly Rate Calculation files.
- Quarterly Cost Report Data Q1 2024 through Q4 2024.
- Rate Comp Cost Report Data 2012 to 2024.

Index or sample first, because extraction is heavier:

- Individual Nursing Facility Cost Reports and summaries.
- Older census PDFs back to 2019.
- Demand projection reports. These should probably remain linked policy resources, not facility-level data.

## 7. Sources Needing More Verification Before Integration

- CT DSS rate/census/cost files: verify identifiers and build a state-provider-to-CCN crosswalk.
- CMS Chain Performance: verify relationship to owner/entity, PECOS PAC IDs, and SNF Enrollment affiliation entities before display.
- Abuse Icon and SFF/Candidate status: fields appear in Provider Information, but public wording and definitions must be reviewed before adding badges.

## 8. CT DPH Governance / Leadership Files

Already found in Downloads; archive later, do not integrate yet:

| File | Recommended location | Use |
|---|---|---|
| `Chronic_and_Convalescent_Nursing_Home.csv` | `source_data/ct_dph/facilities/` | CT facility master and DPH license crosswalk input |
| `Nursing_Home_Management_History.csv` | `source_data/ct_dph/leadership_history/` | Administrator, DON, Medical Director role-period modeling |
| `Nursing_Home_Administrator.csv` | `source_data/ct_dph/administrator_registry/` | Administrator license validation support |
| `Nursing_Home_Management_Company.csv` | `source_data/ct_dph/management_companies/` | Licensed management-company registry |
| `Nursing_Home_Management_Company (1).csv` | Do not archive as separate source | Byte-for-byte duplicate of canonical management-company file |

Next DPH-related acquisition work:

- Find whether CT DPH publishes older snapshots or official download pages for these files.
- Look for a separate facility-to-management-company assignment or change-history source. The current management-company registry does not identify which nursing homes each company managed.
- Build a DPH facility-license to CMS CCN crosswalk as a separate project asset before any governance display work.
