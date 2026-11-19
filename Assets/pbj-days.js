(() => {
  'use strict';
  const get = id => document.getElementById('pbj-' + id);
  const panel = document.getElementById('daily-staffing');
  if (!panel) return;
  let dossier, home, catalog, dataset, dates, generation = 0;
  const params = new URLSearchParams(location.search);
  const iso = day => day.slice(0, 4) + '-' + day.slice(4, 6) + '-' + day.slice(6);
  const format = value => value == null ? '—' : value.toLocaleString('en-US', {maximumFractionDigits: 2});
  function element(tag, text) {
    const el = document.createElement(tag);
    el.textContent = text;
    return el;
  }
  function selectOptions(control, items) {
    control.replaceChildren(...items.map(([value, label]) => new Option(label, value)));
  }
  async function read(url, compressed = false) {
    const response = await fetch(url);
    if (!response.ok) throw new Error('HTTP ' + response.status);
    if (!compressed) return response.json();
    const buffer = await response.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    if (bytes[0] !== 31 || bytes[1] !== 139) return JSON.parse(new TextDecoder().decode(buffer));
    return new Response(new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
  }
  function reset(message) {
    dataset = null;
    get('status').textContent = message;
    get('controls').hidden = true;
  }
  async function openHome() {
    const token = ++generation;
    reset(home ? 'Loading reported staffing…' : 'Select a facility to see its staffing.');
    if (!home || !panel.open) return;
    try {
      catalog ??= await read('/data/ct_daily_staffing/index.json');
      if (token !== generation) return;
      const archive = get('archive');
      if (!archive.options.length) {
        const historical = Object.entries(catalog.historical_homes || {}).sort((a,b) => a[1].localeCompare(b[1]));
        selectOptions(archive, [['', 'Use selected facility'], ...historical.map(([ccn,name]) => [ccn, name + ' (' + ccn + ')'])]);
        get('archive-label').hidden = historical.length === 0;
        if (catalog.historical_homes?.[params.get('pbj_home')]) archive.value = params.get('pbj_home');
      }
      home = archive.value ? {ccn: archive.value, name: catalog.historical_homes[archive.value]} : dossier;
      get('home').textContent = home.name + ' · CCN ' + home.ccn;
      if (get('support').open) annual();
      const quarters = catalog.facilities[home.ccn] || [];
      if (!quarters.length) { reset('No daily PBJ reports for this facility.'); return; }
      selectOptions(get('quarter'), quarters.slice().reverse().map(q => [q, q]));
      selectOptions(get('role'), [['', 'All positions'], ...catalog.roles.map(r => [r.id, r.label])]);
      let day;
      if ((params.get('pbj_home') || params.get('ccn')) === home.ccn) {
        day = params.get('day');
        if (day && /^\d{4}-\d{2}-\d{2}$/.test(day)) {
          const q = day.slice(0,4) + 'Q' + Math.ceil(Number(day.slice(5,7)) / 3);
          if (quarters.includes(q)) get('quarter').value = q;
        }
        if (catalog.roles.some(r => String(r.id) === params.get('role'))) get('role').value = params.get('role');
      }
      await loadQuarter(day);
    } catch { if (token === generation) reset('Staffing could not load. Close and reopen this section to retry.'); }
  }
  async function loadQuarter(day) {
    const token = ++generation;
    const q = get('quarter').value;
    reset('Loading ' + q + '…');
    try {
      const data = await read('/data/ct_daily_staffing/' + q + '/' + home.ccn + '.json.gz', true);
      if (token !== generation) return;
      dataset = data;
      dates = Object.keys(data).sort();
      get('day').min = iso(dates[0]);
      get('day').max = iso(dates.at(-1));
      get('day').value = day && day >= get('day').min && day <= get('day').max ? day : get('day').max;
      const sources = get('sources');
      sources.replaceChildren('CMS Payroll-Based Journal sources: ');
      const quarter = catalog.quarters[q];
      for (const [kind, label] of [['nurse','Nursing hours'],['other','Other positions'],['detail','Employee detail']]) {
        if (!quarter.sources[kind]) continue;
        const link = element('a', label);
        link.href = quarter.sources[kind];
        sources.append(link, '  ');
      }
      get('controls').hidden = false;
      render();
    } catch { if (token === generation) reset('This quarter could not load. Close and reopen the section to retry.'); }
  }
  function render() {
    if (!dataset) return;
    const day = get('day').value.replaceAll('-', '');
    const record = dataset[day];
    const role = get('role').value;
    const rows = get('rows');
    rows.replaceChildren();
    get('status').textContent = record ? '' : 'No report for this date.';
    get('prev').disabled = !dates.some(d => d < day);
    get('next').disabled = !dates.some(d => d > day);
    get('census').textContent = record ? 'Resident census: ' + format(record[0]) + ' · Distinct workers across all roles: ' + format(record[1]) : '';
    const link = new URL(location.href);
    link.search = new URLSearchParams({ccn: home.ccn, day: get('day').value});
    if (get('archive').value) { link.searchParams.set('ccn', dossier.ccn); link.searchParams.set('pbj_home',home.ccn); }
    if (role) link.searchParams.set('role', role);
    link.hash = 'daily-staffing';
    get('link').href = link.href;
    let group = -1;
    catalog.roles.forEach((r, index) => {
      if (!record || (role && String(r.id) !== role)) return;
      if (group !== r.group) {
        group = r.group;
        const heading = element('th', catalog.groups[group]);
        heading.colSpan = 6;
        const tr = rows.insertRow();
        tr.className = 'pbj-group';
        tr.append(heading);
      }
      const [total, emp, ctr, workers, excluded] = record[2][index];
      const tr = rows.insertRow();
      const name = element('th', r.label + (excluded ? ' (CMS excluded)' : ''));
      name.scope = 'row';
      tr.append(name);
      [workers, total, emp, ctr, total != null && record[0] > 0 ? total * 60 / record[0] : null]
        .forEach(value => tr.append(element('td', format(value))));
    });
    drawTrend(role);
  }
  function drawTrend(role) {
    const index = catalog.roles.findIndex(r => String(r.id) === role);
    const values = dates.map(d => {
      const hours = dataset[d][2].map(r => r[0]);
      if (index >= 0) return hours[index];
      return hours.every(n => n != null) ? hours.reduce((a,b) => a+b, 0) : null;
    });
    const max = Math.max(1, ...values.filter(v => v != null));
    get('trend-label').textContent = (index < 0 ? 'All positions combined' : catalog.roles[index].label) +
      ' · Daily hours from ' + iso(dates[0]) + ' to ' + iso(dates.at(-1)) + '. Gaps indicate unavailable totals.';
    get('bars').replaceChildren(...values.map((v,i) => {
      const bar = element('span', '');
      bar.style.height = v == null ? '0' : Math.max(1, v * 100 / max) + '%';
      bar.title = iso(dates[i]) + ': ' + format(v) + ' hours';
      return bar;
    }));
  }
  function download() {
    if (!dataset) return;
    const csv = [['CCN','Date','Census','Distinct workers (facility)','Job code','Position','Hours','Employee hours','Contract hours','Distinct workers (role)','Minutes per resident','CMS excluded']];
    for (const d of dates) {
      const [census, workers, fields] = dataset[d];
      catalog.roles.forEach((r,i) => {
        const [hours,employee,contract,count,excluded] = fields[i];
        csv.push([home.ccn,iso(d),census,workers,r.id,r.label,hours,employee,contract,count,
          census && hours != null ? (60*hours/census).toFixed(2) : '', excluded ? 'yes' : 'no']);
      });
    }
    const content = csv.map(row => row.map(v => '"' + String(v ?? '').replaceAll('"','""') + '"').join(',')).join('\r\n');
    const a = element('a','');
    a.href = URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8'}));
    a.download = home.ccn + '-' + get('quarter').value + '-daily-staffing.csv';
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  async function annual() {
    const selected = home;
    const out = get('annual');
    out.replaceChildren();
    if (!selected || !get('support').open) return;
    try {
      const data = await read('/data/cost_reports/' + selected.ccn + '.json');
      if (home !== selected) return;
      const years = data.cost_years.slice().sort((a,b) => b.cost_year - a.cost_year);
      if (!years.length) throw Error();
      const label = element('label','Cost-report year ');
      const picker = document.createElement('select');
      selectOptions(picker, years.map(r => [r.cost_year,r.cost_year]));
      label.append(picker);
      const detail = element('p','');
      const source = element('a','Open facility cost report');
      function show() {
        const y = years.find(r => String(r.cost_year) === picker.value);
        const support = y.support_services || {};
        detail.textContent = 'Annual costs per resident day (' + y.period_start + ' to ' + y.period_end + '): ' +
          ['dietary','housekeeping','laundry'].map(k => k + ' ' + (support[k]?.per_resident_day != null ?
            '$' + format(support[k].per_resident_day) : 'unavailable')).join(' · ') + '. These reports measure spending. Daily headcounts for these services are unavailable here.';
        source.href = '/staffing/tools/nursing-home-cost-reports.html?ccn=' + selected.ccn + '&year=' + picker.value;
      }
      picker.addEventListener('change', show);
      show();
      out.replaceChildren(label,detail,source);
    } catch { if (home === selected) out.textContent = 'Annual cost-report detail is unavailable for this facility.'; }
  }
  get('archive').addEventListener('change',openHome);
  get('support').addEventListener('toggle', annual);
  get('quarter').addEventListener('change', () => loadQuarter());
  get('role').addEventListener('change', render);
  get('day').addEventListener('change', render);
  for (const [id, forward] of [['prev',false],['next',true]]) {
    get(id).addEventListener('click', () => {
      const current = get('day').value.replaceAll('-','');
      const next = forward ? dates.find(d => d > current) : dates.findLast(d => d < current);
      if (next) { get('day').value = iso(next); render(); }
    });
  }
  get('export').addEventListener('click',download);
  panel.addEventListener('toggle',openHome);
  function openAnchor() { if (location.hash === '#daily-staffing') panel.open = true; }
  window.addEventListener('hashchange',openAnchor);
  document.querySelectorAll('a[href="#daily-staffing"]').forEach(a => a.addEventListener('click',() => { panel.open = true; }));
  openAnchor();
  window.DanBeemDailyStaffing = {selectFacility(facility) {
    dossier = home = facility;
    get('archive').value = '';
    get('home').textContent = facility ? facility.name + ' · CCN ' + facility.ccn : '';
    openHome();
    if (!home) get('annual').replaceChildren();
  }};
})();
