# Advanced Connecticut Nursing Home Facility Dossier Roadmap

Phase 11A planning document. This document does not change application behavior, calculations, source data, generated exports, formulas, or public runtime logic.

## 1. Purpose and Product Vision

The current Connecticut nursing home staffing tools should evolve toward an advanced Connecticut LTCOP facility dossier: a clean, expandable, dashboard-style facility profile that begins with plain-language consumer context and allows deeper ombudsman, policy, and systems review.

The future dossier should help different users start from the same facility page and move into the level of detail they need. A resident, family member, or community user should be able to understand the facility's basic context and high-level staffing questions. An ombudsman, advocate, researcher, or policy user should be able to expand deeper sections for historical staffing, current CMS context, survey findings, ownership and governance context, reimbursement context, and source-linked review materials.

PBJ320 is useful as inspiration for clean layout, section organization, and drill-down pathways. This project should not copy PBJ320 branding, conclusions, risk scoring, premium logic, proprietary workflows, or unsupported interpretations. The Connecticut LTCOP tools should continue to use their own source-grounded language, public-data caveats, and screening-focused guardrails.

## 2. Current Foundation

The current suite already provides a strong base for a future dossier.

- Facility Explorer: facility-level staffing view using the generated Connecticut current/context export, current CMS snapshot context, facility identity, current staffing trend rows, historical PBJ loaded on demand, print summaries, CSV exports, and links to affiliation context.
- Statewide Comparison: latest-quarter statewide comparison table with search, filters, sorting, summary analytics, print reporting, CSV export, copyable briefing summaries, and facility drill-down links.
- Change Over Time: historical PBJ change explorer with latest-4, latest-8, full-history, and custom windows; CT direct-care decline/improvement modes; CT crossing modes limited by applicability fields; contract staffing increase mode; RN HPRD decrease mode; print, CSV, and copy-summary actions.
- Persistent Patterns: historical PBJ persistent-pattern explorer with CT 3.00 direct-care, CT 0.84 licensed, contract 10%+, and contract 20%+ modes; minimum-quarter and eligible-share thresholds; quarter-by-quarter pattern strips; print, CSV, and copy-summary actions.
- Ownership / Affiliation: current affiliation-level staffing explorer based on CMS SNF Enrollment affiliation fields, with affiliation summaries, facility comparisons, persistent staffing pattern summaries, print actions, CSV exports, and links back to facility views.
- Methodology page: public explanation of source data, HPRD formulas, PBJ row inclusion rules, Connecticut direct-care comparison estimates, current CMS context, case-mix limitations, affiliation context, source links, audit validation, and screening-use limitations.

The current data architecture separates current/context data from PBJ-only historical data:

- `data/nursing_home_staffing_ct.json` remains the current/context dataset. It contains current and recent staffing rows plus current CMS context such as Provider Information, Care Compare ratings when available, Quality Measures Claims, CMS case-mix staffing comparison points, and SNF Enrollment affiliation context.
- `data/nursing_home_staffing_history_ct.json` is the PBJ-only historical dataset. It covers Q4 2017 through Q4 2025 and does not embed current CMS ratings, quality measures, case-mix benchmark fields, or affiliation fields as historical quarter-specific values.
- Current CMS snapshot context is not historical quarter-specific. It should be displayed as current context unless historically aligned snapshots are later acquired, validated, and explicitly integrated.
- The historical PBJ audit is clean: 6,569 facility-quarter rows, 33 source quarters, 0 missing rows, 0 extra rows, 0 field mismatches, 0 CT applicability mismatches, and 0 forbidden current-context field hits.
- Connecticut applicability guardrails are already in place. CT comparison labels and crossing logic should only be used for Connecticut facilities and applicable periods.

## 3. Proposed Advanced Facility Dossier Layout

The future facility page should use clean accordion or card sections. The first screen should be useful immediately, and deeper sections should be expandable without overwhelming a consumer user.

### 1. Facility Overview and Current CMS Snapshot

Purpose: establish the facility identity, current CMS context, and the most important caveats before users interpret deeper data.

Intended user questions:

- Is this the facility I meant to review?
- What is the current CMS snapshot context?
- What are the latest available staffing and quality context dates?
- What should I know before comparing this facility over time?

Likely data sources:

- `data/nursing_home_staffing_ct.json`
- CMS Nursing Home Provider Information
- CMS Quality Measures Claims already integrated for current context
- CMS SNF Enrollment affiliation context already integrated for current context
- Future source-currency metadata and official source links

