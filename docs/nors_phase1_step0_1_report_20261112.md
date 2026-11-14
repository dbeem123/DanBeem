# NORS Phase 1 — Steps 0–1 report

Date: 2026-11-12
Worktree: `C:\Users\Dan\Documents\Codex\nors-phase1-step0-1-20261112`
Branch: `codex/nors-phase1-step0-1-20261112`
Base: `origin/main` at `494d3cd32931a9d4756959a8f3b23f8a4e4a72d0`
Status: **Steps 0–1 complete and committed locally. No push.**

## Revision 4 source pack

Used only the Revision 4-listed source families from the supplied `GitHub\DanBeem\source_data\` directory; copied their exact bytes into this isolated worktree's ignored `source_data/` directory. The original OneDrive source pack was left unchanged. The additive `revision4_source_inventory` in `data/nors_source_pack_lock.json` records each exact filename/path, byte size, SHA-256, Daniel-supplied retrieval date (`2026-11-12`), date basis, and printed edition/revision where present. The filename with the browser suffix is preserved exactly. 105 listed source files (74,919,407 bytes) were copied and all 105 were rechecked: **0 missing, 0 size mismatches, 0 SHA-256 mismatches**. `git check-ignore -v` confirmed the root source_data ignore rule; no supplied source file is staged or committed.

The unrelated `Agent-Broker-Help-Desks Updates_051024_0.pdf` was excluded and recorded as unrelated. The excluded annual/trend XLSX files and other handoff-listed exclusions were not copied into the Revision 4 inventory. The existing `source_data/nors_sources/` legacy ignored bundle was not moved or edited.

Currency check: Connecticut eRegulations shows §§17b-411-1—17b-411-14, last updated 11/03/2015; the saved PDF title sheet says revised 2015-11-2. No newer text is shown by the official portal. The checked portal section is https://eregulations.ct.gov/eRegsPortal/Browse/RCSA/Title_17bSubtitle_17b-411Section_17b-411-1/ . The saved Chapter 368v HTML contains §§19a-532 and 19a-550. The saved Chapter 319l HTML contains §17a-878(c), which states the resident-record confidentiality limitation for the Office's access/use. DAS AI-01 through AI-04 versions were not supplied (state-internal and not expected); logo-use permission is not a source file and remains unverified.

## Source extraction check

`scripts/audit_nors_source_quality.py` uses `pypdf 6.10.2` for PDFs and Python standard-library HTML/XML parsing. It does no OCR, installs, or source modifications. The reproducible details are in `docs/nors_source_quality_20261112.md`: 83 PDFs / 4,364 pages scanned; 208 pages have fewer than 40 non-whitespace extracted characters and are flagged (including graphic slide pages; the threshold is not itself proof of a scan). The 2019 standards PDF has no extractable text on its 10 pages; multiple slide PDFs have sparse/image-oriented pages. No authority text was guessed from these pages. The 45 CFR Part 1324 Subpart A PDF and HTML contain the same 19 section identifiers (no PDF-only or HTML-only identifiers); this is a structural match, not a byte-for-byte rendering comparison.

## Step 1 audit and corrections

Added the read-only `scripts/audit_nors_crosswalk.py` and findings in `docs/nors_crosswalk_audit_20261112.md`. Against the Revision 4 Appendix PP PDF: 94 existing tag-page entries audited, 0 page-map discrepancies; 60 code records contain Connecticut overlay fields, 49 empty; 74 authority references, none missing from `authority_index.json`; six tracked UTF-8 BOM files; root and `data/keyword_map.json` hashes differ, so `/data` remains source of truth.

For F554, `heading_exact` is now exactly `F554`, and `display_title` carries the separate descriptive name. The exact F554 tag heading starts on PDF page 17, its associated 42 CFR 483.10(c)(7) text starts on page 18, and the investigative text cites F554 on page 19. F554 is in a dedicated medication-self-administration group. The reserved F556 page anchor is 20. The CT inspection builder was rerun with the supplied latest ignored data:

- `source_data/cms_survey/NH_SurveyDates_Oct2026.csv`
- `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`
- `source_data/provider_info/NH_ProviderInfo_Oct2026.csv`

It regenerated 9,585 citations and the CT roster (197 CCNs; 191 in Provider Information; 171 with PBJ 2026Q2). The derived records include the corrected F554 and F556 anchors. The detailed source data stays ignored.

## Verification

- Source lock: **105 files, 0 mismatches**.
- Builder: completed; 9,585 citations and 191 homes in the inspections file.
- `python -m unittest discover -s scripts -p test_ct_inspections.py -v`: **14 passed**.
- `python scripts/audit_nors_crosswalk.py --write-report`: completed; 0 page-map discrepancies.
- Source quality scan: completed; report saved as `docs/nors_source_quality_20261112.md`.
- No UI changes, live service changes, installations, OCR, database access, or pushes.

## Backups

Exact-byte backups with SHA-256 verification were created before edits under:

`C:\Users\Dan\Documents\Codex\nors-phase1-followup-backups-20261112T193225Z\before\`

This follow-up backup includes the modified JSON, tests, scripts, and existing report files. Earlier pre-task backups are preserved at `C:\Users\Dan\Documents\Codex\nors-phase1-backups-20261112T182542Z\before\`.

## Files changed

- `data/nors_source_pack_lock.json`
- `data/appendix_pp_tag_pages.json`
- `data/reference/resident_rights_tag_map.json`
- `data/ct_inspections.json`
- `data/nursing_home_facility_roster_ct.json`
- `scripts/audit_nors_crosswalk.py`
- `scripts/audit_nors_source_quality.py`
- `scripts/test_ct_inspections.py`
- `docs/nors_crosswalk_audit_20261112.md`
- `docs/nors_source_quality_20261112.md`
- This report
