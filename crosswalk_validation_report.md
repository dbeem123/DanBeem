# Crosswalk Validation Report

Generated: 2026-04-21

## Files reviewed

- C:\Users\Dan\Downloads\nors_hierarchy.json
- C:\Users\Dan\Downloads\authority_index (1).json
- C:\Users\Dan\Downloads\crosswalk_catalog.json
- C:\Users\Dan\Downloads\keyword_map (1).json
- C:\Users\Dan\Downloads\retrieval_rules (1).json

## Source list used

- National Ombudsman Resource Center / Consumer Voice NORS page: https://ltcombudsman.org/omb_support/nors
- NORS Table 2 Complaint codes and definitions: https://ltcombudsman.org/uploads/files/support/NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf
- NORS updated complaint codes list: https://ltcombudsman.org/uploads/files/support/nors-updated-complaint-codes-list.pdf
- eCFR 42 CFR Part 483 Subpart B: https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-483/subpart-B
- eCFR 45 CFR Part 1324 Subpart A: https://www.ecfr.gov/current/title-45/subtitle-B/chapter-XIII/subchapter-C/part-1324/subpart-A
- CMS R232SOMA transmittal for Appendix PP: https://www.cms.gov/medicare/regulations-guidance/transmittals/2025-transmittals/r232soma
- CMS Appendix PP PDF: https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf
- Connecticut LTCOP regulations/statutes page: https://portal.ct.gov/ltcop/regulations
- Connecticut General Assembly Chapter 319l: https://www.cga.ct.gov/current/pub/chap_319l.htm
- Connecticut General Assembly Chapter 368v: https://www.cga.ct.gov/current/pub/chap_368v.htm

## Gaps found

- NORS hierarchy and crosswalk catalog are complete against each other: 60 hierarchy minor codes and 60 catalog records.
- Missing crosswalk records: None.
- Extra catalog records not in hierarchy: None.
- Authority IDs referenced but missing from authority_index.json: None.
- Duplicate keyword phrases: None.
- Non-facility K/L records with Appendix PP tags: None.

## Corrections made

- Normalized all required files to the requested production shapes.
- Repaired mojibake in citations and titles, including section symbols and dash characters.
- Added missing state_overlay mapping legend entry to crosswalk_catalog.json.
- Rebuilt authority reverse links from forward crosswalk records and keyword mappings so each authority carries related topics and NORS codes.
- Removed F551 from L01 and related keyword records because L01 is a non-facility representative/family conflict code and should not be forced into facility F-tag mappings.
- Sorted keyword records by phrase for deterministic lookup/review.
- Preserved official source URLs at section or source-document level.
- Preserved F-tag consolidation note for transfer/discharge tags F627/F628 in retrieval_rules.json.

## Uncertain mappings retained

None labeled uncertain in the working draft.

## Duplicate / conflicting mappings resolved

- No duplicate keyword phrases remained after normalization.
- No referenced authority IDs were missing after reverse-link rebuild.
- Non-facility K/L codes do not carry Appendix PP/F-tag mappings in the normalized catalog.

## Records needing human review

- K02, K03, K04, K05, K06, L01, L02: intentionally have no direct 42 CFR Part 483/F-tag mappings because they are non-facility or outside-agency complaint types.
- K01 and L03: include Ombudsman program authority only as topic-based or related support; review if Connecticut program wants additional state-specific workflow references.
- State overlay mappings should be reviewed by Connecticut LTCOP counsel/program leadership before use as legal authority in public-facing materials.

