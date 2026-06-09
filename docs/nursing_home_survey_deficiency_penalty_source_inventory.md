# CMS Survey, F-Tag, Deficiency, and Penalty Source Inventory

Phase 11D planning document. This document does not build public UI, integrate runtime datasets, change formulas, change generated staffing data, change CT applicability logic, change current or historical staffing JSON, or change public tool behavior.

## 1. Purpose

This inventory identifies official source leads and feasibility considerations for adding survey, F-tag, deficiency, harm/immediate-jeopardy, and penalty/enforcement context to a future advanced Connecticut nursing home facility dossier.

The next data layer should be source-backed, denominator-aware, and clearly separated from staffing calculations. Survey and enforcement data can help users understand inspection context, recent citations, serious-deficiency screening patterns, and enforcement activity, but they should not be converted into unsupported legal conclusions or broad care-quality claims.

## 2. Current Repo Findings

Searched local repo paths `source_data`, `data`, and `docs`, plus the current attachment cache, for source leads related to citations, deficiencies, penalties, enforcement, surveys, CMS-2567, data dictionaries, and the named files below.

| File/source lead | Current availability in repo/workspace | Notes |
|---|---|---|
| `NH_CitationDescriptions_Apr2026.csv` | Not found | Should be acquired from CMS Provider Data Catalog before any F-tag lookup implementation. |
| `NH_Data_Dictionary.pdf` | Not found as a local file | Official CMS online data dictionary was reviewed as a source lead. |
| `Summary-Citations-022026.xlsx` | Not found | If later provided, treat as a source lead only until publisher, provenance, fields, and denominator methods are validated. |
| CMS Health Deficiencies CSV | Not found | Needed for citation-level F-tag health deficiency analysis. |
| CMS Fire Safety Deficiencies CSV | Not found | Needed for K-tag/life-safety citation analysis. |
| CMS Penalties CSV | Not found | Needed for CMP/payment-denial enforcement context. |
| CMS Survey Summary CSV | Not found | Useful for survey recency and facility-level survey counts. |

Existing integrated runtime files remain staffing/current-context focused and should not be treated as survey/deficiency datasets.

## 3. Source Inventory Table

