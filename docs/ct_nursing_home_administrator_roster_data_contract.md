# Connecticut Nursing Home Administrator Roster Data Contract

## Status and purpose

This document defines a proposed future normalized file:

`data/ct_nursing_home_administrator_roster.json`

The file is not created in Phase 11E.1. The future dataset would represent individual Connecticut Nursing Home Administrator license records from the Connecticut Department of Public Health roster. It would not represent employment assignments, current practice locations, or nursing-home affiliations.

## Top-level structure

```json
{
  "metadata": {},
  "administrators": []
}
```

`metadata` describes source provenance, build counts, validation findings, and limitations. `administrators` contains one normalized object for each nonblank source license row. Array order should be deterministic: normalized license number ascending, followed by source row number.

## Metadata contract

| Field | Type | Definition |
| --- | --- | --- |
| `source_name` | string | Human-readable source name, such as `Connecticut Nursing Home Administrator license roster`. |
| `source_agency` | string | `Connecticut Department of Public Health`. |
| `source_file` | string | Exact source filename. |
| `roster_date` | string | Source snapshot date in `YYYY-MM-DD` form: `2026-05-22`. |
| `acquired_date` | string | Repository acquisition/download date in `YYYY-MM-DD` form. For this source, `2026-05-22`. |
| `build_date` | string | Builder execution date in `YYYY-MM-DD` form. This is provenance only and must not drive expiration flags. |
| `source_row_count` | integer | All CSV data rows, including any completely blank rows. |
| `normalized_record_count` | integer | Administrator objects emitted from nonblank source records. |
| `unique_license_count` | integer | Distinct nonblank normalized license-number strings. |
| `duplicate_license_count` | integer | Number of normalized license values occurring more than once; duplicate rows must also be separately reported during validation. |
| `active_license_count` | integer | Records whose exact source status normalizes to `ACTIVE`. |
| `ct_mailing_address_count` | integer | Records whose normalized mailing state is `CT`. |
| `non_ct_mailing_address_count` | integer | Records with a nonblank mailing state other than `CT`. |
| `legacy_issue_date_count` | integer | Records with source original issue date `1901-01-01`. |
| `zip_correction_count` | integer | Records whose validation-only ZIP replaces `O` with `0` under the safe pattern rule. |
| `limitations` | array of strings | Plain-language limitations, including no employment/facility relationship and mailing-address constraints. |

Recommended additional metadata fields are `schema_version`, `source_file_size_bytes`, `completely_blank_row_count`, `missing_license_count`, `duplicate_normalized_name_count`, `expired_as_of_roster_date_count`, `status_counts`, `status_reason_counts`, `expiration_window_counts`, and `validation_reference_date`. `validation_reference_date` must equal the roster date, not the builder's system date.

## Administrator record contract

| Field | Type | Definition |
| --- | --- | --- |
| `license_number` | string | Stable normalized identifier; leading zeros preserved and never converted to an integer. |
| `license_number_raw` | string | Exact trimmed source value from `LICENSE NO.` before wrapper/quote normalization. |
| `first_name` | string | Trimmed, repeated-space-normalized first name. |
| `middle_name` | string or null | Normalized middle name when a future source provides it; `null` for this roster because no column exists. |
| `last_name` | string | Trimmed, repeated-space-normalized last name. |
| `suffix` | string or null | Normalized suffix when a future source provides it; `null` for this roster because no column exists. |
| `display_name` | string | Display-safe concatenation of available name parts; punctuation retained. |
| `normalized_match_name` | string | Conservative comparison key for candidate matching, never a unique person identifier. |
| `address_line_1` | string or null | Trimmed source `ADDRESS1`. |
| `address_line_2` | string or null | Trimmed source `ADDRESS2`. |
| `city` | string | Trimmed mailing city. |
| `state` | string | Uppercase mailing-state value. |
| `zip_code_raw` | string | Exact trimmed source ZIP, including any letter `O`. |
| `zip_code_normalized` | string | Validation-only five-digit or ZIP+4 value after the safe `O`-to-`0` rule; otherwise the cleaned source value. |
| `zip_code_corrected` | boolean | `true` only when the safe normalization changed one or more `O` characters to `0`. |
| `country` | string or null | Source country when available; `null` for this roster because the column is absent. |
| `license_status` | string | Exact trimmed source license status. |
| `status_reason` | string | Exact trimmed administrative status reason; no interpretation added. |
| `original_issue_date` | string or null | Parsed ISO date `YYYY-MM-DD`, or `null` if missing/invalid with a validation flag. |
| `expiration_date` | string or null | Parsed ISO date `YYYY-MM-DD`, or `null` if missing/invalid with a validation flag. |
| `possible_legacy_issue_date` | boolean | `true` when the source issue date is exactly `1901-01-01`. |
| `expired_as_of_roster_date` | boolean | `true` when expiration is earlier than `2026-05-22`; independent of source status. |
| `expires_within_90_days_of_roster_date` | boolean | `true` when expiration is on/after `2026-05-22` and no later than 90 days afterward. |
| `source_row_number` | integer | One-based physical CSV row number, including header as row 1. |
| `validation_flags` | array of strings | Deterministic flags documenting corrections, missing values, or review conditions. |

To preserve fields present in this source but omitted from the initial recommended list, the future contract should also include:

| Field | Type | Definition |
| --- | --- | --- |
| `first_name_raw` | string | Exact trimmed source `FIRST NAME`, retained separately from normalized output. |
| `last_name_raw` | string | Exact trimmed source `LAST NAME`, retained separately from normalized output. |
| `mailing_county` | string or null | Exact trimmed source `COUNTY`; not inferred when blank. |

No full-name source field exists. `display_name` is derived and must not be described as source-supplied.

## Exact source mapping

| Source column | Future field or handling |
| --- | --- |
| `LICENSE NO.` | `license_number_raw`, `license_number` |
| `FIRST NAME` | `first_name_raw`, `first_name` |
| `LAST NAME` | `last_name_raw`, `last_name` |
| `ADDRESS1` | `address_line_1` |
| `ADDRESS2` | `address_line_2` |
| `CITY` | `city` |
| `STATE` | `state` |
| `ZIP` | `zip_code_raw`, `zip_code_normalized`, `zip_code_corrected` |
| `COUNTY` | `mailing_county` |
| `STATUS` | `license_status` |
| `REASON` | `status_reason` |
| `ISSUE DATE` | `original_issue_date`, `possible_legacy_issue_date` |
| `EXPIRATION DATE` | `expiration_date`, expiration flags |

The source contains no columns for middle name, suffix, country, facility name, employer, work address, facility license number, CMS Certification Number, National Provider Identifier, or Connecticut facility identifier.

## Normalization rules

### License numbers

1. Preserve the trimmed source value in `license_number_raw`.
2. Remove an exact spreadsheet wrapper such as `="000050"` or `='000050'`.
3. Remove matching unnecessary outer quote pairs.
4. Trim and collapse whitespace without numeric conversion.
5. Preserve all leading zeros.
6. Flag a nonblank result containing non-digits as `unexpected_license_number_format`.
7. Do not merge duplicate license rows automatically; fail or require an explicit reviewed duplicate policy.

### Names

1. Preserve the source first and last name fields.
2. Trim and collapse repeated whitespace in normalized components.
3. Retain punctuation in `display_name`.
4. Build `normalized_match_name` using Unicode decomposition, combining-mark removal, alphanumeric tokenization, collapsed spaces, and uppercase comparison text.
5. Treat a matching comparison key only as a candidate match. Never merge people solely because it matches.

Matching review must consider middle-name initials, suffixes, hyphens, apostrophes, previous names, spelling variation, and different people with the same name. The current source's two distinct `CHRISTOPHER JOHNSON` license records are a concrete collision example.

### Addresses and ZIP codes

1. Preserve `zip_code_raw` exactly after outer whitespace trimming.
2. Remove internal spaces only in the validation-only normalized candidate.
3. Replace `O` with `0` only when the candidate matches five `[0-9O]` characters or five plus four separated by a hyphen and the result is a valid numeric ZIP/ZIP+4 pattern.
4. Set `zip_code_corrected` and add `zip_letter_o_corrected_to_zero` for every correction.
5. Retain and flag values that do not meet the safe rule rather than guessing.
6. Never treat mailing city, state, ZIP, or county as a facility, employer, work location, or practice-location field.

### Dates and status

1. Parse explicit U.S. source dates and emit ISO `YYYY-MM-DD` strings.
2. Preserve invalid or missing source context through flags; do not silently repair dates.
3. Keep `1901-01-01` and flag it `possible_legacy_issue_date`.
4. Calculate expiration flags from the fixed roster date `2026-05-22`.
5. Keep `license_status` and `status_reason` distinct from date-derived flags.
6. Do not infer meaning beyond source wording for reasons such as `PRIOR DISCIPLINE`.

## Recommended validation flags

- `spreadsheet_formula_wrapper_removed`
- `surrounding_quotes_removed`
- `unexpected_license_number_format`
- `missing_first_name`
- `missing_last_name`
- `missing_mailing_state`
- `missing_street_address`
- `missing_zip_code`
- `zip_letter_o_corrected_to_zero`
- `unexpected_zip_format`
- `missing_original_issue_date`
- `invalid_original_issue_date`
- `possible_legacy_issue_date`
- `missing_expiration_date`
- `invalid_expiration_date`
- `expiration_before_issue_date`
- `expired_as_of_roster_date`
- `duplicate_normalized_license_number`
- `duplicate_normalized_match_name`

## Integrity expectations for a future builder

- Read only the ignored DPH CSV and write only an explicitly designated preview/runtime target.
- Fail if required source columns disappear or duplicate header names occur.
- Reconcile source rows, normalized records, status totals, state totals, ZIP corrections, and date flags.
- Produce deterministic ordering and stable JSON formatting.
- Retain raw identifiers and correction flags.
- Never create administrator-to-facility relationships from this roster.
- Keep a preview/dry-run mode separate from an explicit production-write option.
- Do not wire the file into public UI until an official affiliation source and matching methodology are validated.

## Required limitation language

The future runtime file represents individual license records only. Appearance in the roster may support license validation for a named person, subject to identity matching, but does not establish current employment or facility affiliation. `ACTIVE` is a license status in this source; it does not establish that the licensee currently works, practices in the mailing state, or manages a Connecticut nursing home.

## Phase 11E.1 observed baseline

The May 22, 2026 source currently has 581 rows, 581 normalized records, 581 unique license numbers, no duplicate license values, 581 `ACTIVE` statuses, 460 Connecticut mailing states, 121 non-Connecticut mailing states, 26 possible legacy issue dates, and 549 safely correctable ZIP values. These values are validation baselines, not permanent contract constants; a future builder must calculate them from its input.
