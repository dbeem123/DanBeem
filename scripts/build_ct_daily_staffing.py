"""Build public facility/quarter shards from Connecticut PBJ source rows and aggregate counts."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import zipfile
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

from fetch_ct_daily_staffing import releases

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ["Nursing", "Medical and pharmacy", "Therapy and rehabilitation", "Activities and social services",
          "Food and nutrition", "Administration and support"]
# CMS job codes connect the two independent publications.
ROLE_ROWS = [
    (5,0,"RNDON","Director of nursing (RN)"), (6,0,"RNadmin","RN with administrative duties"),
    (7,0,"RN","Registered nurse"), (8,0,"LPNadmin","LPN with administrative duties"),
    (9,0,"LPN","Licensed practical nurse"), (10,0,"CNA","Certified nurse aide"),
    (11,0,"NAtrn","Nurse aide in training"), (12,0,"MedAide","Medication aide or technician"),
    (2,1,"MedDir","Medical director"), (3,1,"OthMD","Other physician"), (4,1,"PA","Physician assistant"),
    (13,1,"NP","Nurse practitioner"), (14,1,"ClinNrsSpec","Clinical nurse specialist"),
    (15,1,"Pharmacist","Pharmacist"), (18,2,"OT","Occupational therapist"),
    (19,2,"OTasst","Occupational therapy assistant"), (20,2,"OTaide","Occupational therapy aide"),
    (21,2,"PT","Physical therapist"), (22,2,"PTasst","Physical therapist assistant"),
    (23,2,"PTaide","Physical therapy aide"), (24,2,"RespTher","Respiratory therapist"),
    (25,2,"RespTech","Respiratory therapy technician"), (26,2,"SpcLangPath","Speech-language pathologist"),
    (27,3,"TherRecSpec","Therapeutic recreation specialist"), (28,3,"QualActvProf","Qualified activities professional"),
    (29,3,"OthActv","Other activities staff"), (30,3,"QualSocWrk","Qualified social worker"),
    (31,3,"OthSocWrk","Other social worker"), (34,3,"MHSvc","Mental health service worker"),
    (16,4,"Dietician","Dietitian"), (17,4,"FeedAsst","Paid feeding assistant"), (1,5,"Admin","Administrator")]
NURSE = [r for r in ROLE_ROWS if r[1]==0]
OTHER = [r for r in ROLE_ROWS if r[1]!=0]
ALIASES = {"hrs_rn_donadmin":"hrs_rndon","hrs_lpn_admin":"hrs_lpnadmin","hrs_na_trn":"hrs_natrn",
           "hrs_foodsvc":"hrs_feedasst"}


def load(path):
    return json.loads(path.read_bytes().decode("utf-8-sig"))


def unpack(path):
    with gzip.open(path, "rt", encoding="utf8") as stream:
        return json.load(stream)


def dump(path, value):
    raw=(json.dumps(value, ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n").encode()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(gzip.compress(raw,compresslevel=5,mtime=0) if path.suffix==".gz" else raw)


@contextmanager
def nurse_rows(path, entry):
    if entry:
        with zipfile.ZipFile(path) as archive, archive.open(entry) as stream, io.TextIOWrapper(stream,encoding="utf-8-sig") as text:
            yield csv.DictReader(text)
    else:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            yield csv.DictReader(stream)


def number(value):
    if value in ("",None,".","NA"): return None
    n=float(value)
    if not math.isfinite(n) or n<0: raise ValueError(f"Invalid hours or census: {value}")
    return int(n) if n.is_integer() else n


def column_name(key):
    key = key.lower()
    for suffix in ("_emp", "_ctr", "_fn"):
        if key.endswith(suffix):
            base = key[:-len(suffix)]
            return ALIASES.get(base, base) + suffix
    return ALIASES.get(key, key)


def collect(days, rows, roles, q):
    allowed = {("hrs_"+r[2]).lower() for r in roles}
    checked=False
    seen=set()
    for raw in rows:
        row={column_name(k):v for k,v in raw.items()}
        if row["state"]!="CT":continue
        if not checked:
            unknown={k for k in row if k.startswith("hrs_") and not k.endswith(("_emp","_ctr","_fn"))}-allowed
            if unknown:raise ValueError(f"Unmapped CMS columns {unknown} in {q}")
            checked=True
        ccn=row["provnum"].strip().zfill(6)
        date=str(row["workdate"])
        if row["cy_qtr"].upper()!=q or len(date)!=8 or date[:4]!=q[:4] or (int(date[4:6])-1)//3+1!=int(q[-1]):
            raise ValueError(f"Unexpected quarter/date: {q}, {date}")
        if (ccn,date) in seen:raise ValueError(f"Duplicate facility day: {ccn} {date}")
        seen.add((ccn,date))
        census=number(row["mdscensus"])
        day=days[ccn].setdefault(date,{"census":census,"roles":{}})
        if day["census"] is None:day["census"]=census
        if census is not None and day["census"]!=census:raise ValueError(f"Census mismatch {ccn} {date}")
        for code,_,field,_ in roles:
            k="hrs_"+field.lower()
            if k not in row:continue
            excluded=row.get(k+"_fn") not in (None,"","0",0)
            hours=[None]*3 if excluded else [number(row.get(k+s)) for s in ("","_emp","_ctr")]
            day["roles"][code]=hours+[1 if excluded else 0]


def build(args):
    history=load(ROOT/"data/nursing_home_staffing_history_ct.json")
    inventory={r["quarter"]:r for r in history["pbj_source_inventory"]}
    urls=releases(load(args.cache/"catalog.json"))
    out=args.out
    manifest={"groups":GROUPS,"roles":[{"id":i,"group":g,"label":label} for i,g,_,label in ROLE_ROWS],
              "facilities":{},"quarters":{}}
    current = {f["ccn"] for f in load(ROOT/"data/nursing_home_staffing_ct.json")["facilities"]}
    manifest["historical_homes"] = {f["ccn"]: f["latest_pbj_provider_name"] for f in history["facilities"]
                                    if f["ccn"] not in current}
    known={(r["ccn"],r["quarter"]):r for r in history["facility_quarterly_staffing_history"]}
    for q, source in sorted(inventory.items()):
        if args.quarters and q not in args.quarters:continue
        directory=args.cache/q
        path=args.nurse_root/Path(source["source_file"]).relative_to("source_data/pbj")
        if q=="2026Q2" and args.latest:path=args.latest
        days=defaultdict(dict)
        if not path.is_file():
            raise FileNotFoundError(path)
        with nurse_rows(path,source.get("zip_entry")) as rows:
            collect(days,rows,NURSE,q)
        other=directory/"other.gz"
        if "other" in urls.get(q, {}) and not other.exists():
            raise FileNotFoundError(other)
        if other.exists():
            collect(days, unpack(other), OTHER, q)
        coverage={"facilities":len(days),"facility_days":0,"worker_days":0,"reconciled":0,"sources":urls.get(q,{})}
        if path.is_file():coverage["nurse_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        if other.is_file():coverage["other_sha256"]=hashlib.sha256(other.read_bytes()).hexdigest()
        for ccn,bydate in sorted(days.items()):
            wp=directory/f"workers-{ccn}.gz"
            if "detail" in urls.get(q, {}) and not wp.exists():
                raise FileNotFoundError(wp)
            workers=unpack(wp) if wp.exists() else {}
            packed={}
            nursing_hours = [0.0, 0.0, 0.0]
            resident_days = 0
            for day, record in sorted(bydate.items()):
                counts=workers.get(day)
                if counts:coverage["worker_days"]+=1
                entries=[]
                for code,_,_,_ in ROLE_ROWS:
                    total,emp,ctr,excluded=record["roles"].get(code,[None,None,None,0])
                    count=counts["roles"].get(str(code), 0 if total is not None else None) if counts and not excluded else None
                    if count==0 and total and total>0:count=None
                    entries.append([total,emp,ctr,count,excluded])
                packed[day]=[record["census"],counts["total"] if counts else None,entries]
                if record["census"] and all(v[0] is not None for v in entries[:8]):
                    for i, block in enumerate((entries[:3], entries[3:5], entries[5:8])):
                        nursing_hours[i] += sum(v[0] for v in block)
                    resident_days += record["census"]
            prior=known.get((ccn,q))
            if prior and resident_days:
                totals = dict(zip(("rn_hprd", "lpn_lvn_hprd", "nurse_aide_hprd"), nursing_hours))
                totals["total_nurse_hprd"] = sum(nursing_hours)
                for metric, hours in totals.items():
                    expected = prior["metrics"].get(metric)
                    if expected is None:
                        continue
                    if resident_days != prior["resident_days"] or abs(hours/resident_days - expected) > .005001:
                        raise ValueError(f"Reconciliation failed: {ccn} {q} {metric} {hours/resident_days} vs {expected}")
                coverage["reconciled"] += 1
            dump(out/q/(ccn+".json.gz"),packed)
            manifest["facilities"].setdefault(ccn,[]).append(q)
            coverage["facility_days"]+=len(packed)
        manifest["quarters"][q]=coverage
        print(q,coverage["facilities"],coverage["worker_days"],flush=True)
    dump(out/"index.json",manifest)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--nurse-root",type=Path,required=True)
    parser.add_argument("--latest",type=Path)
    parser.add_argument("--quarters",nargs="+")
    parser.add_argument("--out",type=Path,default=ROOT/"data/ct_daily_staffing")
    build(parser.parse_args())
