# Nursing Home Penalties / Enforcement Data Contract

Phase 11D.10 data contract and builder planning document. This document defines a future app-ready Connecticut penalties/enforcement output, but it does not create runtime JSON, build public UI, modify runtime JS/HTML, change staffing formulas, change generated staffing data, alter current or historical staffing JSON, change Connecticut applicability logic, modify geography JSON, or modify facility status review JSON.

## 1. Purpose

`data/nursing_home_penalties_ct.json` should become a Connecticut-only, enforcement-row dataset derived from the official CMS Penalties source. It should support future advanced facility dossier enforcement context, penalty timelines, fine summaries, payment-denial summaries, and carefully labeled state-level enforcement summaries.

This dataset should not be used as a standalone legal conclusion, care-quality score, staffing formula input, CT applicability input, current-only facility status source, or citation finding source.

## 2. Source Basis

Validated source from Phase 11D.9:

- `source_data/cms_enforcement/NH_Penalties_May2026.csv`

Official CMS source metadata:

- CMS dataset title: `Penalties`
- CMS dataset ID: `g6vv-u9sr`
- source filename: `NH_Penalties_May2026.csv`
- modified date: May 1, 2026
- released date: May 27, 2026
- acquired date: June 22, 2026
- source URL: <https://data.cms.gov/provider-data/sites/default/files/resources/c671cdaa1461db5a685367690785fcb3_1778861763/NH_Penalties_May2026.csv>
- source landing page: <https://data.cms.gov/provider-data/dataset/g6vv-u9sr>
- source metadata endpoint: <https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/g6vv-u9sr>

Validation results:

- total source rows: 16,571
- Connecticut rows: 179
- unique Connecticut CCNs: 102
- joined to current staffing data: 102
- unmatched CT penalty/enforcement CCNs: 0
- duplicate CT full-row signatures: 3
- penalty date range: 2023-05-17 to 2026-03-17
- processing date: all CT rows were 2026-05-01
- payment denial start date range: 2024-01-17 to 2024-12-03
- fine rows: 167
- payment denial rows: 12
- CT fine amount range: 2,117.00 to 195,360.00
- CT fine amount total across source rows: 3,925,517.00
- payment denial length total: 368 days

## 3. Future Output File

Proposed future output:

- `data/nursing_home_penalties_ct.json`

Do not create this output in Phase 11D.10. It should be created only after builder implementation and validation expectations are approved.

The file should remain separate from:

- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_staffing_history_ct.json`
- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_citation_descriptions.json`
- geography, facility status review, and CT applicability outputs

## 4. Recommended JSON Shape

```json
{
  "metadata": {
    "source_name": "CMS Provider Data Catalog Penalties",
    "source_file": "NH_Penalties_May2026.csv",
    "source_url_or_endpoint": "https://data.cms.gov/provider-data/sites/default/files/resources/c671cdaa1461db5a685367690785fcb3_1778861763/NH_Penalties_May2026.csv",
    "cms_dataset_id": "g6vv-u9sr",
    "source_month": "May",
    "source_year": 2026,
    "acquired_date": "2026-06-22",
    "build_date": "YYYY-MM-DD",
    "state_filter": "CT",
    "source_row_count": 16571,
    "ct_row_count": 179,
    "unique_ct_ccn_count": 102,
    "joined_current_ccn_count": 102,
    "unmatched_current_ccn_count": 0,
    "duplicate_full_row_signature_count": 3,
    "penalty_date_min": "2023-05-17",
    "penalty_date_max": "2026-03-17",
    "processing_date_min": "2026-05-01",
    "processing_date_max": "2026-05-01",
    "payment_denial_start_date_min": "2024-01-17",
    "payment_denial_start_date_max": "2024-12-03",
    "fine_row_count": 167,
    "payment_denial_row_count": 12,
    "ct_fine_amount_total": 3925517.0,
    "payment_denial_length_total_days": 368,
    "limitations": [
      "Penalties/enforcement rows are official CMS enforcement records.",
      "Fine rows and payment-denial rows are different enforcement types.",
      "Fine amount is not a quality score.",
      "Penalty date, payment denial start date, and processing date are different fields.",
      "Facility-level totals require a defined time window.",
      "State-level totals require careful denominator labels.",
      "Duplicate source rows must be preserved or handled transparently under an approved rule.",
      "This rolling CMS source is not complete lifetime enforcement history."
    ]
  },
  "penalties": [
    {
      "ccn": "075000",
      "provider_name": "Example Facility",
      "provider_address": "123 Example Street",
      "city": "Example",
      "state": "CT",
      "zip_code": "06000",
      "penalty_date": "2025-01-01",
      "penalty_year": 2025,
      "penalty_type": "Fine",
      "fine_amount": "10000",
      "payment_denial_start_date": null,
      "payment_denial_length_days": null,
      "location": "123 Example Street,Example,CT,06000",
      "processing_date": "2026-05-01",
      "source_row_hash": "sha256-of-normalized-source-row",
      "duplicate_full_row_signature": false,
      "enforcement_category": "fine",
      "has_fine": true,
      "has_payment_denial": false,
      "normalized_fine_amount": 10000.0,
      "display_amount": "$10,000.00",
      "event_year": 2025
    }
  ]
}
```

