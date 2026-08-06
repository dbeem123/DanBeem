#!/usr/bin/env python3
"""Audit the complete Connecticut survey/enforcement static release.

The audit is intentionally read-only. It independently parses and reconciles
the statewide runtime datasets, compact summary, per-facility detail layer,
metadata, public methodology, and Facility Explorer loading architecture.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DETAIL_DIR = DATA / "nursing_home_survey_enforcement_details_ct"

PATHS = {
    "staffing": DATA / "nursing_home_staffing_ct.json",
    "health": DATA / "nursing_home_health_deficiencies_ct.json",
    "fire": DATA / "nursing_home_fire_safety_deficiencies_ct.json",
    "penalties": DATA / "nursing_home_penalties_ct.json",
    "summary": DATA / "nursing_home_survey_enforcement_summary_ct.json",
    "detail_index": DETAIL_DIR / "index.json",
    "manifest": DATA / "nursing_home_source_manifest.json",
    "registry": DATA / "current_tool_context_registry.json",
    "explorer": ROOT / "tools" / "nursing-home-staffing-explorer.html",
    "javascript": ROOT / "Assets" / "nursing-home-staffing.js",
    "methodology": ROOT / "tools" / "nursing-home-staffing-methodology.html",
}

EXPECTED = {
    "current_facilities": 196,
    "health_rows": 6761,
    "health_ccns": 191,
    "health_dates": ("2018-11-08", "2026-03-31"),
    "health_distinct_tags": 164,
    "health_lookup_misses": 0,
    "health_groups": {
        "actual_harm_not_ij": 172,
        "immediate_jeopardy": 73,
        "no_actual_harm_minimal": 463,
        "no_actual_harm_more_than_minimal": 6053,
    },
    "fire_rows": 2135,
    "fire_ccns": 178,
    "fire_k_rows": 2007,
    "fire_e_rows": 128,
    "fire_distinct_codes": 84,
    "fire_dates": ("2018-11-08", "2026-02-27"),
    "fire_lookup_misses": 145,
    "fire_lookup_codes": {"K-0133": 2, "K-0211": 143},
    "fire_scope_counts": {"D": 1556, "E": 338, "F": 238, "J": 2, "K": 1},
    "penalty_rows": 179,
    "penalty_ccns": 102,
    "fine_rows": 167,
    "payment_denial_rows": 12,
    "fine_total": 3925517.00,
    "denial_days": 368,
    "duplicate_penalty_rows": 3,
    "penalty_dates": ("2023-05-17", "2026-03-17"),
    "processing_dates": ("2026-05-01", "2026-05-01"),
    "denial_start_dates": ("2024-01-17", "2024-12-03"),
    "recent_window": ("2023-03-31", "2026-03-31"),
    "zero_record_facilities": 5,
    "summary_all_time": {
        "all_time_health_deficiency_count": 6761,
        "all_time_actual_harm_count": 172,
        "all_time_immediate_jeopardy_count": 73,
        "all_time_fire_safety_citation_count": 2007,
        "all_time_emergency_preparedness_citation_count": 128,
        "all_time_enforcement_event_count": 179,
        "all_time_fine_count": 167,
        "all_time_fine_total": 3925517.00,
        "all_time_payment_denial_count": 12,
        "all_time_payment_denial_days": 368,
    },
    "summary_recent": {
        "recent_health_deficiency_count": 4717,
        "recent_actual_harm_count": 141,
        "recent_immediate_jeopardy_count": 66,
        "recent_fire_safety_citation_count": 1151,
        "recent_emergency_preparedness_citation_count": 57,
        "recent_enforcement_event_count": 179,
        "recent_fine_count": 167,
        "recent_fine_total": 3925517.00,
        "recent_payment_denial_count": 12,
        "recent_payment_denial_days": 368,
    },
}

REQUIRED_METADATA = {
    "health": {
        "source_name", "source_file", "source_month", "source_year", "build_date",
        "state_filter", "ct_row_count", "unique_ct_ccn_count", "survey_date_min",
        "survey_date_max", "citation_description_lookup_miss_count", "limitations",
    },
    "fire": {
        "source_name", "source_file", "source_month", "source_year", "build_date",
        "state_filter", "ct_row_count", "unique_ct_ccn_count", "survey_date_min",
        "survey_date_max", "k_tag_count", "e_tag_count",
        "citation_description_lookup_miss_count", "citation_description_lookup_missed_codes",
        "limitations",
    },
    "penalties": {
        "source_name", "source_file", "source_month", "source_year", "build_date",
        "state_filter", "ct_row_count", "unique_ct_ccn_count", "penalty_date_min",
        "penalty_date_max", "processing_date_min", "processing_date_max",
        "payment_denial_start_date_min", "payment_denial_start_date_max",
        "fine_row_count", "payment_denial_row_count", "ct_fine_amount_total",
        "payment_denial_length_total_days", "duplicate_full_row_signature_count", "limitations",
    },
    "summary": {
        "source_files", "build_date", "current_facility_count", "summary_record_count",
        "health_deficiency_row_count", "fire_safety_deficiency_row_count",
        "penalties_row_count", "health_unique_ccn_count", "fire_safety_unique_ccn_count",
        "penalties_unique_ccn_count", "source_date_ranges", "recent_window_definition",
        "source_join_coverage", "fire_safety_citation_lookup_gaps", "limitations",
    },
}

DETAIL_ARRAYS = (
    "health_deficiencies",
    "fire_safety_deficiencies",
    "emergency_preparedness_deficiencies",
    "penalties",
)

HEALTH_DETAIL_FIELDS = (
    "survey_date", "survey_year", "survey_type", "deficiency_code",
    "deficiency_description", "deficiency_category", "scope_severity_code",
    "harm_ij_group", "standard_deficiency", "complaint_deficiency",
    "infection_control_inspection_deficiency", "correction_date",
    "citation_under_idr", "citation_under_iidr", "processing_date",
    "citation_description_lookup_matched", "citation_description_category",
    "citation_description_text", "source_row_hash",
)

FIRE_DETAIL_FIELDS = (
    "survey_date", "survey_year", "survey_type", "deficiency_code",
    "deficiency_description", "deficiency_category", "tag_version",
    "scope_severity_code", "deficiency_corrected", "standard_deficiency",
    "complaint_deficiency", "correction_date", "citation_under_idr",
    "citation_under_iidr", "processing_date", "citation_description_lookup_matched",
    "citation_description_category", "citation_description_text",
    "citation_description_lookup_gap_reason", "source_row_hash",
)

PENALTY_DETAIL_FIELDS = (
    "penalty_date", "penalty_year", "penalty_type", "enforcement_category",
    "payment_denial_start_date", "processing_date", "duplicate_full_row_signature",
    "source_row_hash",
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def html_text(text: str) -> str:
    parser = TextExtractor()
    parser.feed(text)
    return normalized_text(" ".join(parser.parts))


def date_range(rows: Iterable[dict[str, Any]], field: str) -> tuple[str | None, str | None]:
    values = [str(row[field]) for row in rows if row.get(field)]
    return (min(values), max(values)) if values else (None, None)


def six_digit_ccn(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"\d{6}", value))


def numeric(value: Any) -> float:
    if isinstance(value, bool):
        raise TypeError("Boolean is not a numeric audit value")
    return float(value or 0)


def newest_first_key(row: dict[str, Any], date_field: str, stable_fields: tuple[str, ...]) -> tuple[Any, ...]:
    parsed = date.fromisoformat(str(row.get(date_field) or ""))
    return (-parsed.toordinal(), *(str(row.get(field) or "") for field in stable_fields))


def display_value(value: Any) -> str:
    """Keep verbose output useful without dumping thousands of hashes."""
    if isinstance(value, Counter) and len(value) > 12:
        return f"Counter({len(value)} keys, {sum(value.values())} values)"
    if isinstance(value, (list, tuple, set)) and len(value) > 12:
        return f"{type(value).__name__}({len(value)} items)"
    if isinstance(value, dict) and len(value) > 12:
        return f"dict({len(value)} keys)"
    return repr(value)


class ReleaseAudit:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.failures: list[str] = []
        self.section_results: list[tuple[str, bool]] = []
        self.data: dict[str, Any] = {}
        self.detail_by_ccn: dict[str, dict[str, Any]] = {}
        self.metrics: dict[str, Any] = {}
        self._section_name = "startup"

    def fail(self, message: str) -> None:
        self.failures.append(f"{self._section_name}: {message}")

    def check(self, description: str, actual: Any, expected: Any) -> bool:
        if actual != expected:
            self.fail(f"{description}: expected {expected!r}; actual {actual!r}")
            return False
        if self.verbose:
            print(f"  OK  {description}: {display_value(actual)}")
        return True

    def require(self, condition: bool, description: str, *, actual: Any = None, expected: Any = True) -> bool:
        if condition:
            if self.verbose:
                print(f"  OK  {description}")
            return True
        self.fail(f"{description}: expected {expected!r}; actual {actual!r}")
        return False

    def section(self, name: str, callback: Callable[[], None]) -> None:
        self._section_name = name
        starting_failures = len(self.failures)
        try:
            callback()
        except Exception as exc:  # collect section-level failures and continue where practical
            self.fail(f"unexpected audit exception: {type(exc).__name__}: {exc}")
        passed = len(self.failures) == starting_failures
        self.section_results.append((name, passed))
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        if not passed:
            for failure in self.failures[starting_failures:]:
                print(f"  - {failure.removeprefix(name + ': ')}")

    def load_json(self, key: str, path: Path) -> Any:
        if not path.is_file():
            self.fail(f"missing required file: {path.relative_to(ROOT).as_posix()}")
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            self.fail(f"could not parse {path.relative_to(ROOT).as_posix()}: {exc}")
            return None
        self.data[key] = value
        return value

    def rows(self, key: str, field: str) -> list[dict[str, Any]]:
        value = self.data.get(key)
        if not isinstance(value, dict):
            return []
        rows = value.get(field)
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            self.fail(f"{PATHS[key].relative_to(ROOT).as_posix()} requires an object array at {field}")
            return []
        return rows

    def audit_json_structure(self) -> None:
        for key in ("staffing", "health", "fire", "penalties", "summary", "detail_index", "manifest", "registry"):
            value = self.load_json(key, PATHS[key])
            self.require(isinstance(value, dict), f"{key} top level is a JSON object", actual=type(value).__name__)

        staffing = self.data.get("staffing", {})
        self.require(isinstance(staffing.get("facilities"), list), "staffing.facilities is an array")
        self.require(isinstance(staffing.get("sources"), list), "staffing.sources is an array")
        for key, array_key in (("health", "deficiencies"), ("fire", "deficiencies"), ("penalties", "penalties")):
            data = self.data.get(key, {})
            self.require(isinstance(data.get("metadata"), dict), f"{key}.metadata is an object")
            self.require(isinstance(data.get(array_key), list), f"{key}.{array_key} is an array")
            metadata = data.get("metadata", {})
            missing = sorted(REQUIRED_METADATA[key] - set(metadata)) if isinstance(metadata, dict) else sorted(REQUIRED_METADATA[key])
            self.check(f"{key} required metadata fields missing", missing, [])

        summary = self.data.get("summary", {})
        self.require(isinstance(summary.get("metadata"), dict), "summary.metadata is an object")
        self.require(isinstance(summary.get("facilities"), list), "summary.facilities is an array")
        summary_metadata = summary.get("metadata", {})
        missing = sorted(REQUIRED_METADATA["summary"] - set(summary_metadata)) if isinstance(summary_metadata, dict) else sorted(REQUIRED_METADATA["summary"])
        self.check("summary required metadata fields missing", missing, [])

        index = self.data.get("detail_index", {})
        required_index = {
            "build_date", "facility_file_count", "expected_current_facility_count",
            "total_health_records", "total_fire_safety_records",
            "total_emergency_preparedness_records", "total_penalty_records",
            "facilities_with_no_detail_records", "source_ccn_coverage", "source_files",
            "summary_cross_check_file", "limitations", "facilities",
        }
        self.check("detail index required fields missing", sorted(required_index - set(index)), [])
        self.require(isinstance(index.get("facilities"), list), "detail index facilities is an array")

        all_detail_json = sorted(DETAIL_DIR.glob("*.json"))
        unexpected_detail_json = [path.name for path in all_detail_json if path.name != "index.json" and not re.fullmatch(r"\d{6}\.json", path.name)]
        self.check("unexpected non-CCN detail JSON files", unexpected_detail_json, [])
        facility_files = [path for path in all_detail_json if re.fullmatch(r"\d{6}\.json", path.name)]
        for path in facility_files:
            ccn = path.stem
            detail = self.load_json(f"detail:{ccn}", path)
            if not isinstance(detail, dict):
                continue
            self.detail_by_ccn[ccn] = detail
            self.check(f"{ccn}.json top-level fields", set(detail), {"metadata", *DETAIL_ARRAYS})
            self.require(isinstance(detail.get("metadata"), dict), f"{ccn}.json metadata is an object")
            metadata = detail.get("metadata", {})
            required_detail_metadata = {
                "ccn", "provider_name", "build_date", "source_files", "health_record_count",
                "fire_safety_record_count", "emergency_preparedness_record_count",
                "penalty_record_count", "fire_lookup_gap_record_count",
                "duplicate_penalty_record_count", "limitations",
            }
            self.check(f"{ccn}.json required metadata fields missing", sorted(required_detail_metadata - set(metadata)), [])
            for array_name in DETAIL_ARRAYS:
                self.require(isinstance(detail.get(array_name), list), f"{ccn}.json {array_name} is an array")

        ccn_locations: list[tuple[str, Any]] = []
        for key, field in (("staffing", "facilities"), ("health", "deficiencies"), ("fire", "deficiencies"), ("penalties", "penalties"), ("summary", "facilities")):
            for number, row in enumerate(self.rows(key, field), start=1):
                ccn_locations.append((f"{key}.{field}[{number}].ccn", row.get("ccn")))
        for ccn, detail in self.detail_by_ccn.items():
            ccn_locations.append((f"detail {ccn} metadata.ccn", detail.get("metadata", {}).get("ccn")))
        index_facilities = index.get("facilities", []) if isinstance(index, dict) else []
        for number, row in enumerate(index_facilities, start=1):
            if isinstance(row, dict):
                ccn_locations.append((f"detail index facilities[{number}].ccn", row.get("ccn")))
        invalid = [(location, value) for location, value in ccn_locations if not six_digit_ccn(value)]
        self.check("invalid or non-string CCNs", invalid, [])

    def audit_current_coverage(self) -> None:
        staffing_rows = self.rows("staffing", "facilities")
        summary_rows = self.rows("summary", "facilities")
        staffing_ccns = [row.get("ccn") for row in staffing_rows]
        summary_ccns = [row.get("ccn") for row in summary_rows]
        detail_ccns = sorted(self.detail_by_ccn)
        self.check("current staffing facility rows", len(staffing_rows), EXPECTED["current_facilities"])
        self.check("current staffing unique CCNs", len(set(staffing_ccns)), EXPECTED["current_facilities"])
        self.check("compact summary rows", len(summary_rows), EXPECTED["current_facilities"])
        duplicate_summary = sorted(ccn for ccn, count in Counter(summary_ccns).items() if count != 1)
        self.check("summary duplicate CCNs", duplicate_summary, [])
        self.check("missing summary CCNs", sorted(set(staffing_ccns) - set(summary_ccns)), [])
        self.check("unexpected summary CCNs", sorted(set(summary_ccns) - set(staffing_ccns)), [])
        self.check("CCN-named detail files", len(detail_ccns), EXPECTED["current_facilities"])
        self.check("missing detail CCNs", sorted(set(staffing_ccns) - set(detail_ccns)), [])
        self.check("unexpected detail CCNs", sorted(set(detail_ccns) - set(staffing_ccns)), [])

    def audit_health(self) -> None:
        rows = self.rows("health", "deficiencies")
        metadata = self.data["health"]["metadata"]
        groups = Counter(row.get("harm_ij_group") for row in rows)
        mapping = {
            "J": "immediate_jeopardy", "K": "immediate_jeopardy", "L": "immediate_jeopardy",
            "G": "actual_harm_not_ij", "H": "actual_harm_not_ij", "I": "actual_harm_not_ij",
            "D": "no_actual_harm_more_than_minimal", "E": "no_actual_harm_more_than_minimal",
            "F": "no_actual_harm_more_than_minimal", "A": "no_actual_harm_minimal",
            "B": "no_actual_harm_minimal", "C": "no_actual_harm_minimal",
        }
        grouping_mismatches = []
        for number, row in enumerate(rows, start=1):
            code = str(row.get("scope_severity_code") or "").strip().upper()
            expected_group = mapping.get(code, "unknown_or_unmapped")
            if row.get("harm_ij_group") != expected_group:
                grouping_mismatches.append((number, code, row.get("harm_ij_group"), expected_group))
        self.check("health rows", len(rows), EXPECTED["health_rows"])
        self.check("health unique CCNs", len({row.get("ccn") for row in rows}), EXPECTED["health_ccns"])
        self.check("health survey date range", date_range(rows, "survey_date"), EXPECTED["health_dates"])
        self.check("health distinct F-tags", len({row.get("deficiency_code") for row in rows}), EXPECTED["health_distinct_tags"])
        misses = sum(row.get("citation_description_lookup_matched") is not True for row in rows)
        self.check("health citation-description lookup misses", misses, EXPECTED["health_lookup_misses"])
        self.check("health harm group counts", dict(groups), EXPECTED["health_groups"])
        self.check("health scope/severity grouping mismatches", grouping_mismatches, [])
        self.check("health metadata row count", metadata.get("ct_row_count"), len(rows))
        self.check("health metadata F-tag count", metadata.get("f_tag_count"), len(rows))
        self.check("health metadata unique CCNs", metadata.get("unique_ct_ccn_count"), len({row.get("ccn") for row in rows}))
        self.check("health metadata date range", (metadata.get("survey_date_min"), metadata.get("survey_date_max")), date_range(rows, "survey_date"))
        self.check("health metadata lookup misses", metadata.get("citation_description_lookup_miss_count"), misses)
        self.check("health May 2026 source metadata", (metadata.get("source_file"), metadata.get("source_month"), metadata.get("source_year"), metadata.get("state_filter")), ("NH_HealthCitations_May2026.csv", "May", 2026, "CT"))
        self.check("health citation-description source", metadata.get("citation_descriptions_source_file"), "NH_CitationDescriptions_May2026.csv")

    def audit_fire(self) -> None:
        rows = self.rows("fire", "deficiencies")
        metadata = self.data["fire"]["metadata"]
        prefixes = Counter(row.get("deficiency_prefix") for row in rows)
        misses_by_code = Counter(
            row.get("deficiency_code") for row in rows
            if row.get("citation_description_lookup_matched") is not True
        )
        scope_counts = Counter(row.get("scope_severity_code") for row in rows)
        missing_source_descriptions = [
            row.get("source_row_hash") for row in rows
            if row.get("deficiency_code") in EXPECTED["fire_lookup_codes"]
            and not str(row.get("deficiency_description") or "").strip()
        ]
        unflagged_gaps = [
            row.get("source_row_hash") for row in rows
            if row.get("deficiency_code") in EXPECTED["fire_lookup_codes"]
            and (row.get("citation_description_lookup_matched") is not False
                 or not str(row.get("citation_description_lookup_gap_reason") or "").strip())
        ]
        self.check("fire/emergency rows", len(rows), EXPECTED["fire_rows"])
        self.check("fire/emergency unique CCNs", len({row.get("ccn") for row in rows}), EXPECTED["fire_ccns"])
        self.check("Fire Safety K rows", prefixes.get("K", 0), EXPECTED["fire_k_rows"])
        self.check("Emergency Preparedness E rows", prefixes.get("E", 0), EXPECTED["fire_e_rows"])
        self.check("unexpected Fire Safety prefixes", sorted(set(prefixes) - {"K", "E"}), [])
        self.check("fire/emergency distinct citation codes", len({row.get("deficiency_code") for row in rows}), EXPECTED["fire_distinct_codes"])
        self.check("fire/emergency survey date range", date_range(rows, "survey_date"), EXPECTED["fire_dates"])
        self.check("fire/emergency lookup misses", sum(misses_by_code.values()), EXPECTED["fire_lookup_misses"])
        self.check("lookup misses by code", dict(misses_by_code), EXPECTED["fire_lookup_codes"])
        self.check("fire/emergency scope/severity counts", dict(scope_counts), EXPECTED["fire_scope_counts"])
        self.check("health grouping fields on fire/emergency records", sum("harm_ij_group" in row for row in rows), 0)
        self.check("lookup-gap rows missing source descriptions", missing_source_descriptions, [])
        self.check("lookup-gap rows not transparently flagged", unflagged_gaps, [])
        self.check("fire metadata row count", metadata.get("ct_row_count"), len(rows))
        self.check("fire metadata unique CCNs", metadata.get("unique_ct_ccn_count"), len({row.get("ccn") for row in rows}))
        self.check("fire metadata date range", (metadata.get("survey_date_min"), metadata.get("survey_date_max")), date_range(rows, "survey_date"))
        self.check("fire metadata K rows", metadata.get("k_tag_count"), prefixes.get("K", 0))
        self.check("fire metadata E rows", metadata.get("e_tag_count"), prefixes.get("E", 0))
        self.check("fire metadata lookup-miss total", metadata.get("citation_description_lookup_miss_count"), sum(misses_by_code.values()))
        self.check("fire metadata lookup gaps", metadata.get("citation_description_lookup_missed_codes"), dict(misses_by_code))
        self.check("fire May 2026 source metadata", (metadata.get("source_file"), metadata.get("source_month"), metadata.get("source_year"), metadata.get("state_filter")), ("NH_FireSafetyCitations_May2026.csv", "May", 2026, "CT"))
        self.check("fire citation-description source", metadata.get("citation_descriptions_source_file"), "NH_CitationDescriptions_May2026.csv")

    def audit_penalties(self) -> None:
        rows = self.rows("penalties", "penalties")
        metadata = self.data["penalties"]["metadata"]
        categories = Counter(row.get("enforcement_category") for row in rows)
        fine_rows = [row for row in rows if row.get("enforcement_category") == "fine"]
        denial_rows = [row for row in rows if row.get("enforcement_category") == "payment_denial"]
        duplicate_rows = sum(row.get("duplicate_full_row_signature") is True for row in rows)
        duplicate_signatures = sum(count > 1 for count in Counter(row.get("source_row_hash") for row in rows).values())
        fine_total = round(sum(numeric(row.get("normalized_fine_amount")) for row in fine_rows), 2)
        denial_days = sum(int(numeric(row.get("payment_denial_length_days"))) for row in denial_rows)
        invalid_amounts = [
            row.get("source_row_hash") for row in rows
            if (row.get("enforcement_category") == "fine"
                and (row.get("fine_amount") is None or row.get("normalized_fine_amount") is None))
            or (row.get("enforcement_category") == "payment_denial"
                and (row.get("fine_amount") is not None or row.get("normalized_fine_amount") is not None))
        ]
        invalid_denials = [
            row.get("source_row_hash") for row in rows
            if (row.get("enforcement_category") == "payment_denial"
                and (not row.get("payment_denial_start_date") or row.get("payment_denial_length_days") is None))
            or (row.get("enforcement_category") == "fine"
                and (row.get("payment_denial_start_date") is not None or row.get("payment_denial_length_days") is not None))
        ]
        self.check("penalty rows", len(rows), EXPECTED["penalty_rows"])
        self.check("penalty unique CCNs", len({row.get("ccn") for row in rows}), EXPECTED["penalty_ccns"])
        self.check("enforcement category counts", dict(categories), {"fine": 167, "payment_denial": 12})
        self.check("Fine source type count", sum(row.get("penalty_type") == "Fine" for row in rows), EXPECTED["fine_rows"])
        self.check("Payment Denial source type count", sum(row.get("penalty_type") == "Payment Denial" for row in rows), EXPECTED["payment_denial_rows"])
        self.check("fine total", fine_total, EXPECTED["fine_total"])
        self.check("payment-denial days", denial_days, EXPECTED["denial_days"])
        self.check("flagged duplicate source rows", duplicate_rows, EXPECTED["duplicate_penalty_rows"])
        self.check("duplicated full-row signatures", duplicate_signatures, EXPECTED["duplicate_penalty_rows"])
        self.check("penalty date range", date_range(rows, "penalty_date"), EXPECTED["penalty_dates"])
        self.check("processing date range", date_range(rows, "processing_date"), EXPECTED["processing_dates"])
        self.check("payment-denial start-date range", date_range(denial_rows, "payment_denial_start_date"), EXPECTED["denial_start_dates"])
        self.check("fine amounts on inappropriate rows", invalid_amounts, [])
        self.check("payment-denial fields on inappropriate rows", invalid_denials, [])
        self.require(all(row.get("penalty_date") and row.get("processing_date") for row in rows), "penalty and processing dates remain populated separately")
        self.check("penalties metadata row count", metadata.get("ct_row_count"), len(rows))
        self.check("penalties metadata unique CCNs", metadata.get("unique_ct_ccn_count"), len({row.get("ccn") for row in rows}))
        self.check("penalties metadata fine rows", metadata.get("fine_row_count"), len(fine_rows))
        self.check("penalties metadata payment-denial rows", metadata.get("payment_denial_row_count"), len(denial_rows))
        self.check("penalties metadata duplicate rows", metadata.get("duplicate_full_row_signature_count"), duplicate_rows)
        self.check("penalties metadata penalty dates", (metadata.get("penalty_date_min"), metadata.get("penalty_date_max")), date_range(rows, "penalty_date"))
        self.check("penalties metadata processing dates", (metadata.get("processing_date_min"), metadata.get("processing_date_max")), date_range(rows, "processing_date"))
        self.check("penalties metadata denial start dates", (metadata.get("payment_denial_start_date_min"), metadata.get("payment_denial_start_date_max")), date_range(denial_rows, "payment_denial_start_date"))
        self.check("penalties metadata fine total", metadata.get("ct_fine_amount_total"), fine_total)
        self.check("penalties metadata denial days", metadata.get("payment_denial_length_total_days"), denial_days)
        self.check("penalties May 2026 source metadata", (metadata.get("source_file"), metadata.get("source_month"), metadata.get("source_year"), metadata.get("state_filter")), ("NH_Penalties_May2026.csv", "May", 2026, "CT"))

    def audit_summary(self) -> None:
        rows = self.rows("summary", "facilities")
        metadata = self.data["summary"]["metadata"]
        recent = metadata.get("recent_window_definition", {})
        self.check("summary facility rows", len(rows), EXPECTED["current_facilities"])
        self.check("recent window start/end", (recent.get("start_date"), recent.get("end_date")), EXPECTED["recent_window"])
        self.check("recent window is inclusive", recent.get("inclusive"), True)
        self.check("health facility coverage", sum(bool(row.get("has_health_deficiency_records")) for row in rows), EXPECTED["health_ccns"])
        self.check("fire/emergency facility coverage", sum(bool(row.get("has_fire_safety_records")) for row in rows), EXPECTED["fire_ccns"])
        self.check("penalty facility coverage", sum(bool(row.get("has_penalty_records")) for row in rows), EXPECTED["penalty_ccns"])
        zero_rows = [row for row in rows if not any((row.get("has_health_deficiency_records"), row.get("has_fire_safety_records"), row.get("has_penalty_records")))]
        self.check("zero-record facilities", len(zero_rows), EXPECTED["zero_record_facilities"])
        for field, expected in {**EXPECTED["summary_all_time"], **EXPECTED["summary_recent"]}.items():
            actual = round(sum(numeric(row.get(field)) for row in rows), 2) if field.endswith("fine_total") else sum(int(numeric(row.get(field))) for row in rows)
            self.check(f"summary aggregate {field}", actual, expected)
        count_fields = [field for field in rows[0] if field.startswith(("all_time_", "recent_")) and not field.endswith("date")]
        invalid_zero_rows = []
        for row in zero_rows:
            if any(numeric(row.get(field)) != 0 for field in count_fields):
                invalid_zero_rows.append((row.get("ccn"), "nonzero numeric value"))
            if any(row.get(field) is not None for field in ("latest_health_survey_date", "latest_fire_safety_survey_date", "latest_penalty_date")):
                invalid_zero_rows.append((row.get("ccn"), "latest date not null"))
            combined = normalized_text(json.dumps({"flags": row.get("survey_enforcement_caution_flags"), "limits": row.get("summary_limitations")}))
            if "available" not in combined and "source" not in combined:
                invalid_zero_rows.append((row.get("ccn"), "missing limited-source caution"))
        self.check("zero-record facility representation errors", invalid_zero_rows, [])
        self.check("summary metadata record count", metadata.get("summary_record_count"), len(rows))
        self.check("summary metadata current facilities", metadata.get("current_facility_count"), EXPECTED["current_facilities"])
        self.check("summary metadata runtime rows", (metadata.get("health_deficiency_row_count"), metadata.get("fire_safety_deficiency_row_count"), metadata.get("penalties_row_count")), (6761, 2135, 179))
        runtime_rows = {
            "health": self.rows("health", "deficiencies"),
            "fire": self.rows("fire", "deficiencies"),
            "penalties": self.rows("penalties", "penalties"),
        }
        self.check(
            "summary metadata source date ranges",
            metadata.get("source_date_ranges"),
            {
                "health_survey_dates": {"min": date_range(runtime_rows["health"], "survey_date")[0], "max": date_range(runtime_rows["health"], "survey_date")[1]},
                "fire_safety_survey_dates": {"min": date_range(runtime_rows["fire"], "survey_date")[0], "max": date_range(runtime_rows["fire"], "survey_date")[1]},
                "penalty_dates": {"min": date_range(runtime_rows["penalties"], "penalty_date")[0], "max": date_range(runtime_rows["penalties"], "penalty_date")[1]},
            },
        )
        coverage_expected = {
            "health_deficiencies": len({row["ccn"] for row in runtime_rows["health"]}),
            "fire_safety_deficiencies": len({row["ccn"] for row in runtime_rows["fire"]}),
            "penalties": len({row["ccn"] for row in runtime_rows["penalties"]}),
        }
        coverage_errors = []
        for key, expected_count in coverage_expected.items():
            coverage = metadata.get("source_join_coverage", {}).get(key, {})
            expected_coverage = {
                "unique_source_ccn_count": expected_count,
                "joined_current_ccn_count": expected_count,
                "unmatched_source_ccn_count": 0,
                "unmatched_source_ccns": [],
            }
            if coverage != expected_coverage:
                coverage_errors.append((key, coverage, expected_coverage))
        self.check("summary metadata source-join coverage errors", coverage_errors, [])
        self.check("summary metadata lookup gaps", metadata.get("fire_safety_citation_lookup_gaps"), EXPECTED["fire_lookup_codes"])

    def audit_facility_details(self) -> None:
        index = self.data["detail_index"]
        index_rows = index.get("facilities", [])
        index_by_ccn = {row.get("ccn"): row for row in index_rows if isinstance(row, dict)}
        self.check("detail files excluding index", len(self.detail_by_ccn), EXPECTED["current_facilities"])
        self.check("index facility count", index.get("facility_file_count"), EXPECTED["current_facilities"])
        self.check("index facility entries", len(index_rows), EXPECTED["current_facilities"])
        self.check("index unique facility entries", len(index_by_ccn), EXPECTED["current_facilities"])

        actual_totals = Counter()
        actual_hashes = {name: Counter() for name in DETAIL_ARRAYS}
        ordering_errors: list[tuple[str, str]] = []
        metadata_errors: list[tuple[str, str, Any, Any]] = []
        index_errors: list[tuple[str, str, Any, Any]] = []
        per_facility_hash_errors: list[tuple[str, str]] = []
        health_group_missing: list[str] = []
        nonhealth_group_present: list[tuple[str, str]] = []
        staffing_by_ccn = {row["ccn"]: row for row in self.rows("staffing", "facilities")}
        runtime_by_ccn: dict[str, dict[str, Counter[Any]]] = {
            ccn: {name: Counter() for name in DETAIL_ARRAYS} for ccn in staffing_by_ccn
        }
        projected_by_ccn: dict[str, dict[str, Counter[str]]] = {
            ccn: {name: Counter() for name in DETAIL_ARRAYS} for ccn in staffing_by_ccn
        }

        def canonical(record: dict[str, Any]) -> str:
            return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

        for row in self.rows("health", "deficiencies"):
            runtime_by_ccn[row["ccn"]]["health_deficiencies"][row.get("source_row_hash")] += 1
            projected_by_ccn[row["ccn"]]["health_deficiencies"][canonical({field: row[field] for field in HEALTH_DETAIL_FIELDS})] += 1
        for row in self.rows("fire", "deficiencies"):
            target = "fire_safety_deficiencies" if row.get("deficiency_prefix") == "K" else "emergency_preparedness_deficiencies"
            runtime_by_ccn[row["ccn"]][target][row.get("source_row_hash")] += 1
            projected_by_ccn[row["ccn"]][target][canonical({field: row[field] for field in FIRE_DETAIL_FIELDS})] += 1
        for row in self.rows("penalties", "penalties"):
            runtime_by_ccn[row["ccn"]]["penalties"][row.get("source_row_hash")] += 1
            projection = {field: row[field] for field in PENALTY_DETAIL_FIELDS}
            projection["fine_amount"] = None if row.get("normalized_fine_amount") is None else float(row["normalized_fine_amount"])
            projection["payment_denial_length_days"] = None if row.get("payment_denial_length_days") is None else int(row["payment_denial_length_days"])
            projected_by_ccn[row["ccn"]]["penalties"][canonical(projection)] += 1
        for ccn, detail in self.detail_by_ccn.items():
            metadata = detail["metadata"]
            arrays = {name: detail[name] for name in DETAIL_ARRAYS}
            counts = {
                "health_record_count": len(arrays["health_deficiencies"]),
                "fire_safety_record_count": len(arrays["fire_safety_deficiencies"]),
                "emergency_preparedness_record_count": len(arrays["emergency_preparedness_deficiencies"]),
                "penalty_record_count": len(arrays["penalties"]),
            }
            for field, actual in counts.items():
                if metadata.get(field) != actual:
                    metadata_errors.append((ccn, field, metadata.get(field), actual))
            if metadata.get("ccn") != ccn:
                metadata_errors.append((ccn, "ccn", metadata.get("ccn"), ccn))
            expected_name = staffing_by_ccn.get(ccn, {}).get("provider_name")
            if metadata.get("provider_name") != expected_name:
                metadata_errors.append((ccn, "provider_name", metadata.get("provider_name"), expected_name))
            fire_rows = arrays["fire_safety_deficiencies"] + arrays["emergency_preparedness_deficiencies"]
            gap_count = sum(row.get("citation_description_lookup_matched") is False for row in fire_rows)
            duplicate_count = sum(row.get("duplicate_full_row_signature") is True for row in arrays["penalties"])
            if metadata.get("fire_lookup_gap_record_count") != gap_count:
                metadata_errors.append((ccn, "fire_lookup_gap_record_count", metadata.get("fire_lookup_gap_record_count"), gap_count))
            if metadata.get("duplicate_penalty_record_count") != duplicate_count:
                metadata_errors.append((ccn, "duplicate_penalty_record_count", metadata.get("duplicate_penalty_record_count"), duplicate_count))
            for name, rows in arrays.items():
                actual_totals[name] += len(rows)
                facility_hashes = Counter(row.get("source_row_hash") for row in rows)
                actual_hashes[name].update(facility_hashes)
                if facility_hashes != runtime_by_ccn[ccn][name]:
                    per_facility_hash_errors.append((ccn, name))
                if Counter(canonical(row) for row in rows) != projected_by_ccn[ccn][name]:
                    per_facility_hash_errors.append((ccn, f"{name}:field_projection"))
            sort_specs = {
                "health_deficiencies": ("survey_date", ("deficiency_code", "source_row_hash")),
                "fire_safety_deficiencies": ("survey_date", ("deficiency_code", "source_row_hash")),
                "emergency_preparedness_deficiencies": ("survey_date", ("deficiency_code", "source_row_hash")),
                "penalties": ("penalty_date", ("penalty_type", "source_row_hash")),
            }
            for name, (date_field, stable_fields) in sort_specs.items():
                rows = arrays[name]
                if rows != sorted(rows, key=lambda row, d=date_field, s=stable_fields: newest_first_key(row, d, s)):
                    ordering_errors.append((ccn, name))
            health_group_missing.extend(f"{ccn}:{row.get('source_row_hash')}" for row in arrays["health_deficiencies"] if "harm_ij_group" not in row)
            for name in ("fire_safety_deficiencies", "emergency_preparedness_deficiencies", "penalties"):
                nonhealth_group_present.extend((ccn, name) for row in arrays[name] if "harm_ij_group" in row)
            index_row = index_by_ccn.get(ccn)
            if index_row is None:
                index_errors.append((ccn, "entry", None, "present"))
            else:
                expected_index_values = {
                    **counts,
                    "total_detail_record_count": sum(counts.values()),
                    "file_size_bytes": (DETAIL_DIR / f"{ccn}.json").stat().st_size,
                }
                for field, actual in expected_index_values.items():
                    if index_row.get(field) != actual:
                        index_errors.append((ccn, field, index_row.get(field), actual))

        expected_detail_totals = {
            "health_deficiencies": EXPECTED["health_rows"],
            "fire_safety_deficiencies": EXPECTED["fire_k_rows"],
            "emergency_preparedness_deficiencies": EXPECTED["fire_e_rows"],
            "penalties": EXPECTED["penalty_rows"],
        }
        self.check("detail array aggregate totals", dict(actual_totals), expected_detail_totals)
        self.check("detail metadata count mismatches", metadata_errors, [])
        self.check("detail index count/size mismatches", index_errors, [])
        self.check("per-facility source-row multiset mismatches", per_facility_hash_errors, [])
        self.check("detail stable newest-first ordering errors", ordering_errors, [])
        self.check("health detail records missing harm grouping", health_group_missing, [])
        self.check("non-health detail records with health grouping", nonhealth_group_present, [])

        runtime_hashes = {
            "health_deficiencies": Counter(row.get("source_row_hash") for row in self.rows("health", "deficiencies")),
            "fire_safety_deficiencies": Counter(row.get("source_row_hash") for row in self.rows("fire", "deficiencies") if row.get("deficiency_prefix") == "K"),
            "emergency_preparedness_deficiencies": Counter(row.get("source_row_hash") for row in self.rows("fire", "deficiencies") if row.get("deficiency_prefix") == "E"),
            "penalties": Counter(row.get("source_row_hash") for row in self.rows("penalties", "penalties")),
        }
        for name in DETAIL_ARRAYS:
            self.check(f"{name} source-row multiset reconciliation", actual_hashes[name], runtime_hashes[name])

        fire_details = [row for detail in self.detail_by_ccn.values() for name in ("fire_safety_deficiencies", "emergency_preparedness_deficiencies") for row in detail[name]]
        gap_counts = Counter(row.get("deficiency_code") for row in fire_details if row.get("citation_description_lookup_matched") is False)
        self.check("detail K-0211/K-0133 lookup gaps", dict(gap_counts), EXPECTED["fire_lookup_codes"])
        duplicate_flags = sum(row.get("duplicate_full_row_signature") is True for detail in self.detail_by_ccn.values() for row in detail["penalties"])
        self.check("detail duplicate penalty flags", duplicate_flags, EXPECTED["duplicate_penalty_rows"])
        zero_count = sum(sum(len(detail[name]) for name in DETAIL_ARRAYS) == 0 for detail in self.detail_by_ccn.values())
        self.check("detail zero-record facilities", zero_count, EXPECTED["zero_record_facilities"])
        self.check("index zero-record facilities", index.get("facilities_with_no_detail_records"), zero_count)
        self.check("index aggregate totals", (index.get("total_health_records"), index.get("total_fire_safety_records"), index.get("total_emergency_preparedness_records"), index.get("total_penalty_records")), (6761, 2007, 128, 179))
        self.check(
            "index source CCN coverage",
            index.get("source_ccn_coverage"),
            {
                "health_unique_ccn_count": EXPECTED["health_ccns"],
                "fire_safety_and_emergency_preparedness_unique_ccn_count": EXPECTED["fire_ccns"],
                "penalties_unique_ccn_count": EXPECTED["penalty_ccns"],
            },
        )

    @staticmethod
    def facility_summary(detail: dict[str, Any], recent_start: str, recent_end: str) -> dict[str, Any]:
        health = detail["health_deficiencies"]
        fire = detail["fire_safety_deficiencies"]
        emergency = detail["emergency_preparedness_deficiencies"]
        penalties = detail["penalties"]
        recent_health = [row for row in health if recent_start <= row["survey_date"] <= recent_end]
        recent_fire = [row for row in fire if recent_start <= row["survey_date"] <= recent_end]
        recent_emergency = [row for row in emergency if recent_start <= row["survey_date"] <= recent_end]
        recent_penalties = [row for row in penalties if recent_start <= row["penalty_date"] <= recent_end]

        def fine_total(rows: list[dict[str, Any]]) -> float:
            return round(sum(numeric(row.get("fine_amount")) for row in rows if row.get("enforcement_category") == "fine"), 2)

        def denial_days(rows: list[dict[str, Any]]) -> int:
            return sum(int(numeric(row.get("payment_denial_length_days"))) for row in rows if row.get("enforcement_category") == "payment_denial")

        return {
            "has_health_deficiency_records": bool(health),
            "has_fire_safety_records": bool(fire or emergency),
            "has_penalty_records": bool(penalties),
            "latest_health_survey_date": max((row["survey_date"] for row in health), default=None),
            "latest_fire_safety_survey_date": max((row["survey_date"] for row in fire + emergency), default=None),
            "latest_penalty_date": max((row["penalty_date"] for row in penalties), default=None),
            "all_time_health_deficiency_count": len(health),
            "all_time_actual_harm_count": sum(row.get("harm_ij_group") == "actual_harm_not_ij" for row in health),
            "all_time_immediate_jeopardy_count": sum(row.get("harm_ij_group") == "immediate_jeopardy" for row in health),
            "all_time_fire_safety_citation_count": len(fire),
            "all_time_emergency_preparedness_citation_count": len(emergency),
            "all_time_enforcement_event_count": len(penalties),
            "all_time_fine_count": sum(row.get("enforcement_category") == "fine" for row in penalties),
            "all_time_fine_total": fine_total(penalties),
            "all_time_payment_denial_count": sum(row.get("enforcement_category") == "payment_denial" for row in penalties),
            "all_time_payment_denial_days": denial_days(penalties),
            "recent_health_deficiency_count": len(recent_health),
            "recent_actual_harm_count": sum(row.get("harm_ij_group") == "actual_harm_not_ij" for row in recent_health),
            "recent_immediate_jeopardy_count": sum(row.get("harm_ij_group") == "immediate_jeopardy" for row in recent_health),
            "recent_fire_safety_citation_count": len(recent_fire),
            "recent_emergency_preparedness_citation_count": len(recent_emergency),
            "recent_enforcement_event_count": len(recent_penalties),
            "recent_fine_count": sum(row.get("enforcement_category") == "fine" for row in recent_penalties),
            "recent_fine_total": fine_total(recent_penalties),
            "recent_payment_denial_count": sum(row.get("enforcement_category") == "payment_denial" for row in recent_penalties),
            "recent_payment_denial_days": denial_days(recent_penalties),
        }

    def audit_cross_layer(self) -> None:
        summary_rows = self.rows("summary", "facilities")
        summary_by_ccn = {row["ccn"]: row for row in summary_rows}
        recent = self.data["summary"]["metadata"]["recent_window_definition"]
        mismatches: list[tuple[str, str, Any, Any]] = []
        for ccn, detail in self.detail_by_ccn.items():
            calculated = self.facility_summary(detail, recent["start_date"], recent["end_date"])
            summary = summary_by_ccn.get(ccn, {})
            for field, actual in calculated.items():
                if summary.get(field) != actual:
                    mismatches.append((ccn, field, summary.get(field), actual))
        self.check("per-facility detail-to-summary mismatches", mismatches, [])
        self.check("facilities reconciled across detail and summary", len(self.detail_by_ccn) - len({row[0] for row in mismatches}), EXPECTED["current_facilities"])

    def audit_manifest_registry(self) -> None:
        manifest = self.data["manifest"]
        registry = self.data["registry"]
        manifest_sources = {row.get("source_key"): row for row in manifest.get("sources", []) if isinstance(row, dict)}
        runtime_metadata = {key: self.data[key]["metadata"] for key in ("health", "fire", "penalties")}
        source_keys = {
            "health": "cms_health_deficiencies",
            "fire": "cms_fire_safety_deficiencies",
            "penalties": "cms_penalties_enforcement",
        }
        errors: list[str] = []
        for runtime_key, source_key in source_keys.items():
            record = manifest_sources.get(source_key)
            if not record:
                errors.append(f"missing manifest source {source_key}")
                continue
            meta = runtime_metadata[runtime_key]
            record_text = normalized_text(json.dumps(record, ensure_ascii=False))
            required_values = [meta["source_file"]]
            if runtime_key in {"health", "fire"}:
                required_values.extend([meta["survey_date_min"], meta["survey_date_max"]])
            else:
                required_values.extend([meta["penalty_date_min"], meta["penalty_date_max"], meta["processing_date_min"]])
            required_values.extend([
                "data/nursing_home_survey_enforcement_summary_ct.json",
                "data/nursing_home_survey_enforcement_details_ct/{CCN}.json",
            ])
            for value in required_values:
                if normalized_text(str(value)) not in record_text:
                    errors.append(f"{source_key} missing runtime-derived marker {value!r}")
            if "integrated" not in normalized_text(str(record.get("integrated_status"))):
                errors.append(f"{source_key} does not identify integrated UI status")
        manifest_text = normalized_text(json.dumps(manifest, ensure_ascii=False))
        registry_text = normalized_text(json.dumps(registry, ensure_ascii=False))
        source_file_markers = [
            runtime_metadata["health"]["source_file"],
            runtime_metadata["health"]["citation_descriptions_source_file"],
            runtime_metadata["fire"]["source_file"],
            runtime_metadata["penalties"]["source_file"],
        ]
        for marker in source_file_markers:
            if normalized_text(marker) not in manifest_text:
                errors.append(f"manifest missing CMS source filename {marker!r}")
        shared_markers = [
            "data/nursing_home_health_deficiencies_ct.json",
            "data/nursing_home_fire_safety_deficiencies_ct.json",
            "data/nursing_home_penalties_ct.json",
            "data/nursing_home_survey_enforcement_summary_ct.json",
            "data/nursing_home_survey_enforcement_details_ct/{CCN}.json",
            *EXPECTED["recent_window"], "K-0211", "K-0133",
        ]
        for label, text in (("manifest", manifest_text), ("registry", registry_text)):
            for marker in shared_markers:
                if normalized_text(marker) not in text:
                    errors.append(f"{label} missing marker {marker!r}")
        if "may 2026" not in registry_text:
            errors.append("registry missing May 2026 CMS source-release marker")
        registry_requirements = ["selected facility", "view detailed findings", "staffing classification", "compact summary"]
        for marker in registry_requirements:
            if marker not in registry_text:
                errors.append(f"registry missing UI/separation marker {marker!r}")
        self.check("manifest and registry consistency errors", errors, [])

    def audit_methodology(self) -> None:
        raw = PATHS["methodology"].read_text(encoding="utf-8")
        text = html_text(raw)
        raw_normalized = normalized_text(raw)
        health_meta = self.data["health"]["metadata"]
        fire_meta = self.data["fire"]["metadata"]
        penalty_meta = self.data["penalties"]["metadata"]
        raw_markers = [
            health_meta["source_file"], fire_meta["source_file"],
            health_meta["citation_descriptions_source_file"], penalty_meta["source_file"],
            health_meta["survey_date_min"], health_meta["survey_date_max"],
            fire_meta["survey_date_min"], fire_meta["survey_date_max"],
            penalty_meta["penalty_date_min"], penalty_meta["penalty_date_max"],
            *EXPECTED["recent_window"],
        ]
        text_markers = [
            "j, k, or l", "g, h, or i", "d, e, or f", "a, b, or c",
            "immediate jeopardy", "actual harm, not immediate jeopardy",
            "potential for more than minimal harm", "potential for minimal harm",
            "k-0211", "k-0133", "three duplicated full-row signatures",
            "penalty date", "payment-denial start date", "processing date",
            "196 facilities", "191 current ccns", "178 current ccns", "102 current ccns",
            "five current facility records", "do not change a facility's staffing classification",
            "not a standalone quality score", "citation counts", "fine amounts",
            "does not mean a facility has never had a deficiency or enforcement action",
        ]
        missing = [marker for marker in raw_markers if normalized_text(str(marker)) not in raw_normalized]
        missing.extend(marker for marker in text_markers if normalized_text(str(marker)) not in text)
        self.check("methodology semantic markers missing", missing, [])

    def audit_loading_architecture(self) -> None:
        javascript = PATHS["javascript"].read_text(encoding="utf-8")
        explorer = PATHS["explorer"].read_text(encoding="utf-8")
        combined = javascript + "\n" + explorer
        errors: list[str] = []
        required_js = {
            "compact summary reference": "nursing_home_survey_enforcement_summary_ct.json",
            "detail directory": "nursing_home_survey_enforcement_details_ct",
            "six-digit detail validation": r"/^\d{6}$/",
            "explicit detail action": "data-survey-detail-action=\"toggle\"",
            "user-facing action label": "View detailed findings",
            "session cache": "surveyEnforcementDetailCache = new Map()",
            "request-token stale protection": "surveyEnforcementDetailRequestToken",
            "loading state": "state.status === 'loading'",
            "empty state": "survey-detail-empty",
            "error state": "state.status === 'error'",
            "retry state": "data-survey-detail-action=\"retry\"",
            "collapsed state": "surveyEnforcementDetailState.isOpen = false",
            "escaped source description": "escapeHtml(record.deficiency_description",
            "escaped lookup-gap reason": "escapeHtml(record.citation_description_lookup_gap_reason)",
        }
        for label, marker in required_js.items():
            if marker not in combined:
                errors.append(f"missing {label} marker {marker!r}")
        prohibited = (
            "nursing_home_health_deficiencies_ct.json",
            "nursing_home_fire_safety_deficiencies_ct.json",
            "nursing_home_penalties_ct.json",
        )
        for filename in prohibited:
            if filename in combined:
                errors.append(f"Facility Explorer references prohibited statewide runtime {filename}")

        handler_start = javascript.find("function handleSurveyEnforcementDetailAction")
        handler_end = javascript.find("function handleSurveyEnforcementDetailSectionToggle", handler_start)
        handler = javascript[handler_start:handler_end] if handler_start >= 0 and handler_end > handler_start else ""
        detail_calls = [match.start() for match in re.finditer(r"\bloadSurveyEnforcementDetails\(", javascript)]
        calls_in_handler = [position for position in detail_calls if handler_start <= position < handler_end]
        self.check("detail loader call sites", len(detail_calls), 3)  # declaration plus toggle and retry calls
        self.check("user-handler detail loader calls", len(calls_in_handler), 2)
        if "loadSurveyEnforcementDetails" in javascript[:handler_start].replace("async function loadSurveyEnforcementDetails", ""):
            errors.append("detail loading appears before the explicit-action handler")
        self.check("Facility Explorer loading architecture errors", errors, [])

    def audit_performance(self) -> None:
        runtime_sizes = {key: PATHS[key].stat().st_size for key in ("health", "fire", "penalties")}
        summary_size = PATHS["summary"].stat().st_size
        index_size = PATHS["detail_index"].stat().st_size
        facility_paths = sorted(DETAIL_DIR.glob("[0-9][0-9][0-9][0-9][0-9][0-9].json"))
        facility_sizes = [path.stat().st_size for path in facility_paths]
        directory_size = sum(path.stat().st_size for path in DETAIL_DIR.iterdir() if path.is_file())
        statewide_size = sum(runtime_sizes.values())
        median_size = statistics.median(facility_sizes)
        largest_by_records = sorted(
            (
                {
                    "ccn": ccn,
                    "provider_name": detail["metadata"]["provider_name"],
                    "records": sum(len(detail[name]) for name in DETAIL_ARRAYS),
                    "bytes": (DETAIL_DIR / f"{ccn}.json").stat().st_size,
                }
                for ccn, detail in self.detail_by_ccn.items()
            ),
            key=lambda item: (-item["records"], item["provider_name"].casefold(), item["ccn"]),
        )[:10]
        self.metrics["performance"] = {
            "runtime_sizes": runtime_sizes,
            "statewide_runtime_total": statewide_size,
            "summary_size": summary_size,
            "index_size": index_size,
            "facility_file_count": len(facility_paths),
            "facility_files_total": sum(facility_sizes),
            "detail_directory_total": directory_size,
            "minimum_facility_size": min(facility_sizes),
            "maximum_facility_size": max(facility_sizes),
            "median_facility_size": median_size,
            "average_facility_size": statistics.mean(facility_sizes),
            "median_transfer_reduction_percent": round((1 - median_size / statewide_size) * 100, 3),
            "largest_facilities_by_record_count": largest_by_records,
        }
        self.check("performance facility file count", len(facility_paths), EXPECTED["current_facilities"])
        self.require(all(size > 0 for size in (*runtime_sizes.values(), summary_size, index_size, *facility_sizes)), "all audited payload sizes are positive")
        print("  Performance statistics:")
        print(f"    statewide runtime files: {runtime_sizes}")
        print(f"    statewide runtime total: {statewide_size} bytes")
        print(f"    compact summary: {summary_size} bytes")
        print(f"    detail index: {index_size} bytes")
        print(f"    facility files: {len(facility_paths)} files, {sum(facility_sizes)} bytes")
        print(f"    detail directory total: {directory_size} bytes")
        print(f"    facility size min/median/average/max: {min(facility_sizes)} / {median_size} / {statistics.mean(facility_sizes):.2f} / {max(facility_sizes)} bytes")
        print(f"    median selected-facility transfer reduction: {self.metrics['performance']['median_transfer_reduction_percent']:.3f}%")
        if self.verbose:
            print("    largest facility files by record count:")
            for item in largest_by_records:
                print(f"      {item['ccn']} {item['provider_name']}: {item['records']} records, {item['bytes']} bytes")

    def run(self) -> int:
        sections = (
            ("JSON parsing and required structure", self.audit_json_structure),
            ("Current facility coverage", self.audit_current_coverage),
            ("Health runtime", self.audit_health),
            ("Fire Safety / Emergency Preparedness runtime", self.audit_fire),
            ("Penalties runtime", self.audit_penalties),
            ("Compact summary consistency", self.audit_summary),
            ("Per-facility detail reconciliation", self.audit_facility_details),
            ("Cross-layer per-facility reconciliation", self.audit_cross_layer),
            ("Manifest and registry consistency", self.audit_manifest_registry),
            ("Public methodology consistency", self.audit_methodology),
            ("Facility Explorer loading architecture", self.audit_loading_architecture),
            ("Performance information", self.audit_performance),
        )
        for name, callback in sections:
            self.section(name, callback)
        passed = len(self.failures) == 0
        print()
        print(f"{'PASS' if passed else 'FAIL'}  Survey/enforcement release audit: {sum(ok for _, ok in self.section_results)}/{len(self.section_results)} sections passed; {len(self.failures)} failure(s).")
        if passed:
            print("Release artifacts are internally consistent and ready for the next release step.")
        else:
            print("Release is not ready. No audited files were modified; resolve the discrepancies above and rerun.")
        return 0 if passed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="Print successful individual checks and largest-facility details.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return ReleaseAudit(verbose=args.verbose).run()


if __name__ == "__main__":
    sys.exit(main())
