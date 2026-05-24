# Nursing Home Staffing History Calculation Audit

## Conclusion

**Historical PBJ calculations and CT applicability fields validated.**

- History file: `data\nursing_home_staffing_history_ct.json`
- Quarters: 33 (2017Q4 through 2025Q4)
- Facilities: 216
- Facility-quarter rows: 6569
- Raw Connecticut PBJ daily rows re-read: 599930

## Independent Calculation Comparison

- Rows compared: 6569
- Missing generated rows: 0
- Extra generated rows: 0
- Total field mismatches: 0

## CT Applicability Field Audit

- Full-quarter applicable rows: 2145
- Non-applicable/reference/transitional rows: 4424
- Status mismatches: 0

## Current Context Separation Audit

- Forbidden current-context field hits in history rows: 0

The historical export is PBJ-only and does not embed CMS ratings, Quality Measures Claims, case-mix benchmark fields, or SNF Enrollment affiliation fields as quarter-specific historical values.
