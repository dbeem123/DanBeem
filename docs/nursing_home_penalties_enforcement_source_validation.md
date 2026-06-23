# CMS Penalties / Enforcement Source Validation

Phase 11D.9 source acquisition and validation document. This validates the CMS Nursing Home Penalties source file for future penalty and enforcement context work.

This phase does not build public UI, create runtime JSON, change runtime JS/HTML, change staffing formulas, change generated staffing data, change Connecticut applicability logic, modify current or historical staffing JSON, modify health deficiencies runtime JSON, modify fire safety runtime JSON, modify citation descriptions runtime JSON, modify geography JSON, or modify facility status review JSON.

## 1. Acquisition Summary

Acquisition date: June 22, 2026.

| Source | Official CMS endpoint/source URL | Local placement | File size |
|---|---|---|---:|
| CMS Penalties | <https://data.cms.gov/provider-data/sites/default/files/resources/c671cdaa1461db5a685367690785fcb3_1778861763/NH_Penalties_May2026.csv> | `source_data/cms_enforcement/NH_Penalties_May2026.csv` | 2,768,010 bytes |

CMS Provider Data metadata identified the source as:

- title: `Penalties`;
- dataset identifier: `g6vv-u9sr`;
- modified date: May 1, 2026;
- released date: May 27, 2026;
- next update date listed by CMS metadata: June 24, 2026;
- description: fines and payment denials received by nursing homes in the last three years;
- landing page: <https://data.cms.gov/provider-data/dataset/g6vv-u9sr>;
- metadata endpoint used for source confirmation: <https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/g6vv-u9sr>.

Raw source files under `source_data/` are ignored by Git and should remain uncommitted unless explicitly approved.

## 2. Validation Method

Validation script:

- `scripts/validate_nursing_home_penalties_enforcement.py`

The script:

- reads the ignored CMS Penalties CSV from `source_data/cms_enforcement/`;
- detects the latest `NH_Penalties_*.csv` file by filename;
- loads `data/nursing_home_staffing_ct.json` for current app CCN join testing;
- filters Connecticut rows by `State == CT`;
- normalizes CCNs to six characters;
- parses penalty dates, payment denial start dates, and processing dates;
- parses fine amounts and payment denial lengths;
- prints validation results only;
- does not write runtime JSON.

## 3. Schema Summary

Observed CSV columns:

| Column | Validation/use note |
|---|---|
| `CMS Certification Number (CCN)` | Primary provider join key. Preserve leading zeroes. |
| `Provider Name` | Source provider name. |
| `Provider Address` | Source provider street address. |
| `City/Town` | Source city/town. |
| `State` | Used for Connecticut filtering. |
| `ZIP Code` | Source ZIP code. |
| `Penalty Date` | Source penalty/enforcement date. Preserve separately from processing date and payment denial start date. |
| `Penalty Type` | Source type/category. Observed CT values were `Fine` and `Payment Denial`. |
| `Fine Amount` | Monetary amount for fine rows. Blank for payment denial rows. |
| `Payment Denial Start Date` | Start date for payment denial rows. Blank for fine rows. |
| `Payment Denial Length in Days` | Denial duration for payment denial rows. Blank for fine rows. |
| `Location` | Source location string. |
| `Processing Date` | CMS processing/source date. |

Required source columns were present.

## 4. Row Counts And Connecticut Filtering

| Measure | Count |
|---|---:|
| Total source rows | 16,571 |
| Connecticut penalty/enforcement rows | 179 |
| Unique Connecticut CCNs in Penalties source | 102 |
| Current staffing CCNs in `data/nursing_home_staffing_ct.json` | 196 |
| CT Penalties CCNs joined to current staffing data | 102 |
| CT Penalties CCNs not joined to current staffing data | 0 |

Provider/CCN field used:

- `CMS Certification Number (CCN)`

CCNs were normalized to six characters with leading zeroes preserved.

Join interpretation:

- All 102 unique CT Penalties source CCNs joined to current staffing data.
- There were no unmatched CT penalty/enforcement CCNs to classify.
- Facilities without penalty rows in this rolling source should not be interpreted as having no enforcement history outside the source window or outside the CMS Penalties file scope.

## 5. Duplicate Row Finding

Validation found 3 duplicate Connecticut rows by full-row signature:

| CCN | Provider name | Penalty date | Penalty type | Fine amount |
|---|---|---|---|---:|
| `075350` | CIVITA SHERIDEN WOODS | 2026-01-30 | Fine | 14,015 |
| `075353` | MOZAIC SENIOR LIFE | 2023-10-19 | Fine | 10,059 |
| `075400` | BETHEL HEALTH CARE CENTER | 2024-05-10 | Fine | 8,018 |

Recommended handling:

