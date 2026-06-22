# CMS Survey and Enforcement Source Acquisition Validation Plan

Phase 11D.1 planning document. This plan does not build public UI, integrate runtime datasets, change formulas, change generated staffing data, change Connecticut applicability logic, modify current or historical staffing JSON, or modify runtime JS/HTML.

## 1. Purpose

Phase 11D identified the likely source families for inspections, deficiencies, F-tags, K-tags, citation descriptions, penalties, enforcement, and Connecticut DPH survey documents. Phase 11D.1 defines the next acquisition and validation path before any public application work or runtime data integration.

The purpose is to decide exactly what to acquire, where raw files should live, how Connecticut-only extraction should be validated, what denominators must be defined, and what future builder scripts/data contracts may be needed.

## 2. Repo Connection Confirmation

Expected repository:

- `dbeem123/DanBeem`

Session verification performed before creating this plan:

| Check | Result |
|---|---|
| `pwd` | `C:\Users\Dan\OneDrive\Documents\GitHub\DanBeem` |
| `git rev-parse --show-toplevel` | `C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem` |
| `git remote -v` | `origin https://github.com/dbeem123/DanBeem.git` |
| `git status --short --branch` | `## main...origin/main` |
| Recent history | Latest commit includes `f6f8724 Add survey deficiency and penalty source inventory` |

## 3. Acquisition Principles

- Acquire raw official source files first; do not create runtime outputs until schemas and joins are validated.
- Store raw files under `source_data` with clear source family folders and source snapshot names.
- Preserve source file names, source URLs, processing dates, survey dates, correction dates, enforcement dates, and extract/build dates separately.
- Keep current CMS Provider Information snapshot context separate from historical citation/enforcement timelines.
- Keep Connecticut-only filtering reproducible.
- Do not infer harm/immediate-jeopardy from narrative text if structured scope/severity fields exist.
- Do not merge health F-tags and fire-safety K-tags without explicit labels.
- Do not treat penalties as standalone proof of current poor care.
- Do not create legal conclusions beyond official citation/enforcement language.

## 4. Source Acquisition Matrix

