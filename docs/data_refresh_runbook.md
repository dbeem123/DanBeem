# Data refresh runbook

How the staffing tools stay current. The list of sources, how often each publisher updates it, and where it
comes from is in `data/data_sources.json`; the methodology page shows the same table
("Where the data comes from and how often it is updated", written by `scripts/build_data_sources_section.py`).

## The three tools

| Command | Network | What it does |
|---|---|---|
| `python scripts/validate_data_freshness.py` | none | Reads the published data files, prints each source's version on the site and whether it is past its age limit. Part of the release gate (warns, exit 0; `--strict` exits 1). |
| `python scripts/refresh/refresh_sources.py check --out <dir>` | data.cms.gov, data.ct.gov | Asks each publisher for its latest release and compares it with the site: NEW, CURRENT, MANUAL or ERROR. Writes `<dir>/refresh_check.json`. |
| `python scripts/refresh/refresh_sources.py fetch --out <dir>` | same | Downloads every NEW release into `<dir>/<source id>/`, keeps a Connecticut-only copy of national files, records URL, size and SHA-256 in `<dir>/fetch_manifest.json`. |

`check` and `fetch` need the session's network to allow `data.cms.gov` and `data.ct.gov` (in claude.ai:
Settings > Capabilities, allowed domains). The DSS cost reports and the DPH eLicense rosters are manual
downloads; `check` lists them as MANUAL with the page to use.

## Schedule

| When | What |
|---|---|
| Monthly (first week) | `check`. Care Compare files (Provider Information, Quality Measures, Ownership, Health and Fire Safety Deficiencies, Citation Look-up, Penalties) and SNF All Owners refresh monthly. |
| Quarterly | PBJ adds a quarter about every three months; SNF Change of Ownership is every three months; DPH rosters and the data.ct.gov license file are pulled with them. SNF Enrollments is refreshed here too (monthly at CMS, but affiliations change slowly). |
| Each spring (March to May) | DSS cost reports for the cost year that ended the previous September 30 (due to DSS before February 15). |

A refresh only goes live through the usual Codex handoff (patch, release gate, push). Nothing here publishes.

## Where downloads go

The container is temporary. After `fetch`, copy each source's files to Daniel's computer with the device
bridge, into the folder the builds read:

