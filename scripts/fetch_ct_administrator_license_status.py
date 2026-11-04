"""Acquire only the five approved professional-license fields from CT Open Data.

This is an explicit network intake command, never part of the offline builder.
The snapshot is private input, not a public administrator-to-facility dataset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://data.ct.gov/resource/ngch-56tr.json"
FIELDS = ("name", "credentialnumber", "status", "issuedate", "expirationdate")
PAGE_SIZE = 1000
MAX_PAGES = 20


def fetch(opener=urlopen) -> dict:
    records = []
    unnumbered = 0
    for page in range(MAX_PAGES):
        query = {
            "$select": ",".join(FIELDS),
            "$where": "credentialtype = '36'",
            "$order": "credentialid",
            "$limit": str(PAGE_SIZE),
            "$offset": str(page * PAGE_SIZE),
        }
        with opener(ENDPOINT + "?" + urlencode(query), timeout=30) as response:
            body = response.read(4_000_001)
        if len(body) > 4_000_000:
            raise ValueError("License response exceeded the intake size limit")
        rows = json.loads(body)
        if not isinstance(rows, list) or len(rows) > PAGE_SIZE:
            raise ValueError("Unexpected license response shape")
        for row in rows:
            if not isinstance(row, dict) or set(row) - set(FIELDS):
                raise ValueError("License response contains an unrequested field")
            if any(not isinstance(value, str) for value in row.values()):
                raise ValueError("Invalid license record")
            if not row.get("credentialnumber", "").strip():
                # Applications without an issued number cannot validate a
                # tenure's license. Count, but never identify them by name.
                unnumbered += 1
                continue
            records.append({field: row.get(field, "") for field in FIELDS})
        if len(rows) < PAGE_SIZE:
            break
    else:
        raise ValueError("License pagination exceeded its bounded intake limit")
    if not records:
        raise ValueError("Empty license snapshot; do not treat it as no license matches")
    return {
        "schema_version": "ct-nha-license-crosscheck-1.0",
        "source_url": ENDPOINT,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "where": "credentialtype = '36'",
        "selected_fields": list(FIELDS),
        "unnumbered_records_excluded": unnumbered,
        "records": records,
    }


def save_snapshot(result: dict, output: Path) -> dict:
    private = (ROOT / "source_data" / "ct_dph").resolve()
    if not output.resolve().is_relative_to(private):
        raise ValueError("License intake must remain under ignored source_data/ct_dph")
    payload = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        handle.write(payload)
    return {"file": output.name, "rows": len(result["records"]),
            "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Refuse an unsafe/existing destination before making the network request.
    private = (ROOT / "source_data" / "ct_dph").resolve()
    if not args.output.resolve().is_relative_to(private) or args.output.exists():
        raise SystemExit("Refused: choose a NEW file under source_data/ct_dph")
    try:
        print(json.dumps(save_snapshot(fetch(), args.output)))
    except Exception as exc:
        # No source rows, HTTP bodies, identities or sensitive columns in errors.
        raise SystemExit(f"License intake failed ({type(exc).__name__}); no complete snapshot saved") from None


if __name__ == "__main__":
    main()
