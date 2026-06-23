# Fire Safety Deficiencies Builder Dry Run Report

Phase 11D.12 dry-run report for the Connecticut CMS Fire Safety Deficiencies builder. This phase created a builder script and an ignored testing preview only. It did not create runtime JSON, build public UI, modify runtime JS/HTML, change staffing formulas, change generated staffing data, alter current or historical staffing JSON, change Connecticut applicability logic, modify geography JSON, or modify facility status review JSON.

## 1. Script Behavior

Builder script:

- `scripts/build_nursing_home_fire_safety_deficiencies_ct.py`

Default behavior:

- reads the ignored CMS Fire Safety Deficiencies source file;
- reads the ignored CMS Citation Descriptions lookup file when available;
- reads the current/context staffing dataset for CCN join validation;
- filters to Connecticut rows;
- normalizes CCNs while preserving leading zeroes;
- normalizes K-tags and E-tags into stable `deficiency_code` values;
- joins citation descriptions where official lookup rows are available;
- preserves documented lookup misses transparently;
- preserves source survey date, survey type, prefix, tag number, tag version, source description, scope/severity, correction date, standard/complaint indicators, IDR/IIDR indicators, and processing date;
- preserves original `Scope Severity Code`;
- does not apply the health F-tag harm/immediate-jeopardy grouping to fire safety rows;
- prints a validation summary;
- writes no output.

Optional testing behavior:

- `python scripts/build_nursing_home_fire_safety_deficiencies_ct.py --write-testing-preview`

The optional flag writes only:

- `data/testing/nursing_home_fire_safety_deficiencies_ct_preview.json`

The script never writes:

- `data/nursing_home_fire_safety_deficiencies_ct.json`

## 2. Source Files Used

| Source | Path |
|---|---|
| CMS Fire Safety Deficiencies source | `source_data/cms_survey/NH_FireSafetyCitations_May2026.csv` |
| CMS Citation Descriptions source | `source_data/cms_survey/NH_CitationDescriptions_May2026.csv` |
| Current/context staffing data | `data/nursing_home_staffing_ct.json` |

CMS source metadata:

- source name: CMS Provider Data Catalog Fire Safety Deficiencies
- source file: `NH_FireSafetyCitations_May2026.csv`
- CMS dataset ID: `ifjz-ge4w`
- source URL: <https://data.cms.gov/provider-data/sites/default/files/resources/a212e8d9a0e8d36ebee28b8334485334_1778861750/NH_FireSafetyCitations_May2026.csv>
- acquired date used in metadata: 2026-06-22

## 3. Dry-Run Validation Summary

| Measure | Result |
|---|---:|
| Source file size | 69,121,738 bytes |
| Total source rows | 199,760 |
| Connecticut rows | 2,135 |
| Unique CT CCNs | 178 |
| Current staffing CCNs | 196 |
| Joined CT fire safety deficiency CCNs to current staffing | 178 |
| Unmatched CT fire safety deficiency CCNs | 0 |
| Distinct citation codes | 84 |

Join result:

- All 178 unique CT Fire Safety Deficiency CCNs joined to `data/nursing_home_staffing_ct.json`.
- No unmatched CT CCNs were found.

## 4. Survey Date Range

| Date field | Minimum | Maximum |
|---|---|---|
| `Survey Date` | 2018-11-08 | 2026-02-27 |

Date guardrail:

- `Survey Date`, `Correction Date`, and `Processing Date` are preserved separately and should not be treated as interchangeable.

## 5. K/E Tag Counts

Prefix counts:

| Prefix | Rows |
|---|---:|
| `E` | 128 |
| `K` | 2,007 |

Tag version counts:

| Tag version | Rows |
|---|---:|
| `New` | 2,135 |

Interpretation:

- `K` rows are fire safety / life safety code tags.
- `E` rows are emergency preparedness tags.
- K-tags and E-tags should remain separate from health F-tags in future UI, exports, and denominator planning.

## 6. Citation Description Join Results

Citation Descriptions source:

- `source_data/cms_survey/NH_CitationDescriptions_May2026.csv`

Join behavior:

- canonical join key is normalized prefix plus zero-padded tag number, such as `K-0211`;
- source `Deficiency Description` is always preserved;
- Citation Descriptions category/text are included only when an official lookup row exists;
- unmatched lookup rows are preserved with null lookup text/category and a gap reason.

Lookup result:

| Measure | Result |
|---|---:|
| Citation description lookup misses | 145 |

Missed codes:

| Code | Missed rows | Handling |
|---|---:|---|
| `K-0211` | 143 | Preserved as `official_lookup_row_absent`. |
| `K-0133` | 2 | Preserved as `official_lookup_row_absent`. |

These misses match the Phase 11D.8 lookup gap review. They appear to be CMS lookup-source gaps or cross-file consistency gaps, not a local normalization bug.

## 7. Scope / Severity Counts

| Scope/severity code | Rows |
|---|---:|
| `D` | 1,556 |
| `E` | 338 |
| `F` | 238 |
| `J` | 2 |
| `K` | 1 |

Guardrail:

- The builder preserves original `Scope Severity Code`.
- The builder does not apply health-deficiency harm/immediate-jeopardy grouping to fire safety rows.
- Do not infer harm/IJ from fire safety description text.

## 8. Testing Preview Output

Testing preview created:

- `data/testing/nursing_home_fire_safety_deficiencies_ct_preview.json`

Preview details:

| Measure | Result |
|---|---:|
| Preview file size | 2,657,543 bytes |
| Fire safety deficiency records | 2,135 |

This file is non-runtime, ignored by Git, and should not be committed. It exists only to verify the future JSON shape and builder behavior.

Runtime output status:

- `data/nursing_home_fire_safety_deficiencies_ct.json` was not created.

## 9. Metadata Added In Preview

The preview metadata includes:

- source identity and acquisition fields;
- CT row and CCN join counts;
- survey date range;
- K/E tag counts;
- citation description lookup miss count;
- missed citation code counts;
- note that `K-0211` and `K-0133` appear to be CMS lookup-source gaps;
- limitations explaining citation-level rows, source-date distinctions, K/E/F separation, and non-runtime preview status.

## 10. Verification Commands

Commands run:

```powershell
python -m py_compile scripts/build_nursing_home_fire_safety_deficiencies_ct.py
python scripts/build_nursing_home_fire_safety_deficiencies_ct.py
python scripts/build_nursing_home_fire_safety_deficiencies_ct.py --write-testing-preview
```

Results:

- Python compile check passed.
- Dry run passed and wrote no output.
- Testing preview run passed and wrote only `data/testing/nursing_home_fire_safety_deficiencies_ct_preview.json`.
- Runtime output `data/nursing_home_fire_safety_deficiencies_ct.json` does not exist.

## 11. Runtime Readiness Recommendation

The builder is ready for a future runtime JSON build phase after these decisions are approved:

1. Whether public UI should display K-tags and E-tags in the same section or separate subsections.
2. How to label lookup gaps for `K-0211` and `K-0133` without implying missing source citations.
3. Whether fire safety scope/severity should remain source-only or receive a separate, officially validated grouping.
4. What denominator labels should be used for facility-level, facility-year, and state-level fire safety summaries.
5. Whether the future advanced facility dossier should show health, fire safety, penalties, and citation descriptions as separate source modules before any combined inspection/enforcement summary is attempted.

Recommended next phase: **Phase 11D.13: Survey / Enforcement Runtime Architecture Decision**, or a narrower fire safety runtime build phase if lookup-gap and denominator rules are accepted.

