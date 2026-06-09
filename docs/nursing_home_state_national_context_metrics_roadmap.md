# State and National SNF Context Metrics Roadmap

Phase 11I planning addendum. This document is planning-only and does not change public UI, runtime JSON, generated data, staffing formulas, Connecticut applicability logic, or public tool behavior.

## Purpose

Future Connecticut nursing home facility dossiers and statewide views may benefit from limited state and national skilled nursing facility context metrics. These metrics should help consumers, ombudsman users, and policy users understand broader access, capacity, rurality, post-acute utilization, and survey/citation context without turning state-level statistics into facility-level findings.

The metrics in this document are not ready for runtime integration. Each requires a reproducible data source, clear denominator, source freshness record, audit trail, and careful labeling before use.

## Candidate Metrics

### 1. Average SNF Length of Stay by State

Purpose:

- Provide broad post-acute utilization context by state.
- Help users understand whether SNF stays are shorter or longer in a state-level Medicare or all-payer frame.

Likely source leads:

- CMS Medicare Post-Acute Care Utilization - Skilled Nursing Facility by Geography and Provider: <https://data.cms.gov/provider-summary-by-type-of-service/medicare-post-acute-care-hospice/medicare-post-acute-care-utilization-skilled-nursing-facility-by-geography-and-provider>
- CMS Medicare Post-Acute Care & Hospice public use files: <https://data.cms.gov/provider-summary-by-type-of-service/medicare-post-acute-care-hospice>
- MedPAC SNF payment policy reports and data books, including March 2026 SNF services chapter and post-acute care data book materials: <https://www.medpac.gov/document/march-2026-report-to-the-congress-medicare-payment-policy/>
- MACPAC nursing facility issue briefs, Medicaid payment analyses, and long-term services and supports context: <https://www.macpac.gov/subtopic/nursing-facilities/>
- LTCFocus, if state-level SNF utilization or stay-length fields are available and licensing permits use.
- Academic and policy literature using Medicare claims, MedPAR, Minimum Data Set, or post-acute claims.

Feasibility:

- Medium for Medicare FFS context if CMS PAC PUF fields support state-level aggregation.
- Low-to-medium for all-payer average SNF length of stay unless a reliable state-level source is found.

Denominator questions:

- Medicare fee-for-service SNF stays?
- Medicare Advantage plus FFS?
- all SNF stays?
- post-hospital SNF stays only?
- facility admissions, covered stays, episodes, or resident days?

Required before use:

- Define numerator and denominator.
- Distinguish Medicare-covered short-stay SNF use from long-stay nursing facility care.
- Decide whether state-level averages should be weighted by stays, days, residents, or facilities.
- Confirm whether the source supports Connecticut and national comparisons using the same method.

### 2. Harm and Immediate Jeopardy Deficiency Percentages by State

Purpose:

- Provide state-level survey/citation context related to actual harm and immediate jeopardy.
- Support policy-level review of survey outcomes while avoiding unsupported facility-level conclusions.

Likely source leads:

- Attached Summary Citations spreadsheet, if available and source provenance is confirmed.
- CMS Health Deficiencies dataset: <https://data.cms.gov/provider-data/dataset/r5ix-sfxw>
- CMS Fire Safety Deficiencies dataset through the CMS nursing homes Provider Data Catalog topic: <https://data.cms.gov/provider-data/topics/nursing-homes>
- CMS Citation Descriptions / Nursing Home Data Dictionary: <https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/nursing_home/NH_Data_Dictionary.pdf>
- CMS Nursing Home Enforcement scope/severity guidance: <https://www.cms.gov/medicare/health-safety-standards/enforcement/nursing-home-enforcement>
- KFF state indicator on nursing facilities with actual harm or immediate jeopardy deficiencies: <https://www.kff.org/other-health/state-indicator/nursing-facilities-receiving-deficiency-for-actual-harm-or-immediate-jeopardy/>
- LTCCC citations and penalties analyses as secondary source leads, not as a substitute for official CMS data.

Feasibility:

- Medium-high if CMS deficiency files include structured scope/severity fields and state/facility identifiers.
- Low if only narrative text is available.

Possible denominators:

- citation-level: harm/IJ citations divided by all citations.
- survey-level: surveys with at least one harm/IJ citation divided by surveys.
- facility-level: facilities with at least one harm/IJ citation divided by certified facilities.
- facility-year: facility-years with at least one harm/IJ citation divided by facility-years.

Required before use:

- Use structured severity/scope fields or official harm/IJ indicators.
- Do not infer harm or immediate jeopardy from narrative text alone unless structured fields support it.
- Decide whether fire-safety and health citations are included together or separately.
- Preserve survey date, citation date, correction status, and source snapshot date.

### 3. Rural Nursing Home Distribution by State

