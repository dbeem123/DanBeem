"""Build a non-runtime Connecticut nursing home facility geography crosswalk.

The output is a candidate geography crosswalk for future county/regional
features. It must not be treated as a runtime dependency until a later phase
explicitly wires it into public tools.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_INFO_PATH = ROOT / "source_data" / "provider_info" / "NH_ProviderInfo_Apr2026.csv"
CURRENT_PATH = ROOT / "data" / "nursing_home_staffing_ct.json"
HISTORY_PATH = ROOT / "data" / "nursing_home_staffing_history_ct.json"
OUTPUT_PATH = ROOT / "data" / "nursing_home_facility_geography_ct.json"
CONTRACT_PATH = ROOT / "docs" / "nursing_home_facility_geography_data_contract.md"
REVIEW_QUEUE_PATH = ROOT / "docs" / "nursing_home_facility_geography_manual_review_queue.md"


def clean(value: object) -> str:
    return str(value or "").strip()


def normalize_ccn(value: object) -> str:
    text = clean(value)
    return text.zfill(6) if text else ""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_provider_info_ct() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with PROVIDER_INFO_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if clean(row.get("State")).upper() != "CT":
                continue
            ccn = normalize_ccn(row.get("CMS Certification Number (CCN)"))
            if not ccn:
                continue
            rows[ccn] = {
                "ccn": ccn,
                "facility_name": clean(row.get("Provider Name")),
                "address": clean(row.get("Provider Address")),
                "city": clean(row.get("City/Town")),
                "state": clean(row.get("State")).upper(),
                "zip_code": clean(row.get("ZIP Code")),
                "county_name": clean(row.get("County/Parish")),
                "provider_ssa_county_code": clean(row.get("Provider SSA County Code")),
            }
    return rows


def load_current_facilities() -> dict[str, dict]:
    data = load_json(CURRENT_PATH)
    rows = {}
    for row in data.get("facilities", []):
        ccn = normalize_ccn(row.get("ccn"))
        if ccn:
            rows[ccn] = row
    return rows


def load_history_facilities() -> dict[str, dict]:
    data = load_json(HISTORY_PATH)
    rows = {}
    for row in data.get("facilities", []):
        ccn = normalize_ccn(row.get("ccn"))
        if ccn:
            rows[ccn] = row
    return rows


def choose_name(ccn: str, provider: dict | None, current: dict | None, history: dict | None) -> str:
    return (
        clean(provider.get("facility_name") if provider else "")
        or clean(current.get("provider_name") if current else "")
        or clean(current.get("provider_info_provider_name") if current else "")
        or clean(current.get("pbj_provider_name") if current else "")
        or clean(history.get("latest_pbj_provider_name") if history else "")
        or ccn
    )


def choose_city(provider: dict | None, current: dict | None, history: dict | None) -> str:
    return (
        clean(provider.get("city") if provider else "")
        or clean(current.get("city") if current else "")
        or clean(history.get("latest_pbj_city") if history else "")
    )


def build_record(ccn: str, provider: dict | None, current: dict | None, history: dict | None) -> dict:
    current_match = current is not None
    history_match = history is not None
    provider_match = provider is not None

    manual_review_required = False
    manual_review_reason = ""
    confidence = "high"
    match_method = "ccn_exact" if provider_match else "unmatched"
    notes = ""

    if not provider_match and current_match:
      manual_review_required = True
      confidence = "needs_review"
      manual_review_reason = "Current runtime CCN not found in April 2026 Provider Information."
    elif not provider_match and history_match:
      manual_review_required = True
      confidence = "needs_review"
      manual_review_reason = "Historical PBJ CCN not found in April 2026 Provider Information. May represent closed, changed, or otherwise non-current facility context."

    address = clean(provider.get("address") if provider else "") or clean(current.get("address") if current else "")
    city = choose_city(provider, current, history)
    state = clean(provider.get("state") if provider else "") or clean(current.get("state") if current else "") or clean(history.get("state") if history else "") or "CT"
    zip_code = clean(provider.get("zip_code") if provider else "") or clean(current.get("zip_code") if current else "")

    return {
        "ccn": ccn,
        "facility_name": choose_name(ccn, provider, current, history),
        "current_runtime_facility": current_match,
        "historical_pbj_facility": history_match,
        "provider_info_match": provider_match,
        "provider_info_source_file": "NH_ProviderInfo_Apr2026.csv" if provider_match else "",
        "provider_info_snapshot": "April 2026" if provider_match else "",
        "address": address,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "county_name": provider["county_name"] if provider_match else None,
        "provider_ssa_county_code": provider["provider_ssa_county_code"] if provider_match else None,
        "municipality": city or None,
        "ltcop_region": None,
        "aaa_region": None,
        "dph_region": None,
        "match_method": match_method,
        "confidence": confidence,
        "manual_review_required": manual_review_required,
        "manual_review_reason": manual_review_reason,
        "notes": notes,
    }


def write_contract() -> None:
    CONTRACT_PATH.write_text(
        """# Nursing Home Facility Geography Data Contract

