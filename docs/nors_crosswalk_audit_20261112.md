# NORS crosswalk audit — Step 1

Audit date: 2026-11-12. Read-only audit; source data and site content were not changed by the audit script.
Source PDF: `source_data/som107ap_pp_guidelines_ltcf_0.pdf` (CMS Rev. 232, 07-23-25; source-lock hash verified).

## Summary

- Appendix PP tag-page rows checked: 94.
- Appendix PP page-map discrepancies: 0.
- Records with a `connecticut_overlay` field: 60; empty overlays: 49.
- Authority IDs referenced in JSON: 74; absent from `authority_index.json`: 0.
- Tracked files with UTF-8 BOM: 6.
- Root and `data/keyword_map.json` copies: DIFFERENT.

## Appendix PP tag-page map vs PDF

| Tag | Mapped page | PDF tag-header page | Status | Result |
|---|---:|---:|---|---|
| F550 | 6 | 6 | confirmed | match |
| F552 | 14 | 14 | confirmed | match |
| F553 | 15 | — | confirmed | no standalone tag header; documented shared/continuation section |
| F554 | 17 | 17 | confirmed | match |
| F555 | 19 | 19 | confirmed | match |
| F556 | 20 | 20 | reserved | match |
| F557 | 20 | 20 | confirmed | match |
| F558 | 22 | 22 | confirmed | match |
| F559 | 23 | 23 | confirmed | match |
| F560 | 24 | 24 | confirmed | match |
| F561 | 26 | 26 | confirmed | match |
| F562 | 28 | 28 | confirmed | match |
| F563 | 29 | 29 | confirmed | match |
| F564 | 32 | 32 | confirmed | match |
| F565 | 33 | 33 | confirmed | match |
| F566 | 35 | 35 | confirmed | match |
| F567 | 36 | 36 | confirmed | match |
| F568 | 39 | 39 | confirmed | match |
| F569 | 40 | 40 | confirmed | match |
| F570 | 40 | 40 | confirmed | match |
| F572 | 44 | 44 | confirmed | match |
| F573 | 45 | 45 | confirmed | match |
| F576 | 49 | 49 | confirmed | match |
| F578 | 51 | 51 | confirmed | match |
| F580 | 56 | 56 | confirmed | match |
| F583 | 61 | 61 | confirmed | match |
| F584 | 64 | 64 | confirmed | match |
| F585 | 68 | 68 | confirmed | match |
| F586 | 71 | 71 | confirmed | match |
| F600 | 71 | 71 | confirmed | match |
| F602 | 97 | 97 | confirmed | match |
| F603 | 106 | 106 | confirmed | match |
| F605 | 130 | 130 | confirmed | match |
| F607 | 151 | 151 | confirmed | match |
| F609 | 162 | 162 | confirmed | match |
| F610 | 184 | 184 | confirmed | match |
| F620 | 186 | 186 | confirmed | match |
| F621 | 193 | 193 | confirmed | match |
| F627 | 197 | 197 | confirmed | match |
| F628 | 219 | 219 | confirmed | match |
| F656 | 264 | 264 | confirmed | match |
| F675 | 284 | 284 | confirmed | match |
| F676 | 290 | 290 | confirmed | match |
| F677 | 290 | 290 | confirmed | match |
| F679 | 299 | 299 | confirmed | match |
| F680 | 303 | 303 | confirmed | match |
| F684 | 305 | 305 | confirmed | match |
| F686 | 320 | 320 | confirmed | match |
| F688 | 345 | 345 | confirmed | match |
| F689 | 350 | 350 | confirmed | match |
| F690 | 375 | 375 | confirmed | match |
| F691 | 396 | 396 | confirmed | match |
| F692 | 397 | 397 | confirmed | match |
| F693 | 410 | 410 | confirmed | match |
| F694 | 419 | 419 | confirmed | match |
| F695 | 424 | 424 | confirmed | match |
| F700 | 478 | 478 | confirmed | match |
| F725 | 510 | 510 | confirmed | match |
| F726 | 522 | 522 | confirmed | match |
| F740 | 548 | 548 | confirmed | match |
| F741 | 558 | 558 | confirmed | match |
| F742 | 567 | 567 | confirmed | match |
| F743 | 575 | 575 | confirmed | match |
| F744 | 580 | 580 | confirmed | match |
| F745 | 585 | 585 | confirmed | match |
| F755 | 587 | 587 | confirmed | match |
| F756 | 603 | 603 | confirmed | match |
| F757 | 616 | 616 | confirmed | match |
| F758 | — | 627 | deleted | deleted/redirect; no current page anchor |
| F759 | 627 | 627 | confirmed | match |
| F760 | 627 | 627 | confirmed | match |
| F761 | 639 | 639 | confirmed | match |
| F800 | 660 | 660 | confirmed | match |
| F801 | 660 | — | confirmed | no standalone tag header; documented shared/continuation section |
| F802 | 663 | 663 | confirmed | match |
| F803 | 665 | 665 | confirmed | match |
| F804 | 667 | 667 | confirmed | match |
| F805 | 669 | 669 | confirmed | match |
| F806 | 669 | 669 | confirmed | match |
| F807 | 670 | 670 | confirmed | match |
| F808 | 672 | 672 | confirmed | match |
| F809 | 673 | 673 | confirmed | match |
| F810 | 675 | 675 | confirmed | match |
| F811 | 675 | 675 | confirmed | match |
| F812 | 683 | 683 | confirmed | match |
| F813 | 706 | 706 | confirmed | match |
| F880 | 809 | 809 | confirmed | match |
| F920 | 900 | 900 | confirmed | match |
| F921 | 902 | 902 | confirmed | match |
| F922 | 902 | 902 | confirmed | match |
| F923 | 902 | 902 | confirmed | match |
| F924 | 902 | 902 | confirmed | match |
| F925 | 903 | 903 | confirmed | match |
| F926 | 903 | 903 | confirmed | match |

