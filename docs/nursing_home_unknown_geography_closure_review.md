# Unknown Geography Closure Review

Phase 11C.7 source-backed closure review. This document is documentation-only. It does not change public UI, runtime JSON, generated staffing data, historical PBJ data, staffing formulas, Connecticut applicability logic, or public tool behavior.

## 1. Purpose

Five current runtime facilities appear under `Unknown / needs review` in the Statewide Comparison county filter because they did not match April 2026 CMS Provider Information by CCN. This review checks whether official evidence supports closure, termination, no-longer-certified, renamed, merged, or otherwise non-current status for those facilities.

This review does not assign county. County should remain null until official address/county evidence is approved for the geography crosswalk.

## 2. Review Guardrails

- Do not infer closure solely from absence in April 2026 Provider Information.
- Do not assign county from facility name, city, ZIP, address memory, or informal geography knowledge.
- Distinguish date types. Closure dates, CMS certification/provider termination dates, license end dates, and bed-termination effective dates are not interchangeable.
- Treat secondary sources as context only unless an official source confirms the status and date.
- Preserve `Unknown / needs review` in the public county filter until a later implementation phase updates source-backed metadata.
- Do not change `data/nursing_home_staffing_ct.json`, `data/nursing_home_staffing_history_ct.json`, runtime JS/HTML, or generated staffing outputs.

## 3. Official Sources Reviewed

| Source | Source type | Use in this review | URL |
|---|---|---|---|
| Connecticut DSS, `Connecticut Nursing Home CCH and RHNS Latest Bed Census Received`, data as of January 29, 2026 | Official state PDF | Contains a `Closed Facilities` section with facility names, towns, bed counts, bed-change terminations, and effective dates. Used as official evidence for four current unknown facilities. | <https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/medicaid-nursing-home-reimbursement/2026_1_29-cch-and-rhns-january-bed-census.pdf> |
| CMS notice, `Notice of Involuntary Termination of Medicare Provider Agreement`, Abbott Terrace Health Center, August 26, 2024 | Official CMS letter hosted by DocumentCloud | Confirms CMS Certification No. 075351 and involuntary Medicare provider agreement termination effective September 10, 2024. Used as official provider-termination evidence for Abbott Terrace. | <https://s3.documentcloud.org/documents/25116648/abbott-terrace-health-center-075351-facility-termination-notice-3-4-2024-enforcement-cyclesv.pdf> |
| CMS, `FY 2026 SNFs Excluded from APU` | Official CMS PDF | Lists Abbott Terrace Health Center and Countryside Manor of Bristol with `Has Termination Date = Yes`. Used only as supplemental official evidence because it does not provide the exact termination date in the visible table. | <https://www.cms.gov/files/document/pac-snf-fy2026-apu-excluded.pdf> |
| CT eLicense / CMS Form 2567 document for Springs at Watermark East Hill, survey completed February 5, 2020 | Official CMS/CT licensing-document lead | Confirms CCN 075441, name `SPRINGS AT WATERMARK EAST HILL, THE`, and address `611 East Hill Road, Southbury, CT 06488` for a prior survey record. It does not confirm closure or non-current status. | <https://elicense.ct.gov/Lookup/ViewPublicLookupDocument.aspx?DocumentIdnt=3422519&GUID=5DD8713B-3BD4-4872-8BC8-95D471CFC564> |
| Connecticut DSS, East Hill Disclosure Statement, 2025 | Official state-hosted continuing-care disclosure lead | Mentions `The Springs` as an adjacent skilled nursing facility in the East Hill campus context. It does not provide closure or certification-end evidence for CCN 075441. | <https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/health-and-home-care/continuing-care-facility/disclosure-statements/2025/east-hill-disclosure-statement-20250310.pdf> |

## 4. Review Summary