Phase 11C.2 non-runtime data contract. This contract describes `data/nursing_home_facility_geography_ct.json`, a candidate Connecticut nursing home geography crosswalk for future county and regional comparison features.

## 1. Purpose

The geography crosswalk provides one CCN-keyed place to store current county context and future region assignments for Connecticut nursing home facilities. It is intended to support later county filters, facility-to-county comparison cards, and region-aware analysis after validation.

This file is not currently used by public runtime tools.

## 2. Source Files

- `source_data/provider_info/NH_ProviderInfo_Apr2026.csv`
- `data/nursing_home_staffing_ct.json`
- `data/nursing_home_staffing_history_ct.json`
- `docs/nursing_home_facility_geography_crosswalk_validation_report.md`

## 3. Key Field Definitions

- `ccn`: CMS Certification Number, normalized to six characters.
- `facility_name`: best available display name, preferring Provider Information when matched.
- `current_runtime_facility`: true when the CCN exists in `data/nursing_home_staffing_ct.json`.
- `historical_pbj_facility`: true when the CCN exists in `data/nursing_home_staffing_history_ct.json`.
- `provider_info_match`: true when the CCN matched April 2026 CMS Provider Information.
- `provider_info_source_file`: Provider Information source filename when matched.
- `provider_info_snapshot`: human-readable Provider Information snapshot period.
- `address`, `city`, `state`, `zip_code`: Provider Information location fields when matched; current runtime fallback where Provider Information is unavailable.
- `county_name`: CMS Provider Information `County/Parish`, populated only for exact Provider Information CCN matches.
- `provider_ssa_county_code`: CMS Provider Information `Provider SSA County Code`, preserved separately from any future county FIPS field.
- `municipality`: currently the same as the matched/fallback city value; future phases may normalize Connecticut town names.
- `ltcop_region`, `aaa_region`, `dph_region`: reserved fields. They remain null until validated region mappings are approved.
- `match_method`: `ccn_exact` for Provider Information exact CCN matches, otherwise `unmatched`.
- `confidence`: `high` for exact Provider Information CCN matches, `needs_review` for unmatched records.
- `manual_review_required`: true when county cannot be populated from Provider Information or another issue requires review.
- `manual_review_reason`: concise explanation for review.
- `notes`: reserved for future validation notes.

## 4. Match Methodology

The builder uses exact CCN matching only. It does not infer county from city, ZIP, address, name, coordinates, or any other field.

The record universe is the union of:

- all current runtime CCNs;
- all historical PBJ facility CCNs;
- all Connecticut Provider Information CCNs in the April 2026 file.

## 5. County Limitations

County values are current CMS Provider Information context from April 2026. They are not historical quarter-specific geography. If a facility moved, closed, reopened, changed CCN, or changed address over time, this crosswalk should not be treated as proof of historical county assignment for every PBJ quarter.

## 6. Manual Review Flags

