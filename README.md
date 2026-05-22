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
- **Connecticut Nursing Home Staffing Explorer:** http://localhost:8000/tools/nursing-home-staffing-explorer.html
- **Statewide Staffing Comparison:** http://localhost:8000/tools/nursing-home-statewide-staffing-comparison.html
- **Staffing Change Over Time:** http://localhost:8000/tools/nursing-home-staffing-change-over-time.html
- **Persistent Staffing Patterns:** http://localhost:8000/tools/nursing-home-persistent-staffing-patterns.html
- **Ownership & Staffing Explorer:** http://localhost:8000/tools/nursing-home-ownership-staffing-explorer.html
- **Staffing Data Methodology:** http://localhost:8000/tools/nursing-home-staffing-methodology.html
- **Responsible Use:** http://localhost:8000/tools/responsible-use.html
- **Impact Dashboard:** http://localhost:8000/dashboards/impact-2024.html

The landing page includes a Connecticut Nursing Home Staffing Transparency Tools overview that explains which staffing tool to use for facility detail, latest-quarter statewide comparison, change over time, persistent multi-quarter patterns, and ownership/affiliation grouping. The suite also includes a public methodology page explaining sources, formulas, limitations, and audit coverage.

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

### Connecticut Nursing Home Staffing Explorer

- public-facing PBJ staffing prototype
- normalized local mock facility data from `data/nursing_home_staffing_mock.json`
- screening-level metrics, quarterly comparison table, and ombudsman follow-up questions
- includes Connecticut direct-care staffing comparison fields as PBJ-derived screening estimates, not compliance determinations
- supports selected-facility print summaries and five-quarter facility trend CSV exports

### Statewide Staffing Comparison

- public-facing latest-quarter Connecticut facility comparison table
- supports search, filters, sorting, facility drill-down links, filtered-view summary analytics, print reporting, filtered CSV export, and a copyable briefing summary
- uses PBJ-derived screening metrics and CT direct-care HPRD estimates from `data/nursing_home_staffing_ct.json`
- frames statewide rankings as review questions, not care-quality or compliance conclusions

### Staffing Change Over Time

- public-facing earliest-to-latest Connecticut PBJ staffing change explorer
- identifies CT direct-care HPRD estimate declines and improvements, CT 3.00 direct-care comparison point crossings, contract staffing increases, and RN HPRD decreases
- supports search, affiliation and ownership filters, facility trend drill-down links, printable current change views, current change table CSV export, and a copyable briefing summary
- treats missing endpoint-quarter rows as incomplete data rather than zero staffing values

### Persistent Staffing Patterns

- public-facing multi-quarter Connecticut PBJ staffing screening explorer
- identifies facilities repeatedly below the CT 3.00 direct-care comparison point, below the CT 0.84 licensed comparison point, below CMS case-mix comparison points, or at/above contract staffing thresholds
- supports minimum-quarter thresholds, quarter-by-quarter pattern strips, search, affiliation and ownership filters, complete-history filtering, facility trend drill-down links, printable current views, current persistent-pattern CSV export, and a copyable briefing summary
- treats missing PBJ rows and unavailable case-mix benchmark values as unavailable context rather than adverse findings

### Ownership & Staffing Explorer

- public-facing affiliation-level staffing view
- groups Connecticut facilities by CMS SNF Enrollment affiliation entity when available
- derives group averages and facility comparisons from `data/nursing_home_staffing_ct.json`
- includes a latest-quarter statewide affiliation comparison table and compact five-quarter affiliation pattern summary
- includes affiliation-level persistent staffing pattern summaries using the same modes and thresholds as the Persistent Staffing Patterns tool, with current-view CSV export, print reporting, and a copyable briefing summary
- summarizes latest-quarter CT direct-care HPRD estimates at the affiliation level
- frames ownership and staffing patterns as screening context, not legal or care-quality findings

### Staffing Data Methodology