### F554 verification

PDF p.17 exact tag heading: `F554`; PDF p.18 regulation: `§483.10(c)(7) The right to self-administer medications if the interdisciplinary team, as  defined by §483.21(b)(2)(ii), has determined that this practice is clinically appropriate.    GUIDANCE §483.10(c)(7)  If a resident requests to self-administer medication(s), it is th`; PDF p.19 investigative reference: `ored? 
 
If the interdisciplinary team was not involved in determining whether the self-administration of 
medications was clinically appropriate, cite here at F554. If other concerns related to care 
planning are identified, see guidance at §483.21, Comprehensive Person-Centered Care 
Planning. 
 
F555 
(Rev. 173, Issued: 11-22-17, Effec`.

Finding: the exact tag heading is `F554` on PDF page 17, cited again in investigative guidance on page 19. The related §483.10(c)(7) regulation begins on page 18. The exact code is stored in `heading_exact`; the descriptive name is separate. The former page-map description ('Continuation of Planning/Care Information Rights') was inaccurate and has been corrected.

## NORS codes with Connecticut overlay

- `A01` in `crosswalk_catalog.json`: populated.
- `A02` in `crosswalk_catalog.json`: populated.
- `A03` in `crosswalk_catalog.json`: EMPTY.
- `A04` in `crosswalk_catalog.json`: EMPTY.
- `A05` in `crosswalk_catalog.json`: EMPTY.
- `B01` in `crosswalk_catalog.json`: populated.
- `B02` in `crosswalk_catalog.json`: EMPTY.
- `B03` in `crosswalk_catalog.json`: populated.
- `C01` in `crosswalk_catalog.json`: populated.
- `C02` in `crosswalk_catalog.json`: EMPTY.
- `C03` in `crosswalk_catalog.json`: populated.
- `C04` in `crosswalk_catalog.json`: EMPTY.
- `D01` in `crosswalk_catalog.json`: EMPTY.
- `D02` in `crosswalk_catalog.json`: EMPTY.
- `D03` in `crosswalk_catalog.json`: populated.
- `D04` in `crosswalk_catalog.json`: EMPTY.
- `D05` in `crosswalk_catalog.json`: populated.
- `D06` in `crosswalk_catalog.json`: populated.
- `D07` in `crosswalk_catalog.json`: EMPTY.
- `D08` in `crosswalk_catalog.json`: EMPTY.
- `D09` in `crosswalk_catalog.json`: EMPTY.
- `E01` in `crosswalk_catalog.json`: EMPTY.
- `E02` in `crosswalk_catalog.json`: EMPTY.
- `F01` in `crosswalk_catalog.json`: EMPTY.
- `F02` in `crosswalk_catalog.json`: EMPTY.
- `F03` in `crosswalk_catalog.json`: EMPTY.
- `F04` in `crosswalk_catalog.json`: EMPTY.
- `F05` in `crosswalk_catalog.json`: EMPTY.
- `F06` in `crosswalk_catalog.json`: EMPTY.
- `F07` in `crosswalk_catalog.json`: EMPTY.
- `F08` in `crosswalk_catalog.json`: EMPTY.
- `F09` in `crosswalk_catalog.json`: EMPTY.
- `F10` in `crosswalk_catalog.json`: EMPTY.
- `F11` in `crosswalk_catalog.json`: EMPTY.
- `F12` in `crosswalk_catalog.json`: EMPTY.
- `F13` in `crosswalk_catalog.json`: EMPTY.
- `G01` in `crosswalk_catalog.json`: EMPTY.
- `G02` in `crosswalk_catalog.json`: EMPTY.
- `G03` in `crosswalk_catalog.json`: EMPTY.
- `G04` in `crosswalk_catalog.json`: EMPTY.
- `H01` in `crosswalk_catalog.json`: EMPTY.
- `H02` in `crosswalk_catalog.json`: EMPTY.
- `H03` in `crosswalk_catalog.json`: EMPTY.
- `I01` in `crosswalk_catalog.json`: EMPTY.
- `I02` in `crosswalk_catalog.json`: EMPTY.
- `I03` in `crosswalk_catalog.json`: EMPTY.
- `I04` in `crosswalk_catalog.json`: EMPTY.
- `I05` in `crosswalk_catalog.json`: EMPTY.
- `J01` in `crosswalk_catalog.json`: populated.
- `J02` in `crosswalk_catalog.json`: EMPTY.
- `J03` in `crosswalk_catalog.json`: populated.
- `K01` in `crosswalk_catalog.json`: EMPTY.
- `K02` in `crosswalk_catalog.json`: EMPTY.
- `K03` in `crosswalk_catalog.json`: EMPTY.
- `K04` in `crosswalk_catalog.json`: EMPTY.
- `K05` in `crosswalk_catalog.json`: EMPTY.
- `K06` in `crosswalk_catalog.json`: EMPTY.
- `L01` in `crosswalk_catalog.json`: EMPTY.
- `L02` in `crosswalk_catalog.json`: EMPTY.
- `L03` in `crosswalk_catalog.json`: EMPTY.
- Empty overlay codes (49): `A03`, `A04`, `A05`, `B02`, `C02`, `C04`, `D01`, `D02`, `D04`, `D07`, `D08`, `D09`, `E01`, `E02`, `F01`, `F02`, `F03`, `F04`, `F05`, `F06`, `F07`, `F08`, `F09`, `F10`, `F11`, `F12`, `F13`, `G01`, `G02`, `G03`, `G04`, `H01`, `H02`, `H03`, `I01`, `I02`, `I03`, `I04`, `I05`, `J02`, `K01`, `K02`, `K03`, `K04`, `K05`, `K06`, `L01`, `L02`, `L03`.

