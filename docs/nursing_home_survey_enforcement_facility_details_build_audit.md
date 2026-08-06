# Nursing Home Survey and Enforcement Facility Details Build Audit

## Scope

Phase 11D.19A created a static per-facility survey and enforcement detail layer for all current Connecticut nursing homes. This phase created and audited data files only. No Facility Explorer or other public UI wiring was added.

## Inputs

The builder reads only repository runtime JSON:

- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_penalties_ct.json`
- `data/nursing_home_survey_enforcement_summary_ct.json` for reconciliation cross-checking only

No raw CMS source files are read by this builder.

## Build Commands

```text
python -m py_compile scripts/build_nursing_home_survey_enforcement_facility_details_ct.py
python scripts/build_nursing_home_survey_enforcement_facility_details_ct.py
python scripts/build_nursing_home_survey_enforcement_facility_details_ct.py --write-runtime
python scripts/build_nursing_home_survey_enforcement_facility_details_ct.py
git diff --check
git status --short --branch
```

The default command performs validation and reports planned output without writing. Production output requires `--write-runtime`.

## Outputs

- Directory: `data/nursing_home_survey_enforcement_details_ct/`
- Manifest: `data/nursing_home_survey_enforcement_details_ct/index.json`
- Facility detail files: 196 six-digit CCN filenames
- Total JSON files including the manifest: 197

Every current staffing CCN has exactly one facility file, including facilities with no records. No unexpected CCNs appear. Facility records are sorted newest date first, followed by stable citation/event identifiers.

The runtime write replaces expected generated files atomically. Stale cleanup is limited to six-digit `######.json` files inside the designated output directory; unrelated files are not removed. The initial production build removed zero stale files.

## Manifest Summary

- Build date: 2026-08-04
- Facility file count: 196
- Expected current facility count: 196
- Health records: 6,761
- Fire safety K-tag records: 2,007
- Emergency preparedness E-tag records: 128
- Penalty/enforcement records: 179
- Facilities with no detail records: 5
- Health source CCNs: 191
- Combined fire safety/emergency preparedness source CCNs: 178
- Penalty source CCNs: 102

Each manifest facility entry contains CCN, provider name, repository-relative detail path, category counts, total detail record count, and exact file size.

## Record Reconciliation

| Detail category | Per-facility total | Detailed runtime total | Result |
| --- | ---: | ---: | --- |
| Health deficiencies | 6,761 | 6,761 | Exact |
| Fire safety K-tags | 2,007 | 2,007 | Exact |
| Emergency preparedness E-tags | 128 | 128 | Exact |
| Penalty/enforcement events | 179 | 179 | Exact |

The builder also reconciles every facility's four category counts against the compact summary JSON. Independent validation confirmed:

- health F-tag harm/immediate-jeopardy grouping is present only on health records;
- no fire safety or emergency preparedness record contains `harm_ij_group`;
- K-0211 retains 143 citation-description lookup misses;
- K-0133 retains 2 citation-description lookup misses; and
- all 3 duplicate penalty source rows remain preserved and flagged.

## File Size and Performance Audit

Facility-file statistics exclude `index.json`; directory totals include it.

| Measure | Size |
| --- | ---: |
| Facility files combined | 10,063,431 bytes |
| Manifest | 81,237 bytes |
| Total generated directory | 10,144,668 bytes |
| Smallest facility file | 991 bytes |
| Largest facility file | 138,900 bytes |
| Median facility file | 50,545.5 bytes |
| Average facility file | 51,344.04 bytes |
| Three statewide detailed runtime files | 11,737,832 bytes |

The smallest file is `075001.json` at 991 bytes. The largest file is `075113.json` at 138,900 bytes.

For a future selected-facility request, the median file is 0.431% of the three statewide detail files, a 99.569% transfer reduction. The average file is 0.437% of the statewide payload, and even the largest facility file is only 1.183%, a 98.817% reduction. The complete generated directory is 13.573% smaller than the three input detail files because facility records retain display-relevant fields instead of repeating statewide/facility metadata on every citation row.

## Largest Facilities by Detail Record Count

| CCN | Facility | Detail records | File size |
| --- | --- | ---: | ---: |
| 075228 | ARDEN CARE CENTER | 127 | 136,960 bytes |
| 075113 | GREENTREE MANOR NURSING AND REHABILITATION CENTER | 126 | 138,900 bytes |
| 075358 | BICKFORD HEALTH CARE CENTER | 109 | 119,561 bytes |
| 075397 | NEW HAVEN CENTER FOR NURSING & REHABILITATION LLC | 108 | 117,601 bytes |
| 075060 | CIVITA CARE CENTER AT SALMON BROOK | 106 | 115,101 bytes |
| 075158 | NEW LONDON SUB-ACUTE AND NURSING | 104 | 109,279 bytes |
| 075182 | GRANDVIEW REHABILITATION AND HEALTHCARE CENTER | 99 | 104,572 bytes |
| 075348 | ADVANCED CENTER FOR NURSING & REHABILITATION | 95 | 103,122 bytes |
| 075017 | MONTOWESE CENTER FOR HEALTH & REHABILITATION | 87 | 95,433 bytes |
| 075403 | APPLE REHAB WEST HAVEN | 86 | 95,757 bytes |

## Determinism and Validation

The generated directory content hash was `641e99977bcc82f1efefe4e208413be5e94b8d31744570cfdee6782df55d23c9` before and after the required validation-only rerun. This confirms that the default command did not overwrite or otherwise change production output.

## Limitations

- Facility files reflect the available rolling CMS runtime sources, not complete lifetime histories.
- Citation counts provide context and are not a standalone quality score.
- Fine amounts and payment denials are enforcement values, not facility ranking measures.
- No composite score or ranking is calculated.
- K-0211 and K-0133 citation-description lookup gaps remain documented CMS reference-source limitations.
- Duplicate penalty source rows remain preserved and transparently flagged.
- Facility files contain display-relevant detail fields, not duplicate copies of every statewide metadata field.
- The public UI does not load these files in this phase.

## Runtime Behavior

No JavaScript, HTML, CSS, staffing formulas, staffing JSON, historical PBJ JSON, geography JSON, facility-status review JSON, compact summary JSON, or detailed statewide runtime JSON was modified in this phase. Public UI behavior is unchanged, and the Facility Explorer continues to load only the compact summary JSON.

## Recommendation

Proceed to a separately scoped Phase 11D.19B for an optional lazy-loaded Facility Explorer detail section. Fetch only `data/nursing_home_survey_enforcement_details_ct/{CCN}.json` after an explicit user action, retain the compact snapshot as the default view, provide a gentle failure state, and keep health, fire safety, emergency preparedness, and enforcement records visibly separate with their existing caveats.
