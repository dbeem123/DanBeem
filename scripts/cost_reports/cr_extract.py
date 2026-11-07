"""Extract figures from one DSS annual cost report (text) into a flat record + validation checks."""
import re
from cr_parse import split_pages, page_lines, page_header, read_cols, nh_value, nh_hours


def labelled_rows(page):
    """Yield (full_label, row) for rows with numbers; label includes preceding number-less lines
    since the last numbered row (multi-line item labels)."""
    rows = page_lines(page)
    pend = []
    out = []
    for r in rows:
        if r["nums"]:
            full = " ".join(pend + [r["label"]])
            out.append((" ".join(full.split()), r))
            pend = []
        else:
            if re.match(r"^\s*(State of Connecticut|Annual Report|CSP-|Name of Facility|\*)", r["raw"]):
                pend = []
                continue
            if re.match(r"^\s*(\*\s*)?([A-Z]-?\d+[a-z]?\.?|\d{1,2}[a-zA-Z]?\.|[a-zA-Z]\.|[IVX]+\.)\s", r["raw"]):
                pend = [r["label"]]
            else:
                pend = (pend + [r["label"]])[-3:]
    return out


def find(pages, code, pattern, col="NH", nth=0, within=None, fallback=("Total",)):
    """Value in column `col` of the nth row on page `code` whose full label matches `pattern`.
    `within` = (start_regex, end_regex) to restrict to a block of rows."""
    for page in pages.get(code, []):
        header, hi = page_header(page)
        rows = labelled_rows(page)
        active = within is None
        hits = []
        for lab, r in rows:
            if within:
                if re.search(within[0], lab, re.I) or re.search(within[0], r["raw"], re.I):
                    active = True
                elif active and within[1] and re.search(within[1], r["raw"], re.I):
                    active = False
            own = r["label"]
            cont = not re.match(r"^\s*(\*\s*)?([A-Z]-?\d+[a-z]?\.?|\d{1,2}[a-zA-Z]?\.|[a-zA-Z]\.|[IVX]+\.)\s", own) and (own[:1].islower() or own[:1] in "(" or own.startswith("of ") or not own)
            target = lab if cont else own
            if active and re.search(pattern, target, re.I):
                hits.append(r)
        if len(hits) > nth:
            vals = read_cols(hits[nth], header)
            vals["_hours"] = nh_hours(vals)
            for c in (col,) + tuple(fallback):
                v = nh_value(vals, header) if c == "NH" else vals.get(c)
                if v is not None:
                    return v, vals
            return None, vals
    return None, None


def block_value(pages, code, block_rx, item_rx, col="NH"):
    """For page 10/13: read an item inside a block that begins at a header row (e.g. 'b. RN')."""
    for page in pages.get(code, []):
        header, hi = page_header(page)
        lines = page.splitlines()
        rows = page_lines(page)
        in_block = False
        for r in rows:
            raw = r["raw"]
            if re.search(block_rx, raw):
                in_block = True
                if not r["nums"]:
                    continue
            elif in_block and re.match(r"^\s*[a-z]\.\s", raw) and not re.search(block_rx, raw):
                in_block = False
            if in_block and re.search(item_rx, raw, re.I) and r["nums"]:
                v = read_cols(r, header)
                v["_hours"] = nh_hours(v)
                return (nh_value(v, header) if col == "NH" else v.get(col)), v
    return None, None


