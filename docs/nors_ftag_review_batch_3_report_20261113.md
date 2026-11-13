# NORS batch 3 triage and title-regulation fallback report

## Batch 3 triage (not imported)

Created `docs/nors_ftag_review_batch_3_claude_triage.csv` from the regenerated batch 3 candidate sheet. Every sheet row has a decision; the separate F646/F03 addition is included. Nothing from this sheet was imported into `data/nors_reviewed_links.json`.

- **71 total rows:** 8 keep, 3 add, 60 drop.
- Kept: F636/F03 (check), F637/F07 (check), F644/F03, F645/F03, F655/F03, F656/F03, F656/F01 (check), F658/F12 (check).
- Added: F646/F03 (check), F657/F03, F658/F03. Every addition quotes the CMS title and the F03 Table 2 definition with source locators.
- F646/F03 is a manual addition; the builder still produces no candidate for F646. F657/F03 is newly surfaced by the fallback. F658/F03 already appeared in the prior candidate sheet; the fallback now supplies its basis.
- All other batch 3 sheet rows were marked drop. Batch 3 remains for Daniel/Claude review; no decision was imported.

### Rows per tag

- F635: 1
- F636: 5
- F637: 5
- F638: 4
- F639: 2
- F640: 5
- F641: 5
- F642: 1
- F644: 5
- F645: 5
- F646: 2
- F655: 5
- F656: 5
- F657: 5
- F658: 5
- F659: 5
- F661: 1
- F842: 5

### Addition evidence

Table 2 F03, quoted in the three add rows:

> F03 Facility does not create or follow a person- centered care plan. Care planning does not include the resident or resident representative, or staff disregards or is not informed of the plan. s Use if the nursing home resident�s Specialized Services an indicated by a PASRR level II screen are not included in the care plan. Use if care plans are not scheduled, not enough time allowed at the meeting, or a copy of plan is not provided to the resident, etc.

Locator: `source_data/NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf; PDF page 10; Table 2 row F03`. The title quote and its CMS CSV locator are in evidence field 1 of each add row. The extracted Table 2 text is kept verbatim, including source-extraction artifacts.

## Builder fix and regenerated candidate sheets

The shared builder now falls back to the CMS title and Regulation sentence when matching each allowed Table 2 code. It compares ordered, stemmed phrases of two or more meaningful terms; single common words cannot trigger a match. “Care plan” is retained as a specific phrase despite the broad keyword stoplist. Fallback evidence carries the CMS CSV or Regulation locator and is labeled `title_regulation_fallback`. Existing app links keep their existing basis and evidence.

Candidate sheet counts after rerun: batch 1 **219 rows/219 candidates**, batch 2 **23 rows/21 candidates**, batch 3 **70 rows/66 candidates**. Batch 3 rows by tag are listed above; its triage sheet has 71 rows because of the manual F646/F03 add.

### Candidate changes vs. the pre-fix sheets

These are suggestion-sheet changes, not imported review decisions:

**Batch 1:** 219→219 rows; 219→219 candidates.
- Added pairs: F550/C03, F551/F03, F551/F08, F551/H03, F560/D02, F560/F03, F561/D04, F561/G02, F568/D02, F568/F03, F571/F03, F571/F05, F571/F08, F573/F03, F574/B02, F574/J01, F576/B03, F577/D02, F577/F03, F578/D04, F580/F01, F602/A01, F602/A03, F602/F12, F603/A01, F603/F12, F609/D06, F610/F02.
- Removed pairs: F550/D03, F551/B01, F551/F07, F551/G01, F560/D06, F560/F07, F561/F11, F561/H02, F568/B03, F568/C02, F571/C01, F571/D09, F571/H03, F573/D01, F574/C02, F574/J02, F576/F11, F577/D04, F577/I03, F578/C01, F580/F13, F602/D02, F602/E02, F602/J03, F603/D02, F603/F11, F609/E02, F610/D04.
- Basis changed to title/regulation fallback: F566/D02, F566/F03, F571/C02, F571/E01, F574/D02, F574/D06, F575/D02, F575/D06, F575/J01, F578/B01, F582/C02, F582/C03, F582/E01, F586/B03, F600/J01, F602/J01, F603/J01, F606/J01, F607/A05, F609/A05, F609/F01, F610/D06, F610/J01.

**Batch 2:** 23→23 rows; 17→21 candidates.
- Added pairs: F622/C03, F623/C03, F624/C03, F625/C03.
- Removed pairs: none.
- Basis changed to title/regulation fallback: F621/C03.

**Batch 3:** 68→70 rows; 63→66 candidates.
- Added pairs: F639/F03, F639/F08, F644/F08, F655/F08, F656/F08, F657/F03, F657/F08, F658/F08, F659/F03, F659/F08.
- Removed pairs: F644/F10, F655/F06, F656/F10, F657/F06, F657/F10, F658/F10, F659/F04.
- Basis changed to title/regulation fallback: F644/F03, F658/F03.

The batch 1 and batch 2 triage records were not edited; their Git blob SHA-1 hashes remain `9bbf9bf30d4b5f248760167a8b2117f64a33f1f9` and `05699a8a40df04e4ddfa62cb13abe715711d8612`. Their keep/drop/add decisions are unchanged.

## Requested no-decision lookup

Full quoted definitions and Table 2 locators are in `docs/nors_ftag_title_lookup_batch3_20261113.md`. The lexical lookup reports every definition with at least one stemmed title-key-term match, with no keep/add/drop recommendation:

- F635: 8 matching Table 2 definitions.
- F639: 14 matching Table 2 definitions.
- F642: 11 matching Table 2 definitions.
- F661: 15 matching Table 2 definitions.
- F842: 8 matching Table 2 definitions.
- F659: 8 matching Table 2 definitions.

## Validation

- `py -m unittest discover -s scripts -p "test_nors*.py"` — **48 passed**.
- `git diff --check` — passed.
- Batch 3 triage remains unimported; no live or publication changes were made.
