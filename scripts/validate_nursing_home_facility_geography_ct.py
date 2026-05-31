"""Validate Connecticut nursing home geography fields for future crosswalk use.

This script is planning/validation only. It does not modify runtime staffing
exports or public tool behavior.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_INFO_PATH = ROOT / "source_data" / "provider_info" / "NH_ProviderInfo_Apr2026.csv"
CURRENT_RUNTIME_PATH = ROOT / "data" / "nursing_home_staffing_ct.json"
HISTORY_RUNTIME_PATH = ROOT / "data" / "nursing_home_staffing_history_ct.json"
REPORT_PATH = ROOT / "docs" / "nursing_home_facility_geography_crosswalk_validation_report.md"
PREVIEW_PATH = ROOT / "data" / "testing" / "nursing_home_facility_geography_ct_preview.json"


def normalize_ccn(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.zfill(6)


def clean(value: object) -> str:
    return str(value or "").strip()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_provider_info_ct(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if clean(row.get("State")).upper() != "CT":
                continue
            rows.append(
                {
                    "ccn": normalize_ccn(row.get("CMS Certification Number (CCN)")),
                    "facility_name": clean(row.get("Provider Name")),
                    "address": clean(row.get("Provider Address")),
                    "city": clean(row.get("City/Town")),
                    "state": clean(row.get("State")).upper(),
                    "zip_code": clean(row.get("ZIP Code")),
                    "provider_ssa_county_code": clean(row.get("Provider SSA County Code")),
                    "county_name": clean(row.get("County/Parish")),
                }
            )
    return rows


def index_by_ccn(rows: list[dict]) -> dict[str, list[dict]]:
    indexed: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        ccn = normalize_ccn(row.get("ccn"))
        if ccn:
            indexed[ccn].append(row)
    return dict(indexed)


def get_current_facilities() -> list[dict]:
    data = load_json(CURRENT_RUNTIME_PATH)
    return data.get("facilities", [])


def get_history_facilities() -> list[dict]:
    data = load_json(HISTORY_RUNTIME_PATH)
    return data.get("facilities", [])


def make_preview_rows(provider_rows: list[dict], current_ccns: set[str], history_ccns: set[str]) -> list[dict]:
    preview_rows = []
    for row in sorted(provider_rows, key=lambda item: (item["facility_name"], item["ccn"])):
        ccn = row["ccn"]
        notes = []
        if ccn not in current_ccns:
            notes.append("Provider Information CT facility is not present in current runtime staffing export.")
        if ccn not in history_ccns:
            notes.append("Provider Information CT facility is not present in historical PBJ facility directory.")
        if not row["county_name"]:
            notes.append("County/Parish is missing in Provider Information.")
        if not row["zip_code"]:
            notes.append("ZIP Code is missing in Provider Information.")
        if not row["address"]:
            notes.append("Provider Address is missing in Provider Information.")
        preview_rows.append(
            {
                "ccn": ccn,
                "facility_name": row["facility_name"],
                "address": row["address"],
                "city": row["city"],
                "state": row["state"],
                "zip_code": row["zip_code"],
                "county_name": row["county_name"],
                "provider_ssa_county_code": row["provider_ssa_county_code"],
                "municipality": row["city"],
                "ltcop_region": None,
                "aaa_region": None,
                "dph_region": None,
                "match_source": "CMS Provider Information April 2026",
                "match_method": "ccn_exact",
                "confidence": "high" if ccn in current_ccns or ccn in history_ccns else "review",
                "manual_review_required": bool(notes),
                "notes": " ".join(notes),
            }
        )
    return preview_rows


def markdown_list(items: list[str], empty_text: str = "None.") -> str:
    if not items:
        return empty_text
    return "\n".join(f"- `{item}`" for item in items)


def write_report(results: dict) -> None:
    provider_only = results["provider_only_current"]
    current_unmatched = results["current_unmatched"]
    history_unmatched = results["history_unmatched"]
    duplicate_provider_ccns = results["duplicate_provider_ccns"]
    inconsistent_counties = results["inconsistent_counties"]
    missing_county = results["missing_county"]
    missing_address = results["missing_address"]
    missing_zip = results["missing_zip"]

    report = f"""# Nursing Home Facility Geography Crosswalk Validation Report

