# Step 3b and source UI — review report

Status: local draft for Claude review. Batch 1 decisions remain pending; no publication.

## Data

- `nors_distinctions.json` contains 139 verbatim “Use” rules: 70 from Table 2 and 69 from the NORC companion handout. Counts for all 60 codes and the 17 codes without extracted rules are in the file. Twelve targets remain unresolved. All records are draft, have `controls_coding: false`, and questions remain blank pending Daniel's review. All 139 quotes were checked against cited PDF pages. Broader FAQ/training contrasts have not been exhaustively extracted.
- `nors_coding_scenarios.json` contains 13 traceable official quiz scenarios and three synthetic medication scenarios with no asserted answer, pending Daniel's review. Three expressly residential-care scenarios were excluded under the SNF scope. Ambiguous answer keys and other quiz/FAQ scenarios remain unverified; this is not a complete regression corpus.

## UI

- Daniel approved Claude's first-pass batch 1 triage unchanged on 2026-11-13. The review overlay contains 89 reviewed links and 140 rejected rows; reviewed links include Daniel, date and review method. Existing catalog links and validated reviewed links may appear as context only; draft and rejected rows do not render.
- All 60 codes and 204 tags are available. Section grouping is verified only for §§483.10 and 483.12; other tags are labeled “Section not verified” instead of using potentially misleading cross-references.
- The medication pilot remains contextual, not a coding rule: F554 displays reviewed links F04, D01 and D09. Daniel-approved app guidance expands a medication term paired with “own”, “my own”, “bedside” or “self” to `self-administer` for Appendix PP search only. Search ranking uses the pairing builder's rarity formula and stoplist; trigger words activate the synonym rather than outranking its source match. NORS matches and ranking use only query terms present in NORS text.
- Selecting a code or F-tag opens it immediately. Result cards scroll into view, `hashchange` and history navigation restore cards/searches, and the source revision line is labeled “Tag header.”

## Checks

- `node scripts/test_nors_source_ui.js`: passed, including the imported review metadata, F554 links F04/D01/D09, all three approved medication searches returning F554 first, rarity weighting, NORS-only ranking, scrolling, card links, hash/history navigation and open-on-select.
- `py -m unittest discover -s scripts -p "test_nors*.py"`: 33 passed.
- Claude's Chromium check of commit `5c8e5b1` passed (cards, no outside requests, no storage and no console errors). The browser check was not repeated after these changes; the local UI test and NORS Python suite passed.

The triage CSV remains unchanged. No push or publication was performed.
