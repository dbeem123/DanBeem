# NORS Phase 1 — Step 2 and Revision 5 A/C review report

Date: 2026-11-12  
Branch: `codex/nors-phase1-step0-1-20261112`  
Base: `494d3cd32931a9d4756959a8f3b23f8a4e4a72d0`

## Completed locally

- Step 0–1 fixes are committed in `17800dfe19888ea537ad331b2523916ce8757839`, `0c863fc602256d0e2f9216701438e660e028f46e`, and `79449201d86af839208b1f18c41adf879887da18`.
- Extended the ignored-source lock for the Revision 4 source inventory. The supplied `source_data/` copy matched all 105 locked hashes. Source files remain ignored and are not part of the commits.
- Rebuilt the inspection data from `source_data/cms_survey/`; the existing inspection suite passes.
- Corrected the F554 `heading_exact` field as described in the Step 0–1 audit.
- Built the exact-source primary authority records, Appendix PP extracts and indexes, ambiguity data, complete 60-code topic mapping, and separate NORS/Appendix PP term index.
- Added the app-guidance label to the 17 existing curated complaint-code guidance entries. No guidance entries were added or presented as official NORS text.
- Step 2/Revision 5 A/C generated outputs and builder are local changes pending this report commit.

## Data inventory

- `nors_primary_authority.json`: 8,462 records: 60 Table 2 definitions, 60 lower-priority NORC handout entries, 35 NORS principles/FAQ/quiz-answer passages, 11 Connecticut statute passages, one federal regulation passage, one Connecticut regulation passage, and 8,294 CMS Appendix PP regulation and interpretive-guidance passages.
- `appendix_pp/index.json` and tag extracts: 204 active/shared tags; extraction quality is 201 `text_extracted`, two `review_shared_section` (F553 and F801), and one `review_low_text` (F949, page 923). F556 and F581 are reserved; F758 is deleted and excluded. Shared sections are explicitly marked, not fabricated as standalone tag text.
- The locked PDF and existing tag metadata do not supply short titles for 106 of the 204 tags. Those titles remain blank and are marked `not_printed_in_locked_pdf_or_existing_tag_metadata`; no titles were invented.
- `nors_to_topic.json` maps all 60 complaint codes to topic-slug arrays. The ambiguity file is limited to source-backed Table 2 relations; where no explicit neighbor is listed it uses the code's own definition and a neutral review prompt.
- `term_index.json` is 20,719,453 bytes and contains 72,500 normalized exact-source unigram/contiguous-bigram entries, with NORS and Appendix PP classes kept separate. No inferred synonym mapping was added.
- Deterministic 10-tag spot-check sample (seed `20261112`): F628, F948, F778, F627, F712, F919, F645, F839, F579, F926. The automated suite verifies all indexed passages against exact normalized source text and page locations.

## Validation

- `py -m unittest scripts.test_nors_primary_data -v` — **9 passed** (33.468 s).
- `py -m unittest discover -s scripts -p test_ct_inspections.py -v` — **14 passed** (0.023 s).
- `py scripts/audit_nors_crosswalk.py` — completed with exit code 0; Appendix PP page-map discrepancies: **0**; 74 authority IDs referenced and none absent from `authority_index.json`.
- The same read-only audit reports 49 empty Connecticut overlays and differing root versus `data/keyword_map.json` copies. These are recorded for Claude; no overlay or duplicate keyword map was changed here.
- `git diff --check` — passed.

## Scope and review gate

No UI work, Step 3, Step 4 pilot, or Step 5 hub changes were made. The source-backed terms are preparation for later retrieval work; they do not implement user-facing search. The 106 unavailable CMS short titles and F949's low-text page require review before any UI consumes these data.

**STOP before Step 3/UI for Claude review. No push performed.**
