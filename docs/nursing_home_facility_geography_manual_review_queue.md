# Nursing Home Facility Geography Manual Review Queue

Phase 11C.2 manual review queue. Do not assign counties or regions by guesswork.

## Summary

- Current runtime unmatched CCNs: 5
- Historical PBJ unmatched CCNs: 25
- Records requiring manual review: 25

## Current Runtime CCNs Not Found In April 2026 Provider Information

These records exist in `data/nursing_home_staffing_ct.json` but did not match April 2026 Provider Information by CCN.

| CCN | Facility name | Current runtime | Historical PBJ | City | Address | ZIP | Review reason |
|---|---|---:|---:|---|---|---|---|
| 075001 | ST JOSEPH'S CENTER | yes | yes | TRUMBULL |  |  | Current runtime CCN not found in April 2026 Provider Information. |
| 075351 | ABBOTT TERRACE HEALTH CENTER | yes | yes | WATERBURY |  |  | Current runtime CCN not found in April 2026 Provider Information. |
| 075415 | COUNTRYSIDE MANOR OF BRISTOL | yes | yes | BRISTOL |  |  | Current runtime CCN not found in April 2026 Provider Information. |
| 075432 | MATTATUCK HEALTH CARE FACILITY, INC. | yes | yes | WATERBURY |  |  | Current runtime CCN not found in April 2026 Provider Information. |
| 075441 | SPRINGS AT EAST HILL, THE | yes | yes | SOUTHBURY |  |  | Current runtime CCN not found in April 2026 Provider Information. |


## Historical PBJ CCNs Not Found In April 2026 Provider Information

These records exist in `data/nursing_home_staffing_history_ct.json` but did not match April 2026 Provider Information by CCN. They may represent closed, changed, or otherwise non-current facility context.

| CCN | Facility name | Current runtime | Historical PBJ | City | Address | ZIP | Review reason |
|---|---|---:|---:|---|---|---|---|
| 075001 | ST JOSEPH'S CENTER | yes | yes | TRUMBULL |  |  | Current runtime CCN not found in April 2026 Provider Information. |
| 075013 | CRESTFIELD REHABILITATION CENTER & FENWOOD MANOR | no | yes | MANCHESTER |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075028 | CHESTERFIELDS HEALTH CARE CENTER | no | yes | CHESTER |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075069 | REGALCARE AT GREENWICH | no | yes | GREENWICH |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075082 | HUGHES HEALTH AND REHABILITATION | no | yes | WEST HARTFORD |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075096 | GROVE MANOR NURSING HOME, INC | no | yes | WATERBURY |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075102 | MERIDIAN MANOR | no | yes | WATERBURY |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075106 | MIDDLESEX HEALTH CARE CENTER | no | yes | MIDDLETOWN |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075185 | CASSENA CARE AT NEW BRITAIN | no | yes | NEW BRITAIN |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075205 | WESTFIELD CARE & REHAB CENTER | no | yes | MERIDEN |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075210 | WATERBURY GARDENS NURSING AND REHAB | no | yes | WATERBURY |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075234 | QUINNIPIAC VALLEY CENTER | no | yes | WALLINGFORD |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075251 | TOUCHPOINTS AT FARMINGTON | no | yes | FARMINGTON |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075280 | WESTPORT REHABILITATION COMPLEX | no | yes | WESTPORT |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075282 | WOLCOTT VIEW MANOR | no | yes | WOLCOTT |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075328 | WATROUS NURSING CENTER | no | yes | MADISON |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075340 | TRINITY TERRACES | no | yes | WATERTOWN |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075346 | ROSE HAVEN, LTD | no | yes | LITCHFIELD |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075351 | ABBOTT TERRACE HEALTH CENTER | yes | yes | WATERBURY |  |  | Current runtime CCN not found in April 2026 Provider Information. |
| 075370 | BRIDGEPORT HEALTH CARE CENTER | no | yes | BRIDGEPORT |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075415 | COUNTRYSIDE MANOR OF BRISTOL | yes | yes | BRISTOL |  |  | Current runtime CCN not found in April 2026 Provider Information. |
| 075417 | THREE RIVERS | no | yes | NORWICH |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075426 | LOURDES HEALTH CARE CENTER, IN | no | yes | WILTON |  |  | Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context. |
| 075432 | MATTATUCK HEALTH CARE FACILITY, INC. | yes | yes | WATERBURY |  |  | Current runtime CCN not found in April 2026 Provider Information. |
| 075441 | SPRINGS AT EAST HILL, THE | yes | yes | SOUTHBURY |  |  | Current runtime CCN not found in April 2026 Provider Information. |


## Recommended Next Steps

1. Check each unmatched CCN against archived Provider Information snapshots, CMS Care Compare history, and PBJ source files.
2. Determine whether the CCN reflects a closed facility, changed provider number, name/address mismatch, or another non-current status.
3. Do not populate county from city, ZIP, or address until a documented matching rule is approved.
4. Do not assign LTCOP, AAA, or DPH regions until a validated region mapping exists.
5. Preserve current snapshot versus historical PBJ separation in any later public feature.