| Category | Expected source name | Likely publisher | Format | Suggested local folder | Expected join key | Expected key date fields | Expected update frequency | CT-only filtering | Facility-level output | State-level output | Harm/IJ analysis | Priority | Risks/caveats | Validation steps |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CMS Citation Descriptions | `NH_CitationDescriptions_MonYYYY.csv` | CMS Provider Data Catalog | CSV/API | `source_data/cms_survey/` | deficiency prefix + tag number | source snapshot / processing date if provided | To be confirmed from CMS metadata; likely monthly with PDC release | Not applicable; lookup is national/reference | Reference only | Reference only | No | 1 | Lookup text is not a facility citation finding. Tag keys must be unique and prefix-aware. | Confirm file acquired, parse prefix/tag, validate unique keys, confirm F/K/E coverage, document source snapshot. |
| CMS Nursing Home Data Dictionary | `NH_Data_Dictionary.pdf` | CMS Provider Data Catalog | PDF | `source_data/cms_survey/` | Reference document | publication/update date | To be determined | Not applicable | Reference only | Reference only | Supports field interpretation only | 1 | Field names and meanings can shift over time; retain snapshot used for validation. | Save source PDF, record URL/date, compare expected file schemas to dictionary. |
| CMS Health Deficiencies | `NH_HealthCitations_MonYYYY.csv` / Health Deficiencies dataset | CMS Provider Data Catalog | CSV/API | `source_data/cms_survey/` | CMS Certification Number / CCN | survey date, correction date, processing/source date | To be confirmed from CMS metadata; likely monthly with PDC release | Yes, by state and/or CT CCN universe | Yes, citation-level by facility | Yes, after denominator decisions | Yes, if structured scope/severity mapping is documented | 2 | Citation-level rows include specific CMS inclusion rules. IDR/IIDR indicators and survey type flags must be preserved. | Validate CT row count, CCN format, CCN joins, F-tag parsing, scope/severity codes, survey dates, correction dates, complaint/standard/infection-control indicators, and harm/IJ mapping. |
| CMS Fire Safety Deficiencies | `NH_FireSafetyCitations_MonYYYY.csv` / Fire Safety Deficiencies dataset | CMS Provider Data Catalog | CSV/API | `source_data/cms_survey/` | CMS Certification Number / CCN | survey date, correction date, processing/source date | To be confirmed from CMS metadata; likely monthly with PDC release | Yes, by state and/or CT CCN universe | Yes, citation-level by facility | Yes, after denominator decisions | Possible from structured scope/severity, but separate from health F-tag analysis | 3 | K-tags/life-safety citations are not health F-tags. Do not blend without labels. | Validate CT row count, CCN joins, K/E tag prefixes, scope/severity values, survey dates, and separate health/fire denominators. |
| CMS Penalties / Enforcement | `NH_Penalties_MonYYYY.csv` / Penalties dataset | CMS Provider Data Catalog | CSV/API | `source_data/cms_enforcement/` | CMS Certification Number / CCN | penalty date, payment denial start date, processing/source date | To be confirmed from CMS metadata; likely monthly with PDC release | Yes, by state and/or CT CCN universe | Yes, penalty-level by facility | Yes, after denominator decisions | Not directly; may be contextual if linked carefully to citations/surveys | 4 | Enforcement actions are not citations. CMPs and denial of payment require separate labels. Penalty date is not necessarily citation date. | Validate CT row count, CCN joins, penalty type values, CMP amount parsing, denial dates/days, duplicate handling, and date semantics. |
| CMS Survey Summary | `NH_SurveySummary_MonYYYY.csv` / Survey Summary dataset | CMS Provider Data Catalog | CSV/API | `source_data/cms_survey/` | CMS Certification Number / CCN | standard survey dates, complaint survey dates, fire/life safety dates, processing/source date | To be confirmed from CMS metadata; likely monthly with PDC release | Yes, by state and/or CT CCN universe | Yes, facility-level survey summary | Yes, after denominator decisions | Limited; citation-level severity should come from Health/Fire files | 5 | Summary counts may not equal citation-row counts if CMS inclusion rules differ. | Validate row count, CCN joins, date fields, survey-count fields, and consistency against Health/Fire citation rows. |
| CMS Inspection Dates | `NH_SurveyDates_MonYYYY.csv` / Inspection Dates dataset | CMS Provider Data Catalog | CSV/API | `source_data/cms_survey/` | CMS Certification Number / CCN | inspection/survey dates, processing/source date | To be confirmed from CMS metadata; likely monthly with PDC release | Yes, by state and/or CT CCN universe | Yes, survey recency by facility | Yes | No | 5 | Complaint dates may appear only under CMS file rules; not a substitute for citation details. | Validate date completeness and reconcile with Provider Information and Survey Summary fields. |
| CMS Provider Information / Care Compare Context | `NH_ProviderInfo_MonYYYY.csv` | CMS Provider Data Catalog | CSV/API | `source_data/cms_provider/` | CMS Certification Number / CCN | provider snapshot/source date, inspection-related date fields if present | Existing project pattern suggests monthly PDC snapshots; confirm from metadata | Yes | Yes, current snapshot context | Yes | Abuse icon/rating context only, not citation-level harm/IJ | 6 | Already used as current/context source. Do not treat as historical citation timeline. | Inventory already integrated fields, confirm health inspection rating, overall rating, abuse icon, SFF status/candidate, and survey-related fields. |
| CT DPH survey and licensure documents | State inspection reports, CMS-2567 Statements of Deficiencies, Plans of Correction, licensure status, enforcement actions, closure/receivership notices | Connecticut DPH and related state agencies | Web/PDF/manual, possibly portal records | `source_data/ct_dph/` | CCN if available; facility license ID; facility name/address; official document identifiers | survey date, document date, correction/POC date, enforcement/order date, license/status date | Event/document based; to be determined | Yes, after matching | Yes, if matched and audited | Limited unless structured index exists | Possible only if structured severity/scope exists or CMS-2567 fields are extracted accurately | 7 | Likely less structured. PDF/OCR/manual review may be needed. State legal/process dates are not interchangeable with CMS survey dates. | Identify structured index availability, test one facility match, document identifiers, and decide whether PDF extraction is feasible. |

