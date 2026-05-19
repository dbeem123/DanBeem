# Nursing Home Staffing Explorer Data Contract

This document defines the static JSON contract used by `tools/nursing-home-staffing-explorer.html`.

The browser should load a small normalized JSON export only. Full CMS PBJ, Provider Information, and benchmark files should be processed offline in a later ETL step, then emitted into this contract.

## File

`data/nursing_home_staffing_mock.json`

## Top-Level Shape

```json
{
  "schema_version": "2.0-phase2a",
  "dataset_type": "nursing_home_staffing_explorer",
  "generated_at": "2026-05-18",
  "reporting_period": {},
  "sources": [],
  "facilities": [],
  "facility_quarterly_staffing": [],
  "field_map": {}
}
```

## Required Sections

### `reporting_period`

The quarter currently emphasized by the UI.

- `quarter`: normalized quarter key, such as `2025Q4`
- `label`: display label, such as `Q4 2025`
- `start_date`: ISO date
- `end_date`: ISO date

### `sources`

Source metadata for the static export.

- `source_dataset_name`: source file family or CMS dataset name
- `source_release`: release label, publication month, or CMS release identifier when available
- `freshness_date`: date the source was checked or exported
- `source_level`: `local mock data`, `official CMS export`, or another explicit source level
- `notes`: plain-language source caveat

### `facilities`

Facility directory rows keyed by CCN.

- `facility_id`: stable local slug or generated identifier
- `ccn`: CMS Certification Number
- `provider_name`: facility name from provider data
- `city`: provider city
- `state`: two-letter state abbreviation

### `facility_quarterly_staffing`

One row per facility per quarter.

- `ccn`: joins to `facilities.ccn`
- `quarter`: normalized quarter key
- `quarter_label`: display label
- `quarter_start_date`: ISO date
- `quarter_end_date`: ISO date
- `average_resident_census`: resident days divided by days in quarter, when available
- `resident_days`: resident-day denominator used for HPRD calculations, when available
- `metrics`: normalized staffing metrics
- `benchmarks`: optional comparison values
- `interpretation`: UI-ready plain-language interpretation for the selected reporting period
- `data_quality`: missing fields and row-level notes

## Metrics

`metrics` should contain:

- `total_nurse_hprd`
- `rn_hprd`
- `lpn_lvn_hprd`
- `nurse_aide_hprd`
- `contract_staff_pct`
- `ct_direct_care_total_hprd_estimate`
- `ct_direct_care_licensed_nurse_hprd_estimate`
- `ct_total_direct_care_minimum_hprd`
- `ct_licensed_direct_care_minimum_hprd`
- `ct_total_direct_care_difference_from_minimum`
- `ct_licensed_direct_care_difference_from_minimum`
- `ct_total_direct_care_below_minimum_estimate`
- `ct_licensed_direct_care_below_minimum_estimate`

Use `null` when a value is unavailable. Do not omit expected metric keys when the absence has meaning.

The Connecticut direct-care fields are PBJ-derived screening estimates for comparison to Connecticut Title 19 Sec. 19-13-D8t(m)(6). They are not formal Department of Public Health compliance determinations.

## Benchmarks

`benchmarks` should contain:

- `case_mix_total_nurse_hprd`
- `case_mix_rn_hprd`
- `case_mix_lpn_lvn_hprd`
- `case_mix_nurse_aide_hprd`
- `case_mix_benchmark_available`
- `benchmark_source`
- `benchmark_source_note`

Use `null` and `false` when no benchmark is included in the static export.

When populated from CMS Nursing Home Provider Information, case-mix fields are contextual provider-file benchmarks. They are not replacements for the PBJ-calculated actual staffing HPRD values in `metrics`.

## Interpretation Blocks

For the row matching `reporting_period.quarter`, `interpretation` may include:

- `shows`
- `suggests`
- `cannot_prove`

These are displayed directly by the UI. They must remain cautious and screening-level. They must not state or imply compliance findings, harm findings, causation, neglect, or resident-specific conclusions from HPRD alone.

## Future CMS Field Map

The exact column names may vary by CMS release, so Phase 2B should confirm names against the current official files before building the generator.

