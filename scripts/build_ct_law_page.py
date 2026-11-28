"""Generate /legislation/law/ from data/ct_ltc_authorities.json.

The page is fully static: every quote is in the HTML, so it works without JavaScript and prints.
A small inline script only filters what is already on the page. Masthead, navigation and footer
are copied from /legislation/2027/ so the suite stays consistent.

Run: python scripts/build_ct_law_page.py   (rewrites legislation/law/index.html)
"""
from __future__ import annotations

import html
import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TEMPLATE = ROOT / "legislation/2027/index.html"
OUT = ROOT / "legislation/law/index.html"

GROUPS = [
    ("cgs", "Connecticut General Statutes, chapter 368v", lambda a: a["id"].startswith("ct-cgs-")),
    ("d8t", "Nursing home regulations, RCSA §19-13-D8t", lambda a: a["id"].startswith("ct-rcsa-19-13-d8t")),
    ("ltcop", "Long Term Care Ombudsman Program regulations, RCSA §§17b-411-1 to 17b-411-14", lambda a: a["id"].startswith("ct-rcsa-17b-411")),
    ("cfr1324", "Federal Ombudsman rule, 45 CFR Part 1324", lambda a: a["id"].startswith("45cfr-1324")),
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def section_key(a: dict) -> str:
    """Group paragraphs by their section (e.g. 'Conn. Gen. Stat. §19a-535')."""
    return re.sub(r"(\([^)]*\))+$", "", a["citation"]).strip()


def render(doc: dict) -> str:
    auths = doc["authorities"]
    parts = []
    toc = []
    for gid, label, test in GROUPS:
        rows = [a for a in auths if test(a)]
        if not rows:
            continue
        sections: OrderedDict[str, list] = OrderedDict()
        for a in rows:
            sections.setdefault(section_key(a), []).append(a)
        toc.append(f'<a href="#g-{gid}">{esc(label)}</a>')
        parts.append(f'<section class="wrap content-section law-group" id="g-{gid}" aria-labelledby="h-{gid}"><div class="panel">'
                     f'<h2 id="h-{gid}">{esc(label)}</h2>'
                     f'<p class="subtle">{len(rows)} paragraphs in {len(sections)} section{"" if len(sections) == 1 else "s"}.</p>')
        for sec, items in sections.items():
            title = items[0]["title"]
            title = "" if title.strip() == sec.split("§")[-1].strip() else title
            url = items[0]["source_url"]
            anchor = re.sub(r"[^a-z0-9]+", "-", sec.lower()).strip("-")
            parts.append(f'<details class="law-section" id="{anchor}" data-law="{gid}"><summary><strong>{esc(sec)}</strong>'
                         + (f' <span class="law-title">{esc(title)}</span>' if title else "")
                         + f' <span class="microcopy">({len(items)})</span></summary>'
                         f'<p class="src">Source: <a href="{esc(url)}">{esc(url)}</a> · official copy saved {esc(items[0]["verified_date"])}</p><ol class="law-paras">')
            for a in items:
                parts.append(f'<li id="{esc(a["id"])}"><span class="cite">{esc(a["citation"])}</span>'
                             f'<blockquote>{esc(a["quote"])}</blockquote></li>')
            parts.append("</ol></details>")
        parts.append("</div></section>")
    limits = "".join(f"<li>{esc(x)}</li>" for x in doc.get("limitations", []))
    main = f"""
  <main id="main-content">
    <section class="hero wrap" aria-labelledby="law-title">
      <div class="panel">
        <div class="breadcrumb"><a href="/legislation/">Legislative Tracker</a> / Current law</div>
        <div class="pill">Reference</div>
        <h1 id="law-title">Connecticut long-term care law, word for word</h1>
        <p>The statutes and regulations the legislative storylines refer to, quoted exactly from official copies, paragraph by paragraph, with the source and the date the copy was saved. Use it to check what current law says before reading a bill.</p>
        <nav class="dossier-guide" aria-label="On this page">{''.join(toc)}<a href="#about-law">About these quotes</a></nav>
        <div class="notice warning">Independent research, not affiliated with the Connecticut Long Term Care Ombudsman Program or any State agency. This is not legal advice. Laws change; check the official source for amendments after the date shown.</div>
        <div class="filter-grid law-filter" hidden>
          <div><label for="law-q">Find words in the law</label><input id="law-q" type="search" placeholder="Try discharge, bed reservation, virtual monitoring"></div>
          <p id="law-count" class="subtle" role="status"></p>
        </div>
      </div>
    </section>
{''.join(parts)}
    <section class="wrap content-section" aria-labelledby="about-law">
      <div class="panel">
        <h2 id="about-law">About these quotes</h2>
        <ul>{limits}</ul>
        <p class="subtle">Data: <a href="/data/ct_ltc_authorities.json">ct_ltc_authorities.json</a> ({len(auths)} paragraphs).</p>
      </div>
    </section>
  </main>
"""
    script = """
<script>
(() => {
  const openHash = () => { const t = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1))); const d = t && (t.matches('details') ? t : t.closest('details')); if (d) { d.open = true; t.scrollIntoView(); } };
  window.addEventListener('hashchange', openHash); openHash();
  const box = document.querySelector('.law-filter'); const q = document.getElementById('law-q'); const count = document.getElementById('law-count');
  if (!box || !q) return; box.hidden = false;
  const items = [...document.querySelectorAll('.law-paras li')];
  const run = () => {
    const words = q.value.toLowerCase().split(/\\s+/).filter(Boolean); let shown = 0;
    document.querySelectorAll('.law-section').forEach(sec => {
      let any = false; const head = sec.querySelector('summary').textContent.toLowerCase();
      sec.querySelectorAll('li').forEach(li => { const text = head + ' ' + li.textContent.toLowerCase(); const hit = words.every(w => text.includes(w)); li.hidden = !hit; if (hit) { any = true; shown++; } });
      sec.hidden = !any; if (words.length) sec.open = any;
    });
    document.querySelectorAll('.law-group').forEach(g => { g.hidden = ![...g.querySelectorAll('.law-section')].some(x => !x.hidden); });
    count.textContent = words.length ? `${shown} of ${items.length} paragraphs match.` : `${items.length} paragraphs.`;
  };
  q.addEventListener('input', run); run();
})();
</script>
"""
    style = """
  <style>
    .law-section { border-top:1px solid var(--ltcop-border); padding:10px 0; }
    .law-section summary { cursor:pointer; }
    .law-title { color:var(--ltcop-muted); }
    .law-paras { margin:8px 0 0; padding-left:0; list-style:none; display:grid; gap:10px; }
    .law-paras .cite { display:block; font-weight:800; font-size:13px; }
    .law-paras blockquote { margin:4px 0 0; padding:8px 12px; border-left:3px solid var(--ltcop-border); max-width:88ch; line-height:1.55; }
    .src, #main-content li { overflow-wrap:anywhere; }
    .src { font-size:12px; color:var(--ltcop-muted); }
    .dossier-guide { display:flex; flex-wrap:wrap; gap:6px 14px; }
    label { display:block; font-weight:800; margin-bottom:6px; }
    input { width:100%; padding:10px 12px; border-radius:8px; border:1px solid var(--ltcop-border); font-family:inherit; }
    @media print { .ltcop-masthead, footer, .law-filter, .dossier-guide { display:none !important; } .law-section { break-inside:avoid; } details.law-section > *:not(summary) { display:block; } }
  </style>
"""
    tpl = TEMPLATE.read_text(encoding="utf-8")
    head_end = tpl.index("</head>")
    head = tpl[:head_end]
    head = re.sub(r"<title>.*?</title>", "<title>Connecticut Long-Term Care Law, Word for Word | CT Long-Term Care Advocacy</title>", head, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*"', '<meta name="description" content="Connecticut nursing home and residential care home statutes and regulations, and the federal Ombudsman rule, quoted exactly from official copies with sources and dates."', head)
    head = head.replace('<script defer src="/Assets/ct-session-tracker.js"></script>', "")
    head = re.sub(r"\s*<style>.*?</style>", "", head, count=1, flags=re.S) + style
    body_start = tpl.index("<body")
    pre_main = tpl[body_start:tpl.index("<main")]
    post_main = tpl[tpl.index("</main>") + len("</main>"):]
    post_main = post_main.replace("2027 Long-Term Care Bill Tracker. Research support; not an official position.", "Connecticut long-term care law reference. Research support; not legal advice and not an official position.")
    post_main = post_main.replace('<div id="toast" class="toast" role="status" aria-live="polite"></div>', "")
    return head + "</head>\n" + pre_main.rstrip() + main + post_main.replace("</body>", script + "</body>")


def main() -> None:
    doc = json.loads((DATA / "ct_ltc_authorities.json").read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(doc), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(doc['authorities'])} paragraphs.")


if __name__ == "__main__":
    main()
