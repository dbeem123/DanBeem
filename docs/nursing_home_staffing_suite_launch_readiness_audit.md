# Connecticut Nursing Home Staffing Transparency Suite Launch-Readiness Audit

Generated during Phase 7A on 2026-05-20.

Phase 7B follow-up note: the terminology variants and homepage staffing-suite overview recommended in this audit were addressed after this report was created. The observations below remain useful as the historical launch-readiness baseline.

## Bottom Line

The Connecticut Nursing Home Staffing Transparency suite is coherent enough for deeper browser/manual launch review. The five tools now form a recognizable product family: facility detail, latest-quarter statewide scan, change over time, persistent multi-quarter patterns, and ownership/affiliation grouping. The strongest launch-readiness strengths are consistent static-data architecture, shared caution language, facility drill-down pathways, and increasingly useful print/export/reporting actions.

The main remaining risks are not calculation or data-contract issues. They are product-polish and QA risks: dense wide tables, uneven top-level navigation in a few pages before this audit, some terminology variants, and documentation that still partly reflects earlier phases instead of the full five-tool suite.

## 1. Tool Inventory And Purpose

| Tool | Purpose | Primary user question | Inputs / scope | Key outputs | Navigation relationships |
|---|---|---|---|---|---|
| Facility Staffing Explorer | Facility-level PBJ staffing detail and trend context. | "What does this facility's staffing pattern look like across the available quarters?" | `data/nursing_home_staffing_ct.json`; facility directory; facility-quarter PBJ metrics; Provider Information case-mix fields; SNF Enrollment affiliation fields. | Facility summary, latest metrics, quarter table, CT direct-care screening estimates, case-mix comparison, ownership/affiliation context, print summary, facility trend CSV. | Accepts `?ccn=` deep links from statewide, change, persistent, and ownership tables. Links to ownership/affiliation summary when affiliation fields are present. Top navigation now links to the related staffing tools. |
| Statewide Facility Staffing Comparison | Latest-quarter statewide scan across facilities. | "Which facilities stand out in the latest quarter under selected filters/sorts?" | Latest quarter from generated JSON, currently 2025Q4. | Search/filter/sort table, filtered-view summary, print current statewide view, filtered CSV, facility links. | Links to facility explorer by `?ccn=`. Top navigation links to facility and ownership; adding links to change/persistent would make it fully parallel. |
| Staffing Change Over Time Explorer | Earliest-to-latest change scan. | "Which facilities changed most across the current data window?" | Facilities with both endpoint rows across current window, currently 2024Q4 to 2025Q4. | Change modes, filters, filtered summary, print current change view, CSV, facility trend links. | Links to facility explorer by `?ccn=`. Top navigation links to facility, statewide, ownership, responsible use. |
| Persistent Multi-Quarter Staffing Patterns | Repeated pattern scan across quarters. | "Which facilities repeatedly match a selected staffing screening pattern?" | All available facility-quarter rows across current window, currently 2024Q4 to 2025Q4. | Pattern modes, threshold control, quarter-by-quarter strip, search/filters, print current persistent-pattern view, CSV, facility links. | Accepts query parameters for `mode`, `threshold`, and `affiliation`. Links to facility explorer by `?ccn=` and is linked from the ownership persistence table. |
| Ownership / Affiliation Staffing Explorer | Staffing grouped by CMS SNF Enrollment affiliation entity. | "What patterns appear among Connecticut facilities connected to the same CMS affiliation entity?" | Facilities with nonblank `affiliation_entity_name`; latest-quarter and multi-quarter PBJ rows; Provider Information; SNF Enrollments. Current export has 108 facilities across 19 affiliation entities. | Statewide affiliation comparison, selected-affiliation detail, group trend, facility comparison, affiliation persistent-pattern table, CSV/print/copy actions. | Accepts `?affiliation=` by ID or name. Links to facility explorer and persistent-pattern table. Top navigation now links to the related staffing tools. |

