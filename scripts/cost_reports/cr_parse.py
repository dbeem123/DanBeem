"""Parse DSS 'Annual Report of Long-Term Care Facility' text (pdftotext -layout or OCR) into structured pages.

Every form page carries a 'CSP-<n>' code. For each page we keep:
  - lines: [{label, nums:[(value, right_edge_x)], raw}]
  - columns: header tokens with their right-edge x positions
and we offer helpers that find a labelled line and read the value in a named column.
"""
import re

NUM = re.compile(r"\(?\$?\s?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?|\(?\$?\s?-?\d+(?:\.\d+)?\)?")


def to_num(tok):
    t = tok.replace("$", "").replace(",", "").replace(" ", "")
    neg = t.startswith("(") and t.endswith(")") or t.startswith("-")
    t = t.strip("()-")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def split_pages(text):
    pages = {}
    for p in text.split("\f"):
        m = re.search(r"\bCSP\s?-\s?(\d{1,2}[A-Za-z]?)\b", p[:600])
        if not m:
            continue
        code = m.group(1).upper().replace("L", "1") if re.fullmatch(r"\d+[lL]", m.group(1)) else m.group(1).upper()
        pages.setdefault(code, []).append(p)
    return pages


def number_tokens(line, start=0):
    out = []
    for m in NUM.finditer(line, start):
        tok = m.group(0)
        digits = re.sub(r"\D", "", tok)
        if not digits:
            continue
        out.append((to_num(tok), m.end(), tok))
    return out


ITEM = re.compile(r"^\s*(?:\*\s*)?((?:[A-Z]-?\d+[a-z]?\.?)|(?:\d{1,2}[a-z]?\.)|(?:[a-z]\.)|(?:[IVX]+\.)|(?:\d{1,2}[a-z]?\.?\s?[a-z]\.))\s")


def page_lines(p):
    """Return list of (label, nums, raw). The label is the text before the first number that follows
    some letters; leading item numbers like '3.' or 'b.' are kept in the label."""
    rows = []
    for raw in p.splitlines():
        if not raw.strip():
            continue
        # find where the label ends: first number token after at least one letter, ignoring item codes
        m_item = ITEM.match(raw)
        start = m_item.end() if m_item else 0
        nums = []
        for v, end, tok in number_tokens(raw, start):
            # skip numbers embedded inside words like 'A-13', 'Sec. I', '3A'
            s = end - len(tok)
            if s > 0 and (raw[s - 1].isalpha() or raw[s - 1] in "-/#"):
                continue
            if end < len(raw) and (raw[end].isalpha() or raw[end] in "/"):
                continue
            # item codes like "A-13" whose letter was read as a digit ("4-13"): not an amount
            if end + 1 < len(raw) and raw[end] == "-" and raw[end + 1].isdigit() and not nums:
                continue
            if tok.startswith("(") and not tok.endswith(")"):
                continue
            nums.append((v, end, tok))
        first = nums[0][1] - len(nums[0][2]) if nums else len(raw)
        label = raw[:first].strip(" .$:")
        rows.append({"label": label, "nums": nums, "raw": raw})
    return rows


def header_columns(p, keywords):
    """Find the header block and return {colname: right_edge_x} for the given ordered keywords.
    keywords: list of (name, regex). Searches the first 40 lines."""
    lines = p.splitlines()[:45]
    cols = {}
    for name, rx in keywords:
        best = None
        for ln in lines:
            for m in re.finditer(rx, ln):
                if best is None:
                    best = m.end()
        if best is not None:
            cols[name] = best
    return cols


def assign(nums, cols, slack=14):
    """Map numbers to the nearest column by right edge (numbers are right-aligned under headers)."""
    out = {}
    if not cols:
        return out
    items = sorted(cols.items(), key=lambda x: x[1])
    for v, end, tok in nums:
        best, dist = None, 1e9
        for name, x in items:
            d = abs(end - x)
            if d < dist:
                best, dist = name, d
        if dist <= slack + 12 and best not in out:
            out[best] = v
    return out


HDR_WORDS = re.compile(r"(\b(?:Total|CCNH|RHNS|Adjustment|Adjustments|Hours|Other|Home|Levels|Level|Amount|Allowable)\b|\(Specify\))")


