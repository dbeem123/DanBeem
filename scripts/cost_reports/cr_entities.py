"""Parse the free-form entity pages of a DSS cost report:
CSP-2 (ownership type, administrator, CHOW note), CSP-3 (partners/members), CSP-3A (corporate owners,
directors/officers, 10% stockholders), CSP-4 (related parties), CSP-11/12 (owner & administrator pay),
CSP-17 (management services).

Free-form text is split into column segments (runs separated by 2+ spaces) and grouped into entries.
Every entry keeps its raw text so a reader can check the parse."""
import re
if __package__:
    from .cr_parse import to_num
else:
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
RELATED_CELL = re.compile(r"\S+(?:[ \t]\S+)*")
AMOUNT = re.compile(r"(?<![\w/.,])(?:\*+)?\$?\s*(\(?-?\$?\d+(?:[,.]\d{3})*(?:\.\d{1,2})?\)?)(?:\*+)?(?=\s|$)")
ADDRESS = re.compile(
    r"^\s*(?:P\.?\s*O\.?\s+Box\b|\d+[A-Z]?\s+.+?\b(?:street|st|road|rd|avenue|ave|"
    r"drive|dr|lane|ln|highway|hwy|boulevard|blvd|turnpike|tpke|court|ct|way|suite)\b"
    r"|(?:[A-Z]{2},?\s+)?\d{5}(?:-\d{4})?$|"
    r"[\w .'-]+,\s*[A-Z]{2},?(?:\s+\d{5}(?:-\d{4})?)?$)", re.I
)
STREET_START = re.compile(r"(?<!\S)\d+[A-Z]?\s+(?=[^|]*\b(?:st|street|rd|road|ave|avenue|dr|drive|"
                          r"ln|lane|hwy|highway|tpke|turnpike|blvd|boulevard)\b)", re.I)
COMPANY_TAIL = re.compile(r"\b(?:realty|propco|properties|llc|llp|inc|corp|company|center|services)\b[.,]*$", re.I)
CITY_STATE = re.compile(r"\s+[A-Z][\w'-]+,\s*[A-Z]{2}(?:,?\s+\d{5}(?:-\d{4})?)?$", re.I)
AMOUNT_SUFFIX = re.compile(r"\b(?:N/?A|replaced by fair rent|fair rent(?:al)?(?: value)?|not applicable)\b", re.I)
STATE_ZIP = re.compile(r"\s+(?:[A-Z]{2},?\s+)?\d{5}(?:-\d{4})?$")
SUMMARY = re.compile(r"^(?:see\b.*(?:attach|page\s*4\s*a)|various\b.*see\s+attach|(?:see\s+)?(?:addit[io]*nal\s+)?page\s*4\s*a\b|4\s*a\b)", re.I)
STOP_RELATED = re.compile(r"^\s*(?:\*{0,3}\s*(?:Use additional sheets|Provide the percentage)|\*{1,3}\s*(?:Actual Cost|N/A))", re.I)
REPORTED = re.compile(r"\bRe[po ]{1,4}rted\b", re.I)
REFERENCE = re.compile(r"\bPage\s*#?\s*/\s*Line\s*#?", re.I)
BALANCE_CATEGORY = "loans / interest / receivables"
RENT_CATEGORY = "rent / lease / real estate"
RELATED_PARTY_METHOD = (
    "Totals use readable itemized rows on page 4 and its continuation pages, including signed credits. "
    "Attachment references and their summary amounts, duplicate lines, loans, balances and unreadable rows "
    "are excluded. A report can list additional costs that the reader could not assign."
)


def related_row(lines, names, descriptions, where, reported, actual, status=None):
    name = " ".join(names) or None
    service = " ".join(descriptions) or None
    if SUMMARY.match(name or ""):
        status = "attachment summary"
    if not status and (not name or reported is None):
        status = "unreadable"
    text = " | ".join(" ".join(line.split()) for line in lines)
    return {"name_guess": name, "description": service, "text": text, "where": where,
            "pct_revenue_from_non_related": next(
                (float(m.group(1)) for m in re.finditer(r"(?<!\d)(\d{1,3})\s*%", text)
                 if int(m.group(1)) <= 100), None),
            "cost_reported": reported, "actual_cost_to_related_party": actual,
            "category": None if status else categorize_related(service, name),
            "row_status": status}


