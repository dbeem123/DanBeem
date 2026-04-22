# NORS Knowledge Base Batch 2 Integration Notes

## Files Staged
- `data/nors_knowledge_base_batch2.json`

## Integrated Now
- `code_summary_rows` are loaded alongside Batch 1 by `Assets/crosswalk.js`.
- `authority_rows` are used as supplemental runtime mappings for Batch 2 codes.
- `do_not_map_catalog` entries are surfaced as review caveats in crosswalk warnings and Drafting Assistant trace output.
- Batch 2 Appendix PP page rows were merged into `data/appendix_pp_tag_pages.json` when no existing live-verified row was present.

## Page-Link Handling
- Existing live Rev. 232 rows in `data/appendix_pp_tag_pages.json` were preserved, including F627 and F628.
- Batch 2 rows were added with their official CMS source URL and page starts from the Batch 2 handoff.
- Reserved or deleted tags, such as F556 and F758, are retained as metadata and are not used for active citation page jumps.

## Runtime Safeguards
- F556 is blocked from supplemental authority suggestions.
- F758 supplemental references are redirected to F605.
- K and L series caveats remain visible so non-facility/system codes do not get forced into Appendix PP F-tag mappings.

## Next Safe Step
- Have a reviewer spot-check newly added Appendix PP page anchors against the current live CMS PDF for tags that were only extracted from Rev. 225.
- After review, promote approved Batch 2 authority rows into `crosswalk_catalog.json` and `authority_index.json` if permanent static rows are desired.
