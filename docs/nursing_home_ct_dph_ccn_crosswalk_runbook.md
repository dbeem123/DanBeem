# CT DPH License to CMS CCN Crosswalk: Runbook

Roadmap item: "CT DPH-to-CMS CCN crosswalk construction" (`nursing_home_data_acquisition_roadmap.md`, `nursing_home_ct_specific_additions_plan_20261030.md`, Phase B item 5). Every Connecticut state data source in Phase B depends on this crosswalk: DPH leadership timeline, DSS rates, census and facility CMI.

Status, 2026-10-30: the builder and its tests are written. It has **not** been run on the real DPH file, because that file sits in Daniel's Downloads folder and was not available to Claude.

## Run it
1. Copy `Chronic_and_Convalescent_Nursing_Home.csv` (189 rows, SHA-256 `1806cd31...0aa5b5` per `data/ct_dph_source_profile.json`) to `source_data/ct_dph/`. That folder is gitignored, so the file is never published.
2. `python scripts/build_ct_dph_ccn_crosswalk.py`
3. Outputs go to `data/testing/`, which is also gitignored:
   - `ct_dph_ccn_crosswalk_candidate.json`: every license with its best CCN, tier, score and evidence.
   - `ct_dph_ccn_crosswalk_candidate.review.md`: the review queue (everything below `auto_high`), plus CMS facilities with no license match.
4. Tests: `python scripts/test_build_ct_dph_ccn_crosswalk.py`

## How matching works
- **Normalization:**
  - Names are uppercased, `&` becomes `AND`, and punctuation is dropped. Generic words (CENTER, HEALTH, REHABILITATION, NURSING...) are ignored for similarity.
  - Addresses keep the street number, standardize suffixes and directions (STREET->ST, WEST->W) and drop suite or unit text.
  - ZIP codes keep 5 digits and fix the letter O typed for zero, which appears in CT DPH exports.
  - Licenses keep digits and drop leading zeroes, the same rule as the governance validation.
- **Score:**
  - Up to 0.35 for the same street number.
  - Up to 0.20 for the same street (0.10 for partial).
  - 0.10 for the same ZIP and 0.10 for the same city.
  - 0.25 x name similarity.
- **Tiers:**
  - `auto_high`: same number, same street, same ZIP or city, and name similarity >= 0.35.
  - `likely`: an address and place match, or a place match with name similarity >= 0.6.
  - `review`: anything weaker.
  - `unmatched`.
- **Safety rules:**
  - Each CCN goes to one license only; weaker claims drop to `review`.
  - An `auto_high` whose runner-up is within 0.15 drops to `likely`.

## Acceptance before anything goes public
1. A person reviews every non-`auto_high` row and samples at least 10% of `auto_high`, setting `review_decision` to `accepted` or `rejected` with a note.
2. Expected gaps to explain, not force:
   - DPH has 189 licenses and CMS has 196 facilities in the staffing export, so some CMS facilities may not hold a chronic and convalescent license, or may have closed.
   - Some licenses may be rest homes or non-certified.
3. Record the reviewed file's hash in `data/nursing_home_source_manifest.json`. Only rows with `accepted` may be joined to CCN-keyed public pages.
4. Write `docs/nursing_home_ct_dph_ccn_crosswalk_validation_report.md` with the tier counts, accepted, rejected and unresolved rows, and the hash.

## Data that needs downloading next (by Daniel, from a browser)
These come from portal.ct.gov, which Claude's environment cannot reach. Save each into `source_data/ct_dss/` with its release date in the file name.

| File | Where | Use |
|---|---|---|
| Facility-by-facility CMI averages, 2025 Q1 (.xlsx) | DSS > Medicaid Nursing Home Reimbursement > Acuity Based Methodology > CMI Averages | Facility Medicaid acuity next to staffing (needs the crosswalk) |
| Nursing facility census and bed reports | DSS > Nursing Facility Rates & Census | Beds, occupancy, open beds |
| Case Mix Quarterly Rate Calculation workbooks | DSS > Nursing Facility Rates & Census | Rate components and acuity detail |
| SFY 2026 rate letters | DSS > Nursing Facility Rates | Medicaid per diem by facility |

Keep person-level files, such as `Nursing_Home_Administrator_*.csv` (which has administrators' home addresses), out of every public output. The crosswalk reads facility fields only, and a test checks that no person fields are written.
