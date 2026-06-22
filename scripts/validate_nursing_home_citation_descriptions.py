"""Validate the CMS nursing home Citation Code Look-up source file.

This script reads the raw CMS source CSV only. It does not write runtime JSON
or alter application data.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


SOURCE_DIR = Path("source_data/cms_survey")
REQUIRED_COLUMNS = [
    "Deficiency Prefix",
    "Deficiency Tag Number",
    "Deficiency Prefix and Number",
    "Deficiency Description",
    "Deficiency Category",
]


def find_source_file() -> Path:
    matches = sorted(SOURCE_DIR.glob("NH_CitationDescriptions_*.csv"))
    if not matches:
        raise FileNotFoundError(
            "No NH_CitationDescriptions_<MonthYear>.csv file found in "
            f"{SOURCE_DIR.as_posix()}"
        )
    if len(matches) > 1:
        print("Multiple citation description files found; validating latest by name:")
        for path in matches:
            print(f"  - {path.as_posix()}")
    return matches[-1]


def main() -> None:
    source_path = find_source_file()
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    key_field = "Deficiency Prefix and Number"
    keys = [row.get(key_field, "").strip() for row in rows]
    prefix_counts = Counter(row.get("Deficiency Prefix", "").strip() for row in rows)
    category_counts = Counter(row.get("Deficiency Category", "").strip() for row in rows)
    duplicate_key_count = len(keys) - len(set(keys))
    missing_key_count = sum(1 for key in keys if not key)
    missing_description_count = sum(
        1 for row in rows if not row.get("Deficiency Description", "").strip()
    )
    missing_category_count = sum(
        1 for row in rows if not row.get("Deficiency Category", "").strip()
    )

    print(f"Source file: {source_path.as_posix()}")
    print(f"Columns ({len(fieldnames)}): {', '.join(fieldnames)}")
    print(f"Row count: {len(rows)}")
    print(f"Missing required columns: {len(missing_columns)}")
    if missing_columns:
        print(f"  {', '.join(missing_columns)}")
    print(f"Missing {key_field}: {missing_key_count}")
    print(f"Duplicate {key_field}: {duplicate_key_count}")
    print(f"Missing descriptions: {missing_description_count}")
    print(f"Missing categories: {missing_category_count}")
    print("Prefix counts:")
    for prefix, count in sorted(prefix_counts.items()):
        label = prefix or "(blank)"
        print(f"  {label}: {count}")
    print("Category counts:")
    for category, count in sorted(category_counts.items()):
        label = category or "(blank)"
        print(f"  {label}: {count}")

    if missing_columns or missing_key_count or duplicate_key_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
