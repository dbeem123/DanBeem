# NORS Knowledge Base Research Notes
## Connecticut Long-Term Care Ombudsman — NORS Crosswalk Tool

**Build Date:** 2025-07  
**Batch:** Batch 1 — Codes A01, A02, A03, A04, A05, C03, D01, D03, D04, D05, D06, D07, D09, F02, F03, F04, H01, H02, J03  
**Output File:** `/home/user/workspace/nors_knowledge_base.json`

---

## SOURCES SUCCESSFULLY CONFIRMED (primary sources fetched)

### 42 CFR Part 483 Regulations (via GovInfo XML — authoritative)
| Section | Content | Fetch Status |
|---------|---------|-------------|
| §483.10 | Resident Rights (full text confirmed) | ✅ Confirmed via GovInfo XML |
| §483.12 | Freedom from Abuse, Neglect, Exploitation (full text) | ✅ Confirmed via GovInfo XML |
| §483.15 | Admission, Transfer, and Discharge Rights (full text) | ✅ Confirmed via GovInfo XML |
| §483.21 | Comprehensive Person-Centered Care Planning (full text) | ✅ Confirmed via GovInfo XML |
| §483.35 | Nursing Services/Staffing (full text) | ✅ Confirmed via GovInfo XML |
| §483.45 | Pharmacy Services (full text) | ✅ Confirmed via GovInfo XML |
| §483.60 | Food and Nutrition Services (full text) | ✅ Confirmed via GovInfo XML |

**GovInfo XML URL pattern used:**
`https://www.govinfo.gov/content/pkg/CFR-2023-title42-vol5/xml/CFR-2023-title42-vol5-sec483-[XX].xml`

**Note:** GovInfo XML reflects 2023 edition. Appendix PP Rev. 229 (April 2025) made F-tag renumbering changes (see F-tag changes section below).

---

### Connecticut General Statutes (via Connecticut General Assembly website)
| Section | Content | Fetch Status |
|---------|---------|-------------|
| §19a-550(b)(1)-(30) | Patients' Bill of Rights — full subsection list | ✅ Confirmed via cga.ct.gov |
| §19a-535 | Transfer and Discharge — (b) permissible grounds | ✅ Confirmed via cga.ct.gov (partial) |

**Source URL:** `https://www.cga.ct.gov/current/pub/chap_368v.htm`  
**Publication Date:** 2024-07-01 (current legislative session through July 2024)

#### Key CT §19a-550 subsections confirmed:
- **(b)(1):** All rights of any state resident including association, communication, technology use
- **(b)(4):** Right to choose own physician or APRN, participate in medical treatment planning
- **(b)(6):** Exercise of rights, grievance rights, access to ombudsman — **no reprisal**
- **(b)(7):** Prompt efforts to resolve grievances
- **(b)(9):** Free from mental and physical abuse, corporal punishment, involuntary seclusion
- **(b)(10):** Confidential treatment of personal and medical records
- **(b)(11):** Quality care with reasonable accommodation; treated with consideration, respect, dignity
- **(b)(13)(A):** Right to send/receive mail unopened, make/receive telephone calls privately
- **(b)(14):** Social, religious, and community activities
- **(b)(16):** Privacy for visits by spouse or designee; spousal room sharing
- **(b)(21):** Right to file complaints with DSS and DPH regarding abuse, neglect, misappropriation
- **(b)(22):** Psychopharmacologic drugs only per written plan of care with independent annual review
- **(b)(23):** Transfer/discharge only pursuant to §19a-535, §19a-535a, or §19a-535b
- **(b)(24):** Equal treatment regardless of payment source for transfer, discharge, and services

---

### 45 CFR Part 1324 — LTCO Program (via Cornell LII — authoritative)
| Section | Content | Fetch Status |
|---------|---------|-------------|
| §1324.11 | Establishment of Office of State LTCO (full text) | ✅ Confirmed via law.cornell.edu |
| §1324.13 | Functions and responsibilities of State LTCO (full text) | ✅ Confirmed via law.cornell.edu |
| §1324.19 | Duties of representatives of the Office (full text) | ✅ Confirmed via law.cornell.edu |

**Source URL:** `https://www.law.cornell.edu/cfr/text/45/1324.19`

