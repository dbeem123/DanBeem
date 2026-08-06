# Facility Explorer Survey and Enforcement Snapshot QA

## Scope

Phase 11D.18 adds a cautious, facility-level Survey & Enforcement Snapshot to the advanced dossier in the Nursing Home Staffing Explorer. The snapshot is placed after the core current-staffing section and is collapsed by default.

## Files Changed

- `tools/nursing-home-staffing-explorer.html`
- `Assets/nursing-home-staffing.js`
- `Assets/ltcop-dashboard.css`
- `docs/nursing_home_facility_explorer_survey_enforcement_snapshot_qa.md`

No staffing formulas or source datasets were changed.

## Data Loading

The Facility Explorer loads only `data/nursing_home_survey_enforcement_summary_ct.json` for the new snapshot. It indexes the 196 compact facility records by their six-character CCN strings and joins the selected facility without numeric conversion, preserving leading zeros.

The Facility Explorer does not fetch these detailed files:

- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_penalties_ct.json`

The compact summary request runs independently of the staffing dataset request. If it fails or has an invalid structure, the staffing explorer remains usable and the snapshot displays a gentle unavailable message. This fallback path was code-reviewed; a forced network failure was not introduced during browser QA.

## Snapshot Content

The snapshot displays:

- the metadata-defined recent window, 2023-03-31 through 2026-03-31, inclusive;
- latest health survey, fire safety survey, and enforcement-event dates;
- recent health deficiency, actual harm, immediate jeopardy, fire safety, emergency preparedness, enforcement-event, fine, payment-denial, dollar, and denial-day values;
- a collapsed secondary disclosure with totals across each available source window;
- zero values rather than blank values;
- `Not found in this source` for unavailable dates; and
- a clear zero-record message when all three source-presence flags are false.

The section is visually and verbally separated from staffing classification. It does not calculate scores or rankings.

## Wording and Caution Review

The visible caution panel confirms that:

- counts are CMS survey and enforcement context, not a standalone quality score;
- fine amounts should not be used by themselves to rank facilities;
- survey and enforcement information is separate from staffing measures;
- detailed citation and event rows are not loaded by default; and
- known CMS citation-description lookup gaps exist for K-0211 and K-0133 while source descriptions remain preserved in the detailed dataset.

## Manual Browser QA

The page was served locally and inspected in the in-app browser.

### Facilities Checked

- **60 WEST (CCN 075442):** Health and fire safety counts rendered, unavailable enforcement date rendered as `Not found in this source`, and zero enforcement values displayed as zero.
- **AUTUMN LAKE HEALTHCARE AT WINDSOR (CCN 075011):** Health, fire safety, emergency preparedness, and enforcement values rendered. The recent fine displayed as 1 and $19,432.00.
- **ABBOTT TERRACE HEALTH CENTER (CCN 075351):** The no-record state rendered clearly; all counts displayed as zero and all latest dates displayed as unavailable.

### Existing Behavior Checked

- Facility search filtered `Windsor` to 6 of 196 facilities and updated the selected facility and snapshot.
- Existing staffing metric cards and the five-row quarterly exhibit continued to render after facility changes.
- The staffing source status remained populated.
- The browser console contained no warnings or errors.
- This page has no county/geography control; geography data and other tools were not changed.

### Responsive Review

At a 390-by-844 mobile test viewport, the rendered content width was 375 pixels with no horizontal page overflow. Latest-date and metric cards collapsed to one column, headings wrapped cleanly, and the staffing-separation label remained readable. Desktop cards rendered in responsive multi-column grids.

The first local pass exposed a cached shared stylesheet. Page-local version parameters were added to the changed dashboard CSS and staffing JavaScript references so the prototype assets refresh together.

## Automated and Static Verification

- `node --check Assets/nursing-home-staffing.js` passed.
- `python -m unittest scripts.test_build_nursing_home_staffing_ct` passed all 18 tests.
- A filename scan confirmed that the Facility Explorer JavaScript and HTML reference only the compact summary, not the three detailed runtime files.
- `git diff --check` passed.

## Known Limitations

- The compact summary reflects available rolling CMS source windows, not complete lifetime history.
- The page does not expose individual citation descriptions or enforcement-event detail in this phase.
- Detailed rows are intentionally not loaded by default.
- Known K-0211 and K-0133 description-lookup gaps remain a CMS reference-source limitation.
- The unavailable-summary UI was implemented defensively but was not forced with a simulated 404 during browser QA.

## Recommendation

Proceed to Phase 11D.19 only after reviewing this prototype wording and performance. If detailed dossier sections are added, load the detailed health, fire safety, emergency preparedness, and enforcement files only on explicit user request, retain the compact snapshot as the default view, and keep each source category and its caveats distinct.