## 2. Navigation And Discoverability

The landing page lists all five staffing tools in a sensible sequence: facility detail, statewide latest-quarter comparison, change over time, persistent patterns, then ownership/affiliation. This order supports a natural user path from individual facility review to broader scans and affiliation context.

The tool titles are mostly clear. The facility page had the weakest title because it omitted "Connecticut"; this audit updated the HTML title, brand label, H1, and footer to "Connecticut Nursing Home Staffing Explorer."

Cross-navigation is good but not perfectly symmetrical:

- Affiliation to facility: present through selected-affiliation facility links and persistence matching facility links.
- Facility to affiliation: present when CMS SNF Enrollment affiliation fields are available.
- Affiliation persistence to persistent pattern table: present through query links with mode, threshold, and affiliation.
- Statewide table to facility: present through facility detail links.
- Change-over-time to facility: present through facility trend links.
- Persistent pattern table to facility: present through facility links.

Small cleanup completed in this phase:

- Added Statewide Comparison, Staffing Change, Persistent Patterns, and Ownership Staffing links to the Facility Staffing top navigation.
- Added Statewide Comparison, Staffing Change, and Persistent Patterns links to the Ownership / Affiliation top navigation.

Helpful future cross-links:

- Add Change and Persistent Pattern links to the Statewide Comparison top navigation for full parity.
- Add a small "Start with..." orientation on the landing page so public users know when to use each staffing tool.
- Consider a suite overview page if the five-tool set becomes the public launch path rather than a test-environment collection.

## 3. Terminology Consistency

Generally consistent terms:

- "PBJ staffing" and "quarterly screening data"
- "CT direct-care HPRD" / "CT direct-care HPRD estimate"
- "CT 3.00 direct-care comparison point"
- "CT 0.84 licensed comparison point"
- "case-mix comparison point"
- "affiliation entity"
- "screening estimate" / "screening indicator"
- "not a formal DPH compliance finding"

Potentially confusing variants to smooth later:

- Some UI labels shorten "CT 3.00 direct-care comparison point" to "CT 3.00 comparison point." This is understandable in compact controls, but full explanatory text should use "direct-care."
- Persistent-pattern code labels include "Below CT 0.84 licensed direct-care comparison point" while other pages say "CT 0.84 licensed comparison point." Recommended standard: "CT 0.84 licensed comparison point" or "CT 0.84 licensed nursing comparison point."
- The facility explorer still uses the phrase "Connecticut PBJ - CY2025 Q4" in a static pill. The data is currently latest quarter 2025Q4, but the suite increasingly describes data windows dynamically. Consider deriving that pill from JSON in a later polish pass.
- "Case-mix point," "case-mix comparison," and "case-mix comparison point" all appear. The preferred public-facing form should be "CMS case-mix total nurse comparison point" on first mention and "case-mix comparison point" afterward.

## 4. Disclaimer / Guardrail Consistency

Core caveats are present across the suite:

| Caveat | Where it appears | Assessment |
|---|---|---|
| PBJ data are quarterly screening data. | Facility hero/source note; statewide hero/print; change hero/print; persistent hero/print; README/docs. | Strong coverage. |
| CT comparison values are PBJ-derived estimates, not formal DPH compliance findings. | Statewide hero/interpretation/print; change interpretation/print; persistent interpretation/print; ownership selected metrics/source note; README/docs. | Strong coverage. Facility page says not compliance/harm findings, but could more explicitly say "not formal DPH compliance findings" near the CT direct-care card if desired. |
| Case-mix points come from CMS Provider Information and are contextual, not actual staffing or legal minimums. | Facility benchmark explainer; ownership source note and case-mix group copy; README/data contract. Statewide print says Provider Information contextual comparison points. | Strong coverage after recent refinement. |
| Affiliation entity grouping comes from CMS SNF Enrollments and does not prove common operational control. | Ownership hero, interpretation, source notes, print/copy/export docs; affiliation audit/ranking notes. | Strong coverage in ownership tool. Other tools show affiliation as a filter/context field but do not need the full caveat on every screen. |
| Missing rows are not treated as zero/adverse findings. | Facility missing-quarter rows; change hero/print; persistent hero/interpretation/print; ownership trend and persistence notes. | Good coverage. Statewide latest-quarter table explains facilities without latest row are excluded. |
| Staffing data alone do not prove poor care, neglect, harm, or violations. | Facility hero/source note; statewide hero/print; change hero/print; persistent hero/interpretation; ownership hero/source/persistence/copy. | Strong coverage. |

