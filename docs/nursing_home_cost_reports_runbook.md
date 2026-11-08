# Nursing home cost reports: runbook

Public page: `/staffing/tools/nursing-home-cost-reports.html`. Facility Explorer section: "Cost reports (DSS)".
Management Companies company view: "Management fees reported to DSS".

## Sources (private copies stay out of git)

| Source | Where the raw files live | Private working copy |
|---|---|---|
| DSS *Annual Report of Long-Term Care Facility* PDFs, cost years 2015-2025 (plus 2023-2024 narrative summaries) | `X:\DanBeem-Data\Cost_Reports\` | `data/testing/cost_reports/work/` (`_text/`, `_ocr_p1/`, `ocr_full/`, `reocr_out/`) |
| CMS Skilled Nursing Facility All Owners, monthly since 2022-09 | `X:\DanBeem-Data\Ownership\Skilled Nursing Facility All Owners\` | `data/testing/cost_reports/all_owners/<YYYY-MM>/` (CT rows only) |
| CMS Skilled Nursing Facility Change of Ownership (cumulative) | `X:\DanBeem-Data\Skilled Nursing Facility Change of Ownership\` | `data/testing/cost_reports/SNF_CHOW_<date>.csv` |
| CMS Care Compare Provider Information (legal business name to CCN) | `X:\DanBeem-Data\Ownership\_ct_extract\` | `data/testing/cost_reports/providerinfo/<release>.csv` |

DSS cost reports and CMS files are public records. The site publishes owner, officer and related-party names,
addresses and amounts as filed (Daniel's decision, 2026-11-06: anything public from CMS or Connecticut is published).

## Pipeline

1. **Text.** `pdftotext -layout` for every PDF into `work/_text/`. Scanned PDFs (no text layer) are OCR'd with
   `tesseract --psm 1` (auto-rotation) page by page into `work/ocr_full/`; page 1 only goes to `work/_ocr_p1/` for matching.
   The form pages the parser reads (CSP-2, 3, 3A, 4, 8, 10, 13, 15-20, 22, 27, 30-36) are then OCR'd a second time
   (`scripts/cost_reports/run_reocr.py`): page rendered at 300 dpi, table rules removed, `tesseract --psm 6` word
   boxes laid back out by position, so columns line up as in `pdftotext -layout`. Output goes to `work/reocr_out/`.
   `run_all.py` prefers it and fixes two common misreads ("4," for "4.", "(5.159,901)").
2. **Match each PDF to a home** (`scripts/cost_reports/index_reports.py` -> `work/cost_report_index.json`).
   Evidence: licensed name, page-1 address, DPH license number (reviewed crosswalk), Medicare number.
   "confirmed" needs two kinds of evidence; "probable" one strong kind with a clear margin; others go to review.
   The Medicare number printed on a report is not trusted alone (36 reports print another home's number).
3. **Extract** (`scripts/cost_reports/run_all.py` -> `work/extract_all.json`). Pages are found by their
   `CSP-<n>` form code. Columns are read by position from each page's header row: the 2023+ form has one
   combined `CCNH / RHNS` column; older forms have separate `CCNH` and `RHNS` columns, which are added.
   Entity pages (2, 3, 3A, 4, 17) are parsed into rows with the text kept as written.
4. **Build** `python scripts/build_ct_cost_reports.py` -> `data/ct_nursing_home_cost_reports.json` and
   `data/cost_reports/<ccn>.json`. Joins PBJ quarters for the same cost year, CMS owners, CHOW, management
   company of record, administrators of record, and management fees by company.
5. **Test** `python scripts/test_ct_cost_reports.py` (parser fixtures in `scripts/cost_reports/fixtures/` are
   page text from two public reports, values checked by eye against the PDF images), then the browser test.

## Food and support services (added 2026-11-08)

`cr_support.py` reads page 10 lines 5a-5c (dietary), 6a-6b (housekeeping), 8a-8b (laundry) and the non-salary
pages 18 (raw food 2a1, supplies 2a2, other 2a3, contract services 2b, other 2c, total 2D), 19 (3D) and 20 (4D).
`build_ct_cost_reports.support_services` turns them into cost per resident day:
- all-in department cost = its salaries + their share of fringe (fringe total x department salaries / all
  salaries, the same allocation as direct care) + the department's non-salary total, over total resident days;
- raw food per resident day only when the home buys its own food (raw food >= $3.00 per resident day and
  contract dietary services under half of raw food + contract). Otherwise "contractor" or "unclear";
- page 18's lines must add up to its printed total (a negative "Other" printed only in the Total column is an
  adjustment and is left out); if not, dietary and raw food are withheld.
Ranges (per resident day): raw food $2-$40, dietary $5-$120, housekeeping $1-$60, laundry $0.50-$40.
Older and scanned reports often lack a readable page 18; those years show no support figures.

## Checks and withholding

- Printed totals: payer days sum to total care days; revenue lines sum to total revenue; liabilities sum.
- Plausible ranges: resident days 20-105% of bed-days; direct care $40-$900 per resident day; nursing hours
  1.5-12 per resident day; direct care 15-85% of costs. A figure outside range is withheld on the page and the
  year is marked "check against the original".
- "validated" = core figures present, payer days add up, nothing out of range. Statewide medians use validated
  years only.

## Known limits

- Cost-report nursing hours are paid hours (they include paid time off); PBJ counts hours worked. The median gap
  is about 0.6 hours per resident day.
- Related-party and owner rows are free text on the form; names are a best reading, with the full text shown.
- Homes that do not take Medicaid (many continuing-care community health centers, the state veterans' home)
  do not file DSS cost reports.
- Management fees are linked to a company only when the Schedule C-1 line names it.
