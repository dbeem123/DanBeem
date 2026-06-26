# Nursing Home Survey / Enforcement Runtime Integration Roadmap

Phase 11D.13 documentation-only roadmap. This document describes how validated survey, citation, fire safety, emergency preparedness, and enforcement data should move from dry-run builders into app-ready runtime data and, later, into the Facility Explorer / Advanced Facility Dossier.

This phase does not build public UI, modify runtime JS/HTML, create runtime JSON, modify current staffing JSON, modify historical PBJ JSON, modify geography JSON, modify facility status review JSON, change formulas, change CT applicability logic, or commit raw CMS source files.

## 1. Purpose

The Phase 11D source lanes are now validated enough to plan runtime architecture, but not yet ready for public display. The next work should avoid rushing detailed CMS citation/event rows into the first page load. The safer path is to finalize production builders and audits first, then publish compact facility-level summaries for default dossier display, with detailed rows added later through clearly labeled, optional views.

## 2. Current Validated Source Lanes

| Lane | Source type | Current readiness | Future runtime role |
|---|---|---|---|
| Health F-tags | CMS Health Deficiencies | Source validation, data contract, builder dry run, and ignored preview complete. | Detailed health citation/event file plus facility-level summary. |
| Fire Safety K-tags | CMS Fire Safety Deficiencies | Source validation, data contract, lookup gap review, builder dry run, and ignored preview complete. | Detailed fire safety citation/event file plus facility-level summary. |
| Emergency Preparedness E-tags | CMS Fire Safety Deficiencies | Validated in same Fire Safety lane; E-tags are present and should remain labeled separately. | Detailed emergency preparedness rows in fire safety file, summarized separately. |
| Penalties / Enforcement | CMS Penalties | Source validation, data contract, builder dry run, and ignored preview complete. | Detailed enforcement event file plus facility-level summary. |

Readiness summary:

- The builders reproduce the validation counts.
- All CT source CCNs in the three lanes join to the current/context staffing dataset.
- No public runtime JSON exists yet.
- Testing previews exist only under ignored `data/testing/`.
- Raw CMS source files remain under ignored `source_data/`.

## 3. Current Builder Readiness

| Builder | Source file used | CT rows | Unique CT CCNs | Join result | Testing preview | Runtime JSON exists? | Known caveats |
|---|---|---:|---:|---|---|---|---|
| `scripts/build_nursing_home_health_deficiencies_ct.py` | `source_data/cms_survey/NH_HealthCitations_May2026.csv` | 6,761 | 191 | 191 joined; 0 unmatched | `data/testing/nursing_home_health_deficiencies_ct_preview.json` | No | Detailed preview is about 8.9 MB. Health harm/IJ grouping is derived from structured scope/severity and needs public wording review before display. |
| `scripts/build_nursing_home_fire_safety_deficiencies_ct.py` | `source_data/cms_survey/NH_FireSafetyCitations_May2026.csv` | 2,135 | 178 | 178 joined; 0 unmatched | `data/testing/nursing_home_fire_safety_deficiencies_ct_preview.json` | No | Detailed preview is about 2.66 MB. Citation Descriptions lookup misses exist for `K-0211` and `K-0133`; these should remain transparent. Do not apply health harm/IJ grouping to fire safety rows. |
| `scripts/build_nursing_home_penalties_ct.py` | `source_data/cms_enforcement/NH_Penalties_May2026.csv` | 179 | 102 | 102 joined; 0 unmatched | `data/testing/nursing_home_penalties_ct_preview.json` | No | Detailed preview is about 160 KB. Three duplicate CT full-row signatures are flagged and preserved; runtime totals need an approved duplicate handling rule. |

## 4. Public Runtime Data Strategy

Three possible runtime strategies were considered:

| Strategy | Advantages | Risks |
|---|---|---|
| One large detailed runtime JSON per dataset | Simple builder-to-runtime path; preserves full auditability. | Health detail file is about 8.9 MB and Fire Safety detail file is about 2.66 MB. Loading all detail rows on the first Facility Explorer view would hurt static-site performance. |
| One compact facility-level summary JSON only | Fast default page load; easier first public UI. | Users cannot inspect underlying citation/event rows without a later detail layer. |
| Hybrid approach | Fast default summary, with detailed files available for export or on-demand inspection later. | Requires careful file contracts and lazy-loading behavior. |

Recommended strategy: **hybrid**.

The app should not load every detailed health/fire citation row on the default Facility Explorer screen. Instead:

1. Keep detailed runtime files as audited source-backed data products.
2. Create a compact facility-level summary runtime file for default Facility Explorer / Advanced Facility Dossier display.
3. Add optional detail views later, ideally lazy-loaded only when a user opens a survey/enforcement section for a selected facility.
4. Preserve source dates, processing dates, lookup gaps, and limitations in both detailed and summary metadata.

