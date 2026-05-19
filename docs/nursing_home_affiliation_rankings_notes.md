# Connecticut Nursing Home Affiliation Comparison Notes

## Purpose

The Ownership / Affiliation Staffing Explorer includes statewide affiliation comparison tables for Connecticut nursing homes with a nonblank CMS SNF Enrollment `affiliation_entity_name`.

These tables are staffing screening views. They are not chain quality rankings, legal findings, or determinations of regulatory compliance.

## Sources

- CMS Payroll-Based Journal Daily Nurse Staffing data from the generated Connecticut export.
- CMS Nursing Home Provider Information case-mix benchmark fields where matched by CCN.
- CMS Skilled Nursing Facility Enrollments affiliation entity fields where matched by CCN.

## Grouping

Facilities are grouped by raw nonblank `affiliation_entity_name` from CMS SNF Enrollments. The Phase 4C affiliation entity audit found 108 Connecticut facilities with nonblank affiliation names, 19 unique affiliation entities, and no name/ID issues requiring a normalization layer before statewide comparison.

The raw `affiliation_entity_name` and `affiliation_entity_id` fields remain the grouping source. Facilities without a nonblank affiliation name are counted in the dataset summary but are not included in affiliation comparison rows.

## Deep Links

The ownership explorer supports `?affiliation=` deep links. Facility pages link to the ownership explorer using the CMS SNF Enrollment `affiliation_entity_id` when it is available, with the raw affiliation name as a fallback. The ownership explorer matches deep links by affiliation entity ID first and then by affiliation name for compatibility.

Ownership explorer facility links use `?ccn=` to open the corresponding facility in the facility-level Nursing Home Staffing Explorer.

## Reporting Exports

The selected-affiliation section includes client-side reporting actions:

- print affiliation summary
- download latest-quarter facility comparison CSV
- download five-quarter trend CSV

The print summary is intended for briefing and review preparation. It emphasizes the selected affiliation entity, latest-quarter context, CT facility count, group summary metrics, CT direct-care comparison counts/shares, five-quarter pattern context, and the latest-quarter facility comparison table.

CSV exports use the existing generated JSON in the browser. Missing values remain blank rather than being converted to zero. The facility comparison CSV contains one row per linked facility for the latest quarter. The five-quarter trend CSV contains one row per quarter for the selected affiliation entity and does not fabricate missing facility-quarter rows.

Export labels avoid chain quality language. The outputs should be described as affiliation staffing summaries or facility comparisons, not report cards or compliance findings.

## Latest-Quarter Table

The latest-quarter statewide table shows one row per affiliation entity with latest-quarter PBJ data. As of the current export, the latest quarter is 2025Q4.

Columns include:

- affiliation entity name
- Connecticut facilities in group
- facilities with latest-quarter PBJ data
- average total nurse HPRD
- average RN HPRD
- average CT direct-care total HPRD estimate
- count/share below the CT 3.00 direct-care comparison point
- average CT licensed direct-care HPRD estimate
- count/share below the CT 0.84 licensed nursing comparison point
- average contract staff percentage
- average case-mix total nurse benchmark when available
- average actual total nurse HPRD minus case-mix benchmark when available

The default sort shows the highest share of linked facilities below the CT 3.00 direct-care comparison point first, then larger Connecticut groups, then lower average CT direct-care total HPRD. This ordering is intended to surface potential staffing screening questions quickly. It should not be read as a definitive chain quality ranking.

Groups with only 1 or 2 linked Connecticut facilities remain visible and are labeled as small CT groups in the page. Their percentages can be unstable and less generalizable than larger groups.

## Five-Quarter Pattern Summary

The compact five-quarter summary uses all available facility-quarter rows in the generated Connecticut export, currently 2024Q4 through 2025Q4. Missing facility-quarter rows are not treated as zero. It shows:

- five-quarter average CT direct-care total HPRD estimate
- count/share of facility-quarter rows below the CT 3.00 direct-care comparison point
- five-quarter average contract staff percentage

## Aggregation Choice

Phase 4D uses simple facility averages, consistent with the existing ownership explorer. It does not resident-day weight affiliation averages.

This keeps the view easy to explain and makes each linked Connecticut facility count once in group averages. A resident-day weighted alternative may be useful in a later phase, especially for statewide policy summaries where larger facilities should have proportionally larger influence.

## Interpretation Limits

Shared affiliation does not prove identical operations, uniform decision-making, common control, poor care, harm, neglect, or violations.

Connecticut direct-care comparison fields are PBJ-derived screening estimates. They exclude nursing administration / DON-style hours and are not formal Connecticut Department of Public Health compliance findings.

Provider Information case-mix benchmarks are contextual comparison points and should not be treated as quarter-specific benchmark snapshots for every PBJ quarter.
