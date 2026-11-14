# Example-first Appendix PP to NORS review: batches 4–6

## Purpose and boundaries

This is a supplemental, non-operative research layer for the current NORS crosswalk work (roadmap item 1, “NORS casework tools”). It starts from concrete Appendix PP passages flagged `is_example`, then traces their words backward to NORS Table 2 definitions. It keeps the source excerpts and locators side by side so a reviewer can see how the language connects.

Every generated row is marked `status: draft` and `controls_coding: false`. A row is only a review lead: word overlap does not establish that a NORS code applies to a case. No rows were imported into reviewed links, no site/UI files changed, and no complaint examples were authored.

## Method

- **Pass 1 — example anchor (required):** begin with an extracted Appendix PP passage flagged `is_example: true`; join continuation pages and retain all locators.
- **Pass 2 — separate Appendix PP corroboration:** look for the same NORS definition in a key-element, severity or deficiency-categorization passage. It must have at least two shared non-stoplist terms and weighted support of at least 3.
- **Pass 3 — regulation corroboration:** look for an exact multiword phrase shared by the tag’s regulation text and that NORS definition, plus two shared terms and weighted support of at least 3.
- **Pass 4 — official training scenario:** require the same printed NORS answer code, a shared multiword phrase with the Appendix PP example, at least three shared useful terms and weighted support of at least 3. No candidate in this batch set passed this strict scenario check; the builder does not relax it to force corroboration.
- For each passage, candidate definitions are limited to the categories in the Daniel-approved, non-coding section maps for batches 4–6.
- Matching reuses the existing standard-library stemmer, stoplist and inverse-frequency weights from the crosswalk builder. Candidates rank first by the count of distinct passes, then by the strongest example-language score, then by the number of separate Appendix PP example passages that match. At most five candidates are shown per tag.
- Table 2 “Use” directions are displayed verbatim as a separate routing check. They do **not** count as a positive support pass and cannot be outweighed by a higher rank.
- These are distinct checks, not statistically independent evidence: the Appendix PP example, contextual and regulation checks draw from the same CMS manual. The official training-scenario check uses a separate NORS training source.
- The output includes the verbatim passage and its Appendix PP locator, the verbatim Table 2 definition and row locator, any exact sentence containing a Table 2 “Use” instruction, shared terms, score and draft flags.
- This method exposes possible language paths for review. It is not semantic analysis, a coding recommendation, or an automatic link approval. Broad matches and missing matches both need reviewer judgment.

## Coverage

| Batch | Appendix PP sections | Tags | Example passages | Candidate pairs | 1 pass | 2 passes | 3 passes | Tags with a candidate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 4 | §483.24–25 | 23 | 364 | 94 | 29 | 60 | 5 | 19 |
| 5 | §483.30–45 | 27 | 211 | 96 | 35 | 59 | 2 | 22 |
| 6 | §483.70–90 | 44 | 232 | 67 | 38 | 27 | 2 | 26 |
| **Total** |  | **94** | **807** | **257** | **102** | **146** | **9** | **67** |

Pass frequency across candidate pairs: required example anchor, 257; separate key-element/severity support, 151; regulation phrase support, 13; official training scenario support, 0. Passes can overlap, so the frequencies are not additive.

Tags with no qualifying example-first candidate under this threshold: batch 4 F676, F680, F691, F696; batch 5 F711, F728, F730, F759, F801; batch 6 F835, F836, F839, F840, F843, F844, F850, F866, F907, F910, F913, F916, F918, F921, F922, F923, F924, F926. Absence here means only that this pass did not find enough distinctive shared terms in extracted example passages; it does not mean no relationship exists.

## Example trace

For F687, an Appendix PP Guidance example says: “Facility staff must follow proper infection prevention practices for foot care equipment/devices, including but not limited to nail clippers, scalers, files, and burr tools.” Its locator is `source_data/som107ap_pp_guidelines_ltcf_0.pdf; PDF page 344; Guidance; appendix-pp-f687-p7`.

The highest related candidate in this trace is NORS F13: “F 13 Insufficient measures to prevent or control infection Includes failure to follow infection control procedures; staff not wearing, or not properly wearing, necessary personal protective equipment (PPE); facility not providing necessary PPE; spread of infection; infection unreported or not treated appropriately; and similar problems.” Its locator is `PDF page 13; Table 2 row F13`. Shared terms are `control, equipment, infection`; match basis is shared phrase and terms; score 10.650. This is a concrete, source-visible connection between the example’s equipment cleaning and infection-control language and the NORS definition. The row remains draft and does not decide a case.

## Files and verification

- Builder: `scripts/build_nors_example_first_crosswalk.py`
- Test: `scripts/test_nors_example_first_crosswalk.py`
- Review data: `docs/nors_ftag_example_first_batches_4_6.csv`
- `py scripts/build_nors_example_first_crosswalk.py` — generated 257 candidate pairs from 807 example passages and recorded distinct pass counts.
- `py -m unittest scripts.test_nors_example_first_crosswalk -v` — 5 passed, including the rule that multiple distinct checks outrank a higher single-check lexical score.
- `py -m unittest discover -s scripts -p "test_nors*.py"` — 61 passed, 0 failed after the multi-pass ranking update.
- `node scripts/test_nors_source_ui.js` — passed.
- `py scripts/validate_nors_example_worksheet.py --allow-empty` — passed; 60-code complaint worksheet remains blank.
- `git diff --check` — passed.

## Next review

Use the multi-pass ranking to prioritize review of batches 4–6: start with Appendix PP examples supported by a second source-text pass, then inspect the exact Table 2 definition and routing language. Keep all current `check` and `needs_claude` statuses until a reviewer decides them. Do not treat a higher rank as a coding decision.
