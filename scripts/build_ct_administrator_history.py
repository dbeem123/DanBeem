"""Build a private, privacy-filtered CT administrator tenure review. Never publish.

Source hashes come from data/ct_dph_source_profile.json. A missing or changed
source fails before parsing or writing the review. CMS matching reuses the
existing facility crosswalk builder; this module does not invent a second join.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import build_ct_dph_ccn_crosswalk as crosswalk
from fetch_ct_administrator_license_status import FIELDS

ROOT = Path(__file__).resolve().parents[1]
SOURCE_KEYS = {
    "history": "ct_dph_nursing_home_management_history",
    "facilities": "ct_dph_chronic_convalescent_facility_master",
    "registry": "ct_dph_nursing_home_administrator_registry",
}
HISTORY_FIELDS = ("License No", "Position", "Name", "License", "Start Date",
                  "TerminationDate", "Relationship status")
REGISTRY_FIELDS = ("LICENSE NO.", "FIRST NAME", "LAST NAME", "STATUS",
                   "ISSUE DATE", "EXPIRATION DATE")
FORBIDDEN_KEY = re.compile(
    r"^(?:address.*|.*address|city|state|zip.*|postal.*|county|mailing.*|salary.*|"
    r"compensation.*|dob|date_of_birth|birth.*|phone.*|email.*)$", re.I
)
ADDRESS_VALUE = re.compile(
    r"\b\d{1,6}\s+(?:[\w'.-]+\s+){1,5}(?:street|road|avenue|drive|lane|"
    r"boulevard|court|st|rd|ave|dr|ln|blvd|ct)\b.*\b\d{5}(?:-\d{4})?\b", re.I
)
PRIVATE_LABEL = re.compile(r"\b(?:ADDRESS[12]|ZIP(?:CODE)?|SALARY|COMPENSATION|"
                           r"DATE OF BIRTH|E-?MAIL|PHONE)\s*[:=]", re.I)
EMAIL_VALUE = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
PHONE_VALUE = re.compile(r"(?<!\d)(?:\+1[- .]?)?\(?\d{3}\)?[- .]\d{3}[- .]\d{4}(?!\d)")


def file_hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def safe_text(value: str) -> str:
    return " ".join((value or "").split())


def assert_privacy(value, location="output") -> None:
    """Reject sensitive keys and accidental contact data without echoing values."""
    if isinstance(value, dict):
        for key, item in value.items():
            if FORBIDDEN_KEY.fullmatch(key):
                raise ValueError(f"Forbidden field in {location}")
            assert_privacy(item, location)
    elif isinstance(value, list):
        for item in value:
            assert_privacy(item, location)
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern in
               (ADDRESS_VALUE, PRIVATE_LABEL, EMAIL_VALUE, PHONE_VALUE)):
            raise ValueError(f"Possible private value in {location}")


def read_projected_csv(path: Path, fields: tuple[str, ...]) -> list[dict]:
    """Project each parsed row immediately. Never retain any other columns."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = [safe_text(h or "") for h in reader.fieldnames or []]
        named = [h for h in headers if h]
        if len(named) != len(set(named)) or not set(fields).issubset(named):
            raise ValueError("Missing or duplicate required source columns")
        reader.fieldnames = headers
        rows = []
        for index, raw in enumerate(reader, 2):
            if None in raw:
                raise ValueError("Malformed CSV row width")
            selected = {key: raw.get(key) or "" for key in fields}
            # The full DictReader row (including registry contact fields) is
            # discarded before any processing, logging or accumulation.
            del raw
            if any(safe_text(v) for v in selected.values()):
                selected["source_row"] = index
                rows.append(selected)
        return rows


def normalized_license(raw: str) -> str:
    return crosswalk.normalize_license(raw)


def professional_key(raw: str) -> tuple[str, str | None]:
    text = safe_text(raw)
    if not text:
        return "", "blank_license"
    if "temp" in text.lower():
        return normalized_license(text), "temporary_identity_unlinked"
    number = normalized_license(text)
    if not number or number == "0":
        return "", "unusable_license"
    # The rule is digit normalization, never a fallback to matching names.
    return number, None


def parse_date(raw: str, label: str, flags: list[str]) -> str | None:
    value = safe_text(raw)
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    flags.append("invalid_" + label)
    return None


