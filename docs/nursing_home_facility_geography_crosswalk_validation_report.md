# Nursing Home Facility Geography Crosswalk Validation Report

Phase 11C.1 validation report. This report is non-runtime planning output. It does not change public tool behavior, generated staffing data, formulas, Connecticut applicability logic, or existing runtime JSON.

Generated: 2026-05-31T20:01:58.932917+00:00

## 1. Purpose

This validation checks whether CMS Provider Information county fields can safely support a future Connecticut nursing home facility geography crosswalk keyed by CMS Certification Number (CCN).

The intended future use is county-level and regional comparison planning, not immediate runtime enrichment. County values should remain current Provider Information context until a future geography crosswalk is approved and integrated.

## 2. Source Files Used

- Provider Information: `source_data\provider_info\NH_ProviderInfo_Apr2026.csv`
- Current runtime staffing export: `data\nursing_home_staffing_ct.json`
- Historical PBJ staffing export: `data\nursing_home_staffing_history_ct.json`
- Optional testing preview JSON: `data\testing\nursing_home_facility_geography_ct_preview.json`

## 3. Methodology

The script:

1. Read CMS Provider Information April 2026.
2. Filtered Provider Information rows to Connecticut facilities where `State` is `CT`.
3. Extracted CCN, provider name, address, city, state, ZIP, `Provider SSA County Code`, and `County/Parish`.
4. Compared Provider Information CT CCNs with current runtime CCNs in `data/nursing_home_staffing_ct.json`.
5. Compared Provider Information CT CCNs with historical PBJ facility-directory CCNs in `data/nursing_home_staffing_history_ct.json`.
6. Checked duplicate CCNs, county completeness, address/ZIP completeness, and inconsistent county values by CCN.
7. Wrote a testing-only preview crosswalk schema for review.

## 4. Match Results

| Check | Count |
|---|---:|
| Provider Information CT facilities | 191 |
| Provider Information unique CT CCNs | 191 |
| Current runtime facilities | 196 |
| Current runtime unique CCNs | 196 |
| Historical PBJ unique CCNs | 216 |
| Current runtime CCNs matched to Provider Information | 191 |
| Current runtime CCNs unmatched to Provider Information | 5 |
| Provider Information CCNs not in current runtime | 0 |
| Historical PBJ CCNs matched to current Provider Information | 191 |
| Historical PBJ CCNs not found in current Provider Information | 25 |
| Duplicate Provider Information CT CCNs | 0 |
| Duplicate current runtime CCNs | 0 |
| Duplicate historical PBJ facility CCNs | 0 |

## 5. Unmatched and Review-Needed Records

### Current runtime CCNs unmatched to Provider Information

- `075001`
- `075351`
- `075415`
- `075432`
- `075441`

### Provider Information CT CCNs not in current runtime

None.

### Historical PBJ CCNs not found in current Provider Information

- `075001`
- `075013`
- `075028`
- `075069`
- `075082`
- `075096`
- `075102`
- `075106`
- `075185`
- `075205`
- `075210`
- `075234`
- `075251`
- `075280`
- `075282`
- `075328`
- `075340`
- `075346`
- `075351`
- `075370`
- `075415`
- `075417`
- `075426`
- `075432`
- `075441`

### Duplicate Provider Information CT CCNs

None.

### Inconsistent county values by CCN

None.

### Facilities missing County/Parish in Provider Information

Count: 0

None.

### Facilities missing Provider Address in Provider Information

Count: 0

None.

### Facilities missing ZIP Code in Provider Information

Count: 0

None.

## 6. Proposed Future Geography Crosswalk Schema

The future approved crosswalk can use this row shape:

```json
{
  "ccn": "075000",
  "facility_name": "",
  "address": "",
  "city": "",
  "state": "CT",
  "zip_code": "",
  "county_name": "",
  "provider_ssa_county_code": "",
  "municipality": "",
  "ltcop_region": null,
  "aaa_region": null,
  "dph_region": null,
  "match_source": "CMS Provider Information April 2026",
  "match_method": "ccn_exact",
  "confidence": "high",
  "manual_review_required": false,
  "notes": ""
}
```

Important distinctions:

- County can likely come from CMS Provider Information.
- `Provider SSA County Code` should be preserved separately from any future county FIPS field.
- Municipality can initially use the Provider Information `City/Town` field, but it should be normalized before public grouping.
- LTCOP region, AAA region, and DPH region should remain null until a validated source or approved crosswalk exists.
- Regional assignments must not be invented or inferred from county unless a source-approved mapping is documented.

## 7. County Readiness Recommendation

CMS Provider Information county fields appear sufficient for initial county-level validation and likely sufficient for a future county filter or county comparison layer after a reviewed crosswalk is approved.

Recommended readiness status: **ready for non-runtime crosswalk design, not yet integrated into public runtime data**.

Reasons:

- Provider Information has county fields in the archived April 2026 source.
- CCN is the shared key across Provider Information and the current runtime export.
- Current runtime data has address, city, state, and ZIP for most facilities, which supports review and exception handling.
- County is not yet in the runtime data contract, and 5 current runtime records are missing address/ZIP.

## 8. Future Crosswalk Recommendation

A future `data/nursing_home_facility_geography_ct.json` should be created only after:

1. the geography data contract is documented;
2. Provider Information county values are reviewed;
3. unmatched historical-only CCNs are classified;
4. missing address/ZIP records are reviewed;
5. duplicate and inconsistent county checks remain clean or are resolved;
6. manual-review flags are included for any unresolved records.

The crosswalk should be the source of truth. Runtime exports can later be enriched from it if a public feature needs county or regional fields.

## 9. Recommended First Implementation After Validation

Recommended first public implementation after validation: **county filter on Statewide Comparison**.

Rationale:

- It is simpler than county aggregation cards.
- It does not require immediate decisions about simple averages, weighted averages, medians, or county rankings.
- It lets users scan facilities within a county using existing row-level metrics and guardrails.

Recommended second implementation: **facility county/state comparison cards** in the Facility Explorer dossier after aggregation methodology is documented.

## 10. Guardrails

- County is current Provider Information context unless historical county/address snapshots are added.
- Historical PBJ rows should remain PBJ-only.
- County can be joined by CCN for analysis but should not imply historical geographic continuity if a facility location changed.
- Regional mappings require separate validation.
- Do not invent LTCOP, AAA, or DPH region assignments.
- Do not infer regions from county unless a source-approved mapping is documented.
- County and regional comparisons are screening context, not findings.
- Do not change staffing formulas, CT applicability logic, generated staffing data, or public runtime behavior as part of geography validation.