Purpose:

- Add access and geography context about rural, rural-adjacent, and remote rural nursing home capacity.
- Help Connecticut users understand whether a state or region has different rural/urban facility patterns.

Likely source leads:

- KFF "A Closer Look at Rural Nursing Homes": <https://www.kff.org/medicaid/a-closer-look-at-rural-nursing-homes/>
- KFF Figure 1 and underlying source notes for urban/rural/remote rural classification.
- CMS Provider Information, Provider Data Catalog, or Care Compare facility address/county fields.
- Rural-Urban Commuting Area (RUCA), USDA Rural-Urban Continuum Codes, NCHS urban-rural classification, or another public geography classification, depending on KFF's cited underlying source.
- "Changes in US Skilled Nursing Facility Capacity Following the COVID-19 Pandemic" for rural capacity-loss context: <https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2843861>

Desired categories:

- urban;
- rural adjacent;
- remote rural.

Desired measures:

- percent of SNF beds by state;
- percent of SNF residents by state;
- facility counts by rurality category;
- resident counts by rurality category if reproducible.

Feasibility:

- Medium if KFF source notes identify reproducible public geography inputs.
- Low if only static chart values are available.

Required before use:

- Identify and reproduce the underlying urban/rural classification.
- Decide whether to classify by facility address, county, ZIP, census tract, or another geography.
- Prefer reproducible public datasets over copying a static analysis.
- Keep rurality context distinct from care-quality conclusions.

### 4. Percent of Hospital Discharges Admitted to SNFs by State

Purpose:

- Provide post-acute access and hospital-transition context.
- Support policy-level understanding of how frequently hospital discharges move to SNF care.

Likely source leads:

- AHRQ HCUP discharge disposition variables and State Inpatient Databases: <https://hcup-us.ahrq.gov/db/vars/disp/nisnote.jsp>
- AHRQ HCUP Statistical Brief on hospital discharge to post-acute care: <https://hcup-us.ahrq.gov/reports/statbriefs/sb205-Hospital-Discharge-Postacute-Care.jsp>
- CMS Medicare claims / MedPAR / PAC PUF sources.
- MedPAC post-acute care data book and SNF payment policy reports.
- JAMA Network Open "Skilled Nursing Facility Network Capacity and Hospital Length of Stay": <https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2848405>
- Academic literature on post-acute discharge, SNF network capacity, and hospital length of stay.

Historical reference point:

- An AHA-era 1987 community hospital survey reportedly found approximately 6% of community hospital discharges to SNFs nationally. This should be treated only as historical context until the original source and denominator are verified. Current rates likely differ substantially.

Possible denominators:

- all hospital discharges;
- Medicare discharges;
- older adult discharges;
- community hospital discharges;
- acute-care inpatient discharges;
- condition-specific or surgical/medical discharge cohorts.

Feasibility:

- Medium for Medicare FFS if CMS or MedPAC sources provide state-level discharge-to-SNF measures.
- Medium-low for all-payer state estimates because HCUP SID access and state participation vary.

Required before use:

- Define denominator before comparing states.
- Distinguish discharge destination to SNF from later SNF utilization.
- Confirm whether Medicare Advantage is included.
- Avoid mixing all-payer HCUP estimates with Medicare-only CMS estimates without clear labels.

## Source Inventory Table

| Source lead | Metrics supported | Level | Feasibility | Caveats |
|---|---|---|---|---|
| CMS Medicare Post-Acute Care Utilization SNF by Geography and Provider | SNF utilization, payments, possible stays/days/length measures | provider, geography, state/national depending fields | Medium | Medicare-focused; denominator and MA/FFS scope must be confirmed. |
| CMS Medicare Post-Acute Care & Hospice PUF | SNF post-acute utilization context | provider, geography, national | Medium | Public-use aggregation may not support all desired denominators. |
| CMS Health Deficiencies | harm/IJ deficiency measures if scope/severity fields support it | citation, facility, state | Medium-high | Must define citation/survey/facility denominator. |
| CMS Fire Safety Deficiencies | fire-safety citation context | citation, facility, state | Medium | Should usually be analyzed separately from health deficiencies. |
| CMS Citation Descriptions and Data Dictionary | F-tag definitions and field meanings | reference | High | Lookup/reference only; not a facility finding by itself. |
| CMS Nursing Home Enforcement guidance | harm and immediate jeopardy interpretation | policy/reference | High | Guidance, not a numeric dataset. |
| KFF rural nursing home analysis | rural/urban nursing home distribution source lead | state/national | Medium | Use as lead; reproduce underlying data rather than copying chart values. |
| KFF actual harm/IJ state indicator | harm/IJ state-level source lead | state | Medium | Confirm source year, denominator, and whether data are reproducible. |
| MedPAC SNF and PAC reports | SNF LOS, Medicare utilization, PAC discharge context | national, sometimes state/market | Medium | Often Medicare FFS and national; state detail may be limited. |
| MACPAC nursing facility materials | Medicaid nursing facility context and possible state policy/payment context | state, national | To verify | Medicaid-focused; may not provide SNF length-of-stay denominators directly. |
| AHRQ HCUP SID/NIS discharge disposition | hospital discharge to SNF/post-acute care | discharge, hospital, state/national | Medium-low | SID access restrictions and state participation; denominator must be exact. |
| JAMA Internal Medicine SNF capacity article | SNF capacity decline and rural county context | county/national research | Medium as source lead | Journal analysis should guide research; underlying data/methods required before app use. |
| JAMA Network Open SNF network capacity/LOS article | hospital-SNF network and LOS context | market/national research | Medium as source lead | Not a direct state dashboard source; do not convert association into causation claims. |
| LTCFocus | possible SNF facility/state context | facility/state | To verify | Licensing, field availability, and reproducibility must be confirmed. |

