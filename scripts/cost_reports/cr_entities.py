"""Parse the free-form entity pages of a DSS cost report:
CSP-2 (ownership type, administrator, CHOW note), CSP-3 (partners/members), CSP-3A (corporate owners,
directors/officers, 10% stockholders), CSP-4 (related parties), CSP-11/12 (owner & administrator pay),
CSP-17 (management services).

Free-form text is split into column segments (runs separated by 2+ spaces) and grouped into entries.
Every entry keeps its raw text so a reader can check the parse."""
import re
from cr_parse import to_num

SEG = re.compile(r"\S(?:.*?\S)?(?=\s{2,}|$)")
JUNK = re.compile(r"^(N/?A|None|See attached.*|Various.*|\*.*|Use additional.*|Provide the percentage.*)$", re.I)


def segments(line):
    return [(m.start(), m.group(0)) for m in SEG.finditer(line)]


def body(page, start_rx, end_rx=None):
    lines = page.splitlines()
    out, on = [], False
    for ln in lines:
        if not on and re.search(start_rx, ln, re.I):
            on = True
            continue
        if on and end_rx and re.search(end_rx, ln, re.I):
            break
        if on:
            out.append(ln)
    return out


def entries(lines, gap=1):
    """Group lines into entries; a new entry starts when a line has text in the leftmost column
    (x < 12) after a blank line, or after `gap` blank lines."""
    groups, cur, blanks = [], [], 0
    for ln in lines:
        if not ln.strip():
            blanks += 1
            continue
        segs = segments(ln)
        left = segs and segs[0][0] < 14
        if cur and (blanks >= gap and left or blanks >= 3):
            groups.append(cur); cur = []
        cur.append(ln); blanks = 0
    if cur:
        groups.append(cur)
    return groups


def pct(s):
    m = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", s)
    if m:
        return float(m.group(1))
    m = re.search(r"(?<![\d,])(0?\.\d+|1\.0+|1)\s*$", s.strip())
    if m:
        v = float(m.group(1))
        return round(v * 100, 4) if v <= 1 else v
    m = re.search(r"(?<![\d,.])(\d{1,3}(?:\.\d+)?)\s*$", s.strip())
    if m and float(m.group(1)) <= 100:
        return float(m.group(1))
    return None


def parse_people(lines, with_title=True):
    """Entries of (name, address, title, pct/shares)."""
    out = []
    for g in entries(lines):
        segs = [segments(l) for l in g]
        name_parts = [s[0][1] for s in segs if s and s[0][0] < 30]
        rest = [t for s in segs for x, t in s if x >= 30 or (s and (x, t) != s[0])]
        name = " ".join(name_parts).strip()
        if not name or JUNK.match(name) or re.match(r"^(Name|Legal Name|Business Address|Title|% Owned)", name, re.I):
            continue
        raw = " | ".join(" ".join(l.split()) for l in g)
        p = None
        for l in g:
            p = pct(l) if p is None else p
        addr = " ".join(t for t in rest if not re.fullmatch(r"[\d.,%]+", t))
        out.append({"name": " ".join(name.split()), "address": " ".join(addr.split()) or None,
                    "percent": p, "raw": raw})
    return out


MONEY = re.compile(r"\(?-?\$?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?")
WHERE = re.compile(r"(?:Pg\.?|Page|P\.)\s*\d+[A-Za-z]?\s*[,/]?\s*(?:Line|Ln|L)?\s*[A-Za-z]?\d*[A-Za-z0-9\-]*|\b\d{1,2}[A-Za-z]?\s*/\s*[A-Za-z]?\d*[A-Za-z0-9]*\b|Various\s*/\s*Various", re.I)


def parse_related(page):
    """CSP-4 related parties. A row is anchored on the line with the cost figures (comma-formatted amounts);
    the text lines above it, back to the previous anchor, belong to the row. We keep the row text as written
    (minus amounts), the two amounts, and the page/line reference. Names are linked later by matching known
    organization names inside the row text."""
    L = page.splitlines()
    hi = next((i for i, l in enumerate(L) if re.search(r"Individual or Company", l)), None)
    if hi is None:
        return []
    rows, buf = [], []
    for ln in L[hi + 1:]:
        if re.match(r"^\s*\*{1,2}\s*(Use additional|Provide the percentage)", ln):
            break
        if not ln.strip():
            continue
        buf.append(ln)
        money = MONEY.findall(ln)
        if money:
            vals = [to_num(m) for m in money]
            text = " ".join(" ".join(l.split()) for l in buf)
            for m in money:
                text = text.replace(m, " ")
            where = WHERE.search(text)
            first = segments(buf[0])
            name_guess = None
            for l in buf:
                sg = segments(l)
                if sg and sg[0][0] < 6:
                    name_guess = (name_guess + " " if name_guess else "") + re.split(r"\s\d{1,6}\s", sg[0][1] + " ")[0].strip()
            p = re.search(r"\b(\d{1,3})\s*%", text)
            rows.append({"name_guess": name_guess, "text": " ".join(text.split()),
                         "where": where.group(0).strip() if where else None,
                         "pct_revenue_from_non_related": float(p.group(1)) if p else None,
                         "cost_reported": vals[-2] if len(vals) >= 2 else vals[-1],
                         "actual_cost_to_related_party": vals[-1] if len(vals) >= 2 else None})
            buf = []
    return rows


