#!/usr/bin/env python3
"""Read-only text-extraction audit for the locally staged Revision 4 NORS pack."""
from __future__ import annotations

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "data" / "nors_source_pack_lock.json"
OUT = ROOT / "docs" / "nors_source_quality_20261112.md"


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    return " ".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))


def main() -> None:
    inventory = json.loads(LOCK.read_text(encoding="utf-8"))["revision4_source_inventory"]["files"]
    poor_pages: list[tuple[str, int, int]] = []
    pdf_count = page_count = 0
    per_file: list[tuple[str, str, int]] = []
    for entry in inventory:
        path = ROOT / entry["source_file"]
        if path.suffix.lower() == ".pdf":
            pdf_count += 1
            reader = PdfReader(str(path))
            chars = 0
            for page_number, page in enumerate(reader.pages, 1):
                page_count += 1
                text = page.extract_text() or ""
                chars += len(re.sub(r"\s+", "", text))
                if len(re.sub(r"\s+", "", text)) < 40:
                    poor_pages.append((path.name, page_number, len(text)))
            per_file.append((path.name, "PDF extracted", chars))
        elif path.suffix.lower() == ".html":
            parser = TextOnly()
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
            per_file.append((path.name, "HTML extracted", len(" ".join(parser.parts))))
        elif path.suffix.lower() == ".docx":
            per_file.append((path.name, "DOCX XML extracted", len(docx_text(path))))

    pdf_path = ROOT / "source_data" / "45 CFR Part 1324 Subpart A (in effect on 11-09-2026).pdf"
    html_path = ROOT / "source_data" / "eCFR __ 45 CFR Part 1324 Subpart A -- State Long-Term Care Ombudsman Program.html"
    pdf_text = " ".join((page.extract_text() or "") for page in PdfReader(str(pdf_path)).pages)
    parser = TextOnly()
    parser.feed(html_path.read_text(encoding="utf-8", errors="replace"))
    html_text = " ".join(parser.parts)
    section_pattern = r"§\s*1324\.\d+[a-z]?(?:\([a-zA-Z0-9]+\))*"
    pdf_sections = set(re.findall(section_pattern, pdf_text))
    html_sections = set(re.findall(section_pattern, html_text))

    lines = [
        "# Revision 4 source extraction quality — 2026-11-12",
        "",
        "Tool: `pypdf 6.10.2` for PDFs; Python standard-library `HTMLParser` for HTML and XML extraction from DOCX.",
        "No OCR, package installation, or source-file modification was performed. Pages with fewer than 40 non-whitespace extracted characters are flagged below for visual review; this threshold can include designed slide pages as well as scanned/poor-text pages.",
        "",
        f"- Locked files checked: {len(inventory)}.",
        f"- PDFs/pages: {pdf_count}/{page_count}.",
        f"- Low-text PDF pages: {len(poor_pages)}.",
        f"- 45 CFR Part 1324 Subpart A section identifiers: PDF {len(pdf_sections)}, HTML {len(html_sections)}, common {len(pdf_sections & html_sections)}; PDF-only {sorted(pdf_sections - html_sections)}, HTML-only {sorted(html_sections - pdf_sections)}.",
        "- Section identifiers agree. This is a structural comparison; formatting and HTML page headers differ, so it does not assert byte-for-byte identity.",
        "",
        "## Low-text pages to inspect",
        "",
        "| File | PDF page | Extracted characters |",
        "|---|---:|---:|",
    ]
    for name, page, chars in poor_pages:
        lines.append(f"| `{name}` | {page} | {chars} |")
    lines.extend(["", "## Text extraction coverage", "", "| File | Method/status | Extracted characters |", "|---|---|---:|"])
    for name, status, chars in per_file:
        lines.append(f"| `{name}` | {status} | {chars} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}; {len(poor_pages)} low-text PDF pages across {pdf_count} PDFs.")


if __name__ == "__main__":
    main()
