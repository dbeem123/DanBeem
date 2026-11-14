# Project decisions recorded in repository documents

This file summarizes only decisions or current statuses documented in the repository. Drafts are labeled as drafts; no new approval is implied here.

## 2026-11-13 — Approved §483.10 and §483.12 section prior

Daniel approved the App-guidance section prior on 2026-11-13. The recorded categories are §483.10: B, C, D, E, F, G, H, I, J; and §483.12: A, B, D, E, F, J. This is an App context filter and `controls_coding` is false. Source: `nors_ftag_review_batch_1_report.md` and `data/nors_section_prior.json`.

## 2026-11-13 — §483.15 category C map remains a draft

The §483.15 section-map entry contains category C only, is marked `draft`, and has `controls_coding: false`. The batch 2 report recommends not adding D02's category D based on one weak title-only F660 association. This map is not described as Daniel-approved. Source: `nors_ftag_review_batch_2_report_20261113.md` and `data/nors_section_prior_483_15_draft.json`.

## 2026-11-13 — Approved batch 4–6 category maps for App guidance

Daniel approved the proposed context-filter maps for batches 4–6 on 2026-11-13. Batch 4 maps §483.24 to F/G and §483.25 to F; batch 5 maps §§483.30, .35, .40 and .45 to F; batch 6 maps §§483.70, .71, .75 and .85 to J, §483.80 to F/J, and §483.90 to I. These maps remain non-coding guidance (`controls_coding: false`). Source: `data/nors_section_prior_batch_4_draft.json`, `data/nors_section_prior_batch_5_draft.json`, and `data/nors_section_prior_batch_6_draft.json`, approved by Daniel in chat on 2026-11-13.

Daniel also approved the batch 4–6 proposed triage packages as review materials on 2026-11-13. The per-row `check` and `needs_claude` flags remain outstanding, and none of those proposed links were imported. Source: `docs/nors_ftag_review_batch_4_report_20261113.md`, `docs/nors_ftag_review_batch_5_report_20261113.md`, and `docs/nors_ftag_review_batch_6_report_20261113.md`.

## 2026-11-13 — Context links are not coding decisions

Batch 1 explicitly says each candidate is a draft context link, not a coding decision. Reviewed links are informational context; the crosswalk does not select the complaint code for a case. Source: `nors_ftag_review_batch_1_report.md` and `nors_ftag_review_batch_2_report_20261113.md`.

## 2026-11-13 — Keep quoted source text exact

The review records preserve source excerpts verbatim with locators. The batch 3 report states that the extracted Table 2 text is kept verbatim, including source-extraction artifacts; the UI review report states that all 139 distinction quotes were checked against cited PDF pages. Do not silently normalize or paraphrase text presented as a source quotation. Source: `nors_ftag_review_batch_3_report_20261113.md` and `nors_step3b_ui_review_20261113.md`.
