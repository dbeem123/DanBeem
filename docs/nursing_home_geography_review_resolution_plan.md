# Nursing Home Geography Review Resolution Plan

Phase 11C.6 planning document. This document does not change public UI, runtime JSON, generated staffing data, historical PBJ data, staffing formulas, Connecticut applicability logic, or public tool behavior.

## 1. Purpose

This plan describes how to resolve the five current Connecticut nursing home records that appear as `Unknown / needs review` in the Statewide Comparison county filter, and how to handle the broader geography manual review queue.

The goal is source-backed geography resolution only. County, municipality, LTCOP region, AAA region, DPH region, or closed/non-current status should remain unresolved unless official source evidence supports the update.

## 2. Current County Geography Status

The current geography crosswalk is `data/nursing_home_facility_geography_ct.json`.

Current documented status:

- Total crosswalk records: 216.
- Current runtime records: 196.
- Current runtime records with county populated from exact April 2026 CMS Provider Information CCN matches: 191.
- Current runtime records with county unavailable: 5.
- Historical PBJ unmatched CCNs: 25.
- Distinct manual-review CCNs: 25.
- The 5 current unknown records are included within the 25 manual-review CCNs.

The Statewide Comparison county filter may continue using the current approach:

- all counties / all facilities includes all 196 current runtime records;
- named county filters include only records with that county populated;
- `Unknown / needs review` shows the 5 current runtime records whose county remains unavailable;
- statewide totals continue including unknown-county records.

## 3. Current Unknown Facilities

These five current runtime facilities are present in `data/nursing_home_staffing_ct.json` and in the historical PBJ facility universe, but did not match April 2026 CMS Provider Information by CCN.

| CCN | Facility name | Current runtime status | Historical PBJ status | City in crosswalk | Current geography status | Current review reason |
|---|---|---|---|---|---|---|
| 075001 | ST JOSEPH'S CENTER | current runtime | historical PBJ | TRUMBULL | county null; needs review | Current runtime CCN not found in April 2026 Provider Information. |
| 075351 | ABBOTT TERRACE HEALTH CENTER | current runtime | historical PBJ | WATERBURY | county null; needs review | Current runtime CCN not found in April 2026 Provider Information. |
| 075415 | COUNTRYSIDE MANOR OF BRISTOL | current runtime | historical PBJ | BRISTOL | county null; needs review | Current runtime CCN not found in April 2026 Provider Information. |
| 075432 | MATTATUCK HEALTH CARE FACILITY, INC. | current runtime | historical PBJ | WATERBURY | county null; needs review | Current runtime CCN not found in April 2026 Provider Information. |
| 075441 | SPRINGS AT EAST HILL, THE | current runtime | historical PBJ | SOUTHBURY | county null; needs review | Current runtime CCN not found in April 2026 Provider Information. |

## 4. Why These Records Remain Unknown

The current geography builder uses exact CCN matches to the April 2026 CMS Provider Information file. These five CCNs were not found in that snapshot, so the builder did not populate county, Provider SSA county code, address, ZIP, or region fields from Provider Information.

The crosswalk includes fallback city values from current runtime or PBJ context, but those city values are not sufficient to assign county. Several Connecticut municipalities may be easy to recognize, but this project should not use city/name memory or informal geography knowledge as evidence. The review standard is official source-backed resolution.

Absence from April 2026 Provider Information also does not prove that a facility is closed, terminated, renamed, merged, temporarily absent, or non-current. It only proves that the CCN did not match that specific Provider Information snapshot.

## 5. Acceptable Source Evidence

County may be resolved only when at least one official or project-approved source provides a source-backed facility identity and location for the CCN or a documented successor/predecessor relationship.

Acceptable source leads include:

- CMS Provider Information current and archived snapshots.
- CMS Care Compare archived provider files.
- CMS certification, termination, or provider history records.
- CMS PBJ source files when they contain facility identity and address fields sufficient for a documented match.
- CT DPH nursing home licensure records.
- CT DPH facility closure, ownership change, relocation, or termination records.
- Official facility address records from CMS or CT DPH.
- Other official state or federal records that identify the CCN, facility name, address, and status.

For county assignment, preferred evidence should include:

- CCN or a formally documented facility identifier relationship;
- facility name;
- official address, city, state, and ZIP;
- county or a documented address-to-county method approved for this project;
- source file or URL;
- source snapshot date or publication date;
- reviewer note explaining why the evidence resolves the record.

