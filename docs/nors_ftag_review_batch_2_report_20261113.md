# NORS F-tag review batch 2 — §483.15

## Daniel-approved decisions

Created `docs/nors_ftag_review_batch_2_claude_triage.csv` from the candidate sheet in the batch 1 review format. Every decision records Daniel's approval on 2026-11-13 and the method `approved Claude first-pass triage`.

- Keep: 6 pairings — F620/C01, F621/C01 (check), F627/C03 and C02, F628/C03 and C02.
- Drop: 11 pairings — F620/C02,C03,C04; F621/C02,C03,C04; F627/C01,C04; F628/D02,C04,C01. These are stored as rejected records.
- Add: 7 pairings — F622/C03; F623/C03,C02; F624/C03; F625/C03; F626/C03; F660/D02.
- F660/D02 is a weak, title-only check. It remains visibly labeled `weak — title-only, check`; its extracted Appendix PP content is only a relocation note. F660/C03 is not imported.

Batch 2 triage sheet: **24 rows** (6 keep, 11 drop, 7 add). By tag: F620 4, F621 4, F622 1, F623 2, F624 1, F625 1, F626 1, F627 4, F628 5, F660 1.

## Section map

The §483.15 section map remains `draft`, with category C only and `controls_coding: false`. Recommendation: do **not** add D02 to this broad category map. D02 is a specific, weak, title-only F660 candidate, while the map's schema maps whole categories. Keep that candidate visible with its weak label and revisit the section map only if the broader D-category mapping is independently supported and approved.

## Data totals after import

- Reviewed links: **102** total (89 from batch 1 and 13 from this batch).
- Rejected links: **151** total (140 from batch 1 and 11 from this batch).
- F660/D02: reviewed, `basis: coded_by_reviewer`, `link_strength: weak`, `evidence_basis: title_only`.
- F660/C03: absent.
- Batch 3 (`59fa009`) was not changed or started.

## Validation

- `py -m unittest discover -s scripts -p "test_nors*.py"` — **45 passed**.
- `node scripts/test_nors_source_ui.js` — **passed**. Covers accepted and rejected link display, the weak F660/D02 label, medication search, navigation, and selection behavior.
- `git diff --check` — **passed**.

No publication or push was performed.
