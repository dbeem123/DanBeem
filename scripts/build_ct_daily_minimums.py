"""Compare every reported Connecticut facility-day to the staffing minimum in force that day, and flag anomalies.

Reads the daily PBJ files built by build_ct_daily_staffing.py (data/ct_daily_staffing/<quarter>/<ccn>.json.gz) and the
rule timeline in data/ct_staffing_minimum_rules.json. Writes data/ct_daily_minimums/index.json and one
<quarter>.json.gz per quarter. Deterministic; no network.

Day entry in the daily files: [census, workers_total, entries], entries in ROLE order, each [total, emp, ctr, workers, excluded].
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAILY = ROOT / "data/ct_daily_staffing"
RULES = ROOT / "data/ct_staffing_minimum_rules.json"
OUT = ROOT / "data/ct_daily_minimums"

# Positions of the eight nursing roles in each day's entries (same order as build_ct_daily_staffing.ROLE_ROWS).
DON, RN_ADMIN, RN, LPN_ADMIN, LPN, CNA, NAT, MED_AIDE = range(8)
NURSING = range(8)
DIRECT = (RN, LPN, CNA, NAT, MED_AIDE)          # leaves out the DON and nurses with administrative duties
LICENSED = (DON, RN_ADMIN, RN, LPN_ADMIN, LPN)
AIDES = (CNA, NAT, MED_AIDE)
RN_ON_DUTY = (RN_ADMIN, RN)                      # RN hours toward the federal 8-hour rule; the DON is left out

FLAGS = {
    "below_total": (1, "Below the Connecticut total minimum (all nursing hours counted)"),
    "below_direct_only": (2, "Meets the total only if the director of nursing and administrative nurses count"),
    "below_licensed": (4, "Below the licensed-nurse minimum (0.84)"),
    "below_aide": (8, "Below the nurse-aide minimum (2.16, March 2023 - January 2024 policy)"),
    "rn_under_8": (16, "Fewer than 8 RN hours that day (federal RN-on-duty indicator)"),
    "low_outlier": (32, "Nursing hours per resident at least 25% below this home's median for the quarter"),
    "census_jump": (64, "Census changed by more than 15% (and at least 5 residents) from the previous reported day"),
    "long_hours": (128, "More than 12 nursing hours per nursing worker (long or double shifts)"),
    "high_contract": (256, "More than half of nursing hours from contract staff"),
    "not_evaluated": (512, "Census of zero or nursing hours missing or flagged by CMS; not compared"),
    "implausible": (1024, "Under 1.0 nursing hours per resident: likely a reporting error, so not counted as below the minimum"),
}
# This site's screening rule, not a CMS rule: a staffed nursing home cannot run below about 1 nursing hour per resident day,
# so such days are treated as incomplete payroll reporting rather than as short staffing.
IMPLAUSIBLE_HPRD = 1.0
SHORT = {'below_total': 'Below minimum', 'below_direct_only': 'Meets only with admin nurses', 'below_licensed': 'Licensed below 0.84', 'below_aide': 'Aides below 2.16', 'rn_under_8': 'Under 8 RN hours', 'low_outlier': '25%+ below usual', 'census_jump': 'Census jump', 'long_hours': 'Over 12 hrs per worker', 'high_contract': 'Mostly contract', 'not_evaluated': 'Not compared', 'implausible': 'Likely reporting error'}
BIT = {name: bit for name, (bit, _) in FLAGS.items()}


def load_rules(path: Path = RULES) -> dict:
    rules = json.loads(path.read_text(encoding="utf-8"))
    for p in rules["periods"]:
        p["_from"], p["_to"] = dt.date.fromisoformat(p["from"]), dt.date.fromisoformat(p["to"])
    return rules


def rule_for(rules: dict, day: dt.date) -> dict | None:
    for p in rules["periods"]:
        if p["_from"] <= day <= p["_to"]:
            return p
    return None


def parse_day(key: str) -> dt.date:
    return dt.date(int(key[:4]), int(key[4:6]), int(key[6:]))


def hours(entries, roles) -> float:
    return sum(entries[i][0] for i in roles)


def evaluate_day(key: str, record, rules: dict) -> dict:
    """Numbers and rule flags for one facility-day (anomaly flags that need context are added later)."""
    census, _, entries = record
    day = parse_day(key)
    out = {"date": key, "census": census, "flags": 0, "rule": None}
    nursing = entries[:8]
    usable = bool(census) and all(e[0] is not None and not e[4] for e in nursing)
    if not usable:
        out["flags"] |= BIT["not_evaluated"]
        return out
    all_h, direct_h = hours(nursing, NURSING), hours(nursing, DIRECT)
    lic_h, aide_h, rn_h = hours(nursing, LICENSED), hours(nursing, AIDES), hours(nursing, RN_ON_DUTY)
    contract = sum((e[2] or 0) for e in nursing)
    workers = [e[3] for e in nursing]
    nurse_workers = sum(w for w in workers if w) if all(w is not None for w in workers) else None
    out.update(
        all=all_h / census, direct=direct_h / census, licensed=lic_h / census, aide=aide_h / census,
        rn_hours=rn_h, contract_share=(contract / all_h) if all_h else 0.0,
        hours_per_worker=(all_h / nurse_workers) if nurse_workers else None,
    )
    if out["all"] < IMPLAUSIBLE_HPRD:
        out["flags"] |= BIT["implausible"]
        return out
    rule = rule_for(rules, day)
    if rule:
        out["rule"] = rule["id"]
        eps = 1e-9
        if out["all"] < rule["total"] - eps:
            out["flags"] |= BIT["below_total"]
        elif out["direct"] < rule["total"] - eps:
            out["flags"] |= BIT["below_direct_only"]
        if rule.get("licensed") is not None and out["licensed"] < rule["licensed"] - eps:
            out["flags"] |= BIT["below_licensed"]
        if rule.get("aide") is not None and out["aide"] < rule["aide"] - eps:
            out["flags"] |= BIT["below_aide"]
    if rn_h < rules["federal"]["rn_daily_hours"]:
        out["flags"] |= BIT["rn_under_8"]
    if out["hours_per_worker"] is not None and out["hours_per_worker"] > 12:
        out["flags"] |= BIT["long_hours"]
    if out["contract_share"] > 0.5:
        out["flags"] |= BIT["high_contract"]
    return out


def add_context_flags(days: list[dict]) -> None:
    """Flags that compare a day with the rest of the home's quarter."""
    rated = [d["all"] for d in days if "all" in d and not d["flags"] & BIT["implausible"]]
    median = statistics.median(rated) if rated else None
    previous = None
    for d in days:
        if median and "all" in d and not d["flags"] & BIT["implausible"] and d["all"] < 0.75 * median:
            d["flags"] |= BIT["low_outlier"]
        if d["census"]:
            if previous and abs(d["census"] - previous) >= 5 and abs(d["census"] - previous) / previous > 0.15:
                d["flags"] |= BIT["census_jump"]
            previous = d["census"]


