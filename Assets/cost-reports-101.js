/* Cost Reports 101 (/staffing/tools/nursing-home-cost-reports-101.html).
 * Draws plain SVG charts from /data/ct_cost_reports_101.json and, for one picked home,
 * /api/v1/facilities/{ccn}/financials.json. All data text is inserted with textContent.
 */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var C = { ink: '#173761', teal: '#2e8fa3', gold: '#c98a12', gray: '#8a97a8', red: '#e3212b', line: '#dbe0e5', muted: '#526170', text: '#253746' };
  var SHORT = {
    nursing: 'Nursing care (direct care)', admin: 'Administrative & general', other_staff: 'All other staff', property: 'Building & property',
    dietary: 'Dietary (food & kitchen)', resident_care: 'Resident care supplies', other_fees: 'Other professional fees', plant: 'Plant & utilities',
    housekeeping: 'Housekeeping', laundry: 'Laundry', insurance: 'Insurance', interest: 'Interest'
  };
  var base = null;

  function $(id) { return document.getElementById(id); }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }
  function s(tag, attrs, text) {
    var e = document.createElementNS(NS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }
  function svgRoot(w, h, label) {
    var r = s('svg', { viewBox: '0 0 ' + w + ' ' + h, role: 'img', 'aria-label': label });
    return r;
  }
  function money(v, cents) {
    if (v === null || v === undefined || isNaN(v)) return 'not in data';
    return (v < 0 ? '-$' : '$') + Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: cents ? 2 : 0, maximumFractionDigits: cents ? 2 : 0 });
  }
  function pct(v) { return (v * 100).toFixed(0) + '%'; }
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }
  function width(node, fallback, max) { var w = node && node.clientWidth; return Math.max(300, Math.min(max || 760, w || fallback || 600)); }

  // ------------------------------------------------------------- 2. payers
  function payerChart(d) {
    var box = $('payer-chart'); clear(box);
    var p = d.payer_share_of_days;
    var parts = [['Medicaid (CT)', p.medicaid_ct, C.ink], ['Medicare', p.medicare, C.teal], ['Private pay', p.private, C.gold], ['Other', p.other, C.gray]];
    var W = width(box, 420), H = 150, x = 0;
    var r = svgRoot(W, H, 'Share of Connecticut nursing home resident days by payer, cost year ' + d.cost_year + ': ' +
      parts.map(function (q) { return q[0] + ' ' + pct(q[1]); }).join(', '));
    r.appendChild(s('text', { x: 0, y: 16, 'font-size': 13, fill: C.muted }, 'Share of all resident days, cost year ' + d.cost_year));
    parts.forEach(function (q) {
      var w = q[1] * W;
      var rect = s('rect', { x: x, y: 28, width: Math.max(w - 2, 0), height: 46, rx: 4, fill: q[2], 'class': 'grow' });
      rect.appendChild(s('title', null, q[0] + ': ' + pct(q[1])));
      r.appendChild(rect);
      if (w > 46) r.appendChild(s('text', { x: x + 8, y: 57, 'font-size': 15, 'font-weight': 800, fill: '#fff' }, pct(q[1])));
      x += w;
    });
    var lx = 0;
    parts.forEach(function (q, i) {
      var gx = (i % 2) * (W / 2), gy = 100 + Math.floor(i / 2) * 22;
      r.appendChild(s('rect', { x: gx, y: gy - 10, width: 12, height: 12, rx: 2, fill: q[2] }));
      r.appendChild(s('text', { x: gx + 18, y: gy, 'font-size': 13, fill: C.text }, q[0] + ' ' + pct(q[1])));
      lx = gx;
    });
    box.appendChild(r);
    box.appendChild(el('p', { 'class': 'chart-note' }, 'Pooled from ' + d.pooled_homes + ' homes whose ' + d.cost_year + ' reports passed the site\'s checks.'));
  }

  // ---------------------------------------------------- 3. day's money
  function categoryChart(host, rows, opts) {
    opts = opts || {};
    clear(host);
    var W = width(host, 560), narrow = W < 520, rowH = narrow ? 44 : 30, L = narrow ? 0 : Math.min(210, W * 0.42), H = rows.length * rowH + (opts.compare ? (narrow ? 48 : 34) : 8);
    var max = Math.max.apply(null, rows.map(function (r) { return Math.max(r.value || 0, r.compare || 0); }));
    var r = svgRoot(W, H, opts.label || 'Cost per resident day by category');
    var y0 = opts.compare ? (narrow ? 44 : 26) : 0;
    if (opts.compare) {
      r.appendChild(s('rect', { x: 0, y: 2, width: 12, height: 12, rx: 2, fill: C.ink }));
      r.appendChild(s('text', { x: 18, y: 12, 'font-size': 12, fill: C.text }, opts.compare.home));
      var lx2 = narrow ? 0 : 200, ly2 = narrow ? 22 : 2;
      r.appendChild(s('rect', { x: lx2, y: ly2, width: 12, height: 12, rx: 2, fill: C.gray }));
      r.appendChild(s('text', { x: lx2 + 18, y: ly2 + 10, 'font-size': 12, fill: C.text }, opts.compare.base));
    }
    rows.forEach(function (row, i) {
      var y = y0 + i * rowH, bw = W - L - 120;
      if (narrow) { r.appendChild(s('text', { x: 0, y: y + 12, 'font-size': 13, fill: C.text }, row.label)); y += 14; }
      else r.appendChild(s('text', { x: L - 8, y: y + 18, 'font-size': 13, 'text-anchor': 'end', fill: C.text }, row.label));
      var w = (row.value || 0) / max * bw;
      var bar = s('rect', { x: L, y: y + (opts.compare ? 4 : 6), width: Math.max(w, 1), height: opts.compare ? 11 : 18, rx: 3, fill: row.color || C.ink, 'class': 'grow' });
      bar.appendChild(s('title', null, row.label + ': ' + money(row.value, true) + ' per resident day'));
      r.appendChild(bar);
      if (opts.compare && row.compare !== undefined && row.compare !== null) {
        var cb = s('rect', { x: L, y: y + 17, width: Math.max(row.compare / max * bw, 1), height: 8, rx: 3, fill: C.gray, 'class': 'grow' });
        cb.appendChild(s('title', null, row.label + ', ' + opts.compare.base + ': ' + money(row.compare, true)));
        r.appendChild(cb);
      }
      r.appendChild(s('text', { x: L + w + 6, y: y + 19, 'font-size': 13, 'font-weight': 700, fill: C.ink }, money(row.value, true) + (row.share ? '  (' + pct(row.share) + ')' : '')));
    });
    host.appendChild(r);
  }

  function dayCost(d) {
    $('day-cost').textContent = money(d.pooled_cost_per_resident_day, true);
    $('day-cost-label').textContent = 'Reported cost of one resident day in cost year ' + d.cost_year + ', ' + d.pooled_homes + ' Connecticut homes pooled';
    categoryChart($('category-chart'), d.categories.map(function (c) {
      return { label: SHORT[c.key] || c.label, value: c.per_resident_day, share: c.share, color: c.key === 'nursing' ? C.ink : ['dietary', 'housekeeping', 'laundry'].indexOf(c.key) >= 0 ? C.teal : c.key === 'admin' || c.key === 'property' ? C.gold : '#5d7896' };
    }), { label: 'Reported cost per resident day by category, Connecticut pooled' });
    $('category-note').textContent = 'Navy: direct care. Teal: indirect care departments. Gold: administration and property. All homes\' costs added together, then divided by all their resident days. Typical (median) home: ' +
      money(d.medians.expenses_per_resident_day, true) + ' per resident day.';
  }

  // ---------------------------------------------------- 4. review stats
  function reviewStats(d) {
    var ul = $('not-allowed'); clear(ul);
    d.rate_rules.not_allowed_examples.forEach(function (t) { ul.appendChild(el('li', null, t.charAt(0).toUpperCase() + t.slice(1))); });
    var r = d.dss_review, box = $('review-stats'); clear(box);
    [[r.homes_with_review_changes + ' of ' + r.homes_in_files, 'homes had at least one line changed in DSS\'s review of their ' + d.cost_year + ' report'],
     [r.management_fee_changed + ' of ' + r.homes_reporting_management_fee, 'homes reporting a management fee had it changed in review (' + r.management_fee_fully_removed + ' fully removed)'],
     [money(r.median_medicaid_revenue_per_medicaid_day, true), 'typical Medicaid revenue per Medicaid day (median home, after contractual allowance)'],
     [money(d.medians.expenses_per_resident_day, true), 'typical reported cost per resident day, all payers (median home)']
    ].forEach(function (x) { var c = el('div', { 'class': 'stat' }); c.appendChild(el('strong', null, x[0])); c.appendChild(el('span', null, x[1])); box.appendChild(c); });
  }

  // ---------------------------------------------------- 5. rate build
  function rateBuild(d) {
    var r = $('rate-svg');
    var comps = d.rate_rules.components, H = 360, x = 10, w = 96, y = 330;
    var heights = { direct: 150, indirect: 55, admin: 45, fair_rent: 30, capital: 20 };
    var colors = { direct: C.ink, indirect: C.teal, admin: C.gold, fair_rent: '#7a5aa6', capital: C.gray };
    var lastLabel = 1e9;
    comps.forEach(function (c) {
      var h = heights[c.key] || 30; y -= h;
      var ly = Math.min(y + h / 2, lastLabel - 36); lastLabel = ly;
      var rect = s('rect', { x: x, y: y, width: w, height: h - 3, rx: 4, fill: colors[c.key] });
      rect.appendChild(s('title', null, c.label + ': ' + c.what + (c.cap ? ' Capped at ' + c.cap + '.' : '')));
      r.appendChild(rect);
      r.appendChild(s('polyline', { points: (x + w + 3) + ',' + (y + h / 2) + ' ' + (x + w + 14) + ',' + (y + h / 2) + ' ' + (x + w + 22) + ',' + ly, fill: 'none', stroke: C.gray }));
      r.appendChild(s('text', { x: x + w + 28, y: ly - 2, 'font-size': 15, 'font-weight': 800, fill: C.ink }, c.label));
      r.appendChild(s('text', { x: x + w + 28, y: ly + 15, 'font-size': 13, fill: C.muted }, c.cap ? 'Capped at ' + c.cap.replace(' the peer-group median', ' median').replace(' the median', ' median') + (c.peer ? ', by region' : '') : 'Own formula, not capped'));
    });
    r.appendChild(s('text', { x: x, y: 350, 'font-size': 12, fill: C.muted }, 'One daily rate (per diem). Heights are illustrative.'));
    r.appendChild(s('text', { x: x, y: y - 10, 'font-size': 14, 'font-weight': 800, fill: C.text }, 'The per diem'));
    var ol = $('rate-adjustments'); clear(ol);
    d.rate_rules.adjustments.forEach(function (t) { ol.appendChild(el('li', null, t)); });

    // cap illustration
    var host = $('cap-svg-wrap'), W = width(host, 420), Hc = 210;
    var g = svgRoot(W, Hc, 'Illustration: two homes against a cap set at 135 percent of the median. A home spending 120 percent of the median is counted in full; a home spending 160 percent is counted only up to 135 percent.');
    var base = Hc - 30, unit = 90 / 100, bx = [60, 170, 280];
    var bars = [['Median home', 100, false], ['Home A', 120, false], ['Home B', 160, true]];
    bars.forEach(function (b, i) {
      var h = b[1] * unit, counted = Math.min(b[1], 135) * unit;
      g.appendChild(s('rect', { x: bx[i], y: base - counted, width: 70, height: counted, rx: 3, fill: C.ink }));
      if (b[2]) {
        g.appendChild(s('rect', { x: bx[i], y: base - h, width: 70, height: h - counted, rx: 3, fill: '#fde7e8', stroke: C.red, 'stroke-dasharray': '4 3' }));
        g.appendChild(s('text', { x: bx[i] + 35, y: base - h - 6, 'font-size': 12, 'text-anchor': 'middle', fill: '#a1151c' }, 'not counted'));
      }
      g.appendChild(s('text', { x: bx[i] + 35, y: base + 18, 'font-size': 12, 'text-anchor': 'middle', fill: C.text }, b[0]));
      g.appendChild(s('text', { x: bx[i] + 35, y: base - 8, 'font-size': 13, 'font-weight': 800, 'text-anchor': 'middle', fill: '#fff' }, b[1] + '%'));
    });
    var cy = base - 135 * unit;
    g.appendChild(s('line', { x1: 40, x2: Math.min(W - 10, 400), y1: cy, y2: cy, stroke: C.red, 'stroke-width': 2, 'stroke-dasharray': '6 4' }));
    g.appendChild(s('text', { x: 40, y: cy - 6, 'font-size': 12, 'font-weight': 700, fill: C.red }, 'Cap: 135% of median'));
    host.appendChild(g);
    host.appendChild(el('p', { 'class': 'chart-note' }, 'Illustration of how a cap works, not real homes.'));
  }

  function ratesChart(d) {
    var host = $('rates-chart'); clear(host);
    var r = d.medicaid_rates_sfy2026, vals = r.values;
    if (!vals || !vals.length) { host.appendChild(el('p', { 'class': 'chart-note' }, 'Rates not available.')); return; }
    var lo = Math.floor(Math.min.apply(null, vals) / 25) * 25, hi = Math.ceil(Math.min(Math.max.apply(null, vals), 600) / 25) * 25;
    var bins = []; for (var b = lo; b < hi; b += 25) bins.push({ from: b, n: 0 });
    var over = 0;
    vals.forEach(function (v) { if (v >= hi) { over++; return; } var i = Math.floor((v - lo) / 25); if (bins[i]) bins[i].n++; });
    var W = width(host, 900, 1200), H = 230, L = 34, B = 36, T = 10, pw = W - L - 10, ph = H - T - B;
    var maxN = Math.max.apply(null, bins.map(function (x) { return x.n; }));
    var g = svgRoot(W, H, 'Histogram of Medicaid daily rates for ' + r.homes + ' Connecticut homes, ' + r.rate_period + '. Median ' + money(r.median, true) + ', range ' + money(r.min, true) + ' to ' + money(r.max, true) + '.');
    var bw = pw / bins.length;
    for (var t = 0; t <= maxN; t += Math.max(1, Math.ceil(maxN / 4))) {
      var ty = T + ph - t / maxN * ph;
      g.appendChild(s('line', { x1: L, x2: W - 10, y1: ty, y2: ty, stroke: '#eef1f4' }));
      g.appendChild(s('text', { x: L - 6, y: ty + 4, 'font-size': 11, 'text-anchor': 'end', fill: C.muted }, t));
    }
    bins.forEach(function (x, i) {
      var h = x.n / maxN * ph;
      var rect = s('rect', { x: L + i * bw + 1, y: T + ph - h, width: Math.max(bw - 2, 1), height: h, rx: 2, fill: C.gold });
      rect.appendChild(s('title', null, money(x.from) + ' to ' + money(x.from + 25) + ': ' + x.n + ' homes'));
      g.appendChild(rect);
      if (i % Math.ceil(bins.length / 8) === 0) g.appendChild(s('text', { x: L + i * bw, y: H - B + 16, 'font-size': 11, fill: C.muted }, money(x.from)));
    });
    var mx = L + (r.median - lo) / (hi - lo) * pw;
    g.appendChild(s('line', { x1: mx, x2: mx, y1: T, y2: T + ph, stroke: C.ink, 'stroke-width': 2, 'stroke-dasharray': '5 4' }));
    g.appendChild(s('text', { x: mx + 6, y: T + 14, 'font-size': 12, 'font-weight': 700, fill: C.ink }, 'Median ' + money(r.median, true)));
    g.appendChild(s('text', { x: L, y: H - 4, 'font-size': 11, fill: C.muted }, 'Medicaid daily rate (each bar = $25 range); count of homes on the left'));
    host.appendChild(g);
    $('rates-title').textContent = 'Medicaid daily rates across Connecticut, ' + r.rate_period;
    $('rates-note').textContent = r.homes + ' homes, from DSS\'s rate letters. Lowest ' + money(r.min, true) + ', highest ' + money(r.max, true) +
      (over ? ' (' + over + ' home' + (over > 1 ? 's' : '') + ' above ' + money(hi) + ' not drawn, typically homes with specialized units).' : '.') +
      ' Rates differ mainly because each home\'s own past costs, caps, fair rent and resident acuity differ.';
  }

  // ---------------------------------------------------- 6. one home
  var facilities = [];
  function loadFacilities() {
    return fetch('/api/v1/facilities.json', { cache: 'force-cache' }).then(function (r) { return r.json(); }).then(function (j) {
      facilities = j.facilities;
      var dl = $('home-list');
      facilities.forEach(function (f) { dl.appendChild(el('option', { value: titleCase(f.facility_name) + ', ' + titleCase(f.city) + ' (' + f.ccn + ')' })); });
    });
  }
  function titleCase(t) { return String(t || '').toLowerCase().replace(/\b[a-z]/g, function (c) { return c.toUpperCase(); }); }
  function pick(value) {
    var m = /\((\d{6})\)\s*$/.exec(value || '');
    if (m) showHome(m[1]);
  }
  function card(title) { var c = el('div', { 'class': 'card' }); c.appendChild(el('h3', { style: 'margin-top:0' }, title)); return c; }

  function showHome(ccn) {
    var out = $('home-out'), st = $('home-status');
    clear(out); st.textContent = 'Loading…';
    try { history.replaceState(null, '', '?ccn=' + ccn + '#step-6'); } catch (e) { /* ignore */ }
    fetch('/api/v1/facilities/' + ccn + '/financials.json').then(function (r) { if (!r.ok) throw new Error(); return r.json(); }).then(function (f) {
      var ys = (f.years || []).filter(function (y) { return y.data_quality && y.data_quality.use_in_reports && !y.part_year; });
      if (!ys.length) { st.textContent = 'No cost report for this home passed the site\'s checks, so there is nothing reliable to show.'; return; }
      var y = ys[ys.length - 1], cy = y.cost_year;
      st.textContent = titleCase(f.facility_name) + ', cost year ' + cy + ' (October ' + (cy - 1) + ' to September ' + cy + ')' + (y.data_quality.status === 'unvalidated' ? '. Figures are provisional: the printed totals did not fully reconcile.' : '.');
      // a) categories vs Connecticut
      var c1 = card('Where its day\'s money went');
      if (y.cost_breakdown) {
        var pooled = {}; base.categories.forEach(function (c) { pooled[c.key] = c.per_resident_day; });
        var rows = Object.keys(y.cost_breakdown).map(function (k) { return { key: k, label: SHORT[k] || k, value: y.cost_breakdown[k].per_resident_day, compare: pooled[k] }; })
          .filter(function (r) { return r.value !== null; }).sort(function (a, b) { return (b.value || 0) - (a.value || 0); });
        var host = el('div'); c1.appendChild(host); out.appendChild(c1);
        var drawCats = function () { categoryChart(host, rows, { compare: { home: 'This home', base: 'Connecticut pooled, ' + base.cost_year }, label: 'This home\'s cost per resident day by category compared with Connecticut' }); };
        if (cy !== base.cost_year) c1.appendChild(el('p', { 'class': 'chart-note' }, 'Note: this home\'s latest usable year is ' + cy + '; the Connecticut figures are for ' + base.cost_year + '.'));
      } else {
        c1.appendChild(el('p', null, 'The category lines on this report did not add up to its printed total, so the breakdown is not shown.'));
        out.appendChild(c1);
      }
      // b) three layers
      var c2 = card('Reported, reviewed, paid');
      var dss = f.dss_review || {}, dy = (dss.years || {})[String(cy)];
      var t = el('table', { 'class': 'simple' }), tb = el('tbody');
      function row(a, b, note) { var tr = el('tr'); tr.appendChild(el('th', { scope: 'row' }, a)); tr.appendChild(el('td', { 'class': 'num' }, b)); tr.appendChild(el('td', { style: 'color:#526170;font-size:13px' }, note || '')); tb.appendChild(tr); }
      row('1. Reported cost per resident day', money(y.expenses_per_resident_day, true), 'All payers, before review');
      if (dy) {
        row('2. Removed by the home itself', money(dy.home_adjustments_total), 'Costs it did not claim');
        row('2. Net change in DSS\'s review', money(dy.review_adjustments_total), dy.review_adjusted_lines + ' line(s) changed');
        if (dy.management_fee_reported) row('   Management fee after review', money(dy.management_fee_reported + (dy.management_fee_home_adjustment || 0) + (dy.management_fee_review_adjustment || 0)), 'Reported ' + money(dy.management_fee_reported));
        row('3. Medicaid revenue per Medicaid day', money(dy.medicaid_revenue_net_per_medicaid_day, true), (dy.medicaid_ct_days || 0).toLocaleString('en-US') + ' Medicaid days');
      } else {
        row('2–3. DSS review and Medicaid revenue', 'not in data', 'Not in DSS\'s published files for this year');
      }
      Object.keys(dss.rates || {}).sort().forEach(function (k) { var rr = dss.rates[k]; row('3. Medicaid daily rate, ' + rr.rate_period.slice(0, 4) + '–' + rr.rate_period.slice(14, 18), money(rr.per_diem, true), 'DSS rate letter'); });
      t.appendChild(tb); c2.appendChild(t);
      c2.appendChild(el('p', { 'class': 'chart-note' }, 'Reported cost includes things the daily rate does not cover (for example pharmacy and therapy), so the gap between lines 1 and 3 is not a Medicaid shortfall.'));
      if (dy && y.expenses_per_resident_day && dy.medicaid_revenue_net_per_medicaid_day) {
        var host2 = el('div'); c2.appendChild(host2);
        var drawGap = function () { categoryChart(host2, [
          { label: 'Reported cost / resident day', value: y.expenses_per_resident_day, color: C.ink },
          { label: 'Medicaid revenue / Medicaid day', value: dy.medicaid_revenue_net_per_medicaid_day, color: C.gold }
        ], { label: 'Reported cost per resident day compared with Medicaid revenue per Medicaid day' }); };
      }
      var a = el('a', { href: '/staffing/reports/?ccn=' + ccn + '&type=financial-transparency' }, 'Open the full financial report for this home');
      c2.appendChild(el('p')).appendChild(a);
      out.appendChild(c2);
      if (typeof drawCats === 'function') drawCats();
      if (typeof drawGap === 'function') drawGap();
    }).catch(function () { st.textContent = 'Could not load this home\'s data.'; });
  }

  function timeline(k) {
    var ev = k.timeline, track = $('tl-track'), stage = $('tl-stage'), fill = $('tl-fill'), spark = $('tl-spark');
    var t0 = Date.parse(ev[0].iso), t1 = Date.parse(ev[ev.length - 1].iso);
    var pos = ev.map(function (e) { return (Date.parse(e.iso) - t0) / (t1 - t0) * 100; });
    var nodes = [], cur = -1, timer = null;
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    ev.forEach(function (e, i) {
      var cls = 'tl-node ' + e.kind + (i % 2 ? ' down' : ' up') + (i === 0 ? ' edge-l' : i === ev.length - 1 ? ' edge-r' : '');
      var b = el('button', { type: 'button', 'class': cls, role: 'tab', 'aria-selected': 'false', tabindex: '-1', id: 'tl-n' + i, 'aria-controls': 'tl-stage', style: 'left:' + pos[i] + '%' });
      b.appendChild(el('span', { 'class': 'tl-dot', 'aria-hidden': 'true' }));
      var lab = el('span', { 'class': 'tl-lab' }); lab.appendChild(el('b', null, e.short)); lab.appendChild(document.createTextNode(e.what)); b.appendChild(lab);
      b.addEventListener('click', function () { stop(); go(i); });
      b.addEventListener('keydown', function (x) {
        var j = x.key === 'ArrowRight' ? i + 1 : x.key === 'ArrowLeft' ? i - 1 : x.key === 'Home' ? 0 : x.key === 'End' ? ev.length - 1 : null;
        if (j === null || j < 0 || j >= ev.length) return; x.preventDefault(); stop(); go(j); nodes[j].focus();
      });
      track.appendChild(b); nodes.push(b);
    });
    $('tl-ongoing').textContent = k.ongoing || '';
    function render(i) {
      var e = ev[i]; clear(stage); stage.className = 'tl-stage ' + e.kind;
      stage.setAttribute('aria-labelledby', 'tl-n' + i);
      stage.appendChild(el('div', { 'class': 'tl-step', 'aria-hidden': 'true' }, i + 1));
      stage.appendChild(el('div', { 'class': 'tl-when' }, e.date));
      stage.appendChild(el('h3', null, e.what));
      stage.appendChild(el('p', null, e.detail));
      stage.appendChild(el('div', { 'class': 'tl-meta' }, e.who + ' · Conn. Gen. Stat. ' + e.cite));
      void stage.offsetWidth; if (!reduce) stage.className += ' enter';
    }
    function go(i) {
      if (i === cur) return;
      stage.style.setProperty('--tl-dir', i > cur ? '28px' : '-28px');
      cur = i;
      nodes.forEach(function (n, j) { n.setAttribute('aria-selected', j === i ? 'true' : 'false'); n.tabIndex = j === i ? 0 : -1; });
      fill.style.width = pos[i] + '%'; spark.style.left = pos[i] + '%';
      var wrap = track.parentNode, x = track.offsetLeft + track.clientWidth * pos[i] / 100 - wrap.clientWidth / 2;
      if (wrap.scrollWidth > wrap.clientWidth) wrap.scrollTo({ left: x, behavior: reduce ? 'auto' : 'smooth' });
      if (document.startViewTransition && !reduce) document.startViewTransition(function () { render(i); }); else render(i);
    }
    var play = $('tl-play');
    function stop() { if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play the year'; } }
    play.addEventListener('click', function () {
      if (timer) { stop(); return; }
      play.textContent = 'Pause'; go(0);
      timer = setInterval(function () { if (cur >= ev.length - 1) { stop(); return; } go(cur + 1); }, 3200);
    });
    go(0);
  }

  function keyDates(d) {
    var k = d.key_dates; if (!k) return;
    timeline(k);
    var tb = $('date-rules').querySelector('tbody');
    k.rules.forEach(function (r) {
      var tr = el('tr');
      tr.appendChild(el('td', null, r.when)); tr.appendChild(el('td', { 'data-label': 'What the law requires' }, r.rule));
      tr.appendChild(el('td', { 'data-label': "If it doesn't happen" }, r.if_not || '—'));
      var td = el('td', { 'class': 'cite', 'data-label': 'Law' }); td.appendChild(el('a', { href: r.url, rel: 'noopener' }, r.cite)); tr.appendChild(td);
      tb.appendChild(tr);
    });
    $('date-checked').textContent = 'Source: ' + k.checked + '. Citations link to the statute text.';
    var ul = $('date-not-law'); k.not_in_law.forEach(function (t) { ul.appendChild(el('li', null, t)); });
    var sb = $('source-table').querySelector('tbody');
    (d.sources || []).forEach(function (x) {
      var tr = el('tr'); tr.appendChild(el('td', null, x.group));
      var td = el('td'); td.appendChild(el('a', { href: x.url, rel: 'noopener' }, x.name)); tr.appendChild(td);
      tr.appendChild(el('td', null, x.what)); sb.appendChild(tr);
    });
  }

  function init() {
    fetch('/data/ct_cost_reports_101.json', { cache: 'force-cache' }).then(function (r) { return r.json(); }).then(function (d) {
      base = d;
      payerChart(d); dayCost(d); reviewStats(d); rateBuild(d); ratesChart(d); keyDates(d);
      return loadFacilities();
    }).then(function () {
      var inp = $('home-input');
      inp.addEventListener('change', function () { pick(inp.value); });
      inp.addEventListener('input', function () { if (/\(\d{6}\)\s*$/.test(inp.value)) pick(inp.value); });
      var q = new URLSearchParams(location.search).get('ccn') || '075396';
      var f = facilities.filter(function (x) { return x.ccn === q; })[0];
      if (f) { inp.value = titleCase(f.facility_name) + ', ' + titleCase(f.city) + ' (' + f.ccn + ')'; showHome(f.ccn); }
    }).catch(function () {
      var b = $('payer-chart'); clear(b); b.appendChild(el('p', { 'class': 'chart-note' }, 'Could not load the Connecticut data for these charts.'));
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
