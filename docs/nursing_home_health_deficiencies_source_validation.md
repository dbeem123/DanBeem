# CMS Health Deficiencies Source Validation

Phase 11D.4 source acquisition and validation document. This validates the CMS Nursing Home Health Deficiencies / Health Citations source file for future facility-level survey context work.

This phase does not build public UI, create runtime JSON, change runtime JS/HTML, change staffing formulas, change generated staffing data, change Connecticut applicability logic, modify current or historical staffing JSON, modify geography JSON, modify facility status review JSON, or create citation summaries.

## 1. Acquisition Summary

Acquisition date: June 22, 2026.

| Source | Official CMS endpoint/source URL | Local placement | File size |
|---|---|---|---:|
| CMS Health Deficiencies | <https://data.cms.gov/provider-data/sites/default/files/resources/e269c04e82fe86040cd70b7ba3dd4853_1778861752/NH_HealthCitations_May2026.csv> | `source_data/cms_survey/NH_HealthCitations_May2026.csv` | 164,917,215 bytes |

CMS Provider Data search metadata identified the source as:

- title: `Health Deficiencies`;
- dataset identifier: `r5ix-sfxw`;
- modified date: May 1, 2026;
- released date: May 27, 2026;
- next update date listed by CMS metadata: June 24, 2026;
- current source filename: `NH_HealthCitations_May2026.csv`.

Raw source files under `source_data/` are ignored by Git and should remain uncommitted unless explicitly approved.

## 2. Validation Method

Validation script:

- `scripts/validate_nursing_home_health_deficiencies.py`

The script:

- reads the ignored CMS source CSV from `source_data/cms_survey/`;
- detects the latest `NH_HealthCitations_*.csv` file by filename;
- loads `data/nursing_home_staffing_ct.json` for current app CCN join testing;
- filters Connecticut rows by `State == CT`;
- normalizes CCNs to six characters;
- tests F-tag lookup readiness against `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`;
- prints validation results only;
- does not write runtime JSON.

## 3. Schema Summary

Observed CSV columns:

| Column | Validation/use note |
|---|---|
| `CMS Certification Number (CCN)` | Primary provider join key. Preserve leading zeroes. |
| `Provider Name` | Source provider name. |
| `Provider Address` | Source provider street address. |
| `City/Town` | Source city/town. |
| `State` | Used for Connecticut filtering. |
| `ZIP Code` | Source ZIP code. |
| `Survey Date` | Citation/survey date field. |
| `Survey Type` | All Connecticut rows in this source were `Health`. |
| `Deficiency Prefix` | All Connecticut rows used prefix `F`. |
| `Deficiency Category` | CMS category description. |
| `Deficiency Tag Number` | F-tag number, zero-padded text. |
| `Deficiency Description` | Short tag/citation description. This is not long CMS-2567 narrative text. |
| `Scope Severity Code` | Structured scope/severity code; supports future harm/IJ classification after method approval. |
| `Deficiency Corrected` | Correction/status text. |
| `Correction Date` | Correction date where available. Some rows are blank. |
| `Inspection Cycle` | Inspection cycle value. |
| `Standard Deficiency` | Y/N indicator. |
| `Complaint Deficiency` | Y/N indicator. |
| `Infection Control Inspection Deficiency` | Y/N indicator. |
| `Citation under IDR` | Y/N informal dispute resolution indicator. |
| `Citation under IIDR` | Y/N independent informal dispute resolution indicator. |
| `Location` | Source location string. |
| `Processing Date` | CMS processing/source date. |

Required source columns were present.

## 4. Row Counts And Connecticut Filtering

| Measure | Count |
|---|---:|
| Total source rows | 418,177 |
| Connecticut citation rows | 6,761 |
| Unique Connecticut CCNs in Health Deficiencies source | 191 |
| Current staffing CCNs in `data/nursing_home_staffing_ct.json` | 196 |
| CT Health Deficiency CCNs joined to current staffing data | 191 |
| CT Health Deficiency CCNs not joined to current staffing data | 0 |

Provider/CCN field used:

- `CMS Certification Number (CCN)`

CCNs were normalized to six characters with leading zeroes preserved.

Current staffing CCNs not present in the Health Deficiencies source:

| CCN | Current staffing facility name |
|---|---|
| 075001 | ST JOSEPH'S CENTER |
| 075351 | ABBOTT TERRACE HEALTH CENTER |
| 075415 | COUNTRYSIDE MANOR OF BRISTOL |
| 075432 | MATTATUCK HEALTH CARE FACILITY, INC. |
| 075441 | SPRINGS AT EAST HILL, THE |

This is a join observation only. It should not be treated as a new closure, certification, or provider-status finding. The separate geography/status review documents govern those source-backed status questions.

## 5. Survey Date Validation

| Check | Result |
|---|---:|
| Missing survey dates | 0 |
| Invalid survey dates | 0 |
| Minimum CT survey date | 2018-11-08 |
| Maximum CT survey date | 2026-03-31 |

Connecticut citation rows by survey calendar year:

| Year | Citation rows |
|---|---:|
| 2018 | 3 |
| 2019 | 554 |
| 2020 | 175 |
| 2021 | 545 |
| 2022 | 567 |
| 2023 | 1,280 |
| 2024 | 1,815 |
| 2025 | 1,591 |
| 2026 | 231 |

