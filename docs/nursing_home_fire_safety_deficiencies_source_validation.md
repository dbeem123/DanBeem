# CMS Fire Safety Deficiencies Source Validation

Phase 11D.7 source acquisition and validation document. This validates the CMS Nursing Home Fire Safety Deficiencies / Fire Safety Citations source file for future life-safety and fire-safety survey context work.

This phase does not build public UI, create runtime JSON, change runtime JS/HTML, change staffing formulas, change generated staffing data, change Connecticut applicability logic, modify current or historical staffing JSON, modify health deficiencies runtime JSON, modify citation descriptions runtime JSON, modify geography JSON, or modify facility status review JSON.

## 1. Acquisition Summary

Acquisition date: June 22, 2026.

| Source | Official CMS endpoint/source URL | Local placement | File size |
|---|---|---|---:|
| CMS Fire Safety Deficiencies | <https://data.cms.gov/provider-data/sites/default/files/resources/a212e8d9a0e8d36ebee28b8334485334_1778861750/NH_FireSafetyCitations_May2026.csv> | `source_data/cms_survey/NH_FireSafetyCitations_May2026.csv` | 69,121,738 bytes |

CMS Provider Data metadata previously identified the source as:

- title: `Fire Safety Deficiencies`;
- dataset identifier: `ifjz-ge4w`;
- modified date: May 1, 2026;
- released date: May 27, 2026;
- current source filename: `NH_FireSafetyCitations_May2026.csv`.

Raw source files under `source_data/` are ignored by Git and should remain uncommitted unless explicitly approved.

## 2. Validation Method

Validation script:

- `scripts/validate_nursing_home_fire_safety_deficiencies.py`

The script:

- reads the ignored CMS Fire Safety Deficiencies CSV from `source_data/cms_survey/`;
- detects the latest `NH_FireSafetyCitations_*.csv` file by filename;
- loads `data/nursing_home_staffing_ct.json` for current app CCN join testing;
- filters Connecticut rows by `State == CT`;
- normalizes CCNs to six characters;
- tests K/E tag lookup readiness against `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`;
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
| `Survey Type` | All Connecticut rows in this source were `Fire Safety`. |
| `Deficiency Prefix` | Connecticut rows include `K` and `E` prefixes. |
| `Deficiency Category` | CMS category description. |
| `Deficiency Tag Number` | K/E tag number, zero-padded text. |
| `Tag Version` | Tag version field; all CT rows were `New`. |
| `Deficiency Description` | Short tag/citation description. This is not long CMS-2567 narrative text. |
| `Scope Severity Code` | Structured scope/severity code is present. |
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
| Total source rows | 199,760 |
| Connecticut citation rows | 2,135 |
| Unique Connecticut CCNs in Fire Safety Deficiencies source | 178 |
| Current staffing CCNs in `data/nursing_home_staffing_ct.json` | 196 |
| CT Fire Safety Deficiency CCNs joined to current staffing data | 178 |
| CT Fire Safety Deficiency CCNs not joined to current staffing data | 0 |

Provider/CCN field used:

- `CMS Certification Number (CCN)`

CCNs were normalized to six characters with leading zeroes preserved.

Join interpretation:

- All 178 unique CT fire safety source CCNs joined to current staffing data.
- Current staffing facilities without fire safety citation rows in this source should not be inferred as having no life-safety issues without reviewing CMS source inclusion rules and survey windows.

## 5. Survey Date Validation

| Check | Result |
|---|---:|
| Missing survey dates | 0 |
| Invalid survey dates | 0 |
| Minimum CT survey date | 2018-11-08 |
| Maximum CT survey date | 2026-02-27 |

Connecticut citation rows by survey calendar year:

| Year | Citation rows |
|---|---:|
| 2018 | 1 |
| 2019 | 189 |
| 2020 | 65 |
| 2021 | 323 |
| 2022 | 278 |
| 2023 | 371 |
| 2024 | 514 |
| 2025 | 370 |
| 2026 | 24 |

Guardrail: these are citation rows by survey date, not current-only findings. Any future display must preserve survey date and source processing date separately.

## 6. K/E Tag Coverage And Citation Description Join Readiness

| Check | Result |
|---|---:|
| Distinct citation codes in CT rows | 84 |
| Malformed citation codes | 0 |
| Citation lookup misses against `NH_CitationDescriptions_May2026.csv` | 145 |

Citation rows by prefix:

| Prefix | Count |
|---|---:|
| `E` | 128 |
| `K` | 2,007 |

Tag version:

| Tag version | Count |
|---|---:|
| `New` | 2,135 |

Citation lookup misses:

| Code | Missed rows |
|---|---:|
| `K-0211` | 143 |
| `K-0133` | 2 |

Findings:

- The source contains both K-tags and emergency-preparedness E-tags.
- Fire safety/life-safety K-tags and emergency-preparedness E-tags should remain separate from health F-tags.
- Most CT fire safety citation codes can join to the validated Citation Descriptions source, but `K-0211` and `K-0133` require follow-up before a complete description lookup can be guaranteed.
- Do not force unmatched K-tags into the lookup or copy descriptions from memory.

## 7. Scope/Severity Findings

Structured field:

- `Scope Severity Code`

Unique CT scope/severity values:

| Code | Citation rows |
|---|---:|
| `D` | 1,556 |
| `E` | 338 |
| `F` | 238 |
| `J` | 2 |
| `K` | 1 |

Feasibility decision:

- Fire safety rows do contain structured scope/severity values.
- Do not automatically apply the Health Deficiencies harm/IJ mapping to Fire Safety Deficiencies without confirming official CMS interpretation for fire/life-safety citations and deciding whether a combined harm/IJ summary is appropriate.
- Fire safety K-tags should remain separate from health F-tags in future UI, exports, and denominator planning.

## 8. Survey Indicator Findings

Survey type:

| Value | Count |
|---|---:|
| `Fire Safety` | 2,135 |

Standard deficiency indicator:

| Value | Count |
|---|---:|
| `Y` | 2,111 |
| `N` | 24 |

Complaint deficiency indicator:

| Value | Count |
|---|---:|
| `Y` | 24 |
| `N` | 2,111 |

Infection control inspection deficiency indicator:

| Value | Count |
|---|---:|
| `N` | 2,135 |

Deficiency corrected status:

| Value | Count |
|---|---:|
| `Deficient, Provider has date of correction` | 2,108 |
| `Deficient, Provider has no plan of correction` | 8 |
| `Deficient, Provider has plan of correction` | 10 |
| `Past Non-Compliance` | 8 |
| `Waiver has been granted` | 1 |

Missing correction dates:

- 9 rows.

## 9. Deficiency Text Findings

The `Deficiency Description` field is present for every Connecticut row.

Observed description length:

- minimum: 29 characters;
- maximum: 183 characters.

Interpretation:

- This field appears to contain short CMS tag/citation description text, not long-form CMS-2567 narrative findings.
- Long narrative statements of deficiencies and plans of correction would require separate CMS/CT DPH document source validation.

## 10. Risks And Caveats

- The source file is 69,121,738 bytes and should remain ignored unless explicitly approved for commit.
- The source is citation-level, not survey-level or facility-level summary data.
- Fire safety/life-safety citations are not health F-tags and should not be merged with health deficiencies without clear labels and denominator rules.
- The source includes both `K` and `E` prefixes.
- Citation Descriptions lookup has 145 CT misses for `K-0211` and `K-0133`; this needs review before complete lookup-backed display.
- Scope/severity exists, but public harm/IJ interpretation should not be assumed from the health-deficiency mapping without method review.
- The file includes survey dates from 2018 through 2026, so future UI must avoid presenting all rows as current findings.

## 11. Readiness Recommendation

Readiness: **ready for data contract planning with caveats, not ready for public/runtime use.**

Recommended next phase:

**Phase 11D.8: Fire Safety Deficiencies Data Contract And Lookup Gap Review**

Suggested scope:

1. Define future `data/nursing_home_fire_safety_deficiencies_ct.json`.
2. Preserve K/E citation rows separately from Health Deficiencies.
3. Investigate why `K-0211` and `K-0133` are absent from the May 2026 Citation Descriptions lookup.
4. Decide whether fire safety scope/severity should use the same derived grouping as health citations or a separate method.
5. Preserve survey date, correction date, processing date, scope/severity, tag version, standard/complaint indicators, and IDR/IIDR indicators.

Alternative next source acquisition:

**Phase 11D.8: CMS Penalties / Enforcement Source Acquisition Validation**

This would validate CMP/payment-denial rows separately from citations.

## 12. Runtime Guardrail Confirmation

This phase acquired and validated raw CMS source data only. It did not create app runtime outputs, modify public tools, or change any staffing/geography/formula behavior.
