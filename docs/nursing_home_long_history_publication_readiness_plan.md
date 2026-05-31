# Long-History Publication Readiness Plan

Phase 10C.5 prepares the architecture and review checklist for publishing PBJ staffing history from `2017Q4` through `2025Q4`. It does not publish the full-history dataset.

## Required Before Public Cutover

| Requirement | Reason |
|---|---|
| Verified CT threshold applicability/effective-date logic | Prevents labeling pre-effective quarters as below a requirement that was not applicable during that period. |
| Data-contract separation or equivalent UI/data safeguard for current contextual snapshots | Prevents April/May 2026 ratings, QMs, case-mix, and affiliation data from appearing historically contemporaneous with older PBJ quarters. |
| Source-currency and methodology wording for historical PBJ versus current context | Users need to understand that PBJ history and contextual snapshots have different dates. |
| Removal/generalization of misleading fixed five-quarter language | Long-history windows should use "available quarters," "selected window," or dynamic labels. |
| Safe default behavior for Change Over Time | Automatic 2017Q4-to-latest comparison is not an appropriate default for public interpretation. |
| Safe default behavior for Persistent Patterns | 2+/3+/4+/5 thresholds are not adequate for 33 quarters without selected windows and denominators. |
| Performance/loading strategy | Full history should not slow every initial page load unnecessarily. |
| Final production historical export audit | The final public export must be independently audited after any contract changes. |

## Strongly Recommended Before Public Cutover

| Item | Reason |
|---|---|
| Preview browser testing at desktop and mobile widths | 33-quarter views stress chart, table, and scrolling behavior. |
| Print/export review for long-history tables | Print should stay concise; full-history CSV should remain usable. |
| Current-context snapshot callouts | Facility pages should explicitly label ratings, QMs, affiliation, and case-mix context as current snapshots. |
| Full-history CSV/download strategy | Users may need all quarters without rendering all rows on screen. |
| Quarter/name continuity review | CCNs with name changes need presentation that avoids implying they are different facilities solely because names changed. |

## May Be Deferred

- CT DPH governance timeline
- CMS SFF/Candidate status
- Abuse Icon verification
- Owner / Entity Explorer
- CT DSS rate, census, and financial context
- deficiencies and penalties
- historic ratings/QMs/affiliation snapshots

## Recommended Public Defaults

Facility Explorer:

- Display latest 8 quarters by default when history is live.
- Provide "View full PBJ staffing history" as an explicit action.
- Keep full-history CSV separate from default print summary.

Change Over Time:

- Default to latest 8 quarters.
- Offer latest 4 quarters, latest 8 quarters, full history, and custom start/end quarters.

Persistent Patterns:

- Default to latest 8 quarters.
- Support both count thresholds and share-of-eligible-quarter thresholds.
- Report denominators clearly.

Statewide Comparison:

- Remain latest-quarter by default.
- Add a quarter selector only after source-currency and current-context labeling are ready.

Ownership / Affiliation:

- Remain latest-quarter/current-window by default.
- If historical PBJ is grouped by current affiliation, label it as current-snapshot grouping.

## Cutover Decision

Historical PBJ is technically ready, but public cutover should wait until effective-date handling, contract separation, long-history UI windows, and methodology copy are implemented and audited.