#### Key 45 CFR 1324.19 provisions used:
- **(a)(1):** Core duty — identify, investigate, resolve complaints that may adversely affect health, safety, welfare, or rights of residents
- **(a)(4):** Represent interests of residents before government agencies; pursue administrative, legal, and other remedies
- **(b)(1):** Explicit inclusion of abuse, neglect, and exploitation complaints; resident-serving orientation
- **(b)(3)(i):** May disclose information to agencies for regulatory, protective services, or law enforcement purposes
- **(b)(6):** May disclose resident-identifying info without consent when resident unable to consent and conditions met
- **(b)(8):** Special procedures when ombudsman personally witnesses abuse/gross neglect/exploitation

---

### CMS Appendix PP State Operations Manual
| Item | Status |
|------|--------|
| F-tag page numbers in PDF | ❌ NOT CONFIRMED — PDF too large for extraction; page numbers set to `null` |
| F-tag existence and section assignments | ✅ Confirmed from secondary sources (ANFP document, HHS transmittal documents, NursingHome411) |
| Rev. 229 (April 2025) F-tag changes | ✅ Confirmed from HHS transmittal document |

**Current PDF URL:** `https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf`  
**Current Revision:** Rev. 232 (Issued: 07-23-25) — most current as of research date

---

## F-TAG CHANGES — APPENDIX PP REVISION 229 (EFFECTIVE APRIL 28, 2025)

**Critical changes that affect this knowledge base:**

| Change | Impact |
|--------|--------|
| F622, F623, F624, F625 **deleted** | Content relocated to F627 and F628 |
| F627 **new/revised** — "Inappropriate Transfers and Discharges" | Now covers §483.15(c)(1)-(2) transfer/discharge grounds — relevant to C03 |
| F628 **new/revised** — "Transfer and Discharge Process" | Now covers §483.15(c)(2)-(8) process requirements — relevant to C03 |
| F758 **deleted** — "Free from Unnecessary Psychotropic Medications" | Content relocated to F605 |
| F605 **revised** — now includes §483.45(e) psychotropic drug requirements | Relevant to F04 |
| F660, F661 **deleted** | Content relocated to F627 and F628 |

**Action Required:** Any references to F622-F626, F758, F660, F661 in older crosswalk documents must be updated to current F-tag numbering.

---

## CONFIRMED vs UNCERTAIN DATA

### CONFIRMED (directly verified from primary sources)
- All 19 NORS code definitions (from ltcombudsman.org NORS Codes and Definitions PDF — pre-loaded)
- All 42 CFR 483.10, 483.12, 483.15, 483.21, 483.35, 483.45, 483.60 subsection text
- CT §19a-550(b)(1)-(30) complete subsection list
- CT §19a-535(b) permissible transfer/discharge grounds (partial text)
- 45 CFR §1324.11, §1324.13, §1324.19 complete text
- F-tag to CFR section assignments (A01→F600/§483.12, etc.)
- F-tag changes from Rev. 229 (April 2025)
- Existence of F601, F602, F607, F800-F802 in Appendix PP

### UNCERTAIN / HUMAN REVIEW REQUIRED
1. **Appendix PP PDF page numbers** — All `appendix_pp_pdf_page_start` values are `null`. Requires manual review of current PDF (Rev. 232) to populate.
2. **CT §19a-535 complete text** — Only (b) paragraph was confirmed; full section has many subsections including specific notice periods, bed-hold requirements, and appeal process details that may differ from or supplement federal requirements. Human reviewer should read the complete section.
3. **CT DPH regulations on staffing ratios** — CGS §19a-521 et seq. and CT DPH regulations likely contain specific nursing home staffing ratios that may be stricter than federal minimums. Not confirmed.
4. **CT DPH definition of "gross neglect"** — CT §19a-550(b)(9) uses "mental and physical abuse" language; federal NORS uses "gross neglect" as separate category. CT DPH regulations may or may not explicitly define gross neglect.
5. **CT mandatory reporting obligations** — CGS §17b-450 and §17b-451 govern mandatory abuse reporting in CT. Not reviewed in this research pass; should be cross-referenced for A01, A02, A03, A04, A05 codes.
6. **F553 regulatory citation** — Pre-loaded data maps F553 to §483.10(b)(4); however, §483.10(c)(2)-(3) may be the more precise current citation for right to participate in care planning. Human reviewer should confirm current F553 citation in live Appendix PP.
7. **F801/F802 exact Appendix PP page numbers** — Confirmed these F-tags exist and map to §483.60(a), but PDF page numbers not confirmed.
8. **Current Rev. 232 changes** — The most recent revision (Rev. 232, July 23, 2025) was not fully reviewed. Changes may affect any of the above tags.

