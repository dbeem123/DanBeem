# Nursing Home Survey / Enforcement Methodology and Wording Review

## Review scope

Phase 11D.20 reviewed the public methodology, Facility Explorer disclosures, survey/enforcement runtime wording, and the repository metadata that identifies the CMS sources used by the tool. The review was limited to methodology, source disclosure, public wording, and small accessibility/layout corrections. It did not change staffing formulas, survey/enforcement classifications, generated datasets, data builders, or lazy-loading behavior.

## Files reviewed

- `tools/nursing-home-staffing-methodology.html`
- `tools/nursing-home-staffing-explorer.html`
- `Assets/nursing-home-staffing.js`
- `data/current_tool_context_registry.json`
- `data/nursing_home_source_manifest.json`
- Survey/enforcement runtime JSON and the CMS source files used to build it

## Files changed

- `tools/nursing-home-staffing-methodology.html`
- `tools/nursing-home-staffing-explorer.html`
- `Assets/nursing-home-staffing.js`
- `data/current_tool_context_registry.json`
- `data/nursing_home_source_manifest.json`
- `docs/nursing_home_survey_enforcement_methodology_wording_review.md`

## Methodology and source disclosures added

The public methodology now explains that survey/enforcement information is CMS facility-level context keyed by CMS Certification Number (CCN). It describes Health F-tag, Fire Safety K-tag, Emergency Preparedness E-tag, civil money penalty, and payment-denial records without presenting them as a score, staffing classification, comprehensive legal history, or facility ranking.

The disclosure names the exact May 2026 CMS source files used by the current build:

- `NH_CitationDescriptions_May2026.csv`
- `NH_HealthCitations_May2026.csv`
- `NH_FireSafetyCitations_May2026.csv`
- `NH_Penalties_May2026.csv`

It also publishes the observed source ranges:

- Health citations: 2015-01-01 through 2026-03-31
- Fire Safety citations: 2015-01-01 through 2026-03-31
- Emergency Preparedness citations: 2017-11-15 through 2026-03-31
- Penalty events: 2015-01-01 through 2026-03-31
- Payment-denial events: 2015-01-01 through 2026-03-31
- CMS processing date represented in these files: 2026-05-01

## Recent-window disclosure

The current recent window is 2023-03-31 through 2026-03-31, inclusive. It is anchored to the maximum survey citation date represented in the current source extracts and is applied consistently to Health, Fire Safety, and Emergency Preparedness citation summaries. "Recent" does not mean a facility's latest survey. All penalty rows in the current build fall within this window; penalty dates remain distinct from survey citation dates.

## Health harm grouping

The methodology documents the Health F-tag-only grouping used by the runtime summary:

- Immediate jeopardy: J, K, L
- Actual harm: G, H, I
- Potential for more than minimal harm: D, E, F
- Minimal harm: A, B, C
- Unknown: missing or unrecognized scope/severity values

These group labels are not applied to Fire Safety K-tags or Emergency Preparedness E-tags.

## Citation-description lookup limitations

The current official citation-description lookup does not contain K-0211 or K-0133. The runtime preserves the CMS source description present on those Fire Safety citation rows and does not invent or backfill an official lookup description. This limitation is disclosed in both the methodology and source manifest.

## Penalty fields and duplicate rows

The methodology distinguishes penalty type, penalty amount, penalty event date, payment-denial start date, payment-denial end date, and source processing date. It also discloses that the source contains three duplicate full-row signatures. The runtime preserves those source rows; aggregate counts and totals should therefore be interpreted as source-row aggregates rather than a deduplicated legal-event ledger.

## Runtime architecture disclosure

The Facility Explorer loads a compact statewide survey/enforcement summary by default. Full survey/enforcement details are requested only after a user selects a facility and opens that facility's details, using the CCN-indexed detail manifest and per-facility JSON file. Normal page load does not fetch the statewide Health, Fire Safety, or penalty build datasets. No lazy-loading behavior changed in this phase.

