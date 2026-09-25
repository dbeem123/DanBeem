# Nursing Home Staffing History Calculation Audit

## Conclusion

**Historical PBJ calculations and CT applicability fields validated.**

- History file: `data/nursing_home_staffing_history_ct.json`
- Quarters: 34 (2017Q4 through 2026Q1)
- Facilities: 216
- Facility-quarter rows: 6759
- Raw Connecticut PBJ daily rows re-read: 617030

## Source Discovery

- Source root: `source_data\pbj`
- Target window: 2017Q4 through 2026Q1
- Expected target quarters: 34
- Discovered target quarters: 34
- Missing target quarters: 0
- Duplicate target quarters: 0
- Excluded out-of-window sources: 3
- Source inventory errors: 0

## Independent Calculation Comparison

- Rows compared: 6759
- Missing generated rows: 0
- Extra generated rows: 0
- Total field mismatches: 0

## CT Applicability Field Audit

- Full-quarter applicable rows: 2335
- Non-applicable/reference/transitional rows: 4424
- Status mismatches: 0

## Current Context Separation Audit

- Forbidden current-context field hits in history rows: 0

The historical export is PBJ-only and does not embed CMS ratings, Quality Measures Claims, case-mix benchmark fields, or SNF Enrollment affiliation fields as quarter-specific historical values.
