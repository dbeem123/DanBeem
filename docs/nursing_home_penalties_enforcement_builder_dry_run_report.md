# Penalties / Enforcement Builder Dry Run Report

Phase 11D.11 dry-run report for the Connecticut CMS Penalties / Enforcement builder. This phase created a builder script and an ignored testing preview only. It did not create runtime JSON, build public UI, modify runtime JS/HTML, change staffing formulas, change generated staffing data, alter current or historical staffing JSON, change Connecticut applicability logic, modify geography JSON, or modify facility status review JSON.

## 1. Script Behavior

Builder script:

- `scripts/build_nursing_home_penalties_ct.py`

Default behavior:

- reads the ignored CMS Penalties source file;
- reads the current/context staffing dataset for CCN join validation;
- filters to Connecticut rows;
- normalizes CCNs while preserving leading zeroes;
- parses penalty dates, payment denial start dates, and processing dates separately;
- parses fine amounts and payment denial length in days;
- preserves source `Penalty Type`;
- adds derived fields required by the data contract;
- identifies duplicate full-row signatures;
- adds stable `source_row_hash` values;
- prints a validation summary;
- writes no output.

Optional testing behavior:

- `python scripts/build_nursing_home_penalties_ct.py --write-testing-preview`

The optional flag writes only:

- `data/testing/nursing_home_penalties_ct_preview.json`

The script never writes:

- `data/nursing_home_penalties_ct.json`

## 2. Source Files Used

| Source | Path |
|---|---|
| CMS Penalties source | `source_data/cms_enforcement/NH_Penalties_May2026.csv` |
| Current/context staffing data | `data/nursing_home_staffing_ct.json` |

CMS source metadata:

- source name: CMS Provider Data Catalog Penalties
- source file: `NH_Penalties_May2026.csv`
- CMS dataset ID: `g6vv-u9sr`
- source URL: <https://data.cms.gov/provider-data/sites/default/files/resources/c671cdaa1461db5a685367690785fcb3_1778861763/NH_Penalties_May2026.csv>
- acquired date used in metadata: 2026-06-22

## 3. Dry-Run Validation Summary

| Measure | Result |
|---|---:|
| Source file size | 2,768,010 bytes |
| Total source rows | 16,571 |
| Connecticut rows | 179 |
| Unique CT CCNs | 102 |
| Current staffing CCNs | 196 |
| Joined CT penalty/enforcement CCNs to current staffing | 102 |
| Unmatched CT penalty/enforcement CCNs | 0 |
| Duplicate CT full-row signatures | 3 |

Join result:

- All 102 unique CT penalty/enforcement CCNs joined to `data/nursing_home_staffing_ct.json`.
- No unmatched CT CCNs were found.

## 4. Date Validation

| Date field | Minimum | Maximum |
|---|---|---|
| `Penalty Date` | 2023-05-17 | 2026-03-17 |
| `Processing Date` | 2026-05-01 | 2026-05-01 |
| `Payment Denial Start Date` | 2024-01-17 | 2024-12-03 |

Date guardrail:

- `Penalty Date`, `Payment Denial Start Date`, and `Processing Date` are preserved separately and should not be treated as interchangeable.

## 5. Penalty Type Counts

| Penalty type | Rows |
|---|---:|
| `Fine` | 167 |
| `Payment Denial` | 12 |

Derived enforcement categories:

| Enforcement category | Rows |
|---|---:|
| `fine` | 167 |
| `payment_denial` | 12 |

## 6. Fine Amount And Payment Denial Findings

| Measure | Result |
|---|---:|
| Fine amount rows parsed | 167 |
| CT fine amount total across source rows | 3,925,517.00 |
| Payment denial length rows parsed | 12 |
| Payment denial length total | 368 days |

Interpretation:

- Fine rows and payment-denial rows are separate enforcement types.
- Fine amount is not a quality score.
- Payment denial length is not a dollar amount.
- Any future totals should clearly state whether exact duplicate source rows are retained or deduplicated.

## 7. Duplicate Full-Row Signature Findings

Builder result:

- duplicate full-row signature count: 3

Builder behavior:

- preserves all CT source rows in the testing preview;
- computes stable `source_row_hash` values from normalized full source rows;
- sets `duplicate_full_row_signature` to `true` for duplicate occurrences after the first matching full-row signature;
- reports the duplicate count in metadata.

Recommendation:

- Runtime publication should not silently discard duplicate rows.
- If future summaries use deduplicated counts or totals, they should include a documented, reproducible rule and metadata for both source-row counts and deduplicated counts.

## 8. Testing Preview Output

Testing preview created:

- `data/testing/nursing_home_penalties_ct_preview.json`

Preview details:

| Measure | Result |
|---|---:|
| Preview file size | 159,519 bytes |
| Penalty/enforcement records | 179 |

This file is non-runtime, ignored by Git, and should not be committed. It exists only to verify the future JSON shape and builder behavior.

Runtime output status:

- `data/nursing_home_penalties_ct.json` was not created.

## 9. Derived Fields Added In Preview

Each preview record includes the contract fields plus derived fields:

- `enforcement_category`
- `has_fine`
- `has_payment_denial`
- `normalized_fine_amount`
- `display_amount`
- `event_year`
- `source_row_hash`
- `duplicate_full_row_signature`

## 10. Verification Commands

Commands run:

```powershell
python -m py_compile scripts/build_nursing_home_penalties_ct.py
python scripts/build_nursing_home_penalties_ct.py
python scripts/build_nursing_home_penalties_ct.py --write-testing-preview
```

Results:

- Python compile check passed.
- Dry run passed and wrote no output.
- Testing preview run passed and wrote only `data/testing/nursing_home_penalties_ct_preview.json`.
- Runtime output `data/nursing_home_penalties_ct.json` does not exist.

## 11. Runtime Readiness Recommendation

The builder is ready for a future runtime JSON build phase after these decisions are approved:

1. Whether runtime summaries retain exact duplicate source rows or use deduplicated summary counts/totals.
2. Whether public display should show both fine rows and payment-denial rows in one enforcement timeline or separate subsections.
3. How facility-level totals should define the source time window.
4. What denominator labels should be used for state-level summaries.
5. Whether additional CMS or state enforcement sources are needed before public display.

Recommended next phase: **Phase 11D.12: Survey / Enforcement Runtime Architecture Decision**, or a narrower penalties runtime build phase if the duplicate and denominator rules are accepted.

