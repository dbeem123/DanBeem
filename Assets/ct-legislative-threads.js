/* Storylines, long-term care act reference, topic history and testimony builder for /legislation/.
   Data: ct_ltcop_legislative_threads.json, ct_ltcop_act_reference.json, ct_ltcop_positions.json,
   ct_ltcop_bill_tracker_2027.json and, for data strips, nursing_home_ct_statewide_context.json.
   Exposes window.CTLegThreads for ct-legislative-tracker.js. Stores and sends nothing. */
(function () {
  'use strict';
  const NON_POSITION = 'Listing is not a position of the Long Term Care Ombudsman Program.';
  const NO_POSITION = '[No approved Program position for this topic. Add one only with State Ombudsman approval.]';
  const FILES = {
    threads: '/data/ct_ltcop_legislative_threads.json',
    acts: '/data/ct_ltcop_act_reference.json',
    positions: '/data/ct_ltcop_positions.json',
    session2027: '/data/ct_ltcop_bill_tracker_2027.json',
  };

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
  const svgEl = (tag, attrs) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    return node;
  };
  function parseDate(iso) { const [y, m, d] = iso.split('-').map(Number); return new Date(y, m - 1, d); }
  const niceDate = (iso) => (iso ? parseDate(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '');
  const todayIso = () => { const t = new Date(); return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`; };

  async function load(url) {
    if (window.DanBeemData && typeof window.DanBeemData.loadJson === 'function') return window.DanBeemData.loadJson(url);
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(`Failed to load ${url}: ${r.status}`);
    return r.json();
  }
  async function loadAll() {
    const entries = await Promise.all(Object.entries(FILES).map(async ([k, url]) => {
      try { return [k, await load(url)]; } catch (error) { console.error('Legislative data failed to load', url, error); return [k, null]; }
    }));
    return Object.fromEntries(entries);
  }

  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const a = el('a', { href: url, download: name });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const csvLine = (values) => values.map((v) => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',');

  /* Every bill or act we know about, by id: tracker (past and current), act reference, 2027 session. */
  function buildLookup(ctx) {
    const map = new Map();
    const put = (id, rec) => { map.set(id, Object.assign({}, map.get(id) || {}, rec)); };
    (ctx.acts ? ctx.acts.acts : []).forEach((a) => put(a.id, { id: a.id, session: String(a.session), bill: a.bill, public_act: a.public_act,
      title: a.title, label: a.summary, summary: a.summary, topics: a.topics, enacted: true, url: a.source_url, act_url: a.source_url }));
    ctx.tracker.bills_past.forEach((b) => put(b.id, { id: b.id, session: String(b.session), bill: b.bill, public_act: b.public_act || null,
      title: b.short_title || b.title, label: b.short_title || b.title, summary: b.summary, topics: b.topics, enacted: b.enacted, url: b.bill_status_url }));
    ((ctx.session2027 && ctx.session2027.bills) || []).forEach((b) => put(b.id, { id: b.id, session: '2027', bill: b.bill, public_act: b.public_act || null,
      title: b.summary, summary: b.summary, topics: b.topics || [], status: b.status, live: true, url: b.bill_status_url }));
    return map;
  }

  /* threads -> bills: which storylines mention a bill, act or watch item. Bills carry no thread field. */
  function threadsByRef(threads) {
    const map = new Map();
    (threads ? threads.threads : []).forEach((th) => {
      const ids = new Set(th.events.map((e) => e.ref).filter(Boolean).concat(th.watch || []));
      ids.forEach((id) => { if (!map.has(id)) map.set(id, []); map.get(id).push(th); });
    });
    return map;
  }
  function partOfChips(byRef, id) {
    const list = byRef.get(id) || [];
    if (!list.length) return '';
    return el('div', { className: 'part-of microcopy' }, [document.createTextNode('Part of: '),
      ...list.flatMap((th, i) => [i ? ' ' : '', el('a', { className: 'tag thread-chip', href: `/legislation/#thread-${th.id}`, text: th.title })])]);
  }

  function sessionStatus(ctx, id) {
    const st = ((ctx.session2027 && ctx.session2027.statuses) || []).find((s) => s.id === id);
    return el('span', { className: `status-pill status-${id}`, title: st ? st.detail : '', text: st ? st.label : id });
  }

  function statusLabel(threads, id) {
    return { active: 'Active', settled: 'Settled', watching: 'Watching' }[id] || id;
  }

  function storylineText(th, ctx) {
    const lines = [th.title, '', th.summary, ''];
    th.events.forEach((e) => lines.push(`${e.date} — ${e.label} (${e.source_url})`));
    if ((th.open_questions || []).length) { lines.push('', 'Open questions:'); th.open_questions.forEach((q) => lines.push(`- ${q}`)); }
    lines.push('', `Source: danbeem.xyz/legislation/#thread-${th.id}, ${niceDate(ctx.threads.last_updated)}.`, NON_POSITION);
    return lines.join('\n');
  }

  function quarterOf(iso) { const [y, m] = iso.split('-').map(Number); return `${y}Q${Math.ceil(m / 3)}`; }

  function dataStrip(th, ctx) {
    const def = (ctx.threads.data_series || {})[th.data_series];
    const statewide = ctx.statewide;
    if (!def || !statewide) return '';
    const points = statewide.statewide_quarterly.filter((q) => q[def.field] !== null && q[def.field] !== undefined)
      .map((q) => ({ quarter: q.quarter, label: q.quarter_label, value: q[def.field] }));
    if (points.length < 2) return '';
    const W = 640, H = 120, padL = 34, padR = 12, padT = 12, padB = 26;
    const max = Math.max(...points.map((p) => p.value)), min = 0;
    const x = (i) => padL + (i * (W - padL - padR)) / (points.length - 1);
    const y = (v) => padT + ((max - v) * (H - padT - padB)) / (max - min || 1);
    const first = points[0], last = points[points.length - 1];
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', class: 'strip-svg',
      'aria-label': `${def.label}: ${first.value} in ${first.label}, ${last.value} in ${last.label}.` });
    svg.append(svgEl('line', { x1: padL, x2: W - padR, y1: y(0), y2: y(0), class: 'strip-axis' }));
    const index = new Map(points.map((p, i) => [p.quarter, i]));
    th.events.forEach((e) => {
      const i = index.get(quarterOf(e.date));
      if (i === undefined) return;
      svg.append(svgEl('line', { x1: x(i), x2: x(i), y1: padT, y2: y(0), class: 'strip-marker' }));
    });
    svg.append(svgEl('polyline', { points: points.map((p, i) => `${x(i)},${y(p.value)}`).join(' '), class: 'strip-line' }));
    points.forEach((p, i) => svg.append(svgEl('circle', { cx: x(i), cy: y(p.value), r: 2.5, class: 'strip-dot' })));
    [[0, first], [points.length - 1, last]].forEach(([i, p]) => {
      const t = svgEl('text', { x: x(i), y: H - 8, class: 'strip-text', 'text-anchor': i ? 'end' : 'start' });
      t.textContent = `${p.label}: ${p.value}`;
      svg.append(t);
    });
    const tMax = svgEl('text', { x: 4, y: y(max) + 4, class: 'strip-text' }); tMax.textContent = String(max); svg.append(tMax);
    return el('figure', { className: 'data-strip' }, [svg,
      el('figcaption', { className: 'microcopy', text: `${def.label}, by quarter. ${def.note} Vertical lines mark storyline events in this period.` })]);
  }

  const KIND = { act: 'Act', bill: 'Bill', policy: 'State policy', federal: 'Federal', report: 'Report', budget: 'Budget', data: 'Data' };
  function eventItem(e, lookup) {
    const ref = e.ref ? lookup.get(e.ref) : null;
    const notEnacted = e.kind === 'bill' && ref && ref.enacted === false;
    const future = e.date > todayIso();
    return el('li', { className: `thread-event kind-${e.kind}${notEnacted ? ' not-enacted' : ''}${future ? ' is-future' : ''}` }, [
      el('span', { className: 'thread-dot', 'aria-hidden': 'true' }),
      el('div', { className: 'thread-when', text: niceDate(e.date) }),
      el('div', { className: 'thread-label' }, [link(e.source_url, e.label)]),
      el('div', { className: 'microcopy', text: e.what }),
      el('div', { className: 'microcopy thread-meta' }, [
        el('span', { className: 'tag', text: notEnacted ? 'Bill, not enacted' : (future ? `${KIND[e.kind] || e.kind}, scheduled` : (KIND[e.kind] || e.kind)) }),
        ref && ref.url ? link(ref.url, ref.public_act ? `${ref.public_act} text` : `${ref.session} ${ref.bill} status`) : '',
      ]),
    ]);
  }

  function threadCard(th, ctx, lookup) {
    const years = [...new Set(th.events.map((e) => e.date.slice(0, 4)))];
    const timeline = el('div', { className: 'thread-timeline', role: 'list', 'aria-label': `${th.title} timeline` }, years.map((yr) =>
      el('div', { className: 'thread-year', role: 'listitem' }, [
        el('div', { className: 'thread-year-label', text: yr }),
        el('ol', { className: 'thread-events' }, th.events.filter((e) => e.date.startsWith(yr)).map((e) => eventItem(e, lookup))),
      ])));
    const watch = (th.watch || []).map((id) => ctx.tracker.bills_current.find((b) => b.id === id)).filter(Boolean);
    const live = ((ctx.session2027 && ctx.session2027.bills) || []).filter((b) => th.events.some((e) => e.ref === b.id) || (th.watch || []).includes(b.id));
    const continues = [
      ...watch.map((b) => el('li', {}, [el('strong', { text: b.short_title || b.title }), document.createTextNode(`: ${b.summary}`)])),
      ...live.map((b) => el('li', {}, [link(b.bill_status_url, `2027 ${b.bill}`), document.createTextNode(' '), sessionStatus(ctx, b.status)])),
    ];
    const copyBtn = el('button', { type: 'button', className: 'action-button secondary copy-btn', 'data-copy-thread': th.id, text: 'Copy storyline for testimony' });
    const topicTags = th.topics.map((t) => el('a', { className: 'tag', href: `#topic-${t}`, text: (ctx.tracker.topics.find((x) => x.id === t) || { name: t }).name }));
    return el('article', { className: 'card thread', id: `thread-${th.id}` }, [
      el('div', { className: 'thread-head' }, [
        el('h3', { text: th.title }),
        el('span', { className: `status-pill thread-status thread-status-${th.status}`, text: statusLabel(ctx.threads, th.status) }),
      ]),
      el('p', { className: 'thread-question', text: th.question }),
      el('p', { text: th.summary }),
      el('div', {}, topicTags),
      timeline,
      dataStrip(th, ctx),
      el('div', { className: 'two-col' }, [
        el('div', {}, [el('h4', { className: 'col-heading', text: 'Where it continues' }),
          continues.length ? el('ul', {}, continues) : el('p', { className: 'microcopy', text: 'No 2027 bill or watch item yet.' })]),
        el('div', {}, [el('h4', { className: 'col-heading', text: 'Open questions' }),
          el('ul', {}, (th.open_questions || []).map((q) => el('li', { text: q })))]),
      ]),
      el('div', { className: 'action-row' }, [copyBtn]),
    ]);
  }

  function renderThreads(ctx, copyText) {
    const box = document.getElementById('threads');
    if (!box) return;
    if (!ctx.threads) { box.replaceChildren(el('p', { className: 'empty', text: 'Storylines could not be loaded.' })); return; }
    const lookup = buildLookup(ctx);
    box.replaceChildren(
      el('p', { className: 'notice warning', text: ctx.threads.disclaimer }),
      ...ctx.threads.threads.map((th) => threadCard(th, ctx, lookup)));
    box.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-copy-thread]');
      if (!btn) return;
      const th = ctx.threads.threads.find((t) => t.id === btn.getAttribute('data-copy-thread'));
      if (th) copyText(storylineText(th, ctx));
    });
  }

  /* All long-term care acts since 2021 */
  function renderActs(ctx) {
    const box = document.getElementById('acts-table');
    if (!box) return;
    if (!ctx.acts) { box.replaceChildren(el('p', { className: 'empty', text: 'The act list could not be loaded.' })); return; }
    const topicName = (id) => (ctx.tracker.topics.find((t) => t.id === id) || { name: id }).name;
    const byRef = threadsByRef(ctx.threads);
    const search = document.getElementById('acts-search'), year = document.getElementById('acts-year'), topic = document.getElementById('acts-topic');
    [...new Set(ctx.acts.acts.map((a) => a.session))].sort().reverse().forEach((y) => year.append(el('option', { value: String(y), text: String(y) })));
    ctx.tracker.topics.forEach((t) => topic.append(el('option', { value: t.id, text: t.name })));
    const rows = () => {
      const q = search.value.trim().toLowerCase();
      return ctx.acts.acts.filter((a) => (year.value === 'all' || String(a.session) === year.value)
        && (topic.value === 'all' || a.topics.includes(topic.value))
        && (!q || [a.bill, a.public_act, a.title, a.summary, ...(byRef.get(a.id) || []).map((t) => t.title)].join(' ').toLowerCase().includes(q)))
        .sort((a, b) => b.session - a.session || a.public_act.localeCompare(b.public_act, 'en', { numeric: true }));
    };
    const draw = () => {
      const list = rows();
      if (!list.length) { box.replaceChildren(el('p', { className: 'empty', text: 'No acts match these filters.' })); return; }
      const table = el('table', { className: 'stack' }, [
        el('caption', { text: `${list.length} of ${ctx.acts.acts.length} acts` }),
        el('thead', {}, [el('tr', {}, ['Act', 'What it does', 'Topics', 'Text'].map((h) => el('th', { scope: 'col', text: h })))]),
        el('tbody', {}, list.map((a) => el('tr', {}, [
          el('th', { scope: 'row' }, [el('div', { text: a.public_act }), el('div', { className: 'microcopy', text: `${a.session} ${a.bill}` })]),
          el('td', {}, [el('div', { text: a.summary }), el('div', { className: 'microcopy official-title', text: a.title }), partOfChips(byRef, a.id)]),
          el('td', {}, a.topics.map((t) => el('span', { className: 'tag', text: topicName(t) }))),
          el('td', {}, [link(a.source_url, 'Public act')]),
        ])))]);
      box.replaceChildren(el('div', { className: 'table-scroll' }, [table]));
      const summary = document.querySelector('#acts-details > summary');
      if (summary) summary.textContent = `Show ${list.length} acts`;
    };
    [search, year, topic].forEach((n) => n.addEventListener('input', () => { draw(); const d = document.getElementById('acts-details'); if (d) d.open = true; }));
    window.addEventListener('beforeprint', () => { const d = document.getElementById('acts-details'); if (d) d.open = true; });
    document.getElementById('acts-csv').addEventListener('click', () => {
      const lines = [csvLine(['session', 'public_act', 'bill', 'title', 'summary', 'topics', 'source_url'])];
      rows().forEach((a) => lines.push(csvLine([a.session, a.public_act, a.bill, a.title, a.summary, a.topics.join('; '), a.source_url])));
      download(`ct-long-term-care-acts-2021-2026-${ctx.acts.last_updated}.csv`, lines.join('\r\n'), 'text/csv');
    });
    const src = document.getElementById('acts-sources');
    if (src) src.replaceChildren(document.createTextNode(`${ctx.acts.scope} Compiled from: `),
      ...ctx.acts.sources.flatMap((s, i) => [i ? '; ' : '', link(s.url, s.title)]), '. ', ctx.acts.disclaimer);
    draw();
  }

  /* History 2021-2027 for one topic: bills_past + act reference + 2027 session, by year. */
  function historyFor(topicId, ctx) {
    const lookup = buildLookup(ctx);
    const items = [...lookup.values()].filter((b) => b.bill && (b.topics || []).includes(topicId) && Number(b.session) >= 2021)
      .sort((a, b) => Number(b.session) - Number(a.session) || String(a.public_act || a.bill).localeCompare(String(b.public_act || b.bill), 'en', { numeric: true }));
    const wrap = el('div', { className: 'topic-history' });
    if (!items.length) { wrap.append(el('p', { className: 'microcopy', text: 'None tracked yet.' })); return wrap; }
    const onlyId = `hist-enacted-${topicId}`, yearId = `hist-year-${topicId}`;
    const only = el('input', { type: 'checkbox', id: onlyId });
    const year = el('select', { id: yearId }, [el('option', { value: 'all', text: 'All years' }),
      ...[...new Set(items.map((b) => b.session))].map((y) => el('option', { value: y, text: y }))]);
    const list = el('div', { className: 'history-years', 'aria-live': 'polite' });
    const draw = () => {
      const shown = items.filter((b) => (!only.checked || b.enacted) && (year.value === 'all' || b.session === year.value));
      const years = [...new Set(shown.map((b) => b.session))];
      list.replaceChildren(...(years.length ? years.map((yr) => el('div', { className: 'history-year' }, [
        el('div', { className: 'history-year-label', text: yr }),
        el('ul', { className: 'history-list' }, shown.filter((b) => b.session === yr).map((b) => el('li', {}, [
          b.live ? sessionStatus(ctx, b.status)
            : b.enacted ? el('span', { className: 'status-pill status-signed act-pill', text: b.public_act || 'Enacted' })
              : el('span', { className: 'status-pill outline-pill', text: 'Not enacted' }),
          document.createTextNode(' '),
          link(b.url, b.bill), document.createTextNode(`: ${b.label || b.title}`),
        ]))),
      ])) : [el('p', { className: 'microcopy', text: 'No bills match these filters.' })]));
    };
    only.addEventListener('change', draw); year.addEventListener('input', draw);
    wrap.append(el('div', { className: 'history-filters' }, [
      el('label', { className: 'inline-check', for: onlyId }, [only, document.createTextNode(' Enacted only')]),
      el('label', { className: 'visually-hidden', for: yearId, text: 'Year' }), year,
      el('span', { className: 'microcopy', text: `${items.length} bills and acts` })]), list);
    draw();
    return wrap;
  }

  /* Side-by-side comparison of related policy approaches (e.g. three ways to set staffing). */
  function comparisonFor(topicId, ctx) {
    const list = ((ctx.threads && ctx.threads.comparisons) || []).filter((c) => c.topic === topicId);
    if (!list.length) return '';
    const byId = new Map(ctx.threads.threads.map((t) => [t.id, t]));
    const src = (url) => el('span', { className: 'src' }, [' ', link(url, 'Source')]);
    return el('div', {}, list.map((c) => el('div', { className: 'comparison', id: `compare-${c.id}` }, [
      el('h4', { className: 'col-heading', text: c.title }),
      el('p', { className: 'microcopy', text: c.intro }),
      el('div', { className: 'table-scroll' }, [el('table', { className: 'stack compare-table' }, [
        el('thead', {}, [el('tr', {}, ['Approach', 'Connecticut proposals', 'What happened and why', 'Where it stands'].map((h) => el('th', { scope: 'col', text: h })))]),
        el('tbody', {}, c.rows.map((r) => el('tr', {}, [
          el('th', { scope: 'row' }, [el('div', { text: r.approach }), el('div', { className: 'microcopy', text: r.how }),
            byId.has(r.thread) ? el('div', { className: 'microcopy' }, [link(`#thread-${r.thread}`, 'Storyline')]) : '']),
          el('td', { text: r.proposals }),
          el('td', {}, [el('div', { text: r.outcome }), el('ul', { className: 'reason-list microcopy' }, r.reasons.map((x) => el('li', {}, [document.createTextNode(x.text), src(x.source_url)])))]),
          el('td', {}, [el('div', {}, [document.createTextNode(r.now), src(r.now_source)]),
            r.elsewhere ? el('div', { className: 'microcopy' }, [document.createTextNode(`Elsewhere: ${r.elsewhere.text}`), src(r.elsewhere.source_url)]) : '']),
        ])))]),
      ]),
    ])));
  }

  function threadsForTopic(topicId, ctx) {
    const list = (ctx.threads ? ctx.threads.threads : []).filter((th) => th.topics.includes(topicId));
    if (!list.length) return el('p', { className: 'microcopy', text: 'No storyline yet.' });
    return el('ul', {}, list.map((th) => el('li', {}, [link(`#thread-${th.id}`, th.title), document.createTextNode(` (${statusLabel(ctx.threads, th.status)}): ${th.question}`)])));
  }

  /* Testimony builder: runs in the browser; nothing is stored or sent. */
  function renderBuilder(ctx, stats, copyText) {
    const box = document.getElementById('builder');
    if (!box) return;
    const byKey = new Map(stats.stats.map((s) => [s.key, s]));
    const topics = ctx.tracker.topics;
    const threads = ctx.threads ? ctx.threads.threads : [];
    const bills2027 = (ctx.session2027 && ctx.session2027.bills) || [];
    const positions = (ctx.positions && ctx.positions.positions) || [];
    const start = document.getElementById('builder-start');
    const group = (label, opts) => el('optgroup', { label }, opts.map(([v, t]) => el('option', { value: v, text: t })));
    start.replaceChildren(
      group('Topic', topics.map((t) => [`topic:${t.id}`, t.name])),
      group('Storyline', threads.map((t) => [`thread:${t.id}`, t.title])),
      bills2027.length ? group('2027 bill', bills2027.map((b) => [`bill:${b.id}`, `${b.bill}: ${b.summary.slice(0, 60)}`]))
        : group('2027 bill', [['none', 'No 2027 bills yet']]));
    const statsBox = document.getElementById('builder-stats'), eventsBox = document.getElementById('builder-events'), qBox = document.getElementById('builder-questions');
    const out = document.getElementById('builder-output');

    function selection() {
      const [kind, id] = start.value.split(':');
      if (kind === 'thread') { const th = threads.find((t) => t.id === id); return { kind, th, topicIds: th.topics }; }
      if (kind === 'bill') { const b = bills2027.find((x) => x.id === id); return { kind, bill: b, topicIds: (b && b.topics) || [] }; }
      return { kind: 'topic', topic: topics.find((t) => t.id === id), topicIds: [id] };
    }
    function checks(boxEl, name, items, preselect, max) {
      boxEl.replaceChildren(...(items.length ? items.map((it, i) => el('label', { className: 'inline-check' }, [
        el('input', { type: 'checkbox', name, value: String(i), checked: i < preselect ? 'checked' : null }), document.createTextNode(` ${it.text}`)]))
        : [el('p', { className: 'microcopy', text: 'None for this choice.' })]));
      if (max) {
        const sync = () => {
          const boxes = [...boxEl.querySelectorAll('input')];
          const n = boxes.filter((b) => b.checked).length;
          boxes.forEach((b) => { b.disabled = !b.checked && n >= max; });
        };
        boxEl.addEventListener('change', sync); sync();
      }
      return items;
    }
    let current = { stats: [], events: [], questions: [] };
    function options() {
      const sel = selection();
      const topicObjs = sel.topicIds.map((id) => topics.find((t) => t.id === id)).filter(Boolean);
      const statKeys = [...new Set(topicObjs.flatMap((t) => t.stat_keys))];
      const statItems = statKeys.map((k) => byKey.get(k)).filter(Boolean).map((s) => ({ s, text: `${s.display} ${s.label}` }));
      const evThreads = sel.kind === 'thread' ? [sel.th] : threads.filter((th) => th.topics.some((t) => sel.topicIds.includes(t)));
      const seen = new Set();
      const evItems = evThreads.flatMap((th) => th.events).filter((e) => { const k = e.date + e.label; if (seen.has(k)) return false; seen.add(k); return true; })
        .sort((a, b) => a.date.localeCompare(b.date)).map((e) => ({ e, text: `${e.date} — ${e.label}` }));
      const qs = [...new Set([...topicObjs.flatMap((t) => t.questions.map((q) => (typeof q === 'string' ? q : q.text))),
        ...(sel.kind === 'thread' ? sel.th.open_questions || [] : [])])].map((q) => ({ q, text: q }));
      current = {
        sel,
        stats: checks(statsBox, 'b-stat', statItems, 3, 5),
        events: checks(eventsBox, 'b-event', evItems, sel.kind === 'thread' ? evItems.length : Math.min(5, evItems.length)),
        questions: checks(qBox, 'b-q', qs, Math.min(3, qs.length)),
      };
      draft();
    }
    const picked = (boxEl, items) => [...boxEl.querySelectorAll('input:checked')].map((i) => items[Number(i.value)]).filter(Boolean);
    function draft() {
      const sel = current.sel;
      const lines = [];
      if (sel.kind === 'bill' && sel.bill) lines.push(`${sel.bill.bill} (${ctx.session2027.session.year})`, sel.bill.summary);
      else if (sel.kind === 'thread') lines.push(`Storyline: ${sel.th.title}`, sel.th.summary);
      else lines.push(`Topic: ${sel.topic.name}`, sel.topic.why);
      lines.push('');
      const pos = positions.filter((p) => sel.topicIds.includes(p.topic));
      if (pos.length) pos.forEach((p) => lines.push(`Position of the Connecticut Long Term Care Ombudsman Program (approved ${p.approved_date})`, p.text, `Basis: ${p.basis_label} (${p.basis_url})`, ''));
      else lines.push(NO_POSITION, '');
      const st = picked(statsBox, current.stats);
      if (st.length) { lines.push('Statistics'); st.forEach(({ s }) => lines.push(`- ${s.display} ${s.label} (${s.period}; ${s.source}; ${s.caveat})`)); lines.push(''); }
      const ev = picked(eventsBox, current.events);
      if (ev.length) { lines.push('Legislative history'); ev.forEach(({ e }) => lines.push(`- ${e.date} — ${e.label} (${e.source_url})`)); lines.push(''); }
      const qs = picked(qBox, current.questions);
      if (qs.length) { lines.push('Questions'); qs.forEach(({ q }) => lines.push(`- ${q}`)); lines.push(''); }
      lines.push(`Draft generated from danbeem.xyz research data on ${niceDate(todayIso())}. Verify before submitting.`);
      out.value = lines.join('\n');
    }
    start.addEventListener('input', options);
    [statsBox, eventsBox, qBox].forEach((b) => b.addEventListener('change', draft));
    document.getElementById('builder-copy').addEventListener('click', () => copyText(out.value));
    document.getElementById('builder-download').addEventListener('click', () => download(`testimony-draft-${todayIso()}.txt`, out.value, 'text/plain'));
    options();
  }

  window.CTLegThreads = { loadAll, load, buildLookup, threadsByRef, partOfChips, renderThreads, renderActs, historyFor, comparisonFor, threadsForTopic, renderBuilder, storylineText, NON_POSITION };
})();