## 5. Staged Runtime Approach

### Stage A: Audited Runtime Detail Files

Create production runtime JSON outputs only after final audit:

- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_penalties_ct.json`

These should be detailed citation/event files. They should not be wired into public UI until file size, lazy-loading, methodology wording, and denominator labels are approved.

### Stage B: Compact Facility-Level Summary

Create a compact summary file for default app display:

- `data/nursing_home_survey_enforcement_summary_ct.json`

This should be keyed by CCN or contain one row per current facility, with compact counts and latest-date fields. It should be the first file wired into Facility Explorer because it can provide a cautious snapshot without forcing large detail downloads.

### Stage C: Optional Detail Views

After summary display is reviewed, add optional detail views:

- expandable recent health citations;
- expandable fire safety / emergency preparedness citations;
- enforcement event timeline;
- export controls for selected facility detail.

Detail views should remain clearly labeled as source context, not a scoring engine.

### Stage D: Lazy-Loaded Facility Dossier Details

If detailed files are too large for comfortable static-site loading, split detail data by lane or use lazy-loading:

- load summary on page load;
- load health details only when the selected facility's Health Deficiencies section is opened;
- load fire safety details only when the selected facility's Fire Safety section is opened;
- load penalties details only when the selected facility's Enforcement section is opened.

If needed later, consider per-facility or sharded detail files. Do not introduce that complexity until file size and browser performance testing justify it.

## 6. Recommended Future Runtime Files

| Future file | Role | Detail or summary | First public use |
|---|---|---|---|
| `data/nursing_home_health_deficiencies_ct.json` | CT health F-tag citation rows. | Detailed citation/event file. | Lazy-loaded detail view or export, not default first screen. |
| `data/nursing_home_fire_safety_deficiencies_ct.json` | CT fire safety K-tag and emergency preparedness E-tag citation rows. | Detailed citation/event file. | Lazy-loaded detail view or export, not default first screen. |
| `data/nursing_home_penalties_ct.json` | CT CMS fine and payment-denial rows. | Detailed enforcement event file. | Lazy-loaded detail view or export, not default first screen. |
| `data/nursing_home_survey_enforcement_summary_ct.json` | Facility-level summary derived from audited detailed files. | Compact facility-level summary file. | Default Survey & Enforcement Snapshot card in Facility Explorer. |

The summary file should reference source metadata from the detailed files, including source month/year, processing dates, row counts, lookup gaps, and limitations.

## 7. Facility-Level Summary Design

Recommended summary grain:

- one record per current facility CCN in `data/nursing_home_staffing_ct.json`;
- explicit nulls or zeros for facilities with no rows in a given source lane;
- metadata describing source windows and denominator rules.

Recommended fields by CCN:

| Field | Definition |
|---|---|
| `ccn` | Current facility CCN. |
| `provider_name` | Current/context provider name for display. |
| `health_deficiency_count_all_source_rows` | Health F-tag citation row count across all validated source rows. |
| `health_deficiency_count_last_3_years` | Health F-tag citation row count in the approved last-three-years window. |
| `actual_harm_count_last_3_years` | Count using structured health scope/severity grouping, if approved for public display. |
| `immediate_jeopardy_count_last_3_years` | Count using structured health scope/severity grouping, if approved for public display. |
| `fire_safety_citation_count_last_3_years` | K-tag citation row count in the approved time window. |
| `emergency_preparedness_citation_count_last_3_years` | E-tag citation row count in the approved time window. |
| `enforcement_event_count_last_3_years` | CMS Penalties rows in the approved time window. |
| `fine_count_last_3_years` | Fine rows in the approved time window. |
| `fine_total_last_3_years` | Sum of parsed fine amounts under the approved duplicate handling rule. |
| `payment_denial_count_last_3_years` | Payment denial rows in the approved time window. |
| `latest_health_survey_date` | Latest health deficiency survey date in source rows, if present. |
| `latest_fire_safety_survey_date` | Latest fire safety / emergency preparedness survey date in source rows, if present. |
| `latest_penalty_date` | Latest CMS penalty date in source rows, if present. |
| `latest_processing_date` | Latest processing/source date across included source lanes. |
| `has_fire_safety_lookup_gap` | Whether the facility has K-tag rows affected by documented lookup gaps. |
| `has_duplicate_penalty_source_rows` | Whether the facility has duplicate penalty full-row signatures under the approved rule. |
| `caution_flags` | Array of plain-language caution flags for display/methodology links. |

Recommended time windows:

- `all_source_rows`: preserve full validated source-window counts for audit and exports.
- `last_3_years`: best default public summary window because CMS Penalties describes a last-three-years scope, but the exact cutoff must be defined by date rules.
- `latest_survey_cycle`: useful later where feasible, but do not infer a survey cycle without an explicit source field or audited rule.

Every public count should display or link to the time window and denominator definition.

## 8. Facility Dossier UI Staging

Recommended first UI step:

- Add a cautious **Survey & Enforcement Snapshot** card to the Facility Explorer / Advanced Facility Dossier after compact summary data exists and public wording is approved.

Initial card content should be restrained:

- latest available health survey citation context;
- recent F-tag count with harm/IJ counts only if wording is approved;
- recent fire safety K-tag count;
- recent emergency preparedness E-tag count;
- recent enforcement event count;
- recent fine count and total, with time window;
- payment denial count;
- source date range and methodology link.

UI guardrails:

- Use plain-language labels.
- Keep staffing metrics separate from survey/enforcement findings.
- Avoid ranking facilities by fine amounts alone.
- Avoid implying that a citation count or fine total is a complete quality score.
- Show source context and date ranges.
- Label health F-tags, fire safety K-tags, emergency preparedness E-tags, and penalties separately.
- Explain that citation/enforcement data is one context source, not a complete or definitive quality assessment.

Detail sections can follow later:

- Health Deficiencies detail table.
- Fire Safety / Emergency Preparedness detail table.
- Enforcement timeline.
- Exportable survey/enforcement summary.

## 9. Audit Requirements Before Runtime Output

Before creating production runtime JSON, require:

1. Builder compile checks for all production builders.
2. Builder dry-run checks for all production builders.
3. Preview row counts match validation docs.
4. Source-to-preview audit script or audit report for each lane.
5. Metadata counts match source and preview counts.
6. No unmatched current CCNs unless documented and approved.
7. Citation Descriptions lookup misses documented and reflected in metadata.
8. Duplicate penalty source rows documented and reflected in metadata.
9. JSON file sizes reviewed against static-site performance expectations.
10. Public wording reviewed for methodology, denominator labels, and caveats.
11. Confirmation that current/context staffing data, historical PBJ data, geography data, facility status review data, and CT applicability logic are unchanged.

Suggested audit checks:

- source row count vs output row count;
- CT row count by source lane;
- unique CT CCN count;
- join count and unmatched list;
- date min/max;
- tag/prefix counts;
- harm/IJ group counts for health only, if used;
- lookup miss codes and counts for fire safety;
- penalty type counts;
- fine total and payment denial length total;
- duplicate penalty signature count;
- runtime JSON schema validation.

## 10. Recommended Next Phases

Recommended sequence:

1. **Phase 11D.14: Health / Fire / Penalties Runtime Build Audit Plan**
   Define exact audit scripts, schema checks, duplicate rules, time-window rules, and public wording review requirements before any runtime JSON is created.

2. **Phase 11D.15: Create Production Runtime Detail JSON Outputs, No UI Wiring**
   Create `data/nursing_home_health_deficiencies_ct.json`, `data/nursing_home_fire_safety_deficiencies_ct.json`, and `data/nursing_home_penalties_ct.json` only after audit criteria are approved. Do not wire UI yet.

3. **Phase 11D.16: Create Compact Facility-Level Survey / Enforcement Summary JSON**
   Build `data/nursing_home_survey_enforcement_summary_ct.json` from audited detailed files. Validate one row per current facility CCN and clearly labeled time windows.

4. **Phase 11D.17: Facility Explorer Survey & Enforcement Snapshot Prototype**
   Wire only the compact summary into the Facility Explorer dossier. Keep detail files lazy or unwired until performance and wording pass review.

5. **Phase 11D.18: Methodology, Source Currency, And Public Wording Update**
   Add methodology language explaining source windows, denominators, lookup gaps, duplicate handling, and why these metrics are context rather than a quality score.

This sequence intentionally puts audit and summary architecture before UI, because the detailed Health and Fire Safety files are large enough that default eager loading would be unwise.

## 11. Risks And Caveats

- Citation rows are historical/current-source context, not simple current performance scores.
- Source date windows differ by dataset.
- Health deficiency rows, fire safety rows, emergency preparedness rows, and penalty rows have different meanings.
- Penalties are not quality scores.
- Fine totals need time-window context and duplicate-row handling.
- Payment-denial rows should not be converted into fine amounts.
- Fire safety lookup gaps for `K-0211` and `K-0133` must remain transparent.
- Public UI must avoid implying survey/enforcement data is exhaustive or definitive.
- Static-site file size and browser performance must be tested before detailed rows are loaded in public pages.
- Statewide percentages require explicit denominators.
- Facility-level counts require explicit time windows.
- Survey/enforcement data should not alter staffing formulas, current/context staffing data, historical PBJ data, CT applicability logic, geography data, or facility status review data.

## 12. Recommendation

Proceed with a runtime build audit plan before creating production runtime JSON. The validated builders are useful, but the first public integration should be a compact facility-level summary with careful labels, not eager loading of every detailed citation and enforcement row.

