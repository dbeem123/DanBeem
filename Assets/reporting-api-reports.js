/* Facility Reports page (/staffing/reports/).
 * Reads the static reporting API (/api/v1/...) and renders a report, plus
 * "Ask your AI" links that open the visitor's own ChatGPT or Claude with a
 * prompt pointing at the report's public URL. Read-only; nothing is sent to
 * danbeem.xyz. All text from data is inserted with textContent.
 */
(function () {
  'use strict';

  var PUBLIC = 'https://danbeem.xyz';
  var API = '/api/v1';
  var KIND_LABEL = {
    confirmed_fact: 'Confirmed fact',
    calculated: 'Calculated',
    possible_association: 'Possible association',
    investigative_question: 'Open question',
    missing_data: 'Missing data'
  };
  var TYPE_LABEL = {
    'facility-comprehensive': 'Full facility report',
    'ownership-network': 'Ownership, management and administrators',
    'related-party-screening': 'Related-party screening',
    'staffing-analysis': 'Staffing analysis',
    'financial-transparency': 'Finances (DSS cost reports)',
    'regulatory-history': 'Inspections and penalties',
    'facility-comparison': 'Comparison of two homes',
    'management-company-portfolio': 'Management company portfolio'
  };
  var QUESTIONS = {
    'facility-comprehensive': [
      "Summarize this home's staffing, finances, ownership and inspection record for a resident advocate. What stands out, and what should be verified?",
      'What are the three most important concerns in this report, with the evidence for each?',
      'Who has owned, managed and run this home over time, and did staffing or citations change when they changed?'
    ],
    'ownership-network': [
      'Who owns, controls and manages this home now, and how has that changed over time?',
      'Which people or companies listed here also appear at other Connecticut homes? Explain what that does and does not show.',
      'List the public records I should request to confirm who owns and controls this home.'
    ],
    'related-party-screening': [
      'Which payments go to related parties, and how large are they compared with what the home spends on direct care?',
      'Is there evidence here of a related-party or management-fee concern? Keep confirmed facts separate from possible associations.',
      'What records would I need to confirm or rule out a relationship between this home and the other names I checked?'
    ],
    'staffing-analysis': [
      'How does staffing at this home compare with the Connecticut median over time?',
      'How much does this home rely on agency (contract) staff, and is that changing?',
      'Which quarters fell below Connecticut comparison points, and what should I ask the home about them?',
      "Chart this home's nurse staffing and agency share against the Connecticut median, using only the report's chart data."
    ],
    'financial-transparency': [
      "Where does this home's money go, and how does direct care spending compare with the state median?",
      'How have management fees and related-party costs changed over the years?',
      'Explain the difference between reported wages and total department spending for dietary, housekeeping and laundry at this home.',
      'Which support departments (dietary, housekeeping, laundry, raw food) differ most from the Connecticut median, and what questions does that raise?',
      "Chart this home's direct care cost per resident day against the Connecticut median over time, using only the report's chart data."
    ],
    'regulatory-history': [
      "Summarize this home's inspection and penalty history in plain language.",
      'Which problems keep getting cited, and how serious were they?',
      'What should an ombudsman or family member ask the home about its recent citations?'
    ],
    'facility-comparison': [
      'Compare these two homes on staffing, finances, ownership and inspections. Which differences matter most?',
      'Which home relies more on agency staff, and which spends more on direct care per resident day?'
    ],
    'management-company-portfolio': [
      "Summarize this management company's Connecticut homes and how staffing looked under its management.",
      'How much did homes report paying this company in management fees over time?'
    ]
  };

  var state = { ccn: null, compare: null, company: null, type: 'facility-comprehensive', report: null, reportUrl: null, names: [] };
  var facilities = [];
  var byCcn = {};
  var searchIndex = null;

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }
  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
  function status(msg) { $('rp-status').textContent = msg || ''; }

  // Same normalization as scripts/build_reporting_api.py norm_name().
  function norm(s) {
    s = String(s || '').toUpperCase();
    s = s.replace(/[.,'’`"()]/g, ' ');
    s = s.replace(/\b(INC|LLC|LLP|LP|L L C|CORP|CORPORATION|CO|COMPANY|LTD|D\/B\/A|DBA|THE)\b/g, ' ');
    s = s.replace(/[^A-Z0-9 ]/g, ' ');
    return s.replace(/\s+/g, ' ').trim();
  }

  function getJSON(path) {
    return fetch(path, { cache: 'force-cache' }).then(function (r) {
      if (!r.ok) throw new Error(r.status === 404 ? 'not found' : 'HTTP ' + r.status);
      return r.json();
    });
  }

  function reportPath(type, id) { return API + '/reports/' + type + '/' + encodeURIComponent(id) + '.json'; }

  // ------------------------------------------------------------ prompts
  function buildPrompt(question, urls) {
    var lines = [
      "I'm researching Connecticut nursing homes using public data from danbeem.xyz.",
      'Read ' + (urls.length > 1 ? 'these reports' : 'this report') + ' first: ' + urls.join(' and '),
      'Guide to the data: ' + PUBLIC + '/llms.txt',
      '',
      'Question: ' + question
    ];
    if (state.names.length) {
      lines.push('');
      lines.push('I also checked these names against every dataset on the site: ' + state.names.map(function (n) {
        return n.name + (n.hits.length ? ' (found: ' + n.hits.slice(0, 3).map(function (h) { return h.type.replace(/_/g, ' ') + ' ' + h.name; }).join('; ') + ')' : ' (not found in any dataset)');
      }).join(', ') + '.');
    }
    lines.push('');
    lines.push('Rules: Answer only from the report data. For each claim, cite the dataset, reporting period and record id from its evidence. ' +
      'Keep confirmed facts, calculations, possible associations and open questions separate. ' +
      'A shared person, company or address is not proof of common ownership or a conflict of interest. ' +
      'Before saying a figure is missing, open the files under the report\'s "links" (financials, staffing, ownership, inspections); reports summarize and those files hold every year and department. ' +
      'Use the report\'s "tables" and "charts" data for numbers and charts; if you draw a chart, use only those values and name the source. ' +
      'Do not quote cost-report years or fields that data_quality marks unusable; treat "unvalidated" years as provisional. ' +
      'If something is still missing, say it is not in these datasets rather than that it does not exist. End with what to verify next.');
    return lines.join('\n');
  }

  function copyText(text, btn) {
    function done() { var t = btn.textContent; btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = t; }, 1500); }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(); });
    } else { fallback(); }
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); } catch (e) { window.prompt('Copy this prompt:', text); }
      document.body.removeChild(ta);
    }
  }

  function askButtons(container, getQuestion, urls) {
    clear(container);
    var gpt = el('a', 'btn', 'Open in ChatGPT');
    var cl = el('a', 'btn secondary', 'Open in Claude');
    var cp = el('button', 'btn secondary', 'Copy prompt');
    cp.type = 'button';
    [gpt, cl].forEach(function (a) { a.target = '_blank'; a.rel = 'noopener'; });
    function refresh() {
      var q = getQuestion();
      var p = buildPrompt(q || 'Summarize this report.', urls);
      gpt.href = 'https://chatgpt.com/?q=' + encodeURIComponent(p);
      cl.href = 'https://claude.ai/new?q=' + encodeURIComponent(p);
    }
    [gpt, cl].forEach(function (a) { a.addEventListener('mousedown', refresh); a.addEventListener('focus', refresh); a.addEventListener('click', refresh); });
    cp.addEventListener('click', function () { copyText(buildPrompt(getQuestion() || 'Summarize this report.', urls), cp); });
    refresh();
    container.appendChild(gpt); container.appendChild(cl); container.appendChild(cp);
  }

  function renderAsk(type, urls) {
    var box = $('rp-questions');
    clear(box);
    (QUESTIONS[type] || []).forEach(function (q) {
      var wrap = el('div', 'rp-q');
      wrap.appendChild(el('p', null, q));
      var row = el('div', 'rp-btnrow');
      askButtons(row, function () { return q; }, urls);
      wrap.appendChild(row);
      box.appendChild(wrap);
    });
    askButtons($('rp-custom-btns'), function () { return $('rp-custom').value.trim(); }, urls);
  }

  // ------------------------------------------------------------ render
  function fmt(v) {
    if (v === null || v === undefined) return 'not in data';
    if (typeof v === 'number') return Math.abs(v) >= 1000 ? v.toLocaleString('en-US', { maximumFractionDigits: 0 }) : String(v);
    if (Array.isArray(v)) return v.map(function (x) { return typeof x === 'object' ? (x.tag ? x.tag + ' (' + x.count + ')' : JSON.stringify(x)) : x; }).join(', ') || 'none listed';
    if (typeof v === 'object') return JSON.stringify(v);
    return String(v);
  }
  var LABELS = {
    latest_cost_year: 'Latest cost year', cost_report_check_status: 'Cost report check', resident_days: 'Resident days',
    rn_hprd: 'RN hours per resident day', total_nurse_hprd: 'Total nurse hours per resident day',
    contract_staff_pct: 'Agency share of nursing hours', agency_share_of_direct_care_pct: 'Agency share of direct care cost',
    nursing_pool_agency_cost: 'Nursing pool (agency) cost', operating_margin_nursing_home: 'Nursing home operating margin',
    raw_food_per_resident_day: 'Raw food per resident day', latest_quarter: 'Latest staffing quarter',
    actual_harm_or_ij_citations: 'Actual harm or jeopardy citations',
    dss_review_net_adjustment: 'Net change in DSS review', home_self_adjustments: 'Costs the home removed itself',
    management_fee_after_dss_review: 'Management fee after DSS review', medicaid_revenue_per_medicaid_day: 'Medicaid revenue per Medicaid day',
    medicaid_days: 'Medicaid days', medicaid_share_of_resident_days_pct: 'Medicaid share of resident days',
    reported_cost_per_resident_day: 'Reported cost per resident day (all payers, before review)'
  };
  function label(k) {
    if (LABELS[k]) return LABELS[k];
    return k.replace(/_/g, ' ').replace(/\bhprd\b/g, 'HPRD').replace(/\bct\b/g, 'CT').replace(/\bcms\b/g, 'CMS')
      .replace(/\brn\b/g, 'RN').replace(/\bij\b/g, 'jeopardy').replace(/\bpct\b/g, '(%)').replace(/^./, function (c) { return c.toUpperCase(); });
  }
  function money(v, cents) { return (v < 0 ? '-$' : '$') + Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: cents ? 2 : 0, maximumFractionDigits: cents ? 2 : 0 }); }
  // Format a metric by what it measures, not just its type: years stay bare, margins become %, dollars get $.
  function fmtMetric(k, v) {
    if (v === null || v === undefined) return 'not in data';
    if (typeof v !== 'number') return k === 'cost_report_check_status' ? String(v).replace(/_/g, ' ') : fmt(v);
    if (/(_year|_quarter)$/.test(k)) return String(v);
    if (/margin/.test(k)) return (v * 100).toFixed(1) + '%';
    if (/_pct$/.test(k)) return v.toFixed(1) + '%';
    if (/hprd/.test(k)) return v.toFixed(2);
    if (/per_(resident|medicaid)_day/.test(k)) return money(v, true);
    if (/_days$/.test(k)) return fmt(v);
    if (/(_cost|_costs|_fee_reported|_total_reported|fines_total|wages_reported|fringe_allocated|_adjustment|_adjustments|^reported$|after_dss_review|after_dss_review$)$/.test(k)) return money(v);
    return fmt(v);
  }

  function renderMetrics(m) {
    var box = $('out-metrics');
    clear(box);
    m = m || {};
    Object.keys(m).forEach(function (k) {
      if (/^statewide_median_/.test(k) && (k.replace(/^statewide_median_/, '') in m)) return;  // shown on the home's card
      var card = el('div', 'rp-metric' + (Array.isArray(m[k]) ? ' rp-metric-wide' : ''));
      card.appendChild(el('strong', null, fmtMetric(k, m[k])));
      card.appendChild(el('span', null, label(k.replace(/^statewide_median_/, 'CT median '))));
      var mk = 'statewide_median_' + k;
      if (mk in m) card.appendChild(el('span', 'rp-median', 'CT median ' + fmtMetric(k, m[mk])));
      box.appendChild(card);
    });
  }

  // ------------------------------------------------------------ charts
  var SVGNS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs) {
    var e = document.createElementNS(SVGNS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }
  function niceMax(v) {
    if (!(v > 0)) return 1;
    var p = Math.pow(10, Math.floor(Math.log10(v))), n = v / p;
    return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p;
  }
  function fmtUnit(unit, v, short) {
    if (v === null || v === undefined) return 'not in data';
    if (unit === '$') return short && v >= 1e6 ? '$' + (v / 1e6).toFixed(1) + 'M' : short && v >= 1e3 ? '$' + Math.round(v / 1e3) + 'k' : money(v);
    if (unit.indexOf('$') === 0) return money(v, !short || v < 100);
    if (unit.indexOf('%') === 0) return v.toFixed(1) + '%';
    return v.toFixed(2);
  }
  var SERIES_CLASS = { home: 'rp-s-home', benchmark: 'rp-s-bench', home_secondary: 'rp-s-alt' };

  function drawChart(c, width) {
    // Draw at the container's real width so text stays readable on phones.
    var W = Math.max(300, Math.min(640, Math.round(width || 640))), H = W < 460 ? 230 : 260, L = 58, R = 10, T = 14, B = 40;
    var all = [];
    c.series.forEach(function (s) { s.values.forEach(function (v) { if (typeof v === 'number') all.push(v); }); });
    var max = niceMax(Math.max.apply(null, all.concat([0])));
    var n = c.x.length, pw = W - L - R, ph = H - T - B;
    var root = svg('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'class': 'rp-chart-svg' });
    var home = c.series[0], bench = c.series.filter(function (s) { return s.role === 'benchmark'; })[0];
    var lastI = -1; home.values.forEach(function (v, i) { if (typeof v === 'number') lastI = i; });
    var summary = c.title + '. ' + (lastI >= 0 ? home.name + ' ' + fmtUnit(c.unit, home.values[lastI]) + ' in ' + c.x[lastI] +
      (bench && typeof bench.values[lastI] === 'number' ? ', ' + bench.name + ' ' + fmtUnit(c.unit, bench.values[lastI]) : '') + '.' : '');
    root.setAttribute('aria-label', summary);
    var y = function (v) { return T + ph - (v / max) * ph; };
    for (var g = 0; g <= 4; g++) {
      var gv = max * g / 4, gy = y(gv);
      root.appendChild(svg('line', { x1: L, x2: W - R, y1: gy, y2: gy, 'class': 'rp-grid-line' }));
      var t = svg('text', { x: L - 6, y: gy + 4, 'class': 'rp-axis', 'text-anchor': 'end' }); t.textContent = fmtUnit(c.unit, gv, true); root.appendChild(t);
    }
    var step = Math.ceil(n / Math.max(3, Math.floor((W - L - R) / 64)));
    var xc = function (i) { return L + (c.type === 'bar' ? (i + 0.5) * pw / n : (n === 1 ? pw / 2 : i * pw / (n - 1))); };
    c.x.forEach(function (lab, i) {
      if ((i % step && i !== n - 1) || (i !== n - 1 && n - 1 - i < step)) return;
      var t = svg('text', { x: xc(i), y: H - B + 18, 'class': 'rp-axis', 'text-anchor': 'middle' }); t.textContent = lab; root.appendChild(t);
    });
    if (c.type === 'bar') {
      var groupW = pw / n * 0.72, bw = groupW / c.series.length;
      c.series.forEach(function (s, si) {
        s.values.forEach(function (v, i) {
          if (typeof v !== 'number') return;
          var x0 = xc(i) - groupW / 2 + si * bw;
          var r = svg('rect', { x: x0 + 1, y: y(v), width: Math.max(bw - 2, 1), height: Math.max(T + ph - y(v), 0), rx: 2, 'class': SERIES_CLASS[s.role] || 'rp-s-home' });
          var tt = svg('title'); tt.textContent = s.name + ', ' + c.x[i] + ': ' + fmtUnit(c.unit, v); r.appendChild(tt);
          root.appendChild(r);
        });
      });
    } else {
      c.series.forEach(function (s) {
        var d = '', pen = false;
        s.values.forEach(function (v, i) {
          if (typeof v !== 'number') { pen = false; return; }
          d += (pen ? 'L' : 'M') + xc(i).toFixed(1) + ' ' + y(v).toFixed(1) + ' '; pen = true;
        });
        root.appendChild(svg('path', { d: d, fill: 'none', 'class': 'rp-line ' + (SERIES_CLASS[s.role] || 'rp-s-home') }));
        s.values.forEach(function (v, i) {
          if (typeof v !== 'number') return;
          var pt = svg('circle', { cx: xc(i), cy: y(v), r: s.role === 'benchmark' ? 2.5 : 3.5, 'class': 'rp-pt ' + (SERIES_CLASS[s.role] || 'rp-s-home') });
          var tt = svg('title'); tt.textContent = s.name + ', ' + c.x[i] + ': ' + fmtUnit(c.unit, v); pt.appendChild(tt);
          root.appendChild(pt);
        });
      });
    }
    return { node: root, summary: summary };
  }

  function chartTable(c) {
    var wrap = el('div', 'rp-table-wrap'), t = el('table', 'rp'), head = el('tr');
    head.appendChild(el('th', null, ''));
    c.series.forEach(function (s) { head.appendChild(el('th', null, s.name)); });
    var th = el('thead'); th.appendChild(head); t.appendChild(th);
    var tb = el('tbody');
    c.x.forEach(function (lab, i) {
      var tr = el('tr'); tr.appendChild(el('td', null, lab));
      c.series.forEach(function (s) { tr.appendChild(el('td', 'num', fmtUnit(c.unit, s.values[i]))); });
      tb.appendChild(tr);
    });
    t.appendChild(tb); wrap.appendChild(t); return wrap;
  }

  function renderCharts(charts) {
    var box = $('out-charts');
    clear(box);
    $('out-charts-wrap').hidden = !charts || !charts.length;
    (charts || []).forEach(function (c) {
      var fig = el('figure', 'rp-chart');
      fig.appendChild(el('figcaption', 'rp-chart-title', c.title));
      var legend = el('p', 'rp-legend');
      c.series.forEach(function (s) {
        var key = el('span', 'rp-key ' + (SERIES_CLASS[s.role] || 'rp-s-home'));
        key.setAttribute('aria-hidden', 'true');
        legend.appendChild(key); legend.appendChild(document.createTextNode(s.name + '   '));
      });
      legend.appendChild(el('span', 'rp-unit', '(' + c.unit + ')'));
      fig.appendChild(legend);
      box.appendChild(fig);
      fig.appendChild(drawChart(c, fig.clientWidth - 30).node);
      if (c.note) fig.appendChild(el('p', 'rp-hint', c.note));
      var det = el('details', 'rp-more'); det.appendChild(el('summary', null, 'Show the numbers')); det.appendChild(chartTable(c));
      fig.appendChild(det);
    });
  }

  // ------------------------------------------------------------ tables
  var COL_LABELS = {
    department: 'Department', wages_reported: 'Wages', fringe_allocated: 'Fringe (allocated)', non_wage_costs: 'Non-wage costs',
    total_department_cost: 'Total', wage_share_pct: 'Wages share', non_wage_share_pct: 'Non-wage share',
    per_resident_day: 'Per resident day', statewide_median_per_resident_day: 'CT median per resident day',
    cost_year: 'Cost year', check_status: 'Check', resident_days: 'Resident days',
    page: 'Page', line: 'Line', item: 'Item', reported: 'Reported', home_adjustment: 'Home removed',
    dss_review_adjustment: 'DSS review change', after_dss_review: 'After DSS review', moved_between_lines: 'Moved between lines'
  };
  var TABLE_SKIP = { usable: 1, note: 1 };
  function renderTables(tables) {
    var box = $('out-tables');
    clear(box);
    $('out-tables-wrap').hidden = !tables || !tables.length;
    (tables || []).forEach(function (t) {
      if (!t.rows || !t.rows.length) return;
      var cols = Object.keys(t.rows[0]).filter(function (k) { return !TABLE_SKIP[k]; });
      box.appendChild(el('h4', null, t.title));
      if (t.description) box.appendChild(el('p', 'rp-hint', t.description));
      var wrap = el('div', 'rp-table-wrap'), tab = el('table', 'rp'), hr = el('tr');
      cols.forEach(function (k) { hr.appendChild(el('th', null, COL_LABELS[k] || label(k.replace(/^statewide_median_/, 'CT median ')))); });
      var th = el('thead'); th.appendChild(hr); tab.appendChild(th);
      var tb = el('tbody');
      t.rows.forEach(function (r) {
        var tr = el('tr');
        cols.forEach(function (k) {
          var v = r[k];
          var txt = typeof v === 'boolean' ? (v ? 'yes' : '') : k === 'page' || k === 'line' || k === 'item' ? String(v === null || v === undefined ? '' : v) :
            k === 'department' || k === 'cost_year' ? String(v) : k === 'check_status' ? String(v || '') :
            k === 'resident_days' ? fmt(v) : /share_pct$/.test(k) ? (v === null || v === undefined ? 'not in data' : v.toFixed(1) + '%') :
            (v === null || v === undefined) ? (r.note && k === 'per_resident_day' ? 'not used: ' + r.note : 'not in data') : fmtMetric(k, v);
          tr.appendChild(el('td', typeof v === 'number' && k !== 'cost_year' && k !== 'page' ? 'num' : null, txt));
        });
        tb.appendChild(tr);
      });
      tab.appendChild(tb); wrap.appendChild(tab); box.appendChild(wrap);
    });
  }

  function renderFindings(findings) {
    var box = $('out-findings');
    clear(box);
    if (!findings.length) { box.appendChild(el('p', null, 'No findings for this report.')); return; }
    findings.forEach(function (f) {
      var card = el('div', 'rp-finding' + (f.severity === 'attention' ? ' attention' : ''));
      var p = el('p');
      p.appendChild(el('span', 'rp-kind ' + f.kind, KIND_LABEL[f.kind] || f.kind));
      p.appendChild(document.createTextNode(f.statement));
      card.appendChild(p);
      if (f.formula) card.appendChild(el('p', 'rp-ev', 'How calculated: ' + f.formula));
      (f.evidence || []).forEach(function (e) {
        var ev = el('p', 'rp-ev');
        ev.appendChild(document.createTextNode('Source: '));
        if (e.url) { var a = el('a', null, e.dataset); a.href = e.url; a.target = '_blank'; a.rel = 'noopener'; ev.appendChild(a); }
        else ev.appendChild(document.createTextNode(e.dataset));
        var bits = [e.agency, e.reporting_period ? 'period ' + e.reporting_period : null, e.record_id ? 'record ' + e.record_id : null,
          e.as_of ? 'as of ' + e.as_of : null, e.verification ? e.verification.replace(/_/g, ' ') : null].filter(Boolean);
        ev.appendChild(document.createTextNode(' (' + bits.join(' | ') + ')'));
        if (e.note) ev.appendChild(document.createTextNode(' ' + e.note));
        card.appendChild(ev);
      });
      box.appendChild(card);
    });
  }

  function renderRelationships(rels) {
    var body = $('out-rel');
    clear(body);
    $('out-rel-wrap').hidden = !rels || !rels.length;
    (rels || []).forEach(function (r) {
      var tr = el('tr');
      var who = r.entity_name || r.company_name || r.name || r.facility_name || '';
      if (r.ccn && r.facility_name) who = r.facility_name + ' (' + r.ccn + ')';
      tr.appendChild(el('td', null, who + (r.entity_type ? ' [' + r.entity_type + ']' : '')));
      var rel = (r.relationship_type || '').replace(/_/g, ' ');
      if (r.cms_role_verbatim) rel += ' - ' + r.cms_role_verbatim;
      tr.appendChild(el('td', null, rel + (r.current === false ? ' (past)' : r.current ? ' (current)' : '')));
      var dates = r.association_date ? 'since ' + r.association_date : (r.start || '') + (r.start ? ' to ' + (r.end || 'present') : '');
      tr.appendChild(el('td', null, dates));
      var td = el('td');
      var also = r.also_listed_at_ccns || [];
      if (also.length) {
        also.slice(0, 8).forEach(function (c, i) {
          var b = el('button', null, (byCcn[c] ? byCcn[c].facility_name : c));
          b.type = 'button'; b.className = 'linklike'; b.style.cssText = 'all:unset;cursor:pointer;text-decoration:underline;color:var(--ltcop-navy,#173761)';
          b.addEventListener('click', function () { selectFacility(c); });
          if (i) td.appendChild(document.createTextNode(', '));
          td.appendChild(b);
        });
        if (also.length > 8) td.appendChild(document.createTextNode(' and ' + (also.length - 8) + ' more'));
      } else td.textContent = '-';
      tr.appendChild(td);
      body.appendChild(tr);
    });
  }

  function listInto(id, items, fn) {
    var ul = $(id);
    clear(ul);
    if (!items || !items.length) { ul.appendChild(el('li', null, 'None listed.')); return; }
    items.forEach(function (x) { ul.appendChild(fn ? fn(x) : el('li', null, x)); });
  }

  function renderReport(rep, url) {
    state.report = rep; state.reportUrl = url;
    $('rp-output').hidden = false;
    $('out-compare').textContent = '';
    var subj = rep.subject || {};
    $('out-eyebrow').textContent = TYPE_LABEL[rep.report_type] || rep.report_type;
    $('out-title').textContent = subj.facility_name ? subj.facility_name + (subj.city ? ', ' + subj.city : '') + ' (CCN ' + subj.ccn + ')' : subj.company_name;
    $('out-meta').textContent = 'Data as of ' + rep.generated_at.slice(0, 10) + '. Public link: ' + PUBLIC + url;
    $('out-json').href = url;
    listInto('out-summary', rep.executive_summary, function (s) {
      var li = el('li');
      li.appendChild(el('span', 'rp-kind ' + s.kind, KIND_LABEL[s.kind] || s.kind));
      li.appendChild(document.createTextNode(s.text));
      return li;
    });
    renderMetrics(rep.metrics);
    renderCharts(rep.charts || []);
    renderTables(rep.tables || []);
    renderFindings(rep.findings || []);
    renderRelationships(rep.relationships);
    listInto('out-missing', (rep.missing_data || []).map(function (m) { return m.reason; }));
    listInto('out-follow', rep.recommended_follow_up);
    listInto('out-sources', rep.sources, function (s) {
      var li = el('li');
      if (s.url) { var a = el('a', null, s.dataset); a.href = s.url; a.target = '_blank'; a.rel = 'noopener'; li.appendChild(a); }
      else li.appendChild(document.createTextNode(s.dataset));
      li.appendChild(document.createTextNode(' - ' + s.agency + (s.as_of ? ', as of ' + s.as_of : '')));
      return li;
    });
    listInto('out-limits', rep.limitations);
    $('rp-namecheck-wrap').hidden = rep.report_type !== 'related-party-screening';
    renderAsk(rep.report_type, [PUBLIC + url]);
    status('');
  }

  function renderComparison(a, b, urlA, urlB) {
    renderReport(a, urlA);
    $('out-eyebrow').textContent = TYPE_LABEL['facility-comparison'];
    $('out-title').textContent = a.subject.facility_name + ' vs. ' + b.subject.facility_name;
    $('out-meta').textContent = 'Built in your browser from two full facility reports. Data as of ' + a.generated_at.slice(0, 10) + '.';
    renderCharts([]); renderTables([]);  // single-home charts would mislead in a comparison
    var box = $('out-compare');
    clear(box);
    box.appendChild(el('h3', null, 'Side by side'));
    var wrap = el('div', 'rp-table-wrap');
    var t = el('table', 'rp');
    var hr = el('tr');
    ['Measure', a.subject.facility_name, b.subject.facility_name].forEach(function (h) { hr.appendChild(el('th', null, h)); });
    var th = el('thead'); th.appendChild(hr); t.appendChild(th);
    var tb = el('tbody');
    var keys = Object.keys(a.metrics || {});
    Object.keys(b.metrics || {}).forEach(function (k) { if (keys.indexOf(k) < 0) keys.push(k); });
    keys.forEach(function (k) {
      var tr = el('tr');
      tr.appendChild(el('td', null, label(k)));
      tr.appendChild(el('td', 'num', fmt((a.metrics || {})[k])));
      tr.appendChild(el('td', 'num', fmt((b.metrics || {})[k])));
      tb.appendChild(tr);
    });
    t.appendChild(tb); wrap.appendChild(t); box.appendChild(wrap);
    box.appendChild(el('p', 'rp-hint', 'Findings below are for ' + a.subject.facility_name + '. Open the second home on its own for its findings.'));
    renderAsk('facility-comparison', [PUBLIC + urlA, PUBLIC + urlB]);
  }

  // ------------------------------------------------------------ actions
  function syncUrl() {
    var q = new URLSearchParams();
    if (state.type === 'management-company-portfolio') { if (state.company) q.set('company', state.company); }
    else if (state.ccn) q.set('ccn', state.ccn);
    q.set('type', state.type);
    if (state.type === 'facility-comparison' && state.compare) q.set('compare', state.compare);
    history.replaceState(null, '', location.pathname + '?' + q.toString());
  }

  function load() {
    syncUrl();
    var t = state.type;
    if (t === 'management-company-portfolio') {
      if (!state.company) { status('Search for a management company above.'); return; }
      var cu = reportPath(t, state.company);
      status('Loading...');
      return getJSON(cu).then(function (r) { renderReport(r, cu); }, function (e) { status('Could not load that report (' + e.message + ').'); });
    }
    if (!state.ccn) { status('Search for a home above.'); return; }
    if (t === 'facility-comparison') {
      if (!state.compare) { status('Choose a second home to compare.'); return; }
      var ua = reportPath('facility-comprehensive', state.ccn), ub = reportPath('facility-comprehensive', state.compare);
      status('Loading both reports...');
      return Promise.all([getJSON(ua), getJSON(ub)]).then(function (rs) { renderComparison(rs[0], rs[1], ua, ub); },
        function (e) { status('Could not load the reports (' + e.message + ').'); });
    }
    var u = reportPath(t, state.ccn);
    status('Loading...');
    return getJSON(u).then(function (r) { renderReport(r, u); }, function (e) { status('Could not load that report (' + e.message + ').'); });
  }

  function selectFacility(ccn) {
    state.ccn = ccn;
    if (state.type === 'management-company-portfolio') { state.type = 'facility-comprehensive'; $('rp-type').value = state.type; }
    $('rp-search').value = byCcn[ccn] ? byCcn[ccn].facility_name + ' (' + ccn + ')' : ccn;
    clear($('rp-matches'));
    load();
    var out = $('rp-output'); if (out.scrollIntoView) out.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function selectCompany(id, name) {
    state.company = id; state.type = 'management-company-portfolio'; $('rp-type').value = state.type;
    $('rp-search').value = name;
    clear($('rp-matches'));
    toggleCompare();
    load();
  }

  function ensureIndex() {
    if (searchIndex) return Promise.resolve(searchIndex);
    return getJSON(API + '/search-index.json').then(function (d) { searchIndex = d.entries; return searchIndex; });
  }

  function findEntries(q) {
    var key = norm(q);
    if (!key) return [];
    var exactCcn = /^\d{6}$/.test(q.trim()) ? q.trim() : null;
    var rank = { facility: 0, facility_alias: 1, management_company: 2, cms_owner_organization: 3, cms_owner_individual: 4, administrator: 5, cost_report_related_party: 6 };
    return searchIndex.filter(function (e) { return (exactCcn && e.id === exactCcn) || (key.length >= 3 && e.key.indexOf(key) >= 0); })
      .sort(function (a, b) {
        var pa = a.key.indexOf(key) === 0 ? 0 : 1, pb = b.key.indexOf(key) === 0 ? 0 : 1;
        return ((rank[a.type] || 9) - (rank[b.type] || 9)) || (pa - pb) || a.name.localeCompare(b.name);
      });
  }

  function onSearch() {
    var q = $('rp-search').value;
    var ul = $('rp-matches');
    clear(ul);
    if (q.trim().length < 3) return;
    ensureIndex().then(function () {
      var hits = findEntries(q);
      clear(ul);
      if (!hits.length) { ul.appendChild(el('li', null, 'No match in any dataset on this site.')); return; }
      var seen = {};
      hits.slice(0, 60).forEach(function (h) {
        var k = h.type + '|' + h.id;
        if (seen[k] || Object.keys(seen).length >= 12) return;
        seen[k] = 1;
        var li = el('li');
        if (h.type === 'facility' || h.type === 'facility_alias') {
          var b = el('button', null, (byCcn[h.id] ? byCcn[h.id].facility_name : h.name) + ' (' + h.id + ')');
          b.type = 'button'; b.addEventListener('click', function () { selectFacility(h.id); });
          li.appendChild(b);
          if (h.type === 'facility_alias') li.appendChild(document.createTextNode(' - also recorded as "' + h.name + '"'));
        } else if (h.type === 'management_company') {
          var c = el('button', null, h.name);
          c.type = 'button'; c.addEventListener('click', function () { selectCompany(h.id, h.name); });
          li.appendChild(c);
          li.appendChild(document.createTextNode(' - management company, ' + h.ccns.length + ' home(s)'));
        } else {
          li.appendChild(document.createTextNode(h.name + ' (' + h.type.replace(/_/g, ' ') + ') listed at: '));
          h.ccns.slice(0, 6).forEach(function (c, i) {
            var fb = el('button', null, byCcn[c] ? byCcn[c].facility_name : c);
            fb.type = 'button'; fb.addEventListener('click', function () { selectFacility(c); });
            if (i) li.appendChild(document.createTextNode(', '));
            li.appendChild(fb);
          });
          if (h.ccns.length > 6) li.appendChild(document.createTextNode(' and ' + (h.ccns.length - 6) + ' more'));
        }
        ul.appendChild(li);
      });
    }, function () { status('Search index could not be loaded.'); });
  }

  function checkNames() {
    var raw = $('rp-names').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    var ul = $('rp-namecheck');
    clear(ul);
    ensureIndex().then(function () {
      state.names = raw.map(function (n) {
        return { name: n, hits: findEntries(n) };
      });
      state.names.forEach(function (n) {
        var li = el('li');
        li.appendChild(el('strong', null, n.name + ': '));
        if (!n.hits.length) {
          li.appendChild(el('span', 'rp-notfound', 'Not found in any dataset on this site.'));
        } else {
          li.appendChild(el('span', 'rp-found', 'Found ' + n.hits.length + ' record(s): '));
          li.appendChild(document.createTextNode(n.hits.slice(0, 5).map(function (h) {
            return h.name + ' (' + h.type.replace(/_/g, ' ') + '; homes: ' + h.ccns.slice(0, 4).join(', ') + (h.ccns.length > 4 ? '...' : '') + ')';
          }).join('; ') + '. A name match is not proof it is the same entity.'));
        }
        ul.appendChild(li);
      });
      if (state.report) renderAsk(state.report.report_type, [PUBLIC + state.reportUrl]);
    });
  }

  function toggleCompare() {
    $('rp-compare-wrap').hidden = state.type !== 'facility-comparison';
  }

  function resolveCcn(text) {
    var m = String(text).match(/\b(\d{6})\b/);
    if (m && byCcn[m[1]]) return m[1];
    var k = norm(text);
    var hit = facilities.filter(function (f) { return norm(f.facility_name) === k; })[0];
    return hit ? hit.ccn : null;
  }

  function init() {
    var params = new URLSearchParams(location.search);
    state.ccn = params.get('ccn');
    state.compare = params.get('compare');
    state.company = params.get('company');
    var t = params.get('type');
    if (t && TYPE_LABEL[t]) state.type = t;
    else if (state.company && !state.ccn) state.type = 'management-company-portfolio';
    $('rp-type').value = state.type;
    toggleCompare();

    getJSON(API + '/facilities.json').then(function (d) {
      facilities = d.facilities;
      var dl = $('rp-facility-list');
      facilities.forEach(function (f) {
        byCcn[f.ccn] = f;
        var o = document.createElement('option');
        o.value = f.facility_name + ' (' + f.ccn + ')';
        dl.appendChild(o);
      });
      if (state.ccn && byCcn[state.ccn]) $('rp-search').value = byCcn[state.ccn].facility_name + ' (' + state.ccn + ')';
      if (state.compare && byCcn[state.compare]) $('rp-compare').value = byCcn[state.compare].facility_name + ' (' + state.compare + ')';
      if (state.ccn || state.company) load();
    }, function () { status('The report data could not be loaded. Try again later.'); });

    var timer;
    $('rp-search').addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(onSearch, 200); });
    $('rp-search').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { var c = resolveCcn(this.value); if (c) selectFacility(c); else onSearch(); }
    });
    $('rp-type').addEventListener('change', function () {
      state.type = this.value; toggleCompare();
      if (state.type !== 'related-party-screening') { state.names = []; clear($('rp-namecheck')); }
      load();
    });
    $('rp-compare').addEventListener('change', function () { state.compare = resolveCcn(this.value); load(); });
    $('rp-names-go').addEventListener('click', checkNames);
    $('rp-names').addEventListener('keydown', function (e) { if (e.key === 'Enter') checkNames(); });
    $('out-download').addEventListener('click', function () {
      if (!state.report) return;
      var blob = new Blob([JSON.stringify(state.report, null, 2)], { type: 'application/json' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      var s = state.report.subject || {};
      a.download = (state.report.report_type + '-' + (s.ccn || s.company_id || 'report') + '.json');
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    });
    $('out-copyurl').addEventListener('click', function () { copyText(location.href.replace(location.origin, PUBLIC), this); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();

  // exposed for tests
  window.__reportsPage = { norm: norm, buildPrompt: buildPrompt, state: state };
})();
