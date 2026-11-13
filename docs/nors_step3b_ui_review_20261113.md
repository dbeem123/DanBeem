# Step 3b and source UI — review report

Status: local draft for Claude review. Batch 1 decisions remain pending; no publication.

## Data

- `nors_distinctions.json` contains 139 verbatim “Use” rules: 70 from Table 2 and 69 from the NORC companion handout. Counts for all 60 codes and the 17 codes without extracted rules are in the file. Twelve targets remain unresolved. All records are draft, have `controls_coding: false`, and questions remain blank pending Daniel's review. All 139 quotes were checked against cited PDF pages. Broader FAQ/training contrasts have not been exhaustively extracted.
- `nors_coding_scenarios.json` contains 13 traceable official quiz scenarios and three synthetic medication scenarios with no asserted answer, pending Daniel's review. Three expressly residential-care scenarios were excluded under the SNF scope. Ambiguous answer keys and other quiz/FAQ scenarios remain unverified; this is not a complete regression corpus.

## UI

- Code and F-tag cards, filters and source-word search use local source data. F-tag passages are loaded on demand. Existing catalog links and valid `coded_by_reviewer` entries may appear as context only; entries marked draft are excluded. The reviewed-links file is empty because batch review is pending.
- All 60 codes and 204 tags are available. Section grouping is verified only for §§483.10 and 483.12; other tags are labeled “Section not verified” instead of using potentially misleading cross-references.
- The medication pilot is **partial**: direct D09 and F554 selectors work and F554 displays its source passage. Search for “keep my own medications” does not reliably return D09 because that language is absent from its definition and an app synonym or rule has not been approved. No inferred coding rule was added.

## Checks

- `node scripts/test_nors_source_ui.js`: passed, including 60/204 selectors, F554 and draft/reviewed link filtering in a mock DOM.
- `py -m unittest discover -s scripts -p "test_nors*.py"`: 33 passed.
- The Phase 0 Edge browser harness failed before its assertions: Edge exited with Windows code 3221225477 after access/token errors. No browser presentation or privacy result is claimed. The local server started for this check was stopped.

The untracked `docs/nors_ftag_review_batch_1_claude_triage.csv` was present before this work and was left untouched. No batch decision was inferred from it. No push or publication was performed.
