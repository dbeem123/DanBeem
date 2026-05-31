# County and Regional Comparison Validation

Phase 11C planning document. This document does not change application behavior, runtime data, generated exports, formulas, Connecticut applicability logic, or public tool behavior.

## 1. Purpose

This document validates the current state of geography data for future Connecticut nursing home county and regional comparisons. It answers whether the current integrated staffing exports already contain county information, proposes a safe facility geography model, and recommends a phased path for future county, Connecticut regional, and nearby-state comparisons.

The goal is to support future product work such as:

- comparing one facility with its county and statewide Connecticut;
- adding county filters to statewide tools;
- summarizing county-level staffing patterns;
- supporting future LTCOP, AAA, DPH, or other Connecticut regional groupings;
- eventually supporting nearby-state or New England comparisons using common CMS measures only.

No public UI should be built from this document until a geography crosswalk and validation report are approved.

## 2. Current Data Findings

Current integrated files inspected:

- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_staffing_history_ct.json`
- `data/nursing_home_source_manifest.json`
- `data/current_tool_context_registry.json`

Relevant documentation inspected:

- `docs/nursing_home_advanced_facility_dossier_roadmap.md`
- `docs/nursing_home_data_acquisition_roadmap.md`
- `docs/nursing_home_data_refresh_checklist.md`
- `docs/nursing_home_staffing_data_contract.md`

Current integrated runtime findings:

- `data/nursing_home_staffing_ct.json` contains 196 current/context facility records.
- Those 196 current/context records have 196 unique CCNs and no duplicate CCNs.
- All 196 current/context records have `city` and `state`.
- All 196 current/context records are `CT`.
- 5 current/context records are missing `address`.
- 5 current/context records are missing `zip_code`.
- No county-like field is present in the current integrated facility records.
- `data/nursing_home_staffing_history_ct.json` contains 216 historical PBJ facility directory records and 6,569 historical facility-quarter rows.
- The historical facility directory has 216 unique CCNs and no duplicate CCNs.
- Historical facility records contain `ccn`, `latest_pbj_provider_name`, `latest_pbj_city`, and `state`.
- No county-like field is present in the historical PBJ facility directory.

Source-file finding:

- The raw `source_data/provider_info/NH_ProviderInfo_Apr2026.csv` header includes `Provider SSA County Code` and `County/Parish`.
- Those Provider Information county fields are not currently integrated into `data/nursing_home_staffing_ct.json`.
- This means county may be available from an already archived official CMS source, but it has not yet been validated, normalized, added to the data contract, or emitted into runtime JSON.

## 3. Whether County Exists Now

County does not exist in the current integrated runtime data.

The current/context export includes address, city, state, and ZIP fields that can support future geography matching. It does not include `county`, `county_name`, `county_code`, `Provider SSA County Code`, or `County/Parish`.

The historical PBJ-only export does not include county, address, or ZIP. It only carries latest PBJ city and state in the facility directory. Historical PBJ rows should remain PBJ-only unless a future crosswalk or geography context layer is intentionally joined as a separate, documented enrichment.

The safest interpretation is:

- Current public tools cannot support county display today without a data contract change.
- The raw CMS Provider Information file appears to contain county fields that are likely useful for a first validation pass.
- A separate facility geography crosswalk should be created and validated before runtime enrichment.

## 4. Proposed Geography/Crosswalk Model

Recommended source-of-truth model: create a separate facility geography crosswalk JSON after validation, then optionally enrich runtime exports later.

Proposed future file:

- `data/nursing_home_facility_geography_ct.json`

Recommended top-level structure:

```json
{
  "schema_version": "draft",
  "dataset_type": "ct_nursing_home_facility_geography_crosswalk",
  "generated_at": "YYYY-MM-DD",
  "sources": [],
  "data_quality": {},
  "facilities": []
}
```

Recommended facility fields:

- `ccn`
- `provider_name`
- `address`
- `city`
- `state`
- `zip_code`
- `county_name`
- `county_fips`
- `provider_ssa_county_code`
- `municipality`
- `ltcop_region_id`
- `ltcop_region_name`
- `aaa_region_id`
- `aaa_region_name`
- `dph_region_id`
- `dph_region_name`
- `source_fields`
- `match_method`
- `match_confidence`
- `manual_review_status`
- `notes`

Recommended geography dimension fields:

- county: county name, FIPS code, optional SSA county code, state.
- municipality/town: normalized Connecticut municipality/town name.
- LTCOP region: only after official/current LTCOP region definitions are confirmed.
- Area Agency on Aging region: only if relevant to LTCOP workflow and official region definitions are documented.
- DPH region: only if official source definitions are located and the region is useful for oversight interpretation.
- state: `CT` for Connecticut-only files.
- future nearby-state groupings: separate regional architecture, not folded into the CT-only crosswalk by default.

Recommended architecture:

- Keep the crosswalk JSON as the source of truth.
- Later, enrich current/context runtime facility records with selected geography fields only after validation.
- Keep historical PBJ rows PBJ-only. If historical tools need county grouping, they can join CCN to the geography crosswalk at runtime or during a clearly documented enrichment step.
- Do not add county or region values manually inside UI code.

Why a separate crosswalk is safer:

- It separates geography validation from staffing formulas.
- It allows manual review flags and confidence scores.
- It can support multiple region systems without bloating the staffing export.
- It can be reused by future survey, ownership, DPH governance, DSS, and regional comparison modules.

## 5. County Comparison Product Concepts

Recommended future county comparison outputs:

1. Facility compared to county and statewide.
   - Best fit for the Facility Explorer/dossier.
   - Shows the selected facility next to county and statewide context for the same metric and quarter/window.
   - Suggested first metrics: total nurse HPRD, RN HPRD, nurse aide HPRD, contract staff percentage, CT direct-care HPRD estimate, CT licensed HPRD estimate.

2. Statewide table county filter.
   - Best fit for the Statewide Comparison tool.
   - Lets users filter current statewide rows to one county.
   - Low conceptual complexity once county is validated.

3. County summary cards.
   - Shows facility count, latest-quarter average or median staffing metrics, count below CT comparison points, and contract staffing context.
   - Should disclose whether values are simple facility averages, resident-day weighted averages, medians, or counts.

4. County ranking table.
   - Compares counties on selected current metrics.
   - Should be introduced cautiously because county rankings can be overread as quality rankings.

5. County persistent-pattern summary.
   - Uses historical PBJ windows to summarize repeated patterns within county groups.
   - Requires clear rules for missing PBJ rows and CT applicability periods.

Recommended display order:

1. Add county filters to statewide tools after crosswalk validation.
2. Add facility-to-county/statewide comparison cards to the Facility Explorer/dossier.
3. Add county summary cards after aggregation rules are approved.
4. Add county persistent-pattern summaries after historical aggregation rules are tested.
5. Defer county ranking tables until wording and methodology are reviewed.

## 6. Connecticut Regional Comparison Product Concepts

Potential Connecticut regional layers:

- county;
- municipality/town;
- LTCOP region or service region;
- Area Agency on Aging region, if relevant;
- DPH region, if relevant;
- statewide Connecticut.

Potential future outputs:

- facility compared with LTCOP region and statewide;
- region filter on statewide tools;
- region summary cards;
- region persistent-pattern summaries;
- region-level quality-measure or enforcement summaries after those sources are validated;
- internal review packets organized by county or region.

Validation dependencies:

- Official or approved region definitions.
- Stable region identifiers and names.
- Facility-to-region mapping rules.
- Handling for facilities that move, close, reopen, change address, or have ambiguous city/town names.
- Manual review of unmatched and ambiguous facilities.

Recommended rule:

Do not create regional comparisons until the exact region system is named and documented. "Region" should never be a generic field without a defined authority and purpose.

## 7. Nearby-State Comparison Product Concepts

Nearby-state comparison should be handled separately from Connecticut-only runtime exports.

Potential comparison groups:

- Connecticut and Massachusetts;
- Connecticut and Rhode Island;
- Connecticut and New York;
- Connecticut and New Jersey;
- Connecticut and New England;
- Connecticut and a custom nearby-state peer set.

Rules:

- Use common CMS measures only.
- Do not apply Connecticut thresholds to non-Connecticut facilities.
- Do not show CT direct-care comparison status for non-CT facilities.
- Do not merge nearby-state facilities into `data/nursing_home_staffing_ct.json`.
- Use controlled multi-state extracts with their own source dates, data contract, and audit checks.

Likely future architecture:

- a separate regional/multi-state dataset;
- a separate regional data contract;
- explicit state filters;
- common CMS metric definitions only;
- optional Connecticut-only overlay fields that remain disabled for non-CT rows.

Nearby-state comparisons should come after county and Connecticut regional validation because they introduce more source volume, more policy differences, and higher interpretation risk.

## 8. Data Quality and Validation Requirements

Before public county or region use, run and document these checks:

- CCN match count between current/context facilities and geography crosswalk.
- Historical CCN coverage count against the PBJ-only history facility directory.
- Unmatched current facilities.
- Unmatched historical-only facilities.
- Duplicate CCNs in the geography crosswalk.
- Duplicate geography rows per CCN.
- Ambiguous town/address matches.
- Facilities with missing address.
- Facilities with missing ZIP.
- Facilities with missing county.
- Facilities with county values that conflict across sources.
- County totals compared against expected Connecticut facility count.
- County names normalized to a consistent canonical list.
- County FIPS codes validated where available.
- Provider SSA county code retained separately from county FIPS.
- Manual-review status for every non-exact match.
- Region assignment completeness for each approved region system.
- Source snapshot date and generation date recorded.

Initial current/context validation baseline:

- 196 current/context facilities.
- 196 unique current/context CCNs.
- 0 duplicate current/context CCNs.
- 5 missing current/context addresses.
- 5 missing current/context ZIP codes.
- 196 current/context records have city and state.
- 196 current/context records are in `CT`.

Initial historical validation baseline:

- 216 historical PBJ facility directory records.
- 216 unique historical CCNs.
- 0 duplicate historical CCNs.
- 6,569 historical PBJ facility-quarter rows.
- 6,569 historical PBJ rows are in `CT`.

Recommended first validation script outputs:

- `docs/nursing_home_county_crosswalk_validation_report.md`
- optional non-runtime draft crosswalk under `source_data/geography/` or `data/working/` if such a working area is approved later
- no runtime JSON update until validation is approved

## 9. Guardrails

- County and regional comparisons are screening context, not findings.
- Do not make causation claims.
- Do not make legal compliance claims without official confirmation.
- Connecticut thresholds apply only to Connecticut facilities and applicable periods.
- Do not apply Connecticut staffing thresholds to nearby-state facilities.
- Keep current CMS snapshot context separate from historical PBJ rows.
- Keep geography crosswalk validation separate from staffing formula logic.
- Disclose whether aggregates are simple averages, weighted averages, medians, counts, or percentages.
- Do not rank counties or regions as "best" or "worst" without careful wording and methodology.
- Small counties or regions may require caveats because a few facilities can drive results.
- Source freshness and audit trail are required before every new geography data layer.
- If county is sourced from CMS Provider Information, label it as CMS Provider Information county context and preserve the snapshot date.
- If county is derived from address geocoding or external crosswalks, document the method and confidence.

## 10. Recommended Next Implementation Sequence

Recommended first implementation phase after this validation:

Phase 11C.1: create a non-runtime county crosswalk validation script and report.

Objective:

- Extract `Provider SSA County Code` and `County/Parish` from archived CMS Provider Information.
- Match by CCN to the current/context facility records.
- Produce a validation report with match counts, missing county values, duplicate CCNs, county distribution, and conflicts.

Expected artifacts:

- a validation script under `scripts/` or a one-time documented analysis command, if approved;
- `docs/nursing_home_county_crosswalk_validation_report.md`;
- optionally a draft geography crosswalk file if the project approves a working-data location.

Out of scope:

- public UI changes;
- runtime data enrichment;
- generated staffing data changes;
- formulas;
- CT applicability logic;
- regional/multi-state datasets.

Recommended second implementation phase:

Phase 11C.2: design the geography crosswalk data contract.

Expected artifacts:

- `docs/nursing_home_facility_geography_data_contract.md`;
- draft schema for `data/nursing_home_facility_geography_ct.json`;
- validation checklist for county, town, LTCOP region, AAA region, DPH region, and state.

Recommended first public product phase after validation:

Add county filters to statewide tools first.

Rationale:

- County filtering is easier to explain than aggregation cards.
- It uses row-level facility geography without needing new aggregation methodology.
- It helps users scan facilities within a county before introducing county averages or rankings.

Recommended next public product phase:

Add "compare this facility to county and statewide" cards in the Facility Explorer/dossier.

Rationale:

- The Phase 11B dossier layout already has a natural location for local comparison cards.
- Facility-to-county/statewide comparison is more consumer-friendly than county rankings.
- It should come after aggregation rules are documented, especially simple average versus resident-day weighted average.

Deferred phases:

- county summary cards;
- county ranking table;
- county persistent-pattern summary;
- LTCOP/AAA/DPH region summaries;
- nearby-state or New England comparison datasets.

