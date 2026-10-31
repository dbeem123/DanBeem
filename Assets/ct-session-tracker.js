/* Session bill tracker (one page per session, e.g. /legislation/2026/).
   Reads the file named in <main data-session-file>, so a 2027 page only needs a new data file. */
(function () {
  'use strict';

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (v === null || v === undefined || v === false) return;
      if (k === 'text') node.textContent = v;
      else if (k === 'className') node.className = v;
      else node.setAttribute(k, v);
    });
    (children || []).forEach((c) => { if (c !== null && c !== undefined && c !== '') node.append(c); });
    return node;
  }
  const link = (href, text) => el('a', { href, text });
  function parseDate(iso) { const [y, m, d] = iso.split('-').map(Number); return new Date(y, m - 1, d); }
  function niceDate(iso) {
    return iso ? parseDate(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';
  }
  const billNumber = (b) => Number(b.bill.split(' ')[1]);
  const isFinal = (data) => data.report.final === true || /final/i.test(data.report.label || '');

  async function load(url) {
    if (window.DanBeemData && typeof window.DanBeemData.loadJson === 'function') return window.DanBeemData.loadJson(url);
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(`Failed to load ${url}: ${r.status}`);
    return r.json();
  }

  function stageOf(data, id) { return (data.statuses.find((s) => s.id === id) || { stage: -1 }).stage; }
  function statusPill(data, id) {
    const st = data.statuses.find((s) => s.id === id) || { label: id };
    return el('span', { className: `status-pill status-${id}`, title: st.detail || '', text: st.label });
  }

  function renderHeader(data) {
    const s = data.session, r = data.report;
    document.getElementById('report-pill').textContent = `${s.year} Session · ${r.label}`;
    document.getElementById('disclaimer').textContent = data.disclaimer;
    document.title = `${s.year} Long-Term Care Bill Tracker | Connecticut LTCOP`;
    document.getElementById('st-title').textContent = `${s.year} Long-Term Care Bill Tracker`;
  }

  function renderFunnel(data) {
    const bills = data.bills, n = bills.length;
    const atLeast = (stage) => bills.filter((b) => stageOf(data, b.status) >= stage).length;
    const steps = [
      ['Bills tracked', n, 'on the Program\'s list'],
      ['Public hearing', atLeast(1), 'heard in committee'],
      ['Passed committee', atLeast(2), 'joint favorable report'],
      ['Passed a chamber', atLeast(3), 'House or Senate'],
      ['Became law', bills.filter((b) => b.status === 'signed').length, 'public or special act'],
    ];
    document.getElementById('funnel').replaceChildren(...steps.map(([label, value, sub]) => el('div', { className: 'summary-card funnel-card' }, [
      el('span', { className: 'summary-label', text: label }),
      el('strong', { text: String(value) }),
      el('div', { className: 'microcopy', text: n ? `${sub} · ${Math.round((value / n) * 100)}%` : sub }),
      el('div', { className: 'funnel-bar', 'aria-hidden': 'true' }, [el('i', { style: `width:${n ? (value / n) * 100 : 0}%` })]),
    ])));
    const s = data.session;
    const vetoed = bills.filter((b) => b.status === 'vetoed').length;
    const head = `${s.type}, ${niceDate(s.convenes)} to ${niceDate(s.adjourns)}. ${data.report.label}; statuses as of ${niceDate(data.report.status_as_of)}. `;
    document.getElementById('summary-note').textContent = isFinal(data)
      ? head + `${vetoed ? `${vetoed} vetoed. ` : 'No tracked bill was vetoed. '}Every bill not signed ended without becoming law when the session adjourned.`
      : head + (n ? 'Counts change as bills move; check each bill\'s status page for the latest action.' : (data.report.empty_note || 'No bills have been added yet.'));
  }

  function filters() {
    return {
      q: document.getElementById('f-search').value.trim().toLowerCase(),
      list: document.getElementById('f-list').value,
      status: document.getElementById('f-status').value,
      committee: document.getElementById('f-committee').value,
    };
  }

  function sortBills(data, rows) {
    return rows.slice().sort((a, b) => stageOf(data, b.status) - stageOf(data, a.status)
      || (a.status === 'vetoed') - (b.status === 'vetoed')
      || a.bill.slice(0, 2).localeCompare(b.bill.slice(0, 2)) || billNumber(a) - billNumber(b));
  }

  function renderBills(data) {
    const f = filters();
    const match = (b) => (f.list === 'all' || String(b.list) === f.list)
      && (f.status === 'all' || b.status === f.status)
      && (f.committee === 'all' || b.committee === f.committee)
      && (!f.q || [b.bill, b.title, b.summary, b.committee, b.public_act].join(' ').toLowerCase().includes(f.q));
    if (!data.bills.length) {
      document.getElementById('result-note').textContent = 'No bills yet.';
      document.getElementById('bill-lists').replaceChildren(el('p', { className: 'empty', text: data.report.empty_note || 'No bills have been added yet.' }));
      return;
    }
    const shown = data.bills.filter(match);
    document.getElementById('result-note').textContent = `${shown.length} of ${data.bills.length} bills shown.`;
    const blocks = data.lists.map((list) => {
      const rows = sortBills(data, shown.filter((b) => b.list === list.id));
      if (!rows.length) return null;
      const body = rows.map((b) => el('tr', {}, [
        el('th', { scope: 'row' }, [link(b.bill_status_url, b.bill), b.public_act ? el('span', { className: 'act', text: b.public_act }) : '']),
        el('td', {}, [el('div', { text: b.summary }), el('span', { className: 'tag', text: b.committee })]),
        el('td', {}, [statusPill(data, b.status)]),
        el('td', {}, [el('div', { text: b.latest_action }), b.latest_action_date ? el('div', { className: 'microcopy', text: niceDate(b.latest_action_date) }) : '']),
      ]));
      const signed = rows.filter((b) => b.status === 'signed').length;
      const table = el('table', { className: 'stack' }, [
        el('caption', { text: `${list.name}: ${list.description} (${rows.length} bills, ${signed} became law)` }),
        el('thead', {}, [el('tr', {}, ['Bill', "What it's about", 'Status', 'Latest action'].map((h) => el('th', { scope: 'col', text: h })))]),
        el('tbody', {}, body)]);
      return el('div', { className: 'list-block', id: `list-${list.id}` }, [el('div', { className: 'table-scroll' }, [table])]);
    }).filter(Boolean);
    document.getElementById('bill-lists').replaceChildren(...(blocks.length ? blocks : [el('p', { className: 'empty', text: 'No bills match these filters.' })]));
  }

  function renderEnacted(data) {
    const items = data.also_enacted || [];
    const box = document.getElementById('also-enacted');
    if (!items.length) { box.replaceChildren(el('p', { className: 'empty', text: isFinal(data) ? 'None identified.' : 'Added after the session ends.' })); return; }
    const table = el('table', { className: 'stack' }, [
      el('thead', {}, [el('tr', {}, ['Act', 'Bill', 'What it means for residents'].map((h) => el('th', { scope: 'col', text: h })))]),
      el('tbody', {}, items.map((x) => el('tr', {}, [
        el('th', { scope: 'row', text: x.act }),
        el('td', {}, [link(x.bill_status_url, x.bill), el('div', { className: 'microcopy', text: x.label })]),
        el('td', { text: x.summary }),
      ])))]);
    box.replaceChildren(el('div', { className: 'table-scroll' }, [table]));
  }

  function renderAbout(data) {
    const legend = el('table', {}, [
      el('thead', {}, [el('tr', {}, ['Status', 'What it means'].map((h) => el('th', { scope: 'col', text: h })))]),
      el('tbody', {}, data.statuses.map((s) => el('tr', {}, [el('th', { scope: 'row' }, [statusPill(data, s.id)]), el('td', { text: s.detail })])))]);
    document.getElementById('about').replaceChildren(
      el('div', { className: 'table-scroll' }, [legend]),
      el('p', { className: 'subtle', text: data.report.basis }),
      el('p', { className: 'subtle' }, [document.createTextNode('Lists follow the Program\'s tracker: '),
        ...data.lists.flatMap((l, i) => [i ? '; ' : '', el('strong', { text: l.name }), document.createTextNode(`: ${l.description}`)]), '.']),
      el('ul', { className: 'fact-list' }, data.sources.map((s) => el('li', {}, [link(s.url, s.title)]))));
  }

  function csv(data) {
    const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const listName = (id) => (data.lists.find((l) => l.id === id) || {}).name || id;
    const label = (id) => (data.statuses.find((s) => s.id === id) || {}).label || id;
    const lines = [['session', 'list', 'bill', 'status', 'public_act', 'latest_action', 'latest_action_date', 'committee', 'summary', 'official_title', 'bill_status_url'].join(',')];
    sortBills(data, data.bills).forEach((b) => lines.push([data.session.year, listName(b.list), b.bill, label(b.status), b.public_act, b.latest_action,
      b.latest_action_date, b.committee, b.summary, b.title, b.bill_status_url].map(esc).join(',')));
    const url = URL.createObjectURL(new Blob([lines.join('\r\n')], { type: 'text/csv' }));
    const a = el('a', { href: url, download: `ct-ltcop-bill-tracker-${data.session.year}.csv` });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function init() {
    const main = document.getElementById('main-content');
    let data;
    try {
      data = await load(main.getAttribute('data-session-file'));
    } catch (error) {
      document.getElementById('summary-note').replaceChildren(el('span', { className: 'notice error', text: `The tracker data could not be loaded (${error.message}).` }));
      return;
    }
    const fill = (id, opts) => opts.forEach(([v, t]) => document.getElementById(id).append(el('option', { value: v, text: t })));
    fill('f-list', data.lists.map((l) => [String(l.id), `${l.name}: ${l.description}`]));
    fill('f-status', data.statuses.filter((s) => data.bills.some((b) => b.status === s.id)).map((s) => [s.id, s.label]));
    fill('f-committee', [...new Set(data.bills.map((b) => b.committee))].sort().map((c) => [c, c]));
    [renderHeader, renderFunnel, renderBills, renderEnacted, renderAbout].forEach((step) => {
      try { step(data); } catch (error) { console.error('Session tracker render failed', error); }
    });
    ['f-search', 'f-list', 'f-status', 'f-committee'].forEach((id) => document.getElementById(id).addEventListener('input', () => renderBills(data)));
    document.getElementById('download-csv').addEventListener('click', () => csv(data));
    document.getElementById('print-page').addEventListener('click', () => window.print());
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
