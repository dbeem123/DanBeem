# Governance Timeline Data Model

Planning-only data model for future CT DPH governance and leadership timeline work. This model is not implemented in the live app.

## `ct_facilities`

Connecticut-side facility master table.

| Field | Notes |
|---|---|
| `state_facility_license_id` | Normalized CT DPH facility license ID; extract digits and strip leading zeroes. |
| `raw_license_number` | Preserve raw DPH license value, such as `CCNH.000119C` or `2525`. |
| `facility_name` | DPH facility name. |
| `address` | DPH street address. |
| `city` | DPH city. |
| `state` | Usually `CT`. |
| `zip_code` | DPH ZIP. |
| `facility_status` | DPH facility status. |
| `effective_date` | License effective date where present. |
| `expiration_date` | License expiration date where present. |
| `cms_ccn` | Only after validated crosswalk. |
| `crosswalk_status` | Suggested values: `not_started`, `auto_high_confidence`, `manual_review`, `validated`, `rejected`, `retired_or_unmatched`. |

## `ct_leadership_role_periods`

Cleaned role-period table derived from `Nursing_Home_Management_History.csv`.

| Field | Notes |
|---|---|
| `leadership_period_id` | Stable generated ID for cleaned period. |
| `state_facility_license_id` | Normalized CT DPH facility license ID. |
| `role_type` | At minimum: Administrator, Director of Nurses, Medical Director, President, and other source positions. |
| `person_name_raw` | Raw source name. |
| `person_name_normalized` | Uppercase normalized name with punctuation and spacing standardized. |
| `professional_license_raw` | Raw professional license value. |
| `professional_license_normalized` | Normalized license, preserving TEMP indicator where present. |
| `role_start_date` | Parsed start date, nullable. |
| `role_end_date` | Parsed termination date, nullable. |
| `open_ended_current_role` | True when termination date is blank and relationship status is active/current. |
| `relationship_status` | Raw relationship status. |
| `temporary_license_indicator` | True when professional license contains TEMP or another documented temporary pattern. |
| `source_file` | Source CSV filename. |
| `data_quality_flags` | Array of flags: `missing_start_date`, `missing_end_date`, `temp_license`, `same_person_overlap`, `multiple_active_role_holders`, `name_license_conflict`, `manual_review_required`. |

## `ct_administrator_license_registry`

Current administrator license registry snapshot.

| Field | Notes |
|---|---|
| `administrator_license_id` | Normalized license ID. |
| `raw_license_number` | Raw source value. |
| `person_name` | Registry first and last name. |
| `license_status` | Registry status. |
| `issue_date` | Parsed issue date. |
| `expiration_date` | Parsed expiration date. |
| `source_snapshot_date` | Snapshot/date from source acquisition metadata. |
| `match_notes` | Notes when matching management-history records. |

The registry is useful for validation but should not be used to discard historical role records absent from the current registry.

## `ct_management_company_registry`

Licensed management-company registry.

| Field | Notes |
|---|---|
| `management_company_license_id` | Normalized management-company license ID. |
| `company_name` | Registry company name. |
| `company_status` | Registry status. |
| `effective_date` | Parsed effective date. |
| `expiration_date` | Parsed expiration date. |
| `source_snapshot_date` | Snapshot/date from source acquisition metadata. |

This registry does not assign companies to facilities.

## `future_facility_management_company_periods`

Future table only, pending an explicit assignment source.

| Field | Notes |
|---|---|
| `state_facility_license_id` | CT facility license. |
| `management_company_license_id` | Management-company license, if available. |
| `management_company_name` | Company name. |
| `relationship_start_date` | Assignment start date. |
| `relationship_end_date` | Assignment end date. |
| `relationship_type` | Management agreement, related-party management, operator, etc., only if source defines it. |
| `source` | Assignment source. |
| `source_confidence` | High, medium, low, or manual review. |

Do not build this table from the management-company registry alone.

## Crosswalk Strategy

Future `ct_dph_to_cms_ccn_crosswalk` fields:

- `state_facility_license_id`
- `raw_dph_license_number`
- `cms_ccn`
- `dph_facility_name`
- `cms_facility_name`
- `dph_address`
- `cms_address`
- `city`
- `zip_code`
- `match_method`
- `match_confidence`
- `manual_review_required`
- `validation_notes`
- `effective_period_notes`

Recommended matching rules:

1. Start with exact or near-exact normalized address, city, and ZIP between DPH facility master and CMS Provider Information.
2. Use normalized facility name as supporting evidence, not the sole match.
3. Use CT DSS provider identifiers only as additional evidence after their own source fields are profiled.
4. Require manual review for name/address conflicts, missing ZIPs, relocated facilities, operator-name changes, and one-to-many candidates.
5. Preserve historical name/address evidence because ownership/operator names can change while licenses and CCNs persist or shift.

## Federal And State Connections

After crosswalk validation, governance periods can connect to:

- CMS CCN-keyed PBJ staffing quarters
- CMS Provider Information ratings and case-mix fields
- CMS SNF Enrollment affiliation entities
- CMS detailed ownership records
- CMS Change of Ownership records
- CT DSS rate, census, cost-report, and related-party context

These concepts should remain distinct. A DPH Administrator, DON, management company, CMS owner/entity, CMS affiliation entity, CMS chain, and CT DSS related-party relationship are not interchangeable.

## Cleaning And Overlap Rules

### Missing Start Dates

Records with termination dates but no start dates identify historical role holders but should usually be excluded from tenure-length calculations unless a defensible imputation rule is approved.

### Missing Termination Dates

Treat open-ended active records as ongoing through the source snapshot date for current-tenure analysis only. Do not treat the snapshot date as a confirmed end date.

### TEMP Licenses

Flag TEMP license values. A TEMP-to-permanent record for the same person, role, and facility should be reviewed as a possible continuous tenure period rather than a turnover event.

### Duplicates And Overlaps

Preserve raw lineage. Create cleaned analytical periods separately. Adjacent end/start dates for different holders should be treated as transitions, not overlaps. Same-person overlapping records should usually be merged or flagged after license/name review.

### Multiple Active Holders

Flag same-facility same-role cases with multiple active holders, especially Administrator and Director of Nurses. Distinguish duplicate licensing artifacts from possible concurrent role holders through manual review.

### Name And License Normalization

Normalize capitalization, punctuation, middle initials, suffixes, spaces, hyphens, and Excel-style license values. Professional-license matching should be preferred over name matching. Avoid merging different people solely because names are similar.

## PBJ Quarter Alignment Logic

For each future PBJ facility-quarter:

1. Map CMS CCN to CT facility license through the validated crosswalk.
2. Identify role periods intersecting the quarter.
3. Calculate overlap days for each Administrator and DON period.
4. Select the primary role holder using greatest overlap days.
5. Flag whether a role changed during the quarter.
6. Flag multiple role holders during the quarter.
7. Flag temporary-license periods during the quarter.
8. Flag unknown or incomplete coverage where dates are insufficient.

Future metrics that appear feasible after cleaning:

- Administrator changes in past 12, 24, and 36 months
- DON changes in past 12, 24, and 36 months
- Average tenure by role
- Short tenure under six months
- Rapid succession, such as three or more distinct role holders within twelve months
- Role coverage gaps
- Repeated temporary DON periods
- Staffing decline within the same quarter or within two quarters of a leadership transition
- Contract staffing increase near a DON transition

Interpretation guardrail: alignment between staffing and leadership transitions is temporal context for review, not proof that leadership change caused a staffing outcome.