def extract(text):
    P = split_pages(text)
    rec, notes = {}, []

    def put(key, val):
        rec[key] = val

    # ---- resident statistics (CSP-8): CCNH/RHNS column ----
    put("beds_certified", find(P, "8", r"On last day of THIS", nth=0)[0])
    put("residents_end", find(P, "8", r"(As of midnight|midnight) of THIS", nth=0)[0])
    put("days_medicare", find(P, "8", r"^A\.?\s*Medicare\b|^Medicare\b")[0])
    put("days_medicaid_ct", find(P, "8", r"Medicaid \(Conn")[0])
    put("days_medicaid_other_states", find(P, "8", r"Medicaid \(other")[0])
    put("days_private", find(P, "8", r"Private Pay")[0])
    put("days_other_payer", find(P, "8", r"^F\.?\s*Other|Other \(Specify")[0])
    put("days_total_care", find(P, "8", r"Total Care Days")[0])
    put("days_bed_reserve_medicaid", find(P, "8", r"Medicaid Bed Reserve")[0])
    put("resident_days_total", find(P, "8", r"Total Resident Days")[0])

    # ---- salaries (CSP-10): CCNH/RHNS column + hours ----
    def sal(pat, **kw):
        v, cols = find(P, "10", pat, **kw)
        return v, (cols or {}).get("_hours")
    rec["sal_owners"], _ = sal(r"Operators/Owners")
    rec["sal_administrator"], _ = sal(r"Administrator\(s\)")
    rec["sal_asst_administrator"], _ = sal(r"Assistant Administrator")
    rec["sal_don"], rec["hrs_don"] = sal(r"Director.{0,20}of Nurs")
    for blk, key in ((r"^\s*b\.\s*RN\b|\bb\.\s*R\.?N\.?\s*$", "rn"), (r"^\s*c\.\s*LPN\b|\bc\.\s*L\.?P\.?N\.?\s*$", "lpn")):
        v, c = block_value(P, "10", blk, r"Direct Care")
        rec[f"sal_{key}_direct"], rec[f"hrs_{key}_direct"] = v, (c or {}).get("_hours")
        v, c = block_value(P, "10", blk, r"Administrative")
        rec[f"sal_{key}_admin"], rec[f"hrs_{key}_admin"] = v, (c or {}).get("_hours")
    rec["sal_aides"], rec["hrs_aides"] = sal(r"Aides and Attendants")
    rec["sal_total"], rec["hrs_total"] = sal(r"Total Salary Expenditures")

    # ---- professional fees (CSP-13): nursing pool / agency ----
    for blk, key in ((r"^\s*a\.\s*RN\b", "rn"), (r"^\s*b\.\s*LPN\b", "lpn")):
        v, c = block_value(P, "13", blk, r"Direct Care")
        rec[f"pool_{key}_direct"], rec[f"pool_hrs_{key}_direct"] = v, (c or {}).get("_hours")
        v, c = block_value(P, "13", blk, r"Administrative")
        rec[f"pool_{key}_admin"] = v
    v, c = find(P, "13", r"^c\.\s*Aides\b")
    rec["pool_aides"], rec["pool_hrs_aides"] = v, (c or {}).get("_hours")
    rec["prof_fees_total"] = find(P, "13", r"Total Fees Paid")[0]

    # ---- fringe benefits (CSP-15 1a) ----
    fr = {}
    for k, pat in (("workers_comp", r"Work(men|ers).{0,3}s? Comp"), ("disability", r"Disability Insurance"),
                   ("unemployment", r"Unemployment"), ("fica", r"Social Security|F\.I\.C\.A"),
                   ("health", r"Health Insurance"), ("life", r"Life Insurance"), ("pension", r"Pensions \(Non"),
                   ("uniform", r"Uniform"), ("other", r"^9\.?\s*Other")):
        fr[k] = find(P, "15", pat)[0]
    rec.update({f"fringe_{k}": v for k, v in fr.items()})
    rec["fringe_total"] = sum(v for v in fr.values() if v) or None

    # ---- A&G, management (CSP-16, CSP-17) ----
    rec["mgmt_fee_m12"] = find(P, "16", r"Administrative Management Services")[0]
    rec["mgmt_fee_m12_total_col"] = find(P, "16", r"Administrative Management Services", col="Total")[0]
    rec["ag_total"] = find(P, "16", r"Total Administrative (&|and) General")[0]

    # ---- category totals ----
    rec["dietary_total"] = find(P, "18", r"Total Dietary")[0]
    rec["laundry_total"] = find(P, "19", r"Total Laundry")[0]
    rec["housekeeping_total"] = find(P, "20", r"Total Housekeeping")[0]
    rec["resident_care_total"] = find(P, "20", r"Total Resident Care")[0]
    rec["maint_operating_total"] = find(P, "22", r"Total Maint")[0]
    rec["property_total"] = find(P, "22", r"Total Property")[0]
    rec["interest_total"] = find(P, "27", r"Total All Interest")[0]
    rec["insurance_total"] = find(P, "27", r"Total Insurance")[0]
    rec["expenses_total_ccnh"] = find(P, "27", r"Total All Expenditures")[0]
    rec["expenses_total_all"] = find(P, "27", r"Total All Expenditures", col="Total")[0]

    # ---- revenue (CSP-30) ----
    for k, pat in (("rev_medicaid_ct", r"Medicaid Residents"), ("rev_medicare", r"Medicare Residents"),
                   ("rev_private", r"Private-?\s?Pay Residents"), ("rev_resident_total", r"Total Resident Revenue"),
                   ("rev_other_total", r"Total Other Revenue"), ("rev_total", r"Total All Revenue")):
        rec[k] = find(P, "30", pat)[0]
        rec[k + "_all"] = find(P, "30", pat, col="Total")[0]

    # ---- balance sheet & net income (CSP-31..36): single Total column ----
    def tot(code, pat):
        for c in ("Total", "NH"):
            v = find(P, code, pat, col=c, fallback=())[0]
            if v is not None:
                return v
        # single-column pages: take last number on the line
        for page in P.get(code, []):
            for lab, r in labelled_rows(page):
                if re.search(pat, lab, re.I) and r["nums"]:
                    return r["nums"][-1][0]
        return None
    rec["assets_current"] = tot("31", r"Total Current Assets")
    rec["assets_total"] = tot("32", r"Total All Assets")
    rec["liabilities_current"] = tot("33", r"Total Current Liabilities")
    rec["liabilities_long_term"] = tot("34", r"Total Long-?Term Liabilities")
    rec["liabilities_total"] = tot("34", r"Total All Liabilities")
    rec["net_worth"] = tot("35", r"Total Net Worth")
    rec["revenue_total_p36"] = tot("36", r"Total Revenue")
    rec["expenses_total_p36"] = tot("36", r"Total Expenditures")
    rec["net_income_p36"] = tot("36", r"Net Income")

    # Page 36 repeats whole-facility revenue and expense totals. When page 27 or 30's total line could not be
    # read (mostly scanned reports), use page 36, but only for the nursing-home column when the other page shows
    # the facility is nursing-home only (its nursing-home column equals its all-levels total).
    filled = []
    nh_only = ((rec.get("rev_total") and rec.get("rev_total") == rec.get("rev_total_all"))
               or (rec.get("expenses_total_ccnh") and rec.get("expenses_total_ccnh") == rec.get("expenses_total_all")))
    if rec.get("expenses_total_all") is None and rec.get("expenses_total_p36"):
        rec["expenses_total_all"] = rec["expenses_total_p36"]; filled.append("expenses_total_all")
        if rec.get("expenses_total_ccnh") is None and nh_only:
            rec["expenses_total_ccnh"] = rec["expenses_total_p36"]; filled.append("expenses_total_ccnh")
    if rec.get("rev_total_all") is None and rec.get("revenue_total_p36"):
        rec["rev_total_all"] = rec["revenue_total_p36"]; filled.append("rev_total_all")
        if rec.get("rev_total") is None and nh_only:
            rec["rev_total"] = rec["revenue_total_p36"]; filled.append("rev_total")
    rec["filled_from_p36"] = filled or None

    return rec, P