| App field | Future source |
|---|---|
| `ccn` | CMS Provider Information provider/CCN field and PBJ provider identifier |
| `provider_name` | CMS Provider Information provider name |
| `city` | CMS Provider Information city |
| `state` | CMS Provider Information state |
| `quarter` | PBJ reporting period, normalized to `YYYYQ#` |
| `average_resident_census` | `resident_days / days_in_quarter` |
| `resident_days` | PBJ resident census day denominator, when present in source export |
| `total_nurse_hprd` | `(RN hours + LPN/LVN hours + nurse aide hours) / resident_days` |
| `rn_hprd` | RN hours / resident days |
| `lpn_lvn_hprd` | LPN/LVN hours / resident days |
| `nurse_aide_hprd` | Nurse aide hours / resident days |
| `contract_staff_pct` | contract nursing hours / total nursing hours * 100, when employee/contract indicators are available |
| `ct_direct_care_total_hprd_estimate` | PBJ-derived CT screening estimate: `(Hrs_RN + Hrs_LPN + Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days` |
| `ct_direct_care_licensed_nurse_hprd_estimate` | PBJ-derived CT screening estimate: `(Hrs_RN + Hrs_LPN) / resident_days` |
| `ct_total_direct_care_minimum_hprd` | Connecticut Title 19 Sec. 19-13-D8t(m)(6) total nursing and nurse's aide personnel comparison point: 3.00 HPRD |
| `ct_licensed_direct_care_minimum_hprd` | Connecticut Title 19 Sec. 19-13-D8t(m)(6) licensed nursing personnel comparison point: 0.84 HPRD |
| `case_mix_total_nurse_hprd` | CMS case-mix adjusted nursing benchmark source, when included |
| `source_release` | CMS file release label or publication date captured by the offline generator |
| `freshness_date` | date the generator verified or exported the source file |

## Missing Data Rules

- Use `null` for unavailable numbers.
- Add the field name to `data_quality.missing_fields`.
- Use `data_quality.notes` for caveats that should inform future QA.
- Keep the facility row in the directory even when a quarterly staffing row is missing.
- The UI should show `Not available` rather than removing core metric cards.

## Phase 2B Input Files

Phase 2B adds an offline generator that reads manually supplied CMS PBJ CSV files and writes a Connecticut-only normalized export.

### Local Workflow

Place official CMS Payroll Based Journal Daily Nurse Staffing CSV files in:

`source_data/pbj/`

Then run:

```powershell
python scripts/build_nursing_home_staffing_ct.py --input-dir source_data/pbj --output data/nursing_home_staffing_ct.json
```

To enrich facility metadata with a manually downloaded CMS Nursing Home Provider Information file, use:

```powershell
python scripts/build_nursing_home_staffing_ct.py --input-dir source_data/pbj --provider-info source_data/provider_info/NH_ProviderInfo_MonYYYY.csv --output data/nursing_home_staffing_ct.json
```

To add CMS Skilled Nursing Facility Enrollments legal organization and affiliation context, use:

```powershell
python scripts/build_nursing_home_staffing_ct.py --input-dir source_data/pbj --provider-info source_data/provider_info/NH_ProviderInfo_MonYYYY.csv --snf-enrollments source_data/snf_enrollments/SNF_Enrollments_2026.05.01.csv --output data/nursing_home_staffing_ct.json
```

The explorer attempts to load `data/nursing_home_staffing_ct.json` first. If that generated file is not present, it falls back to `data/nursing_home_staffing_mock.json`.

### PBJ Columns Used

The generator expects these Daily Nurse Staffing source columns, with tolerant matching for minor case/spacing variants:

- `STATE`
- `PROVNUM`
- `PROVNAME`
- `CITY`
- `WorkDate` or `CY_Qtr`
- `MDScensus`
- `Hrs_RNDON`
- `Hrs_RNadmin`
- `Hrs_RN`
- `Hrs_LPNadmin`
- `Hrs_LPN`
- `Hrs_CNA`
- `Hrs_NAtrn`
- `Hrs_MedAide`

For contract percentage, the generator uses matching contract-hour columns when present:

- `Hrs_RNDON_ctr`
- `Hrs_RNadmin_ctr`
- `Hrs_RN_ctr`
- `Hrs_LPNadmin_ctr`
- `Hrs_LPN_ctr`
- `Hrs_CNA_ctr`
- `Hrs_NAtrn_ctr`
- `Hrs_MedAide_ctr`

If contract columns are unavailable or total nursing hours are zero, `contract_staff_pct` is `null`.

### Phase 2B Formulas

- `resident_days = sum(MDScensus)`
- `average_resident_census = simple average of daily MDScensus values in the source rows`
- `rn_hprd = (Hrs_RNDON + Hrs_RNadmin + Hrs_RN) / resident_days`
- `lpn_lvn_hprd = (Hrs_LPNadmin + Hrs_LPN) / resident_days`
- `nurse_aide_hprd = (Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days`
- `total_nurse_hprd = all RN + LPN/LVN + nurse aide categories / resident_days`
- `contract_staff_pct = sum(corresponding *_ctr nurse category hours) / total nurse category hours * 100`

### Connecticut Direct-Care Screening Comparison

Connecticut nursing home regulations, Title 19 Sec. 19-13-D8t(m)(6), establish direct-care staffing minimums of 2.17 total nursing and nurse's aide personnel HPRD from 7 a.m. to 9 p.m. plus 0.83 HPRD from 9 p.m. to 7 a.m., for a total of 3.00 HPRD. The same section establishes licensed nursing personnel minimums of 0.57 HPRD from 7 a.m. to 9 p.m. plus 0.27 HPRD from 9 p.m. to 7 a.m., for a total of 0.84 HPRD.

