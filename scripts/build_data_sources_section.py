"""Write the 'Where the data comes from' table on the methodology page from data/data_sources.json.

  python scripts/build_data_sources_section.py          # rewrite the section between the markers
  python scripts/build_data_sources_section.py --check  # exit 1 if the page is out of date
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "staffing" / "tools" / "nursing-home-staffing-methodology.html"
REG = ROOT / "data" / "data_sources.json"
START, END = "<!-- data-sources:start -->", "<!-- data-sources:end -->"


def render(reg):
    e = html.escape
    rows = "\n".join(
        f'              <tr data-source-id="{e(s["id"])}">'
        f'<th scope="row"><a href="{e(s["page"])}" rel="noopener">{e(s["name"])}</a><div class="subtle">{e(s["publisher"])}</div></th>'
        f'<td data-label="Updated by the publisher">{e(s["frequency"])}<div class="subtle">{e(s["frequency_basis"])}</div></td>'
        f'<td data-label="We check">{e(s["check"])}</td>'
        f'<td data-label="Used in">{e(", ".join(s["feeds"]))}</td></tr>'
        for s in reg["sources"])
    return f"""{START}
    <section class="wrap content-section" aria-labelledby="data-sources-title">
      <div class="panel">
        <div class="sectionHeader">
          <div>
            <div class="eyebrow">Sources And Updates</div>
            <h2 id="data-sources-title">Where the data comes from and how often it is updated</h2>
          </div>
        </div>
        <p>Every figure on these tools comes from a public CMS or Connecticut source. The table lists each source, how often its publisher updates it, and how often this site checks for a new release. Each tool shows the release it was built from. The same list is published as <a href="/data/data_sources.json">data_sources.json</a>.</p>
        <div class="table-scroll">
          <style>.ds-table th, .ds-table td {{ text-align:left; vertical-align:top; padding:10px 12px; }} .ds-table tbody th {{ font-weight:700; min-width:14rem; }} .ds-table .subtle {{ font-weight:400; margin-top:2px; }} @media (max-width: 720px) {{ .ds-table, .ds-table tbody, .ds-table tr, .ds-table th, .ds-table td {{ display:block; width:auto; min-width:0; }} .ds-table thead {{ display:none; }} .ds-table caption {{ display:block; text-align:left; padding:4px 0; }} .ds-table tr {{ border-top:1px solid #d7dee8; padding:8px 0; }} .ds-table td {{ padding:4px 12px; }} .ds-table td::before {{ content: attr(data-label) ": "; font-weight:700; }} }}</style>
          <table class="stack ds-table">
            <caption>Data sources and update schedule</caption>
            <thead><tr><th scope="col">Source</th><th scope="col">Updated by the publisher</th><th scope="col">We check</th><th scope="col">Used in</th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
        </div>
      </div>
    </section>
    {END}"""


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    page = PAGE.read_text(encoding="utf-8")
    block = render(reg)
    if START in page:
        new = page[:page.index(START)] + block + page[page.index(END) + len(END):]
    else:
        anchor = '<section class="wrap content-section" aria-labelledby="limitations-title">'
        if anchor not in page:
            print("anchor not found on the methodology page")
            return 1
        new = page.replace(anchor, block + "\n\n    " + anchor, 1)
    if "--check" in sys.argv:
        ok = new == page
        print(f"Data sources section {'up to date' if ok else 'OUT OF DATE: run scripts/build_data_sources_section.py'}: {len(reg['sources'])} sources.")
        return 0 if ok else 1
    PAGE.write_text(new, encoding="utf-8")
    print(f"Wrote the data sources section: {len(reg['sources'])} sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