- public-facing explanation of the Connecticut nursing home staffing data sources, HPRD formulas, PBJ row inclusion rules, CT direct-care comparison estimates, case-mix comparison points, CMS Care Compare rating context, individual claims-based quality measures, affiliation context, limitations, and audit validation
- includes public source references for CMS PBJ Daily Nurse Staffing, CMS Nursing Home Provider Information, CMS Nursing Home Data Dictionary, CMS Skilled Nursing Facility Enrollments, Connecticut Title 19 Sec. 19-13-D8t, and the Connecticut DPH amended 3.0 staffing implementation notice
- linked from the staffing-suite homepage overview and each staffing tool page
- emphasizes screening, comparison, and question-building use rather than formal compliance or care-quality conclusions

### Phase 9A-9B LTCOP Dashboard Design

- adds reusable Connecticut LTCOP dashboard styling in `Assets/ltcop-dashboard.css`
- uses the transparent color Connecticut LTCOP horizontal logo in `Assets/branding/ct-ltcop-logo-horizontal-color.png` as the primary masthead identity
- applies the branded white masthead, navy navigation, light dashboard background, analytic cards, screening badges, accessible star cards, disclosures, compact tables, and print-safe styling across the staffing-suite homepage, all five staffing tools, and the public methodology page
- keeps the design separate from CT.gov global masthead conventions while linking to the official CT LTCOP website

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
- metrics already precomputed offline, including total nurse HPRD, RN HPRD, LPN/LVN HPRD, nurse aide HPRD, contract staff percentage, CT direct-care HPRD estimates, and optional case-mix benchmark HPRD
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

When Provider Information is supplied, the generator also copies CMS case-mix staffing HPRD fields into the explorer's `benchmarks` object when available. The case-mix total nurse comparison point is imported from CMS Nursing Home Provider Information, not calculated by this project; the UI-calculated comparisons are the actual-minus-benchmark and percent-of-benchmark displays. These benchmark fields are contextual comparisons only; PBJ-calculated HPRD remains the actual staffing metric shown by the explorer.

Provider Information also supplies CMS Care Compare star-rating context when those columns are present, including overall, health inspection, staffing, quality-measure, long-stay QM, and short-stay QM ratings. The April 2026 Provider Information file used here does not include an RN Staffing Rating column, so that optional field is emitted as `null` and reported in `data_quality.provider_rating_missing_columns`. These ratings are imported context, not calculated by this project and not substitutes for PBJ HPRD metrics or Connecticut direct-care screening estimates.

Optionally add CMS Nursing Home Quality Measures Claims rows:

```bash
python scripts/build_nursing_home_staffing_ct.py --input-dir source_data/pbj --provider-info source_data/provider_info/NH_ProviderInfo_MonYYYY.csv --quality-measures-claims source_data/quality_measures/NH_QualityMsr_Claims_MonYYYY.csv --output data/nursing_home_staffing_ct.json
```

Quality Measures Claims adds facility-level `quality_measures_claims[]` rows by CCN, including measure code, description, resident type, adjusted/observed/expected scores, score footnotes, rating-use flags, measure period, and processing date. These are imported CMS Care Compare quality-measure context. They are not calculated by this project, are not staffing measures, and do not replace PBJ staffing metrics, CT direct-care screening estimates, survey findings, complaints, resident experience, or formal review.

The generator also emits Connecticut direct-care staffing comparison fields. Connecticut Title 19 Sec. 19-13-D8t sets nursing-staff requirements, and Connecticut DPH's amended 3.0 staffing implementation notice describes the 3.00 total nursing and nurse's aide HPRD and 0.84 licensed nursing HPRD comparison points used by this suite. The PBJ-derived screening formulas are:

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

The ownership view computes statewide affiliation comparisons in the browser from the generated export. Rankings use simple facility averages, keep small Connecticut groups visible, and are intended as staffing screening tables rather than chain quality or compliance determinations.

The two nursing home explorers support reciprocal drill-down links. Facility pages can link to an affiliation staffing summary with `?affiliation=` using the CMS SNF Enrollment affiliation entity ID when available, and ownership/affiliation rows link back to facility staffing details with `?ccn=`.

The ownership view also provides selected-affiliation reporting actions: a print-friendly affiliation staffing summary, a latest-quarter facility comparison CSV, and a five-quarter trend CSV. The affiliation persistence section adds current-view CSV export, focused print reporting, and a copyable briefing summary based on the selected pattern mode, threshold, data window, and current table sort. These outputs are generated client-side from the same static JSON and carry the same screening-use caveats.

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
