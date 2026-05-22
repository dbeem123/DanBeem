# Phase 9B UI Review Notes

Phase 9B applied the Connecticut LTCOP dashboard design system to the remaining staffing tools and the public methodology page.

## Pages Updated

- `tools/nursing-home-statewide-staffing-comparison.html`
- `tools/nursing-home-staffing-change-over-time.html`
- `tools/nursing-home-persistent-staffing-patterns.html`
- `tools/nursing-home-ownership-staffing-explorer.html`
- `tools/nursing-home-staffing-methodology.html`

## Browser Review Priorities

- Confirm wide analytical tables remain easy to scan on laptop and tablet widths.
- Confirm copy briefing summary fallback textareas are readable after the branded restyle.
- Confirm print views still suppress navigation and keep report content compact.
- Confirm persistent-pattern quarter markers remain understandable without relying on color alone.
- Confirm the dense ownership / affiliation page remains navigable with keyboard focus and horizontal table scrolling.

## Phase 9B.1 Contrast Polish

Browser review found that the shared suite navigation inherited the global dashboard link color, creating dark blue text on the deep navy navigation background. Phase 9B.1 corrected the shared navigation selectors so inactive links use near-white text, hover and keyboard-focus states add visible border/background treatment, and the active page uses white text on a lighter navy pill with a restrained red underline accent.

Remaining manual QA should still include dense-table readability, mobile nav wrapping, and print preview checks across all staffing pages.

## Deferred Ideas

- Add official CMS status indicators only after documented facility-level sources are obtained for Special Focus Facility, Special Focus Facility candidate, Abuse Icon, or deficiency/citation scope and severity.
- Consider a future `Prepare ChatGPT Review` copy/prompt helper only after separate approval. It should summarize visible metrics and caveats and should not embed an API key or live AI call in the static site.