| Source category | Likely official publisher | Source file/table lead | Format | Current repo availability | Key join field | Likely time period | Update frequency | Facility-level use | State-level use | Harm/IJ support | Citation text support | Feasibility | Risks/caveats | Recommended next validation step |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CMS Health Deficiencies | CMS Provider Data Catalog | `NH_HealthCitations_MonYYYY.csv`; PDC Health Deficiencies dataset | CSV/API | Not found | CMS Certification Number / CCN | Last three inspection cycles per CMS data dictionary | Monthly PDC refresh pattern; confirm from metadata at acquisition | Yes, citation-level by facility | Yes, aggregate after denominator decisions | Yes, if using structured scope/severity code and official mapping | Includes deficiency description; may still need lookup table for stable plain-language tag display | likely ready after validation | Includes citations not used for health inspection rating, including IDR/IIDR cases and some cycle 3 standard-survey citations; citation/survey/facility denominators differ | Download current CT rows, validate fields, map scope/severity with official definitions, compare counts to Survey Summary and Provider Information. |
| CMS Fire Safety Deficiencies | CMS Provider Data Catalog | `NH_FireSafetyCitations_MonYYYY.csv`; PDC Fire Safety Deficiencies dataset | CSV/API | Not found | CMS Certification Number / CCN | Last three inspection cycles | Monthly PDC refresh pattern; confirm from metadata | Yes, citation-level by facility | Yes, aggregate separately | Possible via scope/severity, but keep separate from health-deficiency harm/IJ analysis unless methodology approves | Includes K/E tag description fields | likely ready after validation | K-tags/life-safety deficiencies are different from F-tags; fire safety should not be blended into health-deficiency counts without explicit labeling | Download current CT rows, confirm prefixes and severity fields, decide separate UI section/filters for K-tags. |
| CMS Citation Descriptions | CMS Provider Data Catalog | `NH_CitationDescriptions_MonYYYY.csv` | CSV/API | Not found | Deficiency prefix + tag number | Current lookup file; not citation event history | Monthly PDC refresh pattern; confirm from metadata | Reference only | Reference only | No; lookup text does not identify actual harm/IJ findings | Yes, plain-language tag descriptions | ready after acquisition/validation | Descriptions explain tag codes but do not prove a facility received a citation | Download lookup, validate unique prefix/tag keys, join to health and fire citation rows by prefix/tag. |
| CMS Penalties / Enforcement | CMS Provider Data Catalog | `NH_Penalties_MonYYYY.csv`; PDC Penalties dataset | CSV/API | Not found | CMS Certification Number / CCN | Last three years per CMS data dictionary | Monthly PDC refresh pattern; confirm from metadata | Yes, penalty-level by facility | Yes, aggregate after denominator decisions | No direct harm/IJ unless joined to triggering survey/citation with care | No citation narrative; enforcement fields only | likely ready after validation | Penalties are enforcement actions, not citations; penalty date is inspection date that triggered penalty; CMP and payment denial require separate labels | Download current CT rows, validate CMP/payment-denial fields, decide if and how to link to surveys/citations. |
| CMS Survey Summary | CMS Provider Data Catalog | `NH_SurveySummary_MonYYYY.csv`; PDC Survey Summary dataset | CSV/API | Not found | CMS Certification Number / CCN | Last three cycles, including health, fire safety, infection control, and complaint inspection summaries | Monthly PDC refresh pattern; confirm from metadata | Yes, provider inspection summary | Yes | May support counts by categories, but citation-level severity analysis should use Health/Fire Deficiencies | Summary counts only; not full citation text | likely ready after validation | Summary counts can include citations from infection control and complaint inspections; not all counts are used in health inspection rating | Download current CT rows, compare facility counts and survey dates against citation files and Provider Information. |
| CMS Provider Information / Care Compare | CMS Provider Data Catalog | `NH_ProviderInfo_MonYYYY.csv`; Provider Information dataset | CSV/API | Already integrated for current/context staffing data, but not as a survey-detail dataset | CMS Certification Number / CCN | Current active nursing homes in selected snapshot | Monthly PDC refresh pattern; source snapshots already tracked for current context | Yes, current snapshot context | Yes | Abuse icon and health inspection rating context only; not citation-level harm/IJ | No citation text | ready for current-context caveats; not enough for detailed survey layer | Current snapshot only; ratings, abuse icon, SFF status, and most recent inspection flags are CMS context, not project-calculated findings | Inventory existing integrated fields and decide which should be displayed in dossier survey context without duplicating citation files. |
| CMS Inspection Dates | CMS Provider Data Catalog | `NH_SurveyDates_MonYYYY.csv`; Inspection Dates dataset | CSV/API | Not found | CMS Certification Number / CCN | Past three cycles / referenced inspection dates | Monthly PDC refresh pattern; confirm from metadata | Yes, survey recency context | Yes | No | No | likely ready after validation | Complaint dates may appear only when inspection resulted in citations; need exact CMS file rules | Download current CT rows and compare survey dates with Survey Summary and citation rows. |
| CT DPH ePOC / CMS-2567 / Plans of Correction | Connecticut Department of Public Health, CMS/state survey agency systems | ePOC documents, CMS-2567 Statements of Deficiencies, Plans of Correction | Web/PDF/manual portal documents | Not found as structured repo files | Facility license ID, facility name, sometimes CCN/CMS provider number | Varies by posted document | Event/document based, not necessarily a clean periodic dataset | Yes, document-level facility context if matched | Limited unless structured index exists | Yes in source forms if scope/severity appears, but extraction must be audited | Yes, narrative statements of deficiencies and plans of correction | needs research | Likely PDF/manual workflow; may require document matching, OCR, and careful legal/source language | Identify CT DPH lookup/index fields, determine if bulk structured download exists, test one facility document extraction. |
| CT DPH licensure/enforcement/closure/receivership/CON records | Connecticut DPH and related state agencies | Licensure pages, inspection reports, consent orders, receiverships, closure notices, Certificate of Need records | Web/PDF/Excel/manual | No general source set found in repo; status review used separate official CT DSS/DPH leads for closures | Facility license ID, name, address, sometimes CCN | Varies by record | Event/document based | Yes, context section only after source matching | Limited | Usually not primary harm/IJ dataset; may support enforcement/status context | Usually document narrative | needs research | State records may be less structured; status/event dates are not interchangeable | Create CT DPH source map and test facility identifier matching against CCN/geography crosswalk. |
| State US Averages | CMS Provider Data Catalog | `NH_StateUSAverages_MonYYYY.csv`; State US Averages dataset | CSV/API | Not found | State | Current/monthly snapshot with averages | Monthly PDC refresh pattern; confirm from metadata | No direct facility rows | Yes | May include deficiency averages, not citation-level harm/IJ | No citation text | needs research | Averages are denominator-sensitive and may not match project-defined harm/IJ metrics | Review fields after acquisition and decide whether useful for state-level context only. |

