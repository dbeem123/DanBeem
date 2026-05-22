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
- `cms_overall_rating`, `cms_health_inspection_rating`, `cms_staffing_rating`, `cms_rn_staffing_rating`, `cms_qm_rating`, `cms_long_stay_qm_rating`, `cms_short_stay_qm_rating`: optional CMS Care Compare rating context imported from Provider Information when available
- `cms_rating_source`, `cms_rating_source_note`: source and caveat text for imported CMS Care Compare ratings
- `quality_measures_claims`: optional facility-level array of CMS Nursing Home Quality Measures Claims rows merged by CCN

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

The Connecticut direct-care fields are PBJ-derived screening estimates for comparison to Connecticut Title 19 Sec. 19-13-D8t nursing-staff requirements and Connecticut Department of Public Health's amended 3.0 staffing implementation notice. They are not formal Department of Public Health compliance determinations.

The below-comparison flags are currently based on the rounded two-decimal CT estimate fields stored in the export. This matches the UI display, but may differ from an unrounded comparison for values extremely close to 3.00 or 0.84.

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

When populated from CMS Nursing Home Provider Information, case-mix fields are contextual provider-file comparison points. The value for `case_mix_total_nurse_hprd` is copied from the CMS Nursing Home Provider Information field `Case-Mix Total Nurse Staffing Hours per Resident per Day`; it is not calculated by this project. CMS describes that field as case-mix total nurse staffing HPRD combining Aide + LPN + RN. The browser may compare PBJ-reported actual total nurse HPRD in `metrics.total_nurse_hprd` against that CMS-published comparison point; actual-minus-benchmark and percent-of-benchmark display text are project-calculated comparisons. These fields are not replacements for the PBJ-calculated actual staffing HPRD values in `metrics`. In the current generated Connecticut export, April 2026 Provider Information case-mix benchmark values are reused across historical PBJ quarter rows where provider matches exist; they are not verified quarter-specific benchmark snapshots for each PBJ quarter.

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
| `ct_total_direct_care_minimum_hprd` | Connecticut total nursing and nurse's aide personnel comparison point: 3.00 HPRD |
| `ct_licensed_direct_care_minimum_hprd` | Connecticut licensed nursing personnel comparison point: 0.84 HPRD |
| `case_mix_total_nurse_hprd` | Imported CMS Nursing Home Provider Information field `Case-Mix Total Nurse Staffing Hours per Resident per Day`; contextual comparison point, not calculated by this project |
| `cms_overall_rating` | Imported CMS Nursing Home Provider Information `Overall Rating`; contextual CMS Care Compare rating, not calculated by this project |
| `cms_health_inspection_rating` | Imported CMS Nursing Home Provider Information `Health Inspection Rating`; contextual CMS Care Compare rating, not calculated by this project |
| `cms_staffing_rating` | Imported CMS Nursing Home Provider Information `Staffing Rating`; contextual CMS Care Compare rating, not a replacement for PBJ HPRD metrics |
| `cms_rn_staffing_rating` | Imported CMS Nursing Home Provider Information `RN Staffing Rating` when present; optional contextual CMS Care Compare rating |
| `cms_qm_rating` | Imported CMS Nursing Home Provider Information `QM Rating`; contextual CMS Care Compare rating, not calculated by this project |
| `cms_long_stay_qm_rating` | Imported CMS Nursing Home Provider Information `Long-Stay QM Rating`; contextual CMS Care Compare rating, not calculated by this project |
| `cms_short_stay_qm_rating` | Imported CMS Nursing Home Provider Information `Short-Stay QM Rating`; contextual CMS Care Compare rating, not calculated by this project |
| `quality_measures_claims` | Facility-level CMS Nursing Home Quality Measures Claims rows; contextual Care Compare quality-measure data, not calculated by this project |
| `measure_code` | CMS Quality Measures Claims measure code |
| `measure_description` | CMS Quality Measures Claims measure description |
| `resident_type` | CMS Quality Measures Claims resident type |
| `adjusted_score` | CMS Quality Measures Claims adjusted score, parsed as numeric when available |
| `observed_score` | CMS Quality Measures Claims observed score, parsed as numeric when available |
| `expected_score` | CMS Quality Measures Claims expected score, parsed as numeric when available |
| `footnote_for_score` | CMS Quality Measures Claims score footnote |
| `used_in_qm_five_star_rating` | Whether CMS marks the measure as used in the Quality Measure Five-Star Rating |
| `measure_period` | CMS Quality Measures Claims measure period |
| `source_release` | CMS file release label or publication date captured by the offline generator |
| `freshness_date` | date the generator verified or exported the source file |

## Public Source References

