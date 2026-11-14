# Project decisions recorded in repository documents

This file summarizes only decisions or current statuses documented in the repository. Drafts are labeled as drafts; no new approval is implied here.

## 2026-11-13 — Approved §483.10 and §483.12 section prior

Daniel approved the App-guidance section prior on 2026-11-13. The recorded categories are §483.10: B, C, D, E, F, G, H, I, J; and §483.12: A, B, D, E, F, J. This is an App context filter and `controls_coding` is false. Source: `nors_ftag_review_batch_1_report.md` and `data/nors_section_prior.json`.

## 2026-11-13 — §483.15 category C map remains a draft

The §483.15 section-map entry contains category C only, is marked `draft`, and has `controls_coding: false`. The batch 2 report recommends not adding D02's category D based on one weak title-only F660 association. This map is not described as Daniel-approved. Source: `nors_ftag_review_batch_2_report_20261113.md` and `data/nors_section_prior_483_15_draft.json`.

## 2026-11-13 — Context links are not coding decisions

Batch 1 explicitly says each candidate is a draft context link, not a coding decision. Reviewed links are informational context; the crosswalk does not select the complaint code for a case. Source: `nors_ftag_review_batch_1_report.md` and `nors_ftag_review_batch_2_report_20261113.md`.

## 2026-11-13 — Keep quoted source text exact

The review records preserve source excerpts verbatim with locators. The batch 3 report states that the extracted Table 2 text is kept verbatim, including source-extraction artifacts; the UI review report states that all 139 distinction quotes were checked against cited PDF pages. Do not silently normalize or paraphrase text presented as a source quotation. Source: `nors_ftag_review_batch_3_report_20261113.md` and `nors_step3b_ui_review_20261113.md`.
