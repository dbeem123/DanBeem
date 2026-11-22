#!/usr/bin/env python3
"""Build data/ct_dss_review.json: what DSS's cost-report review changed and what Medicaid pays.

Sources (DSS Nursing Facility Rates & Census page, saved under X:\\DanBeem-Data\\DSS_Rates):
  - Quarterly data pulls (cost-report data with the home's own adjustments and the
    adjustments made in DSS's review): CY2024 and CY2025 in the wide layout
    (<line>, <line>_ProvAdj, <line>_MSLCAdj columns); CY2023 in the older layout with a
    long "Part 6-M&S Adjustments" sheet (reported value, adjusted value per line).
  - Annual rate letters (one Medicaid per diem per home): SFY 2025 and SFY 2026 PDFs.

DSS provider names are matched to CMS CCNs only through names already tied to a CCN by
the site's cost-report build (the PDF file names DSS publishes). No fuzzy matching: a
name that is not an exact normalized match is listed under `unmatched` for review.

Needs openpyxl and pdftotext (poppler). Usage:
  python scripts/build_ct_dss_review.py --src "X:/DanBeem-Data/DSS_Rates" \\
      --crosswalk dss_name_crosswalk.json --out data/ct_dss_review.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
from collections import defaultdict

PULLS = {  # cost year -> (file glob, layout)
    2023: ("*CY2023*.xlsx", "long"),
    2024: ("*CY2024*.xlsx", "wide"),
    2025: ("*CY2025*.xlsx", "wide"),
}
LETTERS = {  # state fiscal year -> (file glob, rate period)
    "SFY2025": ("SFY 2025*Rates*.pdf", "2024-07-01 to 2025-06-30"),
    "SFY2026": ("2025-26*Letters*.pdf", "2025-07-01 to 2026-06-30"),
}
PREFIX = "Expense_And_Revenue_"
MGMT = "Expense_And_Revenue_16_m12_Administrative_Management_Services"


def norm(s: str | None) -> str:
    s = str(s or "").upper().replace("&", " AND ")
    s = re.sub(r"[.,'’`\"()/-]", " ", s)
    s = re.sub(r"\b(INC|LLC|THE)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def one(src, pattern):
    hits = sorted(glob.glob(os.path.join(src, pattern)))
    return hits[-1] if hits else None


def line_label(col: str) -> dict:
    """'Expense_And_Revenue_16_m12_Administrative_Management_Services' -> page 16, line m12, readable name."""
    rest = col[len(PREFIX):] if col.startswith(PREFIX) else col
    m = re.match(r"(\d+)_([A-Za-z0-9]+)_(.+)$", rest)
    if not m:
        return {"line": None, "page": None, "name": rest.replace("_", " ")}
    page, line, name = m.groups()
    return {"page": int(page), "line": line, "name": name.replace("_", " ").replace("AAndG", "A&G").strip()}


def read_wide(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = defaultdict(dict)
    for ws in wb.worksheets:
        rows = ws.iter_rows(values_only=True)
        h = list(next(rows))
        for r in rows:
            if not r or not r[0] or (r[1] or "").strip() != "CCNH":
                continue
            out[r[0].strip()].update({h[i]: r[i] for i in range(3, len(h)) if h[i]})
    return out


def summarize_wide(rec):
    adj, prov_total = [], 0.0
    for col, v in rec.items():
        if not col.endswith("_MSLCAdj") or col.endswith("Hours_MSLCAdj") or not col.startswith(PREFIX) or "_30_" in col:
            continue
        base = col[: -len("_MSLCAdj")]
        if v:
            reported = rec.get(base) or 0
            provadj = rec.get(base + "_ProvAdj") or 0
            adj.append({**line_label(base), "reported": reported, "home_adjustment": provadj, "review_adjustment": v,
                        "after_review": reported + provadj + v})
    for col, v in rec.items():
        if col.endswith("_ProvAdj") and col.startswith(PREFIX) and "_30_" not in col and v:
            prov_total += v
    g = lambda k: rec.get(k) or 0  # noqa: E731
    gross = g("Expense_And_Revenue_30_I1a_Medicaid_Residents_CT_Only")
    allowance = g("Expense_And_Revenue_30_I1b_Medicaid_Room_And_Board_Contractual_Allowance")
    days = g("Resident_Stats_08_3B_Total_Number_Of_Days_Care_Medicaid_Connecticut")
    mg = g(MGMT)
    return {
        "medicaid_ct_days": days or None,
        "medicaid_revenue_gross": gross or None,
        "medicaid_contractual_allowance": allowance or None,
        "home_adjustments_total": round(prov_total, 2),
        "management_fee_reported": mg or None,
        "management_fee_home_adjustment": g(MGMT + "_ProvAdj") or 0,
        "management_fee_review_adjustment": g(MGMT + "_MSLCAdj") or 0,
    }, adj


def read_long(path):
    """CY2023 layout: Part 2 has days and Medicaid revenue; Part 6 lists each review adjustment."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    base = {}
    rows = wb["Part 2-E&R and Resident Stats"].iter_rows(values_only=True)
    h = list(next(rows))
    ix = {k: h.index(k) for k in ("Medicaid CT", "Res Room Board Care Rev Medicaid Res CT only", "Medicaid Room and Board Contractual Allowance")}
    for r in rows:
        if r and r[0] and (r[1] or "").strip() == "CCNH":
            base[r[0].strip()] = {k: r[i] for k, i in ix.items()}
    adjs = defaultdict(list)
    rows = wb["Part 6-M&S Adjustments"].iter_rows(values_only=True)
    next(rows)
    for r in rows:
        name, _end, amount, key, ptype, rown, _col, before, after = r[:9]
        if not name or ptype != "CCNH" or not amount or not str(key).startswith("Expense & Revenue"):
            continue
        m = re.match(r"Expense & Revenue-(\d+)-(.+)$", str(key))
        page, nm = (int(m.group(1)), m.group(2)) if m else (None, str(key))
        if page == 30:
            continue
        adjs[name.strip()].append({"page": page, "line": rown, "name": nm, "reported": before, "home_adjustment": None,
                                   "review_adjustment": amount, "after_review": after})
    return base, adjs


