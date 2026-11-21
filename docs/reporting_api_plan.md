# CT Nursing Home Reporting API - architecture assessment and plan

Status: Phase A built on branch `claude/reporting-api-20261120` (2026-11-20). Not deployed until Daniel pushes.

## 1. What the site actually is (discovery)

- **Hosting:** GitHub Pages, custom domain `danbeem.xyz` (`CNAME`). Pure static files: HTML + vanilla JS + CSS. No server, no serverless functions, no database.
- **Deploy:** merge to `main` = live. One GitHub Action (`nursing-home-survey-enforcement-audit.yml`) runs audits only; it does not build the site.
- **Data pipeline:** offline Python scripts in `scripts/build_*.py` read CMS/DPH/DSS source files and write committed JSON to `/data`. Pages load `/data/*.json` in the browser. `AGENTS.md`: `/data` is the source of truth; do not duplicate it.
- **Datasets the API joins (all already public on the site):**

| Dataset | File | Key | Covers |
|---|---|---|---|
| Facility roster | `nursing_home_facility_roster_ct.json` | CCN | all 197 CCNs seen, status, closures |
| PBJ staffing (latest 6 qtrs) + facility metadata, CMS ratings, enrollment org | `nursing_home_staffing_ct.json` | CCN | 195 homes |
| PBJ staffing history | `nursing_home_staffing_history_ct.json` | CCN+quarter | 2017Q4-2026Q2 |
| Health citations, fire safety, penalties, survey summary | `nursing_home_health_deficiencies_ct.json`, `..._fire_safety_...`, `..._penalties_ct.json`, `..._survey_enforcement_summary_ct.json` | CCN | 2019-2026 |
| DSS cost reports, per home | `data/cost_reports/{ccn}.json` | CCN+cost year | 2015-2025: financials, direct care, support services, related parties, management services, owners on report, CMS owners (all releases), CHOW |
| Cost report insights | `ct_cost_report_insights.json` | CCN | statewide medians, bands |
| Management companies | `ct_nursing_home_management_companies.json` (+ aliases) | company id, CCN | CMS ownership archives 2020-2026 + DPH roster |
| Administrators | `ct_nursing_home_administrators.json` | license no., CCN | DPH 1997 onward |

## 2. Architecture decision

Because the host is static-only, the API is **precomputed at build time**:

```
/data/*.json  --scripts/build_reporting_api.py-->  /api/v1/**.json  (committed, served by GitHub Pages)
```

- One generator, no new data sources. Every API value is copied or calculated from `/data`, and every record carries the dataset file it came from.
- Deterministic: `generated_at` is the newest source build date, not the wall clock, so a rebuild with unchanged data produces identical files.
- GitHub Pages serves `.json` as `application/json` over HTTPS with `Access-Control-Allow-Origin: *`, so any AI tool or script can fetch it.
- Static hosting cannot read `?q=` or `?type=`. URLs therefore end in `.json` and put parameters in the path. Search runs client-side over a precomputed index. This is documented in `openapi.json`.
- Abuse resistance comes free: static files, CDN-cached, nothing to overload. No rate limiting is needed.

### URL map (Phase A)

| Spec name | Static URL |
|---|---|
| `GET /api/v1/reports` (catalog) | `/api/v1/index.json` |
| facility list | `/api/v1/facilities.json` |
| `/facilities/{ccn}/profile` | `/api/v1/facilities/{ccn}/profile.json` |
| `/facilities/{ccn}/ownership` | `/api/v1/facilities/{ccn}/ownership.json` |
| `/facilities/{ccn}/staffing` | `/api/v1/facilities/{ccn}/staffing.json` |
| `/facilities/{ccn}/financials` | `/api/v1/facilities/{ccn}/financials.json` |
| `/facilities/{ccn}/inspections` | `/api/v1/facilities/{ccn}/inspections.json` |
| `/management-companies` | `/api/v1/management-companies.json` |
| `/management-companies/{id}` | `/api/v1/management-companies/{id}.json` |
| `/search?q=` | `/api/v1/search-index.json` (client-side search) |
| `/reports?type=T&ccn=C` | `/api/v1/reports/{T}/{ccn}.json` |
| `management-company-portfolio` | `/api/v1/reports/management-company-portfolio/{id}.json` |
| `facility-comparison` | built in the browser from two facility reports (197x197 files would be wasteful) |
| OpenAPI 3.1 | `/api/openapi.json` |
| Docs | `/api/docs/` |
| AI overview | `/llms.txt`, `/llms-full.txt` |
| Report schema | `/api/v1/schema/report.schema.json` |