Records require manual review when they are not found in April 2026 Provider Information. Current unmatched records may reflect facilities in the runtime staffing export that do not appear in the current Provider Information snapshot. Historical-only unmatched records may represent closed, changed, or otherwise non-current facility context.

Unresolved records should not be assigned a county by guesswork.

## 7. Current Snapshot Versus Historical PBJ Separation

Historical PBJ rows remain PBJ-only. This crosswalk can be joined by CCN later for analysis or display, but geography should not be embedded into the historical PBJ file unless a later phase explicitly approves a historically appropriate enrichment method.

## 8. Why Regional Fields Remain Null

LTCOP region, AAA region, and DPH region require validated source mappings. The builder does not infer region from county or municipality. Region fields remain null until official or project-approved mappings are documented.

## 9. Future Validation Needed Before Public County Filters

- review unmatched current runtime CCNs;
- review historical-only unmatched CCNs;
- confirm county labels and county-code semantics;
- decide whether to preserve county FIPS separately from Provider SSA county code;
- define refresh rules when Provider Information snapshots change;
- document how county filters should handle records with missing county;
- confirm public wording that county is current Provider Information context.

## 10. Future Refresh Process

On each Provider Information refresh:

1. archive the raw Provider Information file;
2. rerun the geography builder;
3. compare match counts, county completeness, manual-review counts, and county changes by CCN;
4. review any changed county, address, city, ZIP, or unmatched status before public use;
5. update the manual review queue.
""",
        encoding="utf-8",
    )


def markdown_table(rows: list[dict]) -> str:
    if not rows:
        return "None.\n"
    lines = [
        "| CCN | Facility name | Current runtime | Historical PBJ | City | Address | ZIP | Review reason |",
        "|---|---|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {ccn} | {facility_name} | {current} | {history} | {city} | {address} | {zip} | {reason} |".format(
                ccn=row["ccn"],
                facility_name=str(row["facility_name"]).replace("|", "\\|"),
                current="yes" if row["current_runtime_facility"] else "no",
                history="yes" if row["historical_pbj_facility"] else "no",
                city=str(row["city"] or "").replace("|", "\\|"),
                address=str(row["address"] or "").replace("|", "\\|"),
                zip=str(row["zip_code"] or "").replace("|", "\\|"),
                reason=str(row["manual_review_reason"] or "").replace("|", "\\|"),
            )
        )
    return "\n".join(lines) + "\n"


def write_review_queue(records: list[dict], stats: dict) -> None:
    current_unmatched = [row for row in records if row["current_runtime_facility"] and not row["provider_info_match"]]
    history_unmatched = [row for row in records if row["historical_pbj_facility"] and not row["provider_info_match"]]
    REVIEW_QUEUE_PATH.write_text(
        f"""# Nursing Home Facility Geography Manual Review Queue

Phase 11C.2 manual review queue. Do not assign counties or regions by guesswork.

## Summary

- Current runtime unmatched CCNs: {len(current_unmatched)}
- Historical PBJ unmatched CCNs: {len(history_unmatched)}
- Records requiring manual review: {stats["records_with_manual_review_required"]}

## Current Runtime CCNs Not Found In April 2026 Provider Information

These records exist in `data/nursing_home_staffing_ct.json` but did not match April 2026 Provider Information by CCN.

{markdown_table(current_unmatched)}

## Historical PBJ CCNs Not Found In April 2026 Provider Information

These records exist in `data/nursing_home_staffing_history_ct.json` but did not match April 2026 Provider Information by CCN. They may represent closed, changed, or otherwise non-current facility context.

{markdown_table(history_unmatched)}

## Recommended Next Steps