What can be shown now:

- Facility name, address, CCN, beds, ownership type, current CMS rating context where available, quality-measure context where available, current case-mix staffing comparison point, source dates, and source caveats.
- Current affiliation context from SNF Enrollment when available.
- Current staffing trend and links into historical PBJ views.

What requires future data validation:

- SFF/Candidate status and Abuse Icon status, unless verified from official fields and explained carefully.
- Current inspection summary fields, deficiency counts, and enforcement context.
- County, region, DSS identifiers, and CT DPH license crosswalks.

Key guardrails:

- Current CMS context is a snapshot, not historical quarter-specific data.
- Ratings and quality measures are imported context, not calculated by this project.
- Overview language should support screening and question-building, not findings.

### 2. Historical PBJ Staffing

Purpose: show long-range PBJ staffing trends and allow users to compare recent staffing with the full public PBJ history.

Intended user questions:

- How has reported staffing changed across the facility's available PBJ history?
- What happened in the latest 4 or 8 quarters?
- Are there repeated low-staffing or high-contract-staffing patterns?
- Are missing quarters present, and how should they be interpreted?

Likely data sources:

- `data/nursing_home_staffing_history_ct.json`
- `source_data/pbj` quarterly PBJ Daily Nurse Staffing files
- Historical audit report and data contract documentation

What can be shown now:

- Latest 8 quarters and full PBJ history for selected facilities.
- Quarterly total nurse HPRD, RN HPRD, LPN/LVN HPRD, nurse aide HPRD, contract staff percentage, CT direct-care estimate, CT licensed estimate, and CT applicability context.
- Historical CSV export.

What requires future data validation:

- Historically aligned CMS ratings, quality measures, case-mix comparison points, affiliation, ownership, and enforcement context.
- Future PBJ quarters after separate rebuild and audit.

Key guardrails:

- Missing PBJ rows are unavailable context, not zero staffing.
- Historical PBJ rows should remain PBJ-only unless a future historical context layer is explicitly validated.
- CT comparison status is limited to applicable Connecticut periods.

### 3. Daily Staffing Screening Tools

Purpose: provide day-level PBJ screening views that can identify daily staffing questions hidden inside quarterly averages.

Intended user questions:

- Were there individual days with low reported direct-care staffing?
- How many days were below a screening comparison point?
- Did below-comparison days cluster by weekday, month, or quarter?
- What was the census on the days being reviewed?

Likely data sources:

- CMS PBJ Daily Nurse Staffing quarterly files already used as source inputs
- Future daily screening export or derived static facility-day data layer
- CT applicability rules

What can be shown now:

- Nothing in the public app yet. The current app exposes facility-quarter summaries, not day-level tables.

What requires future data validation:

- A daily export data contract.
- Independent daily audit logic.
- UI performance testing for facility-day tables and exports.
- Applicability rules for daily CT screening labels.

Key guardrails:

- Daily PBJ screening is not a formal DPH compliance finding.
- Zero-census days must be excluded from denominator-based day counts.
- Daily screening should be clearly separated from quarterly public summaries.

### 4. Local, County, and Regional Comparison

Purpose: place a facility's staffing and context in a local comparison frame.

Intended user questions:

- How does this facility compare with nearby facilities?
- How does it compare with its county and statewide Connecticut?
- Are similar patterns visible across a county or service region?

Likely data sources:

- Current and historical staffing exports
- CMS Provider Information address fields
- Future facility-to-county or facility-to-region crosswalk
- Possible CT LTCOP service-region crosswalk if approved

What can be shown now:

- Statewide latest-quarter comparisons and facility-level historical comparisons.

What requires future data validation:

- County field validation or a facility-to-county crosswalk.
- Local peer grouping rules.
- Region definitions and governance for LTCOP or service-region views.

Key guardrails:

- Local comparison groups should disclose their construction.
- County and region summaries should not imply causation or facility quality by themselves.
- Small-group summaries may need suppression or caveats.

### 5. Quality Measures

Purpose: integrate CMS quality-measure context alongside staffing without confusing quality measures with staffing measures.

Intended user questions:

- What current CMS quality-measure context is available for this facility?
- Which measures are claims-based or MDS-based?
- What period does each measure represent?
- How should quality-measure context be interpreted alongside staffing?

Likely data sources:

- CMS Quality Measures Claims already integrated for current context
- Future CMS MDS Quality Measures file
- CMS Nursing Home Data Dictionary

What can be shown now:

- Current claims-based quality-measure context where available in `data/nursing_home_staffing_ct.json`.

What requires future data validation:

- MDS quality-measure download, schema review, measure selection, and display rules.
- Measure grouping and consumer-friendly descriptions.
- Historical quality-measure snapshots if historical display is desired.

Key guardrails:

- Quality measures are imported CMS context, not calculated by this project.
- Quality measures do not replace PBJ staffing metrics, survey findings, resident experience, or formal review.
- Measure periods and snapshot dates must be visible.

### 6. Inspections, F-Tags, Deficiencies, and Enforcement

Purpose: add official oversight context that answers what federal or state oversight records show, without turning summaries into unsupported conclusions.

Intended user questions:

- When was the most recent survey?
- What deficiencies were cited?
- Which F-tags appear, and what do they mean in plain language?
- Were citations repeated over time?
- Were penalties or enforcement actions reported?

Likely data sources:

- CMS Health Deficiencies
- CMS Fire Safety Deficiencies
- CMS Citation Descriptions
- CMS Penalties
- CMS Provider Information fields for SFF/Candidate or Abuse Icon only if verified
- CT DPH inspection reports, enforcement reports, consent orders, or other public oversight materials if available

What can be shown now:

- Nothing beyond current Methodology/source-roadmap references. Facility-level deficiency and enforcement data are not currently integrated.

What requires future data validation:

- Source downloads, schema profiles, citation joins, official definitions, and source-link strategy.
- State versus federal source distinction.
- Consumer summary wording and correction-status handling.

Key guardrails:

- Cite or link official source documents where possible.
- Do not make unsupported conclusions about neglect, harm, causation, or legal violations.
- Distinguish CMS survey data from CT DPH reports and enforcement materials.

### 7. Ownership, Affiliation, Chain, Management, and Governance History

Purpose: help users understand reported organizational, ownership, affiliation, and governance context without collapsing distinct concepts.

Intended user questions:

- What current affiliation entity is reported for this facility?
- What owner or management entities are reported by CMS?
- Are there ownership-change events?
- Is there validated CT DPH governance or leadership timeline context?
- How should affiliation, ownership, management, chain, and related-party relationships be distinguished?

Likely data sources:

- Current CMS SNF Enrollment affiliation data already integrated
- CMS Ownership data
- CMS SNF Change of Ownership and CHOW Owner Information
- CMS Chain Performance methodology and files, only after mapping review
- CT DPH management/governance records
- Future CT DPH-to-CMS CCN crosswalk
- CT DSS related-party fields only if source fields support them

What can be shown now:

- Current SNF Enrollment affiliation context and affiliation-level staffing summaries.

What requires future data validation:

- CMS Ownership parsing and normalization.
- CHOW transaction field validation.
- CT DPH facility license to CMS CCN crosswalk.
- Administrator/DON timeline rules.
- Chain and related-party mapping definitions.

Key guardrails:

- Do not collapse ownership, management, affiliation, chain, and related-party concepts into one label.
- Do not imply causation between governance changes and staffing outcomes without stronger evidence.
- Clearly distinguish current snapshots from historical relationship periods.

### 8. CT DSS Rates, Census, Cost Reports, and Financial Context

Purpose: provide Connecticut-specific reimbursement, census, and financial context when a validated crosswalk and source definitions support it.

Intended user questions:

- What Medicaid rate or reimbursement context exists for this facility?
- What census or capacity context is reported by CT DSS?
- Are cost reports or financial filings available?
- Are related-party or management-fee fields present in official records?

Likely data sources:

- CT DSS nursing facility rates
- CT DSS monthly census files
- CT DSS quarterly case-mix rate calculations
- CT DSS cost reports
- CT DSS cost comparison reports
- CT DSS rate computation files

What can be shown now:

- Nothing in the public app. Existing DSS work is roadmap/source-validation context only.

What requires future data validation:

- CT DSS-to-CMS CCN crosswalk.
- PDF/table extraction and schema validation.
- Field definitions, period definitions, and financial interpretation rules.

Key guardrails:

- Reimbursement and cost context should not be framed as staffing findings.
- Financial fields should be explained carefully and not overinterpreted.
- DSS identifiers and CMS CCNs require validated matching before public display.

### 9. Reports, Exports, and Consumer Summary

Purpose: help users carry a structured, source-linked summary out of the tool for review, discussion, or follow-up.

Intended user questions:

- What are the key facts and questions for this facility?
- What source dates and caveats should be attached?
- What official records should I review next?
- Can I export the data behind a selected view?

