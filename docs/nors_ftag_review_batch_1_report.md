# Revision 6 review batch

The CSV contains 1,222 draft rows for 44 tags in §§483.10 and 483.12. Generated candidates are context for human review, not coding decisions. Existing app links are additional rows marked `existing_app_link`; they are not constrained by the three generated-candidate limit. Reviewer decision fields are blank.

## Rows per tag

| Tag | Rows | Tag | Rows | Tag | Rows | Tag | Rows |
|---|---:|---|---:|---|---:|---|---:|
| F550 | 37 | F551 | 15 | F552 | 3 | F553 | 10 |
| F554 | 3 | F555 | 4 | F557 | 8 | F558 | 7 |
| F559 | 4 | F560 | 10 | F561 | 11 | F562 | 4 |
| F563 | 27 | F564 | 7 | F565 | 7 | F566 | 6 |
| F567 | 3 | F568 | 6 | F569 | 3 | F570 | 9 |
| F571 | 9 | F572 | 5 | F573 | 10 | F574 | 10 |
| F575 | 3 | F576 | 8 | F577 | 3 | F578 | 42 |
| F579 | 3 | F580 | 7 | F582 | 10 | F583 | 16 |
| F584 | 15 | F585 | 13 | F586 | 3 | F600 | 207 |
| F602 | 84 | F603 | 73 | F604 | 139 | F605 | 124 |
| F606 | 18 | F607 | 78 | F609 | 143 | F610 | 15 |

## F554

Three rows use the same verbatim self-administration regulation passage: F04 matches `medications` (score 4.418), and D01 and D09 each match `right` (score 4.012). All three are Table 2 definition candidates, not decisions. The word `right` is broad; review the full definitions and facts before retaining either link.

## Limitations and checks

The generator uses 20 NORC quiz/answer situations for which the printed answer could be tied to the situation. Other quiz and FAQ scenarios with ambiguous answer ordering or page boundaries were excluded and require structured extraction before the NORC corpus can be considered complete. Unmatched scenario fields remain blank.

The former lexical-only Step 3 JSON and Markdown batch, and their generator and tests, are retired in this commit so their superseded matches are not mistaken for the Revision 6 review sheet. They remain recoverable in Git history.

The NORS tests and CT inspection suite were run offline. This batch is for review only; no UI or publication work was done.
