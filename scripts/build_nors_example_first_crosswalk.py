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
    "nors_code", "table_2_definition", "table_2_locator", "table_2_use_text", "shared_terms",
    "match_score", "match_basis", "status", "controls_coding",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def section_number(citation: str) -> int | None:
    match = re.search(r"483\.(\d+)", citation or "")
    return int(match.group(1)) if match else None


def use_text(definition: str) -> str:
    """Return exact Table 2 sentence(s) that give a Use instruction."""
    sentences = re.split(r"(?<=[.!?])\s+", definition)
    return " ".join(sentence for sentence in sentences if re.search(r"\bUse\b", sentence))


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

            # Trace each example passage backward to Table 2. Keep the strongest
            # evidence passage for each code, then at most five codes per tag.
            best_by_code = {}
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
                    prior = best_by_code.get(code)
                    if prior is None or candidate[:3] > prior[:3]:
                        best_by_code[code] = candidate

            selected = sorted(best_by_code.items(), key=lambda pair: (-pair[1][0], pair[0]))[:5]
            for code, (score, _, _, passage, shared, phrase) in selected:
                locators = passage.get("evidence_locator") or (
                    f"{tag['source_file']}; PDF page {passage['pdf_page']}; "
                    f"{passage['section_label']}; {passage['id']}"
                )
                rows.append({
                    "batch": batch,
                    "tag": tag["tag"],
                    "cms_title": tag.get("cms_short_title", ""),
                    "appendix_example_text": passage["text"],
                    "appendix_example_locator": locators,
                    "nors_code": code,
                    "table_2_definition": definitions[code]["text"],
                    "table_2_locator": definitions[code]["locator"],
                    "table_2_use_text": use_text(definitions[code]["text"]),
                    "shared_terms": ", ".join(sorted(shared)),
                    "match_score": f"{score:.3f}",
                    "match_basis": "shared phrase and terms" if phrase else "shared terms",
                    "status": "draft",
                    "controls_coding": "false",
                })

        summary[batch] = {
            "tags": len(batch_tags),
            "tags_with_examples": tags_with_examples,
            "example_passages": example_count,
            "candidate_pairs": len(rows) - batch_start,
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
