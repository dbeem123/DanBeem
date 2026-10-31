/* Connecticut Long-Term Care Legislative Tracker. Reads two /data files through the shared loader. */
(function () {
  'use strict';
  const TRACKER_URL = '/data/ct_ltcop_legislative_tracker.json';
  const STATS_URL = '/data/ct_legislative_research_stats.json';
  const DAY = 86400000;

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
    if (!iso) return '';
    return parseDate(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
  function today() { const t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate()); }

  async function load(url) {
    if (window.DanBeemData && typeof window.DanBeemData.loadJson === 'function') return window.DanBeemData.loadJson(url);
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(`Failed to load ${url}: ${r.status}`);
    return r.json();
  }

  let toastTimer;
  function toast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
  }
  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast('Copied with source');
    } catch (_) {
      const area = el('textarea', { 'aria-label': 'Copy this text' });
      area.value = text;
      document.body.append(area);
      area.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
      area.remove();
      toast(ok ? 'Copied with source' : 'Copy failed. Select the text and copy it.');
    }
  }

  function renderSession(data) {
    const s = data.session;
    const start = parseDate(s.convenes), end = parseDate(s.adjourns), now = today();
    let headline, sub;
    if (now < start) {
      const days = Math.round((start - now) / DAY);
      headline = `${days} days`;
      sub = `until the ${s.year} session convenes`;
    } else if (now <= end) {
      headline = `Day ${Math.round((now - start) / DAY) + 1}`;
      sub = `of the ${s.year} session; ${Math.round((end - now) / DAY)} days to adjournment`;
    } else {
      headline = 'Adjourned';
      sub = `The ${s.year} regular session has ended`;
    }
    const tile = (label, value, subText) => el('div', { className: 'session-tile' }, [
      el('span', { className: 'tile-label', text: label }), el('strong', { text: value }), subText ? el('div', { className: 'tile-sub', text: subText }) : '']);
    document.getElementById('session-banner').replaceChildren(
      tile(`${s.year} session`, headline, sub),
      tile('Convenes', niceDate(s.convenes), s.type),
      tile('Adjourns by', niceDate(s.adjourns), 'Constitutional deadline'),
      tile('Bills tracked', String(data.bills_current.filter((b) => b.bill).length), `${data.bills_current.filter((b) => !b.bill).length} issues on the watch list`));
    document.getElementById('disclaimer').textContent = data.disclaimer;
  }

  function statusChip(statuses, id) {
    const st = statuses.find((x) => x.id === id) || { label: id };
    return el('span', { className: `status status-${id}`, title: st.detail || '', text: st.label });
  }
  const topicName = (data, id) => (data.topics.find((t) => t.id === id) || { name: id }).name;
  const allBills = (data) => new Map([...data.bills_past, ...data.bills_current].map((b) => [b.id, b]));

  function fillSelect(select, options) {
    options.forEach(([value, label]) => select.append(el('option', { value, text: label })));
  }

  function currentRows(data) {
    const q = document.getElementById('bill-search').value.trim().toLowerCase();
    const topic = document.getElementById('bill-topic').value;
    const status = document.getElementById('bill-status').value;
    return data.bills_current.filter((b) => (topic === 'all' || b.topics.includes(topic))
      && (status === 'all' || b.status === status)
      && (!q || [b.bill, b.title, b.summary, b.public_act].join(' ').toLowerCase().includes(q)));
  }

  function renderCurrent(data) {
    const rows = currentRows(data);
    const lookup = allBills(data);
    const box = document.getElementById('current-bills');
    if (!rows.length) { box.replaceChildren(el('p', { className: 'empty', text: 'No bills match these filters.' })); return; }
    const body = rows.map((b) => el('tr', {}, [
      el('th', { scope: 'row' }, [
        el('div', { text: b.bill ? b.bill : 'Watch list' }),
        b.public_act ? el('div', { className: 'microcopy', text: b.public_act }) : '',
      ]),
      el('td', {}, [
        el('strong', { text: b.title }),
        el('div', { className: 'microcopy', text: b.summary }),
        el('div', {}, b.topics.map((t) => el('span', { className: 'chip', text: topicName(data, t) }))),
        (b.related || []).length ? el('div', { className: 'microcopy' }, [document.createTextNode('Related: '),
          ...b.related.flatMap((id, i) => { const r = lookup.get(id); return r ? [i ? ', ' : '', link(r.bill_status_url, `${r.session} ${r.bill}`)] : []; })]) : '',
      ]),
      el('td', {}, [statusChip(data.statuses, b.status), b.last_action ? el('div', { className: 'microcopy', text: `${b.last_action}${b.last_action_date ? ` (${niceDate(b.last_action_date)})` : ''}` }) : '']),
      el('td', {}, [b.bill_status_url ? link(b.bill_status_url, 'Bill status') : el('span', { className: 'microcopy', text: 'No bill yet' })]),
    ]));
    const table = el('table', { className: 'stack' }, [
      el('caption', { text: `${rows.length} shown` }),
      el('thead', {}, [el('tr', {}, ['Bill', 'What it would do', 'Status', 'Links'].map((h) => el('th', { scope: 'col', text: h })))]),
      el('tbody', {}, body)]);
    box.replaceChildren(el('div', { className: 'table-scroll' }, [table]));
  }

  function citation(s) { return `${s.display} ${s.label} (${s.period}). Source: ${s.source}. ${s.caveat}`.replace(/\s+/g, ' ').trim(); }

  function renderTopics(data, stats) {
    const byKey = new Map(stats.stats.map((s) => [s.key, s]));
    const lookup = allBills(data);
    document.getElementById('topic-nav').replaceChildren(...data.topics.map((t) => link(`#topic-${t.id}`, t.name)));
    document.getElementById('topics').replaceChildren(...data.topics.map((t) => {
      const cards = t.stat_keys.map((k) => byKey.get(k)).filter(Boolean).map((s) => el('div', { className: 'stat' }, [
        el('div', { className: 'num', text: s.display }),
        el('div', { className: 'lbl', text: s.label }),
        el('div', { className: 'meta' }, [document.createTextNode(`${s.period}. `), s.link ? link(s.link, s.source) : document.createTextNode(s.source)]),
        el('button', { type: 'button', className: 'copy-btn', 'data-copy': citation(s), text: 'Copy for testimony' }),
      ]));
      const facts = (t.context_facts || []).map((f) => el('li', {}, [document.createTextNode(`${f.text} `), el('span', { className: 'src' }, [link(f.source_url, f.source_title)])]));
      const related = [...lookup.values()].filter((b) => b.bill && b.topics.includes(t.id))
        .sort((a, b) => String(b.session).localeCompare(String(a.session)));
      return el('article', { className: 'topic', id: `topic-${t.id}` }, [
        el('h3', { text: t.name }),
        el('p', { text: t.why }),
        cards.length ? el('div', { className: 'stat-grid' }, cards) : '',
        facts.length ? el('ul', {}, facts) : '',
        el('div', { className: 'two-col' }, [
          el('div', {}, [el('h4', { text: 'Questions testimony can address' }), el('ul', {}, t.questions.map((q) => el('li', { text: q })))]),
          el('div', {}, [
            el('h4', { text: 'Related bills' }),
            related.length ? el('ul', {}, related.slice(0, 8).map((b) => el('li', {}, [link(b.bill_status_url, `${b.session} ${b.bill}`),
              document.createTextNode(`${b.public_act ? ` (${b.public_act})` : ''}: ${b.title}${b.enacted === false ? ' (not enacted)' : ''}`)]))) : el('p', { className: 'microcopy', text: 'None tracked yet.' }),
            (t.tool_links || []).length ? el('h4', { text: 'Data tools' }) : '',
            (t.tool_links || []).length ? el('ul', {}, t.tool_links.map((x) => el('li', {}, [link(x.url, x.title)]))) : '',
          ]),
        ]),
      ]);
    }));
    document.getElementById('topics').addEventListener('click', (e) => {
      const btn = e.target.closest('[data-copy]');
      if (btn) copyText(btn.getAttribute('data-copy'));
    });
  }

  function renderDates(data) {
    const now = today();
    const items = [
      { date: data.session.convenes, what: `${data.session.year} session convenes`, session: true },
      { date: data.session.adjourns, what: `${data.session.year} session must adjourn`, session: true },
      ...data.deadlines,
    ].sort((a, b) => a.date.localeCompare(b.date));
    document.getElementById('key-dates').replaceChildren(...items.map((d) => el('li', { className: `${d.session ? 'is-session' : ''} ${parseDate(d.date) < now ? 'is-past' : ''}`.trim() || null }, [
      el('div', { className: 'when', text: niceDate(d.date) }),
      el('div', {}, [document.createTextNode(d.what), d.source_url ? el('div', { className: 'src' }, [link(d.source_url, 'Source')]) : '']),
    ])));
  }

  function renderPast(data) {
    const session = document.getElementById('past-session').value;
    const topic = document.getElementById('past-topic').value;
    const outcome = document.getElementById('past-outcome').value;
    const rows = data.bills_past.filter((b) => (session === 'all' || b.session === session)
      && (topic === 'all' || b.topics.includes(topic))
      && (outcome === 'all' || (outcome === 'enacted' ? b.enacted : !b.enacted)))
      .sort((a, b) => String(b.session).localeCompare(String(a.session)) || String(a.bill).localeCompare(String(b.bill)));
    const box = document.getElementById('past-bills');
    if (!rows.length) { box.replaceChildren(el('p', { className: 'empty', text: 'No bills match these filters.' })); return; }
    const body = rows.map((b) => el('tr', {}, [
      el('th', { scope: 'row' }, [el('div', { text: `${b.session} ${b.bill}` }), el('div', { className: 'microcopy', text: b.public_act || '' })]),
      el('td', {}, [el('strong', { text: b.title }), el('div', { className: 'microcopy', text: b.summary }),
        el('div', {}, b.topics.map((t) => el('span', { className: 'chip', text: topicName(data, t) })))]),
      el('td', {}, [statusChip(data.statuses, b.enacted ? 'signed' : 'failed'), el('div', { className: 'microcopy', text: b.last_action || '' }),
        (b.key_dates || []).filter((k) => !/signed/i.test(k.what)).length ? el('ul', { className: 'microcopy' },
          b.key_dates.filter((k) => !/signed/i.test(k.what)).map((k) => el('li', { text: `${niceDate(k.date)}: ${k.what}` }))) : '']),
      el('td', {}, [link(b.bill_status_url, 'Bill status'), ...(b.sources || []).slice(0, 2).map((s) => el('div', { className: 'microcopy' }, [link(s.url, s.title)]))]),
    ]));
    const table = el('table', { className: 'stack' }, [
      el('caption', { text: `${rows.length} bills` }),
      el('thead', {}, [el('tr', {}, ['Bill', 'Summary', 'Outcome', 'Sources'].map((h) => el('th', { scope: 'col', text: h })))]),
      el('tbody', {}, body)]);
    box.replaceChildren(el('div', { className: 'table-scroll' }, [table]));
    const summary = document.querySelector('#past-details > summary');
    if (summary) summary.textContent = `Show ${rows.length} past bills`;
  }

  function renderHowTo(data, stats) {
    document.getElementById('howto').replaceChildren(...data.how_to.map((h) => el('article', { className: 'card' }, [
      el('h3', { text: h.title }), el('p', { text: h.text }), h.url ? el('p', {}, [link(h.url, 'Connecticut General Assembly')]) : ''])));
    document.getElementById('updated-note').textContent =
      `Bill list last updated ${niceDate(data.last_updated)}. Statistics computed ${stats.generated_at.slice(0, 10)} from data published on this site. ${data.maintained_by}`;
  }

  function csvDownload(data) {
    const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const head = ['session', 'bill', 'public_act', 'status', 'title', 'topics', 'last_action', 'bill_status_url'];
    const lines = [head.join(',')];
    data.bills_current.forEach((b) => lines.push([b.session, b.bill || 'watch list', b.public_act, b.status, b.title, b.topics.join('; '), b.last_action, b.bill_status_url].map(esc).join(',')));
    data.bills_past.forEach((b) => lines.push([b.session, b.bill, b.public_act, b.enacted ? 'signed' : 'failed', b.title, b.topics.join('; '), b.last_action, b.bill_status_url].map(esc).join(',')));
    const url = URL.createObjectURL(new Blob([lines.join('\r\n')], { type: 'text/csv' }));
    const a = el('a', { href: url, download: `ct-ltc-legislative-tracker-${data.last_updated}.csv` });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function init() {
    let data, stats;
    try {
      [data, stats] = await Promise.all([load(TRACKER_URL), load(STATS_URL)]);
    } catch (error) {
      document.getElementById('tracker-note').replaceChildren(el('span', { className: 'notice error', text: `The tracker data could not be loaded (${error.message}).` }));
      return;
    }
    const topics = data.topics.map((t) => [t.id, t.name]);
    fillSelect(document.getElementById('bill-topic'), topics);
    fillSelect(document.getElementById('past-topic'), topics);
    fillSelect(document.getElementById('bill-status'), data.statuses.map((s) => [s.id, s.label]));
    fillSelect(document.getElementById('past-session'), [...new Set(data.bills_past.map((b) => b.session))].sort().reverse().map((s) => [s, s]));
    const billCount = data.bills_current.filter((b) => b.bill).length;
    document.getElementById('tracker-note').textContent = billCount
      ? `${billCount} ${data.session.year} bills tracked, plus issues on the watch list.`
      : `No ${data.session.year} bills have been filed yet. Bills are introduced once the session convenes; until then, the watch list shows issues likely to return.`;
    const steps = [
      () => renderSession(data), () => renderCurrent(data), () => renderTopics(data, stats),
      () => renderDates(data), () => renderPast(data), () => renderHowTo(data, stats)];
    steps.forEach((step) => { try { step(); } catch (error) { console.error('Legislative tracker render failed', error); } });
    ['bill-search', 'bill-topic', 'bill-status'].forEach((id) => document.getElementById(id).addEventListener('input', () => renderCurrent(data)));
    ['past-session', 'past-topic', 'past-outcome'].forEach((id) => document.getElementById(id).addEventListener('input', () => renderPast(data)));
    document.getElementById('download-csv').addEventListener('click', () => csvDownload(data));
    document.getElementById('print-page').addEventListener('click', () => window.print());
    ['past-session', 'past-topic', 'past-outcome'].forEach((id) => document.getElementById(id).addEventListener('input', () => { document.getElementById('past-details').open = true; }));
    window.addEventListener('beforeprint', () => { document.getElementById('past-details').open = true; });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
