from __future__ import annotations

import hashlib
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = ROOT / "source_data"
PACK = json.loads((DATA / "nors_source_pack_lock.json").read_text(encoding="utf-8-sig"))
LOCK = {row["name"]: row for row in PACK["revision4_source_inventory"]["files"]}
TODAY = "2026-11-12"
TABLE2 = "NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf"
APPENDIX = "som107ap_pp_guidelines_ltcf_0.pdf"
CODE_MATCH = re.compile(r"(?<![A-Z0-9])([A-L])\s*0?\s*(\d{2})(?!\d)", re.I)
F_HEADER = re.compile(r"(?m)^\s*(F\d{3,4})\s*\n\s*\(Rev\.")
STOP_WORDS = set("a an and are as at be been being by for from had has have he her hers him his i if in into is it its may me my of on or our ours she that the their them then there these they this those to was we were what when where which who will with you your about any all such not use used shall must may resident residents facility staff care complaint code include includes including example examples also other right rights problem issue concern where after before because from each does do may should can will".split())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def is_example_passage(text: str) -> bool:
    return bool(re.search(r"\b(?:for example|examples include|such as|may include)\b|(?<!\w)e\.g\.", text, re.I))


def jwrite(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def source_meta(filename: str) -> dict:
    locked = LOCK[filename]
    return {
        "source_file": locked["source_file"],
        "source_sha256": locked["sha256"],
        "source_revision": locked["source_revision"],
        "retrieved": locked["retrieved"],
    }


def source_url(filename: str) -> str:
    source_path = f"source_data/{filename}"
    def walk(value):
        if isinstance(value, dict):
            if str(value.get("source_file", "")).replace("\\", "/").endswith("/" + filename):
                yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)
    for row in walk(PACK):
        if row.get("url"):
            return row["url"]
    urls = {
        TABLE2: "https://ltcombudsman.org/wp-content/uploads/2026/04/NORS_Table_2_Complaint_Code_2024_Renewal-noex.pdf",
        APPENDIX: "https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/som107ap_pp_guidelines_ltcf.pdf",
        "Chapter 368v - Health Care Institutions.html": "https://www.cga.ct.gov/current/pub/chap_368v.htm",
        "Chapter 319l - Department of Aging and Disability Services.html": "https://www.cga.ct.gov/current/pub/chap_319l.htm",
        "42 CFR Part 483 Subpart B (up to date as of 11-10-2026).pdf": "https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-483/subpart-B/section-483.10",
        "19-13-d8v.pdf": "https://eregulations.ct.gov/eRegsPortal/",
    }
    return urls.get(filename, "")


def pdf_pages(filename: str) -> list[str]:
    path = SOURCES / filename
    if not path.is_file():
        raise FileNotFoundError(path)
    locked = LOCK[filename]
    if sha(path) != locked["sha256"]:
        raise ValueError(f"Locked source hash mismatch: {filename}")
    return [page.extract_text() or "" for page in PdfReader(str(path)).pages]


def marker_matches(text: str, codes: list[str]) -> list[tuple[int, str]]:
    matches = []
    # Source typography separates code characters; H01 is rendered as H0I in the supplied PDF.
    for code in codes:
        letter, digits = code[0], code[1:]
        digit_pattern = r"\s*".join(map(re.escape, digits))
        pattern = re.compile(rf"(?<![A-Z0-9]){letter}\s*{digit_pattern}(?!\d)", re.I)
        for match in pattern.finditer(text):
            matches.append((match.start(), code))
    for match in re.finditer(r"(?<![A-Z0-9])H\s*0\s*I(?![A-Z0-9])", text, re.I):
        matches.append((match.start(), "H01"))
    return sorted(set(matches))