## 5. Metadata Field Definitions

| Field | Definition |
|---|---|
| `source_name` | Human-readable official source name. |
| `source_file` | Raw CMS source filename used for the build. |
| `source_url_or_endpoint` | Official CMS source URL or metadata endpoint. |
| `cms_dataset_id` | CMS Provider Data Catalog dataset identifier, currently `g6vv-u9sr`. |
| `source_month` | Source month parsed from filename or CMS metadata. |
| `source_year` | Source year parsed from filename or CMS metadata. |
| `acquired_date` | Date the raw source file was acquired locally. |
| `build_date` | Date the JSON output was built. |
| `state_filter` | State filter applied to source rows, currently `CT`. |
| `source_row_count` | Total rows in the raw source file. |
| `ct_row_count` | Rows emitted after Connecticut filtering. |
| `unique_ct_ccn_count` | Unique CT CCNs in emitted rows. |
| `joined_current_ccn_count` | Unique CT source CCNs that join to current staffing data. |
| `unmatched_current_ccn_count` | Unique CT source CCNs that do not join to current staffing data. |
| `duplicate_full_row_signature_count` | Count of CT rows that duplicate a prior full normalized source-row signature. |
| `penalty_date_min` | Earliest parsed `Penalty Date` in emitted rows. |
| `penalty_date_max` | Latest parsed `Penalty Date` in emitted rows. |
| `processing_date_min` | Earliest parsed `Processing Date` in emitted rows. |
| `processing_date_max` | Latest parsed `Processing Date` in emitted rows. |
| `payment_denial_start_date_min` | Earliest parsed payment denial start date in emitted rows. Null if none. |
| `payment_denial_start_date_max` | Latest parsed payment denial start date in emitted rows. Null if none. |
| `fine_row_count` | Count of emitted rows with `Penalty Type == Fine`. |
| `payment_denial_row_count` | Count of emitted rows with `Penalty Type == Payment Denial`. |
| `ct_fine_amount_total` | Sum of parsed CT fine amounts under the approved duplicate handling rule. |
| `payment_denial_length_total_days` | Sum of parsed CT payment denial length days under the approved duplicate handling rule. |
| `limitations` | Plain-language limitations that must travel with the dataset. |

## 6. Penalty Record Field Definitions

| Field | Source / rule | Definition |
|---|---|---|
| `ccn` | `CMS Certification Number (CCN)` | Normalized six-character CCN with leading zeroes preserved. |
| `provider_name` | `Provider Name` | CMS source provider name. |
| `provider_address` | `Provider Address` | CMS source provider street address. |
| `city` | `City/Town` | CMS source city/town. |
| `state` | `State` | State abbreviation, expected `CT` after filtering. |
| `zip_code` | `ZIP Code` | CMS source ZIP code, preserved as text. |
| `penalty_date` | `Penalty Date` | Source penalty/enforcement date. |
| `penalty_year` | Derived from `penalty_date` | Calendar year of source penalty date. |
| `penalty_type` | `Penalty Type` | Source type, observed as `Fine` or `Payment Denial` in CT rows. |
| `fine_amount` | `Fine Amount` | Original source fine amount text. Null for payment denial rows. |
| `payment_denial_start_date` | `Payment Denial Start Date` | Source payment denial start date. Null for fine rows. |
| `payment_denial_length_days` | `Payment Denial Length in Days` | Parsed integer duration. Null for fine rows. |
| `location` | `Location` | CMS source location string. |
| `processing_date` | `Processing Date` | CMS processing/source date. |
| `source_row_hash` | Derived | Stable hash of normalized full source row values for audit and deduplication. |
| `duplicate_full_row_signature` | Derived | Whether the normalized full source row duplicated an earlier emitted CT row. |

## 7. Derived Field Definitions

| Field | Rule | Definition |
|---|---|---|
| `enforcement_category` | Derived from `penalty_type` | Stable category, such as `fine`, `payment_denial`, or `other_or_unmapped`. |
| `has_fine` | Derived from parsed amount and type | `true` for rows with a valid fine amount. |
| `has_payment_denial` | Derived from payment denial fields and type | `true` for rows with payment denial date or length fields. |
| `normalized_fine_amount` | Parsed from `Fine Amount` | Numeric fine amount for calculation. Null for payment denial rows. |
| `display_amount` | Derived from `normalized_fine_amount` | Formatted amount for display/export. Null for payment denial rows. |
| `event_year` | Derived from `penalty_date` | Preferred event year for filtering and summaries. |

## 8. Penalties / Enforcement Semantics

- Penalties/enforcement rows are official CMS enforcement records.
- Fine rows and payment-denial rows are different enforcement types.
- Penalty rows are not citation rows.
- Fine amount is not a quality score.
- A high or low fine amount should not be presented as a simple ranking without context.
- Payment denial duration is not a fine amount.
- Penalty date, payment denial start date, and processing date are different fields and must not be treated as interchangeable.
- Facility-level totals require a defined time window.
- State-level totals require careful denominators.
- Absence from this rolling source should not be presented as absence of all enforcement history.

