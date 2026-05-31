# Connecticut Staffing Threshold Historical Applicability

Phase 10C.5 reviewed whether the project should publicly label historical PBJ quarters from `2017Q4` through `2025Q4` as below the Connecticut 3.00 total direct-care and 0.84 licensed nursing comparison points.

## Sources Reviewed

- Connecticut regulations, Title 19, Sec. 19-13-D8t, subsection (m): `https://portal.ct.gov/-/media/sots/regulations/title_19/013dpdf.pdf?la=en`
- Connecticut DPH Blast Fax 2022-14, Nursing Home Minimum Staffing Level Requirements: `https://portal.ct.gov/-/media/Departments-and-Agencies/DPH/Facility-Licensing--Investigations/Blast-Faxes/2022/Blast-Fax-2022-14-Nursing-Home-Staffing-Level-Requirements.pdf`
- Connecticut General Statutes Sec. 19a-563h / P.A. 21-185: `https://www.cga.ct.gov/2022/sup/chap_368v.htm`
- Connecticut DPH Blast Fax 2024-3A, Amendments to Policies and Procedures Implementing 3.0 Staffing Ratio: `https://portal.ct.gov/-/media/departments-and-agencies/dph/facility-licensing--investigations/blast-faxes/2024/blast-fax-2024-3a--amendments-to-policies-and-procedures-implementing-30-staffing-revised.pdf`

## Findings

### Pre-3.0 Regulatory Baseline

The older Title 19, Sec. 19-13-D8t(m) text sets chronic and convalescent nursing home minimums of:

- Licensed nursing personnel: 0.47 hours from 7 a.m. to 9 p.m. plus 0.17 hours from 9 p.m. to 7 a.m., totaling 0.64 hours per patient day.
- Total nursing and nurse's aide personnel: 1.40 hours from 7 a.m. to 9 p.m. plus 0.50 hours from 9 p.m. to 7 a.m., totaling 1.90 hours per patient day.

The same subsection excludes director of nurses time in facilities of 61 beds or more and assistant director of nurses time in facilities of 121 beds or more from satisfying those staffing minimums.

Because these older numeric thresholds differ from 3.00 and 0.84, quarters before the 3.00 policy became applicable should not be labeled as below an applicable 3.00/0.84 Connecticut staffing comparison point.

### 2022 Public Act / DPH Notice

P.A. 21-185 directed DPH to establish minimum staffing level requirements of three hours of direct care per resident per day by January 1, 2022. DPH Blast Fax 2022-14 repeated that statutory direction, but also stated that regulatory revisions would not be in place by January 1, 2022 and encouraged nursing homes to begin complying so they could be prepared for adoption of new regulations.

This is enough to document the statutory direction and planning period, but it is not enough for this project to publish period-specific below-3.00/0.84 flags for 2022 quarters without additional legal/DPH confirmation of enforceable implementation timing.

### March 1, 2023 Former Policies

DPH Blast Fax 2024-3A states that now-former policies and procedures had been effective as of March 1, 2023. Those former policies required:

- 0.84 hours of nursing care per resident per day.
- 2.16 hours of nurse aide services per resident per day.

Together, those former policies total 3.00 hours per resident day, but with separate category-specific minimums.

### January 5, 2024 Amended Policies

DPH Blast Fax 2024-3A states that amended policies and procedures became effective January 5, 2024. The amended policies require:

- 3.0 hours of total nursing and nurse aide care.
- 0.84 hours of that care provided by licensed nursing personnel.

The amended policies preserved the 3.0 minimum staffing ratio for direct-care services but changed allocation discretion compared with the March 1, 2023 former policies.

## Historical Applicability Decision For Publication Planning

Recommended display rule for future public historical PBJ release:

| PBJ quarter period | Recommended status display |
|---|---|
| 2017Q4-2021Q4 | Do not label as below applicable CT 3.00/0.84 comparison point. If shown, label 3.00/0.84 only as a retrospective current-reference comparison. |
| 2022Q1-2022Q4 | Do not publish applicable below-threshold flags until legal/DPH confirmation resolves the statutory direction versus implementation-status question. |
| 2023Q1 | Treat as a partial-period policy quarter because March 1, 2023 falls inside the quarter. Avoid a simple quarter-level applicable/not-applicable flag unless a day-weighted or explicit partial-period method is adopted. |
| 2023Q2-2023Q4 | Full-quarter period where the March 1, 2023 former policies appear applicable. CT 3.00 total and 0.84 licensed flags may be shown as PBJ-derived screening estimates if caveated. |
| 2024Q1 | January 5, 2024 falls inside the quarter, but the 3.00/0.84 framework continues from the former policies into the amended policies. Show with caveat if needed. |
| 2024Q2 forward | Full-quarter period where the amended 3.0/0.84 policies appear applicable. CT comparison flags may be shown as PBJ-derived screening estimates if caveated. |

Conservative implementation rule:

- For public quarter-level CT comparison status, start full-quarter applicable display at `2023Q2`.
- Treat `2023Q1` as partial-period context.
- Treat pre-`2023Q1` periods as retrospective reference only unless a legal review confirms a different enforceable applicability date.

## Future Data Fields

Historical rows should eventually include or be accompanied by:

- `ct_comparison_applicable_for_quarter`
- `ct_comparison_effective_date`
- `ct_comparison_display_status`
- `ct_comparison_reference_only_before_effective_date`
- `ct_comparison_partial_period_note`

These fields should control display language before any long-history public cutover.

## Guardrail

The PBJ-derived CT direct-care estimates remain screening estimates. They are not formal DPH compliance findings, do not establish violations, and do not account for every regulatory nuance or facility-specific enforcement judgment.