## 4. CMS Health Deficiencies

Primary lead:

- CMS Provider Data Catalog Health Deficiencies dataset: <https://data.cms.gov/provider-data/dataset/r5ix-sfxw>
- Data dictionary file lead: `NH_HealthCitations_MonYYYY.csv`

Likely fields from the CMS nursing home data dictionary:

- CMS Certification Number / CCN;
- provider name;
- provider address, city, state, ZIP;
- survey date;
- survey type;
- deficiency prefix, expected `F` for health deficiencies;
- deficiency category;
- deficiency tag number;
- deficiency description;
- scope/severity code;
- deficiency corrected status;
- correction date;
- inspection cycle;
- standard deficiency indicator;
- complaint deficiency indicator;
- infection control inspection deficiency indicator;
- citation under IDR / IIDR indicators;
- location;
- processing date.

Harm/IJ feasibility:

- Structured `Scope Severity Code` is the right starting point for harm/IJ analysis because CMS defines it as the level of harm and scope.
- A future phase must document the exact mapping before public use. Common shorthand should not replace official CMS definitions.
- Do not infer harm or immediate jeopardy from narrative deficiency text if structured scope/severity is available.

Feasibility rating: **likely ready after validation**.

Recommended validation:

1. Download the current CMS Health Deficiencies file.
2. Filter to Connecticut using state and/or CCN.
3. Validate CCN format and match count against current/context and geography files.
4. Confirm F-tag prefix and tag-number parsing.
5. Validate scope/severity code values and official harm/IJ mapping.
6. Separate citation-level, survey-level, facility-level, facility-year, and state-level denominators.

## 5. CMS Fire Safety Deficiencies

Primary lead:

- CMS Provider Data Catalog Fire Safety Deficiencies dataset: <https://data.cms.gov/provider-data/dataset/ifjz-ge4w>
- Data dictionary file lead: `NH_FireSafetyCitations_MonYYYY.csv`

Fire safety citations should be treated separately from health F-tags. The data dictionary identifies fire safety deficiency prefixes such as `K` or `E`, and these are not F-tags. A future UI should label them as life-safety/fire-safety citations and avoid blending them into health deficiency totals unless a combined count is explicitly labeled.

Feasibility rating: **likely ready after validation**.

Recommended validation:

1. Download the current CMS Fire Safety Deficiencies file.
2. Confirm prefix values and tag-version fields.
3. Test facility joins by CCN.
4. Decide whether the Facility Dossier should show fire safety in a separate accordion/table.
5. Validate any harm/severity grouping separately from health deficiencies.

## 6. CMS Citation Descriptions

Primary lead:

- CMS citation lookup table described in the data dictionary as `NH_CitationDescriptions_MonYYYY.csv`.
- CMS nursing home data dictionary: <https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/nursing_home/NH_Data_Dictionary.pdf>

Use:

