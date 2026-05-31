# County Filter Readiness Decision

Phase 11C.3 decision document, updated after Phase 11C.4 implementation. It documents the readiness basis and the narrow county-filter implementation path. It does not modify staffing formulas or generated staffing/PBJ files.

## Purpose

This document decides whether the candidate facility geography crosswalk can support a first public county filter on the Connecticut Statewide Staffing Comparison tool, with transparent handling for records whose county remains unavailable pending manual review.

## Crosswalk Coverage

The candidate crosswalk `data/nursing_home_facility_geography_ct.json` contains:

| Measure | Count |
|---|---:|
| Total crosswalk records | 216 |
| Current runtime records included | 196 |
| Historical PBJ records included | 216 |
| Provider Information matched records | 191 |
| Current runtime unmatched records | 5 |
| Historical PBJ unmatched records | 25 |
| Records with county populated | 191 |
| Records requiring manual review | 25 |
| Duplicate CCNs | 0 |
| Missing CCN values | 0 |
| Provider Information matches missing county | 0 |

The 191 Provider Information matches have complete `county_name` and `provider_ssa_county_code` fields. LTCOP, AAA, and DPH region fields remain null.

## Unmatched Accounting Clarification

The 5 current-runtime unmatched CCNs are included within the 25 historical PBJ unmatched CCNs. They are not 30 distinct review records.

Distinct manual-review records:

- 25 total CCNs require manual review.
- 5 are present in both current runtime data and historical PBJ data but absent from April 2026 Provider Information.
- 20 are historical-only unmatched records absent from both current runtime data and April 2026 Provider Information.

## Manual Review Classification Summary

| Classification | Count | Public-use implication |
|---|---:|---|
| `current_and_historical_unmatched` | 5 | These are current runtime facilities with county unavailable. A county filter prototype must handle them transparently. |
| `historical_only_unmatched` | 20 | These do not affect a current Statewide Comparison county filter, but they matter for future historical county analysis. |
| `current_runtime_unmatched` | 0 | No current-only unmatched records were found. |
| `missing_current_provider_info_context` | 5 | Same 5 current-and-historical unmatched records; they lack April 2026 Provider Information county context. |
| `likely_closed_or_non_current_context` | 20 | Supported only for historical-only records absent from April 2026 Provider Information. This should not be treated as a definitive closure reason. |
| `unknown_needs_external_review` | 25 | All manual-review records need source review before county assignment. |

## Readiness Decision

Decision: **ready for a county filter prototype on Statewide Comparison, not yet ready for county summary/ranking cards.**

The crosswalk can support a first county filter because:

- 191 of 196 current runtime facilities have county populated from exact CCN matches to April 2026 CMS Provider Information.
- Provider Information matched records have complete county fields.
- Duplicate CCNs and missing CCN values are zero.
- The 5 current runtime records without county can be handled through an explicit `Unknown / needs review` option and a disclosure.

The crosswalk is not yet ready for more interpretive county summaries because:

- 5 current runtime facilities lack county.
- Aggregation rules are not yet documented.
- County values are current Provider Information context, not historical geography.
- Historical-only unmatched records need classification before historical county pattern analysis.

Phase 11C.4 implementation note: the first public implementation added a county filter to Statewide Comparison only, using this readiness decision. County summary cards, county ranking tables, facility county/state comparison cards, and historical county pattern analysis remain deferred.

## Recommended First Implementation

Recommended first public implementation: **Option A, add a county filter to Statewide Comparison only.**

Reasoning:

- A row-level county filter is simpler and lower risk than aggregation cards.
- It does not require immediate decisions about simple averages, resident-day weighting, medians, rankings, or denominator-sensitive summary language.
- It can include all facilities by default while allowing users to select a county or `Unknown / needs review`.
- It provides practical user value without implying county-level quality, compliance, or causation conclusions.

Recommended later implementation:

- Add facility county/state comparison cards after aggregation methodology is documented.
- Defer county ranking tables and county persistent-pattern summaries until denominator, weighting, and missing-county rules are tested.

## Denominator Rules

For the first county filter:

- No county filter selected: include all current runtime facilities, including unknown-county/manual-review records.
- Specific county selected: include only current runtime facilities whose `county_name` matches that county.
- `Unknown / needs review` selected: include current runtime facilities where `county_name` is null or blank.
- Statewide totals: include all current runtime facilities, including the 5 unknown-county records.
- County-specific denominators: exclude unknown-county records from named-county denominators.
- County list/counts should disclose how many current facilities have unknown county.

For later county summary cards:

- Named-county summaries should use only records assigned to that county.
- Statewide summaries should include unknown-county records unless a metric explicitly requires county assignment.
- Any county percentage should name its denominator.
- If weighted averages are introduced, document whether weights use resident days, beds, average census, or another field.

## Recommended Unknown-County Handling

The UI should include an explicit option such as:

- `Unknown / needs review`

Suggested filter helper text:

> County is current CMS Provider Information context from April 2026 where available. Facilities without a Provider Information county match are shown as Unknown / needs review. They remain included when no county filter is applied.

Suggested summary disclosure:

> County filters use a candidate CCN-based geography crosswalk. County is not historical quarter-specific geography. Five current facilities currently have county unavailable pending review.

Suggested methodology disclosure:

> Historical PBJ rows remain PBJ-only. County can be joined by CCN for analysis, but county values are current Provider Information context unless historical geography snapshots are later added.

## Out-of-Scope Items

- No public UI change in Phase 11C.3.
- County filter implementation is limited to Statewide Comparison as of Phase 11C.4.
- No facility county/state comparison cards yet.
- No county summary cards, county rankings, or county persistent-pattern summaries yet.
- No changes to `data/nursing_home_staffing_ct.json`.
- No changes to `data/nursing_home_staffing_history_ct.json`.
- No inferred county for unmatched records.
- No inferred LTCOP, AAA, or DPH regions.
- No nearby-state comparison dataset.

## Validation Checklist For Future Phase 11C.4

Before implementing the county filter:

1. Confirm `data/nursing_home_facility_geography_ct.json` validates as JSON.
2. Confirm the crosswalk still has 196 current runtime records and 191 current records with county populated, unless source data changed.
3. Confirm the 5 current unknown-county records are surfaced as `Unknown / needs review`.
4. Confirm no duplicate CCNs in the crosswalk.
5. Confirm no missing CCN values.
6. Confirm no Provider Information matched records are missing county.
7. Confirm Statewide Comparison can load the crosswalk without changing staffing formulas.
8. Confirm the filter defaults to all facilities.
9. Confirm selecting a named county excludes unknown-county records from that named county.
10. Confirm selecting `Unknown / needs review` shows the 5 current unmatched records.
11. Confirm CSV/print/copy outputs disclose county filter context.
12. Confirm methodology text explains county is current Provider Information context.
13. Confirm historical PBJ data remains PBJ-only.
14. Run `node --check` on any changed JS.
15. Run route and browser smoke checks for Statewide Comparison.