- Preserve source rows during raw validation.
- Before any runtime build, decide whether exact duplicate rows should be retained as official source rows or deduplicated with explicit source-row hashing and audit notes.
- Do not deduplicate in a way that changes totals without documenting the rule.

## 6. Date Validation

Penalty dates:

| Check | Result |
|---|---:|
| Missing penalty dates | 0 |
| Invalid penalty dates | 0 |
| Minimum CT penalty date | 2023-05-17 |
| Maximum CT penalty date | 2026-03-17 |

Connecticut rows by penalty calendar year:

| Year | Penalty/enforcement rows |
|---|---:|
| 2023 | 41 |
| 2024 | 73 |
| 2025 | 54 |
| 2026 | 11 |

Processing dates:

| Processing date | Rows |
|---|---:|
| 2026-05-01 | 179 |

Payment denial start dates:

| Check | Result |
|---|---:|
| Rows with payment denial start dates | 12 |
| Missing payment denial start dates | 167 |
| Invalid payment denial start dates | 0 |
| Minimum CT payment denial start date | 2024-01-17 |
| Maximum CT payment denial start date | 2024-12-03 |

Guardrail: preserve `Penalty Date`, `Payment Denial Start Date`, and `Processing Date` separately. They are not interchangeable with survey date, citation date, correction date, or source acquisition date.

## 7. Penalty / Enforcement Type Validation

Connecticut rows by `Penalty Type`:

| Penalty type | Rows |
|---|---:|
| `Fine` | 167 |
| `Payment Denial` | 12 |

Findings:

- Civil money penalties and denial-of-payment actions are represented separately through `Penalty Type`.
- Fine rows use `Fine Amount`.
- Payment denial rows use `Payment Denial Start Date` and `Payment Denial Length in Days`.
- The source does not include direct citation/F-tag/K-tag linkage fields in the observed schema.
- No case number, enforcement cycle identifier, survey identifier, or correction-date linkage field was observed.

## 8. Monetary Amount Findings

Fine amount validation for Connecticut rows:

| Check | Result |
|---|---:|
| Fine amount rows parsed | 167 |
| Missing fine amount rows | 12 |
| Invalid fine amount rows | 0 |
| Minimum CT fine amount | 2,117.00 |
| Maximum CT fine amount | 195,360.00 |
| Total CT fine amount across source rows | 3,925,517.00 |

Payment denial length validation for Connecticut rows:

| Check | Result |
|---|---:|
| Payment denial length rows parsed | 12 |
| Missing payment denial length rows | 167 |
| Invalid payment denial length rows | 0 |
| Minimum payment denial length | 5 days |
| Maximum payment denial length | 71 days |
| Total payment denial days across source rows | 368 days |

Interpretation:

- Missing `Fine Amount` values are expected for `Payment Denial` rows.
- Missing payment denial fields are expected for `Fine` rows.
- Monetary amounts are enforcement context, not a quality score.
- Any future totals should disclose whether exact duplicate source rows were retained or deduplicated.

## 9. Facility-Level Readiness

This source appears ready after validation for future planning of:

- facility-level penalty timeline;
- facility-level fine amount totals over a defined source window;
- enforcement event counts;
- payment-denial indicator/counts;
- payment-denial duration summaries;
- state-level enforcement summaries.

Important denominator risks:

- Row-level enforcement actions are not the same as facility counts.
- Fine amount totals are not citation counts.
- Payment denial rows are not fine rows.
- Facility-level totals need a defined time window.
- Facility-year counts need explicit date rules.
- State-level percentages require a denominator, such as current facilities, facilities active in the source window, or facilities with any penalty rows.
- This rolling CMS source is described as covering the last three years, so it should not be presented as complete historical enforcement history.

## 10. Risks And Caveats

- Penalties are enforcement actions, not citations.
- Penalty date is not necessarily the original survey date or citation date.
- Payment denial start date is not the same as penalty date.
- Processing date is not the same as enforcement date.
- The source does not provide a direct field tying penalty rows to Health Deficiencies or Fire Safety Deficiencies citation rows.
- Duplicate source rows require a documented future handling rule before totals are displayed.
- Do not treat penalty amount as a care-quality score.
- Do not treat absence from this source as absence of all enforcement history.
- Do not make legal conclusions beyond official source language.

## 11. Recommended Next Phase

Recommended next phase: **Phase 11D.10: Penalties / Enforcement Data Contract and Builder Planning**.

Suggested scope:

1. Define `data/nursing_home_penalties_ct.json` as a future output, but do not create it yet.
2. Specify metadata, row fields, duplicate handling, date semantics, and denominator guardrails.
3. Decide whether the future builder should default to validation-only dry run and optionally write a non-runtime `data/testing/` preview.
4. Preserve fine rows and payment denial rows with separate fields and labels.
5. Keep penalties separate from health deficiencies, fire safety deficiencies, citation descriptions, and staffing calculations.