def summarize(days: list[dict]) -> dict:
    rated = [d for d in days if "all" in d and not d["flags"] & BIT["implausible"]]
    count = lambda name: sum(1 for d in days if d["flags"] & BIT[name])
    weekday = [d["all"] for d in rated if parse_day(d["date"]).weekday() < 5]
    weekend = [d["all"] for d in rated if parse_day(d["date"]).weekday() >= 5]
    s = {
        "days": len(days), "evaluated": len(rated),
        **{name: count(name) for name in FLAGS},
        "mean_hprd": round(statistics.fmean(d["all"] for d in rated), 3) if rated else None,
        "min_hprd": round(min(d["all"] for d in rated), 3) if rated else None,
        "weekday_hprd": round(statistics.fmean(weekday), 3) if weekday else None,
        "weekend_hprd": round(statistics.fmean(weekend), 3) if weekend else None,
    }
    s["weekend_gap"] = round(1 - s["weekend_hprd"] / s["weekday_hprd"], 3) if weekday and weekend and s["weekday_hprd"] else None
    worst = min(rated, key=lambda d: d["all"], default=None)
    s["worst_day"] = worst["date"] if worst else None
    s["share_below"] = round(s["below_total"] / len(rated), 3) if rated else None
    reported = sum(1 for d in days if "all" in d)
    s["suspect_reporting"] = bool(reported) and s["implausible"] > reported / 2
    return s