def related_layout(lines, i):
    def find(pattern, indexes):
        for j in indexes:
            if 0 <= j < len(lines) and (m := re.search(pattern, lines[j], re.I)):
                return j, m
        return i, None

    nearby = (i, i-1, i+1, i-2, i+2, i-3, i+3)
    name = re.search(r"Individual or Company", lines[i], re.I)
    addr_i, address = find(r"\bAddress\b", nearby)
    provided_i, provided = find(r"\bProvided\b", nearby)
    reported_i, reported = find(REPORTED.pattern, nearby)
    actual_i, actual = find(r"\b(?:Related Party|Party)\b(?=\s*$)", nearby)
    ref_i, ref = find(REFERENCE.pattern, nearby)
    above_i, above_ref = find(r"\b(?:Included\s+)?in Annual\s*Report\b", (i-1, i-2, i-3))
    if above_ref and (not ref or abs(above_ref.start() - ref.start()) < 8):
        ref_i, ref = max(above_i, ref_i), min((m for m in (ref, above_ref) if m), key=lambda m: m.start())
    if not all((name, address, provided, reported, actual)):
        return None
    if (reported.start() - provided.start() < 24 or address.start() - name.start() < 15
            or actual.end() - reported.end() < 11):
        return None
    ref_x = ref.start() if ref else reported.start() - 17
    pct_i, pct = find(r"%\s*\*", nearby)
    service_x = max(provided.start() - 26, pct.start() - 2 if pct else 0)
    name_end = name.start() + (address.start() - name.start()) * .6
    return (name_end, service_x, ref_x, reported.start() - 9,
            (reported.end() + actual.end()) / 2, max(i, addr_i, provided_i, reported_i, actual_i, ref_i, pct_i))


def related_name_cell(part, name_end):
    """Split text that crosses the name/address gutter without two spaces."""
    street = next((m for m in STREET_START.finditer(part) if m.start() >= name_end - 6), None)
    city = CITY_STATE.search(part)
    if street:
        return part[:street.start()].strip(" |"), part[street.start():]
    if city and city.start() >= name_end - 6:
        return part[:city.start()].strip(" |"), part[city.start():].strip()
    if ADDRESS.search(part) and not COMPANY_TAIL.search(part):
        return "", part
    return STATE_ZIP.sub("", part).strip(" |"), ""


def related_line(line, layout):
    name_end, service_x, ref_x, money_x, amount_split, _ = layout
    name, address, description, refs = [], [], [], []
    costs, actuals = [], []
    for cell in RELATED_CELL.finditer(line):
        x, part = cell.start(), cell.group()
        if x >= money_x:
            # Require a stand-alone amount or a pair of amounts in the cost lanes.
            amounts = list(AMOUNT.finditer(part))
            if amounts and not AMOUNT_SUFFIX.sub("", AMOUNT.sub("", part)).strip(" $=|:*.-#\"'"):
                for m in amounts:
                    value = to_num(re.sub(r"\.(?=\d{3}(?:\D|$))", ",", m[1]))
                    (costs if x + m.end() <= amount_split else actuals).append(value)
        elif x >= ref_x - 2:
            if part.strip("|* "):
                refs.append(part)
        elif x >= service_x:
            service = re.sub(r"^[\W_]*(?:[<>]?\s*\d{1,3}\s*%)?\s*", "", part)
            if len(service) > 1:
                description.append(service)
        elif x < name_end and re.search(r"[A-Za-z]", part):
            identity, tail = related_name_cell(part, name_end - x)
            if identity:
                name.append(identity)
            if tail:
                address.append(tail)
        elif x < service_x - 20 and re.search(r"[A-Za-z0-9]", part):
            address.append(part)
    return name, address, description, refs, costs, actuals


def parse_related(page):
    """Read CSP-4 by printed columns, using cost lanes as row anchors."""
    lines = page.splitlines()
    i = next((i for i, line in enumerate(lines) if re.search(r"Individual or Company", line, re.I)), None)
    if i is None:
        # Some OCR pages lose the column header entirely. Only look below the
        # table heading and keep recognizable amount lines as unreadable.
        i = next((i for i, line in enumerate(lines) if "Description of Goods" in line), None)
        if i is None:
            return []
        layout = None
    else:
        layout = related_layout(lines, i)
    rows, pending, names, services, refs = [], [], [], [], []
    had_address = False
    table_start = layout[-1] if layout else i
    for line in lines[table_start+1:]:
        if STOP_RELATED.match(line):
            break
        if not line.strip():
            continue
        if not layout:
            if MONEY.search(line):
                rows.append(related_row([line], [], [], None, None, None, "unreadable"))
            continue
        name, address, desc, ref, costs, actuals = related_line(line, layout)
        # A complete description/reference without amounts can precede a new party.
        # A second street address also marks a new party when the prior name wrapped.
        new_party = bool(name and (services and refs or
                                   had_address and any(re.match(r"^(?:\d+\s|P\.?\s*O\.?\s+Box)", a, re.I)
                                                       and ADDRESS.search(a) for a in address)))
        if new_party and names:
            pending, names, services, refs, had_address = [], [], [], [], False
        pending.append(line)
        names.extend(name)
        services.extend(desc)
        refs.extend(ref)
        had_address = had_address or bool(address)
        if costs or actuals:
            status = "unreadable" if len(costs) != 1 or len(actuals) > 1 else None
            rows.append(related_row(pending, names, services, " ".join(refs) or None,
                                    costs[0] if len(costs) == 1 else None,
                                    actuals[0] if len(actuals) == 1 else None, status))
            pending, names, services, refs, had_address = [], [], [], [], False
        elif any(m.start() >= layout[3] for m in MONEY.finditer(line)):
            rows.append(related_row(pending, names, services, " ".join(refs) or None,
                                    None, None, "unreadable"))
            pending, names, services, refs, had_address = [], [], [], [], False
    return rows