def derive(rec):
    """Direct-care figures following the DSS rate-setting definition (2024 guide book):
    Direct = nursing and nurse aide personnel salaries, related fringe benefits, and nursing pool costs."""
    g = lambda k: rec.get(k) or 0
    d = {}
    d["direct_salaries"] = g("sal_don") + g("sal_rn_direct") + g("sal_rn_admin") + g("sal_lpn_direct") + g("sal_lpn_admin") + g("sal_aides")
    d["hands_on_salaries"] = g("sal_rn_direct") + g("sal_lpn_direct") + g("sal_aides")
    d["nursing_pool"] = g("pool_rn_direct") + g("pool_rn_admin") + g("pool_lpn_direct") + g("pool_lpn_admin") + g("pool_aides")
    share = (d["direct_salaries"] / rec["sal_total"]) if rec.get("sal_total") else None
    d["direct_fringe_allocated"] = round(rec["fringe_total"] * share) if share and rec.get("fringe_total") else None
    d["direct_care_total"] = d["direct_salaries"] + d["nursing_pool"] + (d["direct_fringe_allocated"] or 0)
    days = rec.get("resident_days_total") or rec.get("days_total_care")
    if days:
        d["direct_care_per_resident_day"] = round(d["direct_care_total"] / days, 2)
        if rec.get("expenses_total_ccnh"):
            d["expenses_per_resident_day"] = round(rec["expenses_total_ccnh"] / days, 2)
    if rec.get("expenses_total_ccnh"):
        d["direct_care_share_of_expenses"] = round(d["direct_care_total"] / rec["expenses_total_ccnh"], 4)
    hrs = sum(rec.get(k) or 0 for k in ("hrs_don", "hrs_rn_direct", "hrs_rn_admin", "hrs_lpn_direct", "hrs_lpn_admin", "hrs_aides",
                                          "pool_hrs_rn_direct", "pool_hrs_lpn_direct", "pool_hrs_aides"))
    d["nursing_hours_reported"] = hrs or None
    if hrs and days:
        d["nursing_hours_per_resident_day"] = round(hrs / days, 3)
    if hrs and d["direct_care_total"]:
        d["direct_care_cost_per_nursing_hour"] = round(d["direct_care_total"] / hrs, 2)
    payer = {k: rec.get(k) for k in ("days_medicaid_ct", "days_medicare", "days_private", "days_other_payer", "days_medicaid_other_states")}
    tc = rec.get("days_total_care")
    if tc:
        d["payer_mix"] = {k.replace("days_", ""): round((v or 0) / tc, 4) for k, v in payer.items()}
    return d


def checks(rec):
    """Internal consistency checks: printed totals vs sums of parts."""
    c = {}
    parts = [rec.get(k) for k in ("days_medicare", "days_medicaid_ct", "days_medicaid_other_states", "days_private", "days_other_payer")]
    if rec.get("days_total_care") and any(parts):
        s = sum(p or 0 for p in parts)
        c["days_sum"] = abs(s - rec["days_total_care"]) <= 2
    if rec.get("assets_total") and rec.get("liabilities_total") is not None and rec.get("net_worth") is not None:
        pass
    if rec.get("rev_total") and rec.get("rev_resident_total") is not None and rec.get("rev_other_total") is not None:
        c["revenue_sum"] = abs(rec["rev_resident_total"] + rec["rev_other_total"] - rec["rev_total"]) <= 2
    if rec.get("liabilities_total") and rec.get("liabilities_current") is not None and rec.get("liabilities_long_term") is not None:
        c["liabilities_sum"] = abs(rec["liabilities_current"] + rec["liabilities_long_term"] - rec["liabilities_total"]) <= 2
    c["has_core"] = all(rec.get(k) for k in ("resident_days_total", "sal_total", "expenses_total_ccnh", "rev_total"))
    return c