- plain-language descriptions for F, K, and E tags;
- stable lookup keyed by deficiency prefix and tag number;
- reader-friendly F-tag/K-tag display in a future dossier.

Guardrail:

- Citation descriptions are reference text. They do not show that a facility received a citation and should not replace actual Health or Fire Safety Deficiencies rows.

Feasibility rating: **ready after acquisition/validation**.

Recommended validation:

1. Acquire the current citation descriptions CSV.
2. Confirm uniqueness of prefix + tag number.
3. Confirm formatting for F-tags, K-tags, and E-tags.
4. Join to test Health and Fire Safety citation rows.

## 7. CMS Penalties / Enforcement

Primary lead:

- CMS Provider Data Catalog Penalties dataset: <https://data.cms.gov/provider-data/dataset/g6vv-u9sr>
- Data dictionary file lead: `NH_Penalties_MonYYYY.csv`

Likely fields from the CMS nursing home data dictionary:

- CMS Certification Number / CCN;
- provider name;
- provider address, city, state, ZIP;
- penalty date;
- penalty type;
- fine amount;
- payment denial start date;
- payment denial length in days;
- location;
- processing date.

Interpretation:

- Penalties are enforcement actions, not citations.
- CMP amount and denial of payment should be displayed separately.
- Penalty date should not automatically be treated as citation date, correction date, or enforcement order date without source confirmation.
- Penalties should not be presented as proof of current poor care without survey date, source date, and context.

Feasibility rating: **likely ready after validation**.

Recommended validation:

1. Download current CMS Penalties file.
2. Filter to Connecticut and join by CCN.
3. Validate penalty type values and amount fields.
4. Decide whether to show recent penalties as a timeline or summary card.
5. Test whether penalty rows can be linked to survey/citation rows by date and facility without overclaiming.

## 8. CMS Provider Information / Care Compare Context

Primary lead:

- CMS Provider Data Catalog Provider Information dataset: <https://data.cms.gov/provider-data/dataset/4pq5-n9py>
- Data dictionary file lead: `NH_ProviderInfo_MonYYYY.csv`

Already integrated current/context fields may support limited survey/enforcement context:

- overall rating;
- health inspection rating;
- abuse icon, if present;
- Special Focus Status / SFF candidate, if present;
- most recent health inspection more than two years ago indicator, if present;
- current provider identity/address context;
- Provider Information snapshot date.

Guardrail:

- Provider Information is current snapshot context. It does not replace citation-level health/fire deficiencies, penalty rows, or CT DPH source documents.

Feasibility rating: **ready for current-context caveats; not sufficient by itself for the survey layer**.

Recommended validation:

1. Inventory which Provider Information fields are already included in `data/nursing_home_staffing_ct.json`.
2. Decide where these belong in the advanced facility dossier.
3. Keep current CMS snapshot caveats visible.

## 9. CT DPH Source Leads

Possible Connecticut-specific source leads:

- facility licensure pages and eLicense records;
- inspection reports;
- CMS-2567 Statements of Deficiencies;
- Plans of Correction;
- consent orders;
- receivership records;
- closure notices;
- enforcement actions;
- Certificate of Need / closure-related materials where applicable.

The CT DPH ePOC page explains that the electronic Plan of Correction system is used for Health, Life Safety Code, Revisits, and Complaint surveys, and lets providers see CMS-2567 Statements of Deficiencies and submit Plans of Correction online: <https://portal.ct.gov/dph/facility-licensing--investigations/facility-licensing--investigations-section-flis/epoc>.

Likely limitations:

- many records may be PDF-based or portal/manual rather than bulk CSV;
- facility matching may require CT license IDs in addition to CCN;
- CMS-2567 and POC text need careful extraction and source-date handling;
- state enforcement documents may use legal/process dates that are not citation dates;
- consent orders, receiverships, closures, and terminations should not be mixed without date-type labels.

Feasibility rating: **needs research**.

Recommended validation:

1. Identify whether CT DPH offers a structured export or index for nursing home survey/enforcement documents.
2. Test one facility end-to-end from eLicense/DPH document lookup to CCN match.
3. Decide whether PDF extraction is feasible and necessary.

