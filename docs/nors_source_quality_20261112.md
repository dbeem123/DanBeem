# Revision 4 source extraction quality — 2026-11-12

Tool: `pypdf 6.10.2` for PDFs; Python standard-library `HTMLParser` for HTML and XML extraction from DOCX.
No OCR, package installation, or source-file modification was performed. Pages with fewer than 40 non-whitespace extracted characters are flagged below for visual review; this threshold can include designed slide pages as well as scanned/poor-text pages.

- Locked files checked: 105.
- PDFs/pages: 83/4364.
- Low-text PDF pages: 208.
- 45 CFR Part 1324 Subpart A section identifiers: PDF 23, HTML 19, common 17; PDF-only ['§\n1324.11(e)(3)', '§\n1324.13', '§\n1324.13(c)(2)', '§\n1324.13(e)', '§\n1324.13(h)', '§\n1324.19(b)(5)'], HTML-only ['§ 1324.13(c)(2)', '§ 1324.13(e)'].
- Section identifiers agree. This is a structural comparison; formatting and HTML page headers differ, so it does not assert byte-for-byte identity.

## Low-text pages to inspect

| File | PDF page | Extracted characters |
|---|---:|---:|
| `2019_LTCOP_Training_Standards.pdf` | 1 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 2 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 3 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 4 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 5 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 6 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 7 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 8 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 9 | 0 |
| `2019_LTCOP_Training_Standards.pdf` | 10 | 0 |
| `module-1-1.pdf` | 2 | 35 |
| `module-1-1.pdf` | 4 | 0 |
| `module-1-1.pdf` | 8 | 31 |
| `module-1-1.pdf` | 9 | 13 |
| `module-1-1.pdf` | 12 | 37 |
| `module-1-1.pdf` | 15 | 38 |
| `module-1-1.pdf` | 24 | 37 |
| `module-1-1.pdf` | 28 | 21 |
| `module-1-1.pdf` | 35 | 0 |
| `module-1-1.pdf` | 57 | 29 |
| `module-1-1.pdf` | 66 | 31 |
| `module-1-1.pdf` | 73 | 34 |
| `module-1-1.pdf` | 74 | 0 |
| `module-1-1.pdf` | 75 | 0 |
| `module-1-1.pdf` | 80 | 40 |
| `module-1-1.pdf` | 85 | 32 |
| `module-1-1.pdf` | 86 | 32 |
| `module-1-1.pdf` | 93 | 20 |
| `module-1-1.pdf` | 100 | 10 |
| `module-1-trainee-manual.pdf` | 3 | 102 |
| `module-1-trainee-manual.pdf` | 33 | 101 |
| `module-1-trainee-manual.pdf` | 46 | 92 |
| `module-1-trainer-guide.pdf` | 4 | 97 |
| `module-1-trainer-guide.pdf` | 40 | 100 |
| `module-1-trainer-guide.pdf` | 56 | 92 |
| `module-10-trainee-manual.pdf` | 26 | 50 |
| `module-10-trainee-manual.pdf` | 27 | 46 |
| `module-10-trainer-guide.pdf` | 31 | 46 |
| `module-10.pdf` | 2 | 35 |
| `module-10.pdf` | 4 | 0 |
| `module-10.pdf` | 10 | 23 |
| `module-10.pdf` | 13 | 12 |
| `module-10.pdf` | 19 | 33 |
| `module-10.pdf` | 20 | 47 |
| `module-10.pdf` | 25 | 35 |
| `module-10.pdf` | 26 | 32 |
| `module-10.pdf` | 32 | 11 |
| `module-10.pdf` | 52 | 12 |
| `module-10.pdf` | 53 | 20 |
| `module-10.pdf` | 55 | 10 |
| `module-2.pdf` | 2 | 35 |
| `module-2.pdf` | 4 | 0 |
| `module-2.pdf` | 17 | 41 |
| `module-2.pdf` | 28 | 33 |
| `module-2.pdf` | 34 | 18 |
| `module-2.pdf` | 38 | 35 |
| `module-2.pdf` | 47 | 39 |
| `module-2.pdf` | 53 | 15 |
| `module-2.pdf` | 69 | 20 |
| `module-2.pdf` | 73 | 10 |
| `module-3-1.pdf` | 2 | 35 |
| `module-3-1.pdf` | 4 | 0 |
| `module-3-1.pdf` | 7 | 30 |
| `module-3-1.pdf` | 13 | 42 |
| `module-3-1.pdf` | 14 | 40 |
| `module-3-1.pdf` | 16 | 25 |
| `module-3-1.pdf` | 29 | 22 |
| `module-3-1.pdf` | 32 | 21 |
| `module-3-1.pdf` | 38 | 39 |
| `module-3-1.pdf` | 39 | 46 |
| `module-3-1.pdf` | 48 | 35 |
| `module-3-1.pdf` | 50 | 33 |
| `module-3-1.pdf` | 61 | 42 |
| `module-3-1.pdf` | 63 | 47 |
| `module-3-1.pdf` | 66 | 33 |
| `module-3-1.pdf` | 68 | 20 |
| `module-3-1.pdf` | 71 | 10 |
| `module-3-trainee-manual.pdf` | 3 | 95 |
| `module-3-trainee-manual.pdf` | 9 | 97 |
| `module-3-trainee-manual.pdf` | 16 | 50 |
| `module-3-trainee-manual.pdf` | 27 | 93 |
| `module-3-trainee-manual.pdf` | 43 | 86 |
| `module-3-trainer-guide.pdf` | 4 | 95 |
| `module-3-trainer-guide.pdf` | 11 | 98 |
| `module-3-trainer-guide.pdf` | 19 | 52 |
| `module-3-trainer-guide.pdf` | 30 | 95 |
| `module-3-trainer-guide.pdf` | 49 | 84 |
| `module-4-ppt.pdf` | 2 | 35 |
| `module-4-ppt.pdf` | 4 | 0 |
| `module-4-ppt.pdf` | 7 | 24 |
| `module-4-ppt.pdf` | 19 | 42 |
| `module-4-ppt.pdf` | 56 | 10 |
| `module-4-ppt.pdf` | 60 | 38 |
| `module-4-ppt.pdf` | 65 | 38 |
| `module-4-ppt.pdf` | 73 | 33 |
| `module-4-ppt.pdf` | 74 | 21 |
| `module-4-ppt.pdf` | 76 | 25 |
| `module-4-ppt.pdf` | 77 | 20 |
| `module-4-ppt.pdf` | 80 | 10 |
| `module-4-trainee-manual.pdf` | 3 | 101 |
| `module-4-trainee-manual.pdf` | 8 | 56 |
| `module-4-trainee-manual.pdf` | 46 | 44 |
| `module-4-trainer-guide.pdf` | 5 | 101 |
| `module-4-trainer-guide.pdf` | 11 | 57 |
| `module-4-trainer-guide.pdf` | 54 | 44 |
| `module-5-1.pdf` | 2 | 35 |
| `module-5-1.pdf` | 4 | 0 |
| `module-5-1.pdf` | 7 | 16 |
| `module-5-1.pdf` | 20 | 41 |
| `module-5-1.pdf` | 23 | 10 |
| `module-5-1.pdf` | 36 | 10 |
| `module-5-1.pdf` | 37 | 35 |
| `module-5-1.pdf` | 38 | 39 |
| `module-5-1.pdf` | 39 | 43 |
| `module-5-1.pdf` | 41 | 18 |
| `module-5-1.pdf` | 50 | 19 |
| `module-5-1.pdf` | 53 | 10 |
| `module-5-1.pdf` | 58 | 31 |
| `module-5-1.pdf` | 62 | 20 |
| `module-5-1.pdf` | 66 | 10 |
| `module-5-trainee-manual.pdf` | 3 | 102 |
| `module-5-trainee-manual.pdf` | 8 | 40 |
| `module-5-trainee-manual.pdf` | 32 | 90 |
| `module-5-trainer-guide.pdf` | 5 | 103 |
| `module-5-trainer-guide.pdf` | 11 | 41 |
| `module-5-trainer-guide.pdf` | 42 | 90 |
| `module-6-1.pdf` | 2 | 35 |
| `module-6-1.pdf` | 4 | 0 |
| `module-6-1.pdf` | 7 | 37 |
| `module-6-1.pdf` | 11 | 25 |
| `module-6-1.pdf` | 15 | 28 |
| `module-6-1.pdf` | 19 | 16 |
| `module-6-1.pdf` | 21 | 40 |
| `module-6-1.pdf` | 22 | 10 |
| `module-6-trainee-manual.pdf` | 3 | 70 |
| `module-6-trainee-manual.pdf` | 9 | 51 |
| `module-6-trainee-manual.pdf` | 16 | 44 |
| `module-6-trainer-guide.pdf` | 4 | 69 |
| `module-6-trainer-guide.pdf` | 11 | 52 |
| `module-6-trainer-guide.pdf` | 20 | 44 |
| `module-7-1.pdf` | 2 | 35 |
| `module-7-1.pdf` | 4 | 0 |
| `module-7-1.pdf` | 17 | 26 |
| `module-7-1.pdf` | 24 | 45 |
| `module-7-1.pdf` | 25 | 10 |
| `module-7-1.pdf` | 26 | 34 |
| `module-7-1.pdf` | 39 | 36 |
| `module-7-1.pdf` | 50 | 41 |
| `module-7-1.pdf` | 51 | 22 |
| `module-7-1.pdf` | 53 | 27 |
| `module-7-1.pdf` | 54 | 0 |
| `module-7-1.pdf` | 55 | 12 |
| `module-7-1.pdf` | 56 | 12 |
| `module-7-1.pdf` | 59 | 21 |
| `module-7-1.pdf` | 61 | 10 |
| `module-7-trainee-manual.pdf` | 3 | 70 |
| `module-7-trainee-manual.pdf` | 35 | 47 |
| `module-7-trainee-manual.pdf` | 38 | 51 |
| `module-7-trainee-manual.pdf` | 41 | 44 |
| `module-7-trainer-guide.pdf` | 4 | 68 |
| `module-7-trainer-guide.pdf` | 40 | 45 |
| `module-7-trainer-guide.pdf` | 43 | 49 |
| `module-7-trainer-guide.pdf` | 46 | 42 |
| `module-8-slides.pdf` | 2 | 35 |
| `module-8-slides.pdf` | 4 | 0 |
| `module-8-slides.pdf` | 7 | 31 |
| `module-8-slides.pdf` | 12 | 8 |
| `module-8-slides.pdf` | 22 | 40 |
| `module-8-slides.pdf` | 35 | 27 |
| `module-8-slides.pdf` | 40 | 20 |
| `module-8-slides.pdf` | 42 | 10 |
| `module-8-trainee-manual.pdf` | 3 | 64 |
| `module-8-trainee-manual.pdf` | 8 | 55 |
| `module-8-trainee-manual.pdf` | 28 | 47 |
| `module-8-trainer-guide.pdf` | 4 | 67 |
| `module-8-trainer-guide.pdf` | 10 | 57 |
| `module-8-trainer-guide.pdf` | 33 | 49 |
| `module-9-slides.pdf` | 2 | 35 |
| `module-9-slides.pdf` | 4 | 0 |
| `module-9-slides.pdf` | 7 | 32 |
| `module-9-slides.pdf` | 24 | 8 |
| `module-9-slides.pdf` | 27 | 5 |
| `module-9-slides.pdf` | 29 | 6 |
| `module-9-slides.pdf` | 36 | 32 |
| `module-9-slides.pdf` | 37 | 23 |
| `module-9-slides.pdf` | 38 | 27 |
| `module-9-slides.pdf` | 39 | 17 |
| `module-9-slides.pdf` | 40 | 38 |
| `module-9-slides.pdf` | 42 | 9 |
| `module-9-slides.pdf` | 43 | 26 |
| `module-9-slides.pdf` | 48 | 41 |
| `module-9-slides.pdf` | 52 | 42 |
| `module-9-slides.pdf` | 56 | 44 |
| `module-9-slides.pdf` | 58 | 44 |
| `module-9-slides.pdf` | 60 | 44 |
| `module-9-slides.pdf` | 62 | 43 |
| `module-9-slides.pdf` | 63 | 20 |
| `module-9-slides.pdf` | 69 | 10 |
| `module-9-trainee-manual.pdf` | 3 | 65 |
| `module-9-trainee-manual.pdf` | 8 | 55 |
| `module-9-trainee-manual.pdf` | 33 | 44 |
| `module-9-trainer-guide.pdf` | 5 | 59 |
| `module-9-trainer-guide.pdf` | 11 | 55 |
| `module-9-trainer-guide.pdf` | 40 | 42 |
| `nors-training-part-I-basic-principles.pdf` | 2 | 24 |
| `som107ap_pp_guidelines_ltcf_0.pdf` | 923 | 47 |
| `som107c05_0.pdf` | 110 | 112 |
| `som107c06.pdf` | 85 | 18 |

