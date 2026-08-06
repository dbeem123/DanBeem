# Nursing Home Survey and Enforcement Summary Build Audit

## Scope

Phase 11D.17 created a compact facility-level Connecticut survey and enforcement summary for future Facility Explorer and Advanced Facility Dossier use. This phase created and audited data only; it did not wire the summary into the public UI.

## Source Files

The builder used only existing repository JSON files:

- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_penalties_ct.json`

No raw CMS source files were read by the summary builder.

## Build and Output

Commands:

```text
python -m py_compile scripts/build_nursing_home_survey_enforcement_summary_ct.py
python scripts/build_nursing_home_survey_enforcement_summary_ct.py
git diff --check
git status --short --branch
```

Output: `data/nursing_home_survey_enforcement_summary_ct.json`

- Exact output size: 322,951 bytes.
- Current facility count: 196.
- Summary row count: 196.
- Every current staffing CCN appears exactly once, including facilities with no survey or enforcement records in these inputs.
- CCNs remain six-character strings and preserve leading zeros.
- Rows are sorted by provider name and then CCN.

## Source Join Coverage

| Detailed source | Rows | Unique source CCNs | Joined current CCNs | Unmatched source CCNs |
| --- | ---: | ---: | ---: | ---: |
| Health deficiencies | 6,761 | 191 | 191 | 0 |
| Fire safety and emergency preparedness deficiencies | 2,135 | 178 | 178 | 0 |
| Penalties and enforcement | 179 | 102 | 102 | 0 |

Facilities represented by source:

- Health records: 191.
- Fire safety or emergency preparedness records: 178.
- Penalty or enforcement records: 102.
- No records in any of these three detailed runtime sources: 5.

## Recent Window

The shared recent window is **2023-03-31 through 2026-03-31, inclusive**.

The anchor is 2026-03-31, the maximum survey or event date across all three detailed runtime datasets. The start is three calendar years before that anchor. Health and fire safety rows use survey date; penalties use penalty date. Applying one shared window keeps cross-source summary counts interpretable.

## Aggregate Reconciliation

### All-Time Totals Within Available Sources

| Measure | Total |
| --- | ---: |
| Health deficiency citations | 6,761 |
| Health actual-harm citations | 172 |
| Health immediate-jeopardy citations | 73 |
| Fire safety K-tag citations | 2,007 |
| Emergency preparedness E-tag citations | 128 |
| Enforcement events | 179 |
| Fines | 167 |
| Fine total | $3,925,517.00 |
| Payment denials | 12 |
| Payment-denial days | 368 |

### Recent Totals

| Measure | Total |
| --- | ---: |
| Health deficiency citations | 4,717 |
| Health actual-harm citations | 141 |
| Health immediate-jeopardy citations | 66 |
| Fire safety K-tag citations | 1,151 |
| Emergency preparedness E-tag citations | 57 |
| Enforcement events | 179 |
| Fines | 167 |
| Fine total | $3,925,517.00 |
| Payment denials | 12 |
| Payment-denial days | 368 |

All penalty rows fall within the shared recent window because the available penalties dataset begins on 2023-05-17.

## Interpretation and Limitations

- These counts reflect the available rolling sources and are not complete lifetime histories.
- Citation counts are context, not a complete quality measure.
- Fine amounts and payment denials are enforcement values, not quality scores.
- The summary does not calculate a composite quality score or rank facilities.
- Staffing and survey/enforcement measures remain separate.
- Health F-tag harm and immediate-jeopardy grouping is applied only to health deficiencies, never to fire safety or emergency preparedness rows.
- CMS citation-description lookup gaps for K-0211 (143 rows) and K-0133 (2 rows) remain documented in summary metadata.
- Duplicate penalty rows remain preserved, consistent with the audited detailed runtime file.
- County is unavailable in current staffing facility records, so `county_name` is null.

## Runtime Behavior

No JavaScript, HTML, staffing JSON, historical PBJ JSON, geography JSON, facility-status review JSON, staffing formulas, or raw CMS source files were changed. The summary JSON is not yet wired into the public UI, so public runtime behavior is unchanged.

## Recommendation

Proceed to Phase 11D.18: prototype the Facility Explorer survey and enforcement snapshot using only this compact summary JSON. Keep detailed citation and enforcement files unloaded by default, and retain the source-window, non-score, and lookup-gap caveats in the proposed UI wording.