Phase 11C.1 validation report. This report is non-runtime planning output. It does not change public tool behavior, generated staffing data, formulas, Connecticut applicability logic, or existing runtime JSON.

Generated: {results["generated_at"]}

## 1. Purpose

This validation checks whether CMS Provider Information county fields can safely support a future Connecticut nursing home facility geography crosswalk keyed by CMS Certification Number (CCN).

The intended future use is county-level and regional comparison planning, not immediate runtime enrichment. County values should remain current Provider Information context until a future geography crosswalk is approved and integrated.

## 2. Source Files Used

- Provider Information: `{PROVIDER_INFO_PATH.relative_to(ROOT)}`
- Current runtime staffing export: `{CURRENT_RUNTIME_PATH.relative_to(ROOT)}`
- Historical PBJ staffing export: `{HISTORY_RUNTIME_PATH.relative_to(ROOT)}`
- Optional testing preview JSON: `{PREVIEW_PATH.relative_to(ROOT)}`

## 3. Methodology

The script:

1. Read CMS Provider Information April 2026.
2. Filtered Provider Information rows to Connecticut facilities where `State` is `CT`.
3. Extracted CCN, provider name, address, city, state, ZIP, `Provider SSA County Code`, and `County/Parish`.
4. Compared Provider Information CT CCNs with current runtime CCNs in `data/nursing_home_staffing_ct.json`.
5. Compared Provider Information CT CCNs with historical PBJ facility-directory CCNs in `data/nursing_home_staffing_history_ct.json`.
6. Checked duplicate CCNs, county completeness, address/ZIP completeness, and inconsistent county values by CCN.
7. Wrote a testing-only preview crosswalk schema for review.

## 4. Match Results

| Check | Count |
|---|---:|
| Provider Information CT facilities | {results["provider_ct_count"]} |
| Provider Information unique CT CCNs | {results["provider_unique_ccn_count"]} |
| Current runtime facilities | {results["current_count"]} |
| Current runtime unique CCNs | {results["current_unique_ccn_count"]} |
| Historical PBJ unique CCNs | {results["history_unique_ccn_count"]} |
| Current runtime CCNs matched to Provider Information | {results["current_matched_count"]} |
| Current runtime CCNs unmatched to Provider Information | {len(current_unmatched)} |
| Provider Information CCNs not in current runtime | {len(provider_only)} |
| Historical PBJ CCNs matched to current Provider Information | {results["history_matched_count"]} |
| Historical PBJ CCNs not found in current Provider Information | {len(history_unmatched)} |
| Duplicate Provider Information CT CCNs | {len(duplicate_provider_ccns)} |
| Duplicate current runtime CCNs | {len(results["duplicate_current_ccns"])} |
| Duplicate historical PBJ facility CCNs | {len(results["duplicate_history_ccns"])} |

## 5. Unmatched and Review-Needed Records

### Current runtime CCNs unmatched to Provider Information

{markdown_list(current_unmatched)}

### Provider Information CT CCNs not in current runtime

{markdown_list(provider_only)}

### Historical PBJ CCNs not found in current Provider Information

{markdown_list(history_unmatched)}

### Duplicate Provider Information CT CCNs

{markdown_list(duplicate_provider_ccns)}

### Inconsistent county values by CCN

{markdown_list(inconsistent_counties)}

### Facilities missing County/Parish in Provider Information

Count: {len(missing_county)}

{markdown_list(missing_county[:50])}

### Facilities missing Provider Address in Provider Information

Count: {len(missing_address)}

{markdown_list(missing_address[:50])}

### Facilities missing ZIP Code in Provider Information

Count: {len(missing_zip)}

{markdown_list(missing_zip[:50])}

## 6. Proposed Future Geography Crosswalk Schema

The future approved crosswalk can use this row shape:

```json
{{
  "ccn": "075000",
  "facility_name": "",
  "address": "",
  "city": "",
  "state": "CT",
  "zip_code": "",
  "county_name": "",
  "provider_ssa_county_code": "",
  "municipality": "",
  "ltcop_region": null,
  "aaa_region": null,
  "dph_region": null,
  "match_source": "CMS Provider Information April 2026",
  "match_method": "ccn_exact",
  "confidence": "high",
  "manual_review_required": false,
  "notes": ""
}}
```

Important distinctions:

- County can likely come from CMS Provider Information.
- `Provider SSA County Code` should be preserved separately from any future county FIPS field.
- Municipality can initially use the Provider Information `City/Town` field, but it should be normalized before public grouping.
- LTCOP region, AAA region, and DPH region should remain null until a validated source or approved crosswalk exists.
- Regional assignments must not be invented or inferred from county unless a source-approved mapping is documented.

## 7. County Readiness Recommendation

CMS Provider Information county fields appear sufficient for initial county-level validation and likely sufficient for a future county filter or county comparison layer after a reviewed crosswalk is approved.

Recommended readiness status: **ready for non-runtime crosswalk design, not yet integrated into public runtime data**.

Reasons:

- Provider Information has county fields in the archived April 2026 source.
- CCN is the shared key across Provider Information and the current runtime export.
- Current runtime data has address, city, state, and ZIP for most facilities, which supports review and exception handling.
- County is not yet in the runtime data contract, and 5 current runtime records are missing address/ZIP.

## 8. Future Crosswalk Recommendation

A future `data/nursing_home_facility_geography_ct.json` should be created only after:

1. the geography data contract is documented;
2. Provider Information county values are reviewed;
3. unmatched historical-only CCNs are classified;
4. missing address/ZIP records are reviewed;
5. duplicate and inconsistent county checks remain clean or are resolved;
6. manual-review flags are included for any unresolved records.

The crosswalk should be the source of truth. Runtime exports can later be enriched from it if a public feature needs county or regional fields.

## 9. Recommended First Implementation After Validation

Recommended first public implementation after validation: **county filter on Statewide Comparison**.

Rationale:

- It is simpler than county aggregation cards.
- It does not require immediate decisions about simple averages, weighted averages, medians, or county rankings.
- It lets users scan facilities within a county using existing row-level metrics and guardrails.

Recommended second implementation: **facility county/state comparison cards** in the Facility Explorer dossier after aggregation methodology is documented.

## 10. Guardrails

