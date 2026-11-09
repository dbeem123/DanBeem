# Inspections and Resident Rights: runbook

Page: `staffing/tools/nursing-home-inspections.html` with `Assets/nursing-home-inspections.js`.
Data: `data/ct_inspections.json` and `data/nursing_home_facility_roster_ct.json`, built by
`scripts/build_ct_inspections.py`. Tests: `scripts/test_ct_inspections.py` and the "inspections" block in
`scripts/test_website_presentation.js`.

## Monthly refresh (with the Care Compare release)
1. Refresh the existing CMS inputs as usual (Health and Fire Safety Deficiencies, Citation Look-up, Penalties,
   Provider Information, PBJ). They rebuild `data/nursing_home_health_deficiencies_ct.json`,
   `data/nursing_home_fire_safety_deficiencies_ct.json` and `data/nursing_home_staffing_ct.json`.
2. Download CMS Inspection Dates (https://data.cms.gov/provider-data/dataset/svdt-c123) into
   `source_data/cms_survey/` keeping the CMS file name (`NH_SurveyDates_<Mon><YYYY>.csv`).
3. The builder picks the newest `NH_SurveyDates_*`, `NH_CitationDescriptions_*` and `NH_ProviderInfo_*` by the
   month in the file name. Provider Information must be the national file (or at least every CT row).
4. Run `python scripts/build_ct_inspections.py`, then the tests.

## Rules
- Every citation row in the two deficiency files is kept; the test fails if one is dropped.
- CCNs are six-character strings. Every CCN seen in any source is in the roster, with a note for each gap.
- Correction dates are shown as CMS recorded them, including dates before the survey date.
- Inspection Dates footnote 29 marks a risk-based survey (QSO-26-14-NH). No record is not proof of no survey.
- Resident rights groups live in `data/reference/resident_rights_tag_map.json`. While its `status` is `draft`
  the page shows a notice. Change it to `verified` only after the Appendix PP check.
- No rankings: the score chart shows where a home falls, with no rank number.