def related_parties(pages):
    rows, seen_text, seen_filings = [], set(), set()
    for page in pages:
        on_page = set()
        for row in parse_related(page):
            if row["row_status"] is None:
                raw = " ".join(row["text"].casefold().split())
                filing = tuple(re.sub(r"\W+", "", (row[k] or "").casefold())
                               for k in ("name_guess", "description", "where"))
                key = filing + (row["cost_reported"], row["actual_cost_to_related_party"])
                if raw in seen_text or (all(filing) and key in seen_filings):
                    row["row_status"] = "duplicate"
                    row["category"] = None
                seen_text.add(raw)
                on_page.add(key)
            rows.append(row)
        seen_filings.update(on_page)
    return rows


def included_related(row):
    return not row.get("row_status") and row.get("category") != BALANCE_CATEGORY


def is_related_rent(row):
    # An entity's name (e.g. Bethel Realty) does not establish that a
    # payment for taxes, insurance or another service was rent.
    return included_related(row) and row.get("category") == RENT_CATEGORY and bool(
        re.search(r"\brent(?:als?)?\b|\bleas(?:e|ed|ing)\b", row.get("description") or "", re.I)
    )



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


def extract_related(pages):
    related_pages = pages.get("4", []) + pages.get("4A", [])
    return {"related_parties": related_parties(related_pages),
            "related_party_page_found": bool(related_pages)}


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
    e.update(extract_related(P))
    if "17" in P:
        e["management_services"] = [r for p in P["17"] for r in parse_management(p)]
    for k in ("partners_members", "directors_officers", "stockholders_10pct"):
        for r in e.get(k, []):
            n = r.get("name") or ""
            m = re.search(r"\s\d{1,6}\s+\w", n + " ")
            if m and m.start() > 3:
                r["address"] = (n[m.start():].strip() + " " + (r.get("address") or "")).strip()
                r["name"] = n[:m.start()].strip()
        e[k] = [r for r in e.get(k, []) if not re.match(r"^(of Shares|10% of Shares|Same as above|Name|N/?A)\b", r.get("name") or "", re.I)]
    return e


CATS = [
    # balances between related companies are not costs; checked first so "Due to/from Related / Realty" is not rent
    ("loans / interest / receivables", r"due\s*to|due\s*from|receivable|payable|intercompany|inter-company"),
    ("loans / interest / receivables", r"loan|interest|due to|due from|receivable|payable|intercompany|\bnote"),
    ("pharmacy / supplies", r"pharm|drug|supplies|medical supply|oxygen|\bOTC\b|\bRX\b"),
    ("insurance", r"insur"),
    ("rent / lease / real estate", r"\brent(?:als?)?\b|\bleas(?:e|ed|ing)\b|\brealty\b|real (estate|property)|property tax"),
    ("therapy", r"therap|rehab|\bPT\b|\bOT\b|speech patholog"),
    ("staffing / nursing agency", r"staffing|agency|nursing pool|staff pool|contract (?:RN|LPN|CNA)"),
    ("management / home office", r"manag|home office|shared expense|administrative serv|consult"),
    ("salaries / shared employees", r"salar|shared employ|payroll|benefit"),
    ("food / laundry / housekeeping", r"food|dietary|laundry|housekeep|linen"),
    ("lab / radiology / medical", r"radiolog|x-ray|laborator|diagnost|physician|medical director|hospice"),
]


def categorize(text):
    t = text or ""
    for name, rx in CATS:
        if re.search(rx, t, re.I):
            return name
    return "other"


def categorize_related(description, name):
    # The service is the evidence for what was paid. Use the company name
    # only when the service cell is blank or a generic pointer.
    category = categorize(description)
    if category != "other":
        return category
    if not description or re.fullmatch(r"(?:various|other|see attached)", description, re.I):
        return categorize(name)
    return "other"
