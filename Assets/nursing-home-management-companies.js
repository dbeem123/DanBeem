(function (global) {
  'use strict';

  const DATA_PATH = '/data/ct_nursing_home_management_companies.json';
  const EXPLORER = '/staffing/tools/nursing-home-staffing-explorer.html';
  const ADMIN = '/staffing/tools/nursing-home-administrator-search.html';
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  let data = null;
  let byId = new Map();

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
    return String(text || '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function startText(h) {
    return `${fmtDate(h.start)}${h.start_basis === 'association date reported to CMS' ? '' : ' (first listed)'}`;
  }

  function endText(h) {
    if (h.current) return `Current as of ${fmtDate(data.source_as_of)}`;
    return h.ended_before ? `Ended between ${fmtDate(h.end)} and ${fmtDate(h.ended_before)}` : `Last listed ${fmtDate(h.end)}`;
  }

  function contextText(h) {
    const ctx = h.context;
    if (!ctx) return 'Not available.';
    if (!ctx.quarters) return (h.end || '9999') < '2017-10-01' ? 'Before CMS staffing data begins (Q4 2017).' : 'No full staffing quarter in this period.';
    const span = ctx.first_quarter === ctx.last_quarter ? quarterLabel(ctx.first_quarter)
      : `${quarterLabel(ctx.first_quarter)} to ${quarterLabel(ctx.last_quarter)}`;
    const parts = [];
    if (ctx.ct_direct_care_hprd != null) parts.push(`CT direct-care estimate ${ctx.ct_direct_care_hprd.toFixed(2)}`);
    if (ctx.rn_hprd != null) parts.push(`RN ${ctx.rn_hprd.toFixed(2)}`);
    return `${span} (${ctx.quarters} ${ctx.quarters === 1 ? 'quarter' : 'quarters'}): ${parts.join('; ')} hours per resident day.`;
  }

  function adminList(h) {
    if (!h.administrators.length) return '<span class="subtle">None recorded in the DPH history for this period.</span>';
    return `<ul class="admin-list">${h.administrators.map(a => {
      const dates = `${a.start ? fmtDate(a.start) : 'start not recorded'} to ${a.end ? fmtDate(a.end) : (a.open ? 'open' : 'end not recorded')}`;
      const name = a.person_id ? `<a href="${ADMIN}?license=${esc(a.license_number)}">${esc(a.name)}</a>` : `${esc(a.name)} <span class="subtle">(no license number recorded)</span>`;
      return `<li>${name} <span class="subtle">${esc(dates)}</span></li>`;
    }).join('')}</ul>`;
  }

  function renderList() {
    const q = norm(document.getElementById('mc-filter').value);
    const onlyCurrent = document.getElementById('mc-current').checked;
    const list = data.companies.filter(c => (!onlyCurrent || c.homes_current > 0)
      && (!q || norm([c.name, ...c.other_names].join(' ')).includes(q)));
    document.getElementById('mc-count').textContent = `${list.length} of ${data.companies.length} organizations shown.`;
    document.getElementById('mc-rows').innerHTML = list.map(c => `<tr>
      <td data-label="Organization"><button type="button" data-company="${esc(c.id)}">${esc(c.name)}</button></td>
      <td data-label="Homes now">${c.homes_current}</td>
      <td data-label="Since 2020">${c.homes_total}</td>
      <td data-label="DPH license">${c.dph_license ? `${esc(c.dph_license.license_number)} <span class="subtle">${esc(c.dph_license.status)}</span>` : '<span class="subtle">Not matched</span>'}</td>
    </tr>`).join('');
  }

  function timeline(company) {
    const asOf = data.source_as_of;
    const minYear = Math.min(2020, ...company.homes.map(h => Number(h.start.slice(0, 4))));
    const lo = new Date(`${minYear}-01-01`).getTime();
    const hi = new Date(asOf).getTime();
    const pct = iso => Math.max(0, Math.min(100, ((new Date(iso).getTime() - lo) / (hi - lo)) * 100));
    const rows = company.homes.map(h => {
      const left = pct(h.start);
      const right = h.current ? 100 : pct(h.end);
      return `<li><div class="lbl"><strong>${esc(h.facility_name)}</strong>${esc(startText(h))} to ${esc(endText(h))}</div>
        <div class="track" aria-hidden="true"><i class="${h.current ? 'open' : ''}" style="left:${left.toFixed(2)}%;width:${Math.max(0.6, right - left).toFixed(2)}%"></i></div></li>`;
    }).join('');
    const mid = Math.round((minYear + Number(asOf.slice(0, 4))) / 2);
    return `<ol class="tenure" aria-label="Management timeline, ${esc(company.name)}">${rows}</ol>
      <div class="axis-row" aria-hidden="true"><span></span><div class="axis"><span>${minYear}</span><span>${mid}</span><span>${esc(fmtDate(asOf))}</span></div></div>
      <div class="legend" aria-hidden="true"><span>Management period</span><span class="lg-open">Current as of the latest CMS release</span></div>`;
  }

  function renderCompany(company) {
    const lic = company.dph_license;
    const dphLoaded = data.sources.some(s => /DPH/.test(s.title) && s.as_of);
    document.getElementById('company-section').hidden = false;
    document.getElementById('company-view').innerHTML = `
      <div class="person-head"><h2 id="company-name" tabindex="-1">${esc(company.name)}</h2></div>
      ${company.other_names.length ? `<p class="subtle">Also reported as: ${company.other_names.map(esc).join('; ')}</p>` : ''}
      <div class="facts">
        <div class="fact"><span>Homes managed now</span><strong>${company.homes_current}</strong><div class="subtle">As of ${esc(fmtDate(data.source_as_of))}</div></div>
        <div class="fact"><span>Homes since 2020</span><strong>${company.homes_total}</strong></div>
        <div class="fact"><span>DPH management license</span><strong>${lic ? esc(lic.license_number) : (dphLoaded ? 'Not matched' : 'Not yet checked')}</strong>${lic ? `<div class="subtle">${esc(lic.status)}${lic.expires ? `, expires ${esc(fmtDate(lic.expires))}` : ''}</div>` : ''}</div>
      </div>
      ${company.homes.length ? '' : `<div class="notice">This company holds a Connecticut DPH management company license, but no CMS ownership record from ${esc(fmtDate(data.window.first_release))} to ${esc(fmtDate(data.window.latest_release))} lists an organization with this name as having managerial control of a Connecticut home. It may be reported under a different name or another role, or it may manage homes outside Connecticut.</div>`}
      ${company.homes.length ? `<h3>Management timeline</h3>${timeline(company)}` : ''}
      ${company.homes.length ? `<h3>Homes, staffing and administrators during each period</h3>
      <div class="table-scroll"><table class="stack">
        <caption>Homes where ${esc(company.name)} was reported with managerial control</caption>
        <thead><tr><th scope="col">Home</th><th scope="col">Period</th><th scope="col">Home's staffing during this period</th><th scope="col">Administrators of record during this period</th></tr></thead>
        <tbody>${company.homes.map(h => `<tr>
          <td data-label="Home"><a href="${EXPLORER}?ccn=${esc(h.ccn)}">${esc(h.facility_name)}</a><div class="subtle">CCN ${esc(h.ccn)} · ${esc(h.role)}</div></td>
          <td data-label="Period">${esc(startText(h))}<br>${esc(endText(h))}${h.later_association_dates.length ? `<div class="subtle">CMS later reported ${h.later_association_dates.map(fmtDate).map(esc).join(', ')}</div>` : ''}</td>
          <td data-label="Staffing" class="ctx">${esc(contextText(h))}</td>
          <td data-label="Administrators">${adminList(h)}</td>
        </tr>`).join('')}</tbody>
      </table></div>
      <div class="report-actions no-print"><button id="mc-csv" class="action-button secondary" type="button">Download these records (CSV)</button></div>
      <div class="notice warning">Staffing figures are the home's CMS Payroll-Based Journal averages for the quarters whose midpoint falls in the period, weighted by resident days. Facility conditions during this period reflect many factors and are not a measure of the management company's performance.</div>` : ''}`;
    document.getElementById('mc-csv')?.addEventListener('click', () => downloadCsv(company));
    renderDssFees(company);
  }

  // Management fees the homes themselves reported on DSS cost reports (Schedule C-1), by cost year.
  const COST_PATH = '/data/ct_nursing_home_cost_reports.json';
  const COST_PAGE = '/staffing/tools/nursing-home-cost-reports.html';
  let costPromise = null;
  async function renderDssFees(company) {
    const view = document.getElementById('company-view');
    document.getElementById('mc-dss-fees')?.remove();
    const box = document.createElement('div');
    box.id = 'mc-dss-fees';
    view.after(box);
    try {
      if (!costPromise) costPromise = global.DanBeemData ? global.DanBeemData.loadJson(COST_PATH) : fetch(COST_PATH).then(r => r.json());
      const cost = await costPromise;
      const fees = (cost.management_fees_by_company || {})[company.id];
      if (!fees) {
        box.innerHTML = '<h3>Management fees reported to DSS</h3><p class="subtle">No Connecticut DSS cost report lists this company by name on its management services schedule (Schedule C-1).</p>';
        return;
      }
      const names = new Map(cost.facilities.map(f => [f.ccn, f.facility_name]));
      const money = v => `$${Math.round(v).toLocaleString('en-US')}`;
      box.innerHTML = `<h3>Management fees reported to DSS</h3>
        <div class="table-scroll"><table class="stack"><caption>Fees the homes reported paying this company (DSS cost reports, Schedule C-1), by cost year ending September 30</caption>
        <thead><tr><th scope="col">Cost year</th><th scope="col">Total reported</th><th scope="col">Homes</th></tr></thead><tbody>
        ${Object.entries(fees).reverse().map(([y, v]) => `<tr><td data-label="Cost year">${esc(y)}</td><td data-label="Total">${money(v.total)}</td>
          <td data-label="Homes">${v.homes.map(h => `<a href="${COST_PAGE}?ccn=${esc(h.ccn)}&year=${esc(y)}">${esc(names.get(h.ccn) || h.ccn)}</a> ${money(h.amount)}`).join('; ')}</td></tr>`).join('')}
        </tbody></table></div>
        <p class="microcopy">As reported by each home before DSS audit. A company can be paid under a different name; only schedule lines naming this company are counted.</p>`;
    } catch (err) {
      box.innerHTML = `<p class="notice error">DSS cost-report records could not be loaded. Details: ${esc(err.message)}</p>`;
    }
  }

  function csvCell(value) {
    const text = value == null ? '' : String(value);
    return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }

  function downloadCsv(company) {
    const header = ['organization', 'home', 'ccn', 'role', 'start', 'start_basis', 'end_last_listed', 'ended_before',
      'current', 'staffing_first_quarter', 'staffing_last_quarter', 'staffing_quarters', 'ct_direct_care_hprd',
      'total_nurse_hprd', 'rn_hprd', 'administrators_during_period', 'source_as_of'];
    const lines = [header.join(',')];
    company.homes.forEach(h => {
      const c = h.context || {};
      lines.push([company.name, h.facility_name, h.ccn, h.role, h.start, h.start_basis, h.end, h.ended_before,
        h.current ? 'yes' : 'no', c.first_quarter, c.last_quarter, c.quarters, c.ct_direct_care_hprd,
        c.total_nurse_hprd, c.rn_hprd, h.administrators.map(a => a.name).join('; '), data.source_as_of].map(csvCell).join(','));
    });
    const blob = new Blob([lines.join('\n') + '\n'], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `ct-management-${company.id}.csv`;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => { URL.revokeObjectURL(link.href); link.remove(); }, 0);
  }

  function choose(id, scroll) {
    const company = byId.get(id);
    if (!company) return;
    renderCompany(company);
    const url = new URL(global.location.href);
    url.search = `?company=${encodeURIComponent(id)}`;
    global.history.replaceState(null, '', url);
    if (scroll) {
      document.getElementById('company-name').focus({ preventScroll: true });
      document.getElementById('company-section').scrollIntoView({ block: 'start' });
    }
  }

  function renderSources() {
    document.getElementById('mc-sources').innerHTML = data.sources.map(s => `<li>${s.url ? `<a href="${esc(s.url)}" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}${s.as_of ? `, as of ${esc(/^\d{4}-\d{2}-\d{2}$/.test(s.as_of) ? fmtDate(s.as_of) : quarterLabel(s.as_of))}` : ''}. <span class="subtle">${esc(s.note || '')}</span></li>`).join('');
    document.getElementById('mc-caveats').innerHTML = data.caveats.map(c => `<li>${esc(c)}</li>`).join('');
    document.getElementById('mc-corrections').innerHTML = esc(data.corrections_notice).replace('hello@danbeem.xyz', '<a href="mailto:hello@danbeem.xyz">hello@danbeem.xyz</a>');
  }

  async function init() {
    const note = document.getElementById('mc-note');
    try {
      data = global.DanBeemData ? await global.DanBeemData.loadJson(DATA_PATH) : await (await fetch(DATA_PATH)).json();
    } catch (err) {
      note.textContent = `Management records could not be loaded. Details: ${err.message}`;
      note.className = 'notice error';
      return;
    }
    byId = new Map(data.companies.map(c => [c.id, c]));
    const s = data.summary;
    const listed = data.companies.filter(c => c.homes.length).length;
    note.textContent = `${listed} organizations reported to CMS with managerial control of ${s.homes} Connecticut homes in ${data.window.releases} monthly releases, ${fmtDate(data.window.first_release)} to ${fmtDate(data.window.latest_release)}.`
      + (s.dph_licensed_without_cms_listing ? ` Also listed: ${s.dph_licensed_without_cms_listing} DPH-licensed management companies with no CMS management listing under the same name.` : '');
    renderSources();
    const filter = document.getElementById('mc-filter');
    const current = document.getElementById('mc-current');
    filter.disabled = false;
    current.disabled = false;
    filter.addEventListener('input', renderList);
    current.addEventListener('change', renderList);
    document.getElementById('mc-rows').addEventListener('click', event => {
      const button = event.target.closest('button[data-company]');
      if (button) choose(button.dataset.company, true);
    });
    renderList();
    const id = new URLSearchParams(global.location.search).get('company');
    if (id && byId.has(id)) choose(id, false);
  }

  document.addEventListener('DOMContentLoaded', init);
})(window);
