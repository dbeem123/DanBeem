# Nursing Home Survey and Enforcement CI Release Gate

## Purpose

Phase 11D.22 adds a narrow GitHub Actions release gate for the committed Connecticut nursing home survey and enforcement feature. The gate reruns the Phase 11D.21 consistency audit and related regressions whenever a pull request or push changes an audited input, relevant builder, public integration file, or the workflow itself.

The workflow is read-only validation. It does not rebuild datasets, invoke a production-write option, commit, push, deploy, upload artifacts, or use repository secrets.

## Workflow

The workflow file is:

```text
.github/workflows/nursing-home-survey-enforcement-audit.yml
```

The workflow and job names exposed in GitHub are:

- workflow: **Nursing Home Survey Enforcement Audit**
- job/check: **Survey enforcement release gate**

The job uses `ubuntu-latest`, has a 10-minute timeout, and grants only `contents: read` permission. Checkout persistence is disabled because later steps do not perform Git writes.

## Trigger Conditions

The workflow runs for:

- pull requests targeting `main` when a filtered path changes;
- pushes to `main` when a filtered path changes; and
- manual `workflow_dispatch` runs, regardless of changed paths.

Concurrency groups runs by workflow and Git reference. A newer run on the same reference cancels an older in-progress run.

## Path Filters

The pull-request and push filters contain the same paths.

### Audit and Builder Logic

- `scripts/audit_nursing_home_survey_enforcement_release.py`
- `scripts/build_nursing_home_health_deficiencies_ct.py`
- `scripts/build_nursing_home_fire_safety_deficiencies_ct.py`
- `scripts/build_nursing_home_penalties_ct.py`
- `scripts/build_nursing_home_survey_enforcement_summary_ct.py`
- `scripts/build_nursing_home_survey_enforcement_facility_details_ct.py`
- `scripts/build_nursing_home_staffing_ct.py`
- `scripts/test_build_nursing_home_staffing_ct.py`

The staffing builder and test are included because the release audit derives its current 196-facility coverage from the committed staffing dataset and the CI job runs the staffing regression suite.

### Runtime and Metadata Inputs

- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_health_deficiencies_ct.json`
- `data/nursing_home_fire_safety_deficiencies_ct.json`
- `data/nursing_home_penalties_ct.json`
- `data/nursing_home_survey_enforcement_summary_ct.json`
- `data/nursing_home_survey_enforcement_details_ct/**`
- `data/nursing_home_source_manifest.json`
- `data/current_tool_context_registry.json`

The detail-directory glob is intentionally broad within that single generated directory. It catches index changes, changed CCN files, added facility files, and unexpected JSON files that the audit must reject.

### Public Implementation and Workflow

- `tools/nursing-home-staffing-explorer.html`
- `tools/nursing-home-staffing-methodology.html`
- `Assets/nursing-home-staffing.js`
- `Assets/ltcop-dashboard.css`
- `.github/workflows/nursing-home-survey-enforcement-audit.yml`

The CSS path is included because survey/enforcement disclosure and state styling share the dashboard stylesheet even though the static architecture audit primarily inspects HTML and JavaScript. The filters do not use broad `data/**`, `scripts/**`, `tools/**`, or repository-wide globs, so unrelated changes do not trigger this specialized gate.

## Runtime Setup

The job uses:

- `actions/checkout@v7`;
- `actions/setup-python@v6` with Python 3.13; and
- `actions/setup-node@v6` with Node.js 24.

Python 3.13 supports the audit script's language features, and Node.js 24 supplies the built-in `--check` syntax parser. No `pip`, `npm`, or other dependency installation runs because the audit and staffing tests use the Python standard library and JavaScript validation does not require a package.

## Checks Executed

The workflow fails immediately if any command exits nonzero. It runs:

```text
python --version
node --version
python -m py_compile scripts/audit_nursing_home_survey_enforcement_release.py
python scripts/audit_nursing_home_survey_enforcement_release.py
node --check Assets/nursing-home-staffing.js
python -m unittest scripts.test_build_nursing_home_staffing_ct
python -m json.tool data/nursing_home_source_manifest.json > /dev/null
python -m json.tool data/current_tool_context_registry.json > /dev/null
```

The normal audit mode prints one PASS or FAIL line per major section plus performance statistics and a concise release conclusion. CI does not also run `--verbose`, because the concise run contains the release decision and the verbose run would repeat the same full reconciliation with substantially more console output. Developers can use verbose mode locally when diagnosing a failure.

## Why Raw CMS Files Are Not Required

The release audit operates entirely on committed repository files. It parses the generated statewide runtime JSON, current staffing JSON, compact summary, detail index and CCN files, manifest, registry, methodology, and Facility Explorer implementation.

It does not read ignored `source_data` CMS CSV files and does not import or run a builder. Staffing tests use synthetic fixtures created by the test suite rather than production raw data. This makes pull requests from clean GitHub checkouts reproducible without private or ignored inputs.

## Failure Behavior

Any malformed JSON, missing file, incorrect expected total, CCN coverage drift, runtime/detail mismatch, summary mismatch, metadata or methodology inconsistency, loading-contract regression, JavaScript syntax error, or staffing-test failure exits nonzero and fails the job.

The audit collects multiple consistency failures where practical and prints expected and actual values. It never repairs a mismatch. A failed gate should be investigated by running the same command locally; assertions should not be weakened solely to obtain a passing result.

Python compilation and tests may create `__pycache__` files inside the disposable runner workspace. Nothing is committed or uploaded, and the workspace is destroyed after the job.

## Local Execution

From the repository root, run the release gate commands with:

```text
python -m py_compile scripts/audit_nursing_home_survey_enforcement_release.py
python scripts/audit_nursing_home_survey_enforcement_release.py
node --check Assets/nursing-home-staffing.js
python -m unittest scripts.test_build_nursing_home_staffing_ct
python -m json.tool data/nursing_home_source_manifest.json
python -m json.tool data/current_tool_context_registry.json
```

For detailed successful checks or failure diagnosis, run:

```text
python scripts/audit_nursing_home_survey_enforcement_release.py --verbose
```

Local Python cache changes should be restored or removed before committing.

## Manual Execution

In GitHub, open **Actions**, select **Nursing Home Survey Enforcement Audit**, choose **Run workflow**, select the desired branch, and confirm the run. Manual execution is useful after GitHub runner or action-version changes and for release validation when no filtered file changed.

## Known CI Limitations

- Static methodology and loading checks do not replace browser interaction, accessibility review, or network-panel inspection.
- CI validates committed generated artifacts but does not independently reacquire or validate the upstream CMS CSV files.
- Path-filtered workflows do not produce a check on pull requests that change only unrelated files. Branch protection should account for this GitHub behavior before making a path-filtered check universally required.
- `ubuntu-latest` and major action tags receive supported upstream updates. A manual run should be used after a significant runner or action change.
- The gate tests Python 3.13 and Node.js 24 on Linux; it does not create a cross-platform version matrix because the production artifacts are static and the audit uses portable standard-library operations.

## Branch-Protection Recommendation

Recommend, but do not configure, a `main` branch rule that requires **Survey enforcement release gate** before merging pull requests that affect the filtered survey/enforcement paths.

Because GitHub may leave a path-filtered required workflow absent or pending on unrelated pull requests, use a ruleset or required-check design that applies this requirement only when the workflow is expected to run. An alternative is a small always-running dispatcher check that reports success for irrelevant path sets and invokes this release gate for relevant changes. That broader branch-protection design should be implemented only in a separately reviewed phase.
