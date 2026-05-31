# Long-History Data Contract Recommendation

Phase 10C.5 recommends separating long-range PBJ staffing history from current contextual CMS snapshots before any public historical cutover.

## Problem To Avoid

The temporary full-history build proved that `2017Q4` through `2025Q4` PBJ staffing rows can be generated and audited. However, the same temporary output also attached current contextual files:

- CMS Provider Information: April 2026
- CMS Quality Measures Claims: April 2026
- CMS SNF Enrollments: May 2026

Those contextual files are useful current facility context, but they are not historically aligned with each PBJ quarter from 2017 through 2025.

## Recommended File Structure

### 1. Current Dashboard Export

Keep the current public file unchanged until cutover:

`data/nursing_home_staffing_ct.json`

Purpose:

- Fast current/recent public dashboard experience.
- Latest/recent PBJ staffing display.
- Current Provider Information/rating context.
- Current Quality Measures Claims context.
- Current SNF Enrollment affiliation context.

### 2. PBJ-Only Historical Staffing Export

Preview created in Phase 10C.5:

`data/testing/nursing_home_staffing_history_ct_2017q4_2025q4_preview.json`

Recommended future public shape:

```json
{
  "dataset_type": "nursing_home_staffing_history",
  "history_window": {},
  "sources": [],
  "facility_quarterly_staffing_history": []
}
```

Each historical row should include:

- `ccn`
- PBJ facility name and city for that quarter
- `quarter`, `quarter_start_date`, `quarter_end_date`
- resident days and average census
- PBJ-derived staffing metrics
- data-quality fields
- CT comparison display/applicability fields after effective-date methodology is finalized

It should not include or imply quarter-specific historical values for:

- April 2026 CMS ratings
- April 2026 case-mix comparison points
- April 2026 Quality Measures Claims
- May 2026 SNF Enrollment affiliation entities

### 3. Current Context Object Or File

A later cutover can expose a separate current context object:

```json
{
  "facility_current_context": [],
  "source_snapshots": {}
}
```

This can contain:

- current Provider Information fields
- current CMS Care Compare ratings
- current CMS case-mix comparison point
- current Quality Measures Claims rows
- current SNF Enrollment affiliation context
- source snapshot dates and caveats

### 4. Historically Aligned Events Or Snapshots

Future historically aligned files should be separate until validated:

```json
{
  "historically_aligned_events_or_snapshots": []
}
```

Candidates:

- historical Provider Information/rating snapshots
- historical Quality Measures snapshots
- historical SNF Enrollment or ownership snapshots
- CMS SFF/Candidate statuses over time
- CHOW/ownership changes
- CT DPH leadership role periods
- CT DSS rate, census, and financial context

## Loading Strategy

Use `data/nursing_home_staffing_ct.json` for normal page load. Lazy-load the PBJ-only historical file only when a user opens a full-history view, selects a historical analysis window, or downloads full-history staffing data.

This avoids slowing every public page and reduces the chance that current-context snapshots are interpreted as historical quarter data.

## Page Behavior

Facility Explorer:

- Load current dashboard JSON first.
- Lazy-load historical PBJ when the user requests full history.
- Keep current CMS ratings/QMs/affiliation in a clearly labeled current-context panel.

Statewide Comparison:

- Remain latest-quarter by default.
- A future quarter selector can use historical PBJ rows without copying current context into old quarters.

Change Over Time:

- Use historical PBJ file for selected start/end windows.
- Do not default to oldest-to-latest once 33 quarters are available.

Persistent Patterns:

- Use historical PBJ file for selected windows.
- Disable historic case-mix patterns unless historically aligned Provider Information snapshots exist.

Ownership / Affiliation:

- Use current affiliation context only with explicit language unless historical affiliation snapshots exist.

## Preview Export

The Phase 10C.5 preview PBJ-only file includes 6,569 facility-quarter rows and is not used by the public application.

It is intentionally marked:

`publication_status: preview_only_not_public_runtime`
