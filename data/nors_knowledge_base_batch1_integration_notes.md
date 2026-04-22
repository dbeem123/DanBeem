# NORS Knowledge Base Batch 1 Integration Notes

## Files Staged
- `data/nors_knowledge_base_batch1.json`
- `data/nors_knowledge_base_batch1_notes.md`

## Integrated Now
- `code_summary_rows` are used by `Assets/crosswalk.js` to enrich NORS code guidance in the Drafting Assistant and NORS Crosswalk Tool.
- `handout_or_resource_urls` from matched `code_summary_rows` are surfaced in Crosswalk Tool resources through shared crosswalk logic.
- `authority_rows` are used by `Assets/crosswalk.js` as supplemental authority mappings at runtime. They add exact 45 CFR Ombudsman authority, Connecticut statute overlays, and verified Appendix PP page links without replacing the baseline `crosswalk_catalog.json`.
- `do_not_map_catalog` is surfaced as review caveats in crosswalk warnings and the Drafting Assistant trace area.

## Not Promoted Yet
- `authority_rows` are not yet permanently merged into `crosswalk_catalog.json` or `authority_index.json`.

## Reason
- Original Batch 1 authority rows had `appendix_pp_pdf_page_start` values set to `null`.
- Current live Appendix PP page starts are now staged in `data/appendix_pp_tag_pages.json` and are used by the shared crosswalk renderer for existing F-tag links.
- Runtime use is safer than a permanent catalog rewrite until each Batch 1 row receives SME review against existing `crosswalk_catalog.json` mappings.
- `A01|F602` is skipped at runtime because the Batch 1 label conflicts with the current F602 misappropriation/exploitation meaning.

## Next Safe Step
- Review the runtime supplemental mappings, then permanently promote approved rows into `authority_index.json` and `crosswalk_catalog.json`, preserving:
  - `mapping_confidence`
  - `human_review_note`
  - exact eCFR URLs
  - exact CGA section anchors
  - `no_direct_f_tag` caveats
  - Appendix PP live PDF page starts from `data/appendix_pp_tag_pages.json`
