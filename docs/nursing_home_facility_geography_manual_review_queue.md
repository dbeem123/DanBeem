# Nursing Home Facility Geography Manual Review Queue

Phase 11C.2 manual review queue. Do not assign counties or regions by guesswork.

## Summary

- Current runtime unmatched CCNs: 5
- Historical PBJ unmatched CCNs: 25
- Records requiring manual review: 25
- Distinct manual-review CCNs: 25

Accounting clarification: the 5 current runtime unmatched CCNs are included within the 25 historical PBJ unmatched CCNs. They are not 30 separate records. The distinct manual-review queue contains 25 CCNs: 5 current-and-historical unmatched records and 20 historical-only unmatched records.

## Classification Summary

| Classification | Count | Meaning |
|---|---:|---|
| `current_and_historical_unmatched` | 5 | CCN exists in both the current runtime export and the historical PBJ facility directory, but not in April 2026 Provider Information. |
| `historical_only_unmatched` | 20 | CCN exists in historical PBJ only and is absent from both the current runtime export and April 2026 Provider Information. |
| `current_runtime_unmatched` | 0 | No CCN exists only in the current runtime export while absent from historical PBJ and Provider Information. |
| `missing_current_provider_info_context` | 5 | Current runtime records without April 2026 Provider Information county context. Same 5 records as `current_and_historical_unmatched`. |
| `likely_closed_or_non_current_context` | 20 | Historical-only records absent from April 2026 Provider Information; this supports non-current/closed-or-changed context but does not identify the reason. |
| `unknown_needs_external_review` | 25 | All manual-review records need external/source review before assigning county. |

## Current Runtime CCNs Not Found In April 2026 Provider Information

These records exist in `data/nursing_home_staffing_ct.json` but did not match April 2026 Provider Information by CCN.

Classification: `current_and_historical_unmatched`; also `missing_current_provider_info_context` and `unknown_needs_external_review`.

| CCN | Facility name | Current runtime | Historical PBJ | City | Address | ZIP | Classification | Review reason |
|---|---|---:|---:|---|---|---|---|---|
| 075001 | ST JOSEPH'S CENTER | yes | yes | TRUMBULL |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |
| 075351 | ABBOTT TERRACE HEALTH CENTER | yes | yes | WATERBURY |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |
| 075415 | COUNTRYSIDE MANOR OF BRISTOL | yes | yes | BRISTOL |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |
| 075432 | MATTATUCK HEALTH CARE FACILITY, INC. | yes | yes | WATERBURY |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |
| 075441 | SPRINGS AT EAST HILL, THE | yes | yes | SOUTHBURY |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |


## Historical PBJ CCNs Not Found In April 2026 Provider Information

These records exist in `data/nursing_home_staffing_history_ct.json` but did not match April 2026 Provider Information by CCN. They may represent closed, changed, or otherwise non-current facility context.

Classification: the 5 current-runtime rows are `current_and_historical_unmatched`; the remaining 20 are `historical_only_unmatched`, `likely_closed_or_non_current_context`, and `unknown_needs_external_review`.

| CCN | Facility name | Current runtime | Historical PBJ | City | Address | ZIP | Classification | Review reason |
|---|---|---:|---:|---|---|---|---|---|
| 075001 | ST JOSEPH'S CENTER | yes | yes | TRUMBULL |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |
| 075013 | CRESTFIELD REHABILITATION CENTER & FENWOOD MANOR | no | yes | MANCHESTER |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075028 | CHESTERFIELDS HEALTH CARE CENTER | no | yes | CHESTER |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075069 | REGALCARE AT GREENWICH | no | yes | GREENWICH |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075082 | HUGHES HEALTH AND REHABILITATION | no | yes | WEST HARTFORD |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075096 | GROVE MANOR NURSING HOME, INC | no | yes | WATERBURY |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075102 | MERIDIAN MANOR | no | yes | WATERBURY |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075106 | MIDDLESEX HEALTH CARE CENTER | no | yes | MIDDLETOWN |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075185 | CASSENA CARE AT NEW BRITAIN | no | yes | NEW BRITAIN |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075205 | WESTFIELD CARE & REHAB CENTER | no | yes | MERIDEN |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075210 | WATERBURY GARDENS NURSING AND REHAB | no | yes | WATERBURY |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075234 | QUINNIPIAC VALLEY CENTER | no | yes | WALLINGFORD |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075251 | TOUCHPOINTS AT FARMINGTON | no | yes | FARMINGTON |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075280 | WESTPORT REHABILITATION COMPLEX | no | yes | WESTPORT |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075282 | WOLCOTT VIEW MANOR | no | yes | WOLCOTT |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075328 | WATROUS NURSING CENTER | no | yes | MADISON |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075340 | TRINITY TERRACES | no | yes | WATERTOWN |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075346 | ROSE HAVEN, LTD | no | yes | LITCHFIELD |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075351 | ABBOTT TERRACE HEALTH CENTER | yes | yes | WATERBURY |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |
| 075370 | BRIDGEPORT HEALTH CARE CENTER | no | yes | BRIDGEPORT |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075415 | COUNTRYSIDE MANOR OF BRISTOL | yes | yes | BRISTOL |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |
| 075417 | THREE RIVERS | no | yes | NORWICH |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075426 | LOURDES HEALTH CARE CENTER, IN | no | yes | WILTON |  |  | historical_only_unmatched | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075432 | MATTATUCK HEALTH CARE FACILITY, INC. | yes | yes | WATERBURY |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |
| 075441 | SPRINGS AT EAST HILL, THE | yes | yes | SOUTHBURY |  |  | current_and_historical_unmatched | Current runtime CCN not found in April 2026 Provider Information. |


## Recommended Next Steps

1. Check each unmatched CCN against archived Provider Information snapshots, CMS Care Compare history, and PBJ source files.
2. Determine whether the CCN reflects a closed facility, changed provider number, name/address mismatch, or another non-current status.
3. Do not populate county from city, ZIP, or address until a documented matching rule is approved.
4. Do not assign LTCOP, AAA, or DPH regions until a validated region mapping exists.
5. Preserve current snapshot versus historical PBJ separation in any later public feature.