| Facility | CCN | App geography status | Official closure/non-current evidence found? | Date | Date type | Confidence | Recommended action |
|---|---|---|---|---|---|---|---|
| ABBOTT TERRACE HEALTH CENTER | 075351 | `Unknown / needs review`; current runtime + historical PBJ; unmatched to April 2026 Provider Information | Yes. CMS provider agreement termination and CT DSS closed-facilities listing. | 2024-09-10; 2024-11-05 | provider termination date; other official end date | confirmed official | Mark as closed/non-current in a future non-runtime status file; keep county unknown until source-backed county/address update is approved. |
| COUNTRYSIDE MANOR OF BRISTOL | 075415 | `Unknown / needs review`; current runtime + historical PBJ; unmatched to April 2026 Provider Information | Yes. CT DSS closed-facilities listing; CMS APU file also indicates the facility has a termination date but does not show the exact date. | 2025-03-28 | other official end date | confirmed official | Mark as closed/non-current in a future non-runtime status file; keep county unknown until source-backed county/address update is approved. |
| MATTATUCK HEALTH CARE FACILITY, INC. | 075432 | `Unknown / needs review`; current runtime + historical PBJ; unmatched to April 2026 Provider Information | Yes. CT DSS closed-facilities listing. | 2025-03-25 | other official end date | confirmed official | Mark as closed/non-current in a future non-runtime status file; keep county unknown until source-backed county/address update is approved. |
| ST JOSEPH'S CENTER | 075001 | `Unknown / needs review`; current runtime + historical PBJ; unmatched to April 2026 Provider Information | Yes. CT DSS closed-facilities listing. | 2025-08-14 | other official end date | confirmed official | Mark as closed/non-current in a future non-runtime status file; keep county unknown until source-backed county/address update is approved. |
| SPRINGS AT EAST HILL, THE | 075441 | `Unknown / needs review`; current runtime + historical PBJ; unmatched to April 2026 Provider Information | No official closure, termination, certification-end, or license-end evidence found in this review. Official sources support identity/address history, not closure. | Not found | Not applicable | unresolved | Keep unknown; keep in manual review queue; investigate current CMS/Care Compare naming and archived Provider Information before any crosswalk update. |

## 5. Facility-Level Findings

### ABBOTT TERRACE HEALTH CENTER

| Field | Review finding |
|---|---|
| Facility name | ABBOTT TERRACE HEALTH CENTER |
| CCN | 075351 |
| Existing app city/address | WATERBURY; address unavailable in current app geography crosswalk |
| Current app geography status | `Unknown / needs review`; county null; current runtime facility; historical PBJ facility; unmatched to April 2026 Provider Information |
| Official evidence status | Confirmed official provider termination and official closed-facilities listing |
| Official date 1 | 2024-09-10 |
| Date type 1 | provider termination date |
| Source 1 | CMS, `Notice of Involuntary Termination of Medicare Provider Agreement`, Abbott Terrace Health Center, August 26, 2024 |
| Source URL 1 | <https://s3.documentcloud.org/documents/25116648/abbott-terrace-health-center-075351-facility-termination-notice-3-4-2024-enforcement-cyclesv.pdf> |
| Official date 2 | 2024-11-05 |
| Date type 2 | other official end date; CT DSS closed-facilities bed-termination effective date |
| Source 2 | Connecticut DSS, `Connecticut Nursing Home CCH and RHNS Latest Bed Census Received`, data as of January 29, 2026 |
| Source URL 2 | <https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/medicaid-nursing-home-reimbursement/2026_1_29-cch-and-rhns-january-bed-census.pdf> |
| Confidence | confirmed official |
| Recommended action | Add to a future non-runtime status review file as closed/non-current. Do not update county unless official address/county evidence is separately approved. Keep in manual review queue until crosswalk metadata is updated in a later phase. |

Notes: The CMS letter identifies CMS Certification No. 075351 and states the involuntary Medicare provider agreement termination was effective September 10, 2024. The CT DSS bed census later lists Abbott Terrace Health Center under `Closed Facilities` with bed-change terminations effective November 5, 2024. These dates should not be merged; they describe different official events.

### COUNTRYSIDE MANOR OF BRISTOL

