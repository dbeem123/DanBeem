# Nursing Home Source Data Intake Guide

This directory holds local public-source files used or planned for the Connecticut LTCOP Nursing Home Staffing Transparency Tools.

Do not move or rename currently integrated files until the generator paths are intentionally migrated and retested. The current live generator expects:

- `source_data/pbj/*.csv` for the currently integrated PBJ quarters.
- `source_data/provider_info/NH_ProviderInfo_Apr2026.csv`
- `source_data/snf_enrollments/SNF_Enrollments_2026.05.01.csv`
- `source_data/quality_measures/NH_QualityMsr_Claims_Apr2026.csv`

## Intake Rules

- Keep each official release as an immutable snapshot.
- Prefer filenames that preserve the official CMS or Connecticut release month/date.
- Do not mix newly downloaded historical files into the live generator input directory until compatibility testing has been completed.
- Record any downloaded file in `data/nursing_home_source_manifest.json` or the refresh checklist before integrating it into public displays.
- Do not infer SFF, abuse icon, deficiencies, penalties, ownership, chain, or DSS financial indicators from unrelated fields.

## Recommended Directory Structure

### CMS Staffing

- `source_data/pbj/` - current live PBJ files used by the generator.
- `source_data/pbj/historical/2017/`
- `source_data/pbj/historical/2018/`
- `source_data/pbj/historical/2019/`
- `source_data/pbj/historical/2020/`
- `source_data/pbj/historical/2021/`
- `source_data/pbj/historical/2022/`
- `source_data/pbj/historical/2023/`
- `source_data/pbj/historical/2024/`

Historical PBJ backfill should be tested in stages:

1. One historical quarter.
2. One complete historical year.
3. Full historical archive after header, row-count, and audit checks pass.

### CMS Snapshot Sources

- `source_data/provider_info/snapshots/`
- `source_data/quality_measures/claims/`
- `source_data/quality_measures/mds/`
- `source_data/snf_enrollments/snapshots/`
- `source_data/ownership/snapshots/`
- `source_data/ownership_changes/`
- `source_data/deficiencies/`
- `source_data/penalties/`
- `source_data/sff/`
- `source_data/chain_performance/`

Archive each monthly or periodic CMS release before designating a latest file for future integration.

### Connecticut Sources

- `source_data/ct_dss/rates/`
- `source_data/ct_dss/census/`
- `source_data/ct_dss/case_mix_rates/`
- `source_data/ct_dss/cost_comparison/`
- `source_data/ct_dss/rate_computation/`
- `source_data/ct_dss/cost_reports/`
- `source_data/ct_dph/`
- `source_data/ct_dph/facilities/`
- `source_data/ct_dph/leadership_history/`
- `source_data/ct_dph/administrator_registry/`
- `source_data/ct_dph/management_companies/`
- `source_data/crosswalks/`

Connecticut DSS sources should not be merged into CCN-keyed facility displays until a DSS-to-CMS-CCN crosswalk is validated using stable identifiers such as provider number, license number, address, city, and facility name.

Connecticut DPH governance sources should be archived by snapshot and kept separate from live CMS staffing inputs. Preserve raw DPH license values and any future normalized `state_facility_license_id`; do not merge Administrator, Director of Nurses, Medical Director, or management-company records into CMS CCN-keyed displays until a DPH-to-CMS-CCN crosswalk is validated.

## Historical PBJ Backfill

Place historical quarterly PBJ CSVs under `source_data/pbj/historical/YYYY/` by calendar year. Keep them separate from `source_data/pbj/` until generator compatibility is tested. The planned next analytical expansion is historical PBJ backfill, but historical files should remain intake-only until validation confirms schema compatibility and historical caveats.