def extract_table2() -> tuple[list[dict], dict[str, str], dict[str, int]]:
    catalog = json.loads((ROOT / "crosswalk_catalog.json").read_text(encoding="utf-8-sig"))["records"]
    pages = pdf_pages(TABLE2)
    all_codes = [row["nors_minor_code"] for row in catalog]
    catalog_by_code = {row["nors_minor_code"]: row for row in catalog}
    starts: dict[str, tuple[int, int]] = {}
    for page_no, text in enumerate(pages, 1):
        for start, code in marker_matches(text, all_codes):
            if code in starts:
                continue
            label_words = re.findall(r"[a-z0-9]+", catalog_by_code[code]["nors_minor_label"].lower())
            # Table rows place the label before the code. Cross-references place the
            # code before its parenthetical label (e.g. "Use D03 (Dignity and respect)").
            before = text[max(0, start - 150):start]
            before_norm = re.findall(r"[a-z0-9]+", before.lower())
            if label_words:
                required = {w for w in label_words if w not in {"a", "an", "and", "or", "the", "to"}}
                if not required or len(required & set(before_norm)) / len(required) < 0.72:
                    continue
            tail = text[start:min(len(text), start + 12)]
            if re.match(r"\s*\(", tail) and re.search(r"\b(?:Use|See)\s*$", before, re.I):
                continue
            starts[code] = (page_no, start)
    if set(starts) != set(all_codes):
        raise ValueError(f"Table 2 actual row anchors missing: {sorted(set(all_codes) - set(starts))}")
    ordered = sorted((page, offset, code) for code, (page, offset) in starts.items())
    chunks: dict[str, tuple[str, int]] = {}
    for i, (page, offset, code) in enumerate(ordered):
        raw = pages[page - 1]
        end_offset = ordered[i + 1][1] if i + 1 < len(ordered) and ordered[i + 1][0] == page else len(raw)
        # A printed code row is confined to its table page in this supplied Table 2.
        # Stop before the next row's label, which precedes its code marker in the PDF.
        if i + 1 < len(ordered) and ordered[i + 1][0] == page:
            next_code = ordered[i + 1][2]
            next_label = next(row["nors_minor_label"] for row in catalog if row["nors_minor_code"] == next_code)
            significant = {w for w in re.findall(r"[a-z0-9]+", next_label.lower()) if w not in {"a", "an", "and", "or", "the", "to"}}
            line_starts = [m.end() for m in re.finditer(r"\n", raw[max(0, end_offset - 200):end_offset])]
            candidate_starts = [max(0, end_offset - 200)] + [max(0, end_offset - 200) + value for value in line_starts]
            for candidate in reversed(candidate_starts):
                window = raw[candidate:end_offset]
                words = set(re.findall(r"[a-z0-9]+", window.lower()))
                if significant and len(significant & words) / len(significant) >= 0.72:
                    end_offset = candidate
                    break
        snippet = norm(raw[offset:end_offset])
        chunks[code] = (snippet, page)
    records = []
    texts = {}
    locators = {}
    meta = source_meta(TABLE2)
    for row in catalog:
        code = row["nors_minor_code"]
        if code not in chunks:
            raise ValueError(f"Table 2 row marker not found for {code}")
        text, page = chunks[code]
        rid = f"nors-table2-{code.lower()}"
        records.append({
            "id": rid,
            "authority_type": "nors_table_2_definition",
            "citation": f"NORS Table 2, {code} — {row['nors_minor_label']}",
            "locator": f"PDF page {page}; Table 2 row {code}",
            "text": text,
            **meta,
            "url": source_url(TABLE2),
            "code": code,
            "topic_slug": row["topic_slug"],
        })
        texts[code], locators[code] = text, f"NORS Table 2 PDF p. {page}, {code}"
    return records, texts, locators


