"""Check every data source for a newer release than the site has, and download the new ones.

  python scripts/refresh/refresh_sources.py check  --out <dir>             # what's new (no downloads)
  python scripts/refresh/refresh_sources.py fetch  --out <dir> [--only id,id] [--keep-full]

Reads data/data_sources.json. Needs network access to data.cms.gov and data.ct.gov.

check  writes <out>/refresh_check.json and prints one line per source: NEW, CURRENT, MANUAL or ERROR.
fetch  downloads each NEW source (or the ones named in --only) into <out>/<source id>/, writes a
       Connecticut-only copy of large national files (rows whose state column is CT), and records
       URL, size and SHA-256 in <out>/fetch_manifest.json. The national file is deleted afterwards
       unless --keep-full is given.

Nothing here builds or publishes; docs/data_refresh_runbook.md says which build to run for each source.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_data_freshness import on_site_versions, month_from_name  # noqa: E402

UA = "danbeem-data-refresh/1.0 (+https://danbeem.xyz)"
CMS_PDC_ITEM = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{id}?show-reference-ids=false"
CMS_CATALOG = "https://data.cms.gov/data.json"
SOCRATA_VIEW = "https://data.ct.gov/api/views/{id}.json"
STATE_COLUMNS = ("STATE", "State", "state", "PROVIDER_STATE", "Provider State", "STATE_CD", "ENRLMT_STATE",
                 "Enrollment State", "STATE - OWNER", "STATE - PROVIDER", "Provider State Code")
CT_ONLY = {"cms_pbj", "cms_health_deficiencies", "cms_fire_safety_deficiencies", "cms_penalties", "cms_ownership",
           "cms_provider_info", "cms_quality_claims", "cms_snf_enrollments", "cms_snf_all_owners", "cms_snf_chow"}


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


# ------------------------------------------------------------------ finding the latest release
def latest_pdc(item):
    """CMS Provider Data Catalog metastore item -> (version date, download URL, modified)."""
    dist = item.get("distribution") or []
    url = next((d.get("downloadURL") or (d.get("data") or {}).get("downloadURL") for d in dist
                if (d.get("downloadURL") or (d.get("data") or {}).get("downloadURL"))), None)
    return month_from_name(url or ""), url, item.get("modified"), item.get("nextUpdateDate")


def latest_catalog(catalog, title):
    """data.cms.gov data.json -> (version date, CSV download URL) for the newest CSV of the dataset titled `title`.
    The catalog lists each release as its own entry titled "<title> : YYYY-MM-DD"; older catalogs put every
    release in one entry's distributions. Both are handled."""
    best = (None, None)
    for ds in catalog.get("dataset", []):
        base, _, stamp = ds.get("title", "").partition(" : ")
        if base.strip().lower() != title.lower():
            continue
        for d in ds.get("distribution", []):
            url = d.get("downloadURL")
            if not url or not (d.get("mediaType") == "text/csv" or url.lower().endswith(".csv")):
                continue
            m = re.search(r":\s*(\d{4}-\d{2}-\d{2})", d.get("title", "")) or re.search(r"(\d{4}-\d{2}-\d{2})", stamp)
            when = dt.date.fromisoformat(m.group(1)) if m else month_from_name(url)
            if when and (best[0] is None or when > best[0]):
                best = (when, url)
    return best


def is_newer(source_id, kind, release, have):
    """True when the publisher's release is newer than the version on the site."""
    if release is None:
        return None
    if have is None:
        return True
    if kind == "quarter":
        # PBJ titles carry the quarter's first day ("... : 2026-04-01"); the site stores the quarter end (2026-03-31).
        return release > have
    if kind == "month":
        return (release.year, release.month) > (have.year, have.month)
    return release > have