## Feasibility Summary

| Metric | Likely denominator | Likely level | Feasibility | Possible app use |
|---|---|---|---|---|
| Average SNF length of stay by state | Medicare SNF stays or all SNF stays | state, national | Medium for Medicare; lower for all-payer | State/national context card in methodology or future policy dashboard. |
| Harm/IJ deficiency percentage by state | citation, survey, facility, or facility-year | state, national, facility-derived | Medium-high if structured fields are available | State context chart or source-linked survey context module. |
| Rural nursing home distribution by state | beds, residents, or facilities by rurality category | state, national | Medium if underlying rurality data are reproducible | Access/context section; not a facility quality measure. |
| Percent of hospital discharges admitted to SNFs by state | hospital discharges, Medicare discharges, older adult discharges, or community hospital discharges | state, national | Medium-low until source access/denominator resolved | Post-acute access context; policy dashboard only. |

## App Use Concepts

Potential future placements:

- Methodology page: state/national context explainer with source links and denominator definitions.
- Advanced facility dossier: optional "state/national context" accordion that clearly states the metric is not facility-specific.
- Statewide comparison: future context side panel, not used for facility sorting until methods are approved.
- Policy dashboard: state/national trends, rurality, post-acute utilization, and survey severity context.

These metrics should not be shown as facility findings. They can explain the environment around facilities, access, transitions, and survey systems.

## Caveats and Guardrails

- No runtime integration yet.
- No scraping or reproducing proprietary analysis unless allowed.
- Prefer official CMS, AHRQ, state, or federal data sources where possible.
- Use KFF and journal articles as source leads unless underlying data are available and reproducible.
- Clearly separate state/national context metrics from facility-level findings.
- No causation claims.
- No legal compliance claims.
- Do not mix claims-based, facility-based, resident-based, discharge-based, and citation-based denominators without clear labels.
- Do not compare Medicare-only metrics with all-payer metrics unless the difference is visible in labels.
- Do not present state rankings as quality rankings without source-specific justification and caveats.
- Do not infer harm or immediate jeopardy from citation narratives without structured scope/severity or official indicator fields.
- Clearly distinguish state-level, county-level, regional, facility-level, and national-only metrics.

## Recommended Next Research Steps

1. Create a source-validation matrix for each metric with columns for source URL, file access, fields, geography level, denominator, refresh cadence, license/use restrictions, and reproducibility.
2. Download or inspect CMS PAC PUF metadata to determine whether SNF stay length can be calculated by state.
3. Inspect CMS Health Deficiencies and Fire Safety Deficiencies fields for structured scope/severity coding and state/facility identifiers.
4. Locate the underlying data source and rurality classification used by KFF's rural nursing home analysis.
5. Review AHRQ HCUP discharge disposition fields and access constraints for discharge-to-SNF state estimates.
6. Review MedPAC SNF/PAC reports for current Medicare FFS national or state-level post-acute utilization benchmarks.
7. Confirm the original source and denominator for the reported 1987 AHA community hospital discharge-to-SNF reference before using it beyond a historical note.
8. Decide whether these metrics belong in a future state/national context data contract separate from Connecticut facility-level runtime files.

## Implementation Recommendation

Do not integrate these metrics into the current app yet. The next appropriate phase is a research-only source validation phase:

**Phase 11I.1: State/National SNF Context Source Validation Matrix**

Expected artifacts:

- source validation spreadsheet or markdown table;
- denominator decision notes for each metric;
- a recommendation on which metric, if any, is ready for prototype use;
- a separate data contract proposal if a metric is selected.

Out of scope for Phase 11I.1:

- public UI;
- runtime JSON;
- generated staffing data;
- facility-level conclusions;
- state rankings without denominator review.
