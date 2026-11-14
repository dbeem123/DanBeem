"""Build a non-operative, example-first NORS crosswalk review for batches 4–6.

Each candidate starts with an extracted Appendix PP example passage, then traces
shared, rarity-weighted language back to the verbatim NORS Table 2 definition.
The output is a research aid only: every row is draft and controls no coding.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

try:  # Direct script execution under ``py scripts/...``.
    from build_ftag_review_batch_1 import DATA, ROOT, linked_evidence, terms, stemmed_phrase_match
except ModuleNotFoundError:  # Module-based unittest invocation from the repo root.
    from scripts.build_ftag_review_batch_1 import DATA, ROOT, linked_evidence, terms, stemmed_phrase_match


BATCHES = {
    4: (24, 25),
    5: (30, 45),
    6: (70, 90),
}
FIELDS = [
    "batch", "tag", "cms_title", "appendix_example_text", "appendix_example_locator",
    "nors_code", "table_2_definition", "table_2_locator", "table_2_use_text",
    "example_match_count", "support_pass_count", "support_passes", "rank_within_tag",
    "shared_terms", "example_match_score", "match_basis",
    "appendix_context_text", "appendix_context_locator",
    "regulation_support_text", "regulation_support_locator",
    "norc_scenario_support_text", "norc_scenario_support_locator",
    "status", "controls_coding",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def section_number(citation: str) -> int | None:
    match = re.search(r"483\.(\d+)", citation or "")
    return int(match.group(1)) if match else None


def use_text(definition: str) -> str:
    """Return exact Table 2 sentence(s) that give a Use instruction."""
    sentences = re.split(r"(?<=[.!?])\s+", definition)
    return " ".join(sentence for sentence in sentences if re.search(r"\bUse\b", sentence, re.I))


def strongest_text_match(passages, definition_text, weights, *, require_phrase=False):
    """Find strongest independent text corroboration for one pass."""
    matches = []
    target_terms = terms(definition_text)
    for passage in passages:
        shared = terms(passage["text"]) & target_terms
        phrase = stemmed_phrase_match(passage["text"], definition_text)
        if require_phrase and not phrase:
            continue
        if len(shared) < 2:
            continue
        score = sum(weights.get(term, 0) for term in shared)
        if score < 3:
            continue
        matches.append((score, passage["id"], passage, shared, phrase))
    return max(matches, key=lambda item: (item[0], len(item[3]), item[1])) if matches else None


def scenario_match(example_text, code, scenarios, definition_text, weights):
    """Require the same printed answer code plus phrase and 3 rare terms."""
    matches = []
    example_terms = terms(example_text)
    for scenario in scenarios:
        if code not in scenario.get("expected_codes", []):
            continue
        if scenario.get("answer_status") != "printed_official_answer":
            continue
        shared = example_terms & terms(scenario.get("scenario_text", ""))
        phrase = stemmed_phrase_match(example_text, scenario.get("scenario_text", ""))
        if len(shared) < 3 or not phrase:
            continue
        score = sum(weights.get(term, 0) for term in shared & terms(definition_text))
        if score >= 3:
            matches.append((score, scenario.get("id", ""), scenario, shared))
    return max(matches, key=lambda item: (item[0], len(item[3]), item[1])) if matches else None


def candidate_rank_key(candidate):
    """Sort by distinct evidence checks, strongest example match, then repeats."""
    return (-int(candidate["support_pass_count"]), -float(candidate["example_match_score"]),
            -int(candidate["example_match_count"]), candidate["nors_code"])


def build_rows() -> tuple[list[dict], dict]:
    authority = load(DATA / "nors_primary_authority.json")["authority_records"]
    definitions = {
        row["code"]: row for row in authority
        if row.get("authority_type") == "nors_table_2_definition"
    }
    inventory = load(DATA / "nors_source_pack_lock.json")["revision4_source_inventory"]["files"]
    locked = {row["name"]: row for row in inventory}
    for filename in ("NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf", "som107ap_pp_guidelines_ltcf_0.pdf"):
        row = locked[filename]
        source_path = ROOT / row["source_file"]
        if not source_path.is_file() or hashlib.sha256(source_path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Locked source hash mismatch: {row['source_file']}")
    for definition in definitions.values():
        source = locked.get(Path(definition["source_file"]).name)
        if not source or source["sha256"] != definition["source_sha256"]:
            raise ValueError(f"Table 2 authority record is not tied to the source lock: {definition['code']}")
    frequencies = Counter(term for row in definitions.values() for term in terms(row["text"]))
    weights = {
        term: math.log((len(definitions) + 1) / (count + 1)) + 1
        for term, count in frequencies.items()
    }
    scenarios = load(DATA / "nors_coding_scenarios.json")["scenarios"]
    index = load(DATA / "appendix_pp" / "index.json")["tags"]
    rows: list[dict] = []
    summary = {}

    for batch, (low, high) in BATCHES.items():
        section_map = load(DATA / f"nors_section_prior_batch_{batch}_draft.json")
        if section_map.get("approval_status") != "approved_Daniel" or section_map.get("controls_coding") is not False:
            raise ValueError(f"Batch {batch} section map is not the approved non-coding map")
        category_by_section = {
            section: {category["letter"] for category in value["categories"]}
            for section, value in section_map["sections"].items()
        }
        batch_tags = [item for item in index if (number := section_number(item.get("cfr_section"))) is not None
                      and low <= number <= high]
        tags_with_examples = 0
        example_count = 0
        batch_start = len(rows)

        for item in batch_tags:
            tag = load(DATA / "appendix_pp" / f"{item['tag']}.json")
            by_id = {passage["id"]: passage for passage in tag["passages"]}
            examples = [
                linked_evidence(passage, by_id, tag["source_file"])
                for passage in tag["passages"]
                if not passage.get("continued_from_passage_id")
                and passage.get("is_example")
            ]
            if not examples:
                continue
            tags_with_examples += 1
            example_count += len(examples)
            section = f"483.{section_number(item.get('cfr_section'))}"
            allowed_letters = category_by_section.get(section, set())

            # Pass 1 is required: the candidate must start from at least one
            # Appendix PP example passage and match its source language.
            best_by_code = {}
            example_match_counts = Counter()
            for passage in examples:
                passage_terms = terms(passage["text"])
                for code, definition in definitions.items():
                    if code[0] not in allowed_letters:
                        continue
                    shared = passage_terms & terms(definition["text"])
                    if len(shared) < 2:
                        continue
                    score = sum(weights.get(term, 0) for term in shared)
                    if score < 3:
                        continue
                    phrase = stemmed_phrase_match(passage["text"], definition["text"])
                    candidate = (score, len(shared), passage["id"], passage, shared, phrase)
                    example_match_counts[code] += 1
                    prior = best_by_code.get(code)
                    if prior is None or candidate[:3] > prior[:3]:
                        best_by_code[code] = candidate

            scored_candidates = []
            all_passages = [
                linked_evidence(passage, by_id, tag["source_file"])
                for passage in tag["passages"]
                if not passage.get("continued_from_passage_id")
            ]
            context_passages = [
                passage for passage in all_passages
                if passage["section_label"] in ("Key elements of noncompliance", "Deficiency categorization")
                or "severity" in passage["section_label"].lower()
            ]
            regulation_passages = [p for p in all_passages if p["section_label"] == "Regulation"]

            for code, (score, _, _, passage, shared, phrase) in best_by_code.items():
                definition = definitions[code]
                # Pass 2: a separate key-element/severity passage corroborates
                # the same NORS definition with two rare terms and weighted support.
                context = strongest_text_match(context_passages, definition["text"], weights)
                # Pass 3: the tag's regulation sentence contains a specific
                # multiword phrase also present in this NORS definition.
                regulation = strongest_text_match(regulation_passages, definition["text"], weights, require_phrase=True)
                # Pass 4: an official training scenario has this printed answer
                # and shares a specific phrase plus at least three useful terms
                # with the example passage.
                scenario = scenario_match(passage["text"], code, scenarios, definition["text"], weights)
                support_passes = ["appendix_example"]
                if context:
                    support_passes.append("appendix_key_elements_or_severity")
                if regulation:
                    support_passes.append("appendix_regulation_phrase")
                if scenario:
                    support_passes.append("official_norc_training_scenario")
                scored_candidates.append((len(support_passes), score, code, passage, shared, phrase,
                                          context, regulation, scenario, support_passes))

            # Candidates with more distinct passes rank above candidates whose
            # support is only the required example-language match.
            prepared = []
            for pass_count, score, code, passage, shared, phrase, context, regulation, scenario, support_passes in scored_candidates:
                prepared.append({
                    "batch": batch,
                    "tag": tag["tag"],
                    "cms_title": tag.get("cms_short_title", ""),
                    "appendix_example_text": passage["text"],
                    "appendix_example_locator": passage.get("evidence_locator") or (
                        f"{tag['source_file']}; PDF page {passage['pdf_page']}; "
                        f"{passage['section_label']}; {passage['id']}"
                    ),
                    "nors_code": code,
                    "table_2_definition": definitions[code]["text"],
                    "table_2_locator": definitions[code]["locator"],
                    "table_2_use_text": use_text(definitions[code]["text"]),
                    "example_match_count": example_match_counts[code],
                    "support_pass_count": pass_count,
                    "support_passes": "; ".join(support_passes),
                    "shared_terms": ", ".join(sorted(shared)),
                    "example_match_score": f"{score:.3f}",
                    "match_basis": "shared phrase and terms" if phrase else "shared terms",
                    "appendix_context_text": context[2]["text"] if context else "",
                    "appendix_context_locator": context[2].get("evidence_locator", "") if context else "",
                    "regulation_support_text": regulation[2]["text"] if regulation else "",
                    "regulation_support_locator": regulation[2].get("evidence_locator", "") if regulation else "",
                    "norc_scenario_support_text": scenario[2]["scenario_text"] if scenario else "",
                    "norc_scenario_support_locator": (
                        f"{scenario[2].get('source_file', '')}; {scenario[2].get('locator', '')}"
                        if scenario else ""
                    ),
                    "status": "draft",
                    "controls_coding": "false",
                })
            selected = sorted(prepared, key=candidate_rank_key)[:5]
            for rank, row in enumerate(selected, 1):
                row["rank_within_tag"] = rank
                rows.append(row)

        summary[batch] = {
            "tags": len(batch_tags),
            "tags_with_examples": tags_with_examples,
            "example_passages": example_count,
            "candidate_pairs": len(rows) - batch_start,
            "support_pass_counts": dict(sorted(Counter(
                row["support_pass_count"] for row in rows[batch_start:]
            ).items())),
        }

    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/nors_ftag_example_first_batches_4_6.csv")
    args = parser.parse_args()
    rows, summary = build_rows()
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"output": out.relative_to(ROOT).as_posix(), "summary": summary,
                      "total_candidate_pairs": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