def parse_letters(path):
    txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout
    lines = txt.splitlines()
    out = {}
    for i, ln in enumerate(lines):
        m = re.search(r"Provider Number:\s*(\d+)", ln)
        if not m:
            continue
        name = lines[i - 1].strip()
        rate = None
        for j in range(i, min(i + 25, len(lines))):
            mm = re.search(r"\bCCNH\s+\$([\d,]+\.\d{2})", lines[j])
            if mm:
                rate = float(mm.group(1).replace(",", ""))
                break
        if name and rate is not None:
            out[name] = {"provider_number": m.group(1), "per_diem": rate}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--crosswalk", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    xw = {norm(k): v for k, v in json.load(open(a.crosswalk, encoding="utf-8")).items()}
    facilities, unmatched, sources = {}, defaultdict(list), []

    def ccn_for(name, where):
        hit = xw.get(norm(name))
        if hit and len(hit) == 1:
            return hit[0]
        unmatched[name].append(where + (" (name matches more than one CCN)" if hit else ""))
        return None

    for cy, (pat, layout) in PULLS.items():
        path = one(a.src, pat)
        if not path:
            continue
        sources.append({"title": f"DSS quarterly cost report data pull, cost year {cy}", "file": os.path.basename(path)})
        if layout == "wide":
            recs = read_wide(path)
            items = {n: summarize_wide(r) for n, r in recs.items()}
        else:
            base, adjs = read_long(path)
            items = {}
            for n in set(base) | set(adjs):
                b = base.get(n) or {}
                items[n] = ({"medicaid_ct_days": b.get("Medicaid CT") or None,
                             "medicaid_revenue_gross": b.get("Res Room Board Care Rev Medicaid Res CT only") or None,
                             "medicaid_contractual_allowance": b.get("Medicaid Room and Board Contractual Allowance") or None,
                             "home_adjustments_total": None, "management_fee_reported": None,
                             "management_fee_home_adjustment": None, "management_fee_review_adjustment": None},
                            adjs.get(n) or [])
                mg = [x for x in adjs.get(n) or [] if x["page"] == 16 and x["line"] == "m12"]
                if mg:
                    items[n][0]["management_fee_reported"] = mg[0]["reported"]
                    items[n][0]["management_fee_review_adjustment"] = mg[0]["review_adjustment"]
        for name, (s, adj) in items.items():
            ccn = ccn_for(name, f"cost year {cy} data pull")
            if not ccn:
                continue
            gross, allow, days = s["medicaid_revenue_gross"], s["medicaid_contractual_allowance"], s["medicaid_ct_days"]
            net = (gross or 0) + (allow or 0) if gross else None
            dec = sum(x["review_adjustment"] for x in adj if x["review_adjustment"] < 0)
            inc = sum(x["review_adjustment"] for x in adj if x["review_adjustment"] > 0)
            adj.sort(key=lambda x: -abs(x["review_adjustment"]))
            # A decrease matched by an equal increase on another line is a cost moved between lines, not removed.
            amounts = [round(x["review_adjustment"], 2) for x in adj]
            for x in adj:
                x["moved_between_lines"] = round(-x["review_adjustment"], 2) in amounts
            f = facilities.setdefault(ccn, {"dss_names": [], "years": {}, "rates": {}})
            if name not in f["dss_names"]:
                f["dss_names"].append(name)
            f["years"][str(cy)] = {
                **s,
                "medicaid_revenue_net": round(net, 2) if net is not None else None,
                "medicaid_revenue_net_per_medicaid_day": round(net / days, 2) if net and days else None,
                "review_adjustments_total": round(dec + inc, 2),
                "review_decreases": round(dec, 2),
                "review_increases": round(inc, 2),
                "review_adjusted_lines": len(adj),
                "largest_review_adjustments": [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in x.items()} for x in adj[:8]],
                "source": os.path.basename(path),
            }

    for sfy, (pat, period) in LETTERS.items():
        path = one(a.src, pat)
        if not path:
            continue
        sources.append({"title": f"DSS nursing facility rate letters, {sfy}", "file": os.path.basename(path), "rate_period": period})
        for name, r in parse_letters(path).items():
            ccn = ccn_for(name, f"{sfy} rate letter")
            if ccn:
                f = facilities.setdefault(ccn, {"dss_names": [], "years": {}, "rates": {}})
                f["rates"][sfy] = {"per_diem": r["per_diem"], "rate_period": period, "provider_number": r["provider_number"]}
                if name not in f["dss_names"]:
                    f["dss_names"].append(name)

    doc = {
        "schema_version": "ct-dss-review-1",
        "generated_at": dt.date.today().isoformat(),
        "sources": sources,
        "source_page": "https://portal.ct.gov/dss/health-and-home-care/medicaid-nursing-home-reimbursement/medicaid-nursing-home-reimbursement/nursing-facility-rates",
        "definitions": {
            "home_adjustment": "Amounts the home itself removed on its cost report (adjustment column), for example bad debt, pharmacy or occupational therapy that Medicaid does not cover.",
            "moved_between_lines": "True when a review decrease on one line is matched by an equal increase on another: the cost was reclassified, not removed.",
            "review_adjustment": "Changes made to the cost report in DSS's review (columns marked MSLC / M&S in DSS's data, DSS's cost-report review contractor). Negative removes cost from what DSS counts; positive adds it back. The data shows the change, not the reason.",
            "medicaid_revenue_net": "Connecticut Medicaid room, board and care revenue the home reported, minus its Medicaid contractual allowance: what the home recorded as due from Medicaid for the year.",
            "per_diem": "The Medicaid daily rate DSS set for the state fiscal year (July to June). Provisional: DSS can revise it after review or audit.",
        },
        "caveats": [
            "Review adjustments can still change after a field audit; these files are DSS's published data as of the pull date.",
            "Medicaid pays one daily rate per resident. It is not earmarked for particular costs, so these figures cannot show Medicaid dollars spent on a specific department.",
            "Cost years end September 30; rate years run July to June, so a cost year spans two rate years.",
        ],
        "facilities": dict(sorted(facilities.items())),
        "unmatched": {k: v for k, v in sorted(unmatched.items())},
    }
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"facilities": len(facilities), "unmatched": len(unmatched)}))


if __name__ == "__main__":
    main()