---

## NORS CODE CLASSIFICATION NOTES

### A01-A05 (Abuse/Neglect Codes)
- All map to F600 (§483.12) as primary federal anchor
- A01-A03 also map to CT §19a-550(b)(9)
- A04 maps to CT §19a-550(b)(21) for complaint right; (b)(8) for financial accounting
- A05 (gross neglect) is the most severe category; federal definition controls since CT statute doesn't explicitly define "gross neglect"
- All require 2-hour reporting for serious bodily injury per §483.12(c)(1)

### C03 (Discharge/Eviction)
- Both federal (F627/F628) and CT (§19a-535) apply; CT law may have additional notice/procedural requirements
- Ombudsman receives copy of every discharge notice per §483.15(c)(3)(i) — affirmative monitoring tool
- F627 and F628 are newly consolidated tags as of Rev. 229 (April 2025)

### D-codes (Rights)
- D01: §483.10(d) choice of physician is primary; CT §19a-550(b)(4) extends to APRN choice
- D03: F550 (§483.10(a)(1)) primary; CT §19a-550(b)(11) specific language
- D04: F583 (§483.10(h)) for privacy; F563 for mail; CT §19a-550(b)(10) and (b)(13)(A)
- D05: F585 (§483.10(j)) full grievance process requirements
- D06: §483.10(b)(1)-(2) non-reprisal provisions; CT §19a-550(b)(6)
- D07: F564 (§483.10(f)(4)) detailed visitor rights including non-discrimination
- D09: F561 (§483.10(f)(1)) broadest self-determination right; CT §19a-550(b)(1) extremely broad

### F-codes (Care)
- F02: F558 (§483.10(e)(3)) accommodation; if systemic, consider J03 alongside
- F03: F656 (§483.21(b)) and F553 (§483.10(c)(2)-(3)) dual anchors
- F04: §483.45(f) medication errors; §483.45(d) unnecessary drugs; §483.45(e)/F605 psychotropics; CT §19a-550(b)(22) psychopharmacologic drugs

### H-codes (Dietary)
- H01: Food quality maps to §483.60(c)-(f); F801/F802 are staffing anchors; specific food quality F-tags (F806, F808) not included in pre-loaded mappings — human reviewer should verify
- H02: §483.60(d)(6) hydration; §483.60(g) assistive devices; §483.60(h) paid feeding assistants

### J03 (Staffing)
- F725 (§483.35(a)) and F726 (§483.35(c)) primary federal anchors
- CT DPH staffing regulations should be reviewed
- §483.35(g) requires daily public staffing data posting — actionable investigation tool

---

## SOURCES NOT FETCHED IN THIS PASS (not in pre-loaded data, not required for Batch 1)
- NORS codes B01-B09 (facility characteristics codes)
- NORS codes E01-E08 (environmental codes)
- NORS codes G01-G07 (administrative codes)
- NORS codes K01-K06 and L01-L03 (outside agencies — flagged for do_not_map_catalog per instructions)
- 42 CFR §483.24 (Quality of Life) and §483.25 (Quality of Care) — adjacent to some codes but not in Batch 1
- NORC/LTCO handout resources beyond the NORS Codes and Definitions PDF
- CMS nursing home compare data
- CT DPH nursing home survey regulations

---

## TECHNICAL NOTES
- eCFR.gov requires CAPTCHA for automated access; all CFR text obtained from GovInfo.gov XML or Cornell LII
- GovInfo XML reflects 2023 CFR edition; verify against 2024-2025 amendments where relevant
- Appendix PP PDF (cms.gov) is too large for automated full-text extraction; page numbers require manual lookup
- Cornell LII (law.cornell.edu) confirmed reliable for 45 CFR 1324 text
- CT General Assembly website (cga.ct.gov) confirmed reliable for current CT statute text