Likely data sources:

- Existing current/context and historical PBJ exports
- Future deficiency, ownership, governance, DSS, and regional data layers
- Source manifest and source-currency metadata

What can be shown now:

- Current print summaries, CSV exports, and copyable briefing summaries across existing tools.

What requires future data validation:

- Unified facility dossier report structure.
- Source-linked consumer summary templates.
- Future PDF generation if approved.
- Rules for including unavailable or unvalidated sections.

Key guardrails:

- Consumer summaries should link back to official sources where possible.
- Summaries should distinguish facts, screening questions, limitations, and follow-up prompts.
- Reports should not present unsupported risk scores or findings.

## 4. Daily Staffing Screening Concept

A future daily PBJ staffing screening module could use CMS PBJ Daily Nurse Staffing data to show facility-day screening context. It should be developed as a separate prototype after a daily data contract, performance approach, and audit method are approved.

Possible features:

- Daily direct-care HPRD estimate.
- Daily licensed HPRD estimate.
- Total nurse HPRD.
- RN HPRD.
- Census.
- Zero-census day exclusion.
- Below-comparison day counts.
- Met-day and below-standard day counts.
- Weekday summaries.
- Quarterly summaries.
- Day-level detail table.
- Daily CSV export.
- Possible open-day drill-down.
- Possible day-level print/PDF later.

Guardrails:

- PBJ-derived screening only.
- Not a formal DPH compliance finding.
- CT threshold status only for applicable Connecticut periods.
- No zero-census days in denominator-based calculations.
- Clearly separate daily screening from quarterly public summaries.

## 5. Employee / Roster Tracker Concept

An employee or roster tracker is future-only.

This concept depends on CMS PBJ Employee Detail files and is not part of the current historical PBJ release. It would require separate source validation, schema profiling, privacy review, ethics review, public-display review, and interpretation review before any public or semi-public display.

Potentially appropriate uses may include workforce continuity or roster-level review, but only if source fields, privacy risks, and use limitations are carefully understood. The project should avoid overinterpreting individual-level employee data, should not expose sensitive interpretations about specific workers, and should not add public individual employee-level analysis without explicit approval.

## 6. County and Connecticut Regional Comparison Roadmap

County and regional comparison should help users understand a facility in local context.

Potential outputs:

- Facility compared to county.
- County compared to statewide Connecticut.
- County-by-county summaries.
- Possible LTCOP region or service-region comparison.

Enabling work:

- Validate whether an official county field exists in integrated source data or create a facility-to-county crosswalk.
- Define county and regional groupings.
- Document whether groups use facility count, resident days, beds, or simple facility averages.
- Decide whether small-group suppression or caveats are needed.

Metrics that could be summarized by county:

- Staffing HPRD.
- CT comparison status counts.
- Persistent staffing patterns.
- Contract staffing use.
- CMS ratings and QM context.
- Future deficiencies and enforcement patterns.

Guardrails:

- County and regional comparisons are screening context, not findings.
- CT comparison status remains limited to Connecticut facilities and applicable periods.
- Crosswalk confidence and source dates must be documented.

## 7. Nearby-State / Regional Comparison Roadmap

Nearby-state comparison could help users understand Connecticut in a broader regional frame, but it should use a separate architecture and careful metric selection.

Potential comparison geographies:

- Connecticut compared with Massachusetts.
- Connecticut compared with Rhode Island.
- Connecticut compared with New York.
- Connecticut compared with New Jersey.
- Connecticut compared with New England or selected nearby states.

Rules:

- Use common CMS measures only.
- Do not apply Connecticut thresholds to non-Connecticut facilities.
- Use controlled multi-state extracts with documented source dates.
- Keep regional extracts separate from the Connecticut-only current/context file unless a new regional data architecture is designed.

Likely uses:

- Regional staffing HPRD comparisons.
- Contract staffing comparisons.
- CMS rating or quality-measure context using common CMS definitions.
- Future survey or enforcement summaries using common CMS fields.

Guardrails:

- State laws, staffing thresholds, and enforcement regimes differ.
- Non-Connecticut facilities should not receive CT threshold labels.
- Multi-state files need their own data contract and audit checks.

## 8. Survey, F-Tag, Deficiency, and Enforcement Roadmap

Future source domains:

