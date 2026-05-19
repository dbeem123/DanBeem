# DanBeem Ombudsman Tools and Resource Lab

Static ombudsman workflow tools focused on drafting support, NORS crosswalk reference lookup, responsible-use transparency, and related internal utilities.

## Setup & Running

Start a simple local static file server:

```bash
# Windows (PowerShell)
python -m http.server 8000

# Or with Node
npx http-server -p 8000
```

Then open:

- **Landing Page:** http://localhost:8000/index.html
- **Drafting Assistant:** http://localhost:8000/tools/drafting-assistant.html
- **NORS Crosswalk:** http://localhost:8000/tools/nors-crosswalk.html
- **Nursing Home Staffing Explorer:** http://localhost:8000/tools/nursing-home-staffing-explorer.html
- **Ownership & Staffing Explorer:** http://localhost:8000/tools/nursing-home-ownership-staffing-explorer.html
- **Responsible Use:** http://localhost:8000/tools/responsible-use.html
- **Impact Dashboard:** http://localhost:8000/dashboards/impact-2024.html

## Current Architecture

- **Frontend:** Static HTML/CSS/JS
- **Data model:** Local JSON files, especially under `data/`
- **Crosswalk logic:** Shared loader and matching logic in `Assets/crosswalk.js`
- **Theme:** Dark glass UI with accessible focus states and semantic structure

## Current Primary Workflow

### Landing Page

- entry point for the featured tools
- links to the current NORS/drafting workflow

### Drafting & Reference Assistant

- structured case-note drafting support
- checklist review and validation
- inline topic/reference support driven by local data

### NORS Crosswalk Tool

- NORS code lookup
- keyword / concern lookup
- authority trail grouped by topic
- review support, trace output, and human-review flags

### Nursing Home Staffing Explorer

- public-facing PBJ staffing prototype
- normalized local mock facility data from `data/nursing_home_staffing_mock.json`
- screening-level metrics, quarterly comparison table, and ombudsman follow-up questions
- includes Connecticut direct-care staffing comparison fields as PBJ-derived screening estimates, not compliance determinations

### Ownership & Staffing Explorer

- public-facing affiliation-level staffing view
- groups Connecticut facilities by CMS SNF Enrollment affiliation entity when available
- derives group averages and facility comparisons from `data/nursing_home_staffing_ct.json`
- summarizes latest-quarter Connecticut direct-care comparison estimates at the affiliation level
- frames ownership and staffing patterns as screening context, not legal or care-quality findings

### Responsible Use & Sources

- source registry
- source-pack transparency
- workflow guardrails
- glossary and review flags

### Impact Dashboard

- annual-review dashboard and report links

## Data-Driven Source Of Truth

Per repo rules, use JSON files in `/data` as the source of truth whenever a normalized version exists.

Important files include:

- `data/nors_source_pack_lock.json`
- `data/source_registry.json`
- `data/nors_resource_catalog.json`
- `data/case_note_templates.json`
- `data/case_note_validation_rules.json`
- `data/current_tool_context_registry.json`

## Phase 2 Data Architecture

The Nursing Home Staffing Explorer remains a static page. It should not fetch, parse, or aggregate full CMS PBJ datasets in the browser. Instead, Phase 2 uses a production-oriented static JSON contract in `data/nursing_home_staffing_mock.json`:

- top-level dataset metadata, reporting period, source dataset names, source releases, and freshness dates
- facility directory rows keyed by CCN
- quarterly staffing rows keyed by CCN and normalized quarter
- metrics already precomputed offline, including total nurse HPRD, RN HPRD, LPN/LVN HPRD, nurse aide HPRD, contract staff percentage, Connecticut direct-care comparison estimates, and optional case-mix benchmark HPRD
- UI interpretation blocks generated into the static export, not computed from raw CMS files in the browser

The field map is documented in `docs/nursing_home_staffing_data_contract.md`. Phase 2B should generate this JSON from official CMS PBJ and Provider Information source files before deployment.

### Local PBJ Generator

Place manually downloaded CMS Payroll Based Journal Daily Nurse Staffing CSV files in:

`source_data/pbj/`

Generate the Connecticut static export:

```bash
python scripts/build_nursing_home_staffing_ct.py --input-dir source_data/pbj --output data/nursing_home_staffing_ct.json
```

Optionally enrich facility metadata with a manually downloaded CMS Nursing Home Provider Information CSV:

```bash
python scripts/build_nursing_home_staffing_ct.py --input-dir source_data/pbj --provider-info source_data/provider_info/NH_ProviderInfo_MonYYYY.csv --output data/nursing_home_staffing_ct.json
```

When Provider Information is supplied, the generator also copies CMS case-mix staffing HPRD fields into the explorer's `benchmarks` object when available. These benchmark fields are contextual comparisons only; PBJ-calculated HPRD remains the actual staffing metric shown by the explorer.

The generator also emits Connecticut direct-care staffing comparison fields. Connecticut Title 19 Sec. 19-13-D8t(m)(6) establishes direct-care staffing minimums of 3.00 total nursing and nurse's aide HPRD and 0.84 licensed nursing HPRD. The PBJ-derived screening formulas are:

- `ct_direct_care_total_hprd_estimate = (Hrs_RN + Hrs_LPN + Hrs_CNA + Hrs_NAtrn + Hrs_MedAide) / resident_days`
- `ct_direct_care_licensed_nurse_hprd_estimate = (Hrs_RN + Hrs_LPN) / resident_days`

These estimates intentionally exclude `Hrs_RNDON`, `Hrs_RNadmin`, and `Hrs_LPNadmin` because the Connecticut regulation states that the director of nurses or assistant director of nurses shall not be included in satisfying the minimum requirements. The existing PBJ total nurse HPRD metric is not replaced. The Connecticut comparison fields are screening indicators only and should not be described as formal compliance findings.

Optionally add CMS Skilled Nursing Facility Enrollments legal organization and affiliation context:

```bash
python scripts/build_nursing_home_staffing_ct.py --input-dir source_data/pbj --provider-info source_data/provider_info/NH_ProviderInfo_MonYYYY.csv --snf-enrollments source_data/snf_enrollments/SNF_Enrollments_2026.05.01.csv --output data/nursing_home_staffing_ct.json
```

SNF Enrollments adds CCN-linked organization, DBA, NPI, proprietary/nonprofit, organization structure, and affiliation entity fields. Provider Information remains the source for current facility display metadata.

The explorer loads `data/nursing_home_staffing_ct.json` when present, then falls back to `data/nursing_home_staffing_mock.json` for development. Start the static server and open:

`http://localhost:8000/tools/nursing-home-staffing-explorer.html`

The affiliation-level ownership view uses the same generated Connecticut export:

`http://localhost:8000/tools/nursing-home-ownership-staffing-explorer.html`

## Deployment Notes

- the current NORS crosswalk and drafting workflow are closed-loop and local-data driven
- there is no required backend for the current primary workflow
- production hosting can remain a static-site deployment as long as the app stays in this architecture

## Notes

- **No live AI dependency required for the current NORS/drafting flow**
- **Informational only** guardrails are built into the workflow
- **Human review remains required**
- **Source transparency is part of the product**

## Contact & Support

For issues or questions, use the repository history and source-of-truth data files as the starting point.
