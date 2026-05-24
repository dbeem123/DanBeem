# Connecticut Nursing Home Data Acquisition Roadmap

Generated for Phase 10A. This is a planning document only. It does not change application behavior, calculations, source data, generator logic, exports, or UI.

## Official Source References

- [CMS nursing homes Provider Data Catalog topic](https://data.cms.gov/provider-data/topics/nursing-homes)
- [CMS Payroll-Based Journal staffing submission page](https://www.cms.gov/medicare/quality/nursing-home-improvement/staffing-data-submission)
- [CMS Nursing Home Data Dictionary](https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/nursing_home/NH_Data_Dictionary.pdf)
- [CMS Skilled Nursing Facility Enrollments](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-enrollments)
- [CMS Skilled Nursing Facility Change of Ownership](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-change-of-ownership)
- [CMS Skilled Nursing Facility Change of Ownership - Owner Information](https://catalog.data.gov/dataset/skilled-nursing-facility-change-of-ownership-owner-information)
- [CMS Nursing Home Chain Performance Measures methodology](https://data.cms.gov/sites/default/files/2025-06/97e4c3cd-4104-408e-8bef-24dfab14bf07/UPDATE_Methodology_Nursing_Home_Chain_Performance.pdf)
- [Connecticut DSS Nursing Facility Rates & Census Information](https://portal.ct.gov/DSS/Health-And-Home-Care/Medicaid-Nursing-Home-Reimbursement/Medicaid-Nursing-Home-Reimbursement/Nursing-Facility-Rates)
- [Connecticut DSS Nursing Facility Cost Reports](https://portal.ct.gov/dss/health-and-home-care/medicaid-nursing-home-reimbursement/nursing-facility-cost-reports/cost-report)
- [Connecticut DSS Quarterly Cost Report Data](https://portal.ct.gov/DSS/Health-And-Home-Care/Medicaid-Nursing-Home-Reimbursement/Nursing-Facility-Cost-Reports/Quarterly-Cost-Report-Data)

## Current Local Source Inventory

| Local file | Local directory | Official source | Period / snapshot | Format | Primary join | Integrated | Current or potential use | Retention recommendation | Next action |
|---|---|---|---|---|---|---|---|---|---|
| `PBJ_Daily_Nurse_Staffing_Q4_2024.csv` | `source_data/pbj` | CMS Payroll-Based Journal Daily Nurse Staffing | 2024Q4 | CSV | `PROVNUM` / CCN | Yes | Staffing HPRD, contract %, CT direct-care estimates, trends, change, persistence, affiliation summaries | Keep as immutable quarter file | Backfill earlier quarters into historical layout |
| `PBJ_Daily_Nurse_Staffing_Q1_2025.csv` | `source_data/pbj` | CMS PBJ Daily Nurse Staffing | 2025Q1 | CSV | `PROVNUM` / CCN | Yes | Same as above | Keep | Backfill earlier quarters |
| `PBJ_Daily_Nurse_Staffing_Q2_2025.csv` | `source_data/pbj` | CMS PBJ Daily Nurse Staffing | 2025Q2 | CSV | `PROVNUM` / CCN | Yes | Same as above | Keep | Backfill earlier quarters |
| `PBJ_Daily_Nurse_Staffing_Q3_2025.csv` | `source_data/pbj` | CMS PBJ Daily Nurse Staffing | 2025Q3 | CSV | `PROVNUM` / CCN | Yes | Same as above | Keep | Backfill earlier quarters |
| `PBJ_dailynursestaffing_CY2025Q4.csv` | `source_data/pbj` | CMS PBJ Daily Nurse Staffing | 2025Q4 | CSV | `PROVNUM` / CCN | Yes | Latest staffing quarter | Keep | Archive future quarterly releases |
| `NH_ProviderInfo_Apr2026.csv` | `source_data/provider_info` | CMS Nursing Home Provider Information | April 2026 | CSV | `CMS Certification Number (CCN)` | Yes | Facility metadata, beds, ownership type, case-mix comparison point, Care Compare ratings | Archive every monthly/periodic snapshot | Add source freshness display before more display fields |
| `SNF_Enrollments_2026.05.01.csv` | `source_data/snf_enrollments` | CMS Skilled Nursing Facility Enrollments | 2026-05-01 | CSV | `CCN` | Yes | Legal organization, DBA, NPI, organization structure, proprietary/nonprofit, affiliation entity | Archive every release; high ownership-change value | Keep distinct from ownership and chain data |
| `NH_QualityMsr_Claims_Apr2026.csv` | `source_data/quality_measures` | CMS Nursing Home Quality Measures Claims | April 2026 | CSV | `CMS Certification Number (CCN)` | Yes | Four claims-based QMs: 521, 522, 551, 552 | Archive every release | Download MDS QM file next; defer statewide QM ranking |
| `NH_Ownership_Apr2026.csv` | `C:/Users/Dan/Downloads` | CMS Nursing Home Ownership | April 2026 | CSV | `CMS Certification Number (CCN)` | No | Detailed owner/entity and management-role context | Move to `source_data/ownership/cms/2026/` and archive every release | Leading candidate for owner/entity prototype after source freshness |
| `NH_CitationDescriptions_Apr2026.csv` | `C:/Users/Dan/Downloads` | CMS Citation Code Look-up | April 2026 | CSV | Tag prefix + number | No | Lookup only for deficiencies | Move to `source_data/deficiencies/reference/2026/` | Download facility-level Health and Fire Safety Deficiencies before use |
| `Chain_performance_20260515.csv` | `C:/Users/Dan/Downloads/Nursing Home Chain Performance Measures...` | CMS Nursing Home Chain Performance Measures | 2026-05-15 file date | CSV | `Chain ID` | No | National chain-level aggregate context | Archive for research; do not merge yet | Validate mapping to ownership/PECOS concepts before any display |

## Official CMS Dataset Roadmap

| Dataset | Source / page | Level | Join key | Relevant fields | Cadence / archive notes | Roadmap disposition |
|---|---|---|---|---|---|---|
| PBJ Daily Nurse Staffing | CMS PBJ / data.cms.gov | Facility-day | CCN | Daily census and nursing hours by category, employee/contract split | CMS PBJ page says public PBJ files began Nov. 1, 2017; quarterly submission deadlines are listed by fiscal quarter | Integrate soon as historical backfill |
| Provider Information | CMS nursing homes topic | Facility snapshot | CCN | Metadata, ratings, Special Focus Status, Abuse Icon, ownership changed in last 12 months, staffing, case-mix fields | Archive snapshots; CMS topic has archived data | Already integrated partially; source freshness and factual status are near-term candidates |
| MDS Quality Measures | CMS nursing homes topic / data dictionary | Facility-measure | CCN + measure code | MDS quality-measure scores and quarters | Filename pattern `NH_QualityMsr_MDS_MonYYYY.csv` in CMS data dictionary | Download next; integrate selectively later |
| Claims Quality Measures | CMS nursing homes topic / data dictionary | Facility-measure | CCN + measure code | Claims-based QM scores, footnotes, periods | Filename pattern `NH_QualityMsr_Claims_MonYYYY.csv` | Already integrated for April 2026; archive snapshots |
| Survey Summary | CMS nursing homes topic / data dictionary | Facility-inspection | CCN | Recent inspection dates and citation counts | `NH_SurveySummary_MonYYYY.csv` | Download and evaluate before deficiency UI |
| Health Deficiencies | CMS Provider Data Catalog | Facility-citation | CCN + survey date + tag | Survey date, survey type, tag, scope/severity, correction status/date, IDR/IIDR | PDC shows monthly planned update; includes archived data | Download soon after source freshness; facility detail before statewide analysis |
| Fire Safety Deficiencies | CMS Provider Data Catalog | Facility-citation | CCN + survey date + tag | Fire-safety citation details | Monthly-style PDC updates | Download with Health Deficiencies |
| Citation Code Look-up | CMS data dictionary | Reference | Tag prefix + number | Tag descriptions | Snapshot file | Already in hand; use only with facility-level citation files |
| Penalties | CMS data dictionary | Facility-enforcement | CCN | Fines and payment denials in last three years | Filename pattern `NH_Penalties_MonYYYY.csv` | Download after deficiencies |
| Ownership | CMS nursing homes topic | Facility-owner relationship | CCN | Owner/manager role, owner type, owner name, ownership %, association date | Current active nursing homes; archive snapshots to track change | Build Owner / Entity Explorer after source freshness and initial owner parsing |
| SNF Enrollments | CMS provider-characteristics | Facility/enrollment | CCN | Legal organization, DBA, NPI, organization structure, affiliation entity | Catalog shows repeated snapshots through 2026-05-01 | Already integrated; archive every release |
| SNF Change of Ownership | CMS provider-characteristics | Transaction | CCN / enrollment fields | Buyer, seller, CHOW type, effective date | Catalog metadata indicates quarterly (`R/P3M`) | Download soon for ownership-change context; do not display until mapped |
| SNF CHOW Owner Information | CMS / data.gov | Transaction-owner | CHOW keys / CCN fields to confirm | Buyer/seller ownership and managerial control details | Catalog lists resources back to 2022-06-30 and latest 2026-03-01 | Download with CHOW; validate fields |
| Nursing Home Chain Performance Measures | CMS chain performance resources | Chain aggregate | Chain ID | Chain-level ratings, staffing, SFF counts, abuse icon counts, fines, QMs | Methodology says chain assignment is PECOS/network-analysis based | Retain for later; no merge until mapping is validated |

## Connecticut DSS Source Domain

Connecticut DSS reimbursement sources are strategically important but separate from CMS Care Compare. They are not CCN-first. They must go through a crosswalk and validation layer before facility-level integration.

| DSS category | Availability observed | Format | Likely identifiers | Potential value | Integration caution |
|---|---|---|---|---|---|
| Nursing Facility Rates | SFY 2012-2015 through SFY 2026 links | Mostly PDF rate letters; current SFY 2026 PDF includes provider number, facility name, address, per diem, rate period | DSS provider number, facility name, address, town | Medicaid rate context, fiscal-year trend, rate/case-mix context | No CCN observed in sampled rate letters; build crosswalk first |
| Cost Comparison Reports | `Facility by facility comparison` link | To verify; likely PDF or spreadsheet | Facility name / DSS provider identifiers | Facility-level cost comparisons and policy analysis | Confirm structured fields before ingestion |
| Rate Computation / Cost Report Data | `Rate Comp Cost Report Data 2012 to 2024`; quarterly cost-report page has Q1 2019 through Q4 2024 links | Structured downloads likely for quarterly data; verify file types | Facility name and state/DSS provider identifiers | Rate components, cost-report variables, financial context | Ingest only after schema and crosswalk review |
| Individual Nursing Facility Cost Reports | Cost reports listed by facility, many years 2015-2024 and summaries | PDF-heavy facility documents | Facility name; sometimes provider number inside report | Related-party transactions, management fees, wages, expenses, revenues, resident statistics, ownership/financial context | Index first; full extraction is a later financial-transparency project |
| Case Mix Quarterly Rate Calculation | Q1 2024 through Q3 2025 links observed | To verify; likely PDF/spreadsheet | Facility name / DSS provider identifiers | Medicaid acuity and rate-calculation context distinct from CMS case-mix staffing point | Do not conflate with CMS Provider Information case-mix staffing comparison |
| Nursing Facility Census Files | 2019 partial quarters, monthly 2020-2026 links observed | PDF; sampled January 2026 has provider name, provider type, town, bed capacity, count, hold, total, open beds, bed changes | Facility name, town, provider type | Capacity/access context and monthly census trend | No CCN observed; crosswalk and OCR/table extraction needed |
| Demand Projections | 2025 analysis and appendices | PDF/report | Statewide, not facility-level | Policy background for access planning | Link/reference only; not facility-level integration |

## DSS Crosswalk Findings

- Current app key: CMS CCN.
- DSS sample rate letters include a state provider number, facility name, address, rate period, licensure type, and per diem, but no CCN observed.
- DSS sample census PDF includes provider name, provider type, town, bed capacity, count, holds, total, open beds, bed changes, and effective dates, but no CCN observed.
- A reliable crosswalk should require normalized facility name, address, city/town, Provider Information address, CMS CCN, and DSS provider number where available. Matches should be scored and manually reviewed before any DSS field is shown publicly.
- Do not recommend immediate DSS integration until crosswalk validation reaches a documented threshold.

## CT DPH Facility Governance, Leadership Stability, And Management Timeline Context

Phase 10B.1 identified a new Connecticut DPH source domain that should be planned before historical PBJ ingestion expands the staffing time window too far.

Current DPH files discovered in `C:/Users/Dan/Downloads`:

| File | Rows | Planning status | Future use |
|---|---:|---|---|
| `Chronic_and_Convalescent_Nursing_Home.csv` | 189 | Promising CT facility master | State-side facility license table and future CT DPH-to-CMS CCN crosswalk |
| `Nursing_Home_Management_History.csv` | 2,538 | Promising leadership-history source | Administrator, Director of Nurses, and Medical Director role-period modeling |
| `Nursing_Home_Administrator.csv` | 581 | Useful current license registry | Administrator-license validation, not complete historical validation |
| `Nursing_Home_Management_Company.csv` | 24 | Registry only | Licensed management company context |
| `Nursing_Home_Management_Company (1).csv` | 24 | Duplicate | Byte-for-byte duplicate; do not use separately |

The DPH facility master and management-history files join cleanly by normalized CT facility license number: 189 of 189 facility-master license IDs matched to 189 of 189 management-history license IDs. The normalization rule is to preserve the raw license and create `state_facility_license_id` by extracting digits and removing leading zeroes. This resolved facility-name differences such as `WEST HARTFORD HEALTH AND REHABILITATION CENTER` versus `WEST HARTFORD HEALTH & REHABILITATION CENTER`.

This domain is distinct from CMS ownership, CMS SNF Enrollment affiliation entities, CMS chain performance, CMS Change of Ownership, CT DSS financial/related-party context, and deficiencies/enforcement. It should be treated as governance and leadership timeline context.

Future product concepts:

- Facility Governance Timeline Module with PBJ staffing trend, Administrator role band, Director of Nurses role band, and optionally Medical Director role band.
- Statewide Governance Stability Screening View for frequent Administrator changes, frequent DON changes, repeated temporary DON periods, incomplete coverage, and leadership transitions temporally aligned with staffing screening patterns.
- Governance-Oriented Review Packet that distinguishes what the data shows, what it may suggest for follow-up, and what it cannot prove.
- Management Company Explorer only if an explicit facility-to-management-company assignment-period source is found.

Recommended sequence:

1. Historical PBJ single-quarter compatibility test and staged backfill.
2. CT DPH-to-CMS CCN crosswalk construction as a near-term enabling project.
3. Facility Governance Timeline proof of concept after crosswalk validation and initial historical PBJ expansion.
4. Defer Management Company Explorer until assignment periods are available.
5. Retain Owner / Entity Explorer as a separate future pathway.

See:

- `docs/nursing_home_ct_dph_governance_source_validation.md`
- `docs/nursing_home_governance_timeline_data_model.md`
- `docs/nursing_home_governance_staffing_roadmap_addendum.md`

## Owner / Entity Lookup, Ownership-Change Tracking, And Corporate Relationship Context

Ownership should become a core future product pathway, distinct from the current affiliation-based staffing explorer.

### Current data already in hand

- CMS `NH_Ownership_Apr2026.csv` has facility-level rows keyed by CCN. Local headers include provider name/address, role played by owner or manager, owner type, owner name, ownership percentage, association date, location, and processing date.
- CMS SNF Enrollments are already integrated for legal organization, DBA, NPI, proprietary/nonprofit, organization structure, and affiliation entity.
- CMS Chain Performance file is in hand outside the repo. It is chain-level, not facility-owner relationship data.

### Additional official sources needed

- CMS SNF Change of Ownership transaction file.
- CMS SNF Change of Ownership Owner Information file.
- Repeated CMS Ownership snapshots for historical owner/entity changes.
- CT DSS cost report and quarterly cost report data for later related-party and financial context.

### Product concept

Future route: `tools/nursing-home-owner-entity-explorer.html`.

Potential modules:
- owner/entity identity banner
- reported role and owner type summary
- linked Connecticut facilities
- national footprint, only if reliably supported
- recent reported ownership changes involving linked facilities
- associated CMS affiliation entities, labeled separately
- optional staffing screening summary across linked Connecticut facilities
- facility drill-down links and source caveats

### Conceptual separation required

- Ownership: CMS-reported individual or organizational ownership relationships, roles, percentages, and dates.
- Management: CMS-reported managing employee, management company, administrator, officer, or operational-role information.
- Affiliation entity: CMS SNF Enrollment affiliation grouping already used by the current app.
- Chain performance: CMS-created chain aggregate using PECOS/network analysis; not the same as owner or affiliation.
- Related-party relationships: possible CT DSS cost-report disclosures for management fees, leases, staffing arrangements, and other payments.

These concepts must not be collapsed into a single “owner,” “chain,” or “operator” without a documented mapping.

### Recommended integration sequence

1. Move and archive `NH_Ownership_Apr2026.csv`; parse owner/entity rows in a non-public analysis script.
2. Download SNF CHOW and SNF CHOW Owner Information.
3. Build an internal owner/entity normalization and matching report.
4. Compare owner/entity relationships with current SNF Enrollment affiliation entities without merging concepts.
5. Prototype an Owner / Entity Explorer only after source definitions and caveats are documented.
6. Add CT DSS related-party/cost-report indexing as a later financial/corporate context phase.

## Priority Data Domains

| Domain | Source availability | Integration value | Interpretive risk | Proposed priority |
|---|---|---:|---:|---|
| Historical PBJ staffing backfill | High; CMS says PBJ public use file has been posted since Nov. 1, 2017 | Very high | Medium, due schema and pandemic-era comparability | Near-term, first major data expansion |
| Source freshness metadata | High; current exports already have source dates in filenames/sources | High | Low | Near-term, first or parallel implementation |
| CMS SFF/Candidate factual status | Likely in Provider Information `Special Focus Status`; also chain file has counts | Medium-high | Medium if definitions not displayed | Near-term small factual-status phase after source freshness |
| CMS Abuse Icon factual status | Provider Information has `Abuse Icon` field | Medium-high | Medium-high; strong caveats needed | Near-term/medium after SFF wording is settled |
| Deficiencies/citations | High; Health and Fire Safety Deficiencies available | High | High unless survey date, type, scope/severity, correction status are clear | Medium-term, facility detail first |
| Penalties/enforcement | High; CMS Penalties file listed in data dictionary | Medium-high | Medium-high; historical enforcement can be misread | Medium-term after deficiencies |
| Additional QMs | High; MDS and SNF QRP files available | Medium | Medium; overload risk | Medium-term, selected-measure workflows |
| Detailed CMS ownership | High; local file in hand | Very high | Medium-high; definitions are nuanced | Near-term after freshness; can run in parallel with PBJ acquisition |
| Chain performance | Medium-high; file and methodology available | Medium | High mapping risk | Later, contextual only |
| CT DSS rates/census | High but PDF/crosswalk-heavy | High for CT-specific context | Medium-high | Medium-term after crosswalk |
| CT DSS cost reports/financials | High but extraction-heavy | Very high for policy/financial transparency | High | Later, index first |

## Candidate Next Integration Phases

| Candidate phase | Public value | LTCOP value | Availability certainty | Difficulty | Interpretive risk | Facility dossier fit | Timing |
|---|---:|---:|---:|---:|---:|---:|---|
| Historical PBJ backfill and long-range trends | High | High | High | Medium | Medium | High | Near-term |
| Source currency/freshness display | High | High | High | Low | Low | High | Near-term |
| CMS SFF/Candidate factual status | Medium | High | Medium-high | Low-medium | Medium | High | Near-term/parallel |
| CMS Abuse Icon factual status | Medium | High | Medium-high | Low-medium | Medium-high | High | Medium, after wording review |
| Facility-level deficiencies/citations | High | High | High | Medium-high | High | High | Medium |
| Penalties/enforcement | Medium-high | High | High | Medium | Medium-high | Medium-high | Medium |
| CT DSS rate and census context | Medium-high | High | Medium | High | Medium | Medium-high | Medium |
| CT DSS financial/cost-report exploration | Medium | Very high | Medium | Very high | High | Medium | Later |
| Detailed CMS ownership / Owner Entity Explorer | High | Very high | High | Medium-high | Medium-high | High | Near-term after freshness |
| Additional Quality Measures comparison | Medium | Medium | High | Medium | Medium | Medium | Medium |
| Chain Performance context | Medium | Medium | Medium | Medium | High | Low-medium until mapping | Later |

## Recommendations

First implementation phase after this roadmap: source currency/freshness display plus acquisition scaffolding. This is low-risk and helps every current and future page.

Second implementation phase: historical PBJ backfill. It strengthens the existing facility trend, change-over-time, persistent-pattern, and affiliation tools without changing the core analytical concept.

Parallel acquisition work: download CMS Ownership, SNF CHOW, SNF CHOW Owner Information, Health Deficiencies, Fire Safety Deficiencies, Penalties, MDS QMs, and CT DSS rate/census/cost-report samples into archival directories. Do not integrate them until source-specific validation reports exist.

## Product Workflow Planning

The suite can eventually be presented around three primary entry points:

1. Facility Search / Facility Dossier: for users starting with a known nursing home.
2. Owner / Entity Search: for users starting with a person, organization, reported owner, manager, or affiliated entity.
3. Connecticut Statewide Exploration: for users scanning facilities, trends, persistent patterns, affiliations, ownership concentration, recent changes, or official CMS status indicators.

Deeper analytical pathways can remain available below those entry points: Change Over Time, Persistent Patterns, Ownership / Affiliation, and future deficiency/enforcement/financial modules.

Future concept only: a “Prepare Review Packet” action could generate a structured copyable packet organized by what the data shows, what it may suggest, what it cannot prove, and questions for further review. Do not implement until separately approved.