- CMS Health Deficiencies.
- CMS Fire Safety Deficiencies.
- CMS Citation Descriptions.
- CMS Penalties.
- CMS SFF/Candidate status if available through official source fields.
- CMS Abuse Icon status only if verified through official fields.
- CT DPH inspection reports, enforcement reports, consent orders, or other public oversight materials if available.

Consumer-facing outputs:

- Most recent survey date.
- Number of deficiencies.
- F-tags with plain-language summaries.
- Severity/scope if available.
- Repeated citations over time.
- Penalties or enforcement actions.
- Links to official reports.
- Concise consumer summary with full source links.

Validation needs:

- Download and profile facility-level Health and Fire Safety Deficiencies.
- Join F-tags to Citation Descriptions.
- Confirm how correction dates, IDR/IIDR, complaint surveys, and standard surveys should be displayed.
- Download and profile Penalties.
- Verify SFF/Candidate and Abuse Icon fields from official CMS data before display.
- Inventory CT DPH public oversight materials and determine whether structured extraction is feasible.

Guardrails:

- Summaries must cite or link official source documents where possible.
- No unsupported conclusions about neglect, harm, or causation.
- Distinguish federal CMS survey data from CT DPH reports and enforcement materials.
- Explain scope/severity and correction status in plain language where available.

## 9. Ownership / Entity / Governance Expansion

Ownership and governance should become a future product pathway, but it must preserve source definitions.

Future product concepts:

- Owner/entity lookup as a future primary navigation path.
- Facility-to-owner/entity drill-down.
- Owner/entity pages listing linked Connecticut facilities.
- Current affiliation versus ownership versus management versus chain versus related-party relationship context.
- Ownership-change timeline where CHOW data supports it.
- CT DPH Administrator/DON governance timeline concepts if validated.

Likely sources:

- CMS Ownership data.
- SNF Enrollment affiliation data.
- SNF CHOW and CHOW Owner Information files.
- CT DPH management/governance records.
- Administrator/DON timeline records if validated.
- CT DSS related-party or management-fee context only if source fields support it.

Guardrails:

- Do not collapse ownership, management, affiliation, chain, and related-party relationships into one concept.
- Do not imply causation between ownership/governance changes and staffing outcomes without stronger evidence.
- Clearly distinguish current snapshots from historical relationship periods.
- Chain performance should not be treated as equivalent to CMS ownership or SNF Enrollment affiliation unless a documented mapping supports it.

## 10. CT DSS Financial and Reimbursement Layer

Future possible sources:

- Medicaid nursing facility rates.
- Monthly census files.
- Quarterly case-mix rate calculations.
- Cost reports.
- Cost comparison reports.
- Rate computation files.
- Related-party or management-fee context if source fields support it.

Potential uses:

- Facility Medicaid rate context.
- Monthly census and capacity context.
- Cost-report and reimbursement context.
- Financial transparency context.
- Related-party or management-fee review prompts where source fields are explicit.

Validation needs:

- Build a validated CT DSS-to-CMS CCN crosswalk.
- Profile identifiers, file formats, periods, and field definitions.
- Separate PDF indexing from structured data extraction.
- Document what each financial field represents and what it does not establish.

Guardrails:

- Financial context should be presented carefully and not overinterpreted.
- Reimbursement and cost context are separate from staffing findings.
- Do not infer ownership, quality, causation, or legal responsibility from financial fields alone.

## 11. Recommended Next Phases

### Phase 11B: Advanced Facility Dossier UI Wireframe and Section Architecture

Objective: design the future facility dossier layout using existing data only.

Expected files or artifacts:

- Wireframe plan or static prototype notes.
- Section inventory and progressive disclosure rules.
- Data availability map for each dossier section.
- Consumer summary placement plan.

Intentionally out of scope:

- New datasets.
- Formula changes.
- Generated data changes.
- Public interpretation changes beyond approved planning copy.

Recommended validation checks:

- Confirm all displayed data can come from existing JSON files.
- Confirm current snapshot versus historical PBJ separation remains visible.
- Run HTML/CSS/JS checks only if a prototype file is created.

### Phase 11C: County and Regional Comparison Source/Crosswalk Validation

Objective: determine how to assign Connecticut facilities to county and possible LTCOP/service regions.

Expected files or artifacts:

- Facility-to-county validation report.
- Possible region crosswalk proposal.
- Aggregation methodology note.
- Small-group caveat recommendation.

Intentionally out of scope:

- Public county dashboards.
- Multi-state comparisons.
- CT DSS integration.

Recommended validation checks:

- Compare facility address/county evidence across official sources.
- Review unmatched or ambiguous facilities.
- Document confidence levels and manual-review needs.

### Phase 11D: CMS Survey/F-Tag/Deficiency/Penalty Source Inventory and Prototype

Objective: inventory and validate official CMS survey and enforcement sources before public display.

Expected files or artifacts:

- Source inventory report.
- Schema profile for Health Deficiencies, Fire Safety Deficiencies, Citation Descriptions, and Penalties.
- Prototype data contract or non-public sample join.
- Consumer wording and source-link plan.

Intentionally out of scope:

- Public enforcement conclusions.
- Causation or neglect findings.
- CT DPH enforcement integration unless separately scoped.

Recommended validation checks:

- Validate joins by CCN, survey date, and tag.
- Confirm citation description matching.
- Check correction status and scope/severity interpretation.
- Confirm source freshness and archived raw files.

### Phase 11E: Daily PBJ Staffing Screening Prototype

Objective: prototype day-level PBJ screening for a facility using existing raw PBJ Daily Nurse Staffing source files.

Expected files or artifacts:

- Daily data contract proposal.
- Prototype generator or analysis script.
- Daily audit approach.
- UI wireframe for daily table, weekday summaries, and CSV export.

Intentionally out of scope:

- Formal compliance findings.
- Employee Detail data.
- Public release without audit and wording review.

Recommended validation checks:

- Verify zero-census exclusion.
- Recompute daily HPRD fields independently.
- Confirm daily summaries reconcile to quarterly aggregates where expected.
- Validate CT applicability for daily status labels.

### Phase 11F: Ownership/Entity Explorer Planning and Source Validation

Objective: plan a future owner/entity pathway distinct from current affiliation summaries.

Expected files or artifacts:

- CMS Ownership schema profile.
- CHOW and CHOW Owner Information inventory.
- Entity normalization notes.
- Conceptual separation guide for ownership, management, affiliation, chain, and related-party relationships.

Intentionally out of scope:

- Public owner/entity claims before validation.
- Chain mapping without methodology review.
- CT DSS related-party display.

Recommended validation checks:

- Verify CCN joins and role fields.
- Compare Ownership rows with SNF Enrollment affiliation context without merging concepts.
- Document ownership percentages, roles, association dates, and current-versus-history limits.

### Phase 11G: CT DPH Governance Timeline Validation

Objective: validate CT DPH governance and leadership timeline sources before any facility dossier integration.

Expected files or artifacts:

- CT DPH source validation update.
- DPH license to CMS CCN crosswalk report.
- Administrator/DON role-period modeling note.
- Governance timeline wireframe or data model update.

Intentionally out of scope:

- Public governance timeline display.
- Causation claims between governance changes and staffing outcomes.
- Management Company Explorer unless assignment-period source exists.

Recommended validation checks:

- Validate DPH facility license normalization.
- Manually review CCN crosswalk matches.
- Preserve raw records and cleaned analytical periods separately.
- Review missing start/end date treatment.

### Phase 11H: CT DSS Financial/Census Source Validation

Objective: validate CT DSS reimbursement, census, cost-report, and financial context sources.

Expected files or artifacts:

- DSS source inventory update.
- DSS-to-CMS CCN crosswalk proposal.
- Sample extraction report for rates, census, cost reports, and case-mix rate files.
- Financial interpretation guardrail note.

Intentionally out of scope:

- Public financial dashboards.
- Related-party claims without explicit source fields.
- Any staffing causation claims from financial context.

Recommended validation checks:

- Validate identifiers and crosswalk confidence.
- Preserve source PDFs or raw structured files.
- Document period definitions and field meanings.
- Separate reimbursement, census, cost, and related-party concepts.

## 12. Standing Guardrails

- Screening, not findings.
- No causation claims.
- No legal compliance claim without official confirmation.
- Current snapshot versus historical data separation.
- CT thresholds only for Connecticut facilities and applicable periods.
- Source freshness and audit trail required for every new data layer.
- Consumer summaries should link to official source documents where possible.
- Ownership, management, affiliation, chain, and related-party concepts must remain distinct.
- No individual employee-level public interpretation without separate privacy and ethics review.

## 13. Decision Point After Phase 11A

Recommended next step: build Phase 11B next. Phase 11B should create the advanced facility dossier UI wireframe and section architecture using existing data only.

Do not integrate new data until the dossier layout has a clean home for future sections. The next build should answer where each future domain belongs, what should be visible by default, what should remain expandable, and how source caveats travel with each section.

