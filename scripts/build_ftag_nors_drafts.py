"""Build review-only context links from the locked source term index."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def words(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", text.lower())


def has_term(text, term):
    tokens = words(text)
    target = term.split()
    return any(tokens[i:i + len(target)] == target for i in range(len(tokens) - len(target) + 1))


def excerpt(text, term):
    # Sentences are verbatim substrings of the extracted passage, never paraphrases.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z§(])", text)
    return next((s for s in sentences if has_term(s, term)), text)


def main():
    tag_index = read(DATA / "appendix_pp" / "index.json")["tags"]
    tags = {row["id"]: read(DATA / "appendix_pp" / (row["tag"] + ".json")) for row in tag_index}
    authority = read(DATA / "nors_primary_authority.json")["authority_records"]
    codes = {row["id"]: row for row in authority if row["authority_type"] == "nors_table_2_definition"}
    pairs = defaultdict(set)
    manifest = read(DATA / "term_index.json")
    # Exclude generic cross-references and high-frequency words: they do not establish
    # meaningful context links. This lexical filter is app logic, not source authority.
    generic = {"defined", "definition", "definitions", "including", "section", "requirements", "requirement", "information", "provided", "determine", "determined", "facility", "resident", "residents", "staff", "other", "right", "rights"}
    for shard in manifest["shards"]:
        for term, entries in read(DATA / shard["file"]).items():
            nors = {entry["record_id"] for entry in entries if entry["record_id"] in codes}
            pp = {entry["record_id"] for entry in entries if entry["record_id"] in tags}
            if not nors or not pp or term in generic or term.isdigit():
                continue
            if len(nors) > 12 or len(pp) > 60:
                continue
            for tag_id in pp:
                for code_id in nors:
                    pairs[tag_id, code_id].add(term)

    # Explicit review request: the only indexed overlap for this clinically
    # important example is generic. Preserve it with a clear weak-evidence flag.
    for shard in manifest["shards"]:
        if shard["first"] <= "defined" <= shard["last"]:
            entries = read(DATA / shard["file"]).get("defined", [])
            ids = {entry["record_id"] for entry in entries}
            if {"appendix-pp-f554", "nors-table2-d09"} <= ids:
                pairs["appendix-pp-f554", "nors-table2-d09"].add("defined")
            break

    result = []
    for tag_id, tag in sorted(tags.items()):
        links = []
        for (candidate, code_id), shared in sorted(pairs.items()):
            if candidate != tag_id:
                continue
            code = codes[code_id]
            candidates = []
            for passage in tag["passages"]:
                matched = sorted(t for t in shared if has_term(passage["text"], t) and has_term(code["text"], t))
                if not matched:
                    continue
                is_example = passage.get("is_example", False)
                candidates.append((is_example, sum(" " in x for x in matched), len(matched), passage, matched))
            if not candidates:
                continue
            _, _, _, passage, matched = max(candidates, key=lambda x: (x[0], x[1], x[2], x[3]["id"]))
            strongest = max(matched, key=lambda x: (" " in x, len(x), x))
            links.append({
                "nors_code": code["code"], "status": "draft", "controls_coding": False,
                "context_label": "Context for the facts; does not determine the NORS code",
                "mapping_basis": "both" if passage.get("is_example", False) else "nors_definition",
                "evidence_strength": "weak_generic_term" if shared == {"defined"} else "shared_source_terms",
                "shared_terms": matched,
                "appendix_pp": {"passage_id": passage["id"], "excerpt": excerpt(passage["text"], strongest), "locator": f"PDF page {passage['pdf_page']}; {passage['section_label']}", "is_example": passage.get("is_example", False)},
                "nors_table_2": {"authority_id": code_id, "excerpt": excerpt(code["text"], strongest), "locator": code["locator"]},
            })
        result.append({"f_tag": tag["tag"], "cfr_section": tag["cfr_section"], "status": "draft", "controls_coding": False, "pairings": links, "unmapped_reason": "" if links else "No eligible shared terms were found in the locked term index; review needed."})
    payload = {"version": "1.0", "status": "draft", "controls_coding": False, "method": "Exact shared terms from the source term index; generic and very common terms excluded. Example passages are preferred. Links are context only and require human review.", "tags": result}
    (DATA / "ftag_nors_crosswalk.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["# Draft context links: Appendix PP §§483.10 and 483.12", "", "**Draft for human review. Context for the facts; does not determine the NORS code.** Shared words are a starting point, and do not establish that a code applies.", "", "| F-tag | NORS | Shared terms | Appendix PP excerpt and locator | NORS Table 2 excerpt and locator |", "|---|---|---|---|---|"]
    for tag in result:
        if not re.match(r"^§?483\.(?:10|12)(?:\(|$)", tag["cfr_section"]):
            continue
        for link in tag["pairings"]:
            pp, nors = link["appendix_pp"], link["nors_table_2"]
            lines.append("| " + " | ".join(map(cell, [tag["f_tag"], link["nors_code"], ", ".join(link["shared_terms"]), f"{pp['excerpt']} ({pp['locator']})", f"{nors['excerpt']} ({nors['locator']})"])) + " |")
    f554 = next(row for row in result if row["f_tag"] == "F554")
    found = {row["nors_code"] for row in f554["pairings"]}
    wanted = {"D09", "D01", "F03", "F04", "J01"}
    lines.extend(["", "## Medication self-administration check", "", f"F554 draft links among D09, D01, F03, F04 and J01: {', '.join(sorted(found & wanted)) or 'none'}. The remaining codes require human review: {', '.join(sorted(wanted - found)) or 'none'}. A missing lexical link does not rule out a contextual relationship. D09 and F554 share only the generic indexed word 'defined'; their draft link is explicitly marked weak and needs human review. Both source texts also mention the right, a word excluded from the term index."])
    (ROOT / "docs" / "nors_ftag_crosswalk_review_batch_1.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Tags: {len(result)}; paired: {sum(bool(r['pairings']) for r in result)}; unmapped: {sum(not r['pairings'] for r in result)}; pairings: {sum(len(r['pairings']) for r in result)}")
    print(f"F554 requested review codes: {sorted(found & wanted)}; pending: {sorted(wanted - found)}")


if __name__ == "__main__":
    main()