The regulation also states that the director of nurses or assistant director of nurses shall not be included in satisfying these minimum requirements. For PBJ screening purposes, the generator therefore excludes `Hrs_RNDON`, `Hrs_RNadmin`, and `Hrs_LPNadmin` from the Connecticut comparison fields while leaving the existing PBJ total nurse HPRD metric unchanged.

- `ct_direct_care_total_hprd_estimate = (Hrs_RN + Hrs_LPN + Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days`
- `ct_direct_care_licensed_nurse_hprd_estimate = (Hrs_RN + Hrs_LPN) / resident_days`
- `ct_total_direct_care_minimum_hprd = 3.00`
- `ct_licensed_direct_care_minimum_hprd = 0.84`
- `ct_total_direct_care_difference_from_minimum = ct_direct_care_total_hprd_estimate - 3.00`
- `ct_licensed_direct_care_difference_from_minimum = ct_direct_care_licensed_nurse_hprd_estimate - 0.84`
- `ct_total_direct_care_below_minimum_estimate = true` when the PBJ-derived total direct-care estimate is below 3.00
- `ct_licensed_direct_care_below_minimum_estimate = true` when the PBJ-derived licensed direct-care estimate is below 0.84

These fields are screening estimates derived from quarterly PBJ reporting. They do not determine legal compliance, do not establish whether a facility met staffing on any specific shift, and should not be labeled as violations.

### Daily Inclusion Logic

The Phase 2B generator follows the current-era CMS PBJ Public Use File aggregation approach for quarterly HPRD screening metrics:

- Include daily rows where `MDScensus > 0`.
- Exclude daily rows where `MDScensus` is zero, negative, missing, or malformed.
- For excluded zero-census days, do not add census to `resident_days`, do not add that day to `average_resident_census`, and do not add that day's nursing hours to numerator totals.
- Include daily rows with `MDScensus > 0` even when total included nursing hours are zero.
- Track non-zero-census days with zero total nursing hours in `included_zero_nursing_hours_day_count`; `excluded_zero_nursing_hours_day_count` remains `0` for current-era PBJ logic.

CMS's PBJ Public Use File technical specifications state that aggregate staffing calculations include only days with non-zero census, and for 2018Q4 and later files include all days with non-zero census even if zero nursing hours are reported. This generator is intended for 2025 PBJ files, so it uses that current-era rule.

Precision in generated output:

- HPRD metrics: 2 decimal places
- Contract staff percentage: 1 decimal place
- Average resident census: 1 decimal place

### Phase 2B Data Quality

The generator emits dataset-level and row-level quality notes:

- input file paths
- input row counts
- Connecticut row counts
- skipped row counts
- `input_daily_row_count`
- `included_daily_row_count`
- `excluded_zero_census_day_count`
- `included_zero_nursing_hours_day_count`
- `excluded_zero_nursing_hours_day_count`
- missing required source columns by file
- malformed numeric value counts
- facility-quarter row counts
- whether an available CMS incomplete indicator appeared for a facility-quarter
- zero or missing resident-day denominator flags

### Phase 2B Limitations

- The generator does not download CMS files.
- The browser never processes raw CMS CSV files.
- Provider Information and Care Compare staffing fields are not yet merged.
- Case-mix adjusted benchmark HPRD is left as `null` with `case_mix_benchmark_available: false`.
- Daily PBJ rows are aggregated to quarter-level screening metrics; the output should not be used to infer a specific resident's care, a specific shift, harm, neglect, or compliance findings.

## Phase 2C Provider Information Merge

Phase 2C adds optional enrichment from CMS Nursing Home Provider Information while preserving the PBJ-only flow.

### Merge Key

The merge key is:

- PBJ `PROVNUM`
- Provider Information `CMS Certification Number (CCN)` or equivalent CCN/provider-number column

Both values are treated as strings so leading zeroes are preserved.

### Provider Information Columns Supported

The generator uses tolerant column-name matching for these fields:

- `CMS Certification Number (CCN)`
- `Provider Name`
- `Provider Address`
- `Provider City`
- `Provider State`
- `Provider Zip Code`
- `Provider Phone Number`
- `Number of Certified Beds`
- `Ownership Type`
- `Case-Mix Nurse Aide Staffing Hours per Resident per Day`
- `Case-Mix LPN Staffing Hours per Resident per Day`
- `Case-Mix RN Staffing Hours per Resident per Day`
- `Case-Mix Total Nurse Staffing Hours per Resident per Day`
- optional date/status-like fields when present, such as participation or processing date

