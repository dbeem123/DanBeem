(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const BASE = '/data/ct_daily_minimums/';
  const params = new URLSearchParams(location.search);
  let index, rules, quarter, data, sortKey = 'below_total', sortDesc = true, homeCcn = null;

  const fmt = (v, d = 2) => v == null ? '—' : Number(v).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
  const pct = v => v == null ? '—' : Math.round(v * 100) + '%';
  const iso = k => k.slice(0, 4) + '-' + k.slice(4, 6) + '-' + k.slice(6);
  const el = (tag, text, cls) => { const e = document.createElement(tag); if (text != null) e.textContent = text; if (cls) e.className = cls; return e; };
  const has = (flags, name) => (flags & index.flags[name].bit) !== 0;
  const ANOMALIES = ['low_outlier', 'census_jump', 'long_hours', 'high_contract'];

  async function read(url, gz) {
    const r = await fetch(url);
    if (!r.ok) throw new Error('HTTP ' + r.status + ' for ' + url);
    if (!gz) return r.json();
    const buf = await r.arrayBuffer();
    const b = new Uint8Array(buf);
    if (b[0] !== 31 || b[1] !== 139) return JSON.parse(new TextDecoder().decode(buf));
    return new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
  }

  function ruleFor(dateIso) {
    return rules.periods.find(p => p.from <= dateIso && dateIso <= p.to) || null;
  }
  function quarterRange(q) {
    const y = Number(q.slice(0, 4)), n = Number(q.slice(-1));
    const start = new Date(Date.UTC(y, (n - 1) * 3, 1)), end = new Date(Date.UTC(y, n * 3, 0));
    return [start.toISOString().slice(0, 10), end.toISOString().slice(0, 10)];
  }

  function showRule() {
    const [a, b] = quarterRange(quarter);
    const periods = rules.periods.filter(p => p.from <= b && p.to >= a);
    const box = $('dm-rule');
    box.replaceChildren(el('strong', 'Connecticut rule applied this quarter'));
    periods.forEach(p => {
      const line = el('p');
      line.append(el('strong', (periods.length > 1 ? (p.from > a ? 'From ' + p.from + ': ' : 'Until ' + (p.to < b ? p.to : b) + ': ') : '')), document.createTextNode(p.label + '. '));
      if (p.caveat) line.append(el('span', p.caveat + ' ', 'subtle'));
      p.sources.forEach((s, i) => { const link = el('a', s.label); link.href = s.url; link.rel = 'noopener'; line.append(i ? ' · ' : '', link); });
      box.append(line);
    });
    const fed = el('p', rules.federal.label + '. Days under 8 RN hours are an indicator only; the data cannot show whether hours were consecutive. ');
    fed.className = 'subtle';
    box.append(fed);
    box.hidden = false;
  }

  function showFacts() {
    const s = index.quarters[quarter];
    const facts = [
      [s.homes, 'homes reporting'],
      [s.evaluated.toLocaleString(), 'days compared'],
      [s.below_total.toLocaleString(), 'days below the minimum'],
      [s.homes_with_short_days, 'homes with at least one short day'],
      [s.rn_under_8.toLocaleString(), 'days under 8 RN hours'],
      [s.homes_suspect_reporting, 'homes with likely reporting problems'],
    ];
    $('dm-facts').replaceChildren(...facts.map(([v, label]) => { const d = el('div', null, 'dm-fact'); d.append(el('strong', String(v)), el('span', label)); return d; }));
  }

  function rows() {
    const q = ($('dm-filter').value || '').trim().toLowerCase();
    const onlyShort = $('dm-only-short').checked;
    return Object.entries(data.facilities).map(([ccn, f]) => ({
      ccn, name: index.names[ccn] || ccn, ...f.summary,
      anomalies: f.days.filter(d => ANOMALIES.some(a => has(d[9], a))).length,
    })).filter(r => (!q || r.name.toLowerCase().includes(q) || r.ccn.includes(q))
      && (!onlyShort || r.below_total > 0 || r.suspect_reporting || q));
  }

  function renderTable() {
    const list = rows().sort((a, b) => {
      const x = a[sortKey], y = b[sortKey];
      if (sortKey === 'name') return sortDesc ? y.localeCompare(x) : x.localeCompare(y);
      return ((sortDesc ? (y ?? -1) - (x ?? -1) : (x ?? 1e9) - (y ?? 1e9)) || a.name.localeCompare(b.name));
    });
    const body = $('dm-table').tBodies[0];
    body.replaceChildren(...list.map(r => {
      const tr = el('tr');
      const name = el('td'); const link = el('button', r.name, 'dm-link'); link.type = 'button';
      link.addEventListener('click', () => openHome(r.ccn, true));
      name.append(link, el('div', 'CCN ' + r.ccn + (r.suspect_reporting ? ' · likely reporting problems (' + r.implausible + ' days)' : ''), 'subtle'));
      const below = el('td', r.below_total + ' of ' + r.evaluated);
      if (r.evaluated) { const bar = el('span', null, 'dm-bar'); bar.style.width = Math.round(40 * r.below_total / r.evaluated) + 'px'; bar.setAttribute('aria-hidden', 'true'); below.append(bar); }
      tr.append(name, below, el('td', String(r.below_direct_only)), el('td', String(r.below_licensed)), el('td', String(r.rn_under_8)),
        el('td', fmt(r.mean_hprd)), el('td', r.weekend_gap == null ? '—' : pct(r.weekend_gap)), el('td', String(r.anomalies)));
      return tr;
    }));
    $('dm-status').textContent = list.length + ' homes shown for ' + quarter + '. Sorted by ' + sortLabel() + '.';
  }
  const sortLabel = () => document.querySelector(`[data-sort="${sortKey}"]`).textContent.toLowerCase();

  function dayStatus(d) {
    if (has(d[9], 'not_evaluated') || has(d[9], 'implausible')) return ['data', '?'];
    if (has(d[9], 'below_total')) return ['short', '!'];
    if (has(d[9], 'below_direct_only')) return ['maybe', '~'];
    return ['ok', ''];
  }
  function describe(d, brief) {
    return Object.entries(index.flags).filter(([name]) => has(d[9], name)).map(([, f]) => brief ? (f.short || f.label) : f.label);
  }

  function renderCalendar(f) {
    const byDate = new Map(f.days.map(d => [d[0], d]));
    const [a] = quarterRange(quarter);
    const months = [];
    for (let m = 0; m < 3; m++) {
      const first = new Date(a + 'T00:00:00Z'); first.setUTCMonth(first.getUTCMonth() + m);
      const box = el('div', null, 'dm-month');
      box.append(el('h4', first.toLocaleDateString('en-US', {month: 'long', year: 'numeric', timeZone: 'UTC'})));
      const grid = el('div', null, 'dm-grid');
      ['S', 'M', 'T', 'W', 'T', 'F', 'S'].forEach(x => grid.append(el('div', x, 'dow')));
      for (let i = 0; i < first.getUTCDay(); i++) grid.append(el('span', null, 'dm-day none'));
      const days = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
      for (let n = 1; n <= days; n++) {
        const key = first.toISOString().slice(0, 8).replace(/-/g, '') + String(n).padStart(2, '0');
        const d = byDate.get(key);
        if (!d) { const blank = el('span', String(n), 'dm-day none'); blank.title = iso(key) + ': not reported'; grid.append(blank); continue; }
        const [cls, mark] = dayStatus(d);
        const cell = el('button', null, 'dm-day ' + cls + (ANOMALIES.some(x => has(d[9], x)) ? ' anomaly' : ''));
        cell.type = 'button';
        cell.append(document.createTextNode(String(n)), el('b', mark || (d[2] != null ? fmt(d[2], 1) : '')));
        const text = iso(key) + ': ' + (d[2] == null ? 'not compared' : fmt(d[2]) + ' nursing hours per resident') + (describe(d).length ? '. ' + describe(d).join('; ') : '');
        cell.title = text; cell.setAttribute('aria-label', text);
        cell.addEventListener('click', () => showDay(d));
        grid.append(cell);
      }
      box.append(grid); months.push(box);
    }
    $('dm-calendar').replaceChildren(...months);
  }

  function showDay(d) {
    const box = $('dm-day-detail');
    const rule = ruleFor(iso(d[0]));
    const p = el('p');
    p.append(el('strong', iso(d[0]) + ': '));
    if (d[2] == null) p.append(document.createTextNode('not compared. ' + describe(d).join('; ')));
    else {
      p.append(document.createTextNode(`${d[1]} residents; ${fmt(d[2])} nursing hours per resident (${fmt(d[3])} direct care, ${fmt(d[4])} licensed, ${fmt(d[5])} aide); ${fmt(d[6], 1)} RN hours; ${pct(d[7])} contract` + (d[8] != null ? `; ${fmt(d[8], 1)} hours per nursing worker` : '') + '. '));
      if (rule) p.append(document.createTextNode('Rule that day: ' + rule.label + '. '));
      if (describe(d).length) p.append(el('strong', describe(d).join('; ') + '.'));
    }
    const link = el('a', 'See every position that day in the Facility Explorer');
    link.href = `/staffing/tools/nursing-home-staffing-explorer.html?ccn=${homeCcn}&day=${iso(d[0])}`;
    box.replaceChildren(p, link);
  }

  function renderDays(f) {
    const flagged = f.days.filter(d => d[9] && d[9] !== index.flags.below_direct_only.bit);
    const body = $('dm-days').tBodies[0];
    if (!flagged.length) { const tr = el('tr'); const td = el('td', 'No days stand out this quarter.'); td.colSpan = 10; tr.append(td); body.replaceChildren(tr); return; }
    body.replaceChildren(...flagged.map(d => {
      const tr = el('tr');
      const date = el('td'); const b = el('button', iso(d[0]), 'dm-link'); b.type = 'button'; b.addEventListener('click', () => showDay(d)); date.append(b);
      tr.append(date, el('td', d[1] == null ? '—' : String(d[1])), el('td', fmt(d[2])), el('td', fmt(d[3])), el('td', fmt(d[4])), el('td', fmt(d[5])),
        el('td', fmt(d[6], 1)), el('td', pct(d[7])), el('td', fmt(d[8], 1)), el('td', describe(d, true).join(' · '), 'flags'));
      return tr;
    }));
  }

  function openHome(ccn, scroll) {
    const f = data.facilities[ccn];
    if (!f) { $('dm-home').hidden = true; return; }
    homeCcn = ccn;
    const s = f.summary;
    $('home-title').textContent = (index.names[ccn] || ccn) + ' · ' + quarter;
    $('dm-home-summary').textContent = `CCN ${ccn}. ${s.below_total} of ${s.evaluated} compared days below the Connecticut minimum; ${s.rn_under_8} days under 8 RN hours; average ${fmt(s.mean_hprd)} nursing hours per resident (weekdays ${fmt(s.weekday_hprd)}, weekends ${fmt(s.weekend_hprd)}); lowest day ${s.worst_day ? iso(s.worst_day) : '—'} at ${fmt(s.min_hprd)}.` + (s.suspect_reporting ? ' Most days look like incomplete payroll reporting, so treat this quarter with caution.' : '');
    $('dm-explorer').href = '/staffing/tools/nursing-home-staffing-explorer.html?ccn=' + ccn;
    renderCalendar(f); renderDays(f); $('dm-day-detail').replaceChildren();
    $('dm-home').hidden = false;
    updateUrl();
    if (scroll) $('dm-home').scrollIntoView({behavior: 'smooth', block: 'start'});
  }

  function csv() {
    const f = data.facilities[homeCcn];
    const head = ['date', 'residents', 'nursing_hprd', 'direct_care_hprd', 'licensed_hprd', 'aide_hprd', 'rn_hours', 'contract_share', 'hours_per_nursing_worker', 'flags'];
    const lines = [head.join(',')].concat(f.days.map(d => [iso(d[0]), ...d.slice(1, 9).map(v => v ?? ''), '"' + describe(d).join('; ').replace(/"/g, '""') + '"'].join(',')));
    const url = URL.createObjectURL(new Blob([lines.join('\n') + '\n'], {type: 'text/csv'}));
    const a = el('a'); a.href = url; a.download = `ct-daily-minimums-${homeCcn}-${quarter}.csv`; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function updateUrl() {
    const p = new URLSearchParams();
    p.set('quarter', quarter);
    if (homeCcn) p.set('ccn', homeCcn);
    history.replaceState(null, '', '?' + p.toString());
  }

  async function loadQuarter(q) {
    quarter = q;
    $('dm-status').textContent = 'Loading ' + q + '…';
    data = await read(BASE + q + '.json.gz', true);
    showRule(); showFacts(); renderTable();
    if (homeCcn && data.facilities[homeCcn]) openHome(homeCcn, false); else { $('dm-home').hidden = true; homeCcn = null; updateUrl(); }
  }

  async function init() {
    try {
      [index, rules] = await Promise.all([read(BASE + 'index.json'), read('/data/ct_staffing_minimum_rules.json')]);
      const quarters = Object.keys(index.quarters).sort().reverse();
      $('dm-quarter').replaceChildren(...quarters.map(q => new Option(q, q)));
      const wanted = params.get('quarter');
      $('dm-quarter').value = quarters.includes(wanted) ? wanted : quarters[0];
      homeCcn = params.get('ccn');
      const src = $('dm-sources');
      src.append(el('strong', 'Notes: '));
      rules.notes.forEach(n => src.append(el('p', n)));
      $('dm-quarter').addEventListener('change', e => loadQuarter(e.target.value));
      $('dm-filter').addEventListener('input', renderTable);
      $('dm-only-short').addEventListener('change', renderTable);
      $('dm-csv').addEventListener('click', csv);
      document.querySelectorAll('[data-sort]').forEach(btn => btn.addEventListener('click', () => {
        const key = btn.dataset.sort;
        sortDesc = key === sortKey ? !sortDesc : key !== 'name';
        sortKey = key; renderTable();
      }));
      await loadQuarter($('dm-quarter').value);
    } catch (err) {
      $('dm-status').textContent = 'Could not load the daily comparison data: ' + err.message;
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