## Text extraction coverage

| File | Method/status | Extracted characters |
|---|---|---:|
| `11933_som107c01.pdf` | PDF extracted | 49136 |
| `11936_som107c04.pdf` | PDF extracted | 337435 |
| `11940_som107c08.pdf` | PDF extracted | 14477 |
| `17b-411.pdf` | PDF extracted | 45536 |
| `19-13-d8t.pdf` | PDF extracted | 89081 |
| `19-13-d8v.pdf` | PDF extracted | 14162 |
| `2019_LTCOP_Training_Standards.pdf` | PDF extracted | 0 |
| `2026PA-00015-R00SB-00005-PA.pdf` | PDF extracted | 119468 |
| `42 CFR Part 483 Subpart B (up to date as of 11-10-2026).pdf` | PDF extracted | 202555 |
| `45 CFR Part 1324 (up to date as of 11-09-2026).pdf` | PDF extracted | 89019 |
| `45 CFR Part 1324 Subpart A (in effect on 11-09-2026).pdf` | PDF extracted | 64706 |
| `AI Board and Governance.pdf` | PDF extracted | 2930 |
| `AI Inventory.pdf` | PDF extracted | 9745 |
| `Case_Notes_Checklist.pdf` | PDF extracted | 1950 |
| `Chapter 319l - Department of Aging and Disability Services.html` | HTML extracted | 305797 |
| `Chapter 368v - Health Care Institutions.html` | HTML extracted | 821301 |
| `Considering AI for Your Agency_ Start Here_.pdf` | PDF extracted | 2910 |
| `CT Responsible AI Policy Framework Final 02012024.pdf` | PDF extracted | 42653 |
| `curriculum-overview.pdf` | PDF extracted | 11534 |
| `eCFR __ 45 CFR Part 1324 Subpart A -- State Long-Term Care Ombudsman Program.html` | HTML extracted | 95559 |
| `glossary-of-key-words.pdf` | PDF extracted | 21469 |
| `I-A-During-Visits-TA.pdf` | PDF extracted | 5482 |
| `Is_It_a_Complaint_or_Information__Assistance.pdf` | PDF extracted | 3350 |
| `module-1-1.pdf` | PDF extracted | 22228 |
| `module-1-trainee-manual.docx` | DOCX XML extracted | 78242 |
| `module-1-trainee-manual.pdf` | PDF extracted | 70037 |
| `module-1-trainer-guide.docx` | DOCX XML extracted | 99638 |
| `module-1-trainer-guide.pdf` | PDF extracted | 87263 |
| `module-10-trainee-manual.docx` | DOCX XML extracted | 38851 |
| `module-10-trainee-manual.pdf` | PDF extracted | 34187 |
| `module-10-trainer-guide.docx` | DOCX XML extracted | 48372 |
| `module-10-trainer-guide.pdf` | PDF extracted | 41533 |
| `module-10.pdf` | PDF extracted | 9273 |
| `module-2-trainee-manual.docx` | DOCX XML extracted | 72475 |
| `module-2-trainee-manual.pdf` | PDF extracted | 58363 |
| `module-2-trainer-guide.docx` | DOCX XML extracted | 89621 |
| `module-2-trainer-guide.pdf` | PDF extracted | 72819 |
| `module-2.pdf` | PDF extracted | 15426 |
| `module-3-1.pdf` | PDF extracted | 11951 |
| `module-3-trainee-manual.docx` | DOCX XML extracted | 65547 |
| `module-3-trainee-manual.pdf` | PDF extracted | 59636 |
| `module-3-trainer-guide.docx` | DOCX XML extracted | 83406 |
| `module-3-trainer-guide.pdf` | PDF extracted | 74417 |
| `module-4-ppt.pdf` | PDF extracted | 15292 |
| `module-4-trainee-manual.docx` | DOCX XML extracted | 82621 |
| `module-4-trainee-manual.pdf` | PDF extracted | 73000 |
| `module-4-trainer-guide.pdf` | PDF extracted | 86530 |
| `module-5-1.pdf` | PDF extracted | 10879 |
| `module-5-trainee-manual.pdf` | PDF extracted | 43147 |
| `module-5-trainee-manual.word_.docx` | DOCX XML extracted | 48000 |
| `module-5-trainer-guide.pdf` | PDF extracted | 60793 |
| `module-5-trainer-guide.word_.docx` | DOCX XML extracted | 69183 |
| `module-6-1.pdf` | PDF extracted | 3965 |
| `module-6-trainee-manual.docx` | DOCX XML extracted | 19238 |
| `module-6-trainee-manual.pdf` | PDF extracted | 17719 |
| `module-6-trainer-guide.docx` | DOCX XML extracted | 26461 |
| `module-6-trainer-guide.pdf` | PDF extracted | 23620 |
| `module-7-1.pdf` | PDF extracted | 11027 |
| `module-7-trainee-manual.docx` | DOCX XML extracted | 57671 |
| `module-7-trainee-manual.pdf` | PDF extracted | 53278 |
| `module-7-trainer-guide.docx` | DOCX XML extracted | 72672 |
| `module-7-trainer-guide.pdf` | PDF extracted | 64862 |
| `module-8-slides.pdf` | PDF extracted | 7349 |
| `module-8-trainee-manual.pdf` | PDF extracted | 36071 |
| `module-8-trainer-guide.pdf` | PDF extracted | 46122 |
| `module-9-slides.pdf` | PDF extracted | 11602 |
| `module-9-trainee-manual.docx` | DOCX XML extracted | 58565 |
| `module-9-trainee-manual.pdf` | PDF extracted | 54904 |
| `module-9-trainer-guide.docx` | DOCX XML extracted | 71512 |
| `module-9-trainer-guide.pdf` | PDF extracted | 64901 |
| `nors-codes-and-definitions.pdf` | PDF extracted | 24172 |
| `NORS-Data-Management-Guide.pdf` | PDF extracted | 11664 |
| `nors-faqs.pdf` | PDF extracted | 28352 |
| `nors-training-part-I-basic-principles.pdf` | PDF extracted | 6696 |
| `nors-training-part-I-quiz-answers.pdf` | PDF extracted | 11705 |
| `nors-training-part-I-quiz.pdf` | PDF extracted | 7340 |
| `nors-training-part-II-basic-principles.pdf` | PDF extracted | 2500 |
| `nors-training-part-II-beyond-basics-quiz-answers.pdf` | PDF extracted | 7882 |
| `nors-training-part-II-beyond-basics-quiz.pdf` | PDF extracted | 5453 |
| `nors-training-part-II-quiz-answers.pdf` | PDF extracted | 13177 |
| `nors-training-part-II-quiz.pdf` | PDF extracted | 12167 |
| `nors-training-part-III-basic-principles.pdf` | PDF extracted | 4875 |
| `nors-training-part-III-quiz-answers-verification-disposition-referral-and-closing.pdf` | PDF extracted | 16755 |
| `nors-training-part-III-quiz-verification-disposition-referral-and-closing.pdf` | PDF extracted | 13493 |
| `nors-training-part-IV-basic-principles.pdf` | PDF extracted | 6167 |
| `nors-training-part-IV-quiz-answers.pdf` | PDF extracted | 10690 |
| `nors-training-part-IV-quiz.pdf` | PDF extracted | 6535 |
| `nors-updated-complaint-codes-list.pdf` | PDF extracted | 3073 |
| `NORS_Table_1_Case_Level_2024_Renewal-noex (2).pdf` | PDF extracted | 10324 |
| `NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf` | PDF extracted | 24059 |
| `NORS_Table_3_Program_Information_2024_Renewal-noex.pdf` | PDF extracted | 34858 |
| `NORS_Tables_Revisions_Chart.pdf` | PDF extracted | 4661 |
| `Ombudsman_Visits_Decision_Tree.pdf` | PDF extracted | 1412 |
| `Regulations and Statutes Main Page.html` | HTML extracted | 25363 |
| `revisions-chart.pdf` | PDF extracted | 8637 |
| `som107_appendicestoc.pdf` | PDF extracted | 1684 |
| `som107ap_pp_guidelines_ltcf_0.pdf` | PDF extracted | 2006943 |
| `som107c02.pdf` | PDF extracted | 973560 |
| `som107c03.pdf` | PDF extracted | 278734 |
| `som107c05_0.pdf` | PDF extracted | 219586 |
| `som107c06.pdf` | PDF extracted | 431937 |
| `som107c07.pdf` | PDF extracted | 418881 |
| `som107c09exhibitstoc.pdf` | PDF extracted | 28993 |
| `som107c10.pdf` | PDF extracted | 83438 |
| `Your Rights as a Resident of a Long Term Care Facility.html` | HTML extracted | 16516 |