def page_header(p, max_lines=45):
    """Pick the header line with the most column words; return ordered [(name, right_edge)].
    Money columns: Total, NH (combined 'CCNH / RHNS'), CCNH, RHNS, Other, RCH.
    Hours/Adjustment columns are named after the money column they follow, e.g. 'NH.Hours'.
    Repeated money columns (e.g. period sub-totals on page 8) get a numeric suffix."""
    best, best_n, best_i = None, 0, None
    lines = p.splitlines()
    for i, ln in enumerate(lines[:max_lines]):
        toks = [(m.group(1), m.start(), m.end()) for m in HDR_WORDS.finditer(ln)]
        if len(toks) > best_n:
            best, best_n, best_i = toks, len(toks), i
    if not best:
        return [], None
    # merge 'CCNH / RHNS'
    merged = []
    for w, s0, e0 in best:
        if w == "RHNS" and merged and merged[-1][0] == "CCNH" and s0 - merged[-1][2] <= 6:
            merged[-1] = ("NH", merged[-1][1], e0)
        else:
            merged.append((w, s0, e0))
    # Old forms put 'CCNH /' on the line above 'RHNS' (combined column): detect by looking above.
    if best_i:
        above = " ".join(lines[max(0, best_i - 2):best_i])
        if re.search(r"CCNH\s*/", above) and not any(w in ("CCNH", "NH") for w, _, _ in merged):
            merged = [("NH", s0, e0) if w == "RHNS" and k == [x[0] for x in merged].index("RHNS") else (w, s0, e0)
                      for k, (w, s0, e0) in enumerate(merged)]
    names, seen, last_money = [], {}, None
    for w, s0, e0 in merged:
        w = {"Levels": "Total", "Level": "NH", "Home": "RCH", "Adjustments": "Adjustment", "(Specify)": "Other"}.get(w, w)
        if w in ("Hours", "Adjustment", "Amount", "Allowable"):
            name = f"{last_money}.{w}" if last_money else w
        else:
            last_money = w
            name = w
        seen[name] = seen.get(name, 0) + 1
        if seen[name] > 1:
            name = f"{name}#{seen[name]}"
            if "." not in name.split("#")[0]:
                last_money = name
        names.append((name, (s0 + e0) / 2 if ALIGN == "center" else e0))
    return names, best_i


# "right": numbers line up with the right edge of their header word (text reports).
# "center": OCR'd scans, where the header word is centred over its column.
ALIGN = "right"


def read_cols(row, header, tol=10):
    out = {}
    for v, end, tok in row["nums"]:
        best, dist = None, 1e9
        pos = end - len(tok.strip()) / 2 if ALIGN == "center" else end
        for name, x in header:
            d = abs(pos - x)
            if d < dist:
                best, dist = name, d
        if best is not None and dist <= tol and best not in out:
            out[best] = v
    return out


def nh_value(vals, header=None):
    """Nursing-home value: combined CCNH/RHNS column, else CCNH + RHNS, else None.
    Old page 8 headers read 'Total CCNH Level' / 'Total RHNS Level' -> columns NH and NH#2 before Total#2."""
    if not vals:
        return None
    if header and [n for n, _ in header][:3] == ["Total", "NH", "NH#2"]:
        if "NH" in vals or "NH#2" in vals:
            return (vals.get("NH") or 0) + (vals.get("NH#2") or 0)
    if "NH" in vals:
        return vals["NH"]
    # OCR'd 2023 forms: the amount can sit nearer the Adjustment header than the CCNH/RHNS one.
    # An adjustment with hours but no amount is not a real row, so read it as the amount.
    if ALIGN != "right" and "NH.Adjustment" in vals and "NH.Hours" in vals:
        return vals["NH.Adjustment"]
    if "CCNH" in vals or "RHNS" in vals:
        return (vals.get("CCNH") or 0) + (vals.get("RHNS") or 0)
    return None


def nh_hours(vals):
    if not vals:
        return None
    if "NH.Hours" in vals:
        return vals["NH.Hours"]
    if "CCNH.Hours" in vals or "RHNS.Hours" in vals:
        return (vals.get("CCNH.Hours") or 0) + (vals.get("RHNS.Hours") or 0)
    return vals.get("Hours")