def check(reg):
    have = on_site_versions()
    catalog = None
    rows = []
    for s in reg["sources"]:
        acc = s["access"]
        row = {"id": s["id"], "name": s["name"], "on_site": (have.get(s["id"]) or (None, None))[0]}
        try:
            if acc["type"] == "cms_provider_data":
                when, url, modified, nxt = latest_pdc(json.loads(get(CMS_PDC_ITEM.format(id=acc["dataset_id"]))))
                row.update(latest=when.isoformat() if when else None, url=url, modified=modified, next_update=nxt)
            elif acc["type"] == "cms_data_api":
                if catalog is None:
                    catalog = json.loads(get(CMS_CATALOG))
                when, url = latest_catalog(catalog, acc["dataset_title"])
                row.update(latest=when.isoformat() if when else None, url=url)
            elif acc["type"] == "socrata":
                v = json.loads(get(SOCRATA_VIEW.format(id=acc["view_id"])))
                when = dt.datetime.fromtimestamp(v["rowsUpdatedAt"], dt.timezone.utc).date()
                row.update(latest=when.isoformat(), url=s["page"], script=acc.get("script"))
            else:
                row.update(status="MANUAL", how=acc.get("how"), url=s["page"])
                rows.append(row)
                continue
            have_d = (have.get(s["id"]) or (None, None))[1]
            # a daily dataset counts as new once the site's copy is past its age limit
            if acc["type"] == "socrata":
                new = have_d is None or (dt.date.today() - have_d).days > s["max_age_days"]
            else:
                new = is_newer(s["id"], s["version_kind"], when, have_d)
            row["status"] = "NEW" if new else ("CURRENT" if new is False else "ERROR")
        except Exception as e:  # keep going; report the source as an error
            row.update(status="ERROR", error=repr(e)[:300])
        rows.append(row)
    return rows


# ------------------------------------------------------------------ downloading
def state_column(header):
    for c in STATE_COLUMNS:
        if c in header:
            return c
    return next((h for h in header if h.strip().upper() in ("STATE", "PROVIDER STATE")), None)


def ct_copy(src, dst):
    """Write rows whose state column is CT; returns (rows kept, column used) or (0, None) if no state column."""
    with open(src, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        header = next(rd)
        col = state_column(header)
        if not col:
            return 0, None
        i = header.index(col)
        n = 0
        with open(dst, "w", encoding="utf-8", newline="") as g:
            w = csv.writer(g)
            w.writerow(header)
            for row in rd:
                if len(row) > i and row[i].strip().upper() == "CT":
                    w.writerow(row)
                    n += 1
    return n, col


def download(url, dst):
    h = hashlib.sha256()
    size = 0
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(dst, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b); h.update(b); size += len(b)
    return size, h.hexdigest()


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fetch(rows, out, only=None, keep_full=False):
    manifest = []
    for r in rows:
        if only and r["id"] not in only:
            continue
        if not only and r.get("status") != "NEW":
            continue
        if not r.get("url") or r.get("status") == "MANUAL" or r.get("script"):
            manifest.append({"id": r["id"], "skipped": r.get("how") or r.get("script") or "no download URL"})
            continue
        d = out / r["id"]
        d.mkdir(parents=True, exist_ok=True)
        name = Path(urllib.request.urlparse(r["url"]).path).name or f"{r['id']}.csv"
        full = d / name
        size, digest = download(r["url"], full)
        entry = {"id": r["id"], "url": r["url"], "release": r.get("latest"), "file": str(full.relative_to(out)),
                 "bytes": size, "sha256": digest, "downloaded": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        if r["id"] in CT_ONLY and name.lower().endswith(".csv"):
            ct = d / (full.stem + "_CT.csv")
            n, col = ct_copy(full, ct)
            if col:
                entry.update(ct_file=str(ct.relative_to(out)), ct_rows=n, ct_state_column=col, ct_sha256=sha(ct))
                if not keep_full:
                    full.unlink()
                    entry["full_file_deleted"] = True
            else:
                ct.unlink(missing_ok=True)
                entry["ct_note"] = "no state column found; kept the full file"
        manifest.append(entry)
        print(f"fetched {r['id']}: {name} ({size:,} bytes)" + (f", {entry.get('ct_rows')} CT rows" if entry.get("ct_rows") is not None else ""))
    (out / "fetch_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("check", "fetch"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", help="comma-separated source ids to fetch even if not NEW")
    ap.add_argument("--keep-full", action="store_true", help="keep national files after writing the CT copy")
    a = ap.parse_args()
    reg = json.loads((ROOT / "data" / "data_sources.json").read_text(encoding="utf-8"))
    a.out.mkdir(parents=True, exist_ok=True)
    rows = check(reg)
    (a.out / "refresh_check.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    for r in rows:
        print(f"{r.get('status', '?'):8s} {r['id']:30s} site: {str(r.get('on_site'))[:34]:34s} latest: {r.get('latest') or ''} {r.get('error', '')}")
    new = [r["id"] for r in rows if r.get("status") == "NEW"]
    print(f"Refresh check: {len(new)} new release(s): {', '.join(new) or 'none'}; "
          f"{sum(r.get('status') == 'MANUAL' for r in rows)} manual; {sum(r.get('status') == 'ERROR' for r in rows)} error(s).")
    if a.action == "fetch":
        fetch(rows, a.out, set(a.only.split(",")) if a.only else None, a.keep_full)
    return 0


if __name__ == "__main__":
    sys.exit(main())