def extract_nors_explanatory() -> list[dict]:
    wanted = [
        name for name in LOCK
        if name.startswith("nors-training-part-") and "basic-principles" in name
    ]
    wanted += [name for name in LOCK if name == "nors-faqs.pdf"]
    wanted += [name for name in LOCK if "quiz-answers" in name or "quiz-answers-" in name]
    records = []
    known_codes = re.compile(r"\b(?:[A-L]\s?\d{2}|[A-L]\d{2})\b", re.I)
    overlap = re.compile(r"\b(?:use|rather than|instead|different|overlap|distinguish|code|coded|complaint|table\s*2|coding|category|categories|best fits|case is comprised)\b", re.I)
    application_rule = re.compile(r"\b(?:code|codes|coding|table\s*2|best fits|complaint types|complaint code\(s\)|one code|multiple code|category)\b", re.I)
    for filename in sorted(set(wanted)):
        if filename not in LOCK or not (SOURCES / filename).is_file():
            continue
        pages = pdf_pages(filename)
        for page_no, raw in enumerate(pages, 1):
            for para in re.split(r"\n\s*\n", raw):
                text = norm(para)
                # Keep source passages that directly explain minor-code use/overlap, plus
                # training principles that explain how Table 2 codes fit in a case.
                relevant_code_reference = bool(known_codes.search(text) and overlap.search(text))
                relevant_principle = bool(filename.endswith("basic-principles.pdf") and application_rule.search(text))
                if len(text) < 60 or not (relevant_code_reference or relevant_principle):
                    continue
                codes = sorted({re.sub(r"\s+", "", x.upper()) for x in known_codes.findall(text)})
                # Keep the extracted source as the text, never the paragraph-selection rule.
                suffix = hashlib.sha256(f"{filename}|{page_no}|{text}".encode()).hexdigest()[:12]
                records.append({
                    "id": f"nors-guidance-{suffix}",
                    "authority_type": "nors_training_or_faq",
                    "citation": filename,
                    "locator": f"PDF page {page_no}",
                    "text": text,
                    **source_meta(filename),
                    "url": source_url(filename),
                    "codes_mentioned": codes,
                })
    return records


def extract_norc_handout() -> list[dict]:
    filename = "nors-codes-and-definitions.pdf"
    if filename not in LOCK or not (SOURCES / filename).is_file():
        return []
    catalog = json.loads((ROOT / "crosswalk_catalog.json").read_text(encoding="utf-8-sig"))["records"]
    codes = [r["nors_minor_code"] for r in catalog]
    pages = pdf_pages(filename)
    row_marker = re.compile(r"(?<![A-Z0-9])([A-L]\d{2})\s*[-–]\s*", re.I)
    starts = []
    for pno, raw in enumerate(pages, 1):
        for m in row_marker.finditer(raw):
            code = m.group(1).upper()
            if code in codes:
                catalog_row = next(r for r in catalog if r["nors_minor_code"] == code)
                label_tokens = {w for w in re.findall(r"[a-z0-9]+", catalog_row["nors_minor_label"].lower()) if w not in {"a", "an", "and", "or", "the", "to"}}
                following = set(re.findall(r"[a-z0-9]+", raw[m.end():m.end() + 140].lower()))
                covered = {w for w in label_tokens if any(candidate.startswith(w) or w.startswith(candidate) for candidate in following)}
                if label_tokens and len(covered) / len(label_tokens) < 0.6:
                    continue  # Excludes A01-A05 style cross-reference ranges.
                starts.append((pno, m.start(), code))
    actual = {code for _, _, code in starts}
    if actual != set(codes):
        raise ValueError(f"NORC handout code rows missing: {sorted(set(codes) - actual)}")
    starts.sort()
    row_starts = {}
    for pno, offset, code in starts:
        row_starts.setdefault(code, (pno, offset))
    starts = sorted((pno, offset, code) for code, (pno, offset) in row_starts.items())
    result = []
    meta = source_meta(filename)
    for i, (page, offset, code) in enumerate(starts):
        end_page, end_offset = starts[i + 1][:2] if i + 1 < len(starts) else (len(pages), len(pages[-1]))
        if end_page > page:
            # Each code entry ends on its printed page; the following page begins a new heading/table row.
            end_page, end_offset = page, len(pages[page - 1])
        pieces = []
        for pno in range(page, end_page + 1):
            lo = offset if pno == page else 0
            hi = end_offset if pno == end_page else len(pages[pno - 1])
            pieces.append(pages[pno - 1][lo:hi])
        text = norm(" ".join(pieces))
        # Strip page furniture if a row crosses a page boundary; the actual quoted text remains exact.
        text = re.sub(r"\b\d+\s*\|\s*Revised\s+July\s+2025\s*", "", text, flags=re.I).strip()
        result.append({"id": f"norc-code-handout-{code.lower()}", "authority_type": "norc_nors_handout", "citation": f"NORC NORS Complaint Codes and Definitions, {code}", "locator": f"PDF page {page}; {code}", "text": text, **meta, "url": source_url(filename), "code": code, "source_priority": "companion; Table 2 controls if wording differs"})
    return result