The caveat language is intentionally repetitive, which is appropriate for a public-facing screening suite where users may enter through any page. The most repetitive area is ownership, where multiple sections carry similar affiliation and case-mix caveats. That is acceptable for launch review, but a future design pass could centralize some caveats into a compact "How to interpret this page" disclosure.

## 5. Print / Export / Copy Action Consistency

Button labels are clear and mostly parallel:

- Facility: "Print facility staffing summary"; "Download facility five-quarter trend CSV"
- Ownership selected group: "Print affiliation summary"; "Download facility comparison CSV"; "Download five-quarter trend CSV"
- Statewide: "Print current statewide view"; "Download filtered statewide comparison CSV"
- Change: "Print current change view"; "Download current change table CSV"
- Persistent patterns: "Print current persistent-pattern view"; "Download current persistent-pattern table CSV"
- Ownership persistence: "Download affiliation persistence table CSV"; "Print affiliation persistence view"; "Copy briefing summary"

Behavioral consistency:

- Current-view print/export actions generally capture the active filters, modes, thresholds, or selected entity.
- CSV filenames are descriptive and safe-slugged in the newer tools.
- Empty-state disabling is implemented in the current-view tools; messages vary slightly but are understandable.
- The new copy briefing summary follows the current ownership persistence table state and falls back to an on-page textarea if the clipboard API is unavailable.

Possible future polish:

- Standardize label order as "Print..." then "Download..." then "Copy..." where multiple actions sit together. The ownership persistence section currently places CSV before print because Phase 6D added export first. This is not a launch blocker.
- Add copy briefing summaries to statewide, change, and persistent-pattern views if report-writing becomes a common workflow.

## 6. Data Scope And Freshness Visibility

Current generated data:

- Generated timestamp: `2026-05-19T12:59:17`
- Quarter window: `2024Q4` through `2025Q4`
- Latest quarter: `2025Q4` / Q4 2025
- Facilities: 196
- Facility-quarter rows: 966
- Facilities with nonblank affiliation names: 108
- Unique affiliation entities: 19
- Sources: CMS Payroll-Based Journal Daily Nurse Staffing, CMS Nursing Home Provider Information, CMS Skilled Nursing Facility Enrollments.

Visibility by page:

- Facility: shows dataset summary dynamically and source notes, but the hero pill is hardcoded to "CY2025 Q4." Recommend deriving this from `reporting_period` later.
- Statewide: clearly shows latest quarter and generated export context in status/print.
- Change: clearly explains the derived earliest-to-latest window and print context includes generated timestamp.
- Persistent patterns: clearly states the quarter window and generated timestamp in print context.
- Ownership: dataset summary and print contexts show source/data context; selected group and persistence views explain latest-quarter and multi-quarter scope.

Users can generally understand this is a static generated export, not live CMS polling. README makes this explicit. A short shared footer phrase such as "static generated export; not live CMS polling" could make that clearer on every page.

## 7. Table Density And Responsive Risk Inventory

Browser/manual review priorities:

