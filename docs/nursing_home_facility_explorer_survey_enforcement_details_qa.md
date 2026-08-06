# Facility Explorer survey and enforcement details QA

## Scope

Phase 11D.19B adds an explicitly requested, per-facility survey and enforcement detail view beneath the existing compact Facility Explorer snapshot. The runtime source is the CCN-specific JSON file in `data/nursing_home_survey_enforcement_details_ct/`; no statewide survey or enforcement file is loaded by the browser.

QA was completed on August 4, 2026 against the local static site at `http://127.0.0.1:8765/tools/nursing-home-staffing-explorer.html`.

## Runtime request checks

- A clean page load requested the compact summary and made zero requests to `nursing_home_survey_enforcement_details_ct/`.
- Selecting Arden Care Center (CCN `075228`) updated the compact snapshot and still made zero detail requests.
- Activating **View detailed findings** made one request for exactly `../data/nursing_home_survey_enforcement_details_ct/075228.json`.
- Reopening Arden after selecting other facilities reused the in-memory response. The local server log remained at one successful `075228.json` request for that browser session.
- Autumn Lake Healthcare at Windsor (CCN `075011`) was loaded through a deliberately delayed local response. The selection was changed to Abbott Terrace while the request was pending. Abbott remained selected, the detail view closed, and no Windsor heading or records appeared after the delayed response completed.
- Returning to Windsor opened its successfully cached response without another request. The server log contained one `075011.json` request.
- CCNs remained six characters in request paths, including their leading zero.

The runtime uses a monotonically increasing request token plus the current CCN to reject late renders. Successful responses are cached in a session `Map` keyed by CCN.

## Facility and content matrix

### Arden Care Center — many records (`075228`)

- Rendered four separate sections: 91 health deficiencies, 31 fire safety deficiencies, 1 emergency preparedness deficiency, and 4 penalties/payment denials.
- Health and fire sections initially displayed 10 records each.
- **Show 10 more** increased the visible health records from 10 to 20; **Show all 91** displayed all 91.
- Each section collapsed independently.
- The newest survey and penalty dates appeared first.
- Health records used plain-language harm labels, including “No actual harm, with potential for more than minimal harm.” No health harm-group field appeared in the fire section.
- The unmatched K-0211 fire record displayed a visible CMS citation-description lookup-gap annotation while preserving the source description.
- Penalties displayed formatted dates and dollar values without creating a score or ranking.

### Autumn Lake Healthcare at Windsor — mixed records (`075011`)

- Rendered all four sections with 31 health, 26 fire, 3 emergency preparedness, and 1 penalty record in the source file.
- The emergency preparedness and penalty sections displayed 3 and 1 cards respectively.
- The delayed-response facility-switch test confirmed stale Windsor content could not render into Abbott's view.

### Abbott Terrace Health Center — zero records (`075351`)

- Rendered the explicit limited-source zero state.
- Kept all four semantic sections visible with zero records and no record cards.
- The message states that no included records does not mean the facility has never had a deficiency or enforcement action.

## Failure and retry check

The exact Abbott detail file was temporarily renamed after its absolute path was verified inside the generated detail directory.

- The first explicit detail request returned 404.
- The compact Abbott snapshot remained visible.
- The detail area showed a clear error and **Retry detailed findings** control.
- The file was restored before retry. Its Git object hash was `4101e6866ef4a4ef771b796a97183fcb6242cb54` both before and after the simulation.
- Retry succeeded and rendered the zero-record state.
- No temporary renamed file remained after QA.

## Accessibility and responsive checks

- The opt-in control is a native button with `aria-expanded` and `aria-controls`.
- Loading and result containers expose `aria-busy`/`aria-live`; the recoverable error uses `role="alert"`.
- After a successful open, focus moved to the detail heading (`tabindex="-1"`), and the visible focus treatment was confirmed.
- Record groups use native `details`/`summary` controls, headings, articles, definition lists, and `time` elements rather than a wide data table.
- All progressive-disclosure and retry actions are native buttons; section toggles are native summaries, preserving standard keyboard semantics.
- At 1280 × 900, record cards formed a readable two-column grid.
- At 390 × 844, cards and metadata collapsed to one column without a wide table or horizontal record grid.
- The detail heading includes scroll margin for the sticky navigation at desktop and mobile breakpoints.
- A clean browser session loaded 196 facility options with no console errors.

## Automated and repository checks

- `node --check Assets/nursing-home-staffing.js` — passed.
- `python -m unittest scripts.test_build_nursing_home_staffing_ct` — all 18 tests passed.
- `git diff --check` — passed.
- Runtime source scan found only the compact summary path and the per-facility detail directory in the Facility Explorer JavaScript; no statewide health, fire, or penalty runtime path was introduced.
- No builder or generated data file was modified by Phase 11D.19B.

Protected-data Git object hashes after QA:

- `data/nursing_home_staffing_ct.json`: `8fe1aab997f07839abc62390a7460eda0ad8a88c`
- `data/nursing_home_survey_enforcement_summary_ct.json`: `118d120dba31cd76a31efc331a6c3ea06eff55c3`
- `data/nursing_home_survey_enforcement_details_ct/index.json`: `053b61044ac9e46b709fa3742c0a688466267b2c`

Phase 11D.19B changes are limited to the Facility Explorer HTML, its JavaScript and stylesheet, and this QA record.
