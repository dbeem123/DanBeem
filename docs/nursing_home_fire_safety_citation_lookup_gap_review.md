# Fire Safety Citation Description Lookup Gap Review

Phase 11D.8 review of the two Connecticut Fire Safety Deficiencies citation codes that did not match the May 2026 CMS Nursing Home Citation Descriptions lookup.

This document is documentation-only. It does not patch source data, create manual citation descriptions, build public UI, create runtime JSON, change runtime JS/HTML, alter staffing formulas, modify current or historical staffing JSON, change CT applicability logic, modify geography JSON, or change public app behavior.

## 1. Purpose

Phase 11D.7 validation found 145 Connecticut Fire Safety Deficiencies rows that did not match `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`:

| Code | Missed CT rows |
|---|---:|
| `K-0211` | 143 |
| `K-0133` | 2 |

This review checks whether the misses appear to be caused by leading-zero formatting, alternate code keys, absent Citation Descriptions rows, a CMS source inconsistency, or a validation normalization issue.

## 2. Sources Reviewed

Local ignored CMS source files:

- `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`
- `source_data/cms_survey/NH_FireSafetyCitations_May2026.csv`

Validation script reviewed:

- `scripts/validate_nursing_home_fire_safety_deficiencies.py`

Search terms used against the Citation Descriptions source:

- `K-211`
- `K-0211`
- `K0211`
- `211`
- `K-133`
- `K-0133`
- `K0133`
- `133`

## 3. Citation Descriptions Search Findings

Exact and normalized target matches in `NH_CitationDescriptions_May2026.csv`:

| Search target | Result |
|---|---|
| `K-0211`, `K0211`, `K-211`, `K211` | No exact/normalized row found. |
| `K-0133`, `K0133`, `K-133`, `K133` | No exact/normalized row found. |

Substring matches containing `211` or `133` were present, but they were different K-tags:

| Citation Descriptions code | Finding |
|---|---|
| `K-8133` | Different K-tag; not a match for `K-0133`. |
| `K-8211` | Different K-tag; not a match for `K-0211`. |
| `K-9133` | Different K-tag; not a match for `K-0133`. |
| `K-9211` | Different K-tag; not a match for `K-0211`. |

Interpretation: the lookup misses are not explained by a simple leading-zero or hyphen formatting problem in the Citation Descriptions file.

## 4. Fire Safety Source Findings

The Fire Safety source contains Connecticut rows with exact source prefix/tag values for both missing codes.

| Code | CT rows | Tag version | Source category | Scope/severity distribution |
|---|---:|---|---|---|
| `K-0211` | 143 | `New` | `Egress Deficiencies` | `D`: 105, `E`: 29, `F`: 9 |
| `K-0133` | 2 | `New` | `Construction Deficiencies` | `D`: 1, `E`: 1 |

Observed Fire Safety source descriptions:

| Code | Source description observed in Fire Safety file |
|---|---|
| `K-0211` | Keep aisles, corridors, and exits free of obstruction in case of emergency. |
| `K-0133` | Install a two-hour-resistant firewall separation. |

These descriptions are present in the Fire Safety citation rows themselves. They were not found as standalone lookup rows in the May 2026 Citation Descriptions file.

## 5. Likely Cause

Likely cause: absent Citation Descriptions rows for `K-0211` and `K-0133` in the May 2026 Citation Descriptions source, despite those codes appearing in the May 2026 Fire Safety Deficiencies source.

Rejected causes:

- Leading-zero mismatch: no `K-211`, `K-0211`, `K211`, or `K0211` lookup row was found.
- Hyphen mismatch: normalized lookup search still found no target row.
- Tag version mismatch in CT source: all missed CT rows have `Tag Version = New`.
- Validation script normalization issue: the script normalizes Fire Safety source rows to `K-0211` and `K-0133`, which matches the expected canonical format.

This appears to be a CMS source lookup gap or cross-file consistency gap rather than a local validation bug.

## 6. Validator Decision

No change was made to `scripts/validate_nursing_home_fire_safety_deficiencies.py`.

Reason:

- The validator is correctly reporting official lookup misses.
- Hardcoding descriptions or alternate keys would hide a source-backed gap.
- The future builder should preserve `deficiency_description` from the Fire Safety source and separately flag citation lookup status.

## 7. Future Handling Recommendation

Future fire safety builder behavior should:

- normalize source rows to canonical codes such as `K-0211` and `K-0133`;
- preserve Fire Safety source `Deficiency Description`;
- set `citation_description_lookup_matched` to `false` for `K-0211` and `K-0133` unless CMS publishes official lookup rows;
- leave `citation_description_category` and `citation_description_text` null when no official lookup row exists;
- include lookup gap counts in metadata;
- avoid failing runtime builds solely because of these two documented lookup gaps, if all other validation checks pass;
- continue failing on malformed tags, missing required columns, invalid dates, or unmatched CT CCNs unless explicitly approved.

Do not:

- patch the raw CMS source files;
- create manual citation descriptions;
- copy descriptions from memory;
- map `K-0211` to `K-8211` or `K-9211`;
- map `K-0133` to `K-8133` or `K-9133`;
- treat substring matches as valid lookup matches.

## 8. Proposed Future Builder Note

Future builder:

- `scripts/build_nursing_home_fire_safety_deficiencies_ct.py`

The builder should treat Citation Descriptions lookup as optional enrichment, not as the source of whether a facility received a citation. The Fire Safety source row itself remains the source of the citation record.

Recommended output fields for lookup transparency:

- `citation_description_lookup_matched`
- `citation_description_category`
- `citation_description_text`
- `citation_description_lookup_gap_reason`

Suggested values for `citation_description_lookup_gap_reason`:

- `official_lookup_row_absent`
- `lookup_not_loaded`
- `malformed_code`

For the current May 2026 source, `K-0211` and `K-0133` should use `official_lookup_row_absent` if a future builder writes preview or runtime output.

## 9. Guardrails

- Citation descriptions are lookup/reference text only.
- Citation descriptions do not mean a facility received that citation.
- Fire Safety Deficiencies citation rows are separate from Citation Descriptions lookup rows.
- K-tags and E-tags should remain separate from health F-tags.
- Do not infer harm/immediate jeopardy from fire safety description text.
- Preserve CMS source descriptions, categories, dates, tag versions, and scope/severity codes.
- Do not combine citation-level, survey-level, facility-level, facility-year, or state-level denominators without clear labels.

## 10. Recommendation

Proceed to a future Fire Safety Deficiencies builder dry-run phase with documented lookup gap handling. The current evidence does not justify patching source data or changing the validator. The safest implementation is to preserve source citation descriptions and expose lookup-match metadata when preview or runtime JSON is eventually built.