def build_ambiguity(table_records: list[dict]) -> list[dict]:
    target = {r["nors_minor_code"] for r in json.loads((ROOT / "crosswalk_catalog.json").read_text(encoding="utf-8-sig"))["records"]}
    target = {c for c in target if c.startswith("D") or c in {"F03", "F04", "J01", "F02", "F05", "F07", "F08", "F12", "A05", "C03", "J03"}}
    by_code = {r["code"]: r for r in table_records}
    xrefs = defaultdict(list)
    code_ref = r"[A-L]\s*0?\s*\d{1,2}"
    for source_code, rec in by_code.items():
        for match in re.finditer(rf"\b(?:Use|See)\s+({code_ref}(?:\s*(?:,|or|and|-)\s*{code_ref})*)", rec["text"], re.I):
            phrase = match.group(0)
            refs = []
            for raw_code in re.findall(code_ref, phrase, re.I):
                code_match = re.match(r"([A-L])\s*0?\s*(\d{1,2})", raw_code, re.I)
                if code_match:
                    refs.append(f"{code_match.group(1).upper()}{int(code_match.group(2)):02d}")
            for other in refs:
                if other != source_code and other in by_code:
                    xrefs[other].append({"code": source_code, "source_quote": phrase, "locator": rec["locator"]})
                    xrefs[source_code].append({"code": other, "source_quote": phrase, "locator": rec["locator"]})
    result = []
    for code in sorted(target):
        rec = by_code[code]
        neighbors = sorted(xrefs.get(code, []), key=lambda v: (v["code"], v["source_quote"]))
        # Ambiguity passages use Table 2 text that directly names an alternate code.
        ambiguity = []
        for n in neighbors:
            ambiguity.append({
                "situation": n["source_quote"],
                "source_quote": n["source_quote"],
                "locator": n["locator"],
                "review_prompt": "Check the facts and compare the cited NORS definitions; this tool does not choose a code.",
            })
        if not ambiguity:
            ambiguity.append({
                "situation": rec["text"],
                "source_quote": rec["text"],
                "locator": rec["locator"],
                "review_prompt": "Check the facts against this NORS definition and any applicable neighboring codes; this tool does not choose a code.",
            })
        result.append({"code": code, "neighbors": neighbors, "ambiguity": ambiguity})
    return result


