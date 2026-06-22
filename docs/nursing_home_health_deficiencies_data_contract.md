# Nursing Home Health Deficiencies Data Contract

Phase 11D.5 data contract and builder planning document. This document defines a future app-ready Connecticut Health Deficiencies output, but it does not create runtime JSON, build public UI, modify runtime JS/HTML, change staffing formulas, change generated staffing data, alter current or historical staffing JSON, change Connecticut applicability logic, modify geography JSON, or modify facility status review JSON.

## 1. Purpose

`data/nursing_home_health_deficiencies_ct.json` should become a Connecticut-only, citation-level health deficiency dataset derived from official CMS Health Deficiencies source rows. It should support future advanced facility dossier inspection context, F-tag timelines, survey-date filtering, and carefully labeled harm/immediate-jeopardy screening.

This dataset should not be used as a standalone legal conclusion, care-quality finding, staffing formula input, CT applicability input, or current-only facility status source.

## 2. Source Basis

Validated source from Phase 11D.4:

- `source_data/cms_survey/NH_HealthCitations_May2026.csv`

Official CMS source metadata:

- CMS dataset title: `Health Deficiencies`
- CMS dataset ID: `r5ix-sfxw`
- source filename: `NH_HealthCitations_May2026.csv`
- modified date: May 1, 2026
- released date: May 27, 2026
- acquired date: June 22, 2026
- source URL: <https://data.cms.gov/provider-data/sites/default/files/resources/e269c04e82fe86040cd70b7ba3dd4853_1778861752/NH_HealthCitations_May2026.csv>

Validation results:

- total source rows: 418,177
- Connecticut rows: 6,761
- unique Connecticut CCNs: 191
- joined to current staffing data: 191
- unmatched CT Health Deficiency CCNs: 0
- current staffing CCNs not present in Health Deficiencies source: 5
- survey date range: 2018-11-08 to 2026-03-31
- distinct CT F-tags: 164
- CT prefix coverage: all rows are `F`
- Citation Descriptions lookup misses: 0

## 3. Future Output File

Proposed future output:

- `data/nursing_home_health_deficiencies_ct.json`

Do not create this output in Phase 11D.5. It should be created only after builder implementation and validation expectations are approved.

The file should remain separate from:

- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_staffing_history_ct.json`
- `data/nursing_home_citation_descriptions.json`
- future fire safety, penalty, survey summary, and CT DPH document outputs

## 4. Recommended JSON Shape

```json
{
  "metadata": {
    "source_name": "CMS Provider Data Catalog Health Deficiencies",
    "source_file": "NH_HealthCitations_May2026.csv",
    "source_url_or_endpoint": "https://data.cms.gov/provider-data/sites/default/files/resources/e269c04e82fe86040cd70b7ba3dd4853_1778861752/NH_HealthCitations_May2026.csv",
    "cms_dataset_id": "r5ix-sfxw",
    "source_month": "May",
    "source_year": 2026,
    "acquired_date": "2026-06-22",
    "build_date": "YYYY-MM-DD",
    "state_filter": "CT",
    "source_row_count": 418177,
    "ct_row_count": 6761,
    "unique_ct_ccn_count": 191,
    "joined_current_ccn_count": 191,
    "unmatched_current_ccn_count": 0,
    "survey_date_min": "2018-11-08",
    "survey_date_max": "2026-03-31",
    "f_tag_count": 6761,
    "citation_description_lookup_miss_count": 0,
    "limitations": [
      "Health deficiencies are citation-level records.",
      "One facility may have many citation rows.",
      "Survey date and processing date are not the same.",
      "Citation descriptions are lookup/reference text, not proof of a facility finding by themselves.",
      "Scope/severity grouping is a derived screening classification, not a legal conclusion.",
      "This dataset should not be treated as current-only findings."
    ]
  },
  "deficiencies": [
    {
      "ccn": "075000",
      "provider_name": "Example Facility",
      "state": "CT",
      "survey_date": "2025-01-01",
      "survey_year": 2025,
      "survey_type": "Health",
      "deficiency_prefix": "F",
      "deficiency_tag_number": "0880",
      "deficiency_code": "F-0880",
      "deficiency_description": "CMS source description text",
      "deficiency_category": "Infection Control Deficiencies",
      "scope_severity_code": "D",
      "harm_ij_group": "no_actual_harm_more_than_minimal",
      "standard_deficiency": true,
      "complaint_deficiency": false,
      "infection_control_inspection_deficiency": false,
      "correction_date": "2025-02-01",
      "citation_under_idr": false,
      "citation_under_iidr": false,
      "processing_date": "2026-05-01",
      "source_row_hash": "sha256-of-normalized-source-row",
      "citation_description_lookup_matched": true,
      "citation_description_category": "Infection Control Deficiencies",
      "citation_description_text": "CMS lookup description text"
    }
  ]
}
```

## 5. Metadata Field Definitions

| Field | Definition |
|---|---|
| `source_name` | Human-readable official source name. |
| `source_file` | Raw CMS source filename used for the build. |
| `source_url_or_endpoint` | Official CMS source URL or metadata endpoint. |
| `cms_dataset_id` | CMS Provider Data Catalog dataset identifier, currently `r5ix-sfxw`. |
| `source_month` | Source month parsed from filename or CMS metadata. |
| `source_year` | Source year parsed from filename or CMS metadata. |
| `acquired_date` | Date the raw source file was acquired locally. |
| `build_date` | Date the JSON output was built. |
| `state_filter` | State filter applied to source rows, currently `CT`. |
| `source_row_count` | Total rows in the raw source file. |
| `ct_row_count` | Rows emitted after Connecticut filtering. |
| `unique_ct_ccn_count` | Unique CT CCNs in emitted rows. |
| `joined_current_ccn_count` | Unique CT source CCNs that join to current staffing data. |
| `unmatched_current_ccn_count` | Unique CT source CCNs that do not join to current staffing data. |
| `survey_date_min` | Earliest parsed `Survey Date` in emitted rows. |
| `survey_date_max` | Latest parsed `Survey Date` in emitted rows. |
| `f_tag_count` | Number of emitted rows with deficiency prefix `F`. |
| `citation_description_lookup_miss_count` | Number of emitted rows whose F-tag does not join to citation descriptions lookup. |
| `limitations` | Plain-language limitations that must travel with the dataset. |

## 6. Deficiency Record Field Definitions

| Field | Source / rule | Definition |
|---|---|---|
| `ccn` | `CMS Certification Number (CCN)` | Normalized six-character CCN with leading zeroes preserved. |
| `provider_name` | `Provider Name` | CMS source provider name. |
| `state` | `State` | State abbreviation, expected `CT` after filtering. |
| `survey_date` | `Survey Date` | Citation/survey date from source. |
| `survey_year` | Derived from `survey_date` | Calendar year of survey date. |
| `survey_type` | `Survey Type` | Survey type, `Health` in validated CT rows. |
| `deficiency_prefix` | `Deficiency Prefix` | Expected `F` for Health Deficiencies. |
| `deficiency_tag_number` | `Deficiency Tag Number` | Zero-padded F-tag number preserved as text. |
| `deficiency_code` | Derived from prefix + tag | Canonical code such as `F-0880`. |
| `deficiency_description` | `Deficiency Description` | CMS source description text. This is short tag/citation text, not long CMS-2567 narrative. |
| `deficiency_category` | Source or citation lookup | CMS deficiency category. Prefer source field, compare to lookup for consistency. |
| `scope_severity_code` | `Scope Severity Code` | Original CMS structured scope/severity code. |
| `harm_ij_group` | Derived from `scope_severity_code` | Conservative screening group. Not a legal conclusion. |
| `standard_deficiency` | `Standard Deficiency` | Boolean conversion of Y/N indicator. |
| `complaint_deficiency` | `Complaint Deficiency` | Boolean conversion of Y/N indicator. |
| `infection_control_inspection_deficiency` | `Infection Control Inspection Deficiency` | Boolean conversion of Y/N indicator. |
| `correction_date` | `Correction Date` | Correction date when present; null if blank. |
| `citation_under_idr` | `Citation under IDR` | Boolean conversion of Y/N indicator. |
| `citation_under_iidr` | `Citation under IIDR` | Boolean conversion of Y/N indicator. |
| `processing_date` | `Processing Date` | CMS processing/source date. |
| `source_row_hash` | Derived | Stable hash of normalized source row values for audit and deduplication. |
| `citation_description_lookup_matched` | Derived | Whether `deficiency_code` matched citation descriptions lookup. |
| `citation_description_category` | Lookup | Category from citation descriptions lookup, if included. |
| `citation_description_text` | Lookup | Lookup description text, if included. |

## 7. Health Deficiency Semantics

- Health deficiencies are citation-level records.
- One facility may have many citation rows.
- One survey may have many citation rows.
- Citation row counts are not survey counts.
- Citation row counts are not facility counts.
- Survey date and processing date are not the same.
- Correction date is not survey date.
- Citation descriptions are lookup/reference text and are not proof that a facility received a citation by themselves.
- Health deficiencies should remain separate from fire safety K-tags and emergency preparedness E-tags.

## 8. Harm / Immediate Jeopardy Mapping Plan

The future builder may derive `harm_ij_group` from structured `Scope Severity Code`, while preserving the original code.

Proposed conservative mapping:

| Output group | Scope/severity codes | Meaning for project use |
|---|---|---|
| `immediate_jeopardy` | `J`, `K`, `L` | Structured code indicates immediate jeopardy. |
| `actual_harm_not_ij` | `G`, `H`, `I` | Structured code indicates actual harm but not immediate jeopardy. |
| `no_actual_harm_more_than_minimal` | `D`, `E`, `F` | Structured code indicates no actual harm with more-than-minimal potential. |
| `no_actual_harm_minimal` | `A`, `B`, `C` | Structured code indicates no actual harm with minimal potential. |
| `unknown_or_unmapped` | blank or unexpected values | Do not classify without review. |

Validation-only CT counts from Phase 11D.4:

| Group | Count |
|---|---:|
| `immediate_jeopardy` | 73 |
| `actual_harm_not_ij` | 172 |
| `no_actual_harm_more_than_minimal` | 6,053 |
| `no_actual_harm_minimal` | 463 |

Guardrails:

- This mapping must be validated against official CMS scope/severity definitions before public display.
- Do not infer harm/IJ from narrative text.
- Do not collapse citation-level harm/IJ counts into survey-level, facility-level, facility-year, or state-level percentages without explicit denominator labels.
- The derived group is a screening classification, not a legal conclusion.

## 9. Citation Description Lookup Join

Future builder may optionally read:

- `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`

Join key:

- `Deficiency Prefix and Number`, or derived `deficiency_code`.

Validation results from Phase 11D.4:

- distinct CT F-tags: 164
- citation lookup misses: 0

Recommended behavior:

- include `citation_description_lookup_matched`;
- include lookup `citation_description_category` and `citation_description_text` only if useful;
- preserve source `Deficiency Description` even when lookup text is included;
- fail or warn on lookup misses depending on future build policy.

## 10. Builder Plan

Proposed future builder:

- `scripts/build_nursing_home_health_deficiencies_ct.py`

Recommended behavior:

1. Read `source_data/cms_survey/NH_HealthCitations_May2026.csv` or latest matching `NH_HealthCitations_*.csv`.
2. Read `data/nursing_home_staffing_ct.json` for current CCN join validation.
3. Optionally read `source_data/cms_survey/NH_CitationDescriptions_May2026.csv` or latest matching lookup.
4. Validate required source columns.
5. Filter rows to `State == CT`.
6. Normalize CCNs to six characters with leading zeroes preserved.
7. Parse survey, correction, and processing dates.
8. Normalize F-tags to canonical `F-####` codes.
9. Join citation descriptions lookup.
10. Derive `survey_year`.
11. Derive `harm_ij_group` from structured `Scope Severity Code`.
12. Convert Y/N indicators to booleans while preserving null handling rules.
13. Generate stable `source_row_hash`.
14. Emit metadata and limitations.
15. Write `data/nursing_home_health_deficiencies_ct.json`.
16. Print row counts, join counts, date ranges, prefix counts, scope/severity counts, lookup misses, and validation warnings.
17. Exit nonzero on missing required columns, invalid required dates, malformed tags, unexpected prefixes, or duplicate source row hashes.

