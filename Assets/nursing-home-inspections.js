(function (global) {
  'use strict';

  // Inspections: CMS health, fire safety and emergency preparedness citations for Connecticut nursing homes,
  // resident-rights groups, the A-L scope and severity grid, survey cycles and CMS inspection scores.
  const DATA = '/data/ct_inspections.json';
  const ROSTER = '/data/nursing_home_facility_roster_ct.json';
  const EXPLORER = '/staffing/tools/nursing-home-staffing-explorer.html';
  // Categorical slots in fixed order (validated palette shared with Cost Report Insights).
  const HEX = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'];
  const INK = '#0b0b0b', INK2 = '#52514e', MUTED = '#6b6a66', GRID = '#e6e8ec';
  // Sequential blue for counts in the grid (light to dark), text switches to white on the dark steps.
  const SEQ = ['#f4f7fb', '#dde8f6', '#b9d0ee', '#8db2e2', '#5b8fd3', '#2a6cc0', '#1b4f95'];
  const LETTERS = 'ABCDEFGHIJKL';
  const PAGE = 200;

  let D = null, ROWS = [], TAG = {}, HOMES = [], BYCCN = {}, GROUP = {}, roster = null;
  let view = 'overview', homeIdx = null, findLimit = PAGE;
  const F = { home: '', group: '', cat: '', kind: '0', type: '', from: '', to: '', ss: '', repeat: false, q: '' };
  const HF = { kind: '', type: '', year: '', ss: '' };

  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const norm = t => String(t || '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  const num = v => v == null ? '' : Number(v).toLocaleString('en-US');
  const pct = (a, b) => b ? `${(100 * a / b).toFixed(1)}%` : '';
  const title = n => String(n || '').toLowerCase().replace(/(^|[^a-z0-9'’])([a-z])/g, (_, p, l) => p + l.toUpperCase()).replace(/\b(Llc|Inc|Ct)\b/g, w => w.toUpperCase());
  const fmtDate = d => { if (!d) return ''; const [y, m, dd] = d.split('-').map(Number); return new Date(Date.UTC(y, m - 1, dd)).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' }); };
  const tagLabel = t => t.replace(/^([A-Z])0*(\d+)$/, '$1$2');
  const sevLevel = l => l ? 3 - Math.floor(LETTERS.indexOf(l) / 3) : null;    // 0 = immediate jeopardy ... 3 = minimal
  const scopeOf = l => l ? LETTERS.indexOf(l) % 3 : null;
  const typeNames = bits => [bits & 1 && 'Standard', bits & 2 && 'Complaint', bits & 4 && 'Infection control'].filter(Boolean).join(', ') || 'Not recorded';
  const kindName = k => D.meta.kinds[k];

  // ------------------------------------------------------------------ rows
  function decorate() {
    const seen = {};
    ROWS = D.rows.map((r, i) => ({ i, h: r[0], date: r[1], tag: r[2], ss: r[3], bits: r[4], corr: r[5], idr: r[6], kind: r[7], year: +r[1].slice(0, 4) }));
    // Repeat: the same tag was cited at the same home on an earlier survey date in this file.
    ROWS.slice().sort((a, b) => a.date < b.date ? -1 : a.date > b.date ? 1 : 0).forEach(r => {
      const k = `${r.h}|${r.tag}`;
      r.earlier = (seen[k] || []).filter(d => d < r.date);
      (seen[k] = seen[k] || []).push(r.date);
    });
    ROWS.forEach(r => { r.repeat = r.earlier.length > 0; });
  }
  const tagInfo = t => { const v = D.tags[t] || ['', 0, null, null]; return { desc: v[0], cat: D.categories[v[1]], group: v[2], page: v[3] }; };
  function filtered(f, opts = {}) {
    const q = norm(f.q);
    return ROWS.filter(r => {
      if (f.home !== '' && f.home != null && r.h !== +f.home) return false;
      if (f.kind !== '' && f.kind != null && r.kind !== +f.kind) return false;
      if (f.group && tagInfo(r.tag).group !== f.group) return false;
      if (f.cat && tagInfo(r.tag).cat !== f.cat) return false;
      if (f.type && !(r.bits & +f.type)) return false;
      if (f.from && r.year < +f.from) return false;
      if (f.to && r.year > +f.to) return false;
      if (f.year && r.year !== +f.year) return false;
      if (!opts.ignoreSs && f.ss && r.ss !== f.ss) return false;
      if (f.repeat && !r.repeat) return false;
      if (q && !norm(`${r.tag} ${tagLabel(r.tag)} ${tagInfo(r.tag).desc}`).includes(q)) return false;
      return true;
    });
  }

  // ------------------------------------------------------------------ pieces
  function tipLayer(box) {
    let tip = box.querySelector('.ci-tip');
    if (!tip) { tip = document.createElement('div'); tip.className = 'ci-tip'; tip.hidden = true; box.appendChild(tip); }
    return {
      show(html, x, y) { tip.innerHTML = html; tip.hidden = false; const bw = box.clientWidth, tw = tip.offsetWidth; tip.style.left = `${Math.max(0, Math.min(bw - tw, x + 12))}px`; tip.style.top = `${Math.max(0, y - tip.offsetHeight - 10)}px`; },
      hide() { tip.hidden = true; },
    };
  }
  const legend = items => `<div class="ci-legend">${items.map(i => `<span><i style="background:${i.color}"></i>${esc(i.label)}</span>`).join('')}</div>`;
  const tiles = items => `<dl class="ci-tiles">${items.map(([k, v]) => `<div class="ci-tile"><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`;

  // Scope and severity grid: 4 severity rows (immediate jeopardy at the top) by 3 scope columns. Cells are buttons.
  function matrix(rows, selected, idPrefix) {
    const n = Array.from({ length: 12 }, () => 0);
    const homes = Array.from({ length: 12 }, () => new Set());
    rows.forEach(r => { const k = LETTERS.indexOf(r.ss); if (k >= 0) { n[k]++; homes[k].add(r.h); } });
    const max = Math.max(1, ...n), noSs = rows.filter(r => !r.ss).length;
    const shade = v => v ? SEQ[Math.min(SEQ.length - 1, 1 + Math.floor((SEQ.length - 2) * Math.sqrt(v / max)))] : SEQ[0];
    const sev = D.meta.severity;
    let body = '';
    sev.forEach(([key, label, letters]) => {
      body += `<tr><th scope="row">${esc(label)}</th>`;
      letters.split('').forEach((l, c) => {
        const k = LETTERS.indexOf(l), v = n[k], bg = shade(v), dark = SEQ.indexOf(bg) >= 4;
        body += `<td class="ss-cell"><button type="button" data-ss="${l}" aria-pressed="${selected === l}" style="background:${bg};color:${dark ? '#fff' : INK}"
          aria-label="${l}: ${esc(label)}, ${esc(D.meta.scope[c].toLowerCase())}. ${v} citations at ${homes[k].size} homes.">
          <span class="ss-l">${l}</span><span class="ss-n">${num(v)}</span><span class="ss-h">${homes[k].size} ${homes[k].size === 1 ? 'home' : 'homes'}</span></button></td>`;
      });
      body += '</tr>';
    });
    return `<div class="table-scroll ss-wrap"><table class="ss-grid" id="${idPrefix}-grid"><caption>Scope and severity (A to L). Choose a square to list its citations.</caption>
      <thead><tr><th scope="col">Severity</th>${D.meta.scope.map(s => `<th scope="col">${esc(s)}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>
      ${noSs ? `<p class="subtle">${num(noSs)} citations have no scope and severity code in the CMS file.</p>` : ''}
      ${selected ? `<p><button type="button" class="linkish" data-ss="">Clear the ${esc(selected)} filter</button></p>` : ''}`;
  }

  function citationTable(rows, { showHome = true, caption, limit = rows.length }) {
    const shown = rows.slice(0, limit);
    return `<div class="table-scroll"><table class="stack cite-table"><caption>${esc(caption)}</caption>
      <thead><tr>${showHome ? '<th scope="col">Home</th>' : ''}<th scope="col">Survey date</th><th scope="col">Tag</th><th scope="col">What was cited</th><th scope="col">Scope / severity</th><th scope="col">Survey type</th><th scope="col">Corrected</th></tr></thead>
      <tbody>${shown.map(r => { const t = tagInfo(r.tag), h = HOMES[r.h]; return `<tr>
        ${showHome ? `<td data-label="Home"><button type="button" class="linkish" data-home="${r.h}">${esc(title(h.name))}</button><div class="subtle">${esc(title(h.city || ''))}</div></td>` : ''}
        <td data-label="Survey date">${esc(fmtDate(r.date))}</td>
        <td data-label="Tag">${t.page ? `<a href="${esc(D.meta.resident_rights_map.appendix_pp.url)}#page=${t.page}" target="_blank" rel="noopener">${esc(tagLabel(r.tag))}</a>` : esc(tagLabel(r.tag))}${r.repeat ? `<div><span class="ci-flag" title="Also cited at this home on ${esc(r.earlier.map(fmtDate).join(', '))}">Cited before</span></div>` : ''}</td>
        <td data-label="What was cited">${esc(t.desc)}<div class="subtle">${esc(t.cat)}${r.kind ? ` · ${esc(kindName(r.kind))}` : ''}</div>${r.repeat ? `<div class="subtle">Also cited here: ${esc(r.earlier.map(fmtDate).join(', '))}</div>` : ''}</td>
        <td data-label="Scope / severity">${esc(r.ss || 'None recorded')}${r.ss ? `<div class="subtle">${esc(D.meta.severity[sevLevel(r.ss)][1])}</div>` : ''}</td>
        <td data-label="Survey type">${esc(r.kind ? 'Fire safety' : typeNames(r.bits))}${r.idr ? `<div class="subtle">${r.idr & 1 ? 'Under informal dispute resolution' : 'Under independent dispute resolution'}</div>` : ''}</td>
        <td data-label="Corrected">${r.corr ? esc(fmtDate(r.corr)) : '<span class="subtle">No date in the CMS file</span>'}${r.corr && r.corr < r.date ? '<div class="subtle">Before the survey date, as CMS recorded it</div>' : ''}</td>
      </tr>`; }).join('')}</tbody></table></div>
      ${rows.length > limit ? `<p><button type="button" class="action-button secondary" data-more>Show ${Math.min(PAGE, rows.length - limit)} more (${num(rows.length - limit)} not shown)</button></p>` : ''}`;
  }

  function csv(rows, name) {
    const head = ['ccn', 'home', 'city', 'survey_date', 'tag', 'description', 'category', 'resident_rights_group', 'kind', 'scope_severity', 'survey_type', 'correction_date', 'cited_before_on'];
    const q = v => `"${String(v == null ? '' : v).replace(/"/g, '""')}"`;
    const lines = [`# CMS citations, Connecticut. Sources: ${D.meta.citations_source}, ${D.meta.fire_source}. Built ${D.meta.build_date}. https://danbeem.xyz/staffing/tools/nursing-home-inspections.html`, head.join(',')];
    rows.forEach(r => { const t = tagInfo(r.tag), h = HOMES[r.h]; lines.push([h.ccn, h.name, h.city, r.date, tagLabel(r.tag), t.desc, t.cat, t.group ? GROUP[t.group].label : '', kindName(r.kind), r.ss, r.kind ? 'Fire safety' : typeNames(r.bits), r.corr, r.earlier.join(' ')].map(q).join(',')); });
    const blob = new Blob([lines.join('\n') + '\n'], { type: 'text/csv' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.append(a); a.click(); a.remove();
  }

  // Vertical bars of counts by year, stacked by series.
  function yearBars(box, years, series) {
    const W = Math.max(280, box.clientWidth), H = 220, m = { l: 44, r: 8, t: 10, b: 26 };
    const totals = years.map((_, i) => series.reduce((a, s) => a + s.values[i], 0));
    const max = Math.max(1, ...totals), step = Math.pow(10, Math.floor(Math.log10(max))) * (max / Math.pow(10, Math.floor(Math.log10(max))) > 5 ? 2 : 1);
    const ticks = []; for (let v = 0; v <= max + step * 0.01; v += step) ticks.push(v);
    const top = ticks[ticks.length - 1] < max ? ticks[ticks.length - 1] + step : ticks[ticks.length - 1];
    const Y = v => m.t + (H - m.t - m.b) * (1 - v / top), slot = (W - m.l - m.r) / years.length, bw = Math.min(30, slot * 0.66);
    let g = ticks.concat(top === ticks[ticks.length - 1] ? [] : [top]).map(t => `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(t)}" y2="${Y(t)}" stroke="${GRID}"/><text x="${m.l - 6}" y="${Y(t) + 4}" text-anchor="end" font-size="11" fill="${MUTED}">${num(t)}</text>`).join('');
    years.forEach((y, i) => {
      const x = m.l + slot * i + (slot - bw) / 2; let acc = 0;
      series.forEach((s, j) => { const v = s.values[i]; if (!v) return; const y1 = Y(acc + v), y0 = Y(acc); g += `<rect class="seg" data-i="${i}" data-j="${j}" x="${x}" y="${y1}" width="${bw}" height="${Math.max(0, y0 - y1 - (acc ? 2 : 0))}" rx="${acc ? 0 : 2}" fill="${s.color}"/>`; acc += v; });
      g += `<text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle" font-size="11" fill="${MUTED}">${y}</text>`;
    });
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-hidden="true">${g}</svg>`;
    const svg = box.querySelector('svg'), tip = tipLayer(box);
    svg.addEventListener('pointermove', ev => {
      const s = ev.target.closest('.seg'); if (!s) { tip.hide(); return; }
      const i = +s.dataset.i, rr = svg.getBoundingClientRect();
      tip.show(`<b>${years[i]}</b>${series.map(se => `<div>${esc(se.label)}: <b>${num(se.values[i])}</b></div>`).join('')}<div>Total: ${num(totals[i])}</div>`, ev.clientX - rr.left, ev.clientY - rr.top);
    });
    svg.addEventListener('pointerleave', () => tip.hide());
  }

  // Histogram of CMS total weighted health survey scores, with one home marked.
  function scoreHistogram(box, values, mark) {
    const W = Math.max(280, box.clientWidth), H = 200, m = { l: 34, r: 10, t: 34, b: 24 };
    const max = Math.max(...values), width = max > 400 ? 50 : 20, bins = Math.ceil((max + 1) / width);
    const counts = Array.from({ length: bins }, () => 0); values.forEach(v => counts[Math.min(bins - 1, Math.floor(v / width))]++);
    const cmax = Math.max(...counts), X = v => m.l + (W - m.l - m.r) * v / (bins * width), Y = c => m.t + (H - m.t - m.b) * (1 - c / cmax);
    let g = `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(0)}" y2="${Y(0)}" stroke="${GRID}"/>`;
    counts.forEach((c, i) => { if (c) g += `<rect class="seg" data-i="${i}" x="${X(i * width) + 1}" y="${Y(c)}" width="${Math.max(1, X(width) - X(0) - 2)}" height="${Y(0) - Y(c)}" rx="2" fill="${HEX[0]}"/>`; });
    const tickStep = width * Math.ceil(bins / 6);
    for (let v = 0; v <= bins * width; v += tickStep) g += `<text x="${X(v)}" y="${H - 12}" text-anchor="middle" font-size="11" fill="${MUTED}">${v}</text>`;
    g += `<text x="${m.l}" y="${m.t - 8}" font-size="11" fill="${MUTED}">Homes</text><text x="${W - m.r}" y="${m.t - 8}" text-anchor="end" font-size="11" fill="${MUTED}">Score (CMS total weighted health survey score)</text>`;
    if (mark != null) g += `<line x1="${X(mark)}" x2="${X(mark)}" y1="${m.t - 4}" y2="${Y(0)}" stroke="${INK}" stroke-width="2"/><text x="${X(mark) > W * 0.6 ? X(mark) - 4 : X(mark) + 4}" text-anchor="${X(mark) > W * 0.6 ? 'end' : 'start'}" y="${m.t + 8}" font-size="12" font-weight="700" fill="${INK}">This home: ${num(mark)}</text>`;
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-hidden="true">${g}</svg>`;
    const svg = box.querySelector('svg'), tip = tipLayer(box);
    svg.addEventListener('pointermove', ev => { const s = ev.target.closest('.seg'); if (!s) { tip.hide(); return; } const i = +s.dataset.i, rr = svg.getBoundingClientRect(); tip.show(`<b>${i * width} to ${i * width + width - 1}</b><div>${counts[i]} homes</div>`, ev.clientX - rr.left, ev.clientY - rr.top); });
    svg.addEventListener('pointerleave', () => tip.hide());
  }

  function picker(input, list, onPick) {
    const render = () => {
      const q = norm(input.value);
      if (!q) { list.innerHTML = ''; return; }
      const hits = HOMES.map((h, i) => ({ h, i })).filter(({ h }) => h.ccn.includes(q) || norm(`${h.name} ${h.city || ''}`).includes(q)).slice(0, 12);
      list.innerHTML = hits.map(({ h, i }) => `<li><button type="button" data-pick="${i}">${esc(title(h.name))} <span class="subtle">${esc(title(h.city || ''))} · ${h.ccn}</span></button></li>`).join('') || '<li class="subtle" style="padding:8px 12px">No match</li>';
    };
    input.addEventListener('input', render);
    input.addEventListener('keydown', e => { if (e.key === 'Escape') { input.value = ''; render(); } });
    list.addEventListener('click', e => { const b = e.target.closest('button[data-pick]'); if (!b) return; input.value = ''; list.innerHTML = ''; onPick(+b.dataset.pick); });
  }

  // ------------------------------------------------------------------ views
  function renderOverview() {
    const out = document.getElementById('ov-out');
    const kind = document.getElementById('ov-kind').value;
    const rows = ROWS.filter(r => kind === '' || r.kind === +kind);
    const health = ROWS.filter(r => r.kind === 0), nPi = D.meta.denominators.provider_info_homes;
    const ij = health.filter(r => sevLevel(r.ss) === 0), harm = health.filter(r => sevLevel(r.ss) === 1);
    const homesWith = list => new Set(list.map(r => r.h)).size;
    const years = [...new Set(rows.map(r => r.year))].sort();
    const series = kind === '' || kind === '0'
      ? [{ label: 'Standard survey', color: HEX[0], f: r => r.kind === 0 && (r.bits & 1) && !(r.bits & 2) }, { label: 'Complaint investigation', color: HEX[1], f: r => r.kind === 0 && (r.bits & 2) && !(r.bits & 1) }, { label: 'Both standard and complaint', color: HEX[2], f: r => r.kind === 0 && (r.bits & 3) === 3 }, { label: 'Other or not recorded (health)', color: HEX[3], f: r => r.kind === 0 && !(r.bits & 3) }]
      : [];
    if (kind === '' || kind === '1') series.push({ label: 'Fire safety', color: HEX[4], f: r => r.kind === 1 });
    if (kind === '' || kind === '2') series.push({ label: 'Emergency preparedness', color: HEX[6], f: r => r.kind === 2 });
    series.forEach(s => { s.values = years.map(y => rows.filter(r => r.year === y && s.f(r)).length); });
    const cats = {};
    rows.forEach(r => { const c = tagInfo(r.tag).cat; (cats[c] = cats[c] || { n: 0, h: new Set(), harm: 0 }).n++; cats[c].h.add(r.h); if (sevLevel(r.ss) <= 1 && r.ss) cats[c].harm++; });
    out.innerHTML = `
      <section class="ci-headlines" aria-label="Statewide totals">${tiles([
        ['Homes CMS lists now', `${num(nPi)}`], ['Health citations', `${num(health.length)} at ${homesWith(health)} homes`],
        ['Immediate jeopardy (J, K, L)', `${num(ij.length)} at ${homesWith(ij)} homes`], ['Actual harm (G, H, I)', `${num(harm.length)} at ${homesWith(harm)} homes`]])}
        <p class="subtle">Health citations with survey dates from ${esc(fmtDate(D.meta.citation_date_min))} to ${esc(fmtDate(D.meta.citation_date_max))}; ${num(D.meta.citation_rows_by_kind[1])} fire safety and ${num(D.meta.citation_rows_by_kind[2])} emergency preparedness citations are also included. Denominator: the ${num(nPi)} Connecticut homes in CMS Provider Information, ${esc(D.meta.provider_info_release)}.</p></section>
      <h3>Scope and severity</h3>
      <p class="subtle">Every citation gets a letter from A to L. Rows are how serious the problem was; columns are how many residents or places it affected. Choose a square to see those citations.</p>
      ${matrix(rows, '', 'ov')}
      <h3>Citations by year of survey</h3>
      <p class="subtle">CMS keeps about three standard survey cycles plus recent complaint surveys, so earlier years hold only surveys still in that window and ${esc(D.meta.citation_date_max.slice(0, 4))} runs only to ${esc(fmtDate(D.meta.citation_date_max))}. Read this as what the current file holds, not as a trend.</p>
      ${legend(series.map(s => ({ label: s.label, color: s.color })))}
      <div class="ci-chart" id="ov-years"></div>
      <details class="ci-more"><summary>Show the yearly counts as a table</summary><div class="table-scroll"><table class="stack"><caption>Citations by year of survey</caption><thead><tr><th scope="col">Year</th>${series.map(s => `<th scope="col" class="num">${esc(s.label)}</th>`).join('')}</tr></thead>
        <tbody>${years.map((y, i) => `<tr><td data-label="Year">${y}</td>${series.map(s => `<td class="num" data-label="${esc(s.label)}">${num(s.values[i])}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details>
      <h3>By regulatory category</h3>
      <div class="table-scroll"><table class="stack"><caption>Citations by CMS category</caption><thead><tr><th scope="col">Category</th><th scope="col" class="num">Citations</th><th scope="col" class="num">Homes</th><th scope="col" class="num">Harm or immediate jeopardy</th></tr></thead>
        <tbody>${Object.entries(cats).sort((a, b) => b[1].n - a[1].n).map(([c, v]) => `<tr><td data-label="Category"><button type="button" class="linkish" data-cat="${esc(c)}">${esc(c)}</button></td><td class="num" data-label="Citations">${num(v.n)}</td><td class="num" data-label="Homes">${v.h.size} of ${num(nPi)}</td><td class="num" data-label="Harm or IJ">${num(v.harm)}</td></tr>`).join('')}</tbody></table></div>`;
    yearBars(document.getElementById('ov-years'), years, series);
  }

  function renderRights() {
    const out = document.getElementById('rr-out'), map = D.meta.resident_rights_map, nPi = D.meta.denominators.provider_info_homes;
    const health = ROWS.filter(r => r.kind === 0);
    out.innerHTML = `${map.status === 'draft' ? `<div class="notice warning">${esc(map.status_note)}</div>` : ''}
      <p>Resident rights citations, grouped by topic. Each tag links to its guidance in CMS's State Operations Manual, Appendix PP (${esc(map.appendix_pp.revision)}). Counts cover health citations from ${esc(fmtDate(D.meta.citation_date_min))} to ${esc(fmtDate(D.meta.citation_date_max))}. Each tag is counted in one topic only. Topics with no Connecticut citations in the current file are listed at the end.</p>
      ${map.status === 'verified' ? `<p class="subtle">${esc(map.status_note)}</p>` : ''}
      ${D.groups.slice().sort((a, b) => (health.some(r => tagInfo(r.tag).group === b.id) ? 1 : 0) - (health.some(r => tagInfo(r.tag).group === a.id) ? 1 : 0)).map(g => {
        const rows = health.filter(r => tagInfo(r.tag).group === g.id), homes = new Set(rows.map(r => r.h));
        const serious = rows.filter(r => r.ss && sevLevel(r.ss) <= 1).length, rep = rows.filter(r => r.repeat).length;
        const latest = rows.reduce((a, r) => r.date > a ? r.date : a, '');
        const byTag = g.tags.map(t => ({ t, rows: rows.filter(r => r.tag === t) }));
        return `<article class="ci-card rr-card"><h3>${esc(g.label)}</h3>
          ${tiles([['Citations', num(rows.length)], ['Homes', `${homes.size} of ${num(nPi)}`], ['Harm or immediate jeopardy', num(serious)], ['Cited before at the same home', num(rep)]])}
          ${g.note ? `<p class="subtle">${esc(g.note)}</p>` : ''}
          ${latest ? `<p class="subtle">Most recent: ${esc(fmtDate(latest))}.</p>` : ''}
          <div class="table-scroll"><table class="stack"><caption>Tags in this group</caption><thead><tr><th scope="col">Tag</th><th scope="col">Requirement</th><th scope="col" class="num">Citations</th><th scope="col" class="num">Homes</th></tr></thead>
          <tbody>${byTag.map(({ t, rows: tr }) => { const i = tagInfo(t), ref = (D.tagref || {})[t] || [], url = ref[3] || (i.page ? `${map.appendix_pp.url}#page=${i.page}` : '');
            return `<tr><td data-label="Tag">${url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(tagLabel(t))}</a>` : esc(tagLabel(t))}</td>
              <td data-label="Requirement"><strong>${esc(ref[0] || i.desc || '')}</strong>${i.desc && ref[0] ? `<div>${esc(i.desc)}</div>` : ''}${ref[1] ? `<div class="subtle">${esc(ref[1])}</div>` : ''}${ref[2] ? `<div class="subtle">${esc(ref[2])}</div>` : ''}</td>
              <td class="num" data-label="Citations">${num(tr.length)}</td><td class="num" data-label="Homes">${new Set(tr.map(r => r.h)).size}</td></tr>`; }).join('')}</tbody></table></div>
          <p><button type="button" class="action-button secondary" data-group="${g.id}">List these citations</button></p></article>`;
      }).join('')}`;
  }

  function renderFind() {
    const out = document.getElementById('fd-out');
    const base = filtered(F, { ignoreSs: true }), rows = filtered(F).sort((a, b) => a.date < b.date ? 1 : a.date > b.date ? -1 : a.h - b.h);
    const homes = new Set(rows.map(r => r.h)).size;
    out.innerHTML = `${matrix(base, F.ss, 'fd')}
      <p role="status"><strong>${num(rows.length)}</strong> citations at <strong>${homes}</strong> ${homes === 1 ? 'home' : 'homes'} match.</p>
      ${citationTable(rows, { caption: 'Matching citations, newest first', limit: findLimit })}`;
    document.getElementById('fd-csv').onclick = () => csv(rows, 'ct-nursing-home-citations.csv');
  }

  function renderHome() {
    const out = document.getElementById('hm-out');
    if (homeIdx == null) { out.innerHTML = '<p class="subtle">Search for a home by name, town or CCN.</p>'; return; }
    const h = HOMES[homeIdx], sc = D.scores[String(homeIdx)] || null, all = ROWS.filter(r => r.h === homeIdx);
    const surveys = (D.surveys[String(homeIdx)] || []).map(s => ({ date: s[0], type: D.meta.survey_types[s[1]], cycle: s[2], foot: s[3] }));
    const health = all.filter(r => r.kind === 0), life = all.filter(r => r.kind > 0);
    const hrows = filtered({ home: homeIdx, kind: HF.kind, type: HF.type, year: HF.year, ss: HF.ss }, {});
    const hbase = filtered({ home: homeIdx, kind: HF.kind, type: HF.type, year: HF.year }, { ignoreSs: true });
    const years = [...new Set(all.map(r => r.year))].sort().reverse();
    const std = surveys.filter(s => /Standard/.test(s.type)), cmp = surveys.filter(s => /Complaint/.test(s.type));
    const stdDates = [...new Set(std.map(s => s.date))].sort().reverse();
    const scoreVals = Object.values(D.scores).map(s => s.weighted_score).filter(v => typeof v === 'number');
    const rbs = surveys.filter(s => s.foot === '29');
    const sevMax = list => { const l = list.filter(r => r.ss).map(r => r.ss).sort().pop(); return l || ''; };
    const topCats = list => { const c = {}; list.forEach(r => { const k = tagInfo(r.tag).cat; c[k] = (c[k] || 0) + 1; }); return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => `${k} (${v})`).join('; '); };
    out.innerHTML = `<h2 id="hm-title" tabindex="-1">${esc(title(h.name))}</h2>
      <p class="subtle">${esc(title(h.city || ''))} · CCN ${esc(h.ccn)} · <a href="${EXPLORER}?ccn=${esc(h.ccn)}">Staffing, ratings and the full facility profile</a>${h.in_pi ? '' : ' · Not in the current CMS Provider Information file'}</p>
      <section class="ci-headlines" aria-label="Totals for this home">${tiles([
        ['Health citations', num(health.length)], ['Harm or immediate jeopardy', num(health.filter(r => r.ss && sevLevel(r.ss) <= 1).length)],
        ['Cited before at this home', num(all.filter(r => r.repeat).length)], ['Fire safety and emergency preparedness', num(life.length)]])}</section>

      <h3>CMS health inspection score</h3>
      ${sc && typeof sc.weighted_score === 'number' ? `<p>CMS gives each home a weighted score from its last ${sc.cycle2_date ? 'standard surveys and complaint findings' : 'standard survey'}: more citations, more serious citations and more revisits raise it, and the most recent cycle counts most. This home's score is <strong>${num(sc.weighted_score)}</strong>; the chart shows where it falls among the ${scoreVals.length} Connecticut homes with a score. Its CMS health inspection rating is <strong>${sc.health_rating ? `${sc.health_rating} of 5 stars` : 'not given'}</strong>${sc.health_rating_footnote ? ` (footnote ${esc(sc.health_rating_footnote)})` : ''}.</p>
        <div class="ci-chart" id="hm-score"></div>
        <p class="subtle">Source: ${esc(D.meta.score_fields_source)}. CMS turns scores into stars by comparing homes within each state; the cut-off points will be added once they are verified against CMS's Technical Users' Guide. Survey timing matters: a home inspected recently and one inspected a year ago are compared on different periods.</p>
        <div class="table-scroll"><table class="stack"><caption>How the score is built (CMS Provider Information)</caption><thead><tr><th scope="col">Period</th><th scope="col">Standard survey</th><th scope="col" class="num">Health citations</th><th scope="col" class="num">Citation points</th><th scope="col" class="num">Revisits</th><th scope="col" class="num">Revisit points</th><th scope="col" class="num">Total</th></tr></thead><tbody>
          <tr><td data-label="Period">Cycle 1 (most recent)</td><td data-label="Standard survey">${esc(fmtDate(sc.cycle1_date))}</td><td class="num" data-label="Citations">${num(sc.cycle1_deficiencies)} <span class="subtle">(${num(sc.cycle1_standard)} standard, ${num(sc.cycle1_complaint)} complaint)</span></td><td class="num" data-label="Citation points">${num(sc.cycle1_deficiency_score)}</td><td class="num" data-label="Revisits">${num(sc.cycle1_revisits)}</td><td class="num" data-label="Revisit points">${num(sc.cycle1_revisit_score)}</td><td class="num" data-label="Total">${num(sc.cycle1_total_score)}</td></tr>
          <tr><td data-label="Period">Cycles 2 and 3</td><td data-label="Standard survey">${esc(fmtDate(sc.cycle2_date))}</td><td class="num" data-label="Citations">${num(sc.cycle23_deficiencies)} <span class="subtle">(${num(sc.cycle2_standard)} standard in cycle 2, ${num(sc.cycle23_complaint)} complaint)</span></td><td class="num" data-label="Citation points">${num(sc.cycle23_deficiency_score)}</td><td class="num" data-label="Revisits">${num(sc.cycle23_revisits)}</td><td class="num" data-label="Revisit points">${num(sc.cycle23_revisit_score)}</td><td class="num" data-label="Total">${num(sc.cycle23_total_score)}</td></tr>
          <tr><td data-label="Period"><strong>Weighted total</strong></td><td></td><td></td><td></td><td></td><td></td><td class="num" data-label="Weighted"><strong>${num(sc.weighted_score)}</strong></td></tr></tbody></table></div>`
        : '<p class="subtle">CMS Provider Information has no weighted health inspection score for this home.</p>'}

      <h3>Scope and severity at this home</h3>
      <div class="filter-row">
        <div><label for="hf-kind">Inspection</label><select id="hf-kind"><option value="">All</option><option value="0">Health</option><option value="1">Fire safety</option><option value="2">Emergency preparedness</option></select></div>
        <div><label for="hf-type">Survey type (health)</label><select id="hf-type"><option value="">All</option><option value="1">Standard</option><option value="2">Complaint</option><option value="4">Infection control</option></select></div>
        <div><label for="hf-year">Year</label><select id="hf-year"><option value="">All</option>${years.map(y => `<option>${y}</option>`).join('')}</select></div>
      </div>
      ${matrix(hbase, HF.ss, 'hm')}
      ${citationTable(hrows.sort((a, b) => a.date < b.date ? 1 : -1), { showHome: false, caption: HF.ss ? `Citations with scope and severity ${HF.ss}` : 'All matching citations, newest first' })}

      <h3>Standard survey cycles</h3>
      <p class="subtle">Standard surveys are scheduled inspections of the whole home. Complaint investigations are listed separately below. Dates are from CMS Inspection Dates (${esc(D.meta.inspection_dates_release)}), which covers about the last three years.</p>
      ${stdDates.length ? `<div class="table-scroll"><table class="stack"><caption>Standard surveys</caption><thead><tr><th scope="col">Date</th><th scope="col">Inspections</th><th scope="col" class="num">Health citations</th><th scope="col" class="num">Fire safety / EP</th><th scope="col">Highest scope / severity</th><th scope="col">Main categories</th></tr></thead><tbody>
        ${stdDates.map(d => { const kinds = std.filter(s => s.date === d), hc = all.filter(r => r.date === d && r.kind === 0 && (r.bits & 1)), lc = all.filter(r => r.date === d && r.kind > 0);
          return `<tr><td data-label="Date">${esc(fmtDate(d))}<div class="subtle">Cycle ${esc(kinds[0].cycle)}</div></td><td data-label="Inspections">${esc(kinds.map(k => k.type).join(', '))}${kinds.some(k => k.foot === '29') ? '<div><span class="ci-flag">Risk-based survey</span></div>' : ''}</td><td class="num" data-label="Health">${num(hc.length)}</td><td class="num" data-label="Fire / EP">${num(lc.length)}</td><td data-label="Highest">${esc(sevMax(hc.concat(lc)) || 'None')}</td><td data-label="Categories">${esc(topCats(hc.concat(lc)) || 'No citations')}</td></tr>`; }).join('')}</tbody></table></div>` : '<p class="subtle">No standard surveys for this home in CMS Inspection Dates.</p>'}
      <p class="subtle">${rbs.length ? `CMS records ${rbs.length} risk-based ${rbs.length === 1 ? 'survey' : 'surveys'} for this home (footnote 29).` : 'CMS Inspection Dates has no risk-based survey record (footnote 29) for this home. No record is not proof that no survey occurred.'}</p>

      <h3>Complaint investigations</h3>
      ${cmp.length ? `<div class="table-scroll"><table class="stack"><caption>Complaint investigations (CMS Inspection Dates)</caption><thead><tr><th scope="col">Date</th><th scope="col">Type</th><th scope="col" class="num">Citations from complaints on this date</th></tr></thead><tbody>
        ${cmp.map(s => `<tr><td data-label="Date">${esc(fmtDate(s.date))}</td><td data-label="Type">${esc(s.type)}</td><td class="num" data-label="Citations">${num(all.filter(r => r.date === s.date && (r.kind > 0 || (r.bits & 2))).length)}</td></tr>`).join('')}</tbody></table></div>
        <p class="subtle">An investigation with no citations means inspectors did not cite a requirement on that date; it does not say whether the complaint was substantiated.</p>` : '<p class="subtle">No complaint investigations for this home in CMS Inspection Dates.</p>'}

      <h3>Fire safety and emergency preparedness</h3>
      <p class="subtle">K-tags are Life Safety Code requirements (fire, egress, alarms, sprinklers, emergency power). E-tags are emergency preparedness requirements (plans, evacuation, communication, training).</p>
      ${life.length ? citationTable(life.sort((a, b) => a.date < b.date ? 1 : -1), { showHome: false, caption: 'Fire safety and emergency preparedness citations, newest first' }) : '<p class="subtle">No fire safety or emergency preparedness citations for this home in the CMS file.</p>'}`;
    if (sc && typeof sc.weighted_score === 'number') scoreHistogram(document.getElementById('hm-score'), scoreVals, sc.weighted_score);
    ['kind', 'type', 'year'].forEach(k => { const el = document.getElementById(`hf-${k}`); el.value = HF[k]; el.addEventListener('change', () => { HF[k] = el.value; HF.ss = ''; renderHome(); syncUrl(); }); });
  }

  async function renderCounted() {
    const out = document.getElementById('ct-out');
    if (!roster) {
      out.innerHTML = '<p class="subtle">Loading the facility roster.</p>';
      try { const r = await fetch(ROSTER); if (!r.ok) throw new Error(`HTTP ${r.status}`); roster = await r.json(); }
      catch (err) { out.innerHTML = `<p class="notice error">The facility roster could not be loaded. Details: ${esc(err.message)}</p>`; return; }
    }
    const s = roster.metadata.summary, recs = roster.records;
    out.innerHTML = `<p>Different CMS files cover different sets of homes. This list shows every Connecticut CCN that appears in any source the site uses, and where each one appears, so every percentage on these pages can say what it is out of.</p>
      <div class="table-scroll"><table class="stack"><caption>How many homes each source covers</caption><thead><tr><th scope="col">Source</th><th scope="col" class="num">Homes</th></tr></thead><tbody>
        <tr><td data-label="Source">CMS Provider Information, ${esc(s.provider_info_release)} (homes CMS lists now)</td><td class="num" data-label="Homes">${num(s.provider_info_homes)}</td></tr>
        <tr><td data-label="Source">CMS PBJ staffing, ${esc(s.pbj_latest_quarter)}</td><td class="num" data-label="Homes">${num(s.pbj_homes_latest_quarter)}</td></tr>
        <tr><td data-label="Source">CMS PBJ staffing, any quarter ${esc(s.pbj_quarters[0])} to ${esc(s.pbj_latest_quarter)}</td><td class="num" data-label="Homes">${num(s.pbj_homes_any_quarter)}</td></tr>
        <tr><td data-label="Source">CMS Health Deficiencies</td><td class="num" data-label="Homes">${num(s.homes_with_health_citations)}</td></tr>
        <tr><td data-label="Source">CMS Inspection Dates</td><td class="num" data-label="Homes">${num(s.homes_in_inspection_dates)}</td></tr>
        <tr><td data-label="Source">CMS Penalties (any fine or payment denial in the file)</td><td class="num" data-label="Homes">${num(s.homes_with_penalties)}</td></tr>
        <tr><td data-label="Source">All CCNs seen in any source</td><td class="num" data-label="Homes">${num(s.all_ccns_seen)}</td></tr></tbody></table></div>
      <p class="subtle">${num(s.provider_info_homes_without_latest_pbj)} homes CMS lists now have no PBJ staffing rows for ${esc(s.pbj_latest_quarter)} in the CMS file this site uses. That is a fact about the file, not a finding about the home; CMS can publish late submissions later.</p>
      <div class="table-scroll"><table class="stack"><caption>Homes missing from at least one source</caption><thead><tr><th scope="col">Home</th><th scope="col">CCN</th><th scope="col">Notes</th></tr></thead>
        <tbody>${recs.filter(r => r.notes.length).map(r => `<tr><td data-label="Home">${esc(title(r.name || 'Name not found'))}<div class="subtle">${esc(title(r.city || ''))}</div></td><td data-label="CCN">${esc(r.ccn)}</td><td data-label="Notes">${r.notes.map(n => `<div>${esc(n)}</div>`).join('')}</td></tr>`).join('')}</tbody></table></div>
      <p class="subtle">The full roster is published as <a href="${ROSTER}">nursing_home_facility_roster_ct.json</a>.</p>`;
  }

  // ------------------------------------------------------------------ tabs, URL state, init
  function show(v, focus) {
    view = v;
    document.querySelectorAll('.ci-tabs [role="tab"]').forEach(t => { const on = t.dataset.view === v; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; if (on && focus) t.focus(); });
    document.querySelectorAll('[role="tabpanel"]').forEach(p => { p.hidden = p.id !== `panel-${v}`; });
    render();
  }
  function render() {
    ({ overview: renderOverview, rights: renderRights, find: renderFind, home: renderHome, counted: renderCounted })[view]();
    syncUrl();
  }
  function openFind(patch) {
    Object.assign(F, { home: '', group: '', cat: '', kind: '0', type: '', from: '', to: '', ss: '', repeat: false, q: '' }, patch);
    syncFindControls(); findLimit = PAGE; show('find');
  }
  function openHome(i) { homeIdx = i; Object.assign(HF, { kind: '', type: '', year: '', ss: '' }); show('home'); const t = document.getElementById('hm-title'); if (t) t.focus(); }
  function syncFindControls() {
    const set = (id, v) => { const el = document.getElementById(id); if (el.type === 'checkbox') el.checked = !!v; else el.value = v; };
    set('fd-group', F.group); set('fd-cat', F.cat); set('fd-kind', F.kind); set('fd-type', F.type); set('fd-from', F.from); set('fd-to', F.to); set('fd-repeat', F.repeat); set('fd-q', F.q);
    document.getElementById('fd-home-chip').innerHTML = F.home !== '' ? `<span class="chip">${esc(title(HOMES[+F.home].name))} <button type="button" aria-label="Remove home filter" data-clear-home>×</button></span>` : '';
  }
  function syncUrl() {
    const u = new URL(global.location.href), p = new URLSearchParams();
    p.set('view', view);
    if (view === 'overview' && document.getElementById('ov-kind').value) p.set('kind', document.getElementById('ov-kind').value);
    if (view === 'find') Object.entries(F).forEach(([k, v]) => { if (k === 'home' && v !== '') p.set('ccn', HOMES[+v].ccn); else if (k === 'kind' ? v !== '0' : (v !== '' && v !== false)) p.set(k, v === true ? '1' : v); });
    if (view === 'home' && homeIdx != null) { p.set('ccn', HOMES[homeIdx].ccn); Object.entries(HF).forEach(([k, v]) => { if (v) p.set(`h${k}`, v); }); }
    u.search = p.toString();
    if (u.href !== global.location.href) document.getElementById('ci-copy-status').textContent = '';
    global.history.replaceState(null, '', u);
  }
  async function copyViewLink() {
    const status = document.getElementById('ci-copy-status');
    try { await navigator.clipboard.writeText(global.location.href); status.textContent = 'Link copied.'; }
    catch { status.textContent = 'Copy the link from the address bar.'; }
  }

  async function init() {
    const note = document.getElementById('ci-note');
    try { const r = await fetch(DATA); if (!r.ok) throw new Error(`HTTP ${r.status}`); D = await r.json(); }
    catch (err) { note.textContent = `The inspection data could not be loaded. Details: ${err.message}`; note.className = 'notice error'; return; }
    HOMES = D.homes.map(h => ({ ccn: h[0], name: h[1], city: h[2], in_pi: !!h[3] }));
    HOMES.forEach((h, i) => { BYCCN[h.ccn] = i; });
    D.groups.forEach(g => { GROUP[g.id] = g; });
    decorate();
    note.textContent = `${num(D.meta.citation_rows)} citations at ${num(HOMES.length)} homes. CMS files: ${D.meta.citations_source}, ${D.meta.fire_source}, ${D.meta.inspection_dates_source}.`;

    const q = new URLSearchParams(global.location.search);
    // overview
    const ok = document.getElementById('ov-kind'); ok.value = ['0', '1', '2'].includes(q.get('kind')) ? q.get('kind') : '0'; ok.addEventListener('change', render);
    // find
    document.getElementById('fd-group').innerHTML = '<option value="">Any</option>' + D.groups.map(g => `<option value="${g.id}">${esc(g.label)}</option>`).join('');
    document.getElementById('fd-cat').innerHTML = '<option value="">Any</option>' + D.categories.slice().sort().map(c => `<option>${esc(c)}</option>`).join('');
    const years = [...new Set(ROWS.map(r => r.year))].sort();
    ['fd-from', 'fd-to'].forEach(id => { document.getElementById(id).innerHTML = '<option value="">Any</option>' + years.map(y => `<option>${y}</option>`).join(''); });
    const bind = (id, key, ev = 'change') => document.getElementById(id).addEventListener(ev, e => { F[key] = e.target.type === 'checkbox' ? e.target.checked : e.target.value; findLimit = PAGE; renderFind(); syncUrl(); });
    bind('fd-group', 'group'); bind('fd-cat', 'cat'); bind('fd-kind', 'kind'); bind('fd-type', 'type'); bind('fd-from', 'from'); bind('fd-to', 'to'); bind('fd-repeat', 'repeat'); bind('fd-q', 'q', 'input');
    picker(document.getElementById('fd-home'), document.getElementById('fd-home-results'), i => { F.home = String(i); syncFindControls(); findLimit = PAGE; renderFind(); syncUrl(); });
    document.getElementById('fd-home-chip').addEventListener('click', e => { if (e.target.closest('[data-clear-home]')) { F.home = ''; syncFindControls(); renderFind(); syncUrl(); } });
    picker(document.getElementById('hm-search'), document.getElementById('hm-results'), openHome);
    // delegated clicks
    document.querySelector('main').addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      if (b.dataset.home != null) { openHome(+b.dataset.home); return; }
      if (b.dataset.cat != null) { openFind({ cat: b.dataset.cat, kind: document.getElementById('ov-kind').value }); return; }
      if (b.dataset.group != null) { openFind({ group: b.dataset.group }); return; }
      if (b.hasAttribute('data-more')) { findLimit += PAGE; renderFind(); return; }
      if (b.dataset.ss != null) {
        const panel = b.closest('[role="tabpanel"]').id;
        if (panel === 'panel-overview') { openFind({ ss: b.dataset.ss, kind: document.getElementById('ov-kind').value }); return; }
        if (panel === 'panel-find') { F.ss = F.ss === b.dataset.ss ? '' : b.dataset.ss; findLimit = PAGE; renderFind(); syncUrl(); document.querySelector(`#fd-grid [data-ss="${F.ss || b.dataset.ss}"]`)?.focus(); return; }
        if (panel === 'panel-home') { HF.ss = HF.ss === b.dataset.ss ? '' : b.dataset.ss; renderHome(); syncUrl(); document.querySelector(`#hm-grid [data-ss="${HF.ss || b.dataset.ss}"]`)?.focus(); return; }
      }
    });
    document.getElementById('ci-copy').addEventListener('click', copyViewLink);
    const tabs = [...document.querySelectorAll('.ci-tabs [role="tab"]')];
    tabs.forEach((t, i) => {
      t.addEventListener('click', () => show(t.dataset.view));
      t.addEventListener('keydown', e => { const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0; if (d) { e.preventDefault(); show(tabs[(i + d + tabs.length) % tabs.length].dataset.view, true); } });
    });
    // restore state from the URL
    const v = q.get('view');
    const ccnIdx = q.get('ccn') != null ? BYCCN[q.get('ccn')] : undefined;
    if (v === 'find') {
      Object.keys(F).forEach(k => { if (k === 'home') F.home = ccnIdx != null ? String(ccnIdx) : ''; else if (k === 'repeat') F.repeat = q.get('repeat') === '1'; else if (q.get(k) != null) F[k] = q.get(k); });
      if (F.ss && !LETTERS.includes(F.ss)) F.ss = '';
      syncFindControls();
    }
    if (v === 'home' && ccnIdx != null) { homeIdx = ccnIdx; ['kind', 'type', 'year', 'ss'].forEach(k => { if (q.get(`h${k}`)) HF[k] = q.get(`h${k}`); }); }
    if (!v && ccnIdx != null) { homeIdx = ccnIdx; show('home'); return; }
    show(['overview', 'rights', 'find', 'home', 'counted'].includes(v) ? v : 'overview');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  global.NursingHomeInspections = { _test: { matrix: () => D && matrix(ROWS, '', 't'), rows: () => ROWS, filtered } };
})(window);