| Field | Review finding |
|---|---|
| Facility name | COUNTRYSIDE MANOR OF BRISTOL |
| CCN | 075415 |
| Existing app city/address | BRISTOL; address unavailable in current app geography crosswalk |
| Current app geography status | `Unknown / needs review`; county null; current runtime facility; historical PBJ facility; unmatched to April 2026 Provider Information |
| Official evidence status | Confirmed official closed-facilities listing; supplemental CMS APU file indicates a termination date exists but does not provide the exact date |
| Official date | 2025-03-28 |
| Date type | other official end date; CT DSS closed-facilities bed-termination effective date |
| Source title | Connecticut DSS, `Connecticut Nursing Home CCH and RHNS Latest Bed Census Received`, data as of January 29, 2026 |
| Source URL | <https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/medicaid-nursing-home-reimbursement/2026_1_29-cch-and-rhns-january-bed-census.pdf> |
| Supplemental official source | CMS, `FY 2026 SNFs Excluded from APU`, lists CCN 075415 with `Has Termination Date = Yes` |
| Supplemental source URL | <https://www.cms.gov/files/document/pac-snf-fy2026-apu-excluded.pdf> |
| Confidence | confirmed official |
| Recommended action | Add to a future non-runtime status review file as closed/non-current. Do not update county unless official address/county evidence is separately approved. Keep in manual review queue until crosswalk metadata is updated in a later phase. |

Notes: The CT DSS bed census is the exact-date source used here. The CMS APU file is useful corroboration that a termination date exists, but it is not used as the exact-date source.

### MATTATUCK HEALTH CARE FACILITY, INC.

| Field | Review finding |
|---|---|
| Facility name | MATTATUCK HEALTH CARE FACILITY, INC. |
| CCN | 075432 |
| Existing app city/address | WATERBURY; address unavailable in current app geography crosswalk |
| Current app geography status | `Unknown / needs review`; county null; current runtime facility; historical PBJ facility; unmatched to April 2026 Provider Information |
| Official evidence status | Confirmed official closed-facilities listing |
| Official date | 2025-03-25 |
| Date type | other official end date; CT DSS closed-facilities bed-termination effective date |
| Source title | Connecticut DSS, `Connecticut Nursing Home CCH and RHNS Latest Bed Census Received`, data as of January 29, 2026 |
| Source URL | <https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/medicaid-nursing-home-reimbursement/2026_1_29-cch-and-rhns-january-bed-census.pdf> |
| Confidence | confirmed official |
| Recommended action | Add to a future non-runtime status review file as closed/non-current. Do not update county unless official address/county evidence is separately approved. Keep in manual review queue until crosswalk metadata is updated in a later phase. |

Notes: The CT DSS bed census lists Mattatuck Health Care Facility, Inc. under `Closed Facilities` and gives a bed-change termination effective date of March 25, 2025.

### ST JOSEPH'S CENTER

| Field | Review finding |
|---|---|
| Facility name | ST JOSEPH'S CENTER |
| CCN | 075001 |
| Existing app city/address | TRUMBULL; address unavailable in current app geography crosswalk |
| Current app geography status | `Unknown / needs review`; county null; current runtime facility; historical PBJ facility; unmatched to April 2026 Provider Information |
| Official evidence status | Confirmed official closed-facilities listing |
| Official date | 2025-08-14 |
| Date type | other official end date; CT DSS closed-facilities bed-termination effective date |
| Source title | Connecticut DSS, `Connecticut Nursing Home CCH and RHNS Latest Bed Census Received`, data as of January 29, 2026 |
| Source URL | <https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/medicaid-nursing-home-reimbursement/2026_1_29-cch-and-rhns-january-bed-census.pdf> |
| Confidence | confirmed official |
| Recommended action | Add to a future non-runtime status review file as closed/non-current. Do not update county unless official address/county evidence is separately approved. Keep in manual review queue until crosswalk metadata is updated in a later phase. |

Notes: Secondary news sources reported an intent to close in May 2025, but the official source used for this review is the CT DSS January 29, 2026 bed census.

