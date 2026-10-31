"""Build a candidate CT DPH license -> CMS CCN crosswalk for review.

Inputs
- DPH facility master CSV (Chronic_and_Convalescent_Nursing_Home.csv): FACILITY NAME, ADDRESS,
  CITY, STATE, ZIP, LICENSE NO., STATUS, EFFECTIVE DATE, EXPIRATION DATE. Place it under
  source_data/ct_dph/ (gitignored) and pass --dph.
- CMS side: data/nursing_home_staffing_ct.json facilities (CCN, name, address, city, ZIP).

Output (default data/testing/, gitignored): every DPH license with its best CMS candidate,
the evidence, a score and a match tier. Nothing here is public until a person reviews it.

Tiers
- auto_high: same street number and normalized street, same ZIP or city, and name similarity >= 0.35
- likely: same street number + street OR (same city/ZIP and name similarity >= 0.6)
- review: some evidence but below "likely"
- unmatched: no candidate with meaningful evidence
Each CCN is assigned to at most one license (best score wins); losers drop to review.
Facility data only: no person fields are read or written.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CMS = ROOT / "data" / "nursing_home_staffing_ct.json"
DEFAULT_DPH = ROOT / "source_data" / "ct_dph" / "Chronic_and_Convalescent_Nursing_Home.csv"
DEFAULT_OUT = ROOT / "data" / "testing" / "ct_dph_ccn_crosswalk_candidate.json"

STREET_WORDS = {
    "STREET": "ST", "ROAD": "RD", "AVENUE": "AVE", "AV": "AVE", "DRIVE": "DR", "LANE": "LN",
    "BOULEVARD": "BLVD", "PLACE": "PL", "COURT": "CT", "TURNPIKE": "TPKE", "TPK": "TPKE",
    "HIGHWAY": "HWY", "PARKWAY": "PKWY", "TERRACE": "TER", "CIRCLE": "CIR", "SQUARE": "SQ",
    "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W", "MOUNT": "MT", "SAINT": "ST",
    "ROUTE": "RTE", "EXTENSION": "EXT", "HILL": "HL",
}
NAME_STOP = {
    "THE", "OF", "AND", "AT", "INC", "LLC", "CENTER", "CTR", "HEALTH", "HEALTHCARE", "CARE",
    "REHABILITATION", "REHAB", "NURSING", "HOME", "FACILITY", "SKILLED", "CONVALESCENT",
    "LIVING", "COMMUNITY", "FOR", "A", "AN", "RESIDENCE", "MANOR",
}
SUITE_RE = re.compile(r"\b(SUITE|STE|UNIT|BLDG|BUILDING|APT|FLOOR|FL)\b.*$")


def _clean(text: str) -> str:
    text = (text or "").upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    return " ".join(text.split())


def normalize_zip(value: str) -> str:
    # Some CT DPH exports type the letter O for zero (e.g. "O6897").
    digits = re.sub(r"[^0-9]", "", (value or "").upper().replace("O", "0"))
    return digits[:5].zfill(5) if digits else ""


def normalize_address(value: str) -> tuple[str, str]:
    """Return (street number, normalized street) for the first address line."""
    text = SUITE_RE.sub("", _clean(value)).strip()
    words = [STREET_WORDS.get(w, w) for w in text.split()]
    number = ""
    if words and re.fullmatch(r"\d+[A-Z]?", words[0]):
        number = re.sub(r"[A-Z]$", "", words[0])
        words = words[1:]
    return number, " ".join(words)


def name_tokens(value: str) -> set[str]:
    return {w for w in _clean(value).split() if w not in NAME_STOP and len(w) > 1}


def name_similarity(a: str, b: str) -> float:
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return 0.0
    return round(len(ta & tb) / len(ta | tb), 3)


def normalize_license(value: str) -> str:
    digits = re.sub(r"[^0-9]", "", value or "")
    return digits.lstrip("0") or ("0" if digits else "")


def score_pair(dph: dict, cms: dict) -> dict:
    d_num, d_street = normalize_address(dph["address"])
    c_num, c_street = normalize_address(cms["address"])
    same_number = bool(d_num) and d_num == c_num
    same_street = bool(d_street) and d_street == c_street
    street_overlap = bool(d_street and c_street) and (d_street in c_street or c_street in d_street)
    same_zip = bool(dph["zip"]) and dph["zip"] == cms["zip"]
    same_city = _clean(dph["city"]) == _clean(cms["city"])
    name_sim = name_similarity(dph["name"], cms["name"])
    score = (
        (0.35 if same_number else 0)
        + (0.20 if same_street else (0.10 if street_overlap else 0))
        + (0.10 if same_zip else 0)
        + (0.10 if same_city else 0)
        + 0.25 * name_sim
    )
    address_match = same_number and (same_street or street_overlap)
    place_match = same_zip or same_city
    if address_match and place_match and name_sim >= 0.35:
        tier = "auto_high"
    elif (address_match and place_match) or (place_match and name_sim >= 0.6):
        tier = "likely"
    elif score >= 0.3:
        tier = "review"
    else:
        tier = "unmatched"
    return {
        "score": round(score, 3), "tier": tier,
        "evidence": {
            "same_street_number": same_number, "same_street": same_street,
            "street_overlap": street_overlap, "same_zip": same_zip, "same_city": same_city,
            "name_similarity": name_sim,
        },
    }


def load_dph(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw in reader:
            row = {(k or "").strip().upper(): (v or "").strip() for k, v in raw.items()}
            if not row.get("LICENSE NO.") and not row.get("FACILITY NAME"):
                continue
            rows.append({
                "license_raw": row.get("LICENSE NO.", ""),
                "state_facility_license_id": normalize_license(row.get("LICENSE NO.", "")),
                "name": row.get("FACILITY NAME", ""),
                "address": row.get("ADDRESS", ""),
                "city": row.get("CITY", ""),
                "zip": normalize_zip(row.get("ZIP", "")),
                "status": row.get("STATUS", ""),
                "effective_date": row.get("EFFECTIVE DATE", ""),
                "expiration_date": row.get("EXPIRATION DATE", ""),
            })
    return rows


def load_cms(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [{
        "ccn": f["ccn"], "name": f.get("provider_name") or "", "address": f.get("address") or "",
        "city": f.get("city") or "", "zip": normalize_zip(f.get("zip_code") or ""),
    } for f in data["facilities"]]


TIER_RANK = {"auto_high": 3, "likely": 2, "review": 1, "unmatched": 0}


def build(dph_rows: list[dict], cms_rows: list[dict]) -> dict:
    proposals = []
    for d in dph_rows:
        ranked = sorted(((score_pair(d, c), c) for c in cms_rows),
                        key=lambda pair: (TIER_RANK[pair[0]["tier"]], pair[0]["score"]), reverse=True)
        best, cms = ranked[0] if ranked else ({"score": 0, "tier": "unmatched", "evidence": {}}, None)
        runner = ranked[1][0]["score"] if len(ranked) > 1 else 0
        proposals.append({"dph": d, "cms": cms, "match": best, "margin": round(best["score"] - runner, 3)})

    # One CCN per license: keep the strongest claim, demote the rest to review.
    claims: dict[str, dict] = {}
    for p in sorted(proposals, key=lambda p: (TIER_RANK[p["match"]["tier"]], p["match"]["score"]), reverse=True):
        if p["cms"] is None or p["match"]["tier"] == "unmatched":
            continue
        ccn = p["cms"]["ccn"]
        if ccn in claims:
            p["match"] = dict(p["match"], tier="review", note=f"CCN {ccn} already matched to a stronger license")
        else:
            claims[ccn] = p
    # A close runner-up means the pick is not safe to accept without a person.
    for p in proposals:
        if p["match"]["tier"] == "auto_high" and p["margin"] < 0.15:
            p["match"] = dict(p["match"], tier="likely", note="close runner-up candidate")

    rows = []
    for p in sorted(proposals, key=lambda p: p["dph"]["state_facility_license_id"].zfill(8)):
        cms = p["cms"] if p["match"]["tier"] != "unmatched" else None
        rows.append({
            "state_facility_license_id": p["dph"]["state_facility_license_id"],
            "dph_facility_name": p["dph"]["name"], "dph_address": p["dph"]["address"],
            "dph_city": p["dph"]["city"], "dph_zip": p["dph"]["zip"], "dph_status": p["dph"]["status"],
            "ccn": cms["ccn"] if cms else None,
            "cms_provider_name": cms["name"] if cms else None,
            "cms_address": cms["address"] if cms else None,
            "cms_city": cms["city"] if cms else None,
            "match_tier": p["match"]["tier"], "match_score": p["match"]["score"],
            "margin_over_runner_up": p["margin"], "evidence": p["match"].get("evidence", {}),
            "note": p["match"].get("note"), "review_decision": None,
        })
    matched_ccns = {r["ccn"] for r in rows if r["ccn"]}
    cms_without_license = [c for c in cms_rows if c["ccn"] not in matched_ccns]
    tiers: dict[str, int] = {}
    for r in rows:
        tiers[r["match_tier"]] = tiers.get(r["match_tier"], 0) + 1
    return {
        "schema_version": "ct-dph-ccn-crosswalk-candidate-1.0",
        "publication_status": "staging_review_required",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rule": "Nothing from CT DPH may be shown on a CCN-keyed public page until its row has review_decision = 'accepted'.",
        "summary": {"dph_licenses": len(rows), "cms_facilities": len(cms_rows), "tier_counts": tiers,
                    "cms_facilities_without_license_match": len(cms_without_license)},
        "rows": rows,
        "cms_facilities_without_license_match": cms_without_license,
    }


def review_markdown(result: dict) -> str:
    lines = ["# CT DPH to CMS CCN crosswalk: review queue", "",
             f"Generated {result['generated_at']}. {result['rule']}", "",
             f"Summary: {json.dumps(result['summary'])}", "",
             "| License | DPH facility | Tier | Score | CCN | CMS facility | Evidence |", "|---|---|---|---:|---|---|---|"]
    for r in result["rows"]:
        if r["match_tier"] == "auto_high":
            continue
        ev = r["evidence"]
        flags = ", ".join(k for k, v in ev.items() if v is True) + (f", name {ev.get('name_similarity')}" if ev else "")
        lines.append(f"| {r['state_facility_license_id']} | {r['dph_facility_name']}, {r['dph_city']} | {r['match_tier']} | "
                     f"{r['match_score']} | {r['ccn'] or ''} | {r['cms_provider_name'] or ''} | {flags}{'; ' + r['note'] if r['note'] else ''} |")
    lines += ["", "## CMS facilities with no license match", ""]
    lines += [f"- {c['ccn']} {c['name']}, {c['city']}" for c in result["cms_facilities_without_license_match"]]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dph", type=Path, default=DEFAULT_DPH)
    parser.add_argument("--cms", type=Path, default=DEFAULT_CMS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if not args.dph.exists():
        raise SystemExit(f"DPH facility master not found: {args.dph}. Copy Chronic_and_Convalescent_Nursing_Home.csv there.")
    result = build(load_dph(args.dph), load_cms(args.cms))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    review = args.output.with_suffix(".review.md")
    review.write_text(review_markdown(result), encoding="utf-8")
    print(f"Wrote {args.output} and {review}: {json.dumps(result['summary'])}")


if __name__ == "__main__":
    main()
