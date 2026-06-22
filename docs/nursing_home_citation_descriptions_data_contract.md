# Nursing Home Citation Descriptions Data Contract

Phase 11D.3 data contract and builder planning document. This document defines a future app-ready citation-description lookup output, but it does not create runtime JSON, build public UI, modify runtime JS/HTML, change staffing formulas, change generated staffing data, alter current or historical staffing JSON, or change Connecticut applicability logic.

## 1. Purpose

`data/nursing_home_citation_descriptions.json` should become a reference lookup for CMS nursing home citation/tag descriptions. It should help future tools display plain-language descriptions for F-tags, K-tags, and emergency-preparedness E-tags after source validation and build-script validation are complete.

This lookup is reference text only. It does not mean a facility received a citation. It must not be treated as a survey finding, deficiency event, enforcement action, legal conclusion, harm/immediate-jeopardy indicator, or facility quality finding.

## 2. Source Basis

Validated source files from Phase 11D.2:

- `source_data/cms_survey/NH_Data_Dictionary.pdf`
- `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`

Official CMS source metadata:

- CMS dataset title: `Citation Code Look-up`
- CMS dataset ID: `tagd-9999`
- source filename: `NH_CitationDescriptions_May2026.csv`
- modified date: May 1, 2026
- released date: May 27, 2026
- acquisition date: June 22, 2026

Validated record counts:

- total records: 643
- F-tags: 393
- K-tags: 224
- E-tags: 26
- duplicate `Deficiency Prefix and Number` values: 0
- missing required fields: 0

## 3. Future Output File

Proposed future output:

- `data/nursing_home_citation_descriptions.json`

Do not create this output in Phase 11D.3. It should be created only after the builder is approved and validation expectations are documented.

The output should be national/reference data, not Connecticut-specific facility data. It should remain separate from future Health Deficiencies, Fire Safety Deficiencies, Penalties, Survey Summary, and facility-level survey/enforcement outputs.

## 4. Recommended JSON Shape

```json
{
  "metadata": {
    "source_name": "CMS Provider Data Catalog Citation Code Look-up",
    "source_file": "NH_CitationDescriptions_May2026.csv",
    "source_url_or_endpoint": "https://data.cms.gov/provider-data/sites/default/files/resources/df008647017ce09edbee2e2dbacd76b4_1778861774/NH_CitationDescriptions_May2026.csv",
    "cms_dataset_id": "tagd-9999",
    "source_month": "May",
    "source_year": 2026,
    "acquired_date": "2026-06-22",
    "build_date": "YYYY-MM-DD",
    "record_count": 643,
    "f_tag_count": 393,
    "k_tag_count": 224,
    "e_tag_count": 26,
    "limitations": [
      "Citation descriptions are lookup/reference text only.",
      "Citation descriptions do not mean a facility received that citation.",
      "Citation descriptions must not be treated as survey findings.",
      "Harm and immediate jeopardy analysis require structured scope/severity fields from citation event files."
    ]
  },
  "citations": [
    {
      "citation_code": "F-0880",
      "prefix": "F",
      "tag_number": "0880",
      "description": "Example description text",
      "category": "Infection Control Deficiencies",
      "citation_type": "health_deficiency_f_tag",
      "normalized_code": "F0880",
      "display_label": "F-0880"
    }
  ]
}
```

## 5. Field Definitions

### Metadata

| Field | Definition |
|---|---|
| `source_name` | Human-readable official source name. |
| `source_file` | Raw CMS source filename used for the build. |
| `source_url_or_endpoint` | Official CMS source URL or metadata endpoint used to acquire the source. |
| `cms_dataset_id` | CMS Provider Data Catalog dataset identifier, currently `tagd-9999`. |
| `source_month` | Source month parsed from source filename/metadata. |
| `source_year` | Source year parsed from source filename/metadata. |
| `acquired_date` | Date the raw source file was acquired locally. |
| `build_date` | Date the JSON output was built. |
| `record_count` | Number of citation lookup records emitted. |
| `f_tag_count` | Number of records with prefix `F`. |
| `k_tag_count` | Number of records with prefix `K`. |
| `e_tag_count` | Number of records with prefix `E`. |
| `limitations` | Plain-language limitations that must travel with the lookup. |

### Citation Records

| Field | Source / rule | Definition |
|---|---|---|
| `citation_code` | `Deficiency Prefix and Number` | CMS formatted code, such as `F-0880`, `K-0918`, or `E-0001`. |
| `prefix` | `Deficiency Prefix` | CMS deficiency prefix. |
| `tag_number` | `Deficiency Tag Number` | Zero-padded tag number from the CMS source. Preserve as text. |
| `description` | `Deficiency Description` | Plain-language citation/tag description from CMS. |
| `category` | `Deficiency Category` | CMS Care Compare category description. |
| `citation_type` | Derived from `prefix` | Project label for source context. |
| `normalized_code` | Derived | Uppercase prefix plus zero-padded number without punctuation, such as `F0880`. |
| `display_label` | Derived | User-facing label, normally identical to `citation_code`. |