Do not create this builder in Phase 11D.5. This contract is enough to define expected behavior before implementation.

## 11. Future Validation Requirements

A future builder should fail loudly when:

- raw source file is missing;
- required columns are missing;
- any CT row is missing CCN, provider name, state, survey date, deficiency prefix, tag number, deficiency description, scope/severity code, or processing date;
- any CT survey date is invalid;
- any CT deficiency prefix is not `F`;
- any F-tag is malformed;
- citation lookup misses exceed the approved threshold;
- emitted row count does not match CT source row count;
- metadata counts do not match emitted rows;
- source date, survey date, correction date, and processing date are collapsed or overwritten.

The existing validation script remains the source-level check:

- `scripts/validate_nursing_home_health_deficiencies.py`

## 12. Denominator Planning

Future public metrics must label denominators:

- citation-level counts: rows in `deficiencies`;
- survey-level counts: distinct facility/survey-date/survey-type events;
- facility-level counts: facilities with at least one selected citation;
- facility-year counts: facility-year combinations with selected citations;
- state-level percentages: numerator and denominator must be explicit;
- harm/IJ percentages: must specify whether denominator is citations, surveys, facilities, facility-years, or all current facilities.

Do not mix denominators without labels.

## 13. Runtime Guardrails

- Do not wire the future JSON into public UI until a later phase approves it.
- Do not alter staffing data, PBJ history, CT applicability logic, county/geography data, or facility status review data.
- Do not remove current runtime records based on health deficiency joins.
- Do not treat citation descriptions as facility findings.
- Do not present penalties, fire safety citations, or survey summaries from this file; they require separate source files.
- Do not make legal compliance or causation claims.

## 14. Recommended Next Phase

Recommended next phase:

**Phase 11D.6: Health Deficiencies Builder Dry Run**

Suggested scope:

1. Create `scripts/build_nursing_home_health_deficiencies_ct.py`.
2. Generate `data/testing/nursing_home_health_deficiencies_ct_preview.json` or a local preview only, not public runtime JSON.
3. Compare preview row counts against Phase 11D.4 validation.
4. Validate citation lookup joins and derived harm/IJ groups.
5. Decide whether full `data/nursing_home_health_deficiencies_ct.json` is ready for a later non-runtime commit.

Alternative next source acquisition:

**Phase 11D.6: CMS Fire Safety Deficiencies Source Acquisition Validation**

This would validate K-tag/life-safety rows separately before any combined survey/enforcement architecture is implemented.
