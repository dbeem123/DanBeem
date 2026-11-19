"""Fetch CT PBJ inputs from dated CMS endpoints. Employee identifiers exist only in memory."""
import argparse
import gzip
import json
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode


def request(url, params):
    raw = subprocess.check_output(["curl.exe", "--compressed", "-fsSL", "--retry", "2",
                                   "--max-time", "100", url + "?" + urlencode(params)])
    rows = json.loads(raw)
    if not isinstance(rows, list):
        raise ValueError("Unexpected CMS response")
    return rows


@lru_cache(maxsize=256)
def cms_keys(url):
    row = request(url, {"size": 2})[0]
    return {k.upper(): k for k in row}


def pages(url, **filters):
    # CMS changed column casing between releases. Use each release's actual filter names.
    keys = cms_keys(url)
    params = {f"filter[{keys[k.upper()]}]": v for k,v in filters.items()}
    offset = 0
    while True:
        rows = request(url, {**params,
                             "size": 5000, "offset": offset})
        for raw in rows:
            row = {k.upper():v for k,v in raw.items()}
            if any(str(row[k.upper()]) != str(v) for k,v in filters.items()):
                raise ValueError("CMS filter mismatch")
            yield row
        if len(rows) < 5000:
            break
        offset += len(rows)


def summarize_workers(rows):
    groups = defaultdict(set)
    facility = defaultdict(set)
    seen = set()
    for row in rows:
        ccn, worker, role = row["PROVNUM"], row["SYS_EMPLEE_ID"], int(row["EMPLEE_JOB_CD_ID"])
        key = (ccn, worker, role, row["EMP_CTR"])
        if key in seen:
            raise ValueError("Repeated employee detail row")
        seen.add(key)
        # A missing or suppressed hours value cannot establish that a worker reported hours.
        hours = row["WORK_HRS_NUM"]
        if row.get("WORK_HRS_FN") not in (None, "", "0", 0) or hours in ("", None) or float(hours) <= 0:
            continue
        if not worker:
            raise ValueError("Missing worker identifier")
        groups[ccn, role].add(worker)
        facility[ccn].add(worker)
    result = {ccn: {"total": len(ids), "roles": {}} for ccn, ids in facility.items()}
    for (ccn, role), ids in groups.items():
        result[ccn]["roles"][role] = len(ids)
    return result


def releases(catalog):
    sources = {}
    for entry in catalog["dataset"]:
        title = entry["title"]
        if "Payroll Based Journal" not in title:
            continue
        kind = "detail" if "Employee Detail" in title else "other" if "Non-Nurse" in title else "nurse"
        apis = [x for x in entry["distribution"] if x.get("format") == "API"]
        if not apis:
            continue
        api = apis[-1]
        start = date.fromisoformat(api["temporal"][0]["startDate"])
        q = f"{start.year}Q{(start.month-1)//3+1}"
        sources.setdefault(q, {})[kind] = api["accessURL"]
    return sources


def save(path, payload):
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(gzip.compress(json.dumps(payload,separators=(",",":")).encode(),mtime=0))
    tmp.replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache",type=Path)
    parser.add_argument("quarters",nargs="+")
    parser.add_argument("--hours-only",action="store_true")
    args=parser.parse_args()
    sources=releases(json.loads((args.cache/"catalog.json").read_text(encoding="utf8")))
    history_file = Path(__file__).resolve().parents[1] / "data/nursing_home_staffing_history_ct.json"
    history = json.loads(history_file.read_bytes())
    nurse_homes = defaultdict(set)
    for record in history["facility_quarterly_staffing_history"]:
        nurse_homes[record["quarter"]].add(record["ccn"])
    for q in args.quarters:
        directory=args.cache/q
        directory.mkdir(exist_ok=True)
        urls=sources[q]
        (directory/"sources.json").write_text(json.dumps(urls,indent=2),encoding="utf8")
        if "other" in urls and not (directory/"other.gz").exists():
            rows=list(pages(urls["other"],STATE="CT"))
            if len({(r["PROVNUM"],r["WORKDATE"]) for r in rows})!=len(rows):
                raise ValueError("Non-nursing pagination returned duplicate days")
            save(directory/"other.gz",rows)
        if args.hours_only or "detail" not in urls:
            continue
        with gzip.open(directory/"other.gz","rt",encoding="utf8") as stream:
            ccns = sorted({row.get("PROVNUM", row.get("provnum")) for row in json.load(stream)})
        ccns = sorted(set(ccns) | nurse_homes[q])
        def get_home(ccn):
            path=directory/("workers-"+ccn+".gz")
            if path.exists():
                return
            days=defaultdict(list)
            for row in pages(urls["detail"],STATE="CT",PROVNUM=ccn):
                if row["CY_QTR"] != q:
                    raise ValueError("Employee quarter mismatch")
                days[row["WORKDATE"]].append(row)
            save(path,{day:summarize_workers(rows).get(ccn) for day,rows in days.items()})
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(get_home,ccns))
        print(q,"complete",flush=True)

if __name__=="__main__":
    main()
