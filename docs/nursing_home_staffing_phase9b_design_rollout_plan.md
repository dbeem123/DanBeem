# Phase 9B Staffing Suite Design Rollout Plan

Phase 9A established the Connecticut LTCOP dashboard design system on the staffing-suite homepage and the facility-level Nursing Home Staffing Explorer. Phase 9B should apply the same branded pattern to the remaining staffing tools without changing calculations, data contracts, filters, exports, print behavior, or caveat logic.

## Completion Note

Phase 9B has been implemented across the remaining staffing tools and the methodology page. The rollout added the shared Connecticut LTCOP masthead, navy suite navigation, light dashboard shell, compact table treatment, branded action controls, and public-service footer pattern while preserving the existing JavaScript IDs, data dependencies, filters, exports, print actions, copy briefing summaries, deep links, and screening caveats.

## Rollout Targets

1. `tools/nursing-home-statewide-staffing-comparison.html`
   - Add the white Connecticut LTCOP masthead and navy suite navigation.
   - Restyle filters, table, summary cards, print/export/copy actions, and screening badges using `Assets/ltcop-dashboard.css`.
   - Keep statewide ranking language neutral and avoid unsupported risk labels.

2. `tools/nursing-home-staffing-change-over-time.html`
   - Apply branded masthead, navigation, light dashboard background, and compact cards.
   - Preserve current change modes, current-view CSV, print, and briefing summary behavior.
   - Consider a small visual trend/change cue only after browser review confirms table density is manageable.

3. `tools/nursing-home-persistent-staffing-patterns.html`
   - Apply branded masthead and disclosure-friendly layout.
   - Restyle persistent pattern badges and quarter strips with accessible color and text labels.
   - Preserve missing-row and benchmark-ineligible-quarter caveats.

4. `tools/nursing-home-ownership-staffing-explorer.html`
   - Apply branded masthead and navigation.
   - Restyle affiliation rankings, selected-affiliation summary, persistence table, print/export/copy actions, and affiliation drill-down links.
   - Keep affiliation grouping caveats clear: CMS SNF Enrollment affiliation entity does not prove common day-to-day control.

5. `tools/nursing-home-staffing-methodology.html`
   - Apply masthead, footer, and light public-service content styling.
   - Keep source references and legal/regulatory citations readable.

## Design Rules To Preserve

- Use the transparent color CT LTCOP horizontal logo as the primary masthead identity.
- Keep the combined ADS + LTCOP logo as secondary attribution only if it fits cleanly.
- Use navy for headings, navigation, and table headers.
- Use red sparingly for LTCOP accent and screening indicators.
- Do not use terms such as `violation`, `noncompliant`, or `high-risk` unless a later documented methodology supports them.
- Screening indicators identify questions for review; they are not formal compliance findings.
- Do not add AI API calls or embedded keys to the static site.

## Future Features To Keep Separate

- Official CMS status indicators such as Special Focus Facility, Special Focus Facility candidate, Abuse Icon, or deficiency/citation severity should be added only after official facility-level source fields are obtained and documented.
- A future `Prepare ChatGPT Review` action may generate a copyable prompt from visible metrics and caveats, organized as what the data shows, what it may suggest, and what it cannot prove. This should remain a copy/prompt helper unless separately approved for a server-side integration.
