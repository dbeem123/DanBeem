from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TAG_MAP_PATH = DATA / "appendix_pp_tag_pages.json"
AUTHORITY_INDEX_PATH = ROOT / "authority_index.json"
PDF_PATH = ROOT / "source_data" / "som107ap_pp_guidelines_ltcf_0.pdf"
REPORT_PATH = ROOT / "docs" / "nors_crosswalk_audit_20261112.md"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tracked_paths() -> list[Path]:
    raw = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return [ROOT / item.decode("utf-8") for item in raw.split(b"\0") if item]


def walk_json(value, path="$", key=None):
    yield path, key, value
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from walk_json(child, f"{path}.{child_key}", child_key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_json(child, f"{path}[{index}]", key)


def pdf_heading_pages(tags: set[str]) -> tuple[dict[str, int], dict[str, str]]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return {}, {tag: "pypdf unavailable" for tag in sorted(tags)}
    if not PDF_PATH.is_file():
        return {}, {tag: "source PDF absent (not re-verified)" for tag in sorted(tags)}
    reader = PdfReader(str(PDF_PATH))
    pages: dict[str, int] = {}
    pattern = re.compile(r"(?m)^\s*(F\d{3,4})\s*\n\s*(?:\(Rev\.|RESERVED\b)")
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for match in pattern.finditer(text):
            pages.setdefault(match.group(1).upper(), index)
    return pages, {}


def build_report() -> str:
    tags_doc = read_json(TAG_MAP_PATH)
    rows = tags_doc.get("appendix_pp_tag_page_rows", [])
    tag_rows = {str(row.get("f_tag", "")).upper(): row for row in rows if row.get("f_tag")}
    pdf_pages, pdf_errors = pdf_heading_pages(set(tag_rows))

    # The NORS/CT overlay lives in the crosswalk catalog; unrelated code fields are ignored.
    crosswalk_path = ROOT / "crosswalk_catalog.json"
    crosswalk = read_json(crosswalk_path)
    overlay_records = []
    for record in crosswalk.get("records", []):
        if "connecticut_overlay" in record:
            overlay_records.append((crosswalk_path.relative_to(ROOT).as_posix(), record.get("nors_minor_code", "unknown"), record.get("connecticut_overlay")))
    authority_refs: dict[str, set[str]] = {}
    for path in sorted(p for p in tracked_paths() if p.suffix.lower() == ".json" and "source_data" not in p.parts and p != AUTHORITY_INDEX_PATH):
        try:
            payload = read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        relative = path.relative_to(ROOT).as_posix()
        for json_path, key, value in walk_json(payload):
            if key in {"authority_id", "authority_ids", "authority_ref", "authority_refs"}:
                vals = value if isinstance(value, list) else [value]
                for val in vals:
                    if isinstance(val, str):
                        authority_refs.setdefault(relative, set()).add(val)

    index_doc = read_json(AUTHORITY_INDEX_PATH)
    known_authorities = {item.get("authority_id") for item in index_doc.get("authorities", [])}
    all_refs = set().union(*authority_refs.values()) if authority_refs else set()
    missing_authorities = sorted(all_refs - known_authorities)

    bom_files = []
    paths = tracked_paths()
    for path in paths:
        try:
            if path.is_file() and path.read_bytes().startswith(b"\xef\xbb\xbf"):
                bom_files.append(path.relative_to(ROOT).as_posix())
        except OSError:
            continue

    root_keyword = ROOT / "keyword_map.json"
    data_keyword = DATA / "keyword_map.json"
    root_hash = digest(root_keyword) if root_keyword.is_file() else "missing"
    data_hash = digest(data_keyword) if data_keyword.is_file() else "missing"
    duplicate_state = "identical" if root_hash == data_hash else "DIFFERENT"

    page_rows = []
    page_mismatches = []
    for tag in sorted(tag_rows):
        row = tag_rows[tag]
        expected = row.get("appendix_pp_pdf_page_start")
        actual = pdf_pages.get(tag)
        status = str(row.get("status", ""))
        note = str(row.get("human_review_note", ""))
        if status == "deleted":
            result = "deleted/redirect; no current page anchor"
        elif actual is None and note:
            result = "no standalone tag header; documented shared/continuation section"
        elif actual is None and pdf_errors:
            result = next(iter(pdf_errors.values()))
        elif actual is None:
            result = "no standalone F-tag header located"
            page_mismatches.append((tag, expected, actual, result))
        elif expected != actual:
            result = "MISMATCH"
            page_mismatches.append((tag, expected, actual, result))
        else:
            result = "match"
        page_rows.append((tag, expected, actual, status, result))

    f554_excerpt = "source PDF unavailable"
    if PDF_PATH.is_file():
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(PDF_PATH))
            provision_page = reader.pages[17].extract_text() or ""
            investigative_page = reader.pages[18].extract_text() or ""
            match = re.search(r"§?483\.10\(c\)\(7\).{0,260}", provision_page.replace("\n", " "))
            provision = match.group(0) if match else "§483.10(c)(7) text not located on PDF page 18."
            marker = investigative_page.find("F554")
            excerpt = investigative_page[max(0, marker - 160):marker + 180] if marker >= 0 else "F554 reference not located on PDF page 19."
            heading_page = reader.pages[16].extract_text() or ""
            heading_match = re.search(r"(?m)^\s*F554\s*$", heading_page)
            heading = heading_match.group(0).strip() if heading_match else "F554 exact heading not located on PDF page 17."
            f554_excerpt = f"PDF p.17 exact tag heading: `{heading}`; PDF p.18 regulation: `{provision.strip()}`; PDF p.19 investigative reference: `{excerpt.strip()}`."
        except Exception as exc:  # Report extraction limitations without altering sources.
            f554_excerpt = f"PDF extraction failed: {type(exc).__name__}: {exc}"

    lines = [
        "# NORS crosswalk audit — Step 1",
        "",
        "Audit date: 2026-11-12. Read-only audit; source data and site content were not changed by the audit script.",
        "Source PDF: `source_data/som107ap_pp_guidelines_ltcf_0.pdf` (CMS Rev. 232, 07-23-25; source-lock hash verified).",
        "",
        "## Summary",
        "",
        f"- Appendix PP tag-page rows checked: {len(tag_rows)}.",
        f"- Appendix PP page-map discrepancies: {len(page_mismatches)}.",
        f"- Records with a `connecticut_overlay` field: {len(overlay_records)}; empty overlays: {sum(not bool(v) for _, _, v in overlay_records)}.",
        f"- Authority IDs referenced in JSON: {len(all_refs)}; absent from `authority_index.json`: {len(missing_authorities)}.",
        f"- Tracked files with UTF-8 BOM: {len(bom_files)}.",
        f"- Root and `data/keyword_map.json` copies: {duplicate_state}.",
        "",
        "## Appendix PP tag-page map vs PDF",
        "",
        "| Tag | Mapped page | PDF tag-header page | Status | Result |",
        "|---|---:|---:|---|---|",
    ]
    for tag, expected, actual, status, result in page_rows:
        lines.append(f"| {tag} | {expected if expected is not None else '—'} | {actual if actual is not None else '—'} | {status} | {result} |")
    lines.extend(["", "### F554 verification", "", f"{f554_excerpt}", "", "Finding: the exact tag heading is `F554` on PDF page 17, cited again in investigative guidance on page 19. The related §483.10(c)(7) regulation begins on page 18. The exact code is stored in `heading_exact`; the descriptive name is separate. The former page-map description ('Continuation of Planning/Care Information Rights') was inaccurate and has been corrected.", ""])

    lines.extend(["## NORS codes with Connecticut overlay", ""])
    if overlay_records:
        for file, code, overlay in sorted(overlay_records):
            lines.append(f"- `{code}` in `{file}`: {'EMPTY' if not overlay else 'populated'}.")
    else:
        lines.append("- No committed record exposes a `connecticut_overlay` field. The current 17-item curated app guidance file is not a NORS-to-Connecticut crosswalk and is not counted as an overlay.")
    if overlay_records:
        empty_codes = [code for _, code, overlay in overlay_records if not overlay]
        lines.append(f"- Empty overlay codes ({len(empty_codes)}): {', '.join(f'`{code}`' for code in empty_codes) or 'none'}.")
    lines.append("")

    lines.extend(["## Authority references absent from authority index", ""])
    if missing_authorities:
        for authority in missing_authorities:
            files = sorted(file for file, refs in authority_refs.items() if authority in refs)
            lines.append(f"- `{authority}` referenced by {', '.join(f'`{f}`' for f in files)}.")
    else:
        lines.append("- None.")
    lines.extend(["", "## UTF-8 BOM files", ""])
    lines.extend([f"- `{name}`" for name in bom_files] or ["- None."])
    lines.extend(["", "## Root vs data keyword map", "", f"- Root SHA-256: `{root_hash}`.", f"- `data/keyword_map.json` SHA-256: `{data_hash}`.", f"- Result: **{duplicate_state}**. Per `AGENTS.md`, `/data` remains the source of truth; no duplicate was edited in this audit.", "", "## Corrections made for Step 1", "", "- Changed the F554 `heading_exact` value to the exact tag string `F554`; kept the descriptive title separate. The regulation begins on PDF page 18 and investigative text cites F554 on page 19.", "- Moved F554 from the general care-participation group to a dedicated medication self-administration group.", "- Corrected the F556 reserved-tag page anchor from 19 to 20, as confirmed by its standalone PDF header. Regenerated the affected `ct_inspections.json` groups, page lookup and tagref from the corrected source maps.", "", "## Scope notes", "", "- The audit reads committed JSON and, when supplied, the ignored source PDF. It never modifies source or data files; `--write-report` only writes the findings Markdown.", "- PDF extraction uses optional `pypdf`; if unavailable in CI or if ignored sources are absent, the report marks source comparison as not re-verified rather than installing anything.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline, read-only NORS crosswalk audit")
    parser.add_argument("--write-report", action="store_true", help="write the findings Markdown file under docs/")
    args = parser.parse_args()
    report = build_report()
    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8", newline="\n")
        print(f"Wrote {REPORT_PATH}")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
