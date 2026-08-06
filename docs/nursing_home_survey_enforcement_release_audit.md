# Nursing Home Survey and Enforcement Release Audit

## Purpose

Phase 11D.21 adds an automated, read-only release consistency audit for the Connecticut nursing home survey and enforcement feature. The audit checks the statewide runtime datasets, compact facility summary, per-facility detail layer, metadata disclosures, public methodology, and Facility Explorer loading architecture as one release.

The audit does not rebuild, normalize, repair, or write any audited file. A genuine mismatch is reported with expected and actual values and causes a nonzero exit status.

## Commands

Run the concise release gate with:

```text
python scripts/audit_nursing_home_survey_enforcement_release.py
```

Run the expanded diagnostic form with:

```text
python scripts/audit_nursing_home_survey_enforcement_release.py --verbose
```

The completed Phase 11D.21 verification also used:

```text
python -m py_compile scripts/audit_nursing_home_survey_enforcement_release.py
node --check Assets/nursing-home-staffing.js
python scripts/test_build_nursing_home_staffing_ct.py
python -m json.tool data/nursing_home_source_manifest.json
python -m json.tool data/current_tool_context_registry.json
git diff --check
git status --short --branch
```

## Files Checked

The audit parses or reads:

- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_penalties_ct.json`
- `data/nursing_home_survey_enforcement_summary_ct.json`
- `data/nursing_home_survey_enforcement_details_ct/index.json`
- all 196 six-digit CCN files in `data/nursing_home_survey_enforcement_details_ct/`
- `data/nursing_home_source_manifest.json`
- `data/current_tool_context_registry.json`
- `tools/nursing-home-staffing-explorer.html`
- `Assets/nursing-home-staffing.js`
- `tools/nursing-home-staffing-methodology.html`

## Audit Sections

The script reports an individual PASS or FAIL for each of these sections:

1. JSON parsing and required structure
2. Current facility coverage
3. Health runtime
4. Fire Safety / Emergency Preparedness runtime
5. Penalties runtime
6. Compact summary consistency
7. Per-facility detail reconciliation
8. Cross-layer per-facility reconciliation
9. Manifest and registry consistency
10. Public methodology consistency
11. Facility Explorer loading architecture
12. Performance information

The release run passed all 12 sections with zero failures.

## JSON Structure and CCN Integrity

All required JSON files parsed successfully. Required top-level arrays, metadata objects, index fields, and per-facility detail arrays were present. All CCNs checked across staffing, detailed runtime rows, compact summary rows, index entries, and detail metadata remained six-character strings. Leading zeros were preserved.

The detail directory contained exactly 196 six-digit CCN JSON files plus `index.json`; no unexpected JSON filenames were present.

## Current Facility Coverage

| Check | Expected | Actual | Result |
| --- | ---: | ---: | --- |
| Current staffing facility rows | 196 | 196 | Exact |
| Unique current CCNs | 196 | 196 | Exact |
| Compact summary rows | 196 | 196 | Exact |
| Per-facility detail files | 196 | 196 | Exact |
| Missing or unexpected summary CCNs | 0 | 0 | Exact |
| Missing or unexpected detail CCNs | 0 | 0 | Exact |

Every current CCN appears exactly once in the compact summary and has exactly one CCN-named detail file.

## Detailed Runtime Reconciliation

### Health Deficiencies

| Measure | Expected | Actual | Result |
| --- | ---: | ---: | --- |
| Citation rows | 6,761 | 6,761 | Exact |
| Unique CCNs | 191 | 191 | Exact |
| Survey date minimum | 2018-11-08 | 2018-11-08 | Exact |
| Survey date maximum | 2026-03-31 | 2026-03-31 | Exact |
| Distinct F-tags | 164 | 164 | Exact |
| Citation-description lookup misses | 0 | 0 | Exact |
| Actual harm, not immediate jeopardy | 172 | 172 | Exact |
| Immediate jeopardy | 73 | 73 | Exact |
| No actual harm, potential minimal harm | 463 | 463 | Exact |
| No actual harm, potential more than minimal harm | 6,053 | 6,053 | Exact |

Every Health record's derived grouping reconciled to its Scope Severity Code: J/K/L to immediate jeopardy, G/H/I to actual harm without immediate jeopardy, D/E/F to potential more-than-minimal harm, A/B/C to potential minimal harm, and blank or unexpected values to unknown/unmapped.

### Fire Safety and Emergency Preparedness

| Measure | Expected | Actual | Result |
| --- | ---: | ---: | --- |
| Total citation rows | 2,135 | 2,135 | Exact |
| Unique CCNs | 178 | 178 | Exact |
| Fire Safety K-tag rows | 2,007 | 2,007 | Exact |
| Emergency Preparedness E-tag rows | 128 | 128 | Exact |
| Distinct citation codes | 84 | 84 | Exact |
| Survey date minimum | 2018-11-08 | 2018-11-08 | Exact |
| Survey date maximum | 2026-02-27 | 2026-02-27 | Exact |
| Citation-description lookup misses | 145 | 145 | Exact |
| K-0211 lookup misses | 143 | 143 | Exact |
| K-0133 lookup misses | 2 | 2 | Exact |

Scope/severity counts reconciled exactly: D 1,556; E 338; F 238; J 2; and K 1. K-tags and E-tags remained distinguishable. Health harm/IJ fields were absent, source descriptions remained present for K-0211 and K-0133, and every lookup gap remained flagged with an explanation.

### Penalties and Enforcement

| Measure | Expected | Actual | Result |
| --- | ---: | ---: | --- |
| Enforcement rows | 179 | 179 | Exact |
| Unique CCNs | 102 | 102 | Exact |
| Fine rows | 167 | 167 | Exact |
| Payment Denial rows | 12 | 12 | Exact |
| Fine total | $3,925,517.00 | $3,925,517.00 | Exact |
| Payment-denial days | 368 | 368 | Exact |
| Duplicated full-row signatures | 3 | 3 | Exact |
| Flagged duplicate rows | 3 | 3 | Exact |
| Penalty date range | 2023-05-17 to 2026-03-17 | 2023-05-17 to 2026-03-17 | Exact |
| Processing date range | 2026-05-01 to 2026-05-01 | 2026-05-01 to 2026-05-01 | Exact |
| Payment-denial start-date range | 2024-01-17 to 2024-12-03 | 2024-01-17 to 2024-12-03 | Exact |

Fine and Payment Denial remained distinct source and normalized types. Fine amounts appeared only on Fine rows; denial start dates and denial lengths appeared only on Payment Denial rows. Penalty Date, Payment Denial Start Date, and Processing Date remained separate populated fields. Duplicate source rows remained preserved and flagged.

Runtime metadata counts, CCN coverage, source filenames, date ranges, lookup gaps, penalty types, duplicate counts, fine totals, and denial-day totals were recomputed from the records and matched the stored metadata.

## Compact Summary Reconciliation

The compact summary contains 196 facility rows. Its recent window remains 2023-03-31 through 2026-03-31, inclusive.

Coverage reconciled to 191 facilities with Health records, 178 with Fire Safety or Emergency Preparedness records, 102 with penalty records, and 5 with no records in the included source windows.

### All-Time Available-Source Totals

| Measure | Expected | Actual |
| --- | ---: | ---: |
| Health citations | 6,761 | 6,761 |
| Actual harm | 172 | 172 |
| Immediate jeopardy | 73 | 73 |
| Fire Safety citations | 2,007 | 2,007 |
| Emergency Preparedness citations | 128 | 128 |
| Enforcement events | 179 | 179 |
| Fines | 167 | 167 |
| Fine total | $3,925,517.00 | $3,925,517.00 |
| Payment denials | 12 | 12 |
| Payment-denial days | 368 | 368 |

### Recent-Window Totals

| Measure | Expected | Actual |
| --- | ---: | ---: |
| Health citations | 4,717 | 4,717 |
| Actual harm | 141 | 141 |
| Immediate jeopardy | 66 | 66 |
| Fire Safety citations | 1,151 | 1,151 |
| Emergency Preparedness citations | 57 | 57 |
| Enforcement events | 179 | 179 |
| Fines | 167 | 167 |
| Fine total | $3,925,517.00 | $3,925,517.00 |
| Payment denials | 12 | 12 |
| Payment-denial days | 368 | 368 |

All five zero-record facilities remained present with zero numeric values, null latest dates, and limited-source caution markers. The summary does not treat absence from the available files as proof that a facility never had deficiencies or enforcement actions.

## Per-Facility and Cross-Layer Reconciliation

The audit aggregated the four detail arrays across all 196 files and obtained exactly 6,761 Health deficiencies, 2,007 Fire Safety K-tags, 128 Emergency Preparedness E-tags, and 179 penalties.

For each category, the complete multiset of `source_row_hash` values matched the applicable statewide runtime dataset. The same hash comparison also passed separately for every CCN, preventing records from being silently lost, duplicated, or assigned to a different facility while statewide totals remain unchanged.

Each file's actual array lengths matched its metadata and index entry. Each index byte size matched the physical facility file. Detail metadata CCNs and provider names matched current staffing records. K-0211 and K-0133 gaps, three duplicate-penalty flags, and Health-only harm groupings remained intact. All arrays followed the documented newest-first order with their stable citation or event tie-breakers.

For every CCN, the audit independently recalculated and matched:

- all-time counts by record type;
- Health actual-harm and immediate-jeopardy counts;
- fine counts and totals;
- payment-denial counts and days;
- latest Health, Fire Safety/Emergency Preparedness, and penalty dates; and
- every recent-window count and amount after applying the inclusive window to detail records.

All 196 facilities reconciled without a per-facility mismatch.

## Manifest and Registry Consistency

The source manifest accurately identifies the four May 2026 CMS source files, all three statewide runtime filenames, compact-summary filename, CCN detail path pattern, runtime-derived date ranges, recent window, K-0211/K-0133 gaps, integrated Facility Explorer status, and separation from staffing analysis.

The tool-context registry identifies the compact default load, selected-facility opt-in detail request, runtime and detail paths supported by its schema, May 2026 source context, recent window, lookup gaps, public integration status, and separation from staffing classifications and composite quality scoring.

The audit derives source filenames and date markers from current runtime metadata before comparing the manifest and registry, rather than trusting disclosure text alone.

## Public Methodology Consistency

Stable semantic checks found all required source filenames, source date ranges, recent-window dates and inclusive description, four Health scope/severity mappings, K-0211/K-0133 disclosure, three duplicated full-row signatures, distinct enforcement date fields, facility coverage figures, and zero-record caveat.

The methodology continues to state that survey and enforcement findings do not change staffing classification, records are not a standalone quality score, facilities should not be ranked solely by citation counts or fine amounts, and absence from the included files is not proof that no finding ever existed.

The audit uses normalized semantic markers and HTML date attributes. It does not depend on exact paragraph wording.

## Facility Explorer Loading Architecture

Static implementation checks confirmed that the Facility Explorer:

- loads the compact summary by default;
- constructs a six-digit CCN path under `data/nursing_home_survey_enforcement_details_ct/`;
- contains no reference to or fetch of the three statewide detailed runtime JSON files;
- calls the facility detail loader only from the explicit detail-action handler;
- retains the **View detailed findings** action;
- uses an in-session `Map` cache;
- uses request-token checks to prevent stale responses from replacing the selected facility;
- retains loading, empty, error, retry, and collapsed states; and
- escapes source descriptions and lookup-gap text before inserting rendered markup.

## Performance Statistics

All sizes were calculated directly from the current files. Facility statistics exclude `index.json`; the directory total includes it.

| Payload | Bytes |
| --- | ---: |
| Health statewide runtime | 8,920,771 |
| Fire Safety / Emergency Preparedness statewide runtime | 2,657,540 |
| Penalties statewide runtime | 159,521 |
| Three statewide detailed runtime files combined | 11,737,832 |
| Compact summary | 322,951 |
| Per-facility index | 81,237 |
| 196 facility files combined | 10,063,431 |
| Complete per-facility directory | 10,144,668 |
| Minimum facility file | 991 |
| Median facility file | 50,545.5 |
| Average facility file | 51,344.04 |
| Maximum facility file | 138,900 |

The median selected-facility file is 0.431% of the three statewide detailed runtime files, an estimated 99.569% transfer reduction.

### Largest Facilities by Detail Record Count

| CCN | Facility | Records | Bytes |
| --- | --- | ---: | ---: |
| 075228 | ARDEN CARE CENTER | 127 | 136,960 |
| 075113 | GREENTREE MANOR NURSING AND REHABILITATION CENTER | 126 | 138,900 |
| 075358 | BICKFORD HEALTH CARE CENTER | 109 | 119,561 |
| 075397 | NEW HAVEN CENTER FOR NURSING & REHABILITATION LLC | 108 | 117,601 |
| 075060 | CIVITA CARE CENTER AT SALMON BROOK | 106 | 115,101 |
| 075158 | NEW LONDON SUB-ACUTE AND NURSING | 104 | 109,279 |
| 075182 | GRANDVIEW REHABILITATION AND HEALTHCARE CENTER | 99 | 104,572 |
| 075348 | ADVANCED CENTER FOR NURSING & REHABILITATION | 95 | 103,122 |
| 075017 | MONTOWESE CENTER FOR HEALTH & REHABILITATION | 87 | 95,433 |
| 075403 | APPLE REHAB WEST HAVEN | 86 | 95,757 |

## Known Limitations

- The methodology and loading-architecture checks are static semantic checks. They verify required markers and control-flow structure but do not replace browser interaction, accessibility review, or network-panel inspection.
- The audit verifies the current expected release totals. A future CMS refresh is expected to fail until the release expectations and public disclosures are intentionally reviewed and updated.
- Source-row hashes prove exact record preservation across the current runtime and detail layers; they do not independently validate the upstream CMS CSV contents.
- Available CMS rolling files are not complete lifetime histories, and passing the audit does not convert citation counts or enforcement amounts into facility quality scores.

## Release-Readiness Conclusion

The Phase 11D.21 audit passed all 12 sections. Runtime records, compact summary values, per-facility details, stored metadata, public disclosures, and lazy-loading architecture are internally consistent for the current May 2026 CMS release. No discrepancy requiring a data, builder, methodology, or UI change was identified.

## Recommendation for the Next Phase

Use `python scripts/audit_nursing_home_survey_enforcement_release.py` as a mandatory gate after each future survey/enforcement refresh and before publication. In a separately scoped phase, add the command to continuous integration so pull requests fail when runtime, summary, detail, metadata, methodology, or loading-contract changes drift apart.