- County is current Provider Information context unless historical county/address snapshots are added.
- Historical PBJ rows should remain PBJ-only.
- County can be joined by CCN for analysis but should not imply historical geographic continuity if a facility location changed.
- Regional mappings require separate validation.
- Do not invent LTCOP, AAA, or DPH region assignments.
- Do not infer regions from county unless a source-approved mapping is documented.
- County and regional comparisons are screening context, not findings.
- Do not change staffing formulas, CT applicability logic, generated staffing data, or public runtime behavior as part of geography validation.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    provider_rows = load_provider_info_ct(PROVIDER_INFO_PATH)
    current_facilities = get_current_facilities()
    history_facilities = get_history_facilities()

    provider_by_ccn = index_by_ccn(provider_rows)
    current_ccns = {normalize_ccn(row.get("ccn")) for row in current_facilities if normalize_ccn(row.get("ccn"))}
    history_ccns = {normalize_ccn(row.get("ccn")) for row in history_facilities if normalize_ccn(row.get("ccn"))}
    provider_ccns = set(provider_by_ccn)

    provider_counter = Counter(row["ccn"] for row in provider_rows if row["ccn"])
    current_counter = Counter(normalize_ccn(row.get("ccn")) for row in current_facilities if normalize_ccn(row.get("ccn")))
    history_counter = Counter(normalize_ccn(row.get("ccn")) for row in history_facilities if normalize_ccn(row.get("ccn")))

    county_values_by_ccn: dict[str, set[str]] = defaultdict(set)
    for row in provider_rows:
        if row["ccn"]:
            county_values_by_ccn[row["ccn"]].add(row["county_name"])

    inconsistent_counties = []
    for ccn, counties in county_values_by_ccn.items():
        nonblank = {county for county in counties if county}
        if len(nonblank) > 1:
            inconsistent_counties.append(f"{ccn}: {', '.join(sorted(nonblank))}")

    missing_county = [
        f"{row['ccn']} {row['facility_name']}".strip()
        for row in provider_rows
        if not row["county_name"]
    ]
    missing_address = [
        f"{row['ccn']} {row['facility_name']}".strip()
        for row in provider_rows
        if not row["address"]
    ]
    missing_zip = [
        f"{row['ccn']} {row['facility_name']}".strip()
        for row in provider_rows
        if not row["zip_code"]
    ]

    preview_rows = make_preview_rows(provider_rows, current_ccns, history_ccns)
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_PATH.write_text(
        json.dumps(
            {
                "schema_version": "preview",
                "dataset_type": "ct_nursing_home_facility_geography_crosswalk_preview",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "publication_status": "testing_preview_not_runtime",
                "sources": [
                    {
                        "source_dataset_name": "CMS Nursing Home Provider Information",
                        "source_release": "NH_ProviderInfo_Apr2026.csv",
                        "path": str(PROVIDER_INFO_PATH.relative_to(ROOT)).replace("\\", "/"),
                    }
                ],
                "data_quality": {
                    "provider_information_ct_facility_count": len(provider_rows),
                    "current_runtime_facility_count": len(current_facilities),
                    "historical_pbj_unique_ccn_count": len(history_ccns),
                    "current_runtime_match_count": len(current_ccns & provider_ccns),
                    "current_runtime_unmatched_count": len(current_ccns - provider_ccns),
                    "historical_pbj_match_count": len(history_ccns & provider_ccns),
                    "historical_pbj_unmatched_count": len(history_ccns - provider_ccns),
                    "missing_county_count": len(missing_county),
                    "missing_address_count": len(missing_address),
                    "missing_zip_count": len(missing_zip),
                    "duplicate_provider_info_ccn_count": sum(1 for count in provider_counter.values() if count > 1),
                    "inconsistent_county_ccn_count": len(inconsistent_counties),
                },
                "facilities": preview_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider_ct_count": len(provider_rows),
        "provider_unique_ccn_count": len(provider_ccns),
        "current_count": len(current_facilities),
        "current_unique_ccn_count": len(current_ccns),
        "history_unique_ccn_count": len(history_ccns),
        "current_matched_count": len(current_ccns & provider_ccns),
        "history_matched_count": len(history_ccns & provider_ccns),
        "current_unmatched": sorted(current_ccns - provider_ccns),
        "provider_only_current": sorted(provider_ccns - current_ccns),
        "history_unmatched": sorted(history_ccns - provider_ccns),
        "duplicate_provider_ccns": sorted(ccn for ccn, count in provider_counter.items() if count > 1),
        "duplicate_current_ccns": sorted(ccn for ccn, count in current_counter.items() if count > 1),
        "duplicate_history_ccns": sorted(ccn for ccn, count in history_counter.items() if count > 1),
        "inconsistent_counties": sorted(inconsistent_counties),
        "missing_county": sorted(missing_county),
        "missing_address": sorted(missing_address),
        "missing_zip": sorted(missing_zip),
    }
    write_report(results)

    print(f"Provider Information CT facilities: {results['provider_ct_count']}")
    print(f"Current runtime matched/unmatched: {results['current_matched_count']}/{len(results['current_unmatched'])}")
    print(f"Historical PBJ matched/unmatched: {results['history_matched_count']}/{len(results['history_unmatched'])}")
    print(f"Missing county/address/ZIP: {len(missing_county)}/{len(missing_address)}/{len(missing_zip)}")
    print(f"Report written: {REPORT_PATH.relative_to(ROOT)}")
    print(f"Preview written: {PREVIEW_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