def extract_appendix() -> tuple[list[dict], dict[str, list[str]]]:
    citation_name = "NH_CitationDescriptions_May2026.csv"
    citation_path = SOURCES / "cms_survey" / citation_name
    if sha(citation_path) != LOCK[citation_name]["sha256"]:
        raise ValueError("Locked CMS citation descriptions hash mismatch")
    with citation_path.open(encoding="utf-8-sig", newline="") as stream:
        titles = {}
        for item in csv.DictReader(stream):
            match = re.fullmatch(r"F-0*(\d+)", item["Deficiency Prefix and Number"].strip())
            if match:
                tag = f"F{int(match.group(1))}"
                title = item["Deficiency Description"].strip()
                if tag in titles and titles[tag] != title:
                    raise ValueError(f"Conflicting CMS citation descriptions: {tag}")
                titles[tag] = title
    tag_doc = json.loads((DATA / "appendix_pp_tag_pages.json").read_text(encoding="utf-8-sig"))
    all_rows = {r["f_tag"].upper(): r for r in tag_doc["appendix_pp_tag_page_rows"]}
    authority_titles = {}
    auth_index_path = ROOT / "authority_index.json"
    if auth_index_path.is_file():
        auth_index = json.loads(auth_index_path.read_text(encoding="utf-8-sig"))
        authority_titles = {str(r.get("citation", "")).upper(): r.get("title", "") for r in auth_index.get("authorities", [])}
    resident_titles = {}
    resident_map_path = DATA / "reference" / "resident_rights_tag_map.json"
    if resident_map_path.is_file():
        resident_map = json.loads(resident_map_path.read_text(encoding="utf-8-sig"))
        resident_titles = {str(r.get("tag", "")).upper(): r.get("title", "") for r in resident_map.get("tag_entries", [])}
    pages = pdf_pages(APPENDIX)
    headers = []
    for pno, text in enumerate(pages, 1):
        for m in F_HEADER.finditer(text):
            tag = m.group(1).upper()
            headers.append((tag, pno, m.start()))
    # Ignore repeated headers and preserve document order.
    starts = {}
    for tag, pno, offset in headers:
        starts.setdefault(tag, (pno, offset))
    # F553 and other crosswalk-page entries can be shared subsections without a standalone
    # Appendix PP F-tag header. Keep those mapped shared sections, plus every actual PDF header.
    tag_map = dict(starts)
    for tag, row in all_rows.items():
        if tag in starts or row.get("status") != "confirmed":
            continue
        pno = row.get("appendix_pp_pdf_page_start")
        if isinstance(pno, int) and 1 <= pno <= len(pages):
            tag_map[tag] = (pno, 0)
    indexed = sorted(((tag, p, o) for tag, (p, o) in tag_map.items()), key=lambda x: (x[1], x[2]))
    records = []
    text_sources = {}
    meta = source_meta(APPENDIX)
    # Prior mapped rows identify known reserved/deleted entries. The source text itself is
    # also checked below so unlisted reserved/deleted headers never become active extracts.
    ignored_status = {tag for tag, row in all_rows.items() if row.get("status") in {"reserved", "deleted"}}
    outdir = DATA / "appendix_pp"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("F*.json"):
        old.unlink()
    for i, (tag, start_page, start_offset) in enumerate(indexed):
        if tag in ignored_status:
            continue
        next_item = indexed[i + 1] if i + 1 < len(indexed) else (None, len(pages), len(pages[-1]))
        end_page, end_offset = next_item[1], next_item[2]
        extracted = []
        # Retain exact page text fragments and label them using source headings only.
        for pno in range(start_page, end_page + 1):
            raw = pages[pno - 1]
            lo = start_offset if pno == start_page else 0
            hi = end_offset if pno == end_page else len(raw)
            fragment = raw[lo:hi]
            for para in re.split(r"\n\s*\n", fragment):
                text = norm(para)
                # PDF section headings are often standalone fragments shorter than
                # ordinary passages; keep them so the following text inherits them.
                if len(text) >= 20 or re.match(r"^(INTENT|DEFINITIONS|GUIDANCE|EXAMPLES? OF NONCOMPLIANCE|PROCEDURES|INVESTIGATIVE PROTOCOL|PROBES|KEY ELEMENTS OF NONCOMPLIANCE|DEFICIENCY CATEGORIZATION)\b", text, re.I):
                    extracted.append((pno, text))
        # Shared sections without a standalone tag header are intentionally flagged.
        row = all_rows.get(tag, {})
        is_shared = tag not in starts
        passages = []
        section = "Appendix PP text"
        reached_guidance = False
        for pno, text in extracted:
            upper = text.upper().strip()
            if re.match(r"^INTENT\b", upper):
                section = "Intent"
                reached_guidance = True
            elif re.match(r"^DEFINITIONS\b", upper):
                section = "Definitions"
                reached_guidance = True
            elif re.match(r"^GUIDANCE\b", upper):
                section = "Guidance"
                reached_guidance = True
            elif re.match(r"^EXAMPLES? OF NONCOMPLIANCE\b", upper):
                section = "Examples"
                reached_guidance = True
            elif re.match(r"^(PROCEDURES|INVESTIGATIVE PROTOCOL|PROBES)\b", upper):
                section = "Probes / investigative protocol"
                reached_guidance = True
            elif re.match(r"^KEY ELEMENTS OF NONCOMPLIANCE\b", upper):
                section = "Key elements of noncompliance"
                reached_guidance = True
            elif re.match(r"^DEFICIENCY CATEGORIZATION\b", upper):
                section = "Deficiency categorization"
                reached_guidance = True
            elif not reached_guidance and re.match(r"^(REGULATION|§\s*483\.)", text, re.I):
                section = "Regulation"
            crossrefs = sorted(set(x.upper() for x in re.findall(r"\bF\s*\d{3,4}\b", text, re.I) if re.sub(r"\s+", "", x).upper() != tag))
            passage = {"pdf_page": pno, "section_label": section, "text": text}
            if crossrefs:
                passage["cross_references"] = crossrefs
            # Preserve long rule text as page-sized passages when the joined text
            # occurs verbatim in the source page; never bridge omitted material.
            if passages and passages[-1]["section_label"] == section and passages[-1]["pdf_page"] == pno and (section == "Regulation" or passages[-1]["text"].rstrip().endswith(":")):
                previous = passages[-1]
                merged = previous["text"] + " " + text
                if merged in norm(pages[pno - 1]):
                    previous["text"] = merged
                    refs = sorted(set(previous.get("cross_references", [])) | set(crossrefs))
                    if refs:
                        previous["cross_references"] = refs
                    continue
            passages.append(passage)
        # Determine this after merging so the flag always describes the final text.
        for position, passage in enumerate(passages):
            passage["is_example"] = is_example_passage(passage["text"])
            if position:
                previous = passages[position - 1]
                if (previous["text"].rstrip().endswith(":")
                        and previous["section_label"] == passage["section_label"]
                        and previous["pdf_page"] + 1 == passage["pdf_page"]):
                    previous["continuation_passage_id"] = f"appendix-pp-{tag.lower()}-p{position + 1}"
                    passage["continued_from_passage_id"] = f"appendix-pp-{tag.lower()}-p{position}"
                    if previous["is_example"]:
                        passage["is_example"] = True
                        passage["example_context_inherited"] = True
        if not passages:
            continue
        joined = " ".join(p["text"] for p in passages)
        if re.search(r"(?:This tag number is in reserve for future use|tag number is reserved|this tag is deleted)", joined, re.I):
            continue
        rid = f"appendix-pp-{tag.lower()}"
        passage_pages = sorted({p["pdf_page"] for p in passages})
        low_pages = [pno for pno in passage_pages if len(re.sub(r"\s+", "", pages[pno - 1])) < 40]
        quality = "review_shared_section" if is_shared else ("review_low_text" if low_pages else "text_extracted")
        row = all_rows.get(tag, {})
        first_cfr = next((p["text"] for p in passages if re.search(r"§?\s*483\.\d+", p["text"])), "")
        cfr_match = re.search(r"§?\s*483\.\d+(?:\([a-z0-9]+\))*", first_cfr, re.I)
        cfr = ("§" + cfr_match.group(0).replace("§", "").strip()) if cfr_match else ""
        title = titles.get(tag, "")
        title_status = "cms_citation_description" if title else "missing_cms_citation_description"
        record = {
            "id": rid,
            "tag": tag,
            "cms_short_title": title,
            "cms_short_title_status": title_status,
            "cfr_section": cfr,
            "pdf_page_start": start_page,
            "pdf_page_end": max(p["pdf_page"] for p in passages),
            "source_shared_section": is_shared,
            "extraction_quality": quality,
            "low_text_pages": low_pages,
            "passages": passages,
            **meta,
            "url": source_url(APPENDIX),
        }
        records.append(record)
        text_sources[rid] = [p["text"] for p in passages]
        jwrite(DATA / "appendix_pp" / f"{tag}.json", record)
    index = [{k: r[k] for k in ("tag", "cms_short_title", "cms_short_title_status", "cfr_section", "pdf_page_start", "pdf_page_end", "id", "extraction_quality")} for r in records]
    jwrite(DATA / "appendix_pp" / "index.json", {"version": "1.0", "source_revision": LOCK[APPENDIX]["source_revision"], "source_file": meta["source_file"], "source_sha256": meta["source_sha256"], "tags": index})
    return records, text_sources


