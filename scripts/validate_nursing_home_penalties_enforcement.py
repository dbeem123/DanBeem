"""Validate the CMS nursing home Penalties / Enforcement source file.

This script reads ignored raw CMS source files from source_data/cms_enforcement
and prints validation results only. It does not write runtime JSON or alter app
data.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


SOURCE_DIR = Path("source_data/cms_enforcement")
STAFFING_PATH = Path("data/nursing_home_staffing_ct.json")
PENALTIES_PATTERN = "NH_Penalties_*.csv"

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


def find_latest(pattern: str) -> Path:
    matches = sorted(SOURCE_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No {pattern} file found in {SOURCE_DIR.as_posix()}")
    if len(matches) > 1:
        print(f"Multiple files match {pattern}; validating latest by filename:")
        for path in matches:
            print(f"  - {path.as_posix()}")
    return matches[-1]


def normalize_ccn(value: str) -> str:
    digits = "".join(ch for ch in str(value or "").strip() if ch.isdigit())
    return digits.zfill(6) if digits else ""


def parse_date(value: str) -> date | None:
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_decimal(value: str) -> Decimal | None:
    value = str(value or "").strip().replace(",", "").replace("$", "")
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_int(value: str) -> int | None:
    value = str(value or "").strip().replace(",", "")
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def money(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def load_current_staffing_ccns() -> dict[str, str]:
    with STAFFING_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        normalize_ccn(row.get("ccn")): row.get("provider_name") or row.get("facility_name") or ""
        for row in data.get("facilities", [])
        if normalize_ccn(row.get("ccn"))
    }


def main() -> None:
    source_path = find_latest(PENALTIES_PATTERN)
    source_size = source_path.stat().st_size
    staffing_ccns = load_current_staffing_ccns()

    all_rows = 0
    ct_rows = 0
    ct_ccns: dict[str, str] = {}
    missing_required_values = Counter()
    missing_penalty_dates = 0
    invalid_penalty_dates = 0
    min_penalty_date: date | None = None
    max_penalty_date: date | None = None
    penalty_year_counts = Counter()
    missing_processing_dates = 0
    invalid_processing_dates = 0
    processing_date_counts = Counter()
    missing_payment_denial_start_dates = 0
    invalid_payment_denial_start_dates = 0
    min_payment_denial_start_date: date | None = None
    max_payment_denial_start_date: date | None = None
    penalty_type_counts = Counter()
    fine_amounts: list[Decimal] = []
    missing_fine_amount_rows = 0
    invalid_fine_amount_rows = 0
    payment_denial_lengths: list[int] = []
    missing_payment_denial_length_rows = 0
    invalid_payment_denial_length_rows = 0
    row_signature_counts = Counter()

    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            raise SystemExit(f"Missing required columns: {', '.join(missing_columns)}")

        for row in reader:
            all_rows += 1
            if str(row.get("State", "")).strip().upper() != "CT":
                continue

            ct_rows += 1
            ccn = normalize_ccn(row.get("CMS Certification Number (CCN)"))
            provider_name = str(row.get("Provider Name", "")).strip()
            if ccn:
                ct_ccns.setdefault(ccn, provider_name)

            for column in REQUIRED_COLUMNS:
                if column in {
                    "Fine Amount",
                    "Payment Denial Start Date",
                    "Payment Denial Length in Days",
                }:
                    continue
                if not str(row.get(column, "")).strip():
                    missing_required_values[column] += 1

            penalty_date_raw = row.get("Penalty Date", "")
            if not str(penalty_date_raw or "").strip():
                missing_penalty_dates += 1
            else:
                parsed = parse_date(penalty_date_raw)
                if parsed is None:
                    invalid_penalty_dates += 1
                else:
                    min_penalty_date = parsed if min_penalty_date is None else min(min_penalty_date, parsed)
                    max_penalty_date = parsed if max_penalty_date is None else max(max_penalty_date, parsed)
                    penalty_year_counts[parsed.year] += 1

            processing_raw = row.get("Processing Date", "")
            if not str(processing_raw or "").strip():
                missing_processing_dates += 1
            else:
                parsed_processing = parse_date(processing_raw)
                if parsed_processing is None:
                    invalid_processing_dates += 1
                else:
                    processing_date_counts[parsed_processing.isoformat()] += 1

            penalty_type = str(row.get("Penalty Type", "")).strip() or "(blank)"
            penalty_type_counts[penalty_type] += 1

            fine_raw = row.get("Fine Amount", "")
            fine_amount = parse_decimal(fine_raw)
            if fine_amount is None:
                if str(fine_raw or "").strip():
                    invalid_fine_amount_rows += 1
                else:
                    missing_fine_amount_rows += 1
            else:
                fine_amounts.append(fine_amount)

            denial_start_raw = row.get("Payment Denial Start Date", "")
            if not str(denial_start_raw or "").strip():
                missing_payment_denial_start_dates += 1
            else:
                parsed_denial_start = parse_date(denial_start_raw)
                if parsed_denial_start is None:
                    invalid_payment_denial_start_dates += 1
                else:
                    min_payment_denial_start_date = (
                        parsed_denial_start
                        if min_payment_denial_start_date is None
                        else min(min_payment_denial_start_date, parsed_denial_start)
                    )
                    max_payment_denial_start_date = (
                        parsed_denial_start
                        if max_payment_denial_start_date is None
                        else max(max_payment_denial_start_date, parsed_denial_start)
                    )

            denial_length_raw = row.get("Payment Denial Length in Days", "")
            denial_length = parse_int(denial_length_raw)
            if denial_length is None:
                if str(denial_length_raw or "").strip():
                    invalid_payment_denial_length_rows += 1
                else:
                    missing_payment_denial_length_rows += 1
            else:
                payment_denial_lengths.append(denial_length)

            signature = tuple(str(row.get(column, "")).strip() for column in fieldnames)
            row_signature_counts[signature] += 1

    joined_ccns = sorted(set(ct_ccns).intersection(staffing_ccns))
    unmatched_ccns = sorted(set(ct_ccns).difference(staffing_ccns))
    duplicate_rows = sum(count - 1 for count in row_signature_counts.values() if count > 1)

    print(f"Source file: {source_path.as_posix()}")
    print(f"Source file size bytes: {source_size}")
    print(f"Columns ({len(fieldnames)}): {', '.join(fieldnames)}")
    print(f"All source rows: {all_rows}")
    print(f"Connecticut rows: {ct_rows}")
    print(f"Unique CT CCNs: {len(ct_ccns)}")
    print(f"Current staffing CCNs: {len(staffing_ccns)}")
    print(f"Joined CT penalty/enforcement CCNs to current staffing: {len(joined_ccns)}")
    print(f"Unmatched CT penalty/enforcement CCNs: {len(unmatched_ccns)}")
    print("Sample unmatched CT CCNs:")
    for ccn in unmatched_ccns[:15]:
        print(f"  {ccn}: {ct_ccns.get(ccn, '')}")
    print(f"Duplicate CT source rows by full-row signature: {duplicate_rows}")
    print(f"Missing penalty dates: {missing_penalty_dates}")
    print(f"Invalid penalty dates: {invalid_penalty_dates}")
    print(f"Penalty date min: {min_penalty_date.isoformat() if min_penalty_date else ''}")
    print(f"Penalty date max: {max_penalty_date.isoformat() if max_penalty_date else ''}")
    print("Penalty year counts:")
    for year, count in sorted(penalty_year_counts.items()):
        print(f"  {year}: {count}")
    print(f"Missing processing dates: {missing_processing_dates}")
    print(f"Invalid processing dates: {invalid_processing_dates}")
    print("Processing date counts:")
    for value, count in sorted(processing_date_counts.items()):
        print(f"  {value}: {count}")
    print(f"Missing payment denial start dates: {missing_payment_denial_start_dates}")
    print(f"Invalid payment denial start dates: {invalid_payment_denial_start_dates}")
    print(
        "Payment denial start date min: "
        f"{min_payment_denial_start_date.isoformat() if min_payment_denial_start_date else ''}"
    )
    print(
        "Payment denial start date max: "
        f"{max_payment_denial_start_date.isoformat() if max_payment_denial_start_date else ''}"
    )
    print("Penalty type counts:")
    for value, count in sorted(penalty_type_counts.items()):
        print(f"  {value}: {count}")
    print(f"Fine amount rows parsed: {len(fine_amounts)}")
    print(f"Missing fine amount rows: {missing_fine_amount_rows}")
    print(f"Invalid fine amount rows: {invalid_fine_amount_rows}")
    print(f"Fine amount min: {money(min(fine_amounts) if fine_amounts else None)}")
    print(f"Fine amount max: {money(max(fine_amounts) if fine_amounts else None)}")
    print(f"Fine amount total: {money(sum(fine_amounts, Decimal('0')) if fine_amounts else None)}")
    print(f"Payment denial length rows parsed: {len(payment_denial_lengths)}")
    print(f"Missing payment denial length rows: {missing_payment_denial_length_rows}")
    print(f"Invalid payment denial length rows: {invalid_payment_denial_length_rows}")
    print(f"Payment denial length min days: {min(payment_denial_lengths) if payment_denial_lengths else ''}")
    print(f"Payment denial length max days: {max(payment_denial_lengths) if payment_denial_lengths else ''}")
    print(f"Payment denial length total days: {sum(payment_denial_lengths) if payment_denial_lengths else ''}")
    print("Missing required values among CT rows:")
    for column in REQUIRED_COLUMNS:
        print(f"  {column}: {missing_required_values[column]}")


if __name__ == "__main__":
    main()