def verified_inputs(source_dir: Path, profile: dict) -> tuple[dict, list[dict]]:
    expected = {p["source_key"]: p["sha256"] for p in profile["source_files_profiled"]}
    found = defaultdict(list)
    for path in sorted(source_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() == ".csv":
            found[file_hash(path)].append(path)
    paths, sources = {}, []
    missing = []
    for label, key in SOURCE_KEYS.items():
        digest = expected[key]
        matches = found.get(digest, [])
        if not matches:
            missing.append(key)
            continue
        paths[label] = matches[0]
        sources.append({"id": key, "sha256": digest,
                        "bytes": matches[0].stat().st_size,
                        "url_or_note": "CT eLicense roster export; verified against source profile"})
    if missing:
        raise ValueError("Required hash-verified input missing: " + ", ".join(missing))
    return paths, sources


def license_records(registry: list[dict], public: dict | None) -> dict:
    observations = defaultdict(list)
    for row in registry:
        number, issue = professional_key(row["LICENSE NO."])
        if issue:
            raise ValueError("Registry has an unusable license identifier")
        flags = []
        observations[number].append({
            "name": safe_text(row["FIRST NAME"] + " " + row["LAST NAME"]),
            "status": safe_text(row["STATUS"]),
            "issued": parse_date(row["ISSUE DATE"], "issue_date", flags),
            "expires": parse_date(row["EXPIRATION DATE"], "expiration_date", flags),
            "source": "ct_dph_nursing_home_administrator_registry", "flags": flags,
        })
    if public:
        if public.get("schema_version") != "ct-nha-license-crosscheck-1.0" or \
                public.get("where") != "credentialtype = '36'" or \
                public.get("selected_fields") != list(FIELDS):
            raise ValueError("Unrecognized public license cross-check provenance")
        for row in public["records"]:
            if set(row) - set(FIELDS):
                raise ValueError("Public cross-check contains forbidden extra fields")
            number, issue = professional_key(row.get("credentialnumber", ""))
            if issue:
                raise ValueError("Public cross-check has an unusable license identifier")
            flags = []
            observations[number].append({
                "name": safe_text(row.get("name", "")),
                "status": safe_text(row.get("status", "")),
                "issued": parse_date(row.get("issuedate", ""), "issue_date", flags),
                "expires": parse_date(row.get("expirationdate", ""), "expiration_date", flags),
                "source": "ct_open_data_ngch_56tr", "flags": flags,
            })
    return observations


def project_crosswalk(facilities: list[dict], cms: list[dict], decisions: list[dict]) -> list[dict]:
    candidate = crosswalk.build(facilities, cms)
    decision_map = {}
    for decision in decisions:
        key = decision["facility_license"]
        if key in decision_map or decision.get("decision") not in ("accepted", "rejected") \
                or not safe_text(decision.get("note", "")):
            raise ValueError("Invalid or duplicate crosswalk review decision")
        decision_map[key] = decision
    result, accepted = [], set()
    for row in candidate["rows"]:
        key = row["state_facility_license_id"]
        decision = decision_map.pop(key, None)
        if decision and decision.get("ccn") != row["ccn"]:
            raise ValueError("Review decision does not match the proposed CCN")
        confirmed = decision and decision["decision"] == "accepted"
        if confirmed and (row["match_tier"] not in ("auto_high", "likely") or
                          not row["ccn"] or row["ccn"] in accepted):
            raise ValueError("Unsafe or duplicate accepted CCN")
        if confirmed:
            accepted.add(row["ccn"])
        result.append({
            "facility_license": key, "facility_name": row["dph_facility_name"],
            "ccn": row["ccn"] if confirmed else None,
            "candidate_ccn": row["ccn"], "candidate_name": row["cms_provider_name"],
            "match_tier": row["match_tier"], "score": row["match_score"],
            "margin": row["margin_over_runner_up"], "evidence": row["evidence"],
            "decision": decision["decision"] if decision else "pending",
            "review_note": decision["note"] if decision else None,
            "match_note": row["note"],
        })
    if decision_map:
        raise ValueError("Review decision references an unknown facility")
    assert_privacy(result)
    return result


def bounded_interval(role: dict, as_of: str):
    if not role["start"] or role["start"] > as_of or "end_before_start" in role["flags"]:
        return None
    end = role["end"] or (as_of if role["open"] else None)
    return (role["start"], min(end, as_of)) if end else None


def add_review_flags(people: list[dict], unlinked: list[dict], as_of: str) -> tuple[list, list]:
    overlap_pairs = []
    for person in people:
        for left, right in itertools.combinations(person["roles"], 2):
            a, b = bounded_interval(left, as_of), bounded_interval(right, as_of)
            if a and b and left["facility_license"] != right["facility_license"] and \
                    max(a[0], b[0]) <= min(a[1], b[1]):
                overlap_pairs.append({"person_id": person["id"],
                                      "role_ids": [left["id"], right["id"]]})
                for role in (left, right):
                    if "overlapping_reported_dates" not in role["flags"]:
                        role["flags"].append("overlapping_reported_dates")
    active = defaultdict(list)
    for role in [r for p in people for r in p["roles"]] + unlinked:
        if role["open"] and (not role["start"] or role["start"] <= as_of):
            active[role["facility_license"]].append(role)
    multiple = []
    for key, roles in sorted(active.items()):
        if len(roles) > 1:
            multiple.append({"facility_license": key, "role_ids": [r["id"] for r in roles]})
            for role in roles:
                role["flags"].append("multiple_active_administrator_records")
    return overlap_pairs, multiple


def build_review(history: list[dict], registry: list[dict], facilities: list[dict],
                 cms: list[dict], public: dict | None, sources: list[dict], as_of: str,
                 decisions: list[dict] | None = None) -> dict:
    date.fromisoformat(as_of)
    if public and date.fromisoformat(public["retrieved_at"][:10]) < date.fromisoformat(as_of):
        raise ValueError("Public cross-check predates the DPH snapshot; acquire a fresh cross-check")
    links = project_crosswalk(facilities, cms, decisions or [])
    facility_map = {r["facility_license"]: r for r in links}
    if len(facility_map) != len(facilities) or "" in facility_map:
        raise ValueError("Duplicate or missing normalized facility licenses")
    observations = license_records(registry, public)
    grouped, unlinked = defaultdict(list), []
    for row in history:
        if safe_text(row["Position"]) != "Administrator":
            continue
        facility = normalized_license(row["License No"])
        if facility not in facility_map:
            raise ValueError("Administrator history references a missing facility")
        match = facility_map[facility]
        license_number, unlinked_reason = professional_key(row["License"])
        flags = [unlinked_reason] if unlinked_reason else []
        start = parse_date(row["Start Date"], "start_date", flags)
        end = parse_date(row["TerminationDate"], "end_date", flags)
        status = safe_text(row["Relationship status"]).lower()
        if not start:
            flags.append("start_not_recorded")
        if not end and not safe_text(row["TerminationDate"]):
            flags.append("open_as_of_source" if status == "active" else "end_not_recorded")
        if end and not start:
            flags.append("end_without_start")
        if start and end and end < start:
            flags.append("end_before_start")
        if any(d and d > as_of for d in (start, end)):
            flags.append("date_after_snapshot")
        if status == "active" and end:
            flags.append("active_relationship_has_end")
        if not match["ccn"]:
            flags.append("ccn_pending_review")
        role = {
            "id": f"dph-admin-row-{row['source_row']}",
            "name_raw": row["Name"], "name": safe_text(row["Name"]).title(),
            "license_number": license_number or None, "license_raw": row["License"],
            "facility_license": facility, "facility_license_raw": row["License No"],
            "facility_name": match["facility_name"], "ccn": match["ccn"],
            "start": start, "end": end,
            "open": end is None and not safe_text(row["TerminationDate"]) and status == "active",
            "relationship_status": status, "temporary": "temp" in row["License"].lower(),
            "source": "ct_dph_nursing_home_management_history", "as_of": as_of,
            "source_row": row["source_row"], "flags": flags,
        }
        (unlinked if unlinked_reason else grouped[license_number]).append(role)
    people, unmatched, conflicts = [], [], []
    registry_numbers = {normalized_license(r["LICENSE NO."]) for r in registry}
    for number, roles in sorted(grouped.items(), key=lambda p: (int(p[0]), p[0])):
        obs = observations.get(number, [])
        public_obs = [o for o in obs if o["source"] == "ct_open_data_ngch_56tr"]
        chosen_pool = public_obs or obs
        flags = []
        if number not in registry_numbers:
            flags.append("missing_current_registry")
            unmatched.append({"license_number": number, "role_count": len(roles),
                              "public_crosscheck": "found" if public_obs else
                              ("not_found" if public else "not_checked")})
        chosen = chosen_pool[0] if len(chosen_pool) == 1 else None
        if len(chosen_pool) > 1:
            flags.append("duplicate_license_observations")
        if len({o["status"].casefold() for o in obs}) > 1:
            flags.append("license_status_differs_by_snapshot")
        names = {safe_text(r["name"]).casefold() for r in roles}
        names.update(safe_text(o["name"]).casefold() for o in obs if o["name"])
        if len(names) > 1:
            flags.append("name_variation_review")
        if flags:
            conflicts.append({"license_number": number, "flags": flags})
        people.append({
            "id": "nha-" + number, "name": roles[0]["name"],
            "license_number": number, "license_status": chosen["status"] if chosen else None,
            "license_issued": chosen["issued"] if chosen else None,
            "license_expires": chosen["expires"] if chosen else None,
            "license_source": chosen["source"] if chosen else None,
            "license_as_of": (public["retrieved_at"][:10] if public_obs else as_of) if chosen else None,
            "license_observations": obs, "flags": flags,
            "roles": sorted(roles, key=lambda r: (r["start"] or "", r["facility_license"], r["id"])),
        })
    overlaps, multiple = add_review_flags(people, unlinked, as_of)
    roles = [r for p in people for r in p["roles"]] + unlinked
    dates = [d for r in roles for d in (r["start"], r["end"]) if d]
    flags = Counter(flag for role in roles for flag in role["flags"])
    sample = random.Random(20261103).sample(people, min(20, len(people)))
    result = {
        "schema_version": "ct-administrator-history-review-1.0",
        "publication_status": "private_review_required",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": sources, "source_as_of": as_of,
        "caveats": [
            "Facility conditions during this period reflect many factors and are not a measure of the administrator's performance.",
            "Listing is not an allegation of wrongdoing.",
            "Open roles are observed through the source snapshot, not confirmed current employment.",
            "A license identifies a professional record; people are never merged by name.",
            "Temporary and blank-license roles remain unlinked pending identity review.",
            "All CCN proposals require documented acceptance before the public build.",
        ],
        "summary": {
            "source_history_rows": len(history), "administrator_roles": len(roles),
            "excluded_other_positions": len(history) - len(roles), "people": len(people),
            "unlinked_roles": len(unlinked), "facilities": len({r['facility_license'] for r in roles}),
            "earliest_role_date": min(dates) if dates else None,
            "latest_role_date": max(dates) if dates else None,
            "overlap_pairs": len(overlaps), "multiple_active_facilities": len(multiple),
            "temporary_roles": sum(r["temporary"] for r in roles),
            "missing_registry_unique_licenses": len(unmatched),
            "missing_registry_roles": sum(r["role_count"] for r in unmatched),
            "role_flag_counts": dict(sorted(flags.items())),
            "crosswalk_tiers": dict(sorted(Counter(r['match_tier'] for r in links).items())),
            "ccn_accepted": sum(r["ccn"] is not None for r in links),
        },
        "people": people, "unlinked_roles": unlinked, "crosswalk_review": links,
        "overlap_pairs": overlaps, "multiple_active_facilities": multiple,
        "unmatched_registry_licenses": unmatched, "license_review": conflicts,
        "sample_people_ids": [p["id"] for p in sample], "sample_seed": 20261103,
        "corrections": [], "privacy_check": "passed",
    }
    assert_privacy(result)
    return result


def markdown(result: dict) -> str:
    def cell(text):
        return str(text if text is not None else "not recorded").replace("|", "\\|").replace("\n", " ")
    lines = ["# CT administrator history: private review", "",
             "NOT PUBLIC. Identity and facility matches require Claude's review.", "",
             "## Counts", "", "```json", json.dumps(result["summary"], indent=2), "```", "",
             "## Deterministic sample (seed 20261103)", ""]
    by_id = {p["id"]: p for p in result["people"]}
    for key in result["sample_people_ids"]:
        person = by_id[key]
        lines.extend([f"### {cell(person['name'])} — license {person['license_number']}", "",
                      f"License status: {cell(person['license_status'])} ({cell(person['license_source'])}).", "",
                      "| Facility / DPH license | Start | End | Confirmed CCN | Flags |",
                      "|---|---|---|---|---|"])
        for r in person["roles"]:
            end = r["end"] or ("open at " + r["as_of"] if r["open"] else "end not recorded")
            lines.append(f"| {cell(r['facility_name'])} / {r['facility_license']} | "
                         f"{r['start'] or 'start not recorded'} | {end} | {r['ccn'] or 'pending review'} | "
                         f"{cell(', '.join(r['flags']))} |")
        lines.append("")
    lines += ["## History licenses absent from the registry", "",
              "| License | Roles | Public cross-check |", "|---|---:|---|"]
    lines += [f"| {r['license_number']} | {r['role_count']} | {r['public_crosscheck']} |"
              for r in result["unmatched_registry_licenses"]]
    lines += ["", "## Facility match review", "",
              "Candidate CCNs are proposals, not confirmed links. Review every non-auto-high row and at least 10% of auto-high rows.",
              "", "| DPH license | Facility | Tier | Candidate CCN | CMS name | Decision |",
              "|---|---|---|---|---|---|"]
    lines += [f"| {r['facility_license']} | {cell(r['facility_name'])} | {r['match_tier']} | "
              f"{r['candidate_ccn'] or 'none'} | {cell(r['candidate_name'])} | {r['decision']} |"
              for r in result["crosswalk_review"]]
    lines += ["", "## Privacy and limitations", "", "Projected output passed the private-data checks."]
    lines.extend("- " + caveat for caveat in result["caveats"])
    return "\n".join(lines) + "\n"


def write_review(result: dict, output: Path, root: Path | None = None) -> None:
    root = root or ROOT
    if not output.resolve().is_relative_to((root / "data" / "testing").resolve()):
        raise ValueError("Review output must remain in ignored data/testing")
    summary = output.with_suffix(".md")
    if output.exists() or summary.exists():
        raise ValueError("Review outputs already exist; preserve them and choose a new filename")
    assert_privacy(result)
    text = markdown(result)
    assert_privacy(text, "summary")
    output.parent.mkdir(parents=True, exist_ok=True)
    # These are review artifacts, not a transactional/live state store.
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    with summary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "source_data" / "ct_dph")
    parser.add_argument("--source-as-of", required=True, help="Verified date of the DPH snapshot, YYYY-MM-DD")
    parser.add_argument("--crosscheck", type=Path)
    parser.add_argument("--crosswalk-review", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data/testing/ct_administrator_history_review.json")
    args = parser.parse_args()
    if not args.source_dir.resolve().is_relative_to((ROOT / "source_data" / "ct_dph").resolve()):
        raise SystemExit("Refused: raw inputs must be under ignored source_data/ct_dph")
    try:
        date.fromisoformat(args.source_as_of)
        profile = json.loads((ROOT / "data/ct_dph_source_profile.json").read_text(encoding="utf-8"))
        paths, sources = verified_inputs(args.source_dir, profile)
        for source in sources:
            source["as_of"] = args.source_as_of
        public = json.loads(args.crosscheck.read_text(encoding="utf-8")) if args.crosscheck else None
        if public:
            sources.append({"id": "ct_open_data_ngch_56tr", "sha256": file_hash(args.crosscheck),
                            "as_of": public["retrieved_at"], "url_or_note": public["source_url"]})
        cms_path = ROOT / "data/nursing_home_staffing_ct.json"
        cms_metadata = json.loads(cms_path.read_text(encoding="utf-8"))
        provider_source = next((s for s in cms_metadata.get("sources", [])
                                if s.get("source_dataset_name") == "CMS Nursing Home Provider Information"), {})
        sources.append({"id": "cms_provider_snapshot", "sha256": file_hash(cms_path),
                        "as_of": provider_source.get("freshness_date"),
                        "as_of_basis": "Freshness recorded by the existing CMS export; not tenure-period identity proof",
                        "release_note": provider_source.get("source_release"),
                        "url_or_note": "CMS provider snapshot embedded in nursing_home_staffing_ct.json"})
        decisions = json.loads(args.crosswalk_review.read_text(encoding="utf-8")) if args.crosswalk_review else []
        result = build_review(
            read_projected_csv(paths["history"], HISTORY_FIELDS),
            read_projected_csv(paths["registry"], REGISTRY_FIELDS),
            crosswalk.load_dph(paths["facilities"]), crosswalk.load_cms(cms_path),
            public, sources, args.source_as_of, decisions,
        )
        write_review(result, args.output)
        print(json.dumps(result["summary"]))
        print("PRIVATE REVIEW ONLY; stop for match review. Nothing published.")
    except (ValueError, KeyError, OSError, TypeError) as exc:
        # Errors from parsing/projection never dump records or contact fields.
        message = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError) else type(exc).__name__
        raise SystemExit("Review build stopped: " + message) from None


if __name__ == "__main__":
    main()