## Authority references absent from authority index

- None.

## UTF-8 BOM files

- `authority_index.json`
- `crosswalk_catalog.json`
- `keyword_map.json`
- `nors_hierarchy.json`
- `retrieval_rules.json`
- `tools/testing/nursing-home-long-history-preview.html`

## Root vs data keyword map

- Root SHA-256: `cf9703b44b49bad454cde0ef61714361586c8194870e8fbbe47bfff9a25cf03d`.
- `data/keyword_map.json` SHA-256: `3611f8c818a667493b133a262940eae79818a8a5616d4e370c9201ad1989d2d4`.
- Result: **DIFFERENT**. Per `AGENTS.md`, `/data` remains the source of truth; no duplicate was edited in this audit.

## Corrections made for Step 1

- Changed the F554 `heading_exact` value to the exact tag string `F554`; kept the descriptive title separate. The regulation begins on PDF page 18 and investigative text cites F554 on page 19.
- Moved F554 from the general care-participation group to a dedicated medication self-administration group.
- Corrected the F556 reserved-tag page anchor from 19 to 20, as confirmed by its standalone PDF header. Regenerated the affected `ct_inspections.json` groups, page lookup and tagref from the corrected source maps.

## Scope notes

- The audit reads committed JSON and, when supplied, the ignored source PDF. It never modifies source or data files; `--write-report` only writes the findings Markdown.
- PDF extraction uses optional `pypdf`; if unavailable in CI or if ignored sources are absent, the report marks source comparison as not re-verified rather than installing anything.
