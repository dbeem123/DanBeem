# Nursing Home Fire Safety Deficiencies Data Contract

Phase 11D.8 data contract and builder planning document. This document defines a future app-ready Connecticut Fire Safety Deficiencies output, but it does not create runtime JSON, build public UI, modify runtime JS/HTML, change staffing formulas, change generated staffing data, alter current or historical staffing JSON, change Connecticut applicability logic, modify geography JSON, or modify facility status review JSON.

## 1. Purpose

`data/nursing_home_fire_safety_deficiencies_ct.json` should become a Connecticut-only, citation-level fire safety and emergency preparedness deficiency dataset derived from official CMS Fire Safety Deficiencies source rows. It should support future advanced facility dossier inspection context, life-safety timelines, K-tag and E-tag display, survey-date filtering, and carefully labeled fire safety source context.

This dataset should not be used as a standalone legal conclusion, care-quality finding, staffing formula input, CT applicability input, or current-only facility status source.

## 2. Source Basis

Validated source from Phase 11D.7:

- `source_data/cms_survey/NH_FireSafetyCitations_May2026.csv`

Official CMS source metadata:

- CMS dataset title: `Fire Safety Deficiencies`
- CMS dataset ID: `ifjz-ge4w`
- source filename: `NH_FireSafetyCitations_May2026.csv`
- modified date: May 1, 2026
- released date: May 27, 2026
- acquired date: June 22, 2026
- source URL: <https://data.cms.gov/provider-data/sites/default/files/resources/a212e8d9a0e8d36ebee28b8334485334_1778861750/NH_FireSafetyCitations_May2026.csv>

Validation results:

- total source rows: 199,760
- Connecticut rows: 2,135
- unique Connecticut CCNs: 178
- joined to current staffing data: 178
- unmatched CT Fire Safety Deficiency CCNs: 0
- survey date range: 2018-11-08 to 2026-02-27
- CT K-tag rows: 2,007
- CT E-tag rows: 128
- tag version coverage: all CT rows are `New`
- Citation Descriptions lookup misses: 145
- lookup miss codes: `K-0211` (143 rows), `K-0133` (2 rows)

## 3. Future Output File

Proposed future output:

- `data/nursing_home_fire_safety_deficiencies_ct.json`

Do not create this output in Phase 11D.8. It should be created only after builder implementation and validation expectations are approved.

The file should remain separate from:

- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_staffing_history_ct.json`
- `data/nursing_home_citation_descriptions.json`
- future health deficiency, penalty, survey summary, and CT DPH document outputs

## 4. Recommended JSON Shape

```json
{
  "metadata": {
    "source_name": "CMS Provider Data Catalog Fire Safety Deficiencies",
    "source_file": "NH_FireSafetyCitations_May2026.csv",
    "source_url_or_endpoint": "https://data.cms.gov/provider-data/sites/default/files/resources/a212e8d9a0e8d36ebee28b8334485334_1778861750/NH_FireSafetyCitations_May2026.csv",
    "cms_dataset_id": "ifjz-ge4w",
    "source_month": "May",
    "source_year": 2026,
    "acquired_date": "2026-06-22",
    "build_date": "YYYY-MM-DD",
    "state_filter": "CT",
    "source_row_count": 199760,
    "ct_row_count": 2135,
    "unique_ct_ccn_count": 178,
    "joined_current_ccn_count": 178,
    "unmatched_current_ccn_count": 0,
    "survey_date_min": "2018-11-08",
    "survey_date_max": "2026-02-27",
    "k_tag_count": 2007,
    "e_tag_count": 128,
    "citation_description_lookup_miss_count": 145,
    "limitations": [
      "Fire safety deficiencies are citation-level records.",
      "One facility may have many citation rows.",
      "Survey date and processing date are not the same.",
      "K-tags are fire safety/life safety code tags.",
      "E-tags are emergency preparedness tags.",
      "K-tags and E-tags should remain separate from health F-tags unless a future display labels the sources and denominators clearly.",
      "Citation descriptions are lookup/reference text, not proof of a facility finding by themselves.",
      "Do not apply health F-tag harm/immediate-jeopardy grouping to fire safety rows unless separately validated."
    ]
  },
  "deficiencies": [
    {
      "ccn": "075000",
      "provider_name": "Example Facility",
      "state": "CT",
      "survey_date": "2025-01-01",
      "survey_year": 2025,
      "survey_type": "Fire Safety",
      "deficiency_prefix": "K",
      "deficiency_tag_number": "0211",
      "deficiency_code": "K-0211",
      "deficiency_description": "CMS source description text",
      "tag_version": "New",
      "scope_severity_code": "D",
      "standard_deficiency": true,
      "complaint_deficiency": false,
      "correction_date": "2025-02-01",
      "citation_under_idr": false,
      "citation_under_iidr": false,
      "processing_date": "2026-05-01",
      "source_row_hash": "sha256-of-normalized-source-row",
      "citation_description_lookup_matched": false,
      "citation_description_category": null,
      "citation_description_text": null
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
| `cms_dataset_id` | CMS Provider Data Catalog dataset identifier, currently `ifjz-ge4w`. |
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
| `k_tag_count` | Number of emitted rows with deficiency prefix `K`. |
| `e_tag_count` | Number of emitted rows with deficiency prefix `E`. |
| `citation_description_lookup_miss_count` | Number of emitted rows whose K/E tag does not join to citation descriptions lookup. |
| `limitations` | Plain-language limitations that must travel with the dataset. |

## 6. Deficiency Record Field Definitions

| Field | Source / rule | Definition |
|---|---|---|
| `ccn` | `CMS Certification Number (CCN)` | Normalized six-character CCN with leading zeroes preserved. |
| `provider_name` | `Provider Name` | CMS source provider name. |
| `state` | `State` | State abbreviation, expected `CT` after filtering. |
| `survey_date` | `Survey Date` | Citation/survey date from source. |
| `survey_year` | Derived from `survey_date` | Calendar year of survey date. |
| `survey_type` | `Survey Type` | Survey type, expected `Fire Safety` in validated CT rows. |
| `deficiency_prefix` | `Deficiency Prefix` | `K` for fire safety/life safety tags or `E` for emergency preparedness tags. |
| `deficiency_tag_number` | `Deficiency Tag Number` | Zero-padded K/E tag number preserved as text. |
| `deficiency_code` | Derived from prefix + tag | Canonical code such as `K-0211` or `E-0004`. |
| `deficiency_description` | `Deficiency Description` | CMS source description text. This is short tag/citation text, not long CMS-2567 narrative. |
| `tag_version` | `Tag Version` | CMS source tag version. All validated CT rows were `New`. |
| `scope_severity_code` | `Scope Severity Code` | Original CMS structured scope/severity code. Preserve as source context. |
| `standard_deficiency` | `Standard Deficiency` | Boolean conversion of Y/N indicator. |
| `complaint_deficiency` | `Complaint Deficiency` | Boolean conversion of Y/N indicator. |
| `correction_date` | `Correction Date` | Correction date when present; null if blank. |
| `citation_under_idr` | `Citation under IDR` | Boolean conversion of Y/N indicator. |
| `citation_under_iidr` | `Citation under IIDR` | Boolean conversion of Y/N indicator. |
| `processing_date` | `Processing Date` | CMS processing/source date. |
| `source_row_hash` | Derived | Stable hash of normalized source row values for audit and deduplication. |
| `citation_description_lookup_matched` | Derived | Whether `deficiency_code` matched citation descriptions lookup. |
| `citation_description_category` | Lookup | Category from citation descriptions lookup, if included. |
| `citation_description_text` | Lookup | Lookup description text, if included. |

## 7. Fire Safety And Emergency Preparedness Semantics

- Fire safety deficiencies are citation-level records.
- One facility may have many citation rows.
- One survey may have many citation rows.
- Citation row counts are not survey counts.
- Citation row counts are not facility counts.
- Survey date and processing date are not the same.
- Correction date is not survey date.
- `K` = fire safety / life safety code tag.
- `E` = emergency preparedness tag.
- Fire safety K-tags and emergency preparedness E-tags should remain separate from health F-tags in future UI, exports, summaries, and denominator planning unless a combined display uses explicit labels.
- Citation descriptions are lookup/reference text and are not proof that a facility received a citation by themselves.

## 8. Scope / Severity Guardrails

The source contains structured `Scope Severity Code` values. Validation-only CT counts from Phase 11D.7:

| Scope/severity code | CT citation rows |
|---|---:|
| `D` | 1,556 |
| `E` | 338 |
| `F` | 238 |
| `J` | 2 |
| `K` | 1 |

Guardrails:

- Preserve the original `Scope Severity Code`.
- Do not apply the Health Deficiencies harm/immediate-jeopardy grouping to Fire Safety Deficiencies unless CMS interpretation and project denominator rules are separately validated.
- Do not infer harm/IJ from deficiency description text.
- Do not collapse citation-level scope/severity counts into survey-level, facility-level, facility-year, or state-level percentages without explicit denominator labels.
- Any future fire safety severity grouping should be documented separately from health deficiency harm/IJ mapping.

## 9. Citation Description Lookup Join

Future builder may optionally read:

- `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`

Join key:

- fire safety source: normalized `Deficiency Prefix` + zero-padded `Deficiency Tag Number`
- citation descriptions source: `Deficiency Prefix and Number`
- canonical format: `K-0211`, `E-0004`, etc.

Expected behavior:

- Set `citation_description_lookup_matched` to `true` only when an official lookup row exists.
- Leave lookup category/text null when no official lookup row exists.
- Preserve the source row's own `Deficiency Description` regardless of lookup status.
- Do not synthesize lookup descriptions manually.
- Do not patch CMS source data.

Known Phase 11D.8 lookup gaps:

| Code | CT rows | Source row status |
|---|---:|---|
| `K-0211` | 143 | Present in Fire Safety source; absent from Citation Descriptions source. |
| `K-0133` | 2 | Present in Fire Safety source; absent from Citation Descriptions source. |

## 10. Future Builder Plan

Proposed future builder:

- `scripts/build_nursing_home_fire_safety_deficiencies_ct.py`

Builder responsibilities:

1. Read the ignored CMS Fire Safety Deficiencies CSV from `source_data/cms_survey/`.
2. Read `data/nursing_home_staffing_ct.json` for current CCN join validation.
3. Optionally read the ignored CMS Citation Descriptions CSV from `source_data/cms_survey/`.
4. Filter to Connecticut rows.
5. Normalize CCNs while preserving leading zeroes.
6. Validate joins to current staffing data.
7. Normalize K/E tags into stable `deficiency_code` values.
8. Preserve source fire safety fields required by this contract.
9. Preserve original `Scope Severity Code` without health harm/IJ grouping.
10. Join citation descriptions where available.
11. Mark unmatched lookup rows without failing the build if the gap is documented and approved.
12. Include metadata matching this data contract.
13. Fail loudly on missing required source columns, invalid dates, malformed tags, or unmatched CT CCNs unless explicitly approved.
14. Print a validation summary.

Suggested default behavior:

- validation-only dry run without writing output

Suggested preview flag:

- `--write-testing-preview`

Suggested non-runtime preview path:

- `data/testing/nursing_home_fire_safety_deficiencies_ct_preview.json`

Do not write `data/nursing_home_fire_safety_deficiencies_ct.json` until a future runtime build phase is approved.

## 11. Validation Requirements Before Runtime Use

Before `data/nursing_home_fire_safety_deficiencies_ct.json` is created for public runtime use:

- confirm official CMS source file and dataset metadata;
- validate source schema and required columns;
- validate total, CT, and unique CCN row counts;
- validate all CT source CCNs join to the intended current/context facility universe;
- validate survey date parsing and date range;
- validate K/E prefix counts;
- validate malformed tag count is zero;
- validate `Tag Version` handling;
- document Citation Descriptions lookup gaps and any official supplemental source used;
- preserve lookup miss metadata;
- confirm no health F-tag harm/IJ grouping is applied to fire safety rows;
- confirm future UI labels distinguish K-tags, E-tags, and health F-tags.

## 12. App Use Cases

Possible future uses after runtime integration is approved:

- Facility dossier fire safety and emergency preparedness section.
- Recent fire safety citation timeline.
- K-tag and E-tag lookup/reference display.
- Survey recency context.
- Exportable facility fire safety summary.
- State-level fire safety citation counts with clear citation-level denominators.

## 13. Guardrails

- Survey/enforcement findings must be source-backed.
- Do not merge F-tags, K-tags, and E-tags without explicit labeling.
- Do not treat citation descriptions as facility findings.
- Do not treat penalties, health deficiencies, and fire safety deficiencies as interchangeable.
- Preserve survey date, correction date, and processing date separately.
- Preserve citation-level, survey-level, facility-level, facility-year, and state-level denominators separately.
- Do not use citations as legal conclusions beyond official source language.
- Do not make causation claims.
- Do not modify staffing formulas, current/context staffing JSON, historical PBJ JSON, geography JSON, facility status review JSON, or CT applicability logic.

## 14. Recommendation

The Fire Safety Deficiencies source is likely ready for a future dry-run builder phase, with one important caveat: `K-0211` and `K-0133` should remain documented lookup gaps unless CMS publishes official Citation Descriptions rows or another official supplemental source is validated.

