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
- All Appendix PP `appendix_pp_pdf_page_start` values are currently `null`.
- Several F-tag assignments were confirmed through secondary sources rather than a direct Appendix PP page-start verification pass.
- The tool should not display exact PDF jump links or definitive new F-tag mappings until current CMS Appendix PP page starts are confirmed.

## Next Safe Step
- Complete an Appendix PP page-start lookup for the F-tags in Batch 1.
- Then merge verified authority rows into `authority_index.json` and `crosswalk_catalog.json`, preserving:
  - `mapping_confidence`
  - `human_review_note`
  - exact eCFR URLs
  - exact CGA section anchors
  - `no_direct_f_tag` caveats