def pack_day(d: dict) -> list:
    r = lambda v, n=2: None if v is None else round(v, n)
    if "all" not in d:
        return [d["date"], d["census"], None, None, None, None, None, None, None, d["flags"]]
    return [d["date"], d["census"], r(d["all"]), r(d["direct"]), r(d["licensed"]), r(d["aide"]), r(d["rn_hours"], 1),
            r(d["contract_share"]), r(d["hours_per_worker"], 1), d["flags"]]


def facility_names(root: Path) -> dict:
    names = {}
    current = root / "data/nursing_home_staffing_ct.json"
    if current.exists():
        for f in json.loads(current.read_text(encoding="utf-8"))["facilities"]:
            names[f["ccn"]] = f.get("provider_name") or f.get("pbj_provider_name")
    catalog = json.loads((root / "data/ct_daily_staffing/index.json").read_text(encoding="utf-8"))
    for ccn, name in catalog.get("historical_homes", {}).items():
        names.setdefault(ccn, name)
    return names


def build(root: Path = ROOT, out: Path = OUT, quarters: list[str] | None = None) -> dict:
    rules = load_rules(root / "data/ct_staffing_minimum_rules.json")
    catalog = json.loads((root / "data/ct_daily_staffing/index.json").read_text(encoding="utf-8"))
    names = facility_names(root)
    out.mkdir(parents=True, exist_ok=True)
    index = {
        "generated_from": "data/ct_daily_staffing (CMS PBJ daily nurse staffing) and data/ct_staffing_minimum_rules.json",
        "day_fields": ["date", "census", "all_nursing_hprd", "direct_care_hprd", "licensed_hprd", "aide_hprd",
                       "rn_hours", "contract_share", "hours_per_nursing_worker", "flags"],
        "flags": {name: {"bit": bit, "label": label, "short": SHORT[name]} for name, (bit, label) in FLAGS.items()},
        "names": {}, "quarters": {},
    }
    for q in quarters or sorted(catalog["quarters"]):
        folder = root / "data/ct_daily_staffing" / q
        if not folder.is_dir():
            continue
        facilities, state = {}, {name: 0 for name in FLAGS}
        state.update(days=0, evaluated=0, homes=0, homes_with_short_days=0, homes_suspect_reporting=0)
        for path in sorted(folder.glob("*.json.gz")):
            ccn = path.name.split(".")[0]
            daily = json.loads(gzip.decompress(path.read_bytes()))
            days = [evaluate_day(k, daily[k], rules) for k in sorted(daily)]
            add_context_flags(days)
            summary = summarize(days)
            facilities[ccn] = {"summary": summary, "days": [pack_day(d) for d in days]}
            index["names"].setdefault(ccn, names.get(ccn, ccn))
            state["homes"] += 1
            state["homes_with_short_days"] += 1 if summary["below_total"] else 0
            state["homes_suspect_reporting"] += 1 if summary["suspect_reporting"] else 0
            for key in list(FLAGS) + ["days", "evaluated"]:
                state[key] += summary[key]
        payload = json.dumps({"quarter": q, "facilities": facilities}, separators=(",", ":")).encode()
        (out / f"{q}.json.gz").write_bytes(gzip.compress(payload, mtime=0))
        index["quarters"][q] = state
    (out / "index.json").write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("quarters", nargs="*")
    args = parser.parse_args()
    result = build(out=args.out, quarters=args.quarters or None)
    for q, s in result["quarters"].items():
        print(q, f"homes={s['homes']} days={s['evaluated']}/{s['days']} below_total={s['below_total']} implausible={s['implausible']} suspect_homes={s['homes_suspect_reporting']} rn_under_8={s['rn_under_8']}")