### SPRINGS AT EAST HILL, THE

| Field | Review finding |
|---|---|
| Facility name | SPRINGS AT EAST HILL, THE |
| CCN | 075441 |
| Existing app city/address | SOUTHBURY; address unavailable in current app geography crosswalk |
| Current app geography status | `Unknown / needs review`; county null; current runtime facility; historical PBJ facility; unmatched to April 2026 Provider Information |
| Official evidence status | No official closure, termination, certification-end, license-end, rename, merger, or non-current status confirmed in this review |
| Official date | Not found |
| Date type | Not applicable |
| Source title | CT eLicense / CMS Form 2567 document for `SPRINGS AT WATERMARK EAST HILL, THE`, survey completed February 5, 2020 |
| Source URL | <https://elicense.ct.gov/Lookup/ViewPublicLookupDocument.aspx?DocumentIdnt=3422519&GUID=5DD8713B-3BD4-4872-8BC8-95D471CFC564> |
| Additional official source lead | Connecticut DSS, East Hill Disclosure Statement, 2025 |
| Additional source URL | <https://portal.ct.gov/dss/-/media/departments-and-agencies/dss/health-and-home-care/continuing-care-facility/disclosure-statements/2025/east-hill-disclosure-statement-20250310.pdf> |
| Confidence | unresolved |
| Recommended action | Keep unknown and keep in manual review queue. Investigate whether the April 2026 Provider Information mismatch reflects naming, provider-file scope, Medicare/Medicaid participation status, or another source-refresh issue. Do not mark closed/non-current without official end-date evidence. |

Notes: Official source leads support CCN 075441 identity/address history under a related name, `SPRINGS AT WATERMARK EAST HILL, THE`, but this review did not find official closure or termination evidence. A later county/address update may be appropriate only after the project approves a source-backed geography update method.

## 6. Proposed Future Status Review Data Model

Do not create this file in Phase 11C.7. If a later implementation phase needs a non-runtime review artifact, use a separate file rather than changing staffing data:

Possible future file:

- `data/nursing_home_facility_status_review_ct.json`

Possible fields:

| Field | Purpose |
|---|---|
| `ccn` | CMS Certification Number. |
| `facility_name` | Facility name from current crosswalk or reviewed official source. |
| `status_review_required` | Boolean flag for records needing status review. |
| `current_provider_info_match` | Whether the facility matched the current Provider Information snapshot. |
| `possible_closed_or_non_current` | Boolean flag for records with official or strong source leads suggesting non-current status. |
| `official_status` | Source-backed status such as `closed`, `provider_terminated`, `bed_terminated`, `active_source_found`, or `unresolved`. |
| `official_status_date` | Date from the official source. |
| `official_status_date_type` | One of `closure date`, `certification termination date`, `license expiration/end date`, `provider termination date`, or `other official end date`. |
| `official_status_source` | Source title. |
| `source_url` | Source URL or local source file. |
| `review_confidence` | `confirmed official`, `likely but needs official confirmation`, or `unresolved`. |
| `review_notes` | Short evidence note, including distinctions between multiple date types. |

This file should not drive public UI until reviewed, validated, and explicitly wired in a future phase.

## 7. Recommended Next Actions

1. Keep `data/nursing_home_facility_geography_ct.json` unchanged in this phase.
2. Create a future non-runtime status review artifact only after deciding how status metadata should be validated and refreshed.
3. For Abbott Terrace, preserve both dates: CMS provider termination effective September 10, 2024, and CT DSS bed-termination effective November 5, 2024.
4. For Countryside Manor, Mattatuck, and St. Joseph's, treat the CT DSS dates as official bed-termination effective dates from the closed-facilities section, not as CMS provider termination dates unless a CMS source is later found.
5. For Springs at East Hill, continue source review. Focus on current/archived CMS Provider Information, Care Compare provider files, CT eLicense records, and CCRC/skilled-nursing licensure records.
6. Do not update county values for any of the five without official source-backed county/address evidence and a later crosswalk validation pass.
