"""Index DSS cost-report PDFs (via extracted text / page-1 OCR) and match each to a CMS CCN."""
import csv, glob, json, os, re, collections, difflib

SITE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
# Work folder holding _text/, _ocr_p1/, _ct_extract/ (private; see docs/nursing_home_cost_reports_runbook.md)
ROOT = os.environ.get("COST_REPORT_WORKDIR", os.path.join(SITE, "data", "testing", "cost_reports", "work"))

# ---------- facility master: every CT CCN seen in CMS since 2020 + PBJ history + current list ----------
master = {}  # ccn -> {names:set, legal:set, city, address}
def add(ccn, name=None, legal=None, city=None, addr=None):
    ccn = (ccn or "").strip().zfill(6)
    if not ccn.startswith("07"):
        return
    m = master.setdefault(ccn, {"names": set(), "legal": set(), "city": None, "address": None, "addrs": set(), "cities": set()})
    if addr: m["addrs"].add(addr.strip().upper())
    if city: m["cities"].add(city.strip().upper())
    if name: m["names"].add(name.strip())
    if legal and "NOT AVAILABLE" not in legal.upper(): m["legal"].add(legal.strip())
    if city: m["city"] = city.strip()
    if addr: m["address"] = addr.strip()

for f in sorted(glob.glob(f"{ROOT}/_ct_extract/*/*ProviderInfo*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8")):
        k = {c.lower(): c for c in r}
        ccn = r.get(k.get("cms certification number (ccn)") or k.get("federal provider number") or k.get("provnum"), "")
        add(ccn, r.get(k.get("provider name") or k.get("provname"), ""), r.get(k.get("legal business name", ""), ""),
            r.get(k.get("city/town") or k.get("provider city") or k.get("city"), ""),
            r.get(k.get("provider address") or k.get("address"), ""))
hist = json.load(open(f"{SITE}/data/nursing_home_staffing_history_ct.json", encoding="utf-8"))
for f in hist["facilities"]:
    add(f.get("ccn"), f.get("latest_pbj_provider_name"), None, f.get("latest_pbj_city"))
for f in json.load(open(f"{SITE}/data/nursing_home_staffing_ct.json", encoding="utf-8"))["facilities"]:
    add(f.get("ccn"), f.get("provider_name"), None, f.get("city"))
# CHOW names
for r in csv.DictReader(open(sorted(glob.glob(os.path.join(SITE, "data", "testing", "cost_reports", "SNF_CHOW_*.csv")))[-1], encoding="utf-8-sig", errors="replace")):
    for side in ("BUYER", "SELLER"):
        add(r[f"CCN - {side}"], r[f"DOING BUSINESS AS NAME - {side}"], r[f"ORGANIZATION NAME - {side}"])
# DPH license -> CCN from the reviewed administrator crosswalk
lic2ccn = {}
for d in json.load(open(f"{SITE}/data/testing/ct_dph_ccn_crosswalk_decisions_20261105.json", encoding="utf-8")):
    if d.get("ccn") and d.get("decision") == "accepted":
        lic2ccn[str(d["facility_license"]).lstrip("0")] = d["ccn"]

STOP = set("llc inc the of and at for center centre health care healthcare rehabilitation rehab nursing home "
           "manor dba d b a co corp corporation ltd lp skilled facility convalescent chronic living".split())
def toks(s):
    return {t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if t not in STOP and len(t) > 1}

# ---------- parse documents ----------
def norm_date_year(s):
    m = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,4})", s or "")
    if not m: return None
    y = m.group(3); y = int(y) if len(y) == 4 else 2000 + int(y)
    return y if 2010 <= y <= 2026 else None

def parse(text, kind_hint=None):
    p = text[:6000]
    r = {}
    if re.search(r"Narrative Summary", p[:2500], re.I): r["kind"] = "narrative"
    elif re.search(r"Annual Report of Long.{0,8}Care|Report for Year Ending|Name of Facility \(as licensed\)", p, re.I): r["kind"] = "annual"
    elif "Rate Setting Guide" in p: r["kind"] = "guide"
    else: r["kind"] = "other"
    m = re.search(r"Name of Facility \(as licensed\)\s*\n+\s*(.+)", p) or re.search(r"Facility Name\s{2,}(.+)", p)
    r["name"] = m.group(1).strip() if m else None
    m = re.search(r"Address\s*\(No\..{0,60}\)\s*\n+\s*(.+)", p) or re.search(r"Facility Address\s{2,}(.+\n?.*)", p)
    r["address"] = " ".join(m.group(1).split()) if m else None
    i = p.find("Report for Year")
    if i >= 0:
        ds = re.findall(r"\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{2,4}", p[i:i + 500])
        if len(ds) >= 2:
            r["period_start"], r["period_end"] = [re.sub(r"\s", "", d) for d in ds[:2]]
    r["cost_year"] = norm_date_year(r.get("period_end"))
    m = re.search(r"Cost Year\s+(20\d\d)", p)
    if m and not r["cost_year"]: r["cost_year"] = int(m.group(1))
    j = p.find("License Numbers")
    seg = p[j:j + 700] if j >= 0 else ""
    m = re.search(r"\b0\s?7\s?[-–—]\s?[0-9A-Z]\s?\d\s?\d\s?\d\b", seg) or re.search(r"\b07[-–]?\d{4}\b", seg)
    r["medicare"] = re.sub(r"[^0-9A-Z]", "", m.group(0)) if m else None
    seg2 = re.sub(r"0\s?7\s?[-–—]\s?[0-9A-Z]\s?\d\s?\d\s?\d", " ", seg.split("Medicaid Provider")[0]) if seg else ""
    lics = re.findall(r"(?<![\d/])(\d{3,4})\s*-?\s*[CR]?\b(?!\s*/)", seg2)
    r["licenses"] = sorted({x.lstrip("0") for x in lics})
    k = p.find("Medicaid Provider")
    r["medicaid"] = re.findall(r"\b\d{4,5}C?\b", p[k:k + 300]) if k >= 0 else []
    m = re.search(r"Provider Number\s+(\d{6,10})", p)
    if m: r["provider_number"] = m.group(1)
    return r

