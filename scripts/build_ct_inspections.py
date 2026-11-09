#!/usr/bin/env python3
"""Build the statewide Inspections data and the Connecticut facility roster.

Inputs (all already used elsewhere on the site, plus CMS Inspection Dates):
  data/nursing_home_health_deficiencies_ct.json   CMS Health Deficiencies, CT rows
  data/nursing_home_penalties_ct.json             CMS Penalties, CT rows
  data/nursing_home_staffing_ct.json              Provider Information + PBJ (facility list, quarters)
  data/nursing_home_facility_status_review_ct.json  closures confirmed from primary sources
  data/ct_nursing_home_cost_reports.json          DSS cost reports index (latest cost year per home)
  data/appendix_pp_tag_pages.json                 Appendix PP page anchors
  data/reference/resident_rights_tag_map.json     resident-rights groups
  source_data/cms_survey/NH_SurveyDates_<Mon><YYYY>.csv   CMS Inspection Dates (ignored folder)
  source_data/cms_survey/NH_CitationDescriptions_<Mon><YYYY>.csv
  source_data/provider_info/NH_ProviderInfo_<Mon><YYYY>.csv

Outputs:
  data/ct_inspections.json
  data/nursing_home_facility_roster_ct.json
"""
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SRC = ROOT / "source_data"
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

# Scope and severity grid (CMS): rows are severity levels, columns are scope.
SEVERITY = [
    ("immediate_jeopardy", "Immediate jeopardy to resident health or safety", "JKL"),
    ("actual_harm", "Actual harm that is not immediate jeopardy", "GHI"),
    ("potential_more_than_minimal", "No actual harm, potential for more than minimal harm", "DEF"),
    ("potential_minimal", "No actual harm, potential for minimal harm", "ABC"),
]
SCOPE = ["Isolated", "Pattern", "Widespread"]
TYPE_BITS = {"standard": 1, "complaint": 2, "infection_control": 4}
SURVEY_TYPES = ["Health Standard", "Health Complaint", "Fire Safety Standard", "Fire Safety Complaint"]


def latest(folder, prefix):
    best = None
    for p in (SRC / folder).glob(prefix + "_*.csv"):
        m = re.search(r"_([A-Z][a-z]{2})(\d{4})(?:_\d+)?\.csv$", p.name)
        if m and m.group(1) in MONTHS:
            key = (int(m.group(2)), MONTHS[m.group(1)])
            if best is None or key > best[0]:
                best = (key, p)
    if not best:
        raise SystemExit(f"Missing source file: source_data/{folder}/{prefix}_<Mon><YYYY>.csv")
    return best[1], f"{best[1].name.split('_')[-1][:3]} {best[0][0]}"


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        yield from csv.DictReader(fh)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def tag4(t):
    """'F600' or 'F-0600' -> 'F0600' (the CMS file spelling without the dash)."""
    t = t.replace("-", "").strip().upper()
    return t[0] + t[1:].zfill(4)


def ccn6(value):
    v = (value or "").strip()
    return v.zfill(6) if v.isdigit() else v.upper()