## 5. Proposed Acquisition Order

### Step 1: Reference files first

Acquire:

- `NH_Data_Dictionary.pdf`;
- `NH_CitationDescriptions_MonYYYY.csv`.

Local folder:

- `source_data/cms_survey/`

Validation:

- record source URL, download date, file modified date if available, and CMS snapshot month;
- validate citation description keys;
- document F/K/E prefix handling;
- confirm descriptions are reference text only.

Reason:

Citation lookup and the data dictionary are low-risk foundations for all later schema validation.

### Step 2: CMS Health Deficiencies

Acquire:

- `NH_HealthCitations_MonYYYY.csv` or the equivalent CMS Health Deficiencies export.

Local folder:

- `source_data/cms_survey/`

Validation:

- parse as CSV without lossy type conversion;
- normalize CCN to six characters;
- filter Connecticut by state and cross-check against the CT facility universe;
- validate survey date and correction date parsing;
- confirm deficiency prefix/tag fields produce F-tags;
- validate scope/severity code values;
- preserve standard, complaint, infection-control, IDR, and IIDR indicators where present;
- define official harm/IJ mapping using structured scope/severity fields before any public metric;
- produce preliminary row counts by citation, survey date, facility, and state.

### Step 3: CMS Fire Safety Deficiencies

Acquire:

- `NH_FireSafetyCitations_MonYYYY.csv` or the equivalent CMS Fire Safety Deficiencies export.

Local folder:

- `source_data/cms_survey/`

Validation:

- keep fire/life-safety rows separate from health deficiency rows;
- validate K/E tag prefixes and tag-version fields if present;
- validate survey dates and correction dates;
- validate CCN joins;
- decide whether future UI uses a separate fire-safety section or a clearly labeled subsection.

### Step 4: CMS Penalties / Enforcement

Acquire:

- `NH_Penalties_MonYYYY.csv` or the equivalent CMS Penalties export.

Local folder:

- `source_data/cms_enforcement/`

Validation:

- normalize CCNs;
- filter Connecticut rows;
- validate penalty type values;
- parse CMP amount fields without losing currency precision;
- parse denial-of-payment start date and length fields;
- preserve penalty/enforcement date separately from citation and survey dates;
- test whether facility-level timelines are meaningful without implying causation.

### Step 5: CMS Survey Summary / Inspection Dates

Acquire:

- `NH_SurveySummary_MonYYYY.csv`;
- `NH_SurveyDates_MonYYYY.csv`, if available as a separate file.

Local folder:

- `source_data/cms_survey/`

Validation:

- validate survey recency fields;
- compare most recent health inspection dates against Provider Information where present;
- compare summary counts against Health/Fire citation files;
- decide whether summary fields support facility-level survey recency cards.

### Step 6: CMS Provider Information context review

Acquire only if the current source snapshot needs refreshing or direct schema comparison:

- `NH_ProviderInfo_MonYYYY.csv`.

Local folder:

- `source_data/cms_provider/`

Validation:

- inventory already integrated fields in `data/nursing_home_staffing_ct.json`;
- confirm overall rating, health inspection rating, abuse icon, SFF status/candidate, and survey-related fields;
- keep this as current snapshot context, not historical survey detail.

### Step 7: CT DPH source research

Acquire only after the CMS files are validated:

- structured indexes, if available;
- sample CMS-2567/POC documents;
- licensure/enforcement/closure/receivership documents;
- source documentation explaining access, identifiers, and dates.

Local folder:

- `source_data/ct_dph/`

Validation:

- identify facility identifiers and whether CCN appears;
- test document-to-facility matching;
- document whether source is structured, PDF-based, OCR-based, or manual;
- decide whether CT DPH sources should supplement CMS rows or remain source-link context.

## 6. Proposed Future Scripts

Do not create these scripts in Phase 11D.1. Proposed future scripts:

- `scripts/validate_nursing_home_survey_sources.py`
- `scripts/build_nursing_home_health_deficiencies_ct.py`
- `scripts/build_nursing_home_fire_safety_deficiencies_ct.py`
- `scripts/build_nursing_home_penalties_ct.py`
- `scripts/build_nursing_home_survey_enforcement_summary_ct.py`

