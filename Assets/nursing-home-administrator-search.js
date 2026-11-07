(function (global) {
  'use strict';

  const DATA_PATH = '/data/ct_nursing_home_administrators.json';
  const EXPLORER = '/staffing/tools/nursing-home-staffing-explorer.html';
  const COST_PAGE = '/staffing/tools/nursing-home-cost-reports.html';
  const ELICENSE = 'https://elicense.ct.gov/Lookup/LicenseLookup.aspx';
  const MAX_RESULTS = 50;
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  let data = null;
  let people = [];
  let byId = new Map();
  let byLicense = new Map();
  let current = null;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, ch => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  }

  function fmtDate(iso) {
    if (!iso) return '';
    const [y, m, d] = iso.split('-').map(Number);
    return `${MONTHS[m - 1]} ${d}, ${y}`;
  }

  function quarterLabel(q) {
    return q ? `Q${q.slice(5)} ${q.slice(0, 4)}` : '';
  }

  function norm(text) {
    return String(text || '').toLowerCase().normalize('NFKD').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function startLabel(role) {
    return role.start ? fmtDate(role.start) : 'Start not recorded';
  }

  function endLabel(role) {
    if (role.end) return fmtDate(role.end);
    return role.open ? `Open as of ${fmtDate(data.source_as_of)}` : 'End not recorded';
  }

  function statusClass(status) {
    const s = String(status || '').toUpperCase();
    if (s.startsWith('ACTIVE')) return 'st-active';
    if (s === 'INACTIVE') return 'st-inactive';
    return '';
  }

  function facilityCount(person) {
    return new Set(person.roles.map(r => r.facility_license)).size;
  }

  function search(query) {
    const q = norm(query);
    if (!q) return [];
    if (/^\d+$/.test(q)) {
      const exact = byLicense.get(String(Number(q)));
      return exact ? [exact] : people.filter(p => p.license_number.startsWith(q));
    }
    const terms = q.split(' ');
    return people.filter(p => {
      const hay = p._search;
      return terms.every(t => hay.includes(t));
    });
  }

  function renderResults(list, query) {
    const out = document.getElementById('admin-results');
    const count = document.getElementById('result-count');
    if (!query.trim()) {
      out.innerHTML = '';
      count.textContent = '';
      return;
    }
    count.textContent = list.length
      ? `${list.length} ${list.length === 1 ? 'administrator' : 'administrators'} found${list.length > MAX_RESULTS ? `; showing the first ${MAX_RESULTS}` : ''}.`
      : 'No administrators match. Try a last name only, or a license number.';
    out.innerHTML = list.slice(0, MAX_RESULTS).map(p => {
      const n = facilityCount(p);
      return `<li><button type="button" data-person="${esc(p.id)}"${current && current.id === p.id ? ' aria-current="true"' : ''}>
        <span class="result-name">${esc(p.name)}</span>
        <span class="status-pill ${statusClass(p.license_status)}">${esc(p.license_status || 'Status not recorded')}</span>
        <span class="result-meta">License ${esc(p.license_number)} · ${n} ${n === 1 ? 'home' : 'homes'} on record</span>
      </button></li>`;
    }).join('');
  }

  function contextText(role) {
    const ctx = role.context;
    if (!role.ccn) return 'No CMS match for this home.';
    if (!ctx) return role.start ? 'Not available.' : 'Start not recorded, so the period cannot be matched to staffing data.';
    if (!ctx.quarters) {
      const before = (role.end || '9999') < '2017-10-01';
      return before ? 'Before CMS staffing data begins (Q4 2017).' : 'No full staffing quarter falls in this period.';
    }
    const span = ctx.first_quarter === ctx.last_quarter ? quarterLabel(ctx.first_quarter)
      : `${quarterLabel(ctx.first_quarter)} to ${quarterLabel(ctx.last_quarter)}`;
    const parts = [];
    if (ctx.ct_direct_care_hprd != null) parts.push(`CT direct-care estimate ${ctx.ct_direct_care_hprd.toFixed(2)}`);
    if (ctx.rn_hprd != null) parts.push(`RN ${ctx.rn_hprd.toFixed(2)}`);
    return `${span} (${ctx.quarters} ${ctx.quarters === 1 ? 'quarter' : 'quarters'}): ${parts.join('; ')} hours per resident day.`;
  }

  function timeline(person) {
    const asOf = data.source_as_of;
    const dates = person.roles.flatMap(r => [r.start, r.end]).filter(Boolean);
    if (!dates.length) return '<p class="subtle">No dates were recorded for these roles, so no timeline can be drawn.</p>';
    const minYear = Number(dates.reduce((a, b) => (a < b ? a : b)).slice(0, 4));
    const lo = new Date(`${minYear}-01-01`).getTime();
    const hi = new Date(asOf).getTime();
    const pct = iso => Math.max(0, Math.min(100, ((new Date(iso).getTime() - lo) / (hi - lo)) * 100));
    const rows = person.roles.map(role => {
      let left;
      let right;
      let cls = '';
      if (role.start) {
        left = pct(role.start);
        right = role.end ? pct(role.end) : (role.open ? 100 : left + 2);
        if (!role.end) cls = role.open ? 'open' : 'partial';
      } else if (role.end) {
        right = pct(role.end);
        left = Math.max(0, right - 2);
        cls = 'partial';
      }
      if (role.overlap) cls += ' overlap';
      const bar = left == null ? '' : `<i class="${cls.trim()}" style="left:${left.toFixed(2)}%;width:${Math.max(0.6, right - left).toFixed(2)}%"></i>`;
      return `<li>
        <div class="lbl"><strong>${esc(role.facility_name)}</strong>${esc(startLabel(role))} to ${esc(endLabel(role))}${role.overlap ? ' <span class="tag overlap">Overlapping dates as reported</span>' : ''}</div>
        <div class="track" aria-hidden="true">${bar}</div>
      </li>`;
    }).join('');
    const mid = Math.round((minYear + Number(asOf.slice(0, 4))) / 2);
    return `<ol class="tenure" aria-label="Tenure timeline, ${esc(person.name)}">${rows}</ol>
      <div class="axis-row" aria-hidden="true"><span></span><div class="axis"><span>${minYear}</span><span>${mid}</span><span>${esc(fmtDate(asOf))}</span></div></div>
      <div class="legend" aria-hidden="true"><span>Recorded dates</span><span class="lg-open">Open as of the source date</span><span class="lg-partial">Start or end not recorded</span><span class="lg-overlap">Overlapping dates as reported</span></div>`;
  }

  function roleTable(person) {
    const rows = person.roles.map(role => `<tr>
      <td data-label="Home">${role.ccn ? `<a href="${EXPLORER}?ccn=${esc(role.ccn)}">${esc(role.facility_name)}</a>` : esc(role.facility_name)}<div class="subtle">DPH license ${esc(role.facility_license)}${role.ccn ? ` · CCN ${esc(role.ccn)} · <a href="${COST_PAGE}?ccn=${esc(role.ccn)}">Cost reports</a>` : ''}</div></td>
      <td data-label="Start">${esc(startLabel(role))}</td>
      <td data-label="End">${esc(endLabel(role))}${role.overlap ? '<div><span class="tag overlap">Overlapping dates as reported</span></div>' : ''}</td>
      <td data-label="Staffing" class="ctx">${esc(contextText(role))}</td>
    </tr>`).join('');
    return `<div class="table-scroll"><table class="stack">
      <caption>Homes where ${esc(person.name)} was administrator of record</caption>
      <thead><tr><th scope="col">Home</th><th scope="col">Start</th><th scope="col">End</th><th scope="col">Home's staffing during this period</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
  }

  function renderPerson(person) {
    current = person;
    const section = document.getElementById('person-section');
    const view = document.getElementById('person-view');
    section.hidden = false;
    const n = facilityCount(person);
    view.innerHTML = `
      <div class="person-head">
        <h2 id="person-name" tabindex="-1">${esc(person.name)}</h2>
        <span class="status-pill ${statusClass(person.license_status)}">${esc(person.license_status || 'Status not recorded')}</span>
      </div>
      ${person.other_names.length ? `<p class="subtle">Also recorded as: ${person.other_names.map(esc).join('; ')}</p>` : ''}
      <div class="facts">
        <div class="fact"><span>License number</span><strong>${esc(person.license_number)}</strong></div>
        <div class="fact"><span>License status</span><strong>${esc(person.license_status || 'Not recorded')}</strong><div class="subtle">As of ${esc(fmtDate(person.license_status_as_of))}</div></div>
        <div class="fact"><span>Issued</span><strong>${esc(person.license_issued ? fmtDate(person.license_issued) : 'Not recorded')}</strong></div>
        <div class="fact"><span>Expires</span><strong>${esc(person.license_expires ? fmtDate(person.license_expires) : 'Not recorded')}</strong></div>
        <div class="fact"><span>Homes on record</span><strong>${n}</strong></div>
      </div>
      <p class="subtle">Check the current license in <a href="${ELICENSE}" rel="noopener">Connecticut's eLicense lookup</a> (choose Nursing Home Administrator).</p>
      <h3>Tenure timeline</h3>
      ${timeline(person)}
      <h3>Homes and staffing during each tenure</h3>
      ${roleTable(person)}
      <div class="report-actions no-print"><button id="admin-csv" class="action-button secondary" type="button">Download these records (CSV)</button></div>
      <div class="notice warning">Staffing figures are the home's CMS Payroll-Based Journal averages for the quarters whose midpoint falls within the tenure, weighted by resident days. Facility conditions during this period reflect many factors and are not a measure of the administrator's performance.</div>`;
    document.getElementById('admin-csv').addEventListener('click', () => downloadCsv(person));
    document.querySelectorAll('#admin-results button').forEach(b => {
      if (b.dataset.person === person.id) b.setAttribute('aria-current', 'true');
      else b.removeAttribute('aria-current');
    });
  }

  function csvCell(value) {
    const text = value == null ? '' : String(value);
    return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }

  function downloadCsv(person) {
    const header = ['administrator', 'license_number', 'license_status', 'license_status_as_of', 'home',
      'dph_facility_license', 'ccn', 'start', 'end', 'open_as_of_source', 'overlapping_dates_as_reported',
      'staffing_first_quarter', 'staffing_last_quarter', 'staffing_quarters', 'ct_direct_care_hprd',
      'total_nurse_hprd', 'rn_hprd', 'source_as_of'];
    const lines = [header.join(',')];
    person.roles.forEach(r => {
      const c = r.context || {};
      lines.push([person.name, person.license_number, person.license_status, person.license_status_as_of,
        r.facility_name, r.facility_license, r.ccn, r.start, r.end, r.open && !r.end ? 'yes' : 'no',
        r.overlap ? 'yes' : 'no', c.first_quarter, c.last_quarter, c.quarters, c.ct_direct_care_hprd,
        c.total_nurse_hprd, c.rn_hprd, data.source_as_of].map(csvCell).join(','));
    });
    const blob = new Blob([lines.join('\n') + '\n'], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `ct-administrator-${person.license_number}.csv`;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => { URL.revokeObjectURL(link.href); link.remove(); }, 0);
  }

  function setUrl(params) {
    const url = new URL(global.location.href);
    url.search = '';
    Object.entries(params).forEach(([k, v]) => { if (v) url.searchParams.set(k, v); });
    global.history.replaceState(null, '', url);
  }

  function choose(id) {
    const person = byId.get(id);
    if (!person) return;
    renderPerson(person);
    setUrl({ license: person.license_number });
    document.getElementById('person-name').focus({ preventScroll: true });
    document.getElementById('person-section').scrollIntoView({ block: 'start' });
  }

  function renderSources() {
    document.getElementById('admin-sources').innerHTML = data.sources.map(s => `<li>${s.url ? `<a href="${esc(s.url)}" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}${s.as_of ? `, as of ${esc(/^\d{4}-\d{2}-\d{2}$/.test(s.as_of) ? fmtDate(s.as_of) : quarterLabel(s.as_of))}` : ''}. <span class="subtle">${esc(s.note || '')}</span></li>`).join('');
    const missing = data.coverage.cms_homes_not_in_dph_export || [];
    document.getElementById('admin-coverage').innerHTML = `<p>Covers ${data.coverage.facilities} Connecticut chronic and convalescent nursing homes, all matched to a CMS number, with ${data.summary.people} licensed administrators and recorded dates from ${esc(fmtDate(data.summary.earliest_role_date))} to ${esc(fmtDate(data.summary.latest_role_date))}.</p>`
      + (missing.length ? `<p>These homes appear in CMS staffing data but not in the DPH export, so no administrator history is shown for them: ${missing.map(m => esc(m.name)).join('; ')}.</p>` : '');
    document.getElementById('admin-caveats').innerHTML = data.caveats.map(c => `<li>${esc(c)}</li>`).join('');
    document.getElementById('admin-corrections').innerHTML = esc(data.corrections_notice).replace('hello@danbeem.xyz', '<a href="mailto:hello@danbeem.xyz">hello@danbeem.xyz</a>');
  }

  async function init() {
    const note = document.getElementById('search-note');
    try {
      data = global.DanBeemData ? await global.DanBeemData.loadJson(DATA_PATH)
        : await (await fetch(DATA_PATH)).json();
    } catch (err) {
      note.textContent = `Administrator records could not be loaded. Details: ${err.message}`;
      note.className = 'notice error';
      return;
    }
    people = data.people.map(p => Object.assign(p, {
      _search: norm([p.name, ...p.other_names, p.license_number].join(' ')),
    }));
    byId = new Map(people.map(p => [p.id, p]));
    byLicense = new Map(people.map(p => [p.license_number, p]));
    note.textContent = `${data.summary.people} administrators and ${data.coverage.facilities} homes, from DPH records downloaded ${fmtDate(data.source_as_of)}.`;
    renderSources();

    const form = document.getElementById('admin-search-form');
    const input = document.getElementById('admin-query');
    input.disabled = false;
    form.querySelector('button').disabled = false;
    const run = () => renderResults(search(input.value), input.value);
    input.addEventListener('input', run);
    form.addEventListener('submit', event => {
      event.preventDefault();
      run();
      const first = document.querySelector('#admin-results button');
      if (first && document.querySelectorAll('#admin-results button').length === 1) choose(first.dataset.person);
    });
    document.getElementById('admin-results').addEventListener('click', event => {
      const button = event.target.closest('button[data-person]');
      if (button) choose(button.dataset.person);
    });

    const params = new URLSearchParams(global.location.search);
    const license = (params.get('license') || '').replace(/\D/g, '');
    const query = params.get('q') || '';
    if (license && byLicense.has(String(Number(license)))) {
      const person = byLicense.get(String(Number(license)));
      input.value = person.license_number;
      renderResults([person], input.value);
      renderPerson(person);
    } else if (query) {
      input.value = query;
      run();
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})(window);
