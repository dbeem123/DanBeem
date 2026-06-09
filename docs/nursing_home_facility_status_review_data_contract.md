# Nursing Home Facility Status Review Data Contract

Phase 11C.8 data contract for `data/nursing_home_facility_status_review_ct.json`.

## 1. Purpose

`data/nursing_home_facility_status_review_ct.json` is a non-runtime review file for source-backed facility status findings. It currently covers the five current runtime facilities that appear as `Unknown / needs review` in the Statewide Comparison county filter.

The file records official evidence gathered during the Phase 11C.7 closure review. It may support future status-aware documentation, review workflows, or disclosures after a later implementation phase, but it is not wired into the public application.

## 2. Runtime Guardrails

This file:

- does not alter staffing calculations;
- does not remove records from current statewide totals;
- does not assign county;
- does not update geography crosswalk county assignments;
- does not change historical PBJ data;
- does not change current/context staffing data;
- does not change Connecticut applicability logic;
- does not change public UI, runtime JS, HTML, exports, filters, or formulas.

The Statewide Comparison county filter should continue to include all current runtime records by default, including unknown-county records. Named county filters should continue excluding records whose county remains unavailable.

## 3. Record Scope

The first version contains five records:

- ABBOTT TERRACE HEALTH CENTER;
- COUNTRYSIDE MANOR OF BRISTOL;
- MATTATUCK HEALTH CARE FACILITY, INC.;
- ST JOSEPH'S CENTER;
- SPRINGS AT EAST HILL, THE.

Four records have confirmed official closed/non-current evidence. Springs at East Hill remains unresolved because the source review did not find official closure, provider termination, certification-end, license-end, rename, merger, or other non-current status evidence.

## 4. Field Definitions

| Field | Definition |
|---|---|
| `ccn` | CMS Certification Number, normalized to six characters. |
| `facility_name` | Facility display name from the geography crosswalk/status review. |
| `address` | Existing address value when available from current reviewed data. Blank does not imply no address exists. |
| `city` | Existing city value from current reviewed data. |
| `state` | Existing state value from current reviewed data. |
| `zip_code` | Existing ZIP value when available from current reviewed data. Blank does not imply no ZIP exists. |
| `current_geography_status` | Current county/geography review status, currently `unknown_needs_review` for all five records. |
| `status_review_required` | Boolean indicating that status review is needed or should be retained for audit trail. |
| `current_provider_info_match` | Whether the facility matched the April 2026 CMS Provider Information source used by the geography crosswalk. |
| `possible_closed_or_non_current` | Boolean indicating whether official evidence supports possible closed/non-current handling. |
| `official_status` | Source-backed status label. Current allowed values are `closed_or_non_current` and `unresolved`. |
| `official_status_date` | Primary official status date. Null when unresolved. |
| `official_status_date_type` | Exact date type label. This must not collapse distinct event types into a generic closure date. |
| `additional_official_status_dates` | Array of additional official dates when more than one official event date exists. |
| `official_status_source` | Primary source title supporting `official_status` and `official_status_date`. |
| `source_url_or_file` | URL or local source filename for the primary source. |
| `review_confidence` | Confidence label: `confirmed official` or `unresolved`. |
| `review_notes` | Concise source-backed note, including distinctions between date types where relevant. |
| `recommended_action` | Suggested non-runtime follow-up action. |

## 5. Date-Type Rules

Date type labels must be preserved exactly enough to avoid mixing different official events.

Current date types include:

- `provider termination date`;
- `CT DSS bed-termination effective date`;
- `null` for unresolved records.

Do not treat provider termination dates, certification termination dates, license expiration/end dates, closure dates, and CT DSS bed-termination effective dates as interchangeable.

## 6. Evidence Rules

Official status evidence is required before a record can be marked `closed_or_non_current`.

Acceptable evidence includes official CMS or Connecticut state sources showing provider termination, certification termination, facility closure, license end/expiration, bed termination, or another official end/status event.

Secondary sources may support review notes but should not be the primary basis for `official_status`.

Unresolved records must remain unresolved until official evidence supports a status update.

## 7. Relationship To Geography

This file does not resolve county. A facility may be confirmed closed/non-current while still having `county_name` unavailable in the geography crosswalk.

County assignment still requires source-backed geography evidence and a separate crosswalk validation/update phase. Closure or non-current status should not be converted into a county assignment.

## 8. Future Use

Possible future uses after review and approval:

- status-aware methodology notes;
- non-runtime audit reports;
- review queue dashboards;
- optional public disclosure that a current-context row may reflect closed/non-current source evidence;
- refresh checks that identify current runtime records whose status needs reconciliation.

Before runtime use, a future phase should define validation checks, source-refresh rules, display language, and whether status evidence should affect current runtime inclusion. No such runtime behavior is approved by this contract.
