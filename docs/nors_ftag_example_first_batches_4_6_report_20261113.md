# Example-first Appendix PP to NORS review: batches 4–6

## Purpose and boundaries

This is a supplemental, non-operative research layer for the current NORS crosswalk work (roadmap item 1, “NORS casework tools”). It starts from concrete Appendix PP passages flagged `is_example`, then traces their words backward to NORS Table 2 definitions. It keeps the source excerpts and locators side by side so a reviewer can see how the language connects.

Every generated row is marked `status: draft` and `controls_coding: false`. A row is only a review lead: word overlap does not establish that a NORS code applies to a case. No rows were imported into reviewed links, no site/UI files changed, and no complaint examples were authored.

## Method

- Input passages are the extracted Appendix PP passages with `is_example: true`; continuation pages are joined using the existing passage links, with all page locators retained.
- For each passage, candidate definitions are limited to the categories in the Daniel-approved, non-coding section maps for batches 4–6.
- Matching reuses the existing standard-library stemmer, stoplist and inverse-frequency weights from the crosswalk builder. A candidate needs at least two shared terms and a weighted score of at least 3.0. Up to five candidates are kept per tag, ranked by score.
- The output includes the verbatim passage and its Appendix PP locator, the verbatim Table 2 definition and row locator, any exact sentence containing a Table 2 “Use” instruction, shared terms, score and draft flags.
- This method exposes possible language paths for review. It is not semantic analysis, a coding recommendation, or an automatic link approval. Broad matches and missing matches both need reviewer judgment.

## Coverage

| Batch | Appendix PP sections | Tags | Example passages | Candidate tag/code pairs | Tags with at least one pair |
|---|---|---:|---:|---:|---:|
| 4 | §483.24–25 | 23 | 364 | 94 | 19 |
| 5 | §483.30–45 | 27 | 211 | 96 | 22 |
| 6 | §483.70–90 | 44 | 232 | 67 | 26 |
| **Total** |  | **94** | **807** | **257** | **67** |

Tags with no qualifying example-first candidate under this threshold: batch 4 F676, F680, F691, F696; batch 5 F711, F728, F730, F759, F801; batch 6 F835, F836, F839, F840, F843, F844, F850, F866, F907, F910, F913, F916, F918, F921, F922, F923, F924, F926. Absence here means only that this pass did not find enough distinctive shared terms in extracted example passages; it does not mean no relationship exists.

## Example trace

For F687, an Appendix PP Guidance example says: “Facility staff must follow proper infection prevention practices for foot care equipment/devices, including but not limited to nail clippers, scalers, files, and burr tools.” Its locator is `source_data/som107ap_pp_guidelines_ltcf_0.pdf; PDF page 344; Guidance; appendix-pp-f687-p7`.

The highest related candidate in this trace is NORS F13: “F 13 Insufficient measures to prevent or control infection Includes failure to follow infection control procedures; staff not wearing, or not properly wearing, necessary personal protective equipment (PPE); facility not providing necessary PPE; spread of infection; infection unreported or not treated appropriately; and similar problems.” Its locator is `PDF page 13; Table 2 row F13`. Shared terms are `control, equipment, infection`; match basis is shared phrase and terms; score 10.650. This is a concrete, source-visible connection between the example’s equipment cleaning and infection-control language and the NORS definition. The row remains draft and does not decide a case.

## Files and verification

- Builder: `scripts/build_nors_example_first_crosswalk.py`
- Test: `scripts/test_nors_example_first_crosswalk.py`
- Review data: `docs/nors_ftag_example_first_batches_4_6.csv`
- `py scripts/build_nors_example_first_crosswalk.py` — generated 257 candidate pairs from 807 example passages.
- `py -m unittest discover -s scripts -p "test_nors*.py"` — 60 passed, 0 failed.
- `node scripts/test_nors_source_ui.js` — passed.
- `py scripts/validate_nors_example_worksheet.py --allow-empty` — passed; 60-code complaint worksheet remains blank.
- `git diff --check` — passed.

## Next review

Use the example-first CSV as a lens when triaging batches 4–6: start with the Appendix PP scenario, read the full cited NORS definition and its “Use” directions, then decide whether the relationship is meaningful, only a possible context link, or unsupported. Keep all current `check` and `needs_claude` statuses until a reviewer decides them. Do not treat the candidate ranking as a coding decision.
