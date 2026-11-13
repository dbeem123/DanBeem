# NORS F-tag review batch 2 — §483.15

Status: draft for Claude triage. The section map is a proposal awaiting Daniel's approval; no candidate controls coding.

## Batch 1 review record

Committed `docs/nors_ftag_review_batch_1_claude_triage.csv` with its original row decisions unchanged and the triage field recording Daniel's approval of Claude's first pass on 2026-11-13. It contains 229 rows: 79 keep, 140 drop, and 10 add. The row-level reasons and added codes remain recorded in the CSV.

## Batch 2 scope and method

The batch covers the 10 Appendix PP tags whose source index cites §483.15: F620–F628 and F660. Candidate generation follows the batch 1 method: one row per candidate code, strongest three qualifying excerpts, at most five rows per tag, and existing app links retained even when outside the proposed category. Evidence is drawn from passages flagged as examples and from key-element or deficiency-categorization passages, including the severity examples within deficiency categorization.

The draft §483.15 map proposes category C, “Admission, Transfer, Discharge, Eviction,” based on the locked Table 2 heading. It is stored separately at `data/nors_section_prior_483_15_draft.json` with `status: draft`, `approval_status: pending_Daniel`, and `controls_coding: false`. Existing app links remain eligible for review outside C.

## Counts

- Total review rows: **23** (17 candidate-code rows and 6 no-candidate review rows).
- Per tag: F620 **4**, F621 **4**, F622 **1**, F623 **1**, F624 **1**, F625 **1**, F626 **1**, F627 **4**, F628 **5**, F660 **1**.
- Existing links retained: F620/C01; F621/C01; F627/C02 and C03; F628/C03 and D02.
- F622, F623, F624, F625, F626 and F660 contain only tag headers or relocation notes in the extracted Appendix PP data, with no qualifying example, key-element or severity evidence. Their rows therefore have no candidate code and explain the evidence gap rather than inventing a pairing.

## Checks

- `py scripts/build_ftag_review_batch_2.py` — completed; 10 tags, 23 rows.
- `py -m unittest scripts.test_nors_ftag_review_batch_2 -v` — 6 passed.
- `py -m unittest discover -s scripts -p "test_nors*.py"` — 39 passed.

No push or publication was performed. The batch 2 CSV is draft review material; all decisions remain blank.