## 10. Proposed Future Data Files

Do not create these files in Phase 11D. Proposed future files:

- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_citation_descriptions.json`
- `data/nursing_home_penalties_ct.json`
- `data/nursing_home_survey_enforcement_summary_ct.json`

Possible design:

- keep raw-source snapshots archived under `source_data`;
- create CT-filtered audited JSON files only after validation;
- preserve citation-level rows separately from summary rows;
- preserve source file names, processing dates, survey dates, correction dates, penalty dates, and source snapshot dates;
- avoid embedding these data into `data/nursing_home_staffing_ct.json` or `data/nursing_home_staffing_history_ct.json`.

## 11. Proposed Future App Uses

Potential future uses after validation:

- Facility Dossier inspection/enforcement section;
- F-tag lookup and plain-language description display;
- harm/IJ screening counts using structured scope/severity;
- recent deficiency timeline;
- enforcement summary for CMPs and payment denials;
- survey recency context;
- state-level harm/IJ summary metrics;
- exportable facility survey summary;
- methodology page source and denominator explanations.

Suggested UI separation:

- Health deficiencies / F-tags;
- Fire safety / K-tags;
- survey summary and survey dates;
- enforcement/penalties;
- CT DPH source documents.

## 12. Denominator And Interpretation Guardrails

- Survey/enforcement findings must be source-backed.
- Do not infer harm/IJ from narrative text if structured severity/scope fields are available.
- Do not merge F-tags and K-tags without labeling.
- Do not treat penalties as proof of current poor care without context.
- Do not use citations as legal conclusions beyond official source language.
- Preserve survey date, correction date, processing date, penalty date, and source snapshot date.
- Separate citation-level, survey-level, facility-level, facility-year, and state-level denominators.
- No causation claims.
- Current CMS ratings and survey context are snapshots unless historically aligned snapshots are acquired.
- Citation descriptions are lookup/reference text, not facility findings.
- IDR/IIDR indicators should be preserved where available.

## 13. Feasibility Summary

| Area | Feasibility | Reason |
|---|---|---|
| Health F-tag citation rows | likely ready after validation | CMS PDC appears to provide citation-level CSV with CCN, survey date, F-tag, scope/severity, correction, and inspection-type indicators. |
| Fire safety K-tag rows | likely ready after validation | CMS PDC appears to provide citation-level CSV, but it must be displayed separately from health deficiencies. |
| Citation descriptions lookup | ready after acquisition/validation | Reference table is straightforward if prefix/tag keys are unique and versioned. |
| Penalties/enforcement rows | likely ready after validation | CMS PDC penalties file provides facility-level fine/payment-denial rows, but enforcement interpretation needs guardrails. |
| Survey summary/inspection dates | likely ready after validation | Useful for recency/context, but counts must be reconciled with citation files. |
| CT DPH document layer | needs research | Likely valuable but may be PDF/manual and require identifier matching and extraction audit. |
| State-level harm/IJ summaries | needs research | Feasible only after denominator decisions and official scope/severity mapping are documented. |

## 14. Recommended Next Validation Phase

Recommended next phase: **Phase 11D.1: CMS Survey And Enforcement Source Acquisition Validation**.

Expected tasks:

1. Download current CMS PDC source files for Health Deficiencies, Fire Safety Deficiencies, Citation Descriptions, Survey Summary, Inspection Dates, Penalties, and the current data dictionary.
2. Store raw files under a clearly named `source_data` subfolder without changing runtime behavior.
3. Validate file schemas against the CMS data dictionary.
4. Filter Connecticut rows and test CCN joins against the current/context dataset and geography crosswalk.
5. Create a field inventory and row-count audit.
6. Draft data contracts for each future JSON file.
7. Define official harm/IJ scope/severity mapping and denominator rules before any public display.

Out of scope for Phase 11D.1:

- public UI;
- runtime registry changes;
- generated staffing data changes;
- formula changes;
- county/geography changes;
- legal/compliance conclusions.