## Coverage disclosure

The public methodology now reports the current runtime coverage:

- 196 facilities in the compact summary
- 191 facilities with Health citation records
- 178 facilities with Fire Safety or Emergency Preparedness citation records
- 102 facilities with penalty or payment-denial records
- 5 facilities with no survey/enforcement source rows in the current extracts

A zero in the current source summary does not mean a facility has never had a citation or enforcement action.

## Public wording and accessibility corrections

- Expanded CMS Certification Number on first-use and runtime CCN labels with an accessible abbreviation.
- Expanded Informal Dispute Resolution (IDR) and Independent Informal Dispute Resolution (IIDR).
- Changed the public label to "Health harm grouping" to avoid implying the Health-specific grouping applies to Fire Safety or Emergency Preparedness tags.
- Strengthened zero-result, source-coverage, citation-date, non-ranking, and Fire Safety lookup-gap cautions.
- Added a direct Facility Explorer link to the survey/enforcement methodology section.
- Added semantic section headings for the new methodology content.
- Added safe long-code wrapping and minimum-width behavior so exact CMS filenames do not create horizontal mobile overflow.
- Added anchor scroll spacing so the sticky site header does not obscure the linked methodology heading.

## Metadata changes

`data/nursing_home_source_manifest.json` now records the four integrated CMS survey/enforcement sources, exact filenames, runtime outputs, date coverage, recent-window rule, citation-lookup gaps, distinct penalty fields, duplicate-row caveat, and separation from the staffing classification.

`data/current_tool_context_registry.json` now identifies the compact summary, per-CCN lazy-loaded details, detail index, source dates, coverage, lookup limitations, duplicate penalty signatures, and the statewide build datasets that are explicitly not loaded during normal Facility Explorer use.

## Verification completed

- Both metadata JSON files parse successfully with PowerShell and `python -m json.tool`.
- `node --check Assets/nursing-home-staffing.js` passes.
- `python -m unittest scripts.test_build_nursing_home_staffing_ct` passes all 18 tests.
- `git diff --check` passes.
- Browser review covered desktop and 375-pixel mobile layouts, the methodology anchor, the Facility Explorer methodology link, and console output.
- Mobile horizontal overflow introduced by long source filenames was corrected.
- Protected staffing and survey/enforcement generated datasets and builders have no phase-specific modifications.
- Raw CMS survey/enforcement source directories remain ignored by Git.

Protected-file Git object hashes observed during verification:

- Staffing current: `8fe1aab997f07839abc62390a7460eda0ad8a88c`
- Staffing history: `501e26e61cb9e00ddffc628c27feeb123dbb3711`
- Geography: `9f42e9a8b8acfd1487779b21347ce8daa2a1ca9c`
- Facility status: `3ca689ae43f0bb2511d0cac8e46f0553023f31bb`
- Compact survey/enforcement summary: `118d120dba31cd76a31efc331a6c3ea06eff55c3`
- Survey/enforcement detail index: `053b61044ac9e46b709fa3742c0a688466267b2c`
- Health citations: `b998bc6e8753124b8218567c047d106a77bacd15`
- Fire Safety citations: `b23c636b643034b464a9156101b3d7e6eb5186b2`
- Penalties: `40148be420df61adf8efe26315b7c9da7741d315`

## Known limitations

- The disclosures describe the May 2026 CMS extracts currently present in the repository; future source refreshes must update the dates, coverage, filenames, and caveats together.
- Survey and enforcement records are source-limited context, not a complete regulatory or legal history.
- The three duplicate penalty signatures remain source-preserved and are not deduplicated.
- K-0211 and K-0133 remain absent from the official citation-description lookup used by this build.

## Recommended next phase

Add automated methodology/metadata consistency checks that compare published filenames, date ranges, coverage counts, lookup gaps, and duplicate-row counts with generated runtime metadata during each CMS refresh. A refresh runbook and visible source-currency indicator can follow without introducing rankings or changing the current classifications.
