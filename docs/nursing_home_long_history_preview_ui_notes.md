# Long-History Preview UI Notes

Phase 10C.5 added an unlinked development preview for long-history PBJ behavior:

`tools/testing/nursing-home-long-history-preview.html`

Supporting preview asset:

`Assets/nursing-home-long-history-preview.js`

Preview data:

`data/testing/nursing_home_staffing_history_ct_2017q4_2025q4_preview.json`

This preview is not linked from the homepage or suite navigation and is not a public cutover.

## What The Preview Exercises

- Facility-level long-history PBJ trend behavior.
- Latest 8 quarters versus full PBJ history display.
- CT threshold display states:
  - applicable
  - partial-period context
  - reference-only
- Change-over-time start/end quarter behavior.
- Preset windows:
  - latest 4 quarters
  - latest 8 quarters
  - full available PBJ history
  - custom selected quarters
- Persistent-pattern windowing with:
  - selected analysis window
  - minimum matching quarter count
  - minimum share of eligible quarters
  - denominator text
- Ownership/affiliation historical framing caveat.

## Preview Limitations

- It is intentionally simple and not final visual design.
- It does not alter public tools.
- It does not implement final cutover logic.
- It does not load current CMS ratings, QMs, case-mix, or affiliation data as historical context.
- It does not implement final print/export behavior.

## Recommended UX Direction

Facility:

- Latest 8 quarters should be the default chart/table window.
- Full history should be explicit and user-initiated.
- Current CMS context should remain visually separate from historical PBJ.

Change Over Time:

- Latest 8 quarters is the better default than oldest-to-latest.
- Full history should be an explicit preset, not the default.

Persistent Patterns:

- Latest 8 quarters should be the default window.
- Thresholds should include both count and share of eligible quarters.
- Full-history persistence should report variable denominators clearly.

Ownership / Affiliation:

- Historical PBJ grouped by current affiliation should be labeled as current-snapshot grouping until historic affiliation snapshots exist.