1. Check each unmatched CCN against archived Provider Information snapshots, CMS Care Compare history, and PBJ source files.
2. Determine whether the CCN reflects a closed facility, changed provider number, name/address mismatch, or another non-current status.
3. Do not populate county from city, ZIP, or address until a documented matching rule is approved.
4. Do not assign LTCOP, AAA, or DPH regions until a validated region mapping exists.
5. Preserve current snapshot versus historical PBJ separation in any later public feature.
""",
        encoding="utf-8",
    )


def main() -> None:
    provider = load_provider_info_ct()
    current = load_current_facilities()
    history = load_history_facilities()
    all_ccns = sorted(set(provider) | set(current) | set(history))
    records = [build_record(ccn, provider.get(ccn), current.get(ccn), history.get(ccn)) for ccn in all_ccns]

    ccn_counts = Counter(row["ccn"] for row in records if row["ccn"])
    duplicate_ccns = sorted(ccn for ccn, count in ccn_counts.items() if count > 1)
    missing_ccn_count = sum(1 for row in records if not row["ccn"])
    provider_matched = [row for row in records if row["provider_info_match"]]
    current_unmatched = [row for row in records if row["current_runtime_facility"] and not row["provider_info_match"]]
    history_unmatched = [row for row in records if row["historical_pbj_facility"] and not row["provider_info_match"]]
    manual_review = [row for row in records if row["manual_review_required"]]
    county_populated = [row for row in records if row["county_name"]]
    matched_missing_county = [row for row in provider_matched if not row["county_name"]]

    stats = {
        "total_crosswalk_records": len(records),
        "current_runtime_records_included": sum(1 for row in records if row["current_runtime_facility"]),
        "historical_pbj_records_included": sum(1 for row in records if row["historical_pbj_facility"]),
        "provider_information_matched_records": len(provider_matched),
        "current_runtime_unmatched_records": len(current_unmatched),
        "historical_pbj_unmatched_records": len(history_unmatched),
        "records_with_county_populated": len(county_populated),
        "records_with_manual_review_required": len(manual_review),
        "duplicate_ccns": duplicate_ccns,
        "missing_ccn_values": missing_ccn_count,
        "provider_information_matched_missing_county": len(matched_missing_county),
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "dataset_type": "ct_nursing_home_facility_geography_crosswalk_candidate",
                "publication_status": "non_runtime_candidate_not_used_by_public_tools",
                "generated_at": now_utc(),
                "sources": [
                    {
                        "source_dataset_name": "CMS Nursing Home Provider Information",
                        "source_release": "NH_ProviderInfo_Apr2026.csv",
                        "snapshot": "April 2026",
                        "path": str(PROVIDER_INFO_PATH.relative_to(ROOT)).replace("\\", "/"),
                    },
                    {
                        "source_dataset_name": "Current Connecticut nursing home staffing runtime export",
                        "path": str(CURRENT_PATH.relative_to(ROOT)).replace("\\", "/"),
                    },
                    {
                        "source_dataset_name": "Historical PBJ-only Connecticut nursing home staffing export",
                        "path": str(HISTORY_PATH.relative_to(ROOT)).replace("\\", "/"),
                    },
                ],
                "data_quality": stats,
                "facilities": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    write_contract()
    write_review_queue(records, stats)

    print(f"Total crosswalk records: {stats['total_crosswalk_records']}")
    print(f"Current runtime records included: {stats['current_runtime_records_included']}")
    print(f"Historical PBJ records included: {stats['historical_pbj_records_included']}")
    print(f"Provider Information matched records: {stats['provider_information_matched_records']}")
    print(f"Current runtime unmatched records: {stats['current_runtime_unmatched_records']}")
    print(f"Historical PBJ unmatched records: {stats['historical_pbj_unmatched_records']}")
    print(f"Records with county populated: {stats['records_with_county_populated']}")
    print(f"Records with manual review required: {stats['records_with_manual_review_required']}")
    print(f"Duplicate CCNs: {len(stats['duplicate_ccns'])}")
    print(f"Missing CCN values: {stats['missing_ccn_values']}")
    print(f"County missing among Provider Information matches: {stats['provider_information_matched_missing_county']}")
    print(f"Crosswalk written: {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Data contract written: {CONTRACT_PATH.relative_to(ROOT)}")
    print(f"Manual review queue written: {REVIEW_QUEUE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