## 6. Citation Type Mapping

| Prefix | Citation type | Meaning |
|---|---|---|
| `F` | `health_deficiency_f_tag` | Health deficiency / F-tag. |
| `K` | `fire_safety_k_tag` | Fire safety / life safety K-tag. |
| `E` | `emergency_preparedness_tag` | Emergency preparedness tag. |

Unknown or future prefixes should fail validation unless the builder is explicitly updated with a documented mapping.

## 7. Normalization Rules

- Trim whitespace from all source fields.
- Uppercase `prefix`.
- Preserve `tag_number` as text, including leading zeroes.
- Use `Deficiency Prefix and Number` as the canonical source key.
- Validate that `citation_code` equals `<prefix>-<tag_number>` after normalization.
- Create `normalized_code` by removing punctuation from `citation_code` and uppercasing it.
- Create `display_label` as the canonical hyphenated code, such as `F-0880`.
- Do not rewrite CMS descriptions except for trimming outer whitespace.
- Preserve CMS category text exactly except for trimming outer whitespace.

## 8. Validation Requirements

A future builder should fail loudly when:

- the raw source file is missing;
- required columns are missing;
- any record is missing `Deficiency Prefix`;
- any record is missing `Deficiency Tag Number`;
- any record is missing `Deficiency Prefix and Number`;
- any record is missing `Deficiency Description`;
- any record is missing `Deficiency Category`;
- duplicate `Deficiency Prefix and Number` values are present;
- a prefix is outside the approved mapping;
- the emitted record count does not equal the parsed row count;
- metadata counts do not match emitted citation counts.

The existing validator remains the source-level check:

- `scripts/validate_nursing_home_citation_descriptions.py`

## 9. Builder Plan

Proposed future builder:

- `scripts/build_nursing_home_citation_descriptions.py`

Recommended behavior:

1. Read `source_data/cms_survey/NH_CitationDescriptions_May2026.csv` or the latest matching `NH_CitationDescriptions_*.csv`.
2. Validate required columns and uniqueness.
3. Normalize citation codes using the rules in this contract.
4. Derive `citation_type`, `normalized_code`, and `display_label`.
5. Add metadata with source file, CMS dataset ID, source URL, source month/year, acquired date, build date, counts, and limitations.
6. Write `data/nursing_home_citation_descriptions.json`.
7. Print a concise build summary.
8. Exit nonzero on validation failure.

Do not create this builder in Phase 11D.3 unless a future implementation phase explicitly approves generating the JSON output. Keeping this phase contract-only avoids introducing an app-ready runtime file before health/fire citation event rows are validated.

## 10. Relationship To Future Survey Data

Future Health Deficiencies and Fire Safety Deficiencies datasets should join to this lookup by:

- `Deficiency Prefix and Number`, or
- `Deficiency Prefix` + `Deficiency Tag Number`.

The lookup should support readable labels/descriptions in:

- future facility dossier inspection/enforcement sections;
- F-tag/K-tag lookup views;
- CSV exports with optional tag descriptions;
- methodology/reference pages.

It should not be used to count citations, surveys, harm/IJ events, penalties, or facility findings. Those counts must come from citation event and enforcement source files.

## 11. Runtime Guardrails

- No public UI should read this future output until explicitly wired in a later phase.
- The lookup should not modify `data/nursing_home_staffing_ct.json`.
- The lookup should not modify `data/nursing_home_staffing_history_ct.json`.
- The lookup should not affect staffing formulas, CT applicability logic, county filters, PBJ history, or current CMS snapshot context.
- Citation descriptions should not be displayed as if they are facility-specific survey findings.

## 12. Recommended Next Phase

Recommended next phase:

**Phase 11D.4: CMS Health Deficiencies Source Acquisition Validation**

Reason:

The citation descriptions source is now validated and contract-ready. The next dependency for actual survey context is the citation event file containing facility CCNs, survey dates, F-tags, scope/severity, correction dates, and standard/complaint/infection-control indicators.

Alternative:

**Phase 11D.4: Build Non-Runtime Citation Descriptions Lookup**

This would create `scripts/build_nursing_home_citation_descriptions.py` and generate `data/nursing_home_citation_descriptions.json`, but only if the project wants the reference lookup in place before acquiring facility-level citation rows.
