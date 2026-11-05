"""Extract Connecticut organization rows from the CMS ownership file in monthly Care Compare archives.

Usage: python scripts/extract_ct_ownership_orgs.py <out_dir> <nursing-homes_YYYY-MM-DD.zip> [...]

Writes <out_dir>/ct_org_ownership_<release>.csv. Keep the output under ignored data/testing/.
Individual owners and officers are dropped as rows are read; addresses and ZIP codes are never kept.
Handles both names CMS has used for the file: Ownership_Download.csv (to mid-2020) and NH_Ownership*.csv.
"""
from __future__ import annotations

import csv
import io
import re
import sys
import zipfile
from pathlib import Path

KEEP = ("ccn", "provider_name", "role", "owner_type", "owner_name", "pct", "association", "processing_date")
COLUMNS = {
    "ccn": ("CMS Certification Number (CCN)", "Federal Provider Number", "PROVNUM"),
    "provider_name": ("Provider Name", "PROVNAME"),
    "state": ("State", "Provider State", "STATE"),
    "role": ("Role played by Owner or Manager in Facility", "ROLE_DESC"),
    "owner_type": ("Owner Type", "OWNER_TYPE"),
    "owner_name": ("Owner Name", "OWNER_NAME"),
    "pct": ("Ownership Percentage", "OWNER_PERCENTAGE"),
    "association": ("Association Date", "ASSOCIATION_DATE"),
    "processing_date": ("Processing Date", "filedate"),
}
FILE_NAME = re.compile(r"(NH_?Ownership|^Ownership_Download)", re.I)


def column_map(fields: list[str]) -> dict[str, str]:
    lower = {f.strip().lower(): f for f in fields}
    found = {key: next((lower[n.lower()] for n in names if n.lower() in lower), None)
             for key, names in COLUMNS.items()}
    missing = [k for k, v in found.items() if v is None]
    if missing:
        raise ValueError(f"ownership file is missing columns: {missing}")
    return found


def extract(archive: Path) -> tuple[str, list[dict] | None]:
    release = re.search(r"(\d{4}-\d{2}-\d{2})\.zip$", archive.name).group(1)
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if FILE_NAME.search(n.split("/")[-1]) and n.lower().endswith(".csv")]
        if not names:
            return release, None
        with z.open(names[0]) as handle:
            reader = csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig", errors="replace"))
            m = column_map(reader.fieldnames or [])
            rows = []
            for row in reader:
                if (row[m["state"]] or "").strip().upper() != "CT":
                    continue
                if not (row[m["owner_type"]] or "").strip().lower().startswith("org"):
                    continue
                rows.append({k: (row[m[k]] or "").strip() for k in KEEP})
    return release, rows


def main(out_dir: Path, archives: list[Path]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for archive in archives:
        release, rows = extract(archive)
        if rows is None:
            print(release, "no ownership file (skipped)")
            continue
        with (out_dir / f"ct_org_ownership_{release}.csv").open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=KEEP)
            writer.writeheader()
            writer.writerows(rows)
        print(release, len(rows), "Connecticut organization rows")


if __name__ == "__main__":
    main(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])
