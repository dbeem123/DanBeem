# CMS Citation Descriptions Source Validation

Phase 11D.2 source acquisition and validation document. This document validates the CMS Nursing Home Data Dictionary and Citation Code Look-up source file for future F-tag, K-tag, and emergency-preparedness tag description work.

This phase does not build public UI, integrate runtime datasets, change formulas, change generated staffing data, change Connecticut applicability logic, modify current or historical staffing JSON, modify runtime JS/HTML, or create public-facing JSON outputs.

## 1. Acquisition Summary

Acquisition date: June 22, 2026.

| Source | Official CMS endpoint/source URL | Local placement | File size |
|---|---|---|---:|
| CMS Nursing Home Data Dictionary | <https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/nursing_home/NH_Data_Dictionary.pdf> | `source_data/cms_survey/NH_Data_Dictionary.pdf` | 1,741,471 bytes |
| CMS Citation Code Look-up | <https://data.cms.gov/provider-data/sites/default/files/resources/df008647017ce09edbee2e2dbacd76b4_1778861774/NH_CitationDescriptions_May2026.csv> | `source_data/cms_survey/NH_CitationDescriptions_May2026.csv` | 96,713 bytes |

CMS Provider Data search metadata identified the Citation Code Look-up dataset as:

- title: `Citation Code Look-up`;
- dataset identifier: `tagd-9999`;
- modified date: May 1, 2026;
- released date: May 27, 2026;
- current source filename: `NH_CitationDescriptions_May2026.csv`.

The CMS Nursing Home Data Dictionary downloaded in this phase is titled/marked `Nursing Home Data Dictionary, updated May 2026` and identifies the citation lookup source file pattern as `NH_CitationDescriptions_MonYYYY.csv`.

## 2. File Placement

Raw source files acquired in this phase:

- `source_data/cms_survey/NH_Data_Dictionary.pdf`
- `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`

No health deficiency, fire safety deficiency, penalty, survey summary, inspection date, or other large CMS datasets were downloaded in this phase.

## 3. Citation Descriptions Schema

Observed CSV columns:

| Column | Data dictionary meaning | Validation note |
|---|---|---|
| `Deficiency Prefix` | Deficiency prefix, such as F, K, or E | Present. |
| `Deficiency Tag Number` | Deficiency tag number | Present. Values are zero-padded text in the CSV. |
| `Deficiency Prefix and Number` | Combined code, such as `F-0880` | Present. Recommended future lookup key. |
| `Deficiency Description` | Plain-language citation/tag description | Present. |
| `Deficiency Category` | Category description for Care Compare website | Present. |

The file is a lookup/reference table. It does not show that any facility received a citation and must not replace actual Health Deficiencies or Fire Safety Deficiencies rows.

## 4. Record Counts And Coverage

Validation source:

- `python scripts/validate_nursing_home_citation_descriptions.py`

Observed row count:

- 643 records.

Counts by `Deficiency Prefix`:

| Prefix | Meaning for future use | Count |
|---|---|---:|
| `E` | Emergency preparedness tags | 26 |
| `F` | Health deficiency / F-tags | 393 |
| `K` | Fire/life safety tags | 224 |

Coverage finding:

- The lookup includes F-tags, K-tags, and E-tags.
- It can support future plain-language display for health F-tags, fire/life-safety K-tags, and emergency-preparedness E-tags.
- Future UI/data contracts should keep F, K, and E tag contexts labeled separately.

## 5. Uniqueness And Missing-Value Findings

Key field reviewed:

- `Deficiency Prefix and Number`

Findings:

| Check | Result |
|---|---:|
| Missing required columns | 0 |
| Missing `Deficiency Prefix and Number` | 0 |
| Duplicate `Deficiency Prefix and Number` | 0 |
| Missing `Deficiency Description` | 0 |
| Missing `Deficiency Category` | 0 |

The combined `Deficiency Prefix and Number` field is unique and appears suitable as the primary lookup key for a future `data/nursing_home_citation_descriptions.json` data contract.

## 6. Risks And Caveats

- The file is national/reference lookup data, not Connecticut-specific facility citation data.
- Citation descriptions are not actual citation findings.
- F-tags, K-tags, and E-tags should not be merged without labels.
- The lookup does not provide harm/immediate-jeopardy status. Harm/IJ analysis must come from structured scope/severity fields in Health Deficiencies and Fire Safety Deficiencies, not this lookup text.
- CMS resource URLs use hashed resource folders. Future refresh scripts should discover the current distribution URL from official CMS Provider Data metadata rather than hardcoding the hash path.
- The data dictionary and citation lookup are both May 2026-current in this acquisition. Future source refreshes should confirm that their source periods remain aligned.

## 7. Readiness Recommendation

Readiness: **ready to support a future citation descriptions data contract after data-contract design**.

Recommended next phase:

**Phase 11D.3: Citation Descriptions Data Contract And Non-Runtime Lookup Prototype**

Suggested scope:

1. Design `data/nursing_home_citation_descriptions.json`.
2. Keep the file reference-only and separate from facility citation findings.
3. Preserve prefix, tag number, combined key, description, category, source filename, source URL, and source release date.
4. Add validation checks for uniqueness and required fields.
5. Do not wire the lookup into public UI until Health/Fire citation source rows are validated.

Alternative next source-acquisition phase:

**Phase 11D.3: CMS Health Deficiencies Source Acquisition Validation**

This would acquire `NH_HealthCitations_May2026.csv` or the latest available official CMS Health Deficiencies file and validate CT row counts, CCN joins, dates, F-tags, scope/severity, and harm/IJ mapping.

## 8. Runtime Guardrail Confirmation

This phase acquired and validated reference source files only. It did not create runtime JSON, alter staffing data, alter historical PBJ data, modify formulas, change CT applicability logic, or change public behavior.