For closed/non-current status, preferred evidence should include:

- CCN or official facility identifier;
- termination, closure, certification end, license closure, or provider status field;
- effective date;
- source file or URL;
- reviewer note explaining whether the record should remain in current runtime data, remain historical-only, or be flagged for future data-refresh review.

## 6. Evidence That Is Not Acceptable By Itself

The following should not be enough to assign county or closed/non-current status:

- facility name memory;
- city name memory;
- a county inferred from municipality alone;
- ZIP-to-county lookup without an approved source and ambiguity review;
- address geocoding from a non-official source without project approval;
- search engine snippets;
- commercial directory pages;
- facility marketing pages without CMS or CT DPH confirmation;
- absence from April 2026 Provider Information alone;
- absence from a single current online listing;
- narrative statements without source date, identifier, and audit trail.

## 7. Review Table For Current Unknown Facilities

| Facility name | CCN | Current runtime status | Current geography status | Likely issue category supported by existing data | Required source to resolve county | Required source to mark closed/non-current | Recommended action | Resolution status |
|---|---|---|---|---|---|---|---|---|
| ST JOSEPH'S CENTER | 075001 | Present in current runtime and historical PBJ | `county_name` null; `manual_review_required` true; unmatched to April 2026 Provider Information | `current_and_historical_unmatched`; missing current Provider Information county context | Archived/current CMS Provider Information or Care Compare record, CT DPH licensure record, or other official source linking CCN/facility to official address and county | CMS termination/certification record or CT DPH closure/licensure record with CCN or documented facility identity and effective date | Review official CMS and CT DPH source records; do not assign county from city alone | Do not resolve yet; needs external validation |
| ABBOTT TERRACE HEALTH CENTER | 075351 | Present in current runtime and historical PBJ | `county_name` null; `manual_review_required` true; unmatched to April 2026 Provider Information | `current_and_historical_unmatched`; missing current Provider Information county context | Archived/current CMS Provider Information or Care Compare record, CT DPH licensure record, or other official source linking CCN/facility to official address and county | CMS termination/certification record or CT DPH closure/licensure record with CCN or documented facility identity and effective date | Review official CMS and CT DPH source records; do not assign county from city alone | Do not resolve yet; needs external validation |
| COUNTRYSIDE MANOR OF BRISTOL | 075415 | Present in current runtime and historical PBJ | `county_name` null; `manual_review_required` true; unmatched to April 2026 Provider Information | `current_and_historical_unmatched`; missing current Provider Information county context | Archived/current CMS Provider Information or Care Compare record, CT DPH licensure record, or other official source linking CCN/facility to official address and county | CMS termination/certification record or CT DPH closure/licensure record with CCN or documented facility identity and effective date | Review official CMS and CT DPH source records; do not assign county from city alone | Do not resolve yet; needs external validation |
| MATTATUCK HEALTH CARE FACILITY, INC. | 075432 | Present in current runtime and historical PBJ | `county_name` null; `manual_review_required` true; unmatched to April 2026 Provider Information | `current_and_historical_unmatched`; missing current Provider Information county context | Archived/current CMS Provider Information or Care Compare record, CT DPH licensure record, or other official source linking CCN/facility to official address and county | CMS termination/certification record or CT DPH closure/licensure record with CCN or documented facility identity and effective date | Review official CMS and CT DPH source records; do not assign county from city alone | Do not resolve yet; needs external validation |
| SPRINGS AT EAST HILL, THE | 075441 | Present in current runtime and historical PBJ | `county_name` null; `manual_review_required` true; unmatched to April 2026 Provider Information | `current_and_historical_unmatched`; missing current Provider Information county context | Archived/current CMS Provider Information or Care Compare record, CT DPH licensure record, or other official source linking CCN/facility to official address and county | CMS termination/certification record or CT DPH closure/licensure record with CCN or documented facility identity and effective date | Review official CMS and CT DPH source records; do not assign county from city alone | Do not resolve yet; needs external validation |

## 8. Recommended Review Workflow

