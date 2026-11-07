import re, json, os, sys, collections, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr_extract import extract, derive, checks
import cr_parse
from cr_entities import extract_entities
from cr_period import read_period

SITE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def clean_ocr(t):
    """Fix common OCR misreads that break row matching: an item number read as "4," and a thousands
    comma read as a period inside a bracketed amount, e.g. "(5.159,901)" or "(30.271)"."""
    # stray marks left of the item number (scan specks, table edges): blank them, keeping columns
    t = re.sub(r"(?m)^(\s*)([|_‘’“”'~—–:;,.]+)(?=\s)", lambda m: m.group(1) + " " * len(m.group(2)), t)
    # item code "A-13" read as "4-13" or "A-]3"
    t = re.sub(r"(?m)^(\s*)4-(\d{1,2})([.,]\s)", r"\1A-\2\3", t)
    t = re.sub(r"\bA-\]3\b", "A-13", t)
    t = re.sub(r"(?m)^(\s*)(\d{1,2}),(\s)", r"\1\2.\3", t)
    t = re.sub(r"(?<=\d)\.(?=\d{3},\d{3})", ",", t)
    # thousands separators read as periods: "6.917.519", "222.180" (amounts and hours are whole numbers)
    t = re.sub(r"(?<![\d.,])(\d{1,3})\.(\d{3})\.(\d{3})(?![\d.%])", r"\1,\2,\3", t)
    t = re.sub(r"(?<![\d.,$])(\d{1,3})\.(\d{3})(?![\d.,%])", r"\1,\2", t)
    t = re.sub(r"\((\d{1,3})\.(\d{3})\)", r"(\1,\2)", t)
    # misread words and item codes seen in the scanned reports
    for bad, good in ((r"\bReven[nu]e\b", "Revenue"), (r"\bTtem\b", "Item"), (r"\bA[~_—–]\s?13\b", "A-13"),
                      (r"(?m)^(\s*\d{1,2})\._\s", r"\1. "), (r"\bExpenditnres\b", "Expenditures"),
                      (r"\bSalarv\b", "Salary"), (r"\bTatal\b", "Total"), (r"\bHo(?:ws|uts|nrs|ors|urg|uts|rs|ars)\b", "Hours")):
        t = re.sub(bad, good, t)
    return t


ROOT = os.environ.get("COST_REPORT_WORKDIR", os.path.join(SITE, "data", "testing", "cost_reports", "work"))
idx = json.load(open(f"{ROOT}/cost_report_index.json", encoding="utf-8"))
out = []
for d in idx:
    if d["kind"] != "annual":
        continue
    src = f"{ROOT}/_text/{d['file']}.txt"
    t = open(src, encoding="utf-8", errors="replace").read()
    # the report period is on pages 1-2, which the layout re-OCR skips: read it from the full text
    head = t
    if len(t.strip()) < 50 and os.path.exists(f"{ROOT}/ocr_full/{d['file']}.txt"):
        head = open(f"{ROOT}/ocr_full/{d['file']}.txt", encoding="utf-8", errors="replace").read()
    p_start, p_end = read_period(head, d.get("year")) if d.get("year") else (None, None)
    if len(t.strip()) < 50:
        # scanned report: prefer the layout re-OCR of the form pages (reocr_out/), else the first-pass OCR
        o = f"{ROOT}/reocr_out/{d['file']}.txt"
        source = "ocr_layout"
        if not os.path.exists(o):
            o, source = f"{ROOT}/ocr_full/{d['file']}.txt", "ocr_full"
        if not os.path.exists(o):
            continue
        t = clean_ocr(open(o, encoding="utf-8", errors="replace").read())
        d = dict(d, text_source=source)
    # scanned pages: header words sit centred over their columns, so read columns by centre
    cr_parse.ALIGN = "center" if d.get("text_source", "text").startswith("ocr") else "right"
    try:
        rec, P = extract(t)
        out.append({"file": d["file"], "ccn": d.get("ccn"), "year": d.get("year"), "match": d.get("match"),
                    "text_source": d["text_source"], "pages_found": sorted(P), "fields": rec,
                    "derived": derive(rec), "checks": checks(rec), "entities": extract_entities(P),
                    "period": {"start": p_start.isoformat(), "end": p_end.isoformat()} if p_start else None})
    except Exception as e:
        out.append({"file": d["file"], "error": repr(e), "trace": traceback.format_exc()[-500:]})
json.dump(out, open(f"{ROOT}/extract_all.json", "w", encoding="utf-8"), indent=0, default=float)

ok = [o for o in out if "fields" in o]
print("reports", len(out), "errors", len(out) - len(ok))
keys = list(ok[0]["fields"])
cov = {k: sum(1 for o in ok if o["fields"].get(k) not in (None, 0)) / len(ok) for k in keys}
for k in keys:
    print(f"{k:32s} {cov[k]:.2f}")
for c in ("days_sum", "revenue_sum", "liabilities_sum", "has_core"):
    v = [o["checks"].get(c) for o in ok if c in o["checks"]]
    print(c, f"{sum(v)}/{len(v)}")