def extract_statute_authorities() -> list[dict]:
    # The source is parsed from supplied Chapter 368v HTML, preserving wording and paragraph boundaries.
    from html.parser import HTMLParser

    class TextParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.capture = False
            self.target = None
            self.buf = []
            self.items = defaultdict(list)

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            ident = attrs.get("id", "")
            if ident.startswith("sec_19a-"):
                self.target = ident.removeprefix("sec_")
                self.capture = True
            if self.capture and tag in {"p", "h3", "h4"}:
                self.flush()

        def handle_endtag(self, tag):
            if self.capture and tag in {"p", "h3", "h4"}:
                self.flush()

        def handle_data(self, data):
            if self.capture and data.strip():
                self.buf.append(data.strip())

        def flush(self):
            text = norm(" ".join(self.buf))
            if self.target and text:
                self.items[self.target].append(text)
            self.buf.clear()

    filename = "Chapter 368v - Health Care Institutions.html"
    path = SOURCES / filename
    if not path.exists() or filename not in LOCK:
        return []
    parser = TextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    meta = source_meta(filename)
    out = []
    for section in ("19a-532", "19a-550"):
        for i, text in enumerate(parser.items.get(section, []), 1):
            if section == "19a-550" and not re.search(r"care|resident|participat|individual|choice|plan", text, re.I):
                continue
            out.append({"id": f"ct-statute-{section}-{i}", "authority_type": "connecticut_statute", "citation": f"Conn. Gen. Stat. § {section}", "locator": f"Chapter 368v HTML § {section}, extracted paragraph {i}", "text": text, **meta, "url": source_url(filename)})
    # The self-administration pilot's two state/federal provisions are exact excerpts
    # from the locked source PDFs, not app-authored legal language.
    provisions = [
        ("42 CFR Part 483 Subpart B (up to date as of 11-10-2026).pdf", 8,
         r"\(7\)\s+The right to self-administer medications", r"\(8\)\s+Nothing in this paragraph",
         "42cfr-483-10-c-7", "42 CFR §483.10(c)(7)", "PDF page 8, §483.10(c)(7)", "federal_regulation"),
        ("19-13-d8v.pdf", 5,
         r"\(B\)\s*Patients shall be permitted to self-administer medications", r"\(C\s*\)\s*Medication errors",
         "ct-rcsa-19-13-d8v-b-5-b", "Regs. Conn. State Agencies §19-13-D8v(b)(5)(B)", "PDF page 5, §19-13-D8v(b)(5)(B)", "connecticut_regulation"),
    ]
    for filename, pageno, start_pattern, end_pattern, rid, citation, locator, authority_type in provisions:
        if filename not in LOCK or not (SOURCES / filename).is_file():
            continue
        page = pdf_pages(filename)[pageno - 1]
        start = re.search(start_pattern, page, re.I)
        end = re.search(end_pattern, page[start.end():], re.I) if start else None
        if not start or not end:
            raise ValueError(f"Could not locate exact provision {citation} in {filename} page {pageno}")
        text = norm(page[start.start():start.end() + end.start()])
        out.append({"id": rid, "authority_type": authority_type, "citation": citation, "locator": locator, "text": text, **source_meta(filename), "url": source_url(filename), "controls_coding": False})
    return out


