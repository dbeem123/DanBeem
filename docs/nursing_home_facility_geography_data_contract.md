# Nursing Home Facility Geography Data Contract

Phase 11C.2 non-runtime data contract. This contract describes `data/nursing_home_facility_geography_ct.json`, a candidate Connecticut nursing home geography crosswalk for future county and regional comparison features.

## 1. Purpose

The geography crosswalk provides one CCN-keyed place to store current county context and future region assignments for Connecticut nursing home facilities. It is intended to support later county filters, facility-to-county comparison cards, and region-aware analysis after validation.

This file is not currently used by public runtime tools.

## 2. Source Files

- `source_data/provider_info/NH_ProviderInfo_Apr2026.csv`
- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_staffing_history_ct.json`
- `docs/nursing_home_facility_geography_crosswalk_validation_report.md`

## 3. Key Field Definitions

- `ccn`: CMS Certification Number, normalized to six characters.
- `facility_name`: best available display name, preferring Provider Information when matched.
- `current_runtime_facility`: true when the CCN exists in `data/nursing_home_staffing_ct.json`.
- `historical_pbj_facility`: true when the CCN exists in `data/nursing_home_staffing_history_ct.json`.
- `provider_info_match`: true when the CCN matched April 2026 CMS Provider Information.
- `provider_info_source_file`: Provider Information source filename when matched.
- `provider_info_snapshot`: human-readable Provider Information snapshot period.
- `address`, `city`, `state`, `zip_code`: Provider Information location fields when matched; current runtime fallback where Provider Information is unavailable.
- `county_name`: CMS Provider Information `County/Parish`, populated only for exact Provider Information CCN matches.
- `provider_ssa_county_code`: CMS Provider Information `Provider SSA County Code`, preserved separately from any future county FIPS field.
- `municipality`: currently the same as the matched/fallback city value; future phases may normalize Connecticut town names.
- `ltcop_region`, `aaa_region`, `dph_region`: reserved fields. They remain null until validated region mappings are approved.
- `match_method`: `ccn_exact` for Provider Information exact CCN matches, otherwise `unmatched`.
- `confidence`: `high` for exact Provider Information CCN matches, `needs_review` for unmatched records.
- `manual_review_required`: true when county cannot be populated from Provider Information or another issue requires review.
- `manual_review_reason`: concise explanation for review.
- `notes`: reserved for future validation notes.

## 4. Match Methodology

The builder uses exact CCN matching only. It does not infer county from city, ZIP, address, name, coordinates, or any other field.

The record universe is the union of:

- all current runtime CCNs;
- all historical PBJ facility CCNs;
- all Connecticut Provider Information CCNs in the April 2026 file.

## 5. County Limitations

County values are current CMS Provider Information context from April 2026. They are not historical quarter-specific geography. If a facility moved, closed, reopened, changed CCN, or changed address over time, this crosswalk should not be treated as proof of historical county assignment for every PBJ quarter.

Unmatched current facilities must keep `county_name` and `provider_ssa_county_code` null until manual review or a validated source resolves them. City, ZIP, address, and facility name may support review, but they are not sufficient to assign county in this contract.

## 6. Manual Review Flags

Records require manual review when they are not found in April 2026 Provider Information. Current unmatched records may reflect facilities in the runtime staffing export that do not appear in the current Provider Information snapshot. Historical-only unmatched records may represent closed, changed, or otherwise non-current facility context.

Unresolved records should not be assigned a county by guesswork.

## 7. Current Snapshot Versus Historical PBJ Separation

Historical PBJ rows remain PBJ-only. This crosswalk can be joined by CCN later for analysis or display, but geography should not be embedded into the historical PBJ file unless a later phase explicitly approves a historically appropriate enrichment method.

County joins for historical analysis are current-context joins unless historical geography snapshots are later added. Any historical PBJ display using this crosswalk must disclose that county is from current April 2026 Provider Information where available, not a validated historical county for each PBJ quarter.

## 8. Why Regional Fields Remain Null

LTCOP region, AAA region, and DPH region require validated source mappings. The builder does not infer region from county or municipality. Region fields remain null until official or project-approved mappings are documented.

## 9. Future Validation Needed Before Public County Filters

- review unmatched current runtime CCNs;
- review historical-only unmatched CCNs;
- confirm county labels and county-code semantics;
- decide whether to preserve county FIPS separately from Provider SSA county code;
- define refresh rules when Provider Information snapshots change;
- document how county filters should handle records with missing county;
- confirm public wording that county is current Provider Information context.
- require transparent handling of unknown county records in UI summaries, including an `Unknown / needs review` option or equivalent count/disclosure.

## 10. Future Refresh Process

On each Provider Information refresh:

1. archive the raw Provider Information file;
2. rerun the geography builder;
3. compare match counts, county completeness, manual-review counts, and county changes by CCN;
4. review any changed county, address, city, ZIP, or unmatched status before public use;
5. update the manual review queue.
