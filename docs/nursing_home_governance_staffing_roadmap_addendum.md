# Governance And Staffing Roadmap Addendum

Phase 10B.1 adds Connecticut DPH facility governance and leadership timeline context as a future source domain. This is planning only; no public application behavior changed.

## New Future Domain

### CT DPH Facility Governance, Leadership Stability, And Management Timeline Context

This domain is distinct from:

- Owner / Entity Explorer
- CMS SNF Enrollment Affiliation Explorer
- CMS Chain Performance
- CMS Change of Ownership
- CT DSS Financial / Related-Party Context
- Deficiencies and enforcement context

The newly discovered CT DPH sources can support a state-side governance timeline keyed by CT facility license number. They cannot be used in the current CMS CCN-keyed dashboard until a validated crosswalk exists.

## Product Concepts To Evaluate Later

### 1. Facility Governance Timeline Module

Possible future facility dossier section:

- PBJ staffing trend band
- Administrator period band
- Director of Nurses period band
- Medical Director period band, if useful and clean enough
- Management-company periods only if an explicit assignment source is found
- Ownership-change markers only after CMS CHOW validation
- CT DSS rate/census events only after a validated crosswalk

### 2. Statewide Governance Stability Screening View

Possible future review categories:

- Frequent Administrator changes
- Frequent DON changes
- Repeated temporary DON periods
- Incomplete role coverage
- Leadership transitions temporally aligned with persistent staffing screening patterns

These should be framed as screening context and questions for review, not findings of poor care, causation, or violations.

### 3. Governance-Oriented Review Packet

Possible future staff-facing copy packet:

- staffing trend
- known leadership periods
- documented transition events
- ownership/affiliation context
- what the data shows
- what it may suggest for follow-up
- what it cannot prove

### 4. Management Company Explorer

Defer. The current management-company file is a license registry only and does not assign companies to facilities or dates.

## Roadmap Sequence Recommendation

Recommended sequence after Phase 10B.1:

1. Historical PBJ single-quarter compatibility test and staged backfill.
2. CT DPH-to-CMS CCN crosswalk construction as a near-term enabling project.
3. Facility Governance Timeline proof of concept after crosswalk validation and initial historical PBJ expansion.
4. Management Company Explorer deferred until explicit facility-to-company assignment periods are available.
5. Owner / Entity Explorer retained as a separate high-value future pathway.

## Comparison With Other Candidate Phases

| Candidate phase | Value | Data certainty | Complexity | Interpretive risk | Recommended timing |
|---|---|---|---|---|---|
| Historical PBJ backfill | Very high; strengthens every existing staffing view | High | Medium | Moderate historical comparability caveats | First |
| Source freshness display | Completed in Phase 10B | High | Low | Low | Done |
| CT DPH-to-CMS CCN crosswalk | High enabling value for governance and DSS | Medium-high after license/address review | Medium | Low if manual-reviewed | Near-term parallel/enabling |
| Facility governance timeline | High for facility dossier and review packets | Medium after cleaning | Medium-high | Moderate; temporal context only | After crosswalk and initial PBJ backfill |
| CMS SFF/Candidate factual status | High public-recognition value | High if using Provider Info field | Low | Moderate labeling sensitivity | Near-term small integration |
| Abuse Icon verification | High but sensitive | High if using official Provider Info field | Low-medium | High wording sensitivity | Near-term after definition review |
| Deficiencies/citations | High context value | High once files downloaded | Medium | Moderate date/severity nuance | Medium-term |
| Penalties/enforcement | High context value | High once file downloaded | Medium | Moderate historical nuance | Medium-term |
| Owner / Entity Explorer | High LTCOP and public value | Medium-high with CMS ownership file | Medium-high | Moderate conceptual separation risk | Medium-term, separate from governance |
| CT DSS rate/census context | High state-specific value | Medium pending crosswalk | Medium-high | Moderate; reimbursement concepts need care | Medium-term after crosswalk |
| CT DSS cost-report/related-party context | High policy value | Medium | High | High; financial interpretation risk | Later |
| Additional quality measures | Medium | High | Medium | Moderate display overload | Later or selective |
| Chain performance context | Medium | Medium until mapping validated | Medium | High mapping risk | Later / do not merge yet |

## Guardrails

- Do not describe staffing changes near leadership transitions as caused by those transitions.
- Do not equate DPH management history with CMS ownership, CMS affiliation entity, chain performance, or CT DSS related-party relationships.
- Do not create management-company views without assignment-period data.
- Preserve raw DPH records and build cleaned analytical periods separately.