def build_nors_mapping(table_records: list[dict]) -> None:
    catalog = json.loads((ROOT / "crosswalk_catalog.json").read_text(encoding="utf-8-sig"))["records"]
    mapping = {r["nors_minor_code"]: [r["topic_slug"]] for r in catalog}
    jwrite(ROOT / "nors_to_topic.json", mapping)


def build_term_index(authorities: list[dict], pp_records: list[dict]) -> int:
    hits = defaultdict(lambda: defaultdict(set))

    def add(term: str, source_class: str, record_id: str, locator: str) -> None:
        hits[term][(source_class, record_id)].add(locator)
    for record in authorities:
        if record["authority_type"] not in {"nors_table_2_definition", "nors_training_or_faq", "norc_nors_handout"}:
            continue
        text = record["text"]
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", text.lower())
        terms = set(t for t in tokens if t not in STOP_WORDS)
        # Phrases are contiguous in the source; a stop word prevents phrase collapse.
        terms.update(" ".join(tokens[i:i + 2]) for i in range(max(0, len(tokens) - 1)) if all(t not in STOP_WORDS for t in tokens[i:i + 2]))
        for term in terms:
            add(term, "nors", record["id"], record["locator"])
    for record in pp_records:
        for passage in record["passages"]:
            tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", passage["text"].lower())
            terms = set(t for t in tokens if t not in STOP_WORDS)
            terms.update(" ".join(tokens[i:i + 2]) for i in range(max(0, len(tokens) - 1)) if all(t not in STOP_WORDS for t in tokens[i:i + 2]))
            locator = f"PDF p. {passage['pdf_page']}; {passage['section_label']}"
            for term in terms:
                add(term, "appendix_pp", record["id"], locator)
    packed = {}
    for term, entries in sorted(hits.items()):
        packed[term] = [
            {"source_class": source_class, "record_id": record_id, "locators": sorted(locators)}
            for (source_class, record_id), locators in sorted(entries.items())
        ]
    # Sorted ranges permit a client to load only the shard containing a term.
    outdir = DATA / "term_index"
    outdir.mkdir(exist_ok=True)
    for old in outdir.glob("part-*.json"):
        old.unlink()
    shards = []
    current = []
    size = 2  # braces
    def flush():
        if not current:
            return
        name = f"part-{len(shards) + 1:04}.json"
        payload = "{" + ",".join(item[1] for item in current) + "}\n"
        (outdir / name).write_text(payload, encoding="utf-8", newline="\n")
        shards.append({"file": f"term_index/{name}", "first": current[0][0], "last": current[-1][0], "bytes": len(payload.encode("utf-8"))})
    for term, entries in packed.items():
        encoded = json.dumps(term, ensure_ascii=False) + ":" + json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
        item_size = len(encoded.encode("utf-8")) + 1
        if item_size + 3 > 500_000:
            raise ValueError(f"Term too large for shard: {term}")
        if current and size + item_size + 1 > 500_000:
            flush()
            current = []
            size = 2
        current.append((term, encoded))
        size += item_size
    flush()
    jwrite(DATA / "term_index.json", {"version": "2.0", "method": "Lowercase source tokens and source-contiguous bigrams; no inferred synonyms.", "results_are_separate": ["nors", "appendix_pp"], "shards": shards})
    return len(hits)


