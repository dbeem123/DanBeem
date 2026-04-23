# NORS Knowledge Base Batch 3 Integration Notes

## Files Staged
- `data/nors_knowledge_base_batch3.json`

## Integrated Now
- Batch 3 is loaded by `Assets/crosswalk.js` as an additional knowledge base.
- Batch 3 keyword rows are used by shared keyword matching to improve concern-text lookup for the Batch 2 code set.
- Batch 3 do-not-map caveats are surfaced in warnings, including comma-separated K/L code routing rows.
- `data/appendix_pp_tag_pages.json` was replaced with the 94 Batch 3 Rev. 232 Appendix PP page rows.

## Safety Handling
- F556 remains blocked from supplemental authority suggestions.
- F758 is treated as deleted and redirected to F605 if encountered in supplemental authority rows.
- F627 and F628 are confirmed in the page catalog at pages 197 and 219.
- F553 and F801 retain human-review notes because they do not have standalone Rev. 232 headers.

## Live Catalog Check
- The active A01 crosswalk entry does not include F602. It currently maps to F600, F607, and F609.

## Next Safe Step
- Consider permanently promoting selected Batch 3 keyword rows into `keyword_map.json` if static, file-level keyword coverage is desired outside the shared knowledge-base loader.