## 9. Duplicate Source Row Handling Recommendation

Phase 11D.9 validation found 3 duplicate Connecticut rows by full-row signature. Future builder behavior should be explicit.

Recommended default:

- Preserve all source rows in the raw emitted `penalties` array.
- Compute a stable `source_row_hash` from normalized source fields.
- Set `duplicate_full_row_signature` to `true` on rows that duplicate a prior emitted CT full-row signature.
- Include `duplicate_full_row_signature_count` in metadata.
- Do not silently remove duplicate rows.

Future summary rule:

- For facility totals, statewide totals, and display counts, decide before runtime publication whether duplicate rows are retained or deduplicated.
- If deduplicated summaries are used, include metadata fields for both source-row counts and deduplicated counts.
- Do not change totals by deduplication without a documented, reproducible rule.

Rationale:

- Duplicate rows may reflect source duplication, separate official events with identical fields, or source publication artifacts.
- The CMS file is the official source; any deduplication is a project-level interpretation and should be transparent.

## 10. Fine And Payment-Denial Handling Plan

Fine rows:

- `penalty_type` should remain `Fine`.
- Parse `Fine Amount` into `normalized_fine_amount`.
- Set `has_fine` to `true`.
- Set payment denial fields to null unless source values are present.
- Do not use fine amount as a quality score.

Payment denial rows:

- `penalty_type` should remain `Payment Denial`.
- Preserve `Payment Denial Start Date`.
- Parse `Payment Denial Length in Days` into an integer.
- Set `has_payment_denial` to `true`.
- Set fine amount fields to null unless source values are present.
- Do not convert payment denial days into a dollar amount.

Rows with unexpected `Penalty Type` values:

- Preserve the source value.
- Set `enforcement_category` to `other_or_unmapped`.
- Fail or warn according to the future builder validation policy.
- Do not coerce unknown enforcement types into fine or payment denial categories.

## 11. Future Builder Plan

Proposed future builder:

- `scripts/build_nursing_home_penalties_ct.py`

Builder responsibilities:

1. Read the ignored CMS Penalties CSV from `source_data/cms_enforcement/NH_Penalties_May2026.csv`.
2. Read `data/nursing_home_staffing_ct.json` for current CCN join validation.
3. Filter to Connecticut rows.
4. Normalize CCNs while preserving leading zeroes.
5. Validate joins to current staffing data.
6. Parse penalty dates, payment denial dates, and processing dates separately.
7. Parse fine amounts as numeric values without losing the original source text.
8. Parse payment denial length as integer days.
9. Preserve source penalty type.
10. Identify duplicate full-row signatures.
11. Include metadata and limitations matching this data contract.
12. Fail loudly on missing required source columns, invalid required dates, invalid fine amounts on fine rows, invalid payment denial lengths on payment-denial rows, or unmatched CT CCNs unless explicitly approved.
13. Print a validation summary.

Suggested default behavior:

- validation-only dry run without writing output

Suggested preview flag:

- `--write-testing-preview`

Suggested non-runtime preview path:

- `data/testing/nursing_home_penalties_ct_preview.json`

Do not write `data/nursing_home_penalties_ct.json` until a future runtime build phase is approved.

## 12. Validation Requirements Before Runtime Use

Before `data/nursing_home_penalties_ct.json` is created for public runtime use:

- confirm official CMS source file and dataset metadata;
- validate source schema and required columns;
- validate total, CT, and unique CCN row counts;
- validate all CT source CCNs join to the intended current/context facility universe;
- validate penalty date parsing and date range;
- validate processing date parsing;
- validate payment denial start date parsing;
- validate penalty type counts;
- validate fine amount parsing;
- validate payment denial length parsing;
- document duplicate source row handling;
- preserve date fields separately;
- preserve fine and payment-denial records as separate enforcement types;
- confirm future UI labels do not treat penalty amount as a quality score.

## 13. App Use Cases

Possible future uses after runtime integration is approved:

- Facility dossier enforcement section.
- Recent penalty timeline.
- Facility-level total CMP amount over a defined source window.
- Payment denial indicator and duration summary.
- State-level enforcement summary with explicit denominators.
- Exportable facility enforcement summary.

## 14. Guardrails

- Enforcement findings must be source-backed.
- Do not present penalties as citations.
- Do not link penalty rows to health or fire safety citation rows unless an official source field or audited matching rule supports the relationship.
- Do not present fine amount as a care-quality score.
- Do not rank facilities by fine amount without context and denominator warnings.
- Preserve penalty date, payment denial start date, and processing date separately.
- Preserve row-level, facility-level, facility-year, and state-level denominators separately.
- Do not make legal conclusions beyond official source language.
- Do not make causation claims.
- Do not modify staffing formulas, current/context staffing JSON, historical PBJ JSON, geography JSON, facility status review JSON, or CT applicability logic.

## 15. Recommendation

Proceed to a future Penalties / Enforcement builder dry-run phase. The source is ready for a validation-only builder with explicit duplicate-row metadata, separate fine/payment-denial handling, and no runtime JSON output until the build and denominator rules are approved.