| Source id | Folder on Daniel's computer | Then |
|---|---|---|
| cms_pbj | `source_data\pbj\` (current quarters) and `source_data\pbj\historical\YYYY\` | staffing + history build |
| cms_provider_info | `source_data\provider_info\` | staffing build |
| cms_quality_claims | `source_data\quality_measures\` | staffing build |
| cms_snf_enrollments | `source_data\snf_enrollments\` | staffing build |
| cms_health_deficiencies, cms_fire_safety_deficiencies, cms_citation_lookup | `source_data\cms_survey\` | survey/enforcement build |
| cms_penalties | `source_data\cms_enforcement\` | survey/enforcement build |
| cms_ownership | `X:\DanBeem-Data\Ownership\` | management companies build |
| cms_snf_all_owners | `X:\DanBeem-Data\Ownership\Skilled Nursing Facility All Owners\` | cost reports build |
| cms_snf_chow | `X:\DanBeem-Data\Skilled Nursing Facility Change of Ownership\` | cost reports build |
| ct_dss_cost_reports | `X:\DanBeem-Data\Cost_Reports\` | cost reports pipeline |
| ct_dph_rosters, ct_licenses | `source_data\ct_dph\` | administrators + management companies builds |

`source_data\` is in Daniel's main checkout (`GitHub--DanBeem`), which is git-ignored there. Only Claude
writes new files into it, and only new dated files; nothing existing is overwritten or deleted. Codex
never touches the main checkout.

## What the November 2026 refresh did (use as the pattern)

- Downloads were kept in `X:\DanBeem-Data\CMS_Refresh\YYYY-MM\` with the fetch manifests (URL, size, SHA-256).
  Large national files (over about 100 MB) don't copy back to the PC through the bridge; their Connecticut copies
  do, and the manifest records the national file's URL and hash.
- The PBJ history build needs every quarter since 2017Q4. Connecticut-only copies of the PC's PBJ archive were
  made on the PC with `X:\DanBeem-Data\_pbj_ct_extract\make_ct.py` (same file names, about 30 MB in all) and
  staged into the build workspace. The builders filter to Connecticut, so CT-only inputs give identical output
  (checked: rebuilding with the old inputs reproduced the published files exactly).
- The current staffing file covers the latest six PBJ quarters: copy those six into `source_data/pbj_window/`
  and pass `--input-dir source_data/pbj_window`.
- Inspection builders (health, fire safety, penalties) need the national files, because they record the source's
  national row count and size. Their `SOURCE_URL` and `ACQUIRED_DATE` constants are updated by hand for each
  release, and `scripts/audit_nursing_home_survey_enforcement_release.py` has an `EXPECTED` block pinned to the
  release; update it from the new build's numbers after checking they make sense. Builders and validators now pick
  the newest file by release month in its name (`scripts/cms_release_order.py`), not alphabetically.
- Dated text to update with each release: the methodology page (PBJ range, Care Compare month, inspection files,
  dates and coverage counts), the tools home PBJ range, the Ownership / Affiliation five-quarter range, the source
  manifest and tool registry, the legislative tracker's denominators note, and the pinned values in
  `scripts/test_website_presentation.js`, `scripts/test_build_nursing_home_ct_statewide_context.py` and
  `scripts/test_ct_legislative_tracker.py`.
- If many homes are missing from the newest PBJ quarter, the site says so: the Facility Explorer shows CMS's
  staffing footnote (23 = did not submit staffing data), and the CT rules page and legislative stats warn that the
  quarter's counts aren't comparable with earlier quarters.

## Builds per source

Run in the build workspace (`/home/claude/site` on branch `cost-reports`, or a fresh worktree from main).
Copy in only the files the build needs (CT-only copies where they exist).

- **PBJ, Provider Information, Quality Measures, SNF Enrollments** (one build reads all four):
  `python scripts/build_nursing_home_staffing_ct.py --input-dir source_data/pbj --provider-info source_data/provider_info/NH_ProviderInfo_MonYYYY.csv --snf-enrollments source_data/snf_enrollments/SNF_Enrollments_YYYY.MM.DD.csv --quality-measures-claims source_data/quality_measures/NH_QualityMsr_Claims_MonYYYY.csv --output data/nursing_home_staffing_ct.json`
  For a new PBJ quarter also `python scripts/build_nursing_home_staffing_history_ct.py --end-quarter YYYYQn --source-release "CMS PBJ Daily Nurse Staffing historical archive, 2017Q4-YYYYQn"`,
  then `python scripts/build_nursing_home_ct_statewide_context.py`. Audit with
  `python scripts/audit_nursing_home_staffing_ct.py` and `python scripts/audit_nursing_home_staffing_history_ct.py`.
- **Deficiencies, citation look-up, penalties:** follow `docs/nursing_home_survey_enforcement_monthly_refresh_runbook.md`
  (validate, build with `--write-runtime`, summary, facility details, then `audit_nursing_home_survey_enforcement_release.py`).
- **Ownership (management companies):** `docs/nursing_home_management_companies_runbook.md`.
- **SNF All Owners, CHOW, DSS cost reports:** `docs/nursing_home_cost_reports_runbook.md`; the cost report
  build also picks up new PBJ quarters, management and administrator data, so rerun
  `python scripts/build_ct_cost_reports.py` after any of those.
- **DPH rosters and license status:** `docs/nursing_home_administrator_search_runbook.md`, then the
  management companies build.

After any build: `python scripts/validate_data_freshness.py` (the refreshed sources should read OK), the
full release gate, and the browser test twice. Then a Codex handoff as usual.

## Checks before publishing a refresh

- Row counts: compare CT facility counts and row counts with the previous build; a drop of more than a few
  homes needs an explanation (closure, CCN change) before publishing.
- Validation rates (cost reports, administrators, management companies) should not fall.
- Column changes: if a CMS file's header differs from the last one, stop and adapt the build first.
- Keep every downloaded release; never overwrite an older file.

## Scheduled task prompt

Use this as the monthly scheduled task (first week of each month). It assumes the session can reach
data.cms.gov and data.ct.gov and is linked to Daniel's computer.

> Monthly data refresh for danbeem.xyz staffing tools. Follow docs/data_refresh_runbook.md in the DanBeem repo
> (build workspace /home/claude/site; if it is missing, clone dbeem123/danbeem read-only).
> 1. Run `python scripts/validate_data_freshness.py` and `python scripts/refresh/refresh_sources.py check --out <scratch>/refresh-YYYY-MM`.
> 2. If nothing is NEW and nothing is overdue, message Daniel one line ("Data check: all current") and stop.
> 3. Otherwise run `fetch` for the NEW sources, copy the files to Daniel's computer into the folders in the runbook
>    (new dated files only, never overwrite or delete), run the matching builds, then the freshness check, the full
>    release gate and the browser test twice.
> 4. Compare row counts and validation rates with the previous build. If anything drops unexpectedly or a file's
>    columns changed, stop and report instead of building.
> 5. Write one patch on top of origin/main with its SHA-256 and a Codex handoff in
>    BeemOps-Agent\STATUS\claude-handoff\data-refresh-YYYYMMDD\ (same format as the cost report handoffs), then
>    message Daniel: what was new, what changed on the site, and the paste-ready Codex prompt.
> Never push, never publish, never read .env or credential files. DSS cost reports (each spring) and DPH rosters
> (quarterly) are manual downloads: remind Daniel when they are due, with the page to use.
