"""Build or dry-run a Connecticut Penalties / Enforcement preview.

Default behavior is validation-only: read the CMS Penalties source, validate
joins and derived fields, and print a summary. Use --write-testing-preview to
write an ignored preview under data/testing/. This script never writes the
public runtime file data/nursing_home_penalties_ct.json.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


SOURCE_DIR = Path("source_data/cms_enforcement")
STAFFING_PATH = Path("data/nursing_home_staffing_ct.json")
TESTING_OUTPUT_PATH = Path("data/testing/nursing_home_penalties_ct_preview.json")
RUNTIME_OUTPUT_PATH = Path("data/nursing_home_penalties_ct.json")

PENALTIES_PATTERN = "NH_Penalties_*.csv"

SOURCE_URL = (
    "https://data.cms.gov/provider-data/sites/default/files/resources/"
    "c671cdaa1461db5a685367690785fcb3_1778861763/"
    "NH_Penalties_May2026.csv"
)
CMS_DATASET_ID = "g6vv-u9sr"
SOURCE_NAME = "CMS Provider Data Catalog Penalties"
ACQUIRED_DATE = "2026-06-22"

REQUIRED_COLUMNS = [
    "CMS Certification Number (CCN)",
    "Provider Name",
    "Provider Address",
    "City/Town",
    "State",
    "ZIP Code",
    "Penalty Date",
    "Penalty Type",
    "Fine Amount",
    "Payment Denial Start Date",
    "Payment Denial Length in Days",
    "Location",
    "Processing Date",
]

GENERAL_REQUIRED_COLUMNS = [
    "CMS Certification Number (CCN)",
    "Provider Name",
    "Provider Address",
    "City/Town",
    "State",
    "ZIP Code",
    "Penalty Date",
    "Penalty Type",
    "Location",
    "Processing Date",
]

LIMITATIONS = [
    "Penalties/enforcement rows are official CMS enforcement records.",
    "Fine rows and payment-denial rows are different enforcement types.",
    "Fine amount is not a quality score.",
    "Penalty date, payment denial start date, and processing date are different fields.",
    "Facility-level totals require a defined time window.",
    "State-level totals require careful denominator labels.",
    "Duplicate source rows are flagged and preserved in this preview.",
    "This rolling CMS source is not complete lifetime enforcement history.",
]


def find_latest(pattern: str) -> Path:
    matches = sorted(SOURCE_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No {pattern} file found in {SOURCE_DIR.as_posix()}")
    return matches[-1]


def normalize_ccn(value: str) -> str:
    digits = "".join(ch for ch in str(value or "").strip() if ch.isdigit())
    return digits.zfill(6) if digits else ""


def parse_date(value: str, *, required: bool = False, field_name: str = "date") -> str | None:
    value = str(value or "").strip()
    if not value:
        if required:
            raise ValueError(f"Missing required {field_name}")
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Invalid {field_name}: {value}")


def parse_decimal(value: str, *, required: bool = False, field_name: str = "amount") -> Decimal | None:
    value = str(value or "").strip().replace(",", "").replace("$", "")
    if not value:
        if required:
            raise ValueError(f"Missing required {field_name}")
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid {field_name}: {value}") from exc


def parse_int(value: str, *, required: bool = False, field_name: str = "integer") -> int | None:
    value = str(value or "").strip().replace(",", "")
    if not value:
        if required:
            raise ValueError(f"Missing required {field_name}")
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}: {value}") from exc


def parse_source_month_year(source_path: Path) -> tuple[str, int]:
    stem = source_path.stem
    suffix = stem.rsplit("_", 1)[-1]
    month = "".join(ch for ch in suffix if ch.isalpha())
    year_text = "".join(ch for ch in suffix if ch.isdigit())
    if not month or not year_text:
        raise ValueError(f"Could not parse source month/year from {source_path.name}")
    return month, int(year_text)


def load_current_staffing_ccns() -> dict[str, str]:
    with STAFFING_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        normalize_ccn(row.get("ccn")): row.get("provider_name") or row.get("facility_name") or ""
        for row in data.get("facilities", [])
        if normalize_ccn(row.get("ccn"))
    }


def normalized_row_signature(row: dict[str, str], fieldnames: list[str]) -> str:
    return "\x1f".join(str(row.get(column, "")).strip() for column in fieldnames)


def source_row_hash(row: dict[str, str], fieldnames: list[str]) -> str:
    return hashlib.sha256(normalized_row_signature(row, fieldnames).encode("utf-8")).hexdigest()


def money_display(amount: Decimal | None) -> str | None:
    if amount is None:
        return None
    return f"${amount:,.2f}"


def json_number(amount: Decimal | None) -> float | None:
    if amount is None:
        return None
    return float(amount)


def enforcement_category(penalty_type: str) -> str:
    normalized = str(penalty_type or "").strip().lower()
    if normalized == "fine":
        return "fine"
    if normalized == "payment denial":
        return "payment_denial"
    return "other_or_unmapped"


def build_penalty_record(
    row: dict[str, str],
    fieldnames: list[str],
    signature_seen: Counter[str],
) -> dict[str, Any]:
    for column in GENERAL_REQUIRED_COLUMNS:
        if not str(row.get(column, "")).strip():
            raise ValueError(f"Missing required {column}")

    ccn = normalize_ccn(row.get("CMS Certification Number (CCN)", ""))
    provider_name = str(row.get("Provider Name", "")).strip()
    provider_address = str(row.get("Provider Address", "")).strip()
    city = str(row.get("City/Town", "")).strip()
    state = str(row.get("State", "")).strip().upper()
    zip_code = str(row.get("ZIP Code", "")).strip()
    penalty_date = parse_date(row.get("Penalty Date", ""), required=True, field_name="Penalty Date")
    processing_date = parse_date(row.get("Processing Date", ""), required=True, field_name="Processing Date")
    penalty_type = str(row.get("Penalty Type", "")).strip()
    category = enforcement_category(penalty_type)

    if not ccn:
        raise ValueError("Missing required CCN")
    if state != "CT":
        raise ValueError(f"Unexpected state in CT build: {state}")

    fine_amount_raw = str(row.get("Fine Amount", "")).strip()
    denial_start_raw = str(row.get("Payment Denial Start Date", "")).strip()
    denial_length_raw = str(row.get("Payment Denial Length in Days", "")).strip()

    fine_amount = parse_decimal(
        fine_amount_raw,
        required=category == "fine",
        field_name="Fine Amount",
    )
    payment_denial_start_date = parse_date(
        denial_start_raw,
        required=category == "payment_denial",
        field_name="Payment Denial Start Date",
    )
    payment_denial_length_days = parse_int(
        denial_length_raw,
        required=category == "payment_denial",
        field_name="Payment Denial Length in Days",
    )

    if category == "fine" and (payment_denial_start_date or payment_denial_length_days is not None):
        raise ValueError(f"Fine row has payment denial fields for {ccn} on {penalty_date}")
    if category == "payment_denial" and fine_amount is not None:
        raise ValueError(f"Payment Denial row has Fine Amount for {ccn} on {penalty_date}")

    signature = normalized_row_signature(row, fieldnames)
    signature_seen[signature] += 1

    return {
        "ccn": ccn,
        "provider_name": provider_name,
        "provider_address": provider_address,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "penalty_date": penalty_date,
        "penalty_year": int(penalty_date[:4]),
        "penalty_type": penalty_type,
        "fine_amount": fine_amount_raw or None,
        "payment_denial_start_date": payment_denial_start_date,
        "payment_denial_length_days": payment_denial_length_days,
        "location": str(row.get("Location", "")).strip(),
        "processing_date": processing_date,
        "source_row_hash": source_row_hash(row, fieldnames),
        "duplicate_full_row_signature": signature_seen[signature] > 1,
        "enforcement_category": category,
        "has_fine": fine_amount is not None,
        "has_payment_denial": payment_denial_start_date is not None or payment_denial_length_days is not None,
        "normalized_fine_amount": json_number(fine_amount),
        "display_amount": money_display(fine_amount),
        "event_year": int(penalty_date[:4]),
    }


def build_preview() -> tuple[dict[str, Any], dict[str, Any]]:
    penalties_path = find_latest(PENALTIES_PATTERN)
    staffing_ccns = load_current_staffing_ccns()
    source_month, source_year = parse_source_month_year(penalties_path)

    source_row_count = 0
    penalties: list[dict[str, Any]] = []
    ct_ccns: set[str] = set()
    signature_seen: Counter[str] = Counter()

    with penalties_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        for row in reader:
            source_row_count += 1
            if str(row.get("State", "")).strip().upper() != "CT":
                continue
            record = build_penalty_record(row, fieldnames, signature_seen)
            penalties.append(record)
            ct_ccns.add(record["ccn"])

    unmatched_ccns = sorted(ct_ccns.difference(staffing_ccns))
    if unmatched_ccns:
        sample = ", ".join(unmatched_ccns[:10])
        raise ValueError(f"Unmatched CT penalty/enforcement CCNs: {sample}")

    penalty_dates = [record["penalty_date"] for record in penalties if record["penalty_date"]]
    processing_dates = [record["processing_date"] for record in penalties if record["processing_date"]]
    denial_dates = [
        record["payment_denial_start_date"]
        for record in penalties
        if record["payment_denial_start_date"]
    ]
    penalty_type_counts = Counter(record["penalty_type"] for record in penalties)
    category_counts = Counter(record["enforcement_category"] for record in penalties)
    duplicate_count = sum(1 for record in penalties if record["duplicate_full_row_signature"])
    fine_amounts = [
        Decimal(str(record["normalized_fine_amount"]))
        for record in penalties
        if record["normalized_fine_amount"] is not None
    ]
    payment_denial_lengths = [
        record["payment_denial_length_days"]
        for record in penalties
        if record["payment_denial_length_days"] is not None
    ]

    total_fine_amount = sum(fine_amounts, Decimal("0")) if fine_amounts else Decimal("0")
    total_denial_days = sum(payment_denial_lengths)

    metadata = {
        "source_name": SOURCE_NAME,
        "source_file": penalties_path.name,
        "source_url_or_endpoint": SOURCE_URL,
        "cms_dataset_id": CMS_DATASET_ID,
        "source_month": source_month,
        "source_year": source_year,
        "acquired_date": ACQUIRED_DATE,
        "build_date": datetime.now().date().isoformat(),
        "state_filter": "CT",
        "source_row_count": source_row_count,
        "ct_row_count": len(penalties),
        "unique_ct_ccn_count": len(ct_ccns),
        "joined_current_ccn_count": len(ct_ccns),
        "unmatched_current_ccn_count": 0,
        "duplicate_full_row_signature_count": duplicate_count,
        "penalty_date_min": min(penalty_dates) if penalty_dates else None,
        "penalty_date_max": max(penalty_dates) if penalty_dates else None,
        "processing_date_min": min(processing_dates) if processing_dates else None,
        "processing_date_max": max(processing_dates) if processing_dates else None,
        "payment_denial_start_date_min": min(denial_dates) if denial_dates else None,
        "payment_denial_start_date_max": max(denial_dates) if denial_dates else None,
        "fine_row_count": category_counts["fine"],
        "payment_denial_row_count": category_counts["payment_denial"],
        "ct_fine_amount_total": json_number(total_fine_amount),
        "payment_denial_length_total_days": total_denial_days,
        "limitations": LIMITATIONS,
    }

    preview = {
        "metadata": metadata,
        "penalties": penalties,
    }

    summary = {
        "source_file": penalties_path.as_posix(),
        "source_file_size_bytes": penalties_path.stat().st_size,
        "source_row_count": source_row_count,
        "ct_row_count": len(penalties),
        "unique_ct_ccn_count": len(ct_ccns),
        "current_staffing_ccn_count": len(staffing_ccns),
        "joined_current_ccn_count": len(ct_ccns),
        "unmatched_current_ccn_count": 0,
        "duplicate_full_row_signature_count": duplicate_count,
        "penalty_date_min": metadata["penalty_date_min"],
        "penalty_date_max": metadata["penalty_date_max"],
        "processing_date_min": metadata["processing_date_min"],
        "processing_date_max": metadata["processing_date_max"],
        "payment_denial_start_date_min": metadata["payment_denial_start_date_min"],
        "payment_denial_start_date_max": metadata["payment_denial_start_date_max"],
        "penalty_type_counts": dict(sorted(penalty_type_counts.items())),
        "enforcement_category_counts": dict(sorted(category_counts.items())),
        "fine_amount_rows": len(fine_amounts),
        "ct_fine_amount_total": f"{total_fine_amount:.2f}",
        "payment_denial_length_rows": len(payment_denial_lengths),
        "payment_denial_length_total_days": total_denial_days,
    }
    return preview, summary


def write_testing_preview(preview: dict[str, Any]) -> None:
    if RUNTIME_OUTPUT_PATH.exists():
        raise RuntimeError(
            f"Refusing to continue because runtime output exists: {RUNTIME_OUTPUT_PATH.as_posix()}"
        )
    TESTING_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TESTING_OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(preview, handle, indent=2)
        handle.write("\n")


def print_summary(summary: dict[str, Any], *, wrote_preview: bool) -> None:
    print(f"Source file: {summary['source_file']}")
    print(f"Source file size bytes: {summary['source_file_size_bytes']}")
    print(f"All source rows: {summary['source_row_count']}")
    print(f"Connecticut rows: {summary['ct_row_count']}")
    print(f"Unique CT CCNs: {summary['unique_ct_ccn_count']}")
    print(f"Current staffing CCNs: {summary['current_staffing_ccn_count']}")
    print(f"Joined CT penalty/enforcement CCNs to current staffing: {summary['joined_current_ccn_count']}")
    print(f"Unmatched CT penalty/enforcement CCNs: {summary['unmatched_current_ccn_count']}")
    print(f"Duplicate CT full-row signatures: {summary['duplicate_full_row_signature_count']}")
    print(f"Penalty date min: {summary['penalty_date_min']}")
    print(f"Penalty date max: {summary['penalty_date_max']}")
    print(f"Processing date min: {summary['processing_date_min']}")
    print(f"Processing date max: {summary['processing_date_max']}")
    print(f"Payment denial start date min: {summary['payment_denial_start_date_min']}")
    print(f"Payment denial start date max: {summary['payment_denial_start_date_max']}")
    print("Penalty type counts:")
    for value, count in summary["penalty_type_counts"].items():
        print(f"  {value}: {count}")
    print("Enforcement category counts:")
    for value, count in summary["enforcement_category_counts"].items():
        print(f"  {value}: {count}")
    print(f"Fine amount rows: {summary['fine_amount_rows']}")
    print(f"CT fine amount total: {summary['ct_fine_amount_total']}")
    print(f"Payment denial length rows: {summary['payment_denial_length_rows']}")
    print(f"Payment denial length total days: {summary['payment_denial_length_total_days']}")
    if wrote_preview:
        print(f"Testing preview written: {TESTING_OUTPUT_PATH.as_posix()}")
    else:
        print("Testing preview written: no")
    print(f"Runtime output written: no ({RUNTIME_OUTPUT_PATH.as_posix()} is never written by this script)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-testing-preview",
        action="store_true",
        help=f"Write ignored testing preview to {TESTING_OUTPUT_PATH.as_posix()}",
    )
    args = parser.parse_args()

    preview, summary = build_preview()
    if args.write_testing_preview:
        write_testing_preview(preview)
    print_summary(summary, wrote_preview=args.write_testing_preview)


if __name__ == "__main__":
    main()