1. Preserve the current crosswalk as-is until official evidence is gathered.
2. For each unknown CCN, search archived CMS Provider Information and Care Compare provider files across relevant snapshots.
3. Check CT DPH licensure records for the facility name, CCN if available, address, license status, ownership/name changes, closure, relocation, or termination records.
4. Check CMS termination, certification, or provider history records for CCN-specific status and effective dates.
5. Record every reviewed source, including source name, source file or URL, snapshot/publication date, reviewed fields, and outcome.
6. Classify the issue only after evidence supports it. Possible categories may include:
   - matched_to_archived_provider_info;
   - current_dph_licensed_not_in_provider_info_snapshot;
   - closed_or_terminated_with_source;
   - renamed_or_ccn_changed_with_source;
   - unresolved_after_source_review.
7. If county is resolved, document the source and update only the geography crosswalk in a later implementation phase after validation.
8. If closed/non-current status is resolved, document the status and effective date, then decide in a later data-refresh phase whether runtime inclusion needs review.
9. Re-run crosswalk validation after any future data update.
10. Keep `Unknown / needs review` visible for any unresolved current runtime records.

## 9. Recommended Fields To Add Later If Source-Backed

Do not add these fields until the source review phase identifies a stable evidence model. Possible future fields:

- `review_status`: e.g., `unresolved`, `county_resolved`, `closed_confirmed`, `renamed_or_ccn_changed`, `source_conflict`.
- `review_category`: source-backed reason for the manual-review status.
- `review_source_name`: official source used for the decision.
- `review_source_file_or_url`: source location.
- `review_source_snapshot`: source date or snapshot period.
- `reviewed_by`: reviewer identifier or process name.
- `reviewed_on`: review date.
- `resolved_county_name`: if different from the main county field during staging.
- `resolved_county_source`: source used for county.
- `facility_status`: e.g., `current`, `closed`, `terminated`, `unknown`, if source-backed.
- `facility_status_effective_date`: official effective date when available.
- `successor_ccn` or `predecessor_ccn`: only when an official source documents the relationship.
- `review_notes`: concise, source-backed explanation.

These fields should remain separate from staffing formulas and generated staffing data. The geography crosswalk should stay the source of truth for geography resolution.

## 10. Closed Or Non-Current Status

Closed or non-current status can be documented only with official evidence. Absence from April 2026 Provider Information is a review trigger, not a closure finding.

Acceptable closure/non-current evidence includes:

- CMS termination/certification records with CCN and effective date;
- CT DPH closure, license status, or termination records with facility identity and effective date;
- archived CMS provider records showing status changes, if fields are clear and documented;
- official records documenting a CCN change, merger, relocation, or renamed provider.

If a source confirms closure or non-current status, the review note should avoid overreaching. For example, `CMS termination record confirms certification termination effective YYYY-MM-DD` is acceptable; `facility failed` or causal language is not.

## 11. Transparency If Records Remain Unresolved

If some records remain unresolved after review, the application should preserve transparent handling:

- keep `county_name` null;
- keep `manual_review_required` true;
- keep `Unknown / needs review` available in the county filter;
- keep statewide totals inclusive of unknown records;
- keep named county filters exclusive to source-backed county assignments;
- disclose that county is current-context geography, not historical quarter-specific geography;
- avoid assigning county from city, ZIP, address memory, or informal knowledge.

For historical PBJ analysis, unresolved historical-only CCNs should remain excluded from named-county historical denominators unless a source-backed county assignment is later approved.

## 12. Guardrails

- County should remain null unless supported by official source evidence.
- Closed/non-current status should not be inferred solely from absence in April 2026 Provider Information.
- Current runtime and historical PBJ staffing datasets should not be altered to resolve geography.
- The public county filter may continue showing `Unknown / needs review` until records are resolved.
- Statewide totals should continue including unknown records.
- Named county filters should continue excluding unknown records.
- Do not infer LTCOP, AAA, or DPH regions from county until official or project-approved region mappings are documented.
- Do not use county or region context as a care-quality, compliance, or causation finding.

## 13. Recommended Next Phase

Recommended next phase: **Phase 11C.7: Official Geography Source Review And Evidence Log**.

Expected artifacts:

- source review log for all 25 manual-review CCNs;
- source-backed recommendation for each of the 5 current unknown records;
- source-backed recommendation for the 20 historical-only unmatched records;
- proposed geography crosswalk update only after evidence review;
- validation checklist for any future crosswalk change.

Out of scope for Phase 11C.7:

- public UI changes;
- county summary cards;
- facility county/state comparison cards;
- changes to staffing formulas;
- changes to generated staffing exports;
- changes to CT applicability logic;
- county assignments without official source evidence.
