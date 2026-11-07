/* Connecticut Staffing Rules & Context page. Reads one small generated export; no other requests. */
(function () {
  'use strict';
  const DATA_URL = '/data/nursing_home_ct_statewide_context.json';

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (v === null || v === undefined) return;
      if (k === 'text') node.textContent = v;
      else if (k === 'className') node.className = v;
      else node.setAttribute(k, v);
    });
    (children || []).forEach((c) => node.append(c));
    return node;
  }
  const fmt2 = (v) => (v === null || v === undefined ? 'Unavailable' : Number(v).toFixed(2));
  const pct = (v) => (v === null || v === undefined ? '' : `${Math.round(v * 100)}%`);
  const qLabel = (q) => `Q${q.slice(5)} ${q.slice(0, 4)}`;

  function card(label, value, sub) {
    return el('div', { className: 'summary-card' }, [
      el('span', { className: 'summary-label', text: label }),
      el('strong', { text: value }),
      sub ? el('div', { className: 'summary-sub', text: sub }) : '',
    ]);
  }

  function renderSnapshot(data) {
    const latest = data.statewide_quarterly[data.statewide_quarterly.length - 1];
    const first = data.statewide_quarterly.find((r) => r.ct_comparison_applicable_for_public_status);
    const prev = data.statewide_quarterly[data.statewide_quarterly.length - 2];
    // A quarter where many homes did not submit PBJ makes counts look better than they are: say so.
    const gap = prev && latest.facilities_reporting < 0.95 * prev.facilities_reporting
      ? ` Fewer homes reported than in ${prev.quarter_label} (${prev.facilities_reporting}); homes that did not submit payroll data are missing, so these counts are not comparable with earlier quarters.`
      : '';
    document.getElementById('snapshot-note').textContent =
      `${latest.quarter_label} PBJ, ${latest.facilities_reporting} reporting Connecticut facilities.${gap} ${data.screening_note}`;
    const box = document.getElementById('snapshot-cards');
    box.replaceChildren(
      card('Median CT direct-care estimate', fmt2(latest.median_ct_direct_care_total_hprd), 'hours per resident day'),
      card('Below 3.00 total', String(latest.below_total_3_00_count), `${pct(latest.below_total_3_00_share)} of reporting facilities`),
      card('Below 0.84 licensed', String(latest.below_licensed_0_84_count), 'screening estimate'),
      first ? card(`Below 3.00 in ${first.quarter_label}`, String(first.below_total_3_00_count),
        'first full quarter the standard applied') : ''
    );
  }

  function renderChart(data) {
    const rows = data.statewide_quarterly.filter((r) => r.median_ct_direct_care_total_hprd !== null);
    const W = 760, H = 300, L = 46, R = 14, T = 16, B = 44;
    const values = rows.map((r) => r.median_ct_direct_care_total_hprd);
    const yMin = Math.min(2.8, Math.floor(Math.min(...values) * 10) / 10);
    const yMax = Math.max(3.8, Math.ceil(Math.max(...values) * 10) / 10);
    const n = rows.length;
    const x = (i) => L + (n === 1 ? 0 : (i * (W - L - R)) / (n - 1));
    const y = (v) => T + ((yMax - v) * (H - T - B)) / (yMax - yMin);
    const NS = 'http://www.w3.org/2000/svg';
    const s = (tag, attrs, text) => {
      const node = document.createElementNS(NS, tag);
      Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
      if (text) node.textContent = text;
      return node;
    };
    const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true', focusable: 'false' });
    const step = (W - L - R) / Math.max(1, n - 1);
    const lastNoStatus = rows.reduce((acc, r, i) => (r.ct_comparison_applicable_for_public_status ? acc : i), -1);
    if (lastNoStatus >= 0) {
      svg.append(s('rect', { x: L, y: T, width: Math.max(0, x(lastNoStatus) + step / 2 - L), height: H - T - B, fill: '#eef2f7' }));
    }
    for (let v = Math.ceil(yMin * 10) / 10; v <= yMax + 1e-9; v += 0.2) {
      const yy = y(v);
      svg.append(s('line', { x1: L, x2: W - R, y1: yy, y2: yy, stroke: '#e3e9f2', 'stroke-width': 1 }));
      svg.append(s('text', { x: L - 6, y: yy + 4, 'text-anchor': 'end', 'font-size': 11, fill: '#5f6f85' }, v.toFixed(1)));
    }
    svg.append(s('line', { x1: L, x2: W - R, y1: y(3), y2: y(3), stroke: '#5f6f85', 'stroke-width': 1.5, 'stroke-dasharray': '6 4' }));
    svg.append(s('text', { x: W - R, y: y(3) + 14, 'text-anchor': 'end', 'font-size': 11, fill: '#5f6f85' }, '3.00'));
    rows.forEach((r, i) => {
      if (r.quarter.endsWith('Q1')) {
        svg.append(s('text', { x: x(i), y: H - B + 18, 'text-anchor': 'middle', 'font-size': 11, fill: '#5f6f85' }, r.quarter.slice(0, 4)));
      }
    });
    const markers = [
      { quarter: '2023Q1', offset: 2 / 3, label: 'Mar 2023' },
      { quarter: '2024Q1', offset: 0.05, label: 'Jan 2024' },
    ];
    markers.forEach((m, k) => {
      const i = rows.findIndex((r) => r.quarter === m.quarter);
      if (i < 0) return;
      const xx = x(i) - step / 2 + m.offset * step;
      svg.append(s('line', { x1: xx, x2: xx, y1: T, y2: H - B, stroke: '#e3212b', 'stroke-width': 1.5 }));
      svg.append(s('text', { x: xx + (k ? 4 : -4), y: T + 12, 'text-anchor': k ? 'start' : 'end', 'font-size': 11, 'font-weight': 700, fill: '#b91c1c' }, m.label));
    });
    const d = rows.map((r, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(r.median_ct_direct_care_total_hprd).toFixed(1)}`).join(' ');
    svg.append(s('path', { d, fill: 'none', stroke: '#173761', 'stroke-width': 2.5, 'stroke-linejoin': 'round' }));
    rows.forEach((r, i) => {
      const dot = s('circle', { cx: x(i), cy: y(r.median_ct_direct_care_total_hprd), r: 3, fill: '#173761' });
      dot.append(s('title', {}, `${r.quarter_label}: median ${fmt2(r.median_ct_direct_care_total_hprd)} (${r.facilities_reporting} facilities)`));
      svg.append(dot);
    });
    svg.append(s('text', { x: L, y: H - 6, 'font-size': 11, fill: '#5f6f85' }, 'Hours per resident day, PBJ-derived CT direct-care estimate'));
    document.getElementById('trend-chart').replaceChildren(svg);
  }

  function renderApplicableTable(data) {
    const rows = data.statewide_quarterly.filter((r) => r.ct_comparison_applicable_for_public_status);
    const body = rows.map((r) => el('tr', {}, [
      el('th', { scope: 'row', text: r.quarter_label }),
      el('td', { className: 'num', text: String(r.facilities_reporting) }),
      el('td', { className: 'num', text: fmt2(r.median_ct_direct_care_total_hprd) }),
      el('td', { className: 'num', text: `${r.below_total_3_00_count} (${pct(r.below_total_3_00_share)})` }),
      el('td', { className: 'num', text: String(r.below_licensed_0_84_count) }),
    ]));
    const table = el('table', {}, [
      el('caption', { text: 'Quarters with CT comparison status (Q2 2023 onward)' }),
      el('thead', {}, [el('tr', {}, [
        el('th', { scope: 'col', text: 'Quarter' }),
        el('th', { scope: 'col', className: 'num', text: 'Facilities' }),
        el('th', { scope: 'col', className: 'num', text: 'Median estimate' }),
        el('th', { scope: 'col', className: 'num', text: 'Below 3.00' }),
        el('th', { scope: 'col', className: 'num', text: 'Below 0.84' }),
      ])]),
      el('tbody', {}, body.reverse()),
    ]);
    document.getElementById('applicable-table').replaceChildren(el('div', { className: 'table-scroll' }, [table]));
  }

  function renderScenarios(data) {
    const sc = data.latest_quarter_scenarios;
    const tags = { current: 'Current', proposed: 'Proposed, not enacted', hypothetical: 'Hypothetical' };
    const body = sc.levels.map((lv) => el('tr', { className: `kind-${lv.kind}` }, [
      el('th', { scope: 'row' }, [document.createTextNode(lv.hprd.toFixed(2)), el('span', { className: 'tag', text: tags[lv.kind] || lv.kind })]),
      el('td', { text: lv.label }),
      el('td', { className: 'num', text: `${lv.facilities_below} of ${lv.facilities_with_estimate}` }),
      el('td', {}, [el('div', { className: 'bar', title: pct(lv.share_below) }, [el('i', { style: `width:${(lv.share_below * 100).toFixed(1)}%` })])]),
      el('td', { className: 'num', text: pct(lv.share_below) }),
    ]));
    const table = el('table', {}, [
      el('caption', { text: `${qLabel(sc.quarter)}: facilities whose CT direct-care estimate is below each level` }),
      el('thead', {}, [el('tr', {}, [
        el('th', { scope: 'col', text: 'Level (HPRD)' }),
        el('th', { scope: 'col', text: 'What it is' }),
        el('th', { scope: 'col', className: 'num', text: 'Facilities below' }),
        el('th', { scope: 'col', text: 'Share' }),
        el('th', { scope: 'col', className: 'num', text: '%' }),
      ])]),
      el('tbody', {}, body),
    ]);
    document.getElementById('scenario-table').replaceChildren(el('div', { className: 'table-scroll' }, [table]));
    const proposed = (data.policy_reference.legislation || []).find((b) => b.bill === 'SB 1279');
    const note = document.getElementById('legislation-note');
    note.replaceChildren();
    if (proposed) {
      note.append(document.createTextNode(`${proposed.session} ${proposed.bill}: ${proposed.summary} ${proposed.status} `));
      note.append(el('a', { href: proposed.source_url, text: proposed.source_title }));
      note.append(document.createTextNode('. See the legislation list below for other bills.'));
    }
  }

  function renderLegislation(data) {
    const bills = (data.policy_reference.legislation || []).slice()
      .sort((a, b) => String(b.session).localeCompare(String(a.session)));
    const rows = bills.map((b) => el('tr', {}, [
      el('th', { scope: 'row', text: `${b.session} ${b.bill}` }),
      el('td', {}, [el('strong', { text: b.title }), el('div', { className: 'microcopy', text: b.summary })]),
      el('td', {}, [document.createTextNode(`${b.status} `), el('a', { href: b.source_url, text: 'Bill status' })]),
    ]));
    const table = el('table', {}, [
      el('caption', { text: 'Connecticut nursing home staffing and finance bills tracked here' }),
      el('thead', {}, [el('tr', {}, [
        el('th', { scope: 'col', text: 'Bill' }),
        el('th', { scope: 'col', text: 'What it would do' }),
        el('th', { scope: 'col', text: 'Status' }),
      ])]),
      el('tbody', {}, rows),
    ]);
    const box = document.getElementById('legislation-table');
    box.replaceChildren(el('div', { className: 'table-scroll' }, [table]));
    if (data.policy_reference.legislation_note) {
      box.append(el('p', { className: 'microcopy', text: data.policy_reference.legislation_note }));
    }
  }

  function renderAcuity(data) {
    const cmi = data.policy_reference.dss_case_mix;
    document.getElementById('acuity-note').textContent = cmi.note;
    const rows = cmi.quarters.slice().reverse().map((r) => el('tr', {}, [
      el('th', { scope: 'row', text: qLabel(r.quarter) }),
      el('td', { className: 'num', text: r.medicaid_cmi.toFixed(4) }),
      el('td', { className: 'num', text: r.total_cmi.toFixed(4) }),
    ]));
    const first = cmi.quarters[0], last = cmi.quarters[cmi.quarters.length - 1];
    const change = ((last.medicaid_cmi / first.medicaid_cmi - 1) * 100).toFixed(1);
    const table = el('table', {}, [
      el('caption', { text: `Statewide averages. Medicaid CMI ${qLabel(first.quarter)} to ${qLabel(last.quarter)}: ${change > 0 ? '+' : ''}${change}%` }),
      el('thead', {}, [el('tr', {}, [
        el('th', { scope: 'col', text: 'Quarter' }),
        el('th', { scope: 'col', className: 'num', text: 'Medicaid CMI' }),
        el('th', { scope: 'col', className: 'num', text: 'All payers CMI' }),
      ])]),
      el('tbody', {}, rows),
    ]);
    document.getElementById('acuity-table').replaceChildren(
      el('div', { className: 'table-scroll' }, [table]),
      el('p', { className: 'src' }, [document.createTextNode('Source: '), el('a', { href: cmi.source_url, text: cmi.source_title })])
    );
  }

  function renderWorkforce(data) {
    const items = data.policy_reference.workforce_context || [];
    document.getElementById('workforce-cards').replaceChildren(...items.map((it) => el('article', { className: 'card' }, [
      el('h3', { text: it.label }),
      el('p', { text: it.detail }),
      el('p', { className: 'src' }, [document.createTextNode('Source: '), el('a', { href: it.source_url, text: it.source_title })]),
    ])));
  }

  function renderSources(data) {
    const ref = data.policy_reference;
    const seen = new Map();
    [...(ref.rule_timeline || []), ...(ref.legislation || []), ...(ref.workforce_context || []), ref.dss_case_mix]
      .forEach((x) => { if (x && x.source_url && !seen.has(x.source_url)) seen.set(x.source_url, x.source_title); });
    const list = document.getElementById('source-list');
    list.replaceChildren(...[...seen].map(([url, title]) => el('li', {}, [el('a', { href: url, text: title })])));
    list.append(el('li', { text: `Connecticut policy reference last verified ${ref.last_verified}. Statewide export generated ${data.generated_at.slice(0, 10)} from PBJ history generated ${String(data.source_history_generated_at).slice(0, 10)}.` }));
  }

  function renderTimeline(data) {
    const items = data.policy_reference.rule_timeline || [];
    if (!items.length) return;
    document.getElementById('rules-timeline').replaceChildren(...items.map((it) => el('li', {}, [
      el('div', { className: 'when', text: it.date_label || (it.date === 'pre-2022' ? 'Before 2022' : it.date) }),
      el('div', { className: 'what' }, [
        el('strong', { text: it.label }),
        el('p', { text: it.detail }),
        el('div', { className: 'src' }, [document.createTextNode('Source: '), el('a', { href: it.source_url, text: it.source_title })]),
      ]),
    ])));
  }

  function fail(message) {
    const note = document.getElementById('snapshot-note');
    note.replaceChildren(el('span', { className: 'notice error', text: message }));
  }

  async function init() {
    let data;
    try {
      if (window.DanBeemData && typeof window.DanBeemData.loadJson === 'function') {
        data = await window.DanBeemData.loadJson(DATA_URL);
      } else {
        const response = await fetch(DATA_URL, { cache: 'no-cache' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        data = await response.json();
      }
    } catch (error) {
      fail(`The Connecticut statewide context export could not be loaded (${error.message}).`);
      return;
    }
    const steps = [renderSnapshot, renderTimeline, renderChart, renderApplicableTable, renderScenarios, renderLegislation, renderAcuity, renderWorkforce, renderSources];
    steps.forEach((step) => {
      try { step(data); } catch (error) { console.error(`CT context: ${step.name} failed`, error); }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