def main() -> None:
    # Validate every selected source still matches the additive Step 0 lock.
    for filename in (TABLE2, APPENDIX):
        if sha(SOURCES / filename) != LOCK[filename]["sha256"]:
            raise SystemExit(f"Locked input hash mismatch: {filename}")
    table_records, _, _ = extract_table2()
    guidance = extract_nors_explanatory()
    handout = extract_norc_handout()
    statute = extract_statute_authorities()
    authorities = table_records + handout + guidance + statute
    jwrite(DATA / "nors_code_ambiguity.json", {"version": "1.0", "source_rule": "All source_quote fields are extracted from NORS Table 2 text; review_prompt is app copy, not authority.", "codes": build_ambiguity(table_records)})
    build_nors_mapping(table_records)
    pp_records, _ = extract_appendix()
    appendix_refs = []
    for tag_record in pp_records:
        for i, passage in enumerate(tag_record["passages"], 1):
            passage["id"] = f"{tag_record['id']}-p{i}"
        jwrite(DATA / "appendix_pp" / f"{tag_record['tag']}.json", tag_record)
        appendix_refs.append({"tag": tag_record["tag"], "file": f"appendix_pp/{tag_record['tag']}.json", "passage_ids": [p["id"] for p in tag_record["passages"]]})
    jwrite(DATA / "nors_primary_authority.json", {"version": "2.0", "authority_records": authorities, "appendix_pp_passage_refs": appendix_refs})
    terms = build_term_index(authorities, pp_records)
    print(f"NORS Table 2 authorities: {len(table_records)}")
    print(f"NORS training/FAQ/answer-sheet passages: {len(guidance)}")
    print(f"NORC companion code handout records: {len(handout)}")
    print(f"CT statute paragraphs: {len(statute)}")
    print(f"Appendix PP active tag extracts: {len(pp_records)}")
    print(f"Term index terms/phrases: {terms}")


if __name__ == "__main__":
    main()
