(function (global) {
  'use strict';

  // Cost Report Insights: trends, comparisons, peer groups, pivot, scatter and money flow from DSS cost reports.
  const DATA = '/data/ct_cost_report_insights.json';
  const DETAIL = ccn => `/data/cost_reports/${ccn}.json`;
  const COST_PAGE = '/staffing/tools/nursing-home-cost-reports.html';
  // Categorical slots in fixed order (validated: adjacent CVD dE >= 9.1, normal-vision >= 19.6; three light slots
  // are under 3:1 contrast, so every chart ships a legend and a table view).
  const HEX = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'];
  const INK = '#0b0b0b', INK2 = '#52514e', MUTED = '#6b6a66', GRID = '#e6e8ec', BAND = '#dde6f2', MEDIAN = '#6b7a90', OTHER = '#b8bfc9';

  let D = null, META = {}, KEYS = [], HOMES = {}, real = false;
  const detailCache = {};

  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const norm = t => String(t || '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  const money = v => v == null ? '' : (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString('en-US');
  const money2 = v => v == null ? '' : (v < 0 ? '-$' : '$') + Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const pct = (v, d = 1) => v == null ? '' : `${(v * 100).toFixed(d)}%`;
  const num = (v, d = 0) => v == null ? '' : Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
  const fmt = (key, v) => { const u = (META[key] || {}).unit; return u === 'pct' ? pct(v) : u === 'hours' ? num(v, 2) : money2(v); };
  const signed = (v, format) => v == null ? '' : (v > 0 ? '+' : '') + format(v);
  const relativeChange = (from, to) => from == null || to == null || from === 0 ? null : (to - from) / Math.abs(from);
  const median = a => { const s = a.filter(x => x != null).sort((x, y) => x - y); if (!s.length) return null; const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const mean = a => { const s = a.filter(x => x != null); return s.length ? s.reduce((p, c) => p + c, 0) / s.length : null; };
  const title = n => String(n || '').toLowerCase().replace(/(^|[^a-z0-9'’])([a-z])/g, (_, prefix, letter) => prefix + letter.toUpperCase()).replace(/\b(Llc|Inc|Ct)\b/g, w => w.toUpperCase());

  // ------------------------------------------------------------------ values
  // Composite figure for the scatter: everything that is neither staff nor resident care.
  const VIRTUAL = { overhead: { key: 'overhead', label: 'Administration, building, plant and finance', unit: 'money', group: 'Combined',
    definition: 'Administrative and general + building and property + plant and utilities + interest + insurance, per resident day.', parts: ['admin', 'property', 'plant', 'interest', 'insurance'] } };
  const isMoney = k => (META[k] || {}).unit === 'money';
  const factor = y => real ? (D.cpi.factor_to_base[y] || null) : 1;

  function val(h, y, key) {
    const r = h && h.years[y];
    if (!r) return null;
    if (VIRTUAL[key]) {
      const parts = VIRTUAL[key].parts.map(k => r.v[KEYS.indexOf(k)]);
      if (parts.some(p => p == null)) return null;
      const s = parts.reduce((a, b) => a + b, 0);
      return real ? s * factor(y) : s;
    }
    const v = r.v[KEYS.indexOf(key)];
    if (v == null) return null;
    return isMoney(key) && real ? v * factor(y) : v;
  }
  function bandAt(key, y) {
    const b = (D.bands[key] || {})[y];
    if (!b) return null;
    const f = isMoney(key) ? factor(y) : 1;
    return { lo: b[0] * f, med: b[1] * f, hi: b[2] * f, n: b[3] };
  }
  const usable = (h, y) => h.years[y] && h.years[y].ok;          // passed every check
  const homeYears = h => Object.keys(h.years).sort();

  function metricOptions(sel, keys, chosen) {
    const all = keys.map(k => META[k]);
    const groups = [...new Set(all.map(m => m.group))];
    sel.innerHTML = groups.map(g => `<optgroup label="${esc(g)}">${all.filter(m => m.group === g).map(m => `<option value="${m.key}">${esc(m.label)}</option>`).join('')}</optgroup>`).join('');
    if (chosen) sel.value = chosen;
  }
  function yearOptions(sel, chosen) {
    sel.innerHTML = D.years.slice().reverse().map(y => `<option value="${y}">${y}</option>`).join('');
    sel.value = String(chosen || D.years[D.years.length - 1]);
  }

  // ------------------------------------------------------------------ home picker (search box + list)
  function picker(input, list, onPick) {
    const all = Object.values(HOMES);
    const render = () => {
      const q = norm(input.value);
      if (!q) { list.innerHTML = ''; return; }
      const hits = all.filter(h => h.ccn.includes(q) || norm(`${h.name} ${h.city || ''}`).includes(q)).slice(0, 12);
      list.innerHTML = hits.map(h => `<li><button type="button" data-ccn="${h.ccn}">${esc(title(h.name))} <span class="subtle">${esc(h.city || '')} · ${h.ccn}</span></button></li>`).join('')
        || '<li class="subtle" style="padding:8px 12px">No match</li>';
    };
    input.addEventListener('input', render);
    input.addEventListener('keydown', e => { if (e.key === 'Escape') { input.value = ''; render(); } });
    list.addEventListener('click', e => {
      const b = e.target.closest('button[data-ccn]');
      if (!b) return;
      input.value = ''; list.innerHTML = '';
      onPick(b.dataset.ccn);
    });
  }

  // ------------------------------------------------------------------ chart primitives (SVG, sized to the container)
  function niceTicks(lo, hi, n = 4) {
    if (lo === hi) { hi = lo + 1; }
    const span = hi - lo, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map(s => s * mag).find(s => s >= step0) || 10 * mag;
    const t = []; let v = Math.floor(lo / step) * step;
    for (; v < hi - step * 0.001; v += step) t.push(+v.toFixed(10));
    t.push(+v.toFixed(10));
    return t;
  }
  function axisFmt(unit, v) {
    if (unit === 'pct') return `${Math.round(v * 100)}%`;
    if (unit === 'hours') return num(v, 1);
    return Math.abs(v) >= 10000 ? `$${Math.round(v / 1000)}K` : `$${num(v)}`;
  }
  function tipLayer(box) {
    let tip = box.querySelector('.ci-tip');
    if (!tip) { tip = document.createElement('div'); tip.className = 'ci-tip'; tip.hidden = true; box.appendChild(tip); }
    return {
      show(html, x, y) {
        tip.innerHTML = html; tip.hidden = false;
        const bw = box.clientWidth, tw = tip.offsetWidth;
        tip.style.left = `${Math.max(0, Math.min(bw - tw, x + 12))}px`;
        tip.style.top = `${Math.max(0, y - tip.offsetHeight - 10)}px`;
      },
      hide() { tip.hidden = true; },
    };
  }
  const evX = d => { const [y, m, dd] = d.split('-').map(Number); return y + (m - 1 + (dd - 1) / 30 - 8.97) / 12; };

  // series: [{name, color, points:[[year, value]], dashed, width, faint}] ; band: {year:{lo,med,hi}} ; events: [{date, n, label}]
  function fitLabels(svg) {
    svg.querySelectorAll('text[data-fit]').forEach(text => {
      const full = text.textContent;
      if (text.getComputedTextLength() <= Number(text.dataset.fit)) return;
      const chars = [...full];
      do {
        chars.pop();
        text.textContent = chars.join('').trimEnd() + '…';
      } while (chars.length && text.getComputedTextLength() > Number(text.dataset.fit));
      const tip = document.createElementNS(svg.namespaceURI, 'title');
      tip.textContent = full;
      text.append(tip);
    });
  }

  function pointLabels(points, x, top, bottom, width, className) {
    const labels = points.sort((a, b) => a.y - b.y);
    const gap = 16;
    labels.forEach((p, i) => { p.labelY = Math.max(p.y, i ? labels[i - 1].labelY + gap : top); });
    for (let i = labels.length - 1; i >= 0; i--) {
      labels[i].labelY = Math.min(labels[i].labelY, i === labels.length - 1 ? bottom : labels[i + 1].labelY - gap);
    }
    return `<g pointer-events="none">${labels.map(p => `
      <path d="M${p.x},${p.y} L${x - 4},${p.labelY}" fill="none" stroke="${p.color}" opacity="0.65"/>
      <text class="${className}" data-fit="${width}" x="${x}" y="${p.labelY + 4}" font-size="11" font-weight="700" fill="${INK}">${esc(p.name)}</text>`).join('')}</g>`;
  }

  function lineChart(box, { series, band, unit, events = [], height = 220, years = D.years, yZero = unit !== 'pct', onClickYear }) {
    const W = Math.max(280, box.clientWidth), H = height;
    const labels = series.filter(s => s.endLabel);
    const labelWidth = Math.min(146, Math.round(W * 0.31));
    const m = { l: 54, r: labels.length ? labelWidth + 14 : 14, t: events.length ? 22 : 10, b: 26 };
    const xs = years.map(Number), x0 = xs[0], x1 = xs[xs.length - 1];
    const vals = [];
    series.forEach(s => s.points.forEach(p => p[1] != null && vals.push(p[1])));
    if (band) Object.values(band).forEach(b => b && vals.push(b.lo, b.hi));
    if (!vals.length) { box.innerHTML = '<p class="subtle">No figures for this selection.</p>'; return; }
    let lo = Math.min(...vals), hi = Math.max(...vals);
    if (yZero && lo > 0) lo = 0;
    const ticks = niceTicks(lo, hi); lo = Math.min(lo, ticks[0]); hi = Math.max(hi, ticks[ticks.length - 1]);
    const X = v => m.l + (W - m.l - m.r) * (x1 === x0 ? 0.5 : (v - x0) / (x1 - x0));
    const Y = v => m.t + (H - m.t - m.b) * (1 - (v - lo) / (hi - lo || 1));
    let g = '';
    g += ticks.map(t => `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(t)}" y2="${Y(t)}" stroke="${GRID}" stroke-width="1"/><text x="${m.l - 6}" y="${Y(t) + 4}" text-anchor="end" font-size="11" fill="${MUTED}">${esc(axisFmt(unit, t))}</text>`).join('');
    const step = W < 420 ? 2 : 1;
    g += xs.map((x, i) => (i % step === 0 || i === xs.length - 1) ? `<text x="${X(x)}" y="${H - 8}" text-anchor="middle" font-size="11" fill="${MUTED}">${x}</text>` : '').join('');
    if (band) {
      const pts = xs.filter(x => band[x]);
      if (pts.length > 1) {
        g += `<path d="M${pts.map(x => `${X(x)},${Y(band[x].hi)}`).join('L')}L${pts.slice().reverse().map(x => `${X(x)},${Y(band[x].lo)}`).join('L')}Z" fill="${BAND}" opacity="0.9"/>`;
        g += `<path d="M${pts.map(x => `${X(x)},${Y(band[x].med)}`).join('L')}" fill="none" stroke="${MEDIAN}" stroke-width="1.5" stroke-dasharray="4 3"/>`;
      }
    }
    events.forEach(e => {
      const ex = evX(e.date);
      if (ex < x0 - 1 || ex > x1) return;
      const px = Math.max(m.l, X(Math.max(ex, x0 - 0.0)));
      g += `<g class="ci-screen-only"><line x1="${px}" x2="${px}" y1="${m.t}" y2="${H - m.b}" stroke="#0f1e33" stroke-width="1" stroke-dasharray="2 3" opacity="0.55"/><circle cx="${px}" cy="${m.t - 10}" r="8" fill="#0f1e33"/><text x="${px}" y="${m.t - 6.5}" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">${e.n}</text></g>`;
    });
    series.forEach(s => {
      const segs = []; let cur = [];
      s.points.forEach(p => { if (p[1] == null) { if (cur.length) segs.push(cur); cur = []; } else cur.push(p); });
      if (cur.length) segs.push(cur);
      segs.forEach(seg => {
        if (seg.length > 1) g += `<path d="M${seg.map(p => `${X(p[0])},${Y(p[1])}`).join('L')}" fill="none" stroke="${s.color}" stroke-width="${s.width || 2}" stroke-linejoin="round" stroke-linecap="round"${s.dashed ? ' stroke-dasharray="5 4"' : ''}${s.faint ? ' opacity="0.45"' : ''}/>`;
      });
      if (!s.faint) s.points.forEach(p => { if (p[1] != null) g += `<circle cx="${X(p[0])}" cy="${Y(p[1])}" r="${s.dot || 4}" fill="${s.color}" stroke="#fff" stroke-width="2"/>`; });
    });
    if (labels.length) {
      const points = labels.flatMap(s => {
        const last = s.points.findLast(p => p[1] != null);
        return last ? [{ x: X(last[0]), y: Y(last[1]), name: s.name, color: s.color }] : [];
      });
      g += pointLabels(points, W - m.r + 10, m.t, H - m.b, labelWidth, 'ci-end-label');
    }
    g += `<line class="xh" x1="0" x2="0" y1="${m.t}" y2="${H - m.b}" stroke="${INK2}" stroke-width="1" visibility="hidden"/>`;
    g += `<rect class="hit" x="${m.l}" y="${m.t}" width="${W - m.l - m.r}" height="${H - m.t - m.b}" fill="transparent"/>`;
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-hidden="true">${g}</svg>`;
    const svg = box.querySelector('svg'), xh = svg.querySelector('.xh'), tip = tipLayer(box);
    fitLabels(svg);
    const near = ev => {
      const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) * (W / r.width);
      let best = xs[0]; xs.forEach(x => { if (Math.abs(X(x) - px) < Math.abs(X(best) - px)) best = x; });
      return best;
    };
    const move = ev => {
      const x = near(ev);
      xh.setAttribute('x1', X(x)); xh.setAttribute('x2', X(x)); xh.setAttribute('visibility', 'visible');
      const rows = series.filter(s => !s.faint || series.length < 3).map(s => { const p = s.points.find(q => q[0] === x); return p && p[1] != null ? `<div><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${s.color};margin-right:6px"></span>${esc(s.name)}: <b>${esc(axisFmtFull(unit, p[1]))}</b></div>` : ''; }).join('');
      const b = band && band[x];
      const r = svg.getBoundingClientRect();
      tip.show(`<b>${x}</b>${rows}${b ? `<div>CT median ${esc(axisFmtFull(unit, b.med))} (middle half ${esc(axisFmtFull(unit, b.lo))} to ${esc(axisFmtFull(unit, b.hi))})</div>` : ''}`,
        X(x) * (r.width / W), (ev.clientY - r.top));
    };
    const hit = svg.querySelector('.hit');
    hit.addEventListener('pointermove', move);
    hit.addEventListener('pointerleave', () => { xh.setAttribute('visibility', 'hidden'); tip.hide(); });
    if (onClickYear) { hit.style.cursor = 'pointer'; hit.addEventListener('click', ev => onClickYear(near(ev))); }
  }
  const axisFmtFull = (unit, v) => unit === 'pct' ? pct(v) : unit === 'hours' ? num(v, 2) : money2(v);

  // rows: [{label, values:[...per group], href?, onClick?}] ; groups: [{label, color}]
  function stackedBars(box, { rows, groups, percent = false, horizontal = true, unitLabel = 'per resident day' }) {
    const W = Math.max(280, box.clientWidth);
    const totals = rows.map(r => r.values.reduce((a, b) => a + (b > 0 ? b : 0), 0));
    const max = percent ? 1 : Math.max(...totals, 1);
    let g = '', H;
    if (horizontal) {
      const narrow = W < 520, bar = 22;
      const labelW = narrow ? 2 : Math.min(220, W * 0.32);
      const right = narrow ? 4 : 88, rowHeight = narrow ? 66 : 36;
      H = 8 + rows.length * rowHeight;
      const X = v => labelW + (W - labelW - right) * v / max;
      rows.forEach((r, i) => {
        const y = 6 + i * rowHeight + (narrow ? 16 : 0);
        g += `<text class="ci-bar-label" data-fit="${narrow ? W - 6 : labelW - 10}" x="${narrow ? 2 : labelW - 8}" y="${narrow ? y - 5 : y + bar / 2 + 4}" text-anchor="${narrow ? 'start' : 'end'}" font-size="12" fill="${INK}">${esc(r.label)}</text>`;
        let acc = 0;
        r.values.forEach((v, j) => {
          if (!(v > 0)) return;
          const w0 = percent ? v / totals[i] : v, x = X(acc), w = Math.max(0, X(acc + w0) - x - 2);
          g += `<rect class="seg" data-r="${i}" data-g="${j}" x="${x}" y="${y}" width="${w}" height="${bar}" rx="${j === r.values.length - 1 ? 3 : 0}" fill="${groups[j].color}"/>`;
          acc += w0;
        });
        g += `<text x="${narrow ? W - 4 : X(acc) + 6}" y="${narrow ? y + bar + 14 : y + bar / 2 + 4}" text-anchor="${narrow ? 'end' : 'start'}" font-size="12" fill="${INK2}">${percent ? '100%' : esc(money2(totals[i]))}</text>`;
      });
    } else {
      const m = { l: 54, r: 10, t: 8, b: 26 }; H = 240;
      const n = rows.length, slot = (W - m.l - m.r) / n, bw = Math.min(24, slot * 0.7);
      const Y = v => m.t + (H - m.t - m.b) * (1 - v / max);
      const ticks = percent ? [0, 0.25, 0.5, 0.75, 1] : niceTicks(0, max);
      g += ticks.map(t => `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(t)}" y2="${Y(t)}" stroke="${GRID}"/><text x="${m.l - 6}" y="${Y(t) + 4}" text-anchor="end" font-size="11" fill="${MUTED}">${percent ? `${Math.round(t * 100)}%` : esc(axisFmt('money', t))}</text>`).join('');
      rows.forEach((r, i) => {
        const cx = m.l + slot * (i + 0.5), x = cx - bw / 2;
        let acc = 0;
        r.values.forEach((v, j) => {
          if (!(v > 0)) return;
          const h0 = percent ? v / totals[i] : v, y1 = Y(acc + h0), y0 = Y(acc);
          g += `<rect class="seg" data-r="${i}" data-g="${j}" x="${x}" y="${y1}" width="${bw}" height="${Math.max(0, y0 - y1 - 2)}" fill="${groups[j].color}"/>`;
          acc += h0;
        });
        g += `<text x="${cx}" y="${H - 8}" text-anchor="middle" font-size="11" fill="${MUTED}">${esc(r.label)}</text>`;
      });
    }
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-hidden="true">${g}</svg>`;
    const svg = box.querySelector('svg'), tip = tipLayer(box);
    fitLabels(svg);
    svg.addEventListener('pointermove', ev => {
      const s = ev.target.closest('.seg');
      if (!s) { tip.hide(); return; }
      const r = rows[+s.dataset.r], j = +s.dataset.g, v = r.values[j], tot = totals[+s.dataset.r];
      const rr = svg.getBoundingClientRect();
      tip.show(`<b>${esc(r.label)}</b><div>${esc(groups[j].label)}: <b>${esc(money2(v))}</b> ${esc(unitLabel)}</div><div>${esc(pct(v / tot))} of the total</div>`, ev.clientX - rr.left, ev.clientY - rr.top);
    });
    svg.addEventListener('pointerleave', () => tip.hide());
  }
  const legend = items => `<div class="ci-legend">${items.map(i => `<span><i class="${i.cls || ''}" style="${i.color ? `background:${i.color}` : ''}"></i>${esc(i.label)}</span>`).join('')}</div>`;
  const GROUP_COLORS = () => D.groups.map((g, i) => ({ label: g.label, color: HEX[i] }));
  function groupValues(h, y) {
    return D.groups.map(g => {
      const parts = g.metrics.map(k => val(h, y, k));
      return parts.some(p => p == null) ? null : parts.reduce((a, b) => a + b, 0);
    });
  }

  // ------------------------------------------------------------------ view 1: one home over time
  const HOME_PANELS = ['expenses', 'nursing', 'admin', 'property', 'management_fees', 'related_parties'];
  let homeCcn = null, homeExtra = '';

  function eventsFor(h) {
    return h.events.map((e, i) => Object.assign({ n: i + 1 }, e));
  }
  function storyFor(h) {
    const ys = homeYears(h).filter(y => usable(h, y));
    if (ys.length < 2) return [];
    const last = ys.at(-1), prev = ys.at(-2), first = ys[0];
    const keys = KEYS.filter(k => isMoney(k) && !['expenses', 'revenue'].includes(k));
    const changes = keys.map(k => {
      const a = val(h, prev, k), b = val(h, last, k);
      return a == null || b == null ? null : { k, a, b, d: b - a, r: relativeChange(a, b) };
    }).filter(c => c && Math.abs(c.d) >= 2 && (c.r == null || Math.abs(c.r) >= 0.1))
      .sort((x, y) => Math.abs(y.d) - Math.abs(x.d)).slice(0, 4);
    const out = [];
    const strong = value => `<strong>${esc(value)}</strong>`;
    const amount = value => strong(money2(value));
    const changeText = (a, b) => {
      const ratio = relativeChange(a, b);
      return `from ${amount(a)} to ${amount(b)} per resident day${ratio == null ? '' : ` (${strong(signed(ratio, pct))})`}`;
    };
    const medianText = k => {
      const a = bandAt(k, prev), b = bandAt(k, last);
      return a && b ? `, while the Connecticut median went from ${amount(a.med)} to ${amount(b.med)}` : '';
    };
    const tot0 = val(h, prev, 'expenses'), tot1 = val(h, last, 'expenses');
    if (tot0 != null && tot1 != null) {
      out.push(`Total costs went ${changeText(tot0, tot1)} between cost years ${prev} and ${last}${medianText('expenses')}.`);
    }
    changes.forEach(c => {
      out.push(`${esc(META[c.k].label)} ${c.d > 0 ? 'rose' : 'fell'} ${changeText(c.a, c.b)} between ${prev} and ${last}${medianText(c.k)}.`);
    });
    if (first !== prev) {
      const a = val(h, first, 'expenses'), b = val(h, last, 'expenses');
      if (a != null && b != null) out.push(`Since cost year ${first}, total costs went ${changeText(a, b)}${real ? ' after inflation' : ' in reported dollars'}.`);
    }
    h.events.filter(e => e.date >= `${Number(prev) - 1}-10-01`).forEach(e => {
      out.push(`${esc(e.label)}, ${esc(fmtDate(e.date))}. The timing alone cannot establish a cause.`);
    });
    return out.slice(0, 5);
  }
  const fmtDate = iso => { const [y, m, d] = iso.split('-').map(Number); return `${['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][m - 1]} ${d}, ${y}`; };

  function headlineTiles(h) {
    const y = homeYears(h).filter(year => usable(h, year)).at(-1);
    if (!y) return '<p class="subtle ci-screen-only">No cost year passed every check for this home.</p>';
    const costs = val(h, y, 'expenses'), ct = bandAt('expenses', y)?.med;
    const gap = costs == null || ct == null ? null : costs - ct;
    const gapPct = relativeChange(ct, costs), related = val(h, y, 'related_parties');
    const tiles = [
      ['Total costs per resident day', money2(costs)],
      ['Gap to Connecticut median', gap == null ? '' : `${signed(gap, money2)}${gapPct == null ? '' : ` (${signed(gapPct, pct)})`}`],
      ['Direct care share of costs', pct(val(h, y, 'direct_share'))],
      ['Related-party payments as a share of costs', related == null || !costs ? '' : pct(related / costs)],
    ];
    return `<section class="ci-headlines ci-screen-only" aria-label="Latest checked cost year">
      <p class="subtle">Latest cost year that passed every check: ${y}${real ? `, in ${D.cpi.base_year} dollars` : ''}.</p>
      <dl class="ci-tiles">${tiles.map(([label, value]) => `<div class="ci-tile"><dt>${esc(label)}</dt><dd>${esc(value || 'Unavailable')}</dd></div>`).join('')}</dl>
    </section>`;
  }

  function metricDisclosure(definition) {
    return `<details class="ci-definition ci-screen-only"><summary>What is this?</summary><p class="subtle">${esc(definition)}</p></details>`;
  }

  function renderHome() {
    const out = document.getElementById('home-out');
    const h = HOMES[homeCcn];
    if (!h) { out.innerHTML = '<p class="subtle">Search for a nursing home to see its costs over time against the Connecticut middle half and median, with ownership, management and administrator changes marked.</p>'; return; }
    const evs = eventsFor(h);
    const keys = HOME_PANELS.concat(homeExtra && !HOME_PANELS.includes(homeExtra) ? [homeExtra] : []);
    const story = storyFor(h);
    out.innerHTML = `
      <h2 id="home-title" tabindex="-1" style="margin-bottom:2px">${esc(title(h.name))}</h2>
      <p class="subtle">${esc([h.city, h.county ? `${h.county} planning region` : '', h.beds ? `${h.beds} certified beds` : '', h.ownership, h.affiliation ? `CMS affiliated entity: ${title(h.affiliation)}` : ''].filter(Boolean).join(' · '))} · CCN ${h.ccn} · <a href="${COST_PAGE}?ccn=${h.ccn}">Year-by-year detail on Cost Reports</a></p>
      ${headlineTiles(h)}
      ${story.length ? `<div class="ci-screen-only"><h3>What changed</h3><ul class="ci-story">${story.map(item => `<li>${item}</li>`).join('')}</ul></div>` : ''}
      <h3>Costs over time ${real ? `<span class="ci-flag">in ${D.cpi.base_year} dollars</span>` : ''}</h3>
      ${legend([{ label: title(h.name), color: HEX[0], cls: 'line' }, { label: 'Connecticut middle half of homes', cls: 'band' }, { label: 'Connecticut median', cls: 'dash' }])}
      <div class="ci-grid">${keys.map(k => `<div class="ci-card"><h4>${esc(META[k].label)}</h4><p class="sub">${META[k].unit === 'money' ? 'Per resident day' : esc(META[k].definition)}</p><div class="ci-chart" data-k="${k}"></div>${metricDisclosure(META[k].definition)}</div>`).join('')}</div>
      <p class="subtle">Each chart has its own scale.</p>
      <div class="ci-screen-only">${evs.length ? `<h3>Ownership, management and administrator changes</h3><ol class="ci-events">${evs.map(e => `<li><b>${e.n}</b>${esc(fmtDate(e.date))}: ${esc(e.label)}</li>`).join('')}</ol>` : '<p class="subtle">No ownership, management-of-record or administrator changes recorded in these years.</p>'}</div>
      <h3>Share of every dollar</h3>
      <p class="subtle">Each year's costs split into eight groups, as a share of the total. Hover a segment for its amount per resident day.</p>
      ${legend(GROUP_COLORS())}
      <div class="ci-chart" id="home-share"></div>
      ${metricDisclosure(D.method.values)}
      <details class="ci-more"><summary>Show these figures as a table</summary>${homeTable(h, keys)}</details>`;
    out.querySelectorAll('.ci-chart[data-k]').forEach(box => {
      const k = box.dataset.k, ys = D.years;
      const band = {}; ys.forEach(y => { band[y] = bandAt(k, y); });
      lineChart(box, { unit: META[k].unit, band, events: evs, series: [{ name: title(h.name), color: HEX[0], points: ys.map(y => [y, usable(h, y) || h.years[y] ? val(h, y, k) : null]) }],
        onClickYear: y => { global.location.href = `${COST_PAGE}?ccn=${h.ccn}&year=${y}`; } });
    });
    const ys = homeYears(h);
    const rows = ys.map(y => ({ label: String(y), values: groupValues(h, y) })).filter(r => r.values.every(v => v != null));
    const box = document.getElementById('home-share');
    if (rows.length) {
      stackedBars(box, { rows, groups: GROUP_COLORS(), percent: true, horizontal: false });
      const missing = ys.filter(y => !rows.some(r => r.label === String(y)));
      if (missing.length) box.insertAdjacentHTML('beforeend', `<p class="subtle">Not shown: ${esc(missing.join(', '))} (the report's categories did not add up to its printed total, or a figure was withheld).</p>`);
    } else box.innerHTML = '<p class="subtle">No year adds up for this home.</p>';
  }
  function homeTable(h, keys) {
    const ys = homeYears(h);
    return `<div class="table-scroll"><table><caption>${esc(title(h.name))}, per resident day${real ? ` (${D.cpi.base_year} dollars)` : ''}</caption>
      <thead><tr><th scope="col">Figure</th>${ys.map(y => `<th scope="col" class="num">${y}${h.years[y].part ? '*' : ''}</th>`).join('')}</tr></thead>
      <tbody>${keys.concat(KEYS.filter(k => !keys.includes(k))).map(k => `<tr><th scope="row">${esc(META[k].label)}</th>${ys.map(y => `<td class="num">${esc(fmt(k, val(h, y, k)))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
      <p class="subtle">* part-year filing.</p>`;
  }

  // ------------------------------------------------------------------ view 2: compare homes
  let cmp = [];
  function renderCompare() {
    const out = document.getElementById('cmp-out'), k = document.getElementById('cmp-metric').value, y = document.getElementById('cmp-year').value;
    document.getElementById('cmp-chips').innerHTML = cmp.map((c, i) => `<span class="chip"><i style="background:${HEX[i]}"></i>${esc(title(HOMES[c].name))}<button type="button" data-rm="${c}" aria-label="Remove ${esc(title(HOMES[c].name))}">×</button></span>`).join('');
    syncUrl();
    if (!cmp.length) { out.innerHTML = '<p class="subtle">Add homes with the search box. Tip: open a peer group and use "Compare these homes".</p>'; return; }
    const hs = cmp.map(c => HOMES[c]);
    out.innerHTML = `
      <div class="ci-card"><h3>${esc(META[k].label)} over time</h3><p class="sub">${esc(META[k].definition)}${real && isMoney(k) ? ` In ${D.cpi.base_year} dollars.` : ''}</p>
        ${legend(hs.map((h, i) => ({ label: title(h.name), color: HEX[i], cls: 'line' })).concat([{ label: 'Connecticut median', cls: 'dash' }]))}
        <div class="ci-chart" id="cmp-line"></div></div>
      <div class="ci-card" style="margin-top:14px"><h3>Where each home's costs go, cost year ${y}</h3><p class="sub">Per resident day${real ? ` (${D.cpi.base_year} dollars)` : ''}. Hover a segment for its amount.</p>
        ${legend(GROUP_COLORS())}<div class="ci-chart" id="cmp-bars"></div></div>
      ${compareTable(hs, y)}`;
    const band = {}; D.years.forEach(yy => { const b = bandAt(k, yy); band[yy] = b ? { lo: b.med, med: b.med, hi: b.med } : null; });
    lineChart(document.getElementById('cmp-line'), { unit: META[k].unit, height: 260, series: hs.map((h, i) => ({ name: title(h.name), color: HEX[i], endLabel: hs.length <= 4, points: D.years.map(yy => [yy, val(h, yy, k)]) }))
      .concat([{ name: 'Connecticut median', color: MEDIAN, dashed: true, width: 1.5, dot: 0, points: D.years.map(yy => [yy, band[yy] ? band[yy].med : null]) }]) });
    const rows = hs.map(h => ({ label: title(h.name), values: groupValues(h, y) })).filter(r => r.values.every(v => v != null));
    const bars = document.getElementById('cmp-bars');
    if (rows.length) stackedBars(bars, { rows, groups: GROUP_COLORS() }); else bars.innerHTML = `<p class="subtle">None of these homes has a breakdown that adds up for ${y}.</p>`;
  }
  function compareTable(hs, y) {
    const keys = KEYS;
    return `<details class="ci-more" open><summary>All figures for ${y}, with the gap to the Connecticut median</summary><div class="table-scroll" tabindex="0" role="region" aria-label="All figures for ${y}"><table class="ci-sticky ci-compare-table"><caption>Cost year ${y}${real ? `, ${D.cpi.base_year} dollars` : ''}</caption>
      <thead><tr><th scope="col">Figure</th>${hs.map(h => `<th scope="col" class="num">${esc(title(h.name))}</th>`).join('')}<th scope="col" class="num">CT median</th></tr></thead>
      <tbody>${keys.map(k => { const b = bandAt(k, y); return `<tr><th scope="row">${esc(META[k].label)}</th>${hs.map(h => { const v = val(h, y, k); const gap = v != null && b ? v - b.med : null;
        return `<td class="num" data-label="${esc(title(h.name))}">${esc(fmt(k, v))}${gap != null ? `<div class="subtle">${gap >= 0 ? '+' : ''}${esc(fmt(k, gap))}</div>` : ''}</td>`; }).join('')}<td class="num subtle" data-label="CT median">${esc(fmt(k, b && b.med))}</td></tr>`; }).join('')}</tbody></table></div></details>`;
  }

  // ------------------------------------------------------------------ peer groups
  const PEER_TYPES = [
    ['management', 'Management company of record'], ['affiliation', 'CMS affiliated entity (chain)'], ['county', 'Planning region'],
    ['size', 'Size (certified beds)'], ['ownership', 'Ownership type'], ['medicaid_band', 'Medicaid share of days'],
  ];
  function peerGroups(type) {
    const g = {};
    Object.values(HOMES).forEach(h => {
      const keys = type === 'management' ? h.management : (h[type] ? [h[type]] : []);
      keys.forEach(k => { (g[k] = g[k] || []).push(h.ccn); });
    });
    const name = k => type === 'management' ? title((D.management_companies[k] || {}).name || k) : (type === 'affiliation' ? title(k) : k);
    return Object.entries(g).map(([k, ccns]) => ({ key: k, name: name(k), ccns })).filter(x => x.ccns.length >= 2).sort((a, b) => b.ccns.length - a.ccns.length || a.name.localeCompare(b.name));
  }
  function fillGroupSelect(typeSel, groupSel, chosen) {
    const gs = peerGroups(typeSel.value);
    groupSel.innerHTML = gs.map(g => `<option value="${esc(g.key)}">${esc(g.name)} (${g.ccns.length} homes)</option>`).join('');
    if (chosen && gs.some(g => g.key === chosen)) groupSel.value = chosen;
    return gs;
  }
  function renderPeers() {
    const type = document.getElementById('peer-type').value, key = document.getElementById('peer-group').value;
    const k = document.getElementById('peer-metric').value, y = document.getElementById('peer-year').value;
    const grp = peerGroups(type).find(g => g.key === key);
    const out = document.getElementById('peer-out');
    syncUrl();
    if (!grp) { out.innerHTML = '<p class="subtle">No group selected.</p>'; return; }
    const hs = grp.ccns.map(c => HOMES[c]);
    // the group median is drawn only for years with at least three homes reporting the figure
    const comparable = yy => hs.filter(h => usable(h, yy) && !h.years[yy].part).map(h => val(h, yy, k)).filter(v => v != null);
    const gmed = yy => { const values = comparable(yy); return values.length >= 3 ? median(values) : null; };
    const groupMedian = gmed(y), ctMedian = bandAt(k, y)?.med;
    const ct = yy => { const b = bandAt(k, yy); return b ? b.med : null; };
    const rows = hs.map(h => ({ h, v: val(h, y, k), part: h.years[y] && h.years[y].part })).filter(r => r.v != null).sort((a, b) => b.v - a.v);
    out.innerHTML = `
      <div class="ci-card"><h3>${esc(grp.name)}: ${esc(META[k].label)}</h3><p class="sub">Each home in the group as a thin line, the group's median in blue (years with at least three homes reporting) and the Connecticut median dashed${real && isMoney(k) ? `; ${D.cpi.base_year} dollars` : ''}. ${esc(META[k].definition)}</p>
        ${legend([{ label: 'Group median', color: HEX[0], cls: 'line' }, { label: 'Each home in the group', color: OTHER, cls: 'line' }, { label: 'Connecticut median', cls: 'dash' }])}
        <div class="ci-chart" id="peer-line"></div></div>
      <div class="table-scroll"><table class="stack"><caption>${esc(grp.name)}, cost year ${y}: ${esc(META[k].label)} (Connecticut median ${esc(fmt(k, ct(y)))})</caption>
        <thead><tr><th scope="col">Home</th><th scope="col" class="num">${esc(META[k].label)}</th><th scope="col" class="num">Gap to CT median</th><th scope="col">Town</th></tr></thead>
        <tbody>${rows.map(r => `<tr><td data-label="Home"><button class="linkish" type="button" data-open="${r.h.ccn}">${esc(title(r.h.name))}</button><span class="ci-print-only">${esc(title(r.h.name))}</span>${r.part ? ' <span class="ci-flag">part year</span>' : ''}</td><td class="num" data-label="Value">${esc(fmt(k, r.v))}</td><td class="num" data-label="Gap">${ct(y) != null ? esc((r.v - ct(y) >= 0 ? '+' : '') + fmt(k, r.v - ct(y))) : ''}</td><td data-label="Town">${esc(r.h.city || '')}</td></tr>`).join('')
          || `<tr><td colspan="4" class="subtle">No home in this group has this figure for ${y}.</td></tr>`}
          <tr class="ci-peer-summary"><td data-label="Home"><strong>Group median</strong></td>
            <td class="num" data-label="Value">${groupMedian == null ? 'Unavailable' : esc(fmt(k, groupMedian))}</td>
            <td class="num" data-label="Gap">${groupMedian == null || ctMedian == null ? '' : esc(signed(groupMedian - ctMedian, v => fmt(k, v)))}</td>
            <td data-label="Coverage">${rows.length} homes reporting in ${y} (${comparable(y).length} eligible for median)</td></tr>
        </tbody></table></div>
      <div class="report-actions no-print"><button type="button" class="action-button secondary" id="peer-compare">Compare these homes side by side${hs.length > 5 ? ' (first five by this figure)' : ''}</button></div>`;
    lineChart(document.getElementById('peer-line'), { unit: META[k].unit, height: 280,
      series: hs.map(h => ({ name: title(h.name), color: OTHER, faint: true, width: 1.5, points: D.years.map(yy => [yy, val(h, yy, k)]) }))
        .concat([{ name: 'Group median', color: HEX[0], width: 3, points: D.years.map(yy => [yy, gmed(yy)]) },
          { name: 'Connecticut median', color: MEDIAN, dashed: true, width: 1.5, dot: 0, points: D.years.map(yy => [yy, ct(yy)]) }]) });
    document.getElementById('peer-compare').addEventListener('click', () => {
      cmp = (rows.length ? rows.map(r => r.h.ccn) : grp.ccns).slice(0, 5);
      document.getElementById('cmp-metric').value = k; document.getElementById('cmp-year').value = y;
      show('compare');
    });
  }

  // ------------------------------------------------------------------ pivot
  let pvSort = { col: null, dir: -1 };
  function pivotData() {
    const rowsBy = document.getElementById('pv-rows').value, k = document.getElementById('pv-metric').value, agg = document.getElementById('pv-agg').value;
    const f = norm(document.getElementById('pv-filter').value);
    let rows;
    if (rowsBy === 'home') {
      rows = Object.values(HOMES).map(h => ({ label: title(h.name), sub: h.city, ccn: h.ccn, cells: D.years.map(y => usable(h, y) ? val(h, y, k) : null), n: D.years.map(y => usable(h, y) ? 1 : 0) }));
    } else {
      rows = peerGroups(rowsBy).map(g => {
        const hs = g.ccns.map(c => HOMES[c]);
        const cells = D.years.map(y => { const v = hs.filter(h => usable(h, y) && !h.years[y].part).map(h => val(h, y, k)).filter(x => x != null); return v.length ? (agg === 'mean' ? mean(v) : median(v)) : null; });
        const n = D.years.map(y => hs.filter(h => usable(h, y) && !h.years[y].part && val(h, y, k) != null).length);
        return { label: g.name, sub: `${g.ccns.length} homes`, cells, n };
      });
    }
    rows.push({ label: 'Connecticut (all homes)', sub: 'median', cells: D.years.map(y => { const b = bandAt(k, y); return b ? b.med : null; }), n: D.years.map(y => { const b = bandAt(k, y); return b ? b.n : 0; }), total: true });
    rows = rows.filter(r => r.total || !f || norm(`${r.label} ${r.sub || ''}`).includes(f)).filter(r => r.cells.some(c => c != null));
    return { rows, k, rowsBy, agg };
  }
  function pivotChanges(row) {
    const latest = row.cells.at(-1);
    return [relativeChange(row.cells.at(-2), latest), relativeChange(row.cells[D.years.indexOf(2019)], latest)];
  }

  function renderPivot() {
    const out = document.getElementById('pv-out');
    const previous = out.querySelector('.table-scroll');
    const narrow = global.matchMedia('(max-width: 719px)').matches;
    const scrollLeft = previous && previous.clientWidth && (previous.dataset.narrow === String(narrow))
      ? previous.scrollLeft : null;
    const { rows, k, rowsBy, agg } = pivotData();
    syncUrl();
    const body = rows.filter(r => !r.total), total = rows.find(r => r.total);
    if (pvSort.col === 'label') body.sort((a, b) => pvSort.dir * a.label.localeCompare(b.label));
    else if (pvSort.col != null) {
      const value = row => row.cells.concat(pivotChanges(row))[pvSort.col];
      body.sort((a, b) => {
        const av = value(a), bv = value(b);
        if (av == null) return bv == null ? 0 : 1;
        if (bv == null) return -1;
        return pvSort.dir * (av - bv);
      });
    }
    const all = body.flatMap(r => r.cells).filter(v => v != null).sort((a, b) => a - b);
    const lo = all[Math.floor(all.length * 0.05)] ?? 0, hi = all[Math.floor(all.length * 0.95)] ?? 1;
    // sequential single hue (blue 100 -> 600); text flips to white on the darkest steps
    const ramp = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab', '#184f95'];
    const shade = v => { if (v == null) return ''; const t = Math.max(0, Math.min(1, (v - lo) / ((hi - lo) || 1))); const i = Math.round(t * (ramp.length - 1)); return `background:${ramp[i]};${i >= 6 ? 'color:#fff;' : ''}`; };
    const few = (r, i) => !r.total && rowsBy !== 'home' && r.n[i] > 0 && r.n[i] < 3;
    const cell = (r, v, i) => `<td class="num" style="${r.total || few(r, i) ? '' : shade(v)}" title="${r.n[i]} home${r.n[i] === 1 ? '' : 's'}">${esc(fmt(k, v))}${few(r, i) && v != null ? '<sup>†</sup>' : ''}</td>`;
    const changeCells = row => pivotChanges(row).map(v => `<td class="num">${esc(signed(v, pct))}</td>`).join('');
    out.innerHTML = `<p class="subtle">${body.length} rows. ${rowsBy === 'home' ? 'Each home\'s own figure' : `${agg === 'mean' ? 'Average' : 'Median'} of the homes in each group (full-year filings that passed every check)`} for ${esc(META[k].label.toLowerCase())}${real && isMoney(k) ? `, in ${D.cpi.base_year} dollars` : ''}. Darker blue = higher. Select a heading to sort; hover a cell for how many homes it covers.</p>
      <div class="table-scroll" tabindex="0" role="region" aria-label="Pivot results" data-narrow="${narrow}"><table class="pivot ci-sticky"><caption>${esc(META[k].label)} by ${esc((PEER_TYPES.find(p => p[0] === rowsBy) || ['', 'home'])[1].toLowerCase())} and cost year</caption>
      <thead><tr><th scope="col"><button type="button" data-sort="label">${rowsBy === 'home' ? 'Home' : 'Group'}</button><span class="ci-print-only">${rowsBy === 'home' ? 'Home' : 'Group'}</span></th>${D.years.map((y, i) => `<th scope="col" class="num"><button type="button" data-sort="${i}"${i === D.years.length - 1 ? ' data-latest' : ''}>${y}</button><span class="ci-print-only">${y}</span></th>`).join('')}
        <th scope="col" class="num"><button type="button" data-sort="${D.years.length}" title="${D.years.at(-2)} to ${D.years.at(-1)}">Latest year change (%)</button><span class="ci-print-only">Latest year change (%)</span></th>
        <th scope="col" class="num"><button type="button" data-sort="${D.years.length + 1}" title="2019 to ${D.years.at(-1)}">Change since 2019 (%)</button><span class="ci-print-only">Change since 2019 (%)</span></th></tr></thead>
      <tbody>${body.map(r => `<tr><th scope="row">${r.ccn ? `<button class="linkish" type="button" data-open="${r.ccn}">${esc(r.label)}</button><span class="ci-print-only">${esc(r.label)}</span>` : esc(r.label)} <span class="subtle">${esc(r.sub || '')}</span></th>${r.cells.map((v, i) => cell(r, v, i)).join('')}${changeCells(r)}</tr>`).join('')}
      ${total ? `<tr style="font-weight:800"><th scope="row">${esc(total.label)} <span class="subtle">median</span></th>${total.cells.map((v, i) => cell(total, v, i)).join('')}${changeCells(total)}</tr>` : ''}</tbody></table></div>
      ${rowsBy !== 'home' ? '<p class="subtle">† Fewer than three homes in the group reported this figure that year; not shaded, read with care.</p>' : ''}
      <p class="subtle">Change compares ${D.years.at(-1)} with ${D.years.at(-2)} or 2019. Change is relative to the magnitude of the starting value. Blank means a figure is missing or the starting value is zero.</p>`;
    const scroller = out.querySelector('.table-scroll');
    if (scrollLeft != null) scroller.scrollLeft = scrollLeft;
    else if (narrow) {
      const latest = out.querySelector('[data-latest]').closest('th');
      const first = out.querySelector('thead th');
      scroller.scrollLeft = latest.getBoundingClientRect().left - first.getBoundingClientRect().right;
    }
  }
  function pivotCsv() {
    const { rows, k } = pivotData();
    const q = v => { const t = v == null ? '' : String(v); return /[",\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t; };
    const header = ['row', 'detail', ...D.years, 'latest_year_change_pct', 'change_since_2019_pct'];
    const lines = [header.join(','), ...rows.map(r => [
      r.label, r.sub || '', ...r.cells.map(v => v == null ? '' : (+v).toFixed(4)),
      ...pivotChanges(r).map(v => signed(v, pct)),
    ].map(q).join(','))];
    const blob = new Blob([lines.join('\n') + '\n'], { type: 'text/csv' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `ct-cost-reports-pivot-${k}${real ? '-constant-dollars' : ''}.csv`;
    document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
  }

  // ------------------------------------------------------------------ scatter: money vs care
  function renderScatter() {
    const kx = document.getElementById('sc-x').value, ky = document.getElementById('sc-y').value, y = document.getElementById('sc-year').value;
    const type = document.getElementById('sc-type').value, gkey = document.getElementById('sc-group').value;
    const out = document.getElementById('sc-out');
    syncUrl();
    const grp = type ? peerGroups(type).find(g => g.key === gkey) : null;
    const inG = new Set(grp ? grp.ccns : []);
    const pts = Object.values(HOMES).filter(h => usable(h, y)).map(h => ({ h, x: val(h, y, kx), y: val(h, y, ky), g: inG.has(h.ccn) })).filter(p => p.x != null && p.y != null);
    const mx = META[kx], my = META[ky];
    out.innerHTML = `<div class="ci-card"><h3>${esc(my.label)} against ${esc(mx.label.toLowerCase())}, cost year ${y}</h3>
      <p class="sub">One dot per home (${pts.length} homes). The gray lines are the Connecticut medians, splitting homes into four quarters. Position shows how a home spends, not how good its care is. Select a dot to open that home.</p>
      ${grp ? legend([{ label: `${grp.name}`, color: HEX[0] }, { label: 'Other Connecticut homes', color: OTHER }]) : ''}
      <div class="ci-chart" id="sc-chart"></div></div>
      <details class="ci-more"><summary>Show these figures as a table</summary><div class="table-scroll"><table class="stack"><caption>Cost year ${y}</caption><thead><tr><th scope="col">Home</th><th scope="col" class="num">${esc(mx.label)}</th><th scope="col" class="num">${esc(my.label)}</th></tr></thead>
      <tbody>${pts.sort((a, b) => a.h.name.localeCompare(b.h.name)).map(p => `<tr><td data-label="Home">${esc(title(p.h.name))}${p.g ? ' <span class="ci-flag">in group</span>' : ''}</td><td class="num" data-label="${esc(mx.label)}">${esc(fmt(kx, p.x))}</td><td class="num" data-label="${esc(my.label)}">${esc(fmt(ky, p.y))}</td></tr>`).join('')}</tbody></table></div></details>`;
    const box = document.getElementById('sc-chart');
    if (!pts.length) { box.innerHTML = '<p class="subtle">No homes have both figures for this year.</p>'; return; }
    const W = Math.max(280, box.clientWidth), H = Math.min(460, Math.max(300, W * 0.62));
    const highlighted = pts.filter(p => p.g);
    const showLabels = highlighted.length > 0 && highlighted.length <= 8;
    const labelWidth = Math.min(146, Math.round(W * 0.31));
    const m = { l: 58, r: showLabels ? labelWidth + 14 : 14, t: 10, b: 40 };
    const xsV = pts.map(p => p.x), ysV = pts.map(p => p.y);
    const tx = niceTicks(Math.min(...xsV), Math.max(...xsV), Math.max(2, Math.floor((W - m.l - m.r) / 64))), ty = niceTicks(Math.min(...ysV), Math.max(...ysV));
    const xl = Math.min(tx[0], ...xsV), xh = Math.max(tx[tx.length - 1], ...xsV), yl = Math.min(ty[0], ...ysV), yh = Math.max(ty[ty.length - 1], ...ysV);
    const X = v => m.l + (W - m.l - m.r) * (v - xl) / ((xh - xl) || 1), Y = v => m.t + (H - m.t - m.b) * (1 - (v - yl) / ((yh - yl) || 1));
    let g = '';
    g += ty.map(t => `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(t)}" y2="${Y(t)}" stroke="${GRID}"/><text x="${m.l - 6}" y="${Y(t) + 4}" text-anchor="end" font-size="11" fill="${MUTED}">${esc(axisFmt(my.unit, t))}</text>`).join('');
    g += tx.map(t => `<text x="${X(t)}" y="${H - m.b + 16}" text-anchor="middle" font-size="11" fill="${MUTED}">${esc(axisFmt(mx.unit, t))}</text>`).join('');
    const mxv = median(xsV), myv = median(ysV);
    g += `<line x1="${X(mxv)}" x2="${X(mxv)}" y1="${m.t}" y2="${H - m.b}" stroke="${MEDIAN}" stroke-dasharray="4 3"/><line x1="${m.l}" x2="${W - m.r}" y1="${Y(myv)}" y2="${Y(myv)}" stroke="${MEDIAN}" stroke-dasharray="4 3"/>`;
    g += `<text data-fit="${W - 12}" x="${W - 6}" y="${H - 6}" text-anchor="end" font-size="11" fill="${INK2}">${esc(mx.label)} →</text><text data-fit="${W - m.l - 12}" x="${m.l}" y="${m.t + 12}" font-size="11" fill="${INK2}" dx="6">↑ ${esc(my.label)}</text>`;
    pts.sort((a, b) => a.g - b.g).forEach((p, i) => { g += `<circle class="pt" data-i="${i}" cx="${X(p.x)}" cy="${Y(p.y)}" r="${p.g ? 6 : 4.5}" fill="${p.g ? HEX[0] : OTHER}" stroke="#fff" stroke-width="2" style="cursor:pointer"/>`; });
    if (showLabels) {
      const points = highlighted.map(p => ({ x: X(p.x), y: Y(p.y), name: title(p.h.name), color: HEX[0] }));
      g += pointLabels(points, W - m.r + 10, m.t, H - m.b, labelWidth, 'ci-dot-label');
    }
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-hidden="true">${g}</svg>`;
    const svg = box.querySelector('svg'), tip = tipLayer(box);
    fitLabels(svg);
    svg.addEventListener('pointermove', ev => {
      const c = ev.target.closest('.pt'); if (!c) { tip.hide(); return; }
      const p = pts[+c.dataset.i], r = svg.getBoundingClientRect();
      tip.show(`<b>${esc(title(p.h.name))}</b><div>${esc(mx.label)}: <b>${esc(fmt(kx, p.x))}</b></div><div>${esc(my.label)}: <b>${esc(fmt(ky, p.y))}</b></div><div class="subtle">Select to open</div>`, ev.clientX - r.left, ev.clientY - r.top);
    });
    svg.addEventListener('pointerleave', () => tip.hide());
    svg.addEventListener('click', ev => { const c = ev.target.closest('.pt'); if (c) openHome(pts[+c.dataset.i].h.ccn); });
  }

  // ------------------------------------------------------------------ money flow (Sankey)
  let flowCcn = null;
  async function renderFlow() {
    const out = document.getElementById('flow-out'), y = document.getElementById('flow-year').value;
    syncUrl();
    const h = HOMES[flowCcn];
    if (!h) { out.innerHTML = '<p class="subtle">Search for a nursing home to see where its revenue came from and where its costs went in one cost year, including what it reported paying to related parties.</p>'; return; }
    out.innerHTML = '<p class="subtle">Loading this home\'s report.</p>';
    let det = detailCache[h.ccn];
    try { if (!det) { const r = await fetch(DETAIL(h.ccn)); if (!r.ok) throw new Error(`HTTP ${r.status}`); det = detailCache[h.ccn] = await r.json(); } }
    catch (e) { out.innerHTML = `<p class="notice error">The report for this home could not be loaded (${esc(e.message)}).</p>`; return; }
    const yr = det.cost_years.find(c => String(c.cost_year) === String(y));
    const cb = yr && yr.cost_breakdown;
    if (!yr || !cb || !cb.adds_up) { out.innerHTML = `<h2>${esc(title(h.name))}</h2><p class="subtle">No breakdown that adds up for cost year ${y}. Available years: ${esc(homeYears(h).filter(yy => usable(h, yy)).join(', '))}.</p>`; return; }
    const f = factor(y), cats = cb.categories, days = yr.resident_days.resident_days_total || yr.resident_days.days_total_care;
    const costs = D.groups.map((g, i) => ({ label: g.label, color: HEX[i], v: g.metrics.reduce((a, k) => a + (cats[k] ? cats[k].amount : 0), 0) * f }));
    const totalCost = cb.printed_total * f;
    const rv = yr.revenue || {}, revTotal = (rv.rev_total || 0) * f;
    let revs = [['Medicaid (Connecticut)', rv.rev_medicaid_ct], ['Medicare', rv.rev_medicare], ['Private pay and other residents', rv.rev_private]].map(([l, v]) => ({ label: l, v: (v || 0) * f }));
    const rest = revTotal - revs.reduce((a, r) => a + r.v, 0);
    revs = (rest >= 0 && revs.every(r => r.v >= 0)) ? revs.concat([{ label: 'Other revenue and adjustments', v: rest }]) : [{ label: 'Nursing-home revenue', v: revTotal }];
    revs = revs.filter(r => r.v > 0);
    const gap = revTotal - totalCost;
    const rp = (yr.related_parties || []).filter(p => (p.category || '') !== 'loans / interest / receivables' && p.cost_reported);
    const rpLabel = c => (!c || c === 'other') ? 'other or not classified (see the report)' : c;
    const rpBy = {}; rp.forEach(p => { const c = rpLabel(p.category); rpBy[c] = (rpBy[c] || 0) + p.cost_reported * f; });
    out.innerHTML = `<h2 style="margin-bottom:2px">${esc(title(h.name))}, cost year ${y}</h2>
      <p class="subtle">${esc(num(days))} resident days. Revenue ${esc(money(revTotal))}, costs ${esc(money(totalCost))}: ${gap >= 0 ? `a surplus of ${esc(money(gap))}` : `a shortfall of ${esc(money(-gap))}`} (${esc(pct(gap / (revTotal || 1)))} of revenue)${real ? `, in ${D.cpi.base_year} dollars` : ''}. Hover a band for its amount. <a href="${COST_PAGE}?ccn=${h.ccn}&year=${y}">Full report detail</a></p>
      <div class="ci-chart" id="flow-chart"></div>
      ${legend(costs.map(c => ({ label: c.label, color: c.color })))}
      <h3>Paid to related parties</h3>
      ${rp.length ? `<p>The home reported ${esc(money(rp.reduce((a, p) => a + p.cost_reported * f, 0)))} in costs paid to related parties (companies or people connected to its owners or operators), ${esc(pct(rp.reduce((a, p) => a + p.cost_reported * f, 0) / totalCost))} of its costs. These payments are inside the cost groups above, not in addition to them.</p>
        <div class="table-scroll"><table class="stack"><caption>Related-party costs by type (page 4)</caption><thead><tr><th scope="col">Type</th><th scope="col" class="num">Amount</th><th scope="col" class="num">Per resident day</th></tr></thead>
        <tbody>${Object.entries(rpBy).sort((a, b) => b[1] - a[1]).map(([c, v]) => `<tr><td data-label="Type">${esc(c)}</td><td class="num" data-label="Amount">${esc(money(v))}</td><td class="num" data-label="Per day">${esc(money2(v / days))}</td></tr>`).join('')}</tbody></table></div>`
        : '<p class="subtle">No related-party costs reported on page 4 for this year.</p>'}
      <details class="ci-more"><summary>Show the flow as a table</summary><div class="table-scroll"><table class="stack"><caption>Revenue and costs, cost year ${y}</caption><thead><tr><th scope="col">Line</th><th scope="col" class="num">Amount</th><th scope="col" class="num">Per resident day</th></tr></thead>
        <tbody>${revs.map(r => `<tr><td data-label="Line">Revenue: ${esc(r.label)}</td><td class="num" data-label="Amount">${esc(money(r.v))}</td><td class="num" data-label="Per day">${esc(money2(r.v / days))}</td></tr>`).join('')}
        ${costs.map(c => `<tr><td data-label="Line">Cost: ${esc(c.label)}</td><td class="num" data-label="Amount">${esc(money(c.v))}</td><td class="num" data-label="Per day">${esc(money2(c.v / days))}</td></tr>`).join('')}
        <tr><td data-label="Line">${gap >= 0 ? 'Surplus' : 'Shortfall'}</td><td class="num" data-label="Amount">${esc(money(Math.abs(gap)))}</td><td class="num" data-label="Per day">${esc(money2(Math.abs(gap) / days))}</td></tr></tbody></table></div></details>`;
    sankey(document.getElementById('flow-chart'), revs, costs, gap, days);
  }
  function sankey(box, revs, costs, gap, days) {
    const W = Math.max(300, box.clientWidth), narrow = W < 560;
    const left = revs.concat(gap < 0 ? [{ label: 'Shortfall (costs above revenue)', v: -gap, color: '#9aa4b1' }] : []);
    const right = costs.filter(c => c.v > 0).concat(gap > 0 ? [{ label: 'Surplus', v: gap, color: '#9aa4b1' }] : []);
    const total = Math.max(left.reduce((a, b) => a + b.v, 0), right.reduce((a, b) => a + b.v, 0));
    const pad = 6, H = Math.max(340, 34 * Math.max(left.length, right.length) + 60), m = { t: 10, b: 10 };
    const colW = 14, lx = narrow ? 4 : Math.min(200, W * 0.26), rx = W - (narrow ? 18 : Math.min(240, W * 0.3)), cx = (lx + rx) / 2;
    const scale = (H - m.t - m.b - pad * (Math.max(left.length, right.length) - 1)) / total;
    const place = arr => { let y = m.t; return arr.map(n => { const h = Math.max(2, n.v * scale); const o = Object.assign({}, n, { y, h }); y += h + pad; return o; }); };
    const L = place(left), R = place(right);
    const midH = total * scale, midY = (H - midH) / 2;
    const revFill = ['#184f95', '#2a78d6', '#6da7ec', '#9ec5f4'];
    let g = '', yIn = midY, yOut = midY;
    const band = (x0, y0, h0, x1, y1, h1, fill, i, side) => `<path class="lk" data-side="${side}" data-i="${i}" d="M${x0},${y0} C${(x0 + x1) / 2},${y0} ${(x0 + x1) / 2},${y1} ${x1},${y1} L${x1},${y1 + h1} C${(x0 + x1) / 2},${y1 + h1} ${(x0 + x1) / 2},${y0 + h0} ${x0},${y0 + h0} Z" fill="${fill}" opacity="0.35"/>`;
    L.forEach((n, i) => { const fill = n.color || revFill[i % revFill.length]; g += band(lx + colW, n.y, n.h, cx, yIn, n.h, fill, i, 'L'); yIn += n.h; g += `<rect x="${lx}" y="${n.y}" width="${colW}" height="${n.h}" rx="2" fill="${fill}"/>`; });
    R.forEach((n, i) => { const fill = n.color || '#9aa4b1'; g += band(cx + colW, yOut, n.h, rx, n.y, n.h, fill, i, 'R'); yOut += n.h; g += `<rect x="${rx}" y="${n.y}" width="${colW}" height="${n.h}" rx="2" fill="${fill}"/>`; });
    g += `<rect x="${cx}" y="${midY}" width="${colW}" height="${midH}" rx="2" fill="#0f1e33"/>`;
    // spread labels so small neighbouring nodes never overlap, with a leader line to the node
    const spread = (nodes, minGap) => { const out = []; let last = -Infinity;
      nodes.forEach(n => { const c = n.y + n.h / 2; const ly = Math.max(c, last + minGap); out.push(ly); last = ly; });
      for (let i = out.length - 1; i >= 0; i--) out[i] = Math.min(out[i], i === out.length - 1 ? H - 18 : out[i + 1] - minGap);
      return out.map(v => Math.max(12, v)); };
    if (!narrow) {
      const ly = spread(R, 30);
      R.forEach((n, i) => { if (Math.abs(ly[i] - (n.y + n.h / 2)) > 1) g += `<path d="M${rx + colW + 1},${n.y + n.h / 2} L${rx + colW + 5},${ly[i]}" stroke="${MUTED}" fill="none"/>`; });
      R.forEach((n, i) => { n.ly = ly[i]; });
      L.forEach(n => { g += `<text x="${lx - 6}" y="${n.y + n.h / 2 + 4}" text-anchor="end" font-size="12" fill="${INK}">${esc(n.label)}</text><text x="${lx - 6}" y="${n.y + n.h / 2 + 18}" text-anchor="end" font-size="11" fill="${MUTED}">${esc(money2(n.v / days))}/day</text>`; });
      R.forEach(n => { g += `<text x="${rx + colW + 8}" y="${n.ly + 1}" font-size="12" fill="${INK}">${esc(n.label)}</text><text x="${rx + colW + 8}" y="${n.ly + 14}" font-size="11" fill="${MUTED}">${esc(money2(n.v / days))}/day · ${esc(pct(n.v / total))}</text>`; });
    }
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-hidden="true">${g}</svg>${narrow ? '<p class="subtle">On a narrow screen the labels are in the legend and the table below; hover or tap a band for its amount.</p>' : ''}`;
    const svg = box.querySelector('svg'), tip = tipLayer(box);
    svg.addEventListener('pointermove', ev => {
      const p = ev.target.closest('.lk'); if (!p) { tip.hide(); return; }
      const n = (p.dataset.side === 'L' ? L : R)[+p.dataset.i], r = svg.getBoundingClientRect();
      tip.show(`<b>${esc(n.label)}</b><div>${esc(money(n.v))} · ${esc(money2(n.v / days))} per resident day</div><div>${esc(pct(n.v / total))} of the total</div>`, ev.clientX - r.left, ev.clientY - r.top);
    });
    svg.addEventListener('pointerleave', () => tip.hide());
  }

  // ------------------------------------------------------------------ tabs, URL state, init
  let view = 'home';
  function show(v, focus) {
    view = v;
    document.querySelectorAll('.ci-tabs [role="tab"]').forEach(t => { const on = t.dataset.view === v; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; if (on && focus) t.focus(); });
    document.querySelectorAll('[role="tabpanel"]').forEach(p => { p.hidden = p.id !== `panel-${v}`; });
    render();
  }
  function render() {
    ({ home: renderHome, compare: renderCompare, peers: renderPeers, pivot: renderPivot, scatter: renderScatter, flow: renderFlow })[view]();
    syncUrl();
  }
  function openHome(ccn) { homeCcn = ccn; show('home'); const t = document.getElementById('home-title'); if (t) t.focus(); }
  function syncUrl() {
    const u = new URL(global.location.href), p = new URLSearchParams();
    p.set('view', view);
    if (real) p.set('real', '1');
    const g = id => document.getElementById(id).value;
    if (view === 'home' && homeCcn) { p.set('ccn', homeCcn); if (homeExtra) p.set('extra', homeExtra); }
    if (view === 'compare') { if (cmp.length) p.set('homes', cmp.join(',')); p.set('metric', g('cmp-metric')); p.set('year', g('cmp-year')); }
    if (view === 'peers') { p.set('by', g('peer-type')); p.set('group', g('peer-group')); p.set('metric', g('peer-metric')); p.set('year', g('peer-year')); }
    if (view === 'pivot') {
      p.set('rows', g('pv-rows')); p.set('metric', g('pv-metric')); p.set('agg', g('pv-agg'));
      if (g('pv-filter')) p.set('filter', g('pv-filter'));
      if (pvSort.col != null) { p.set('sort', pvSort.col); p.set('dir', pvSort.dir); }
    }
    if (view === 'scatter') { p.set('x', g('sc-x')); p.set('y', g('sc-y')); p.set('year', g('sc-year')); if (g('sc-type')) { p.set('by', g('sc-type')); p.set('group', g('sc-group')); } }
    if (view === 'flow' && flowCcn) { p.set('ccn', flowCcn); p.set('year', g('flow-year')); }
    u.search = p.toString();
    if (u.href !== global.location.href) document.getElementById('ci-copy-status').textContent = '';
    global.history.replaceState(null, '', u);
  }

  async function copyViewLink() {
    const status = document.getElementById('ci-copy-status');
    const url = global.location.href;
    try {
      await navigator.clipboard.writeText(url);
      status.textContent = 'Link copied.';
    } catch {
      const input = document.createElement('textarea');
      input.value = url;
      input.readOnly = true;
      input.style.cssText = 'position:fixed;inset:0 auto auto 0;opacity:0';
      document.body.append(input);
      try {
        input.select();
        status.textContent = document.execCommand('copy') ? 'Link copied.' : 'Copy the link from the address bar.';
      } catch {
        status.textContent = 'Copy the link from the address bar.';
      } finally {
        input.remove();
        document.getElementById('ci-copy').focus();
      }
    }
  }

  async function init() {
    const note = document.getElementById('ci-note');
    try {
      const r = await fetch(DATA);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      D = await r.json();
    } catch (err) {
      note.textContent = `The cost-report figures could not be loaded. Details: ${err.message}`;
      note.className = 'notice error';
      return;
    }
    D.metrics.forEach(m => { META[m.key] = m; });
    Object.assign(META, VIRTUAL);
    KEYS = D.metrics.map(m => m.key);
    D.homes.forEach(h => { HOMES[h.ccn] = h; });
    note.textContent = `${D.homes.length} homes, cost years ${D.years[0]} to ${D.years[D.years.length - 1]}.`;
    document.getElementById('ci-base-year').textContent = D.cpi.base_year;
    document.getElementById('ci-method').innerHTML = Object.values(D.method).map(v => `<li>${esc(v)}</li>`).join('');

    const q = new URLSearchParams(global.location.search), pick = (k, d) => q.get(k) || d;
    real = q.get('real') === '1';
    document.getElementById('ci-real').checked = real;
    const allKeys = KEYS;
    // home view
    const extra = document.getElementById('home-extra');
    extra.innerHTML = '<option value="">None</option>' + [...new Set(allKeys.map(k => META[k].group))].map(gp => `<optgroup label="${esc(gp)}">${allKeys.filter(k => META[k].group === gp && !HOME_PANELS.includes(k)).map(k => `<option value="${k}">${esc(META[k].label)}</option>`).join('')}</optgroup>`).join('');
    homeExtra = KEYS.includes(q.get('extra')) ? q.get('extra') : '';
    extra.value = homeExtra;
    extra.addEventListener('change', () => { homeExtra = extra.value; renderHome(); syncUrl(); });
    picker(document.getElementById('home-search'), document.getElementById('home-results'), c => { homeCcn = c; renderHome(); syncUrl(); });
    // compare
    metricOptions(document.getElementById('cmp-metric'), allKeys, 'expenses');
    yearOptions(document.getElementById('cmp-year'));
    picker(document.getElementById('cmp-search'), document.getElementById('cmp-results'), c => { if (!cmp.includes(c) && cmp.length < 5) cmp.push(c); renderCompare(); });
    document.getElementById('cmp-chips').addEventListener('click', e => { const b = e.target.closest('[data-rm]'); if (b) { cmp = cmp.filter(c => c !== b.dataset.rm); renderCompare(); } });
    ['cmp-metric', 'cmp-year'].forEach(id => document.getElementById(id).addEventListener('change', renderCompare));
    // peers
    const pt = document.getElementById('peer-type'), pg = document.getElementById('peer-group');
    pt.innerHTML = PEER_TYPES.map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join('');
    metricOptions(document.getElementById('peer-metric'), allKeys, 'admin');
    yearOptions(document.getElementById('peer-year'));
    pt.addEventListener('change', () => { fillGroupSelect(pt, pg); renderPeers(); });
    ['peer-group', 'peer-metric', 'peer-year'].forEach(id => document.getElementById(id).addEventListener('change', renderPeers));
    // pivot
    const pvRows = document.getElementById('pv-rows');
    pvRows.innerHTML = `<option value="management">Management company</option><option value="affiliation">CMS affiliated entity (chain)</option><option value="county">Planning region</option><option value="size">Size (certified beds)</option><option value="ownership">Ownership type</option><option value="medicaid_band">Medicaid share of days</option><option value="home">Each home</option>`;
    metricOptions(document.getElementById('pv-metric'), allKeys, 'management_fees');
    ['pv-rows', 'pv-metric', 'pv-agg'].forEach(id => document.getElementById(id).addEventListener('change', () => { pvSort = { col: null, dir: -1 }; renderPivot(); }));
    document.getElementById('pv-filter').addEventListener('input', renderPivot);
    document.getElementById('pv-csv').addEventListener('click', pivotCsv);
    document.getElementById('pv-out').addEventListener('click', e => {
      const s = e.target.closest('button[data-sort]');
      if (s) { const col = s.dataset.sort === 'label' ? 'label' : +s.dataset.sort; pvSort = { col, dir: pvSort.col === col ? -pvSort.dir : (col === 'label' ? 1 : -1) }; renderPivot(); }
    });
    // scatter
    const scKeys = ['overhead'].concat(allKeys);
    metricOptions(document.getElementById('sc-x'), scKeys, 'overhead');
    metricOptions(document.getElementById('sc-y'), scKeys, 'nursing');
    yearOptions(document.getElementById('sc-year'));
    const st = document.getElementById('sc-type'), sg = document.getElementById('sc-group');
    st.innerHTML = '<option value="">None</option>' + PEER_TYPES.map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join('');
    st.addEventListener('change', () => { if (st.value) fillGroupSelect(st, sg); else sg.innerHTML = ''; sg.disabled = !st.value; renderScatter(); });
    sg.disabled = true;
    ['sc-x', 'sc-y', 'sc-year', 'sc-group'].forEach(id => document.getElementById(id).addEventListener('change', renderScatter));
    // flow
    yearOptions(document.getElementById('flow-year'));
    picker(document.getElementById('flow-search'), document.getElementById('flow-results'), c => { flowCcn = c; const h = HOMES[c]; const ys = homeYears(h).filter(y => usable(h, y)); if (ys.length) document.getElementById('flow-year').value = ys[ys.length - 1]; renderFlow(); });
    document.getElementById('flow-year').addEventListener('change', renderFlow);
    // shared
    document.getElementById('ci-copy').addEventListener('click', copyViewLink);
    document.getElementById('ci-real').addEventListener('change', e => { real = e.target.checked; render(); });
    document.querySelector('main').addEventListener('click', e => { const b = e.target.closest('[data-open]'); if (b) openHome(b.dataset.open); });
    const tabs = [...document.querySelectorAll('.ci-tabs [role="tab"]')];
    tabs.forEach((t, i) => {
      t.addEventListener('click', () => show(t.dataset.view));
      t.addEventListener('keydown', e => {
        const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (d) { e.preventDefault(); show(tabs[(i + d + tabs.length) % tabs.length].dataset.view, true); }
      });
    });
    let rz; global.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(render, 150); });

    // restore from the URL
    const v = pick('view', 'home');
    const okYear = y => D.years.map(String).includes(y);
    if (HOMES[q.get('ccn')]) { homeCcn = q.get('ccn'); flowCcn = q.get('ccn'); }
    if (v === 'compare') { cmp = (q.get('homes') || '').split(',').filter(c => HOMES[c]).slice(0, 5); if (KEYS.includes(q.get('metric'))) document.getElementById('cmp-metric').value = q.get('metric'); if (okYear(q.get('year'))) document.getElementById('cmp-year').value = q.get('year'); }
    if (v === 'peers') { if (PEER_TYPES.some(p => p[0] === q.get('by'))) pt.value = q.get('by'); if (KEYS.includes(q.get('metric'))) document.getElementById('peer-metric').value = q.get('metric'); if (okYear(q.get('year'))) document.getElementById('peer-year').value = q.get('year'); }
    fillGroupSelect(pt, pg, v === 'peers' ? q.get('group') : null);
    if (v === 'pivot') { if (q.get('rows')) pvRows.value = q.get('rows'); if (KEYS.includes(q.get('metric'))) document.getElementById('pv-metric').value = q.get('metric'); if (q.get('agg') === 'mean') document.getElementById('pv-agg').value = 'mean';
      document.getElementById('pv-filter').value = q.get('filter') || '';
      const sort = q.get('sort');
      if (sort === 'label' || (/^\d+$/.test(sort || '') && Number(sort) < D.years.length + 2)) {
        pvSort = { col: sort === 'label' ? sort : Number(sort), dir: q.get('dir') === '1' ? 1 : -1 };
      }
    }
    if (v === 'scatter') {
      if (scKeys.includes(q.get('x'))) document.getElementById('sc-x').value = q.get('x');
      if (scKeys.includes(q.get('y'))) document.getElementById('sc-y').value = q.get('y');
      if (okYear(q.get('year'))) document.getElementById('sc-year').value = q.get('year');
      if (PEER_TYPES.some(p => p[0] === q.get('by'))) { st.value = q.get('by'); fillGroupSelect(st, sg, q.get('group')); sg.disabled = false; }
    }
    if (v === 'flow' && okYear(q.get('year'))) document.getElementById('flow-year').value = q.get('year');
    else if (flowCcn) { const h = HOMES[flowCcn]; const ys = homeYears(h).filter(y => usable(h, y)); if (ys.length) document.getElementById('flow-year').value = ys[ys.length - 1]; }
    show(['home', 'compare', 'peers', 'pivot', 'scatter', 'flow'].includes(v) ? v : 'home');
  }

  document.addEventListener('DOMContentLoaded', init);
})(window);
