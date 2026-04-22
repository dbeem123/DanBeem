# NORS Knowledge Base Batch 1 Integration Notes

## Files Staged
- `data/nors_knowledge_base_batch1.json`
- `data/nors_knowledge_base_batch1_notes.md`

## Integrated Now
- `code_summary_rows` are used by `Assets/crosswalk.js` to enrich NORS code guidance in the Drafting Assistant and NORS Crosswalk Tool.
- `handout_or_resource_urls` from matched `code_summary_rows` are surfaced in Crosswalk Tool resources through shared crosswalk logic.

## Not Promoted Yet
- `authority_rows` are not yet merged into `crosswalk_catalog.json` or `authority_index.json`.

## Reason
- Original Batch 1 authority rows had `appendix_pp_pdf_page_start` values set to `null`.
- Current live Appendix PP page starts are now staged in `data/appendix_pp_tag_pages.json` and are used by the shared crosswalk renderer for existing F-tag links.
- Authority-row promotion still needs a separate merge pass so each new or revised mapping is reviewed against existing `crosswalk_catalog.json` mappings and any deprecated tag references are cleaned up deliberately.

## Next Safe Step
- Merge verified authority rows into `authority_index.json` and `crosswalk_catalog.json`, preserving:
  - `mapping_confidence`
  - `human_review_note`
  - exact eCFR URLs
  - exact CGA section anchors
  - `no_direct_f_tag` caveats
  - Appendix PP live PDF page starts from `data/appendix_pp_tag_pages.json`