- Facility Explorer: quarterly table plus metric cards; verify missing-quarter rows, benchmark explainer, and print summary on mobile and desktop.
- Statewide Comparison: wide latest-quarter table with many columns; verify horizontal scroll, sticky reading order if any, keyboard focus inside table scroll, and print readability.
- Change Over Time: wide ranking table and mode controls; verify mode labels wrap cleanly and print report keeps context plus table readable.
- Persistent Patterns: quarter pattern strip plus wide table; verify marker labels remain readable on mobile, tooltips/aria labels are present, and color is not the only signal.
- Ownership / Affiliation: densest page. It contains statewide affiliation table, persistence table, selector, selected-group cards, trend table, and facility comparison. Verify navigation jumps, print-only persistence mode, copy fallback textarea, and small-screen table scrolling.

Accessibility/keyboard review priorities:

- All table-scroll containers with `tabindex="0"` should be keyboard reachable without trapping focus.
- Mode button groups should announce pressed state consistently.
- Dynamic status regions should update without excessive chatter.
- Quarter pattern markers should be checked with screen-reader tooling because they combine compact visible labels with aria/title text.
- Clipboard fallback textarea should be reachable and selected when clipboard copy fails.

## 8. Existing Audit And Documentation Coverage

Current docs cover the main foundations:

- `docs/nursing_home_staffing_data_contract.md`: data contract, generated fields, formulas, benchmark fields. Coverage is strong; ensure it remains current if future UI-only fields become data fields.
- `docs/nursing_home_staffing_calculation_audit.md`: independent calculation audit confirming generated metrics and counts. Coverage is strong for formulas and enrichment counts.
- `docs/nursing_home_staffing_current_state_feature_audit.md`: useful historical feature audit, but it primarily reflects the original facility and ownership explorer baseline. It does not fully cover the later statewide, change, persistent-pattern, and affiliation persistence reporting phases.
- `docs/nursing_home_affiliation_entity_audit.md`: covers affiliation entity source quality and grouping readiness. Still relevant.
- `docs/nursing_home_affiliation_rankings_notes.md`: current and useful for ownership/affiliation ranking and persistence behavior, including reporting actions.
- `README.md`: now lists all five tools and summarizes current features, but the "Phase 2 Data Architecture" section still reads partly historical/mock-oriented. Not a blocker, but could be reorganized into "Current Static Data Architecture" before public launch.
- `data/current_tool_context_registry.json`: now reflects the Phase 6E ownership reporting state and updated facility role wording.

Documentation gap:

- There is no single public or internal "staffing suite overview" explaining how the five tools fit together, which tool to start with, and which links move between levels. This Phase 7A audit partly fills that internal gap, but a shorter user-facing overview would help launch discoverability.

## 9. Small Cleanup Fixes Made

This phase made only low-risk cleanup changes:

- Updated the Facility Staffing Explorer title, meta description, brand label, H1, and footer to include "Connecticut."
- Added related staffing-tool links to the Facility Staffing Explorer top navigation.
- Added Statewide Comparison, Staffing Change, and Persistent Patterns links to the Ownership / Affiliation top navigation.
- Updated the facility explorer role text in `data/current_tool_context_registry.json` so it no longer describes the current tool as a local-mock prototype.

No formulas, data contract, persistence logic, CSV logic, print behavior, or generated data were changed.

## 10. Recommended Next Steps

1. Run a manual browser smoke-test checklist across all five tools on desktop and mobile widths, with special attention to wide tables, print views, query links, and keyboard navigation.
2. Do a platform-wide accessibility pass covering mode buttons, dynamic status regions, table scroll focus, quarter pattern strips, and print/copy controls.
3. Create a short staffing-suite overview or landing explainer that helps users choose between facility detail, statewide latest-quarter scan, change, persistent patterns, and ownership/affiliation grouping.
4. Standardize a few remaining terminology variants, especially "CT 0.84 licensed comparison point" and compact "CT 3.00 comparison point" labels.
5. Consider copy briefing summaries for the statewide, change-over-time, and persistent-pattern views after the current ownership persistence summary has been tested with real users.