def parse_management(page):
    lines = body(page, r"Company Supplying Service|Supplying Service", r"^\s*\*\s*In addition")
    out = []
    for g in entries(lines):
        txt = " ".join(" ".join(l.split()) for l in g)
        m = re.search(r"\(?\$?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?", txt)
        if not m:
            continue
        name = txt[:m.start()].strip(" $")
        out.append({"name": name or None, "cost": to_num(m.group(0)),
                    "description": txt[m.end():].strip()[:200] or None, "raw": txt})
    return out


def parse_general(page):
    t = " ".join(page.split())
    rec = {}
    m = re.search(r"Name of Administrator\s+(.+?)\s+Nursing Home\s+Administrator'?s?\s+(\d+)", t)
    if m:
        rec["administrator_name"], rec["administrator_license"] = m.group(1).strip(), m.group(2)
    m = re.search(r"change in ownership.*?during this report year\?\s*Yes\s*No\s*If \"?Yes,?\"? explain fully\.?\s*(.{0,300}?)\s*(Administrator|Name of Administrator)", t, re.I)
    if m:
        rec["chow_note"] = m.group(1).strip() or None
    return rec


def extract_entities(P):
    e = {}
    if "2" in P:
        e.update(parse_general(P["2"][0]))
    if "3" in P:
        e["partners_members"] = parse_people(body(P["3"][0], r"Name of Partners/Members"))
        e["partnership_legal_name"] = None
        lines = body(P["3"][0], r"Legal Name of Partnership", r"Name of Partners/Members")
        if lines:
            segs = segments(next((l for l in lines if l.strip()), ""))
            e["partnership_legal_name"] = segs[0][1] if segs else None
    if "3A" in P:
        pg = P["3A"][0]
        lines = body(pg, r"Legal Name of Corporation", r"Name of Directors")
        segs = segments(next((l for l in lines if l.strip()), "")) if lines else []
        e["corporation_legal_name"] = segs[0][1] if segs and not JUNK.match(segs[0][1]) else None
        e["directors_officers"] = parse_people(body(pg, r"Held by Each|Name of Directors", r"Names of Stockholders"))
        e["stockholders_10pct"] = parse_people(body(pg, r"of Shares\s*$|Names of Stockholders", None))
    if "4" in P:
        e["related_parties"] = [r for p in P["4"] for r in parse_related(p)]
    if "17" in P:
        e["management_services"] = [r for p in P["17"] for r in parse_management(p)]
    return e


CATS = [
    ("pharmacy / supplies", r"pharm|drug|supplies|medical supply|oxygen"),
    ("insurance", r"insur"),
    ("rent / lease / real estate", r"\brent|lease|realty|real (estate|property)|property tax|real estate"),
    ("therapy", r"therap|rehab|\bPT\b|\bOT\b"),
    ("staffing / nursing agency", r"staffing|agency|nursing pool|staff pool"),
    ("management / home office", r"manag|home office|shared expense|administrative serv|consult"),
    ("loans / interest / receivables", r"loan|interest|due to|due from|receivable|payable|intercompany|\bnote"),
    ("salaries / shared employees", r"salar|shared employ|payroll|benefit"),
    ("food / laundry / housekeeping", r"food|dietary|laundry|housekeep|linen"),
    ("lab / radiology / medical", r"radiolog|x-ray|laborator|diagnost|physician|medical director|hospice"),
]


def categorize(text):
    t = (text or "").lower()
    for name, rx in CATS:
        if re.search(rx, t, re.I):
            return name
    return "other"


_old_extract = extract_entities


def extract_entities(P):
    e = _old_extract(P)
    for r in e.get("related_parties", []):
        r["category"] = categorize(r.get("text"))
    for k in ("partners_members", "directors_officers", "stockholders_10pct"):
        for r in e.get(k, []):
            n = r.get("name") or ""
            m = re.search(r"\s\d{1,6}\s+\w", n + " ")
            if m and m.start() > 3:
                r["address"] = (n[m.start():].strip() + " " + (r.get("address") or "")).strip()
                r["name"] = n[:m.start()].strip()
        e[k] = [r for r in e.get(k, []) if not re.match(r"^(of Shares|10% of Shares|Same as above|Name|N/?A)\b", r.get("name") or "", re.I)]
    return e