Recommended script responsibilities:

- validate raw file presence, schema, encoding, and required columns;
- normalize CCNs consistently;
- filter Connecticut rows reproducibly;
- join to current/context and geography facility universes without changing those files;
- preserve source filenames and source snapshot dates;
- emit row-count, join-count, missing-CCN, duplicate-key, and date-parse audit reports;
- fail loudly on unexpected schema changes.

## 7. Proposed Future JSON Outputs

Do not create these JSON files in Phase 11D.1. Proposed future outputs:

- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_citation_descriptions.json`
- `data/nursing_home_penalties_ct.json`
- `data/nursing_home_survey_enforcement_summary_ct.json`

Output design notes:

- citation-level health and fire rows should stay separate;
- penalty/enforcement rows should stay separate from citations;
- summary output should be derived from audited source rows, not manually entered;
- outputs should include source metadata and build metadata;
- none of these files should be embedded into `data/nursing_home_staffing_ct.json` or `data/nursing_home_staffing_history_ct.json`.

## 8. Denominator Planning

Future public metrics must label denominators explicitly.

Potential denominator levels:

- citation-level counts: number of citation rows;
- survey-level counts: number of surveys with at least one selected citation type;
- facility-level counts: number of facilities with at least one selected event;
- facility-year counts: facility-years with at least one selected event;
- state-level percentages: state facilities/surveys/citations meeting a defined condition;
- harm/IJ percentages: must specify whether the denominator is citations, surveys, facilities, or facility-years.

Guardrail:

- Do not mix citation-level, survey-level, facility-level, facility-year, and state-level percentages without labels.
- Do not compare CMS citation rows, Provider Information ratings, and penalties as though they share one denominator.
- Do not combine health F-tags and fire-safety K-tags unless the metric name clearly says it combines them.

## 9. Harm / Immediate Jeopardy Planning

Harm/IJ analysis should use structured scope/severity fields when available.

Required before use:

1. Identify all scope/severity code values present in Health Deficiencies and Fire Safety Deficiencies.
2. Locate and cite the official CMS meaning of each scope/severity code.
3. Define which codes count as actual harm and which count as immediate jeopardy.
4. Validate counts by facility, survey, and state.
5. Keep health and fire safety results separate unless a combined denominator is explicitly approved.
6. Document whether IDR/IIDR status affects inclusion.

Do not infer harm/IJ from narrative deficiency text when structured fields are available.

## 10. Validation Audit Checklist

For each acquired source file:

- source file exists in the expected folder;
- source URL and download date recorded;
- file opens with expected encoding;
- required columns exist;
- row count is recorded;
- Connecticut filter count is recorded;
- CCN normalization is tested;
- duplicate key expectations are documented;
- date fields parse without silent failure;
- missing date fields are counted;
- join counts against `data/nursing_home_staffing_ct.json` are recorded;
- join counts against `data/nursing_home_facility_geography_ct.json` are recorded;
- records for closed/non-current status review facilities are handled transparently;
- source snapshot date, survey date, correction date, enforcement date, and build/extract date are kept separate.

## 11. Recommended First Actual Source To Acquire

Recommended first acquisition:

1. `NH_Data_Dictionary.pdf`
2. `NH_CitationDescriptions_MonYYYY.csv`

Reason:

These reference files establish field definitions and tag lookup behavior before any citation/enforcement row processing. They also let validation scripts avoid hardcoded assumptions about tag descriptions and CMS field meanings.

Recommended second acquisition:

- `NH_HealthCitations_MonYYYY.csv`

Reason:

Health F-tag citations are the core future facility-dossier inspection layer and the likely basis for harm/IJ screening once structured scope/severity mapping is validated.

## 12. Out Of Scope For Phase 11D.1

- public UI;
- runtime registry changes;
- source downloads;
- builder scripts;
- runtime JSON outputs;
- generated staffing data changes;
- staffing formula changes;
- current/context staffing JSON changes;
- historical PBJ JSON changes;
- CT applicability changes;
- public legal/compliance conclusions.