## 3. Evidence model (applies to every report)

Each finding has `kind`, one of:
- `confirmed_fact`: a value printed in a public source record (CMS row, DSS cost report line, DPH roster row).
- `calculated`: arithmetic on confirmed facts (per-resident-day costs, trends, shares). The formula is stated.
- `possible_association`: shared names, addresses or principals between entities. **Never** described as ownership, control or a conflict of interest.
- `investigative_question`: something the data cannot answer that a person should check.

Each finding has `evidence[]` with: source agency, dataset, URL, reporting period, as-of date, record id (CCN, cost-report page/line, CMS associate id, DPH license no.), and `verification` (`source_record` / `derived` / `name_match_unverified`).

Missing data is `null` plus an entry in `missing_data[]`. "No records found" is never written as "no problems."

## 4. Related-party screening (priority)

Built only from what the sources contain:
1. **Ownership/control (CMS All Owners):** owners, directors, officers, operational/managerial control, with association dates and release windows.
2. **Management (CMS + DPH):** management company periods.
3. **Cost-report disclosures (DSS):** related parties, amounts, page/line; management services and fees; legal name on report.
4. **Shared principals:** any person or organization in CMS ownership at this home **and** at other CT homes, listed as `possible_association` with both records.
5. **Reported but not in data:** names you supply (e.g. "Serene Health Services", "Adir Healthcare") are checked against every dataset. If they are absent, the report says so explicitly as an investigative question.

Cherry Brook (075396) is a test case. The data shows New Horizons Inc. as the legal entity (CMS enrollment and the DSS cost report) and a $288,000 management-services related-party line for 2025. Athena managed the home until 2025-03-26. **Serene and Adir do not appear in any current dataset**, so they are reported as unverified, never as confirmed.

## 5. "Ask your AI" buttons (Daniel's request)

On `/staffing/reports/`, each report has a set of preset questions. Each question has:
- **Open in ChatGPT:** `https://chatgpt.com/?q=<prompt>`
- **Open in Claude:** `https://claude.ai/new?q=<prompt>`
- **Copy prompt:** for Hermes or any other agent (paste into Discord, CLI, etc.)

The prompt contains the question, the public report URL(s), and the evidence rules: cite sources, label facts vs. calculations vs. associations, and do not invent missing values. The prompt carries URLs, not data, so it stays short. The user's AI needs web access turned on to fetch the URL. The page says so, and the copy option always works. These deep links are unofficial and could change. If one breaks, the copy button still works.

A later phase adds a "Send to Hermes" button, which needs a write endpoint and auth on Daniel's machine. It stays separate from the public read-only API.

## 6. Phases

- **Phase A (this branch):** generator; facility endpoints; management company endpoints; search index; report types facility-comprehensive, ownership-network, staffing-analysis, financial-transparency, regulatory-history, related-party-screening, management-company-portfolio; JSON Schema; OpenAPI; llms.txt; docs page; `/staffing/reports/` page with Ask-your-AI; tests.
- **Phase B:** facility-comparison in the browser; printable report view; Hermes client script (`scripts/hermes_reporting_client.py`); add the generator to `docs/data_refresh_runbook.md` so every data refresh rebuilds the API; GitHub Action that runs the API tests on PRs.
- **Phase C:** benchmarks by peer group (size/payer bands from insights); deeper entity resolution (address matching across cost reports and CMS, with manual review list like `ct_management_company_aliases.json`); vendor/contract records if a source is added; optional MCP server wrapping the same static files.

## 7. Guardrails

- Read-only, public data only. No ombudsman case data, no resident records.
- People appear only as they appear in public CMS/DPH/DSS records (name, role, dates). No addresses for individuals.
- Nothing is merged on name similarity. Entity ids are CCN, CMS associate id, DPH license no., or the site's management company id.
- Existing pages are not modified except for one nav link and one card linking to Reports.