Public methodology links are maintained in `tools/nursing-home-staffing-methodology.html`. Core references include:

- CMS Payroll-Based Journal Daily Nurse Staffing dataset: `https://data.cms.gov/quality-of-care/payroll-based-journal-daily-nurse-staffing`
- CMS Payroll-Based Journal Daily Nursing Staffing Data Dictionary: `https://data.cms.gov/sites/default/files/2023-06/Payroll%20Based%20Journal%20Daily%20Nursing%20Staffing%20Data%20Dictionary.pdf`
- CMS Nursing Home Provider Information dataset: `https://data.cms.gov/provider-data/dataset/4pq5-n9py`
- CMS nursing home quality-measure data: `https://data.cms.gov/provider-data/topics/nursing-homes/quality-measures`
- CMS Nursing Home Data Dictionary: `https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/nursing_home/NH_Data_Dictionary.pdf`
- CMS Skilled Nursing Facility Enrollments dataset: `https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-enrollments`
- Connecticut nursing home staffing regulations, Title 19, Sec. 19-13-D8t: `https://eregulations.ct.gov/eRegsPortal/Browse/RCSA/Title_19Subtitle_19-13Section_19-13-d8t/`
- Connecticut DPH amended 3.0 staffing implementation notice: `https://portal.ct.gov/-/media/departments-and-agencies/dph/facility-licensing--investigations/blast-faxes/2024/blast-fax-2024-3a--amendments-to-policies-and-procedures-implementing-30-staffing-revised.pdf`

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

Connecticut Title 19 Sec. 19-13-D8t establishes nursing-staff requirements in subsection (m). Connecticut DPH's amended 3.0 staffing implementation notice describes the current comparison points used here: 2.17 total nursing and nurse's aide personnel HPRD from 7 a.m. to 9 p.m. plus 0.83 HPRD from 9 p.m. to 7 a.m., for a total of 3.00 HPRD. The same notice describes licensed nursing personnel minimums of 0.57 HPRD from 7 a.m. to 9 p.m. plus 0.27 HPRD from 9 p.m. to 7 a.m., for a total of 0.84 HPRD.

The regulation also states that the director of nurses or assistant director of nurses shall not be included in satisfying these minimum requirements. For PBJ screening purposes, the generator therefore excludes `Hrs_RNDON`, `Hrs_RNadmin`, and `Hrs_LPNadmin` from the Connecticut comparison fields while leaving the existing PBJ total nurse HPRD metric unchanged.

- `ct_direct_care_total_hprd_estimate = (Hrs_RN + Hrs_LPN + Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days`
- `ct_direct_care_licensed_nurse_hprd_estimate = (Hrs_RN + Hrs_LPN) / resident_days`
- `ct_total_direct_care_minimum_hprd = 3.00`
- `ct_licensed_direct_care_minimum_hprd = 0.84`
- `ct_total_direct_care_difference_from_minimum = ct_direct_care_total_hprd_estimate - 3.00`
- `ct_licensed_direct_care_difference_from_minimum = ct_direct_care_licensed_nurse_hprd_estimate - 0.84`
- `ct_total_direct_care_below_minimum_estimate = true` when the PBJ-derived total direct-care estimate is below 3.00
- `ct_licensed_direct_care_below_minimum_estimate = true` when the PBJ-derived CT licensed HPRD estimate is below 0.84

These fields are screening estimates derived from quarterly PBJ reporting. They do not determine legal compliance, do not establish whether a facility met staffing on any specific shift, and should not be labeled as violations.

Implementation note: `ct_total_direct_care_below_minimum_estimate` and `ct_licensed_direct_care_below_minimum_estimate` are evaluated against the rounded two-decimal CT estimate fields stored in the export. This keeps the flags aligned with the displayed values, but an unrounded comparison could differ for values extremely close to 3.00 or 0.84.

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
- Provider Information and CMS Care Compare rating context were outside the original Phase 2B scope; Phase 8A merges available rating fields from the local Provider Information file.
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
- `Overall Rating`
- `Health Inspection Rating`
- `Staffing Rating`
- `RN Staffing Rating`, when present in the Provider Information release
- `QM Rating`
- `Long-Stay QM Rating`
- `Short-Stay QM Rating`
- optional date/status-like fields when present, such as participation or processing date

Column names should be verified against the first live CMS Provider Information file before production use.

### Facility Field Precedence

When a Provider Information row matches by CCN:

- `provider_name`: Provider Information `Provider Name` when nonblank; otherwise PBJ `PROVNAME`
- `city`: Provider Information city when nonblank; otherwise PBJ `CITY`
- `state`: Provider Information state when nonblank; otherwise PBJ `STATE`
- `address`, `zip_code`, `phone_number`, `certified_beds`, `ownership_type`: Provider Information only
- CMS Care Compare rating fields are copied from Provider Information when present. They are facility-level contextual ratings and do not overwrite PBJ staffing metrics, CT direct-care estimates, or case-mix comparison fields.

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
- `provider_rating_fields_available`
- `provider_rating_missing_columns`
- `facilities_with_overall_rating_count`
- `facilities_with_qm_rating_count`
- `facilities_with_staffing_rating_count`

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

These fields are contextual comparison values from the Provider Information file. The benchmark value itself is imported from CMS, not calculated by this project. The `case_mix_total_nurse_hprd` value comes from the CMS Nursing Home Provider Information field `Case-Mix Total Nurse Staffing Hours per Resident per Day`, which CMS describes as case-mix total nurse staffing HPRD combining Aide + LPN + RN. Project UI code may calculate differences or percent-of-benchmark text by comparing PBJ actual total nurse HPRD against the CMS-published case-mix total nurse HPRD comparison point. They should be displayed as comparison context only. They are not PBJ actual staffing calculations, not legal minimums, and not proof of sufficiency, compliance, harm, neglect, poor care, or noncompliance.

Reporting-period caveat: the Provider Information file may not align exactly with the PBJ quarter being aggregated. In the current generated Connecticut export, April 2026 Provider Information case-mix benchmark values are copied into each historical PBJ facility-quarter row where the CCN matches. These are contextual comparison points only, not verified quarter-specific benchmark snapshots for each PBJ quarter. The export records the benchmark source as Provider Information and includes a source note so the UI and future analysis do not imply precise quarter alignment unless a later ETL step verifies it.

### CMS Care Compare Rating Context

When Provider Information is supplied and matched by CCN, the generator copies available CMS Care Compare rating fields into each matched `facilities[]` row:

- `cms_overall_rating`
- `cms_health_inspection_rating`
- `cms_staffing_rating`
- `cms_rn_staffing_rating`
- `cms_qm_rating`
- `cms_long_stay_qm_rating`
- `cms_short_stay_qm_rating`
- `cms_rating_source`
- `cms_rating_source_note`

These fields are imported from CMS Nursing Home Provider Information. They are not calculated by this project and do not replace PBJ-calculated HPRD metrics, CT direct-care screening estimates, case-mix comparison points, survey records, complaint records, or resident experience. Missing rating columns are reported in `data_quality.provider_rating_missing_columns`; a missing rating value should remain `null`, not zero.

### CMS Quality Measures Claims Enrichment

Phase 8B adds optional enrichment from the CMS Nursing Home Quality Measures Claims file while preserving the staffing-focused export. The merge key is CCN. Only Connecticut rows are retained.

Supported source fields:

- `CMS Certification Number (CCN)`
- `Provider Name`
- `State`
- `Measure Code`
- `Measure Description`
- `Resident type`
- `Adjusted Score`
- `Observed Score`
- `Expected Score`
- `Footnote for Score`
- `Used in Quality Measure Five Star Rating`
- `Measure Period`
- `Processing Date`

When a Quality Measures Claims row matches a facility by CCN, the generator appends a normalized object to `facilities[].quality_measures_claims[]`:

- `measure_code`
- `measure_description`
- `resident_type`
- `adjusted_score`
- `observed_score`
- `expected_score`
- `footnote_for_score`
- `used_in_qm_five_star_rating`
- `measure_period`
- `processing_date`
- `quality_measure_source`

These rows are imported CMS Care Compare quality-measure context. They are not calculated by this project, are not staffing measures, and do not replace PBJ staffing metrics, CT direct-care screening estimates, CMS rating summaries, survey findings, complaints, resident experience, or formal review. Missing or nonnumeric scores should remain `null`, not zero.

Dataset-level diagnostics include:

- `quality_measures_claims_file_supplied`
- `quality_measures_claims_row_count`
- `quality_measures_claims_ct_row_count`
- `facilities_with_quality_measures_claims_count`
- `quality_measures_claims_measure_count`
- `quality_measures_claims_missing_columns`
- `unmatched_quality_measure_ccn_count`

## Phase 2C Source Needs

The next phase should identify and download official CMS source files outside the browser, then generate this static JSON:

- CMS PBJ staffing data by facility and quarter, with nurse role hours and resident-day denominator
- CMS Provider Information or Care Compare provider file for CCN, name, city, state, and active provider status
- contract/employee staffing indicators if not already included in the PBJ summary source
- optional CMS case-mix adjusted staffing benchmark source, if the explorer will display benchmark comparisons
- release metadata or publication dates for every source used
