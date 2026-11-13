# NORS F-tag review batch 3 — §§483.20–483.21

Status: draft for Claude triage. Candidate rows do not control coding; all review fields are blank.

## Scope and method

The sheet covers 18 tags whose source index cites §483.20 or §483.21. It uses the same deterministic rarity-weighted overlap method as batch 2, one row per candidate code, at most five rows per tag, up to three evidence excerpts, and retention of existing app links. Evidence is selected from Appendix PP examples, key-element passages, and deficiency categorization/severity passages.

No approved section-map entries exist for §§483.20–483.21. The separate draft at `data/nors_section_prior_483_20_21_draft.json` proposes category F (“Care”) for both sections based on the Table 2 heading. It is marked draft and pending Daniel's approval; existing app links remain included even when outside category F.

## Row counts

- Total rows: **68** (63 candidate-code rows and 5 no-candidate rows).
- Per tag: F635 **1**, F636 **5**, F637 **5**, F638 **4**, F639 **1**, F640 **5**, F641 **5**, F642 **1**, F644 **5**, F645 **5**, F646 **1**, F655 **5**, F656 **5**, F657 **5**, F658 **5**, F659 **4**, F661 **1**, F842 **5**.
- No-candidate rows: F635, F639, F642, F646 and F661. The builder found no qualifying category F match at the review threshold for these tags; this is not a finding that no relevant code could apply.
- Existing app links included: F655→F03 and F656→F03.

## Checks

- `py scripts/build_ftag_review_batch_3.py` — 18 tags, 68 rows.
- `py -m unittest scripts.test_nors_ftag_review_batch_3 -v` — 5 passed.
- `py -m unittest discover -s scripts -p "test_nors*.py"` — 45 passed.
- `node scripts/test_nors_source_ui.js` — passed.

The review CSV is `docs/nors_ftag_review_batch_3.csv`. No push or publication was performed.