docs = []
for f in sorted(glob.glob(f"{ROOT}/_text/*.txt")):
    base = os.path.basename(f)[:-4]
    t = open(f, encoding="utf-8", errors="replace").read()
    src = "text"
    if len(t.strip()) < 50:
        o = f"{ROOT}/_ocr_p1/{base}.txt"
        t = open(o, encoding="utf-8", errors="replace").read() if os.path.exists(o) else ""
        src = "ocr_p1"
    d = parse(t); d["file"] = base; d["text_source"] = src
    # filename year hints
    m = re.search(r"(20\d\d)", base) or re.search(r"FY(\d\d)", base)
    if m: d["file_year"] = int(m.group(1)) if len(m.group(1)) == 4 else 2000 + int(m.group(1))
    docs.append(d)

# ---------- match ----------
names_by_ccn = {c: (m["names"] | m["legal"]) for c, m in master.items()}
def name_score(name, ccn):
    a = toks(name); best = 0
    for n in names_by_ccn.get(ccn, ()):
        b = toks(n)
        if a and b: best = max(best, len(a & b) / max(1, min(len(a), len(b))))
    return best
def addr_score(addr, ccn):
    if not addr: return 0
    A = addr.upper()
    nums = re.findall(r"\b(\d{1,5})\b", A.split(",")[0])
    best = 0
    for ad in master[ccn]["addrs"]:
        n2 = re.findall(r"\b(\d{1,5})\b", ad)
        w1 = toks(A.split(",")[0]) ; w2 = toks(ad)
        sc = 0
        if nums and n2 and nums[0] == n2[0]: sc += 0.5
        if w1 and w2 and len(w1 & w2) / max(1, min(len(w1), len(w2))) >= 0.5: sc += 0.5
        best = max(best, sc)
    if any(c in A for c in master[ccn]["cities"]): best += 0.25
    return best

for d in docs:
    nm = d.get("name") if d.get("name") and d["name"] not in ("Facility Address",) else None
    fname = re.sub(r"(?i)\b(20\d\d|FY\d\d|CR|annual report|cost report|narrative summary.*|nf narrative summary of expenditures|nursing facility)\b|[_-]", " ", d["file"])
    cands = {}
    for c in master:
        sc = {"name": max(name_score(nm, c) if nm else 0, name_score(fname, c)),
              "address": addr_score(d.get("address"), c),
              "medicare": 1 if d.get("medicare") == c else 0,
              "license": 1 if any(lic2ccn.get(l) == c for l in d.get("licenses", [])) else 0}
        tot = sc["name"] + sc["address"] + 1.0 * sc["medicare"] + 1.0 * sc["license"]
        if tot > 0: cands[c] = (tot, sc)
    ranked = sorted(cands.items(), key=lambda x: -x[1][0])
    d["ccn"], d["match"], d["evidence"] = None, None, None
    if ranked:
        c, (tot, sc) = ranked[0]
        second = ranked[1][1][0] if len(ranked) > 1 else 0
        d["evidence"] = {k: round(v, 2) for k, v in sc.items()}
        d["runner_up"] = ranked[1][0] if len(ranked) > 1 else None
        strong = sum([sc["address"] >= 1, sc["medicare"] == 1, sc["license"] == 1, sc["name"] >= 0.67])
        if strong >= 2 and tot - second >= 0.5: d["ccn"], d["match"] = c, "confirmed"
        elif strong >= 1 and tot - second >= 0.5: d["ccn"], d["match"] = c, "probable"
        else: d["candidate"] = c; d["match"] = "review"
    d["year"] = d.get("cost_year") or d.get("file_year")

json.dump(docs, open(f"{ROOT}/cost_report_index.json", "w", encoding="utf-8"), indent=1, default=list)
c = collections.Counter((d["kind"], d["match"]) for d in docs)
for k, v in sorted(c.items(), key=lambda x: (str(x[0]))): print(k, v)
print("master ccns", len(master))