Guardrail: these are citation rows by survey date, not current-only findings. Any future display must preserve survey date and source processing date separately.

## 6. F-Tag Coverage And Citation Description Join Readiness

| Check | Result |
|---|---:|
| Distinct citation codes in CT rows | 164 |
| Malformed citation codes | 0 |
| Citation lookup misses against `NH_CitationDescriptions_May2026.csv` | 0 |

Citation rows by prefix:

| Prefix | Count |
|---|---:|
| `F` | 6,761 |

Findings:

- All Connecticut Health Deficiencies rows are F-tags.
- No K-tags or E-tags appeared in this Health Deficiencies file.
- All CT F-tags can join to the validated Citation Descriptions source using normalized `Deficiency Prefix and Number`.
- Fire safety K-tags and emergency preparedness E-tags should remain separate source layers.

## 7. Scope/Severity And Harm/IJ Feasibility

Structured field:

- `Scope Severity Code`

Unique CT scope/severity values:

| Code | Citation rows |
|---|---:|
| `B` | 372 |
| `C` | 91 |
| `D` | 4,838 |
| `E` | 1,105 |
| `F` | 110 |
| `G` | 167 |
| `H` | 3 |
| `I` | 2 |
| `J` | 66 |
| `K` | 5 |
| `L` | 2 |

Conservative structured grouping used for validation only:

| Group | Codes | Citation rows |
|---|---|---:|
| No actual harm, potential for minimal harm | `A`, `B`, `C` | 463 |
| No actual harm, potential for more than minimal harm | `D`, `E`, `F` | 6,053 |
| Actual harm, not immediate jeopardy | `G`, `H`, `I` | 172 |
| Immediate jeopardy | `J`, `K`, `L` | 73 |

Feasibility decision:

- Structured `Scope Severity Code` supports future harm/IJ classification.
- Future public use should cite the official CMS scope/severity definitions and preserve whether the denominator is citation-level, survey-level, facility-level, facility-year, or state-level.
- Do not infer harm or immediate jeopardy from narrative text.
- Do not create runtime summaries from this validation pass.

## 8. Survey Indicator Findings

Survey type:

| Value | Count |
|---|---:|
| `Health` | 6,761 |

Standard deficiency indicator:

| Value | Count |
|---|---:|
| `Y` | 4,970 |
| `N` | 1,791 |

Complaint deficiency indicator:

| Value | Count |
|---|---:|
| `Y` | 1,994 |
| `N` | 4,767 |

Infection control inspection deficiency indicator:

| Value | Count |
|---|---:|
| `N` | 6,761 |

Deficiency corrected status:

| Value | Count |
|---|---:|
| `Deficient, Provider has date of correction` | 6,519 |
| `Deficient, Provider has no plan of correction` | 35 |
| `Deficient, Provider has plan of correction` | 66 |
| `Past Non-Compliance` | 141 |

Missing correction dates:

- 57 rows.

## 9. Deficiency Text Findings

The `Deficiency Description` field is present for every Connecticut row.

Observed description length:

- minimum: 25 characters;
- maximum: 286 characters.

Interpretation:

- This field appears to contain short CMS tag/citation description text, not long-form CMS-2567 narrative findings.
- Long narrative statements of deficiencies, plans of correction, and survey document text would require separate CMS/CT DPH source validation.

## 10. Risks And Caveats

- The source file is large: 164,917,215 bytes.
- The source is citation-level, not survey-level or facility-level summary data.
- Citation row counts should not be treated as survey counts or facility counts.
- Current staffing data contains five CCNs not present in this Health Deficiencies source; this should remain a join observation, not a status finding.
- Harm/IJ classification is feasible from structured scope/severity, but public use requires official definition citations and denominator decisions.
- The file includes survey dates from 2018 through 2026, so future UI must avoid presenting all rows as current findings.
- Penalties/enforcement, fire safety K-tags, and survey summary/inspection date files remain separate future acquisitions.
- Citation descriptions are short reference text. They do not replace actual survey documents or CMS-2567 narratives.

## 11. Readiness Recommendation

Readiness: **ready for future data contract planning and builder design, not ready for public/runtime use.**

Recommended next phase:

**Phase 11D.5: Health Deficiencies Data Contract And Builder Planning**

Suggested scope:

1. Define future `data/nursing_home_health_deficiencies_ct.json`.
2. Preserve citation-level rows separately from summaries.
3. Preserve source metadata, survey date, correction date, processing date, scope/severity, standard/complaint indicators, IDR/IIDR indicators, and F-tag fields.
4. Define denominator rules before any facility/state summary.
5. Decide whether harm/IJ groupings are stored as derived fields or calculated at display time.

Alternative next source acquisition:

**Phase 11D.5: CMS Fire Safety Deficiencies Source Acquisition Validation**

This would validate K-tag/life-safety rows separately and test joins to the Citation Descriptions lookup.

## 12. Runtime Guardrail Confirmation

This phase acquired and validated raw CMS source data only. It did not create app runtime outputs, modify public tools, or change any staffing/geography/formula behavior.