Column names should be verified against the first live CMS Provider Information file before production use.

### Facility Field Precedence

When a Provider Information row matches by CCN:

- `provider_name`: Provider Information `Provider Name` when nonblank; otherwise PBJ `PROVNAME`
- `city`: Provider Information city when nonblank; otherwise PBJ `CITY`
- `state`: Provider Information state when nonblank; otherwise PBJ `STATE`
- `address`, `zip_code`, `phone_number`, `certified_beds`, `ownership_type`: Provider Information only

When no Provider Information row matches, the facility remains in the export with PBJ-derived name, city, and state.

Facility-level merge diagnostics include:

- `provider_source_matched`
- `pbj_provider_name`
- `provider_info_provider_name`
- `metadata_source`

Dataset-level merge diagnostics in `data_quality` include:

- `provider_info_file_supplied`
- `pbj_facility_count`
- `provider_info_row_count`
- `matched_facility_count`
- `unmatched_pbj_facility_count`
- `unmatched_provider_info_row_count`
- `provider_info_missing_columns`
- `provider_info_duplicate_ccn_count`

The merge matters because PBJ files are staffing submissions, while Provider Information is a better source for standardized facility directory metadata and stable public-facing facility descriptors.

## Phase 4A SNF Enrollments Merge

Phase 4A adds optional enrichment from CMS Skilled Nursing Facility Enrollments. This source is used for legal organization and affiliation context only.

### Merge Key

The merge key is:

- staffing export / PBJ `PROVNUM`
- SNF Enrollments `CCN`

Both values are treated as strings so leading zeroes are preserved.

### SNF Enrollment Columns Supported

- `CCN`
- `NPI`
- `ORGANIZATION NAME`
- `DOING BUSINESS AS NAME`
- `PROPRIETARY_NONPROFIT`
- `ORGANIZATION TYPE STRUCTURE`
- `NURSING HOME PROVIDER NAME`
- `AFFILIATION ENTITY NAME`
- `AFFILIATION ENTITY ID`
- `INCORPORATION STATE`
- `INCORPORATION DATE`
- `ENROLLMENT STATE`
- `STATE`

### Field Purpose And Precedence

Provider Information remains the primary source for current facility display metadata: provider name, address, city, state, ZIP code, phone, certified beds, ownership type, and case-mix benchmark fields.

SNF Enrollments adds enrollment context:

- `enrollment_source_matched`
- `enrollment_npi`
- `enrollment_organization_name`
- `enrollment_doing_business_as_name`
- `enrollment_proprietary_nonprofit`
- `enrollment_organization_type_structure`
- `enrollment_nursing_home_provider_name`
- `affiliation_entity_name`
- `affiliation_entity_id`
- `incorporation_state`
- `incorporation_date`

These fields do not overwrite Provider Information display fields. They are intended to support later ownership, chain, and affiliation analysis.

Dataset-level merge diagnostics include:

- `snf_enrollments_file_supplied`
- `snf_enrollments_file`
- `snf_enrollments_row_count`
- `snf_enrollments_ct_row_count`
- `matched_snf_enrollment_facility_count`
- `unmatched_pbj_facility_count_for_snf_enrollments`
- `unmatched_snf_enrollment_row_count`
- `snf_enrollments_duplicate_ccn_count`
- `snf_enrollments_missing_columns`

Affiliation entity fields may support a later Connecticut chain-summary view, but this phase does not calculate chain-level performance metrics.

### Case-Mix Benchmark Enrichment

When Provider Information is supplied and matched by CCN, the generator copies CMS Provider Information case-mix staffing HPRD fields into each matched facility-quarter row's `benchmarks` object:

- `case_mix_total_nurse_hprd`
- `case_mix_rn_hprd`
- `case_mix_lpn_lvn_hprd`
- `case_mix_nurse_aide_hprd`
- `case_mix_benchmark_available`
- `benchmark_source`
- `benchmark_source_note`

These fields are contextual benchmark values from the Provider Information file. They should be displayed as comparison context only. They are not PBJ actual staffing calculations, not legal minimums, and not proof of sufficiency, compliance, harm, or noncompliance.

Reporting-period caveat: the Provider Information file may not align exactly with the PBJ quarter being aggregated. The export records the benchmark source as Provider Information and includes a source note so the UI and future analysis do not imply precise quarter alignment unless a later ETL step verifies it.

## Phase 2C Source Needs

The next phase should identify and download official CMS source files outside the browser, then generate this static JSON:

- CMS PBJ staffing data by facility and quarter, with nurse role hours and resident-day denominator
- CMS Provider Information or Care Compare provider file for CCN, name, city, state, and active provider status
- contract/employee staffing indicators if not already included in the PBJ summary source
- optional CMS case-mix adjusted staffing benchmark source, if the explorer will display benchmark comparisons
- release metadata or publication dates for every source used