def main():
    deficiencies = load("nursing_home_health_deficiencies_ct.json")
    penalties = load("nursing_home_penalties_ct.json")
    fire = load("nursing_home_fire_safety_deficiencies_ct.json")
    staffing = load("nursing_home_staffing_ct.json")
    status_review = load("nursing_home_facility_status_review_ct.json")
    cost_index = load("ct_nursing_home_cost_reports.json")
    pp = load("appendix_pp_tag_pages.json")
    rr = load("reference/resident_rights_tag_map.json")

    dates_path, dates_release = latest("cms_survey", "NH_SurveyDates")
    lookup_path, _ = latest("cms_survey", "NH_CitationDescriptions")
    pi_path, pi_release = latest("provider_info", "NH_ProviderInfo")

    # ---- Provider Information (current CMS list of certified CT homes)
    pi = {}
    for r in rows(pi_path):
        if r["State"] == "CT":
            pi[ccn6(r["CMS Certification Number (CCN)"])] = r
    pi_processing = next(iter(pi.values()))["Processing Date"] if pi else None

    # ---- PBJ quarters per home
    pbj = {}
    for q in staffing["facility_quarterly_staffing"]:
        pbj.setdefault(q["ccn"], set()).add(q["quarter"])
    quarters = sorted({q for s in pbj.values() for q in s})
    latest_q = quarters[-1]
    names = {f["ccn"]: (f.get("provider_name"), f.get("city")) for f in staffing["facilities"]}

    # ---- Inspection Dates
    surveys = {}
    survey_footnotes = {}
    dates_processing = None
    for r in rows(dates_path):
        c = ccn6(r["CMS Certification Number (CCN)"])
        if not c.startswith("07"):
            continue
        dates_processing = r["Processing Date"]
        t = r["Type of Survey"]
        if t not in SURVEY_TYPES:
            raise SystemExit(f"Unknown survey type in Inspection Dates: {t!r}")
        surveys.setdefault(c, []).append([r["Survey Date"], SURVEY_TYPES.index(t), int(r["Survey Cycle"] or 0), r["Survey Footnote"] or ""])
        if r["Survey Footnote"]:
            survey_footnotes[r["Survey Footnote"]] = survey_footnotes.get(r["Survey Footnote"], 0) + 1
    for v in surveys.values():
        v.sort(key=lambda x: x[0], reverse=True)

    # ---- Citations
    defs = deficiencies["deficiencies"]
    cited = {d["ccn"] for d in defs}
    penal = {p["ccn"] for p in penalties["penalties"]}
    cost_latest = {}
    cost_names = {}
    for h in cost_index.get("homes", cost_index.get("facilities", [])):
        cost_names[h["ccn"]] = h.get("facility_name")
        yrs = [y for y in (h.get("cost_years") or h.get("years") or []) if isinstance(y, (int, str))]
        cost_latest[h["ccn"]] = max((int(y) for y in yrs), default=None) if yrs else h.get("latest_cost_year")
    closed = {r["ccn"]: r for r in status_review["records"] if r.get("official_status") == "closed_or_non_current"}

    # ---- Roster: every CCN seen in any source
    all_ccns = sorted(set(pi) | set(pbj) | cited | penal | set(surveys) | set(c for c in cost_latest if c.startswith("07")))
    roster = []
    for c in all_ccns:
        p = pi.get(c)
        nm, city = names.get(c, (None, None))
        rec = {
            "ccn": c,
            "name": (p["Provider Name"] if p else nm) or next((d["provider_name"] for d in defs if d["ccn"] == c), None)
                    or (closed[c].get("facility_name") if c in closed else None) or cost_names.get(c),
            "city": (p["City/Town"] if p else city),
            "in_provider_info": bool(p),
            "pbj_quarters": sorted(pbj.get(c, [])),
            "in_pbj_latest_quarter": latest_q in pbj.get(c, set()),
            "health_citation_rows": sum(1 for d in defs if d["ccn"] == c),
            "in_penalties": c in penal,
            "inspection_dates_rows": len(surveys.get(c, [])),
            "latest_dss_cost_year": cost_latest.get(c),
            "official_status": closed[c]["official_status"] if c in closed else None,
            "official_status_date": closed[c].get("official_status_date") if c in closed else None,
            "official_status_date_type": closed[c].get("official_status_date_type") if c in closed else None,
        }
        notes = []
        if not rec["in_provider_info"]:
            notes.append(f"Not in CMS Provider Information ({pi_release}).")
            if rec["pbj_quarters"]:
                notes.append("PBJ staffing rows only for " + ", ".join(rec["pbj_quarters"]) + ".")
            if c in closed:
                notes.append(f"Closed or not current: {closed[c].get('official_status_date_type')} {closed[c].get('official_status_date')} (primary source in the facility status review).")
        if rec["in_provider_info"] and not rec["in_pbj_latest_quarter"]:
            notes.append(f"No PBJ staffing rows for {latest_q} in the CMS file used by this site.")
        if rec["in_provider_info"] and not rec["inspection_dates_rows"]:
            notes.append("No rows in CMS Inspection Dates.")
        rec["notes"] = notes
        roster.append(rec)

    summary = {
        "provider_info_release": pi_release,
        "provider_info_processing_date": pi_processing,
        "provider_info_homes": len(pi),
        "pbj_quarters": quarters,
        "pbj_latest_quarter": latest_q,
        "pbj_homes_latest_quarter": sum(1 for c in pbj if latest_q in pbj[c]),
        "pbj_homes_any_quarter": len(pbj),
        "provider_info_homes_without_latest_pbj": sum(1 for c in pi if latest_q not in pbj.get(c, set())),
        "homes_with_health_citations": len(cited),
        "homes_with_penalties": len(penal),
        "homes_in_inspection_dates": len(surveys),
        "all_ccns_seen": len(all_ccns),
        "ccns_not_in_provider_info": [r["ccn"] for r in roster if not r["in_provider_info"]],
    }
    (DATA / "nursing_home_facility_roster_ct.json").write_text(json.dumps({
        "metadata": {
            "dataset_name": "Connecticut nursing home facility roster",
            "build_date": date.today().isoformat(),
            "purpose": "One list of every Connecticut CCN seen in the site's CMS and DSS sources, with where each home appears. "
                       "Used for the denominators shown beside rates. Nothing is dropped: a home missing from a source is listed with a note.",
            "summary": summary,
            "sources": {
                "provider_info": pi_path.name, "inspection_dates": dates_path.name,
                "pbj": "data/nursing_home_staffing_ct.json", "health_citations": deficiencies["metadata"].get("source_file"),
                "penalties": penalties["metadata"].get("source_file"), "status_review": "data/nursing_home_facility_status_review_ct.json",
            },
        },
        "records": roster,
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # ---- Tag lookup
    lookup = {}
    for r in rows(lookup_path):
        lookup[r["Deficiency Prefix and Number"].replace("-", "")] = (r["Deficiency Description"], r["Deficiency Category"])
    pp_page = {}
    for r in pp["appendix_pp_tag_page_rows"]:
        if r.get("appendix_pp_pdf_page_start"):
            pp_page[tag4(r["f_tag"])] = r["appendix_pp_pdf_page_start"]
    group_of = {tag4(t): g["id"] for g in rr["groups"] for t in g["tags"]}
    tagref = {}
    for rec in rr.get("tags", []):
        t = tag4(rec["tag"])
        tagref[t] = [rec.get("title"), rec.get("cfr"), rec.get("note"), rec.get("source_url")]
        if rec.get("appendix_pp_page"):
            pp_page[t] = rec["appendix_pp_page"]

    SCORE_FIELDS = [
        ("cycle1_date", "Rating Cycle 1 Standard Survey Health Date"), ("cycle1_deficiencies", "Rating Cycle 1 Total Number of Health Deficiencies"),
        ("cycle1_standard", "Rating Cycle 1 Number of Standard Health Deficiencies"), ("cycle1_complaint", "Rating Cycle 1 Number of Complaint Health Deficiencies"),
        ("cycle1_deficiency_score", "Rating Cycle 1 Health Deficiency Score"), ("cycle1_revisits", "Rating Cycle 1 Number of Health Revisits"),
        ("cycle1_revisit_score", "Rating Cycle 1 Health Revisit Score"), ("cycle1_total_score", "Rating Cycle 1 Total Health Score"),
        ("cycle2_date", "Rating Cycle 2 Standard Health Survey Date"), ("cycle23_deficiencies", "Rating Cycle 2/3 Total Number of Health Deficiencies"),
        ("cycle2_standard", "Rating Cycle 2 Number of Standard Health Deficiencies"), ("cycle23_complaint", "Rating Cycle 2/3 Number of Complaint Health Deficiencies"),
        ("cycle23_deficiency_score", "Rating Cycle 2/3 Health Deficiency Score"), ("cycle23_revisits", "Rating Cycle 2/3 Number of Health Revisits"),
        ("cycle23_revisit_score", "Rating Cycle 2/3 Health Revisit Score"), ("cycle23_total_score", "Rating Cycle 2/3 Total Health Score"),
        ("weighted_score", "Total Weighted Health Survey Score"), ("health_rating", "Health Inspection Rating"),
        ("health_rating_footnote", "Health Inspection Rating Footnote"),
    ]
    def number(v):
        try:
            return float(v) if "." in v else int(v)
        except (TypeError, ValueError):
            return v or None
    scores = {}
    for c, r in pi.items():
        scores[c] = {k: (r.get(col) or None) if k.endswith(("date", "footnote")) else number(r.get(col)) for k, col in SCORE_FIELDS}
    homes = [r for r in roster if r["health_citation_rows"] or r["in_provider_info"] or r["inspection_dates_rows"]]
    hidx = {r["ccn"]: i for i, r in enumerate(homes)}
    cats = []
    tags = {}
    out_rows = []
    all_defs = [(0, d) for d in defs] + [(1 if d["deficiency_prefix"] == "K" else 2, d) for d in fire["deficiencies"]]
    for d in {d["ccn"] for _, d in all_defs} - set(hidx):
        raise SystemExit(f"Citation for a CCN missing from the roster: {d}")
    for kind, d in sorted(all_defs, key=lambda kd: (kd[1]["ccn"], kd[1]["survey_date"], kd[0], kd[1]["deficiency_code"])):
        code = d["deficiency_code"].replace("-", "")
        desc, cat = lookup.get(code, (d.get("deficiency_description"), d.get("deficiency_category")))
        cat = cat or "Not categorized"
        if cat not in cats:
            cats.append(cat)
        if code not in tags:
            tags[code] = [desc or "", cats.index(cat), group_of.get(code), pp_page.get(code)]
        bits = ((d.get("standard_deficiency") is True) * 1) | ((d.get("complaint_deficiency") is True) * 2) | ((d.get("infection_control_inspection_deficiency") is True) * 4)
        idr = ((d.get("citation_under_idr") is True) * 1) | ((d.get("citation_under_iidr") is True) * 2)
        ss = (d.get("scope_severity_code") or "").strip().upper()
        if ss and ss not in "ABCDEFGHIJKL":
            raise SystemExit(f"Unexpected scope/severity code {ss!r}")
        out_rows.append([hidx[d["ccn"]], d["survey_date"], code, ss, bits, d.get("correction_date") or "", idr, kind])

    dmin = min(r[1] for r in out_rows if r[7] == 0)
    dmax = max(r[1] for r in out_rows if r[7] == 0)
    out = {
        "meta": {
            "build_date": date.today().isoformat(),
            "citations_source": deficiencies["metadata"].get("source_file"),
            "citations_processing_date": defs[0].get("processing_date") if defs else None,
            "inspection_dates_source": dates_path.name,
            "inspection_dates_release": dates_release,
            "inspection_dates_processing_date": dates_processing,
            "inspection_dates_footnotes": survey_footnotes,
            "provider_info_source": pi_path.name,
            "provider_info_release": pi_release,
            "citation_date_min": dmin,
            "citation_date_max": dmax,
            "citation_rows": len(out_rows),
            "citation_rows_by_kind": [sum(1 for r in out_rows if r[7] == k) for k in range(3)],
            "correction_before_survey_rows": sum(1 for r in out_rows if r[5] and r[5] < r[1]),
            "no_correction_date_rows": sum(1 for r in out_rows if not r[5]),
            "denominators": {
                "provider_info_homes": len(pi),
                "homes_with_citations": len(cited),
                "homes_with_citations_in_provider_info": len(cited & set(pi)),
            },
            "resident_rights_map": {"version": rr["version"], "status": rr["status"], "status_note": rr["status_note"],
                                    "appendix_pp": rr["appendix_pp"]},
            "severity": [[k, label, letters] for k, label, letters in SEVERITY],
            "scope": SCOPE,
            "survey_types": SURVEY_TYPES,
            "type_bits": TYPE_BITS,
            "row_fields": ["home", "survey_date", "tag", "scope_severity", "type_bits", "correction_date", "idr_bits", "kind"],
            "kinds": ["Health", "Fire safety (life safety code)", "Emergency preparedness"],
            "fire_source": fire["metadata"].get("source_file"),
            "score_fields_source": "CMS Provider Information " + pi_release + " (Rating Cycle and Total Weighted Health Survey Score columns)",
            "notes": [
                "Health citations (F-tags) come from CMS Health Deficiencies; fire safety (K-tags) and emergency preparedness (E-tags) from CMS Fire Safety Deficiencies.",
                "Some correction dates are earlier than the survey date. CMS records this, for example, for noncompliance that was already corrected when inspectors found it. Dates are shown as CMS recorded them.",
                "CMS publishes about three standard survey cycles and recent complaint surveys; older citations are not in this file.",
                "A citation can come from a standard survey, a complaint investigation, an infection control inspection, or more than one of these.",
                "Inspection Dates footnote 29 marks a risk-based survey. No record is not proof that no survey occurred.",
            ],
        },
        "homes": [[r["ccn"], r["name"], r["city"], int(r["in_provider_info"])] for r in homes],
        "categories": cats,
        "tags": tags,
        "groups": [{"id": g["id"], "label": g["label"], "tags": [tag4(t) for t in g["tags"]], **({"note": g["note"]} if g.get("note") else {})} for g in rr["groups"]],
        "rows": out_rows,
        "tagref": {t: v for t, v in tagref.items() if group_of.get(t)},
        "surveys": {str(hidx[c]): v for c, v in surveys.items() if c in hidx},
        "scores": {str(hidx[c]): v for c, v in scores.items() if c in hidx},
    }
    (DATA / "ct_inspections.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote data/ct_inspections.json: {len(out_rows)} citations, {len(homes)} homes, {len(tags)} tags, "
          f"{(DATA / 'ct_inspections.json').stat().st_size // 1024} KB")
    print(f"Wrote data/nursing_home_facility_roster_ct.json: {len(roster)} CCNs; "
          f"{summary['provider_info_homes']} in Provider Information, {summary['pbj_homes_latest_quarter']} with PBJ {latest_q}")


if __name__ == "__main__":
    main()
