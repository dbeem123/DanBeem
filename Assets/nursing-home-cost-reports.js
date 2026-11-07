(function (global) {
  'use strict';

  // Nursing Home Cost Reports: DSS annual cost reports linked to CMS staffing, ownership and CHOW records.
  const INDEX_PATH = '/data/ct_nursing_home_cost_reports.json';
  const DETAIL_PATH = ccn => `/data/cost_reports/${ccn}.json`;
  const EXPLORER = '/staffing/tools/nursing-home-staffing-explorer.html';
  const ADMIN = '/staffing/tools/nursing-home-administrator-search.html';
  const MGMT = '/staffing/tools/nursing-home-management-companies.html';
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  let index = null;
  let detail = null;
  let selectedYear = null;
  let stateSort = { key: 'direct_care_per_resident_day', dir: -1 };

  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const norm = t => String(t || '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  const money = v => v == null ? '' : (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString('en-US');
  const money2 = v => v == null ? '' : (v < 0 ? '-$' : '$') + Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const num = (v, d = 0) => v == null ? '' : Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = (v, d = 1) => v == null ? '' : `${(v * 100).toFixed(d)}%`;
  function fmtDate(iso) {
    if (!iso || !/^\d{4}-\d{2}-\d{2}/.test(iso)) return iso || '';
    const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
    return `${MONTHS[m - 1]} ${d}, ${y}`;
  }
  const relLabel = r => r ? `${MONTHS[Number(r.slice(5, 7)) - 1]} ${r.slice(0, 4)}` : '';

  async function getJson(path) {
    if (global.DanBeemData) return global.DanBeemData.loadJson(path);
    const res = await fetch(path);
    if (!res.ok) throw new Error(`${res.status} ${path}`);
    return res.json();
  }

  function stateMedian(year, key) {
    const m = index.statewide_medians[String(year)];
    return m ? m[key] : null;
  }

  // ------------------------------------------------------------------ search
  function renderResults() {
    const q = norm(document.getElementById('cr-search').value);
    const out = document.getElementById('cr-results');
    if (!q) { out.innerHTML = ''; return; }
    const hits = index.facilities.filter(f => norm(`${f.facility_name} ${f.ccn}`).includes(q)).slice(0, 12);
    out.innerHTML = hits.map(f => {
      const years = Object.keys(f.years);
      const span = years.length ? `Cost reports ${years[0]} to ${years[years.length - 1]} (${years.length})` : 'No DSS cost report on file';
      return `<li><button type="button" data-ccn="${esc(f.ccn)}"${detail && detail.ccn === f.ccn ? ' aria-current="true"' : ''}>
        <span class="result-name">${esc(f.facility_name)}</span><span class="status-pill ${f.current ? 'st-active' : 'st-inactive'}">${f.current ? 'Open' : 'Closed or renamed'}</span>
        <span class="result-meta">CCN ${esc(f.ccn)} · ${esc(span)}</span></button></li>`;
    }).join('') || '<li class="subtle">No matching home.</li>';
  }

  // ------------------------------------------------------------------ one home
  function yearRec() { return detail.cost_years.find(y => y.cost_year === selectedYear); }

  function factCard(label, value, sub) {
    return `<div class="fact"><span>${esc(label)}</span><strong>${value}</strong>${sub ? `<div class="subtle">${sub}</div>` : ''}</div>`;
  }

  function vsState(v, key, fmt) {
    const s = stateMedian(selectedYear, key);
    return s == null || v == null ? '' : `Statewide median ${fmt(s)}`;
  }

  // Figures that failed a range check are withheld (shown as a dash) rather than displayed.
  function guarded(y) {
    const d = Object.assign({}, y.direct_care);
    const bad = y.checks.out_of_range || [];
    if (bad.includes('direct care per resident day') || bad.includes('direct care share of expenses')) {
      ['direct_care_per_resident_day', 'direct_care_share_of_expenses', 'direct_care_cost_per_nursing_hour'].forEach(k => { d[k] = null; });
    }
    if (bad.includes('nursing hours per resident day')) { d.nursing_hours_per_resident_day = null; d.direct_care_cost_per_nursing_hour = null; }
    if (bad.includes('resident days vs beds')) {
      ['direct_care_per_resident_day', 'nursing_hours_per_resident_day', 'expenses_per_resident_day', 'revenue_per_resident_day'].forEach(k => { d[k] = null; });
    }
    if (d.operating_margin_nh != null && Math.abs(d.operating_margin_nh) > 0.6) d.operating_margin_nh = null;
    return d;
  }

  function trendTable() {
    const rows = detail.cost_years.map(y => {
      const p = y.pbj_same_period || {};
      const d = guarded(y);
      return `<tr>
        <td data-label="Cost year"><button type="button" data-year="${y.cost_year}">${y.cost_year}</button> ${y.checks.validated ? '' : '<span class="cr-flag">check</span>'}</td>
        <td data-label="Direct care / day" class="cr-num">${money2(d.direct_care_per_resident_day)}</td>
        <td data-label="Statewide median" class="cr-num subtle">${money2(stateMedian(y.cost_year, 'direct_care_per_resident_day'))}</td>
        <td data-label="Share of costs" class="cr-num">${pct(d.direct_care_share_of_expenses)}</td>
        <td data-label="Nursing hrs / day" class="cr-num">${num(d.nursing_hours_per_resident_day, 2)}${p.total_nurse_hprd != null ? ` / ${num(p.total_nurse_hprd, 2)}` : ''}</td>
        <td data-label="Agency (pool)" class="cr-num">${money(y.direct_care.nursing_pool)}</td>
        <td data-label="Mgmt fees" class="cr-num">${money(y.expenses.mgmt_fee_m12)}</td>
        <td data-label="Related parties" class="cr-num">${money(y.related_party_total_reported)}</td>
        <td data-label="Margin" class="cr-num">${pct(d.operating_margin_nh)}</td>
      </tr>`;
    }).join('');
    return `<div class="table-scroll"><table class="stack company-table">
      <caption>Every cost year on file (select a year for its full detail)</caption>
      <thead><tr><th scope="col">Cost year</th><th scope="col">Direct care per resident day</th><th scope="col">CT median</th><th scope="col">Direct care share of costs</th><th scope="col">Nursing hours per resident day (cost report / PBJ)</th><th scope="col">Agency (nursing pool)</th><th scope="col">Management fees</th><th scope="col">Paid to related parties</th><th scope="col">Operating margin</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
  }

  function kvTable(caption, rows) {
    const body = rows.filter(r => r[1] != null && r[1] !== '').map(r => `<tr><th scope="row">${esc(r[0])}</th><td class="cr-num">${r[1]}</td></tr>`).join('');
    return body ? `<div class="table-scroll"><table><caption>${esc(caption)}</caption><tbody>${body}</tbody></table></div>` : '';
  }

  function yearDetail(y) {
    const d = guarded(y), rd = y.resident_days, s = y.salaries, h = y.hours, np = y.nursing_pool, ex = y.expenses,
      rv = y.revenue, bs = y.balance_sheet, p = y.pbj_same_period || {};
    const days = rd.resident_days_total || rd.days_total_care;
    const flags = y.checks.out_of_range.length ? `Outside expected range: ${y.checks.out_of_range.join(', ')}.` : '';
    const checks = Object.entries(y.checks.printed_totals).filter(([k]) => k !== 'has_core').map(([k, v]) => `${k.replace(/_/g, ' ')} ${v ? 'match' : 'do not match'}`).join('; ');
    const mgmt = y.management_services.length ? `<div class="table-scroll"><table class="stack"><caption>Management services the home reported (Schedule C-1)</caption>
      <thead><tr><th scope="col">Company</th><th scope="col">Service</th><th scope="col">Cost</th></tr></thead><tbody>
      ${y.management_services.map(m => `<tr><td data-label="Company">${m.company_id ? `<a href="${MGMT}?company=${esc(m.company_id)}">${esc(m.name)}</a>` : esc(m.name)}</td><td data-label="Service">${esc(m.description)}</td><td data-label="Cost" class="cr-num">${money(m.cost)}</td></tr>`).join('')}
      </tbody></table></div>` : '<p class="subtle">No management services listed on Schedule C-1.</p>';
    const rel = y.related_parties.length ? `<div class="table-scroll"><table class="stack"><caption>Related parties the home reported (page 4), as written</caption>
      <thead><tr><th scope="col">Related party</th><th scope="col">Type</th><th scope="col">As written on the report</th><th scope="col">Cost reported</th><th scope="col">Actual cost to related party</th></tr></thead><tbody>
      ${y.related_parties.map(r => `<tr><td data-label="Related party">${r.company_id ? `<a href="${MGMT}?company=${esc(r.company_id)}">${esc(r.name_guess)}</a>` : esc(r.name_guess)}</td><td data-label="Type">${esc(r.category)}</td><td data-label="As written" class="raw">${esc(r.text)}</td><td data-label="Cost" class="cr-num">${money(r.cost_reported)}</td><td data-label="Actual cost" class="cr-num">${money(r.actual_cost_to_related_party)}</td></tr>`).join('')}
      </tbody></table></div>` : '<p class="subtle">No related parties listed on page 4.</p>';
    const ow = y.owners_on_report;
    const people = (title, list) => list.length ? `<div class="table-scroll"><table class="stack"><caption>${esc(title)}</caption><thead><tr><th scope="col">Name</th><th scope="col">Address as filed</th><th scope="col">% / shares</th></tr></thead><tbody>
      ${list.map(x => `<tr><td data-label="Name">${esc(x.name)}</td><td data-label="Address">${esc(x.address)}</td><td data-label="%" class="cr-num">${x.percent == null ? '' : num(x.percent, x.percent % 1 ? 2 : 0)}</td></tr>`).join('')}</tbody></table></div>` : '';
    const cmsM = y.cms_management_during_year.length ? y.cms_management_during_year.map(m => `<a href="${MGMT}?company=${esc(m.company_id)}">${esc(m.name)}</a>`).join('; ') : 'None reported to CMS for these months';
    const adm = y.administrators_during_year.length ? y.administrators_during_year.map(a => `<a href="${ADMIN}?license=${esc(a.license_number)}">${esc(a.name)}</a>`).join('; ') : 'None in the DPH history for these months';
    const chow = y.chow_during_year.length ? y.chow_during_year.map(c => `${esc(fmtDate(c.effective_date))}: ${esc(c.seller)} to ${esc(c.buyer)}`).join('<br>') : 'None';
    return `
      <h3>Cost year ${y.cost_year} (October 1, ${y.cost_year - 1} to September 30, ${y.cost_year})</h3>
      <p class="subtle">Filed as <strong>${esc(y.name_on_report || '')}</strong>${y.address_on_report ? `, ${esc(y.address_on_report)}` : ''}. Read from ${esc(y.source_file)} (${esc(y.read_method)}). Printed totals: ${esc(checks || 'not checked')}. ${y.checks.validated ? '<span class="cr-ok">Checks passed</span>' : `<span class="cr-flag">Check against the original</span> ${esc(flags)}`}${y.other_filings_same_year ? ` Other filings for this year: ${y.other_filings_same_year.map(esc).join(', ')}.` : ''}</p>
      <div class="facts">
        ${factCard('Direct care per resident day', money2(d.direct_care_per_resident_day), vsState(d.direct_care_per_resident_day, 'direct_care_per_resident_day', money2))}
        ${factCard('Direct care share of costs', pct(d.direct_care_share_of_expenses), vsState(d.direct_care_share_of_expenses, 'direct_care_share_of_expenses', pct))}
        ${factCard('Direct care total', money(d.direct_care_total), `Salaries ${money(d.direct_salaries)} · agency ${money(d.nursing_pool)} · fringe ${money(d.direct_fringe_allocated)}`)}
        ${factCard('Nursing hours per resident day', num(d.nursing_hours_per_resident_day, 2), p.total_nurse_hprd != null ? `PBJ same months ${num(p.total_nurse_hprd, 2)} (cost-report hours are paid hours; PBJ counts hours worked)` : 'No PBJ data for these months')}
        ${factCard('Direct care cost per nursing hour', money2(d.direct_care_cost_per_nursing_hour), vsState(d.direct_care_cost_per_nursing_hour, 'direct_care_cost_per_nursing_hour', money2))}
        ${factCard('Operating margin (nursing home)', pct(d.operating_margin_nh), `Revenue ${money2(d.revenue_per_resident_day)} vs costs ${money2(d.expenses_per_resident_day)} per resident day`)}
        ${factCard('Medicaid share of days', pct((y.payer_mix || {}).medicaid_ct), `Medicare ${pct((y.payer_mix || {}).medicare)} · private ${pct((y.payer_mix || {}).private)}`)}
        ${factCard('Management of record (CMS)', cmsM)}
        ${factCard('Administrators (DPH)', adm)}
        ${factCard('Changes of ownership (CMS)', chow)}
      </div>
      <div class="cr-grid">
        ${kvTable('Resident days (page 8)', [['Certified beds', num(y.capacity.beds_certified)], ['Medicaid (CT)', num(rd.days_medicaid_ct)], ['Medicaid (other states)', num(rd.days_medicaid_other_states)], ['Medicare', num(rd.days_medicare)], ['Private pay', num(rd.days_private)], ['Other payers', num(rd.days_other_payer)], ['Total care days', num(rd.days_total_care)], ['Total resident days', num(days)]])}
        ${kvTable('Nursing salaries and paid hours (page 10)', [['Directors of nursing', s.sal_don == null ? '' : `${money(s.sal_don)} · ${num(h.hrs_don)} h`], ['RN direct care', s.sal_rn_direct == null ? '' : `${money(s.sal_rn_direct)} · ${num(h.hrs_rn_direct)} h`], ['RN administrative', s.sal_rn_admin == null ? '' : `${money(s.sal_rn_admin)} · ${num(h.hrs_rn_admin)} h`], ['LPN direct care', s.sal_lpn_direct == null ? '' : `${money(s.sal_lpn_direct)} · ${num(h.hrs_lpn_direct)} h`], ['LPN administrative', s.sal_lpn_admin == null ? '' : `${money(s.sal_lpn_admin)} · ${num(h.hrs_lpn_admin)} h`], ['Aides and attendants', s.sal_aides == null ? '' : `${money(s.sal_aides)} · ${num(h.hrs_aides)} h`], ['All salaries', s.sal_total == null ? '' : `${money(s.sal_total)} · ${num(h.hrs_total)} h`]])}
        ${kvTable('Owner and administrator pay (page 10)', [['Operators / owners', money(s.sal_owners)], ['Administrator(s)', money(s.sal_administrator)], ['Assistant administrator', money(s.sal_asst_administrator)]])}
        ${kvTable('Agency / nursing pool (page 13)', [['RN', np.pool_rn_direct == null ? '' : `${money(np.pool_rn_direct)} · ${num(np.pool_hrs_rn_direct)} h`], ['RN administrative', money(np.pool_rn_admin)], ['LPN', np.pool_lpn_direct == null ? '' : `${money(np.pool_lpn_direct)} · ${num(np.pool_hrs_lpn_direct)} h`], ['Aides', np.pool_aides == null ? '' : `${money(np.pool_aides)} · ${num(np.pool_hrs_aides)} h`], ['All fees in lieu of salaries', money(np.prof_fees_total)]])}
        ${kvTable('Costs by category (nursing home)', [['Administrative and general', money(ex.ag_total)], ['of which management services (line m12)', money(ex.mgmt_fee_m12)], ['Employee benefits (fringe)', money(y.fringe.fringe_total)], ['Dietary', money(ex.dietary_total)], ['Laundry', money(ex.laundry_total)], ['Housekeeping', money(ex.housekeeping_total)], ['Resident care supplies and services', money(ex.resident_care_total)], ['Maintenance and operating', money(ex.maint_operating_total)], ['Property', money(ex.property_total)], ['Interest', money(ex.interest_total)], ['Insurance', money(ex.insurance_total)], ['Total costs (nursing home)', money(ex.expenses_total_ccnh)], ['Total costs (all levels)', money(ex.expenses_total_all)]])}
        ${kvTable('Revenue (page 30, nursing home)', [['Medicaid (CT)', money(rv.rev_medicaid_ct)], ['Medicare', money(rv.rev_medicare)], ['Private pay and other', money(rv.rev_private)], ['Total resident revenue', money(rv.rev_resident_total)], ['Other revenue', money(rv.rev_other_total)], ['Total revenue (nursing home)', money(rv.rev_total)], ['Total revenue (all levels)', money(rv.rev_total_all)]])}
        ${kvTable('Balance sheet (pages 31 to 36, whole entity)', [['Current assets', money(bs.assets_current)], ['Total assets', money(bs.assets_total)], ['Current liabilities', money(bs.liabilities_current)], ['Long-term liabilities', money(bs.liabilities_long_term)], ['Total liabilities', money(bs.liabilities_total)], ['Net worth', money(bs.net_worth)], ['Net income or deficit', money(bs.net_income_p36)]])}
      </div>
      <h3>Management services</h3>${mgmt}
      <h3>Related parties</h3>${y.related_parties.length ? `<details class="cr-more"><summary>Show ${y.related_parties.length} related-party lines (${money(y.related_party_total_reported)} reported, excluding loans and balances)</summary>${rel}</details>` : rel}
      <h3>Owners and officers listed on the report</h3>
      ${ow.partnership_legal_name ? `<p>Partnership / LLC: <strong>${esc(ow.partnership_legal_name)}</strong></p>` : ''}${ow.corporation_legal_name ? `<p>Corporation: <strong>${esc(ow.corporation_legal_name)}</strong></p>` : ''}
      ${people('Partners / members (page 3)', ow.partners_members)}${people('Directors and officers (page 3A)', ow.directors_officers)}${people('Stockholders owning 10% or more (page 3A)', ow.stockholders_10pct)}
      ${!ow.partners_members.length && !ow.directors_officers.length && !ow.stockholders_10pct.length ? '<p class="subtle">No owners could be read from pages 3 and 3A for this year.</p>' : ''}`;
  }

  function ownersSection() {
    const cur = detail.cms_owners.filter(o => o.current), past = detail.cms_owners.filter(o => !o.current);
    const table = (list, cap) => `<div class="table-scroll"><table class="stack"><caption>${esc(cap)}</caption>
      <thead><tr><th scope="col">Name</th><th scope="col">Role</th><th scope="col">%</th><th scope="col">Since</th><th scope="col">Listed</th><th scope="col">Type and address</th></tr></thead><tbody>
      ${list.map(o => `<tr><td data-label="Name">${esc(o.name)}${o.title ? `<div class="subtle">${esc(o.title)}</div>` : ''}</td><td data-label="Role">${esc(o.role)}</td><td data-label="%" class="cr-num">${o.percent == null ? '' : num(o.percent, o.percent % 1 ? 2 : 0)}</td><td data-label="Since">${esc(o.association_date)}</td><td data-label="Listed">${esc(relLabel(o.first_release))} to ${o.current ? 'now' : esc(relLabel(o.last_release))}</td><td data-label="Type">${esc(o.type)}${o.flags.length ? `<div>${o.flags.map(f => `<span class="tag">${esc(f)}</span>`).join('')}</div>` : ''}${o.address ? `<div class="subtle">${esc(o.address)}</div>` : ''}</td></tr>`).join('')}</tbody></table></div>`;
    if (!detail.cms_owners.length) return '<p class="subtle">No CMS All Owners records were matched to this home.</p>';
    return `${cur.length ? `<details class="cr-more"><summary>Current CMS owners and associated parties (${cur.length}, ${esc(relLabel(detail.cms_owners_window.latest_release))} release)</summary>${table(cur, 'Listed in the latest release')}</details>` : ''}
      ${past.length ? `<details class="cr-more"><summary>Earlier CMS owners and associated parties (${past.length})</summary>${table(past, 'No longer listed')}</details>` : ''}`;
  }

  function chowSection() {
    if (!detail.changes_of_ownership.length) return '<p class="subtle">No change of ownership for this home in the CMS file.</p>';
    return `<div class="table-scroll"><table class="stack"><caption>Changes of ownership reported to CMS</caption>
      <thead><tr><th scope="col">Effective</th><th scope="col">Seller</th><th scope="col">Buyer</th></tr></thead><tbody>
      ${detail.changes_of_ownership.map(c => `<tr><td data-label="Effective">${esc(fmtDate(c.effective_date))}</td><td data-label="Seller">${esc(c.seller)}${c.seller_dba ? `<div class="subtle">d/b/a ${esc(c.seller_dba)}</div>` : ''}</td><td data-label="Buyer">${esc(c.buyer)}${c.buyer_dba ? `<div class="subtle">d/b/a ${esc(c.buyer_dba)}</div>` : ''}</td></tr>`).join('')}</tbody></table></div>`;
  }

  function renderHome() {
    const view = document.getElementById('home-view');
    const years = detail.cost_years.map(y => y.cost_year);
    if (!years.includes(selectedYear)) selectedYear = years[years.length - 1];
    const y = yearRec();
    view.innerHTML = `
      <div class="person-head"><h2 id="home-name" tabindex="-1">${esc(detail.facility_name)}</h2><span class="subtle">CCN ${esc(detail.ccn)} · <a href="${EXPLORER}?ccn=${esc(detail.ccn)}">Facility Explorer</a></span></div>
      ${years.length ? `<div class="year-row" role="group" aria-label="Cost year">${years.map(v => `<button type="button" data-year="${v}" aria-pressed="${v === selectedYear}">${v}</button>`).join('')}</div>` : '<div class="notice">No DSS cost report is on file for this home. Homes that do not take Medicaid, such as many continuing-care retirement community health centers, do not file one.</div>'}
      ${years.length ? `<h3>Year by year</h3>${trendTable()}` : ''}
      ${y ? yearDetail(y) : ''}
      <h3>CMS ownership records</h3>${ownersSection()}
      <h3>Changes of ownership</h3>${chowSection()}
      ${years.length ? '<div class="report-actions no-print"><button id="cr-home-csv" class="action-button secondary" type="button">Download every year for this home (CSV)</button></div>' : ''}
      <p class="microcopy">${esc(detail.caveats[0])} ${esc(detail.caveats[2])}</p>`;
    document.getElementById('cr-home-csv')?.addEventListener('click', downloadHomeCsv);
  }

  async function choose(ccn, scroll) {
    const section = document.getElementById('home-section');
    section.hidden = false;
    document.getElementById('home-view').innerHTML = '<p class="subtle">Loading this home\'s cost reports.</p>';
    try {
      detail = await getJson(DETAIL_PATH(ccn));
    } catch (err) {
      const f = index.facilities.find(x => x.ccn === ccn);
      detail = { ccn, facility_name: f ? f.facility_name : ccn, cost_years: [], cms_owners: [], changes_of_ownership: [], cms_owners_window: {}, caveats: index.caveats };
    }
    const qy = Number(new URLSearchParams(global.location.search).get('year'));
    selectedYear = detail.cost_years.some(y => y.cost_year === qy) ? qy : selectedYear;
    renderHome();
    const url = new URL(global.location.href);
    url.search = `?ccn=${encodeURIComponent(ccn)}${selectedYear ? `&year=${selectedYear}` : ''}`;
    global.history.replaceState(null, '', url);
    renderResults();
    if (scroll) {
      document.getElementById('home-name').focus({ preventScroll: true });
      section.scrollIntoView({ block: 'start' });
    }
  }

  // ------------------------------------------------------------------ statewide year table
  function stateRows() {
    const y = document.getElementById('cr-year').value;
    return index.facilities.filter(f => f.years[y] && f.years[y].validated).map(f => ({ ccn: f.ccn, facility_name: f.facility_name, ...f.years[y] }));
  }

  function renderState() {
    const y = document.getElementById('cr-year').value;
    const rows = stateRows();
    const { key, dir } = stateSort;
    rows.sort((a, b) => {
      const av = a[key], bv = b[key];
      if (typeof av === 'string' || typeof bv === 'string') return dir * String(av || '').localeCompare(String(bv || ''));
      return dir * ((av == null ? -Infinity : av) - (bv == null ? -Infinity : bv));
    });
    const med = index.statewide_medians[y] || {};
    const max = Math.max(...rows.map(r => r.direct_care_per_resident_day || 0), 1);
    document.getElementById('cr-state-summary').textContent = `${rows.length} homes with checked figures for cost year ${y}. Statewide median direct care ${money2(med.direct_care_per_resident_day)} per resident day, ${pct(med.direct_care_share_of_expenses)} of costs.`;
    document.getElementById('cr-state-rows').innerHTML = rows.map(r => `<tr>
      <td data-label="Home"><button type="button" data-ccn="${esc(r.ccn)}">${esc(r.facility_name)}</button></td>
      <td data-label="Direct care / day" class="cr-num"><span class="cr-bar" style="width:${Math.round(60 * (r.direct_care_per_resident_day || 0) / max)}px" aria-hidden="true"></span>${money2(r.direct_care_per_resident_day)}</td>
      <td data-label="Share of costs" class="cr-num">${pct(r.direct_care_share_of_expenses)}</td>
      <td data-label="Nursing hrs / day" class="cr-num">${num(r.nursing_hours_per_resident_day, 2)}${r.pbj_total_nurse_hprd != null ? ` / ${num(r.pbj_total_nurse_hprd, 2)}` : ''}</td>
      <td data-label="Mgmt fees" class="cr-num">${money(r.management_fee)}</td>
      <td data-label="Related parties" class="cr-num">${money(r.related_party_total_reported)}</td>
      <td data-label="Margin" class="cr-num">${pct(r.operating_margin_nh)}</td></tr>`).join('');
  }

  // ------------------------------------------------------------------ CSV
  const csvCell = v => { const t = v == null ? '' : String(v); return /[",\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t; };
  function saveCsv(name, header, rows) {
    const blob = new Blob([[header.join(','), ...rows.map(r => r.map(csvCell).join(','))].join('\n') + '\n'], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
  }
  function downloadHomeCsv() {
    const header = ['ccn', 'home', 'cost_year', 'checks_passed', 'resident_days', 'medicaid_days', 'medicare_days', 'private_days',
      'direct_care_total', 'direct_salaries', 'nursing_pool', 'direct_fringe_allocated', 'direct_care_per_resident_day',
      'direct_care_share_of_costs', 'nursing_hours_reported', 'nursing_hours_per_resident_day', 'pbj_total_nurse_hprd_same_months',
      'management_fees_m12', 'related_party_total', 'total_costs_nh', 'total_revenue_nh', 'operating_margin_nh',
      'net_income_entity', 'total_assets', 'total_liabilities', 'source_file'];
    saveCsv(`ct-cost-reports-${detail.ccn}.csv`, header, detail.cost_years.map(y => [detail.ccn, detail.facility_name, y.cost_year,
      y.checks.validated ? 'yes' : 'no', y.resident_days.resident_days_total, y.resident_days.days_medicaid_ct, y.resident_days.days_medicare,
      y.resident_days.days_private, y.direct_care.direct_care_total, y.direct_care.direct_salaries, y.direct_care.nursing_pool,
      y.direct_care.direct_fringe_allocated, y.direct_care.direct_care_per_resident_day, y.direct_care.direct_care_share_of_expenses,
      y.direct_care.nursing_hours_reported, y.direct_care.nursing_hours_per_resident_day, (y.pbj_same_period || {}).total_nurse_hprd,
      y.expenses.mgmt_fee_m12, y.related_party_total_reported, y.expenses.expenses_total_ccnh, y.revenue.rev_total,
      y.direct_care.operating_margin_nh, y.balance_sheet.net_income_p36, y.balance_sheet.assets_total, y.balance_sheet.liabilities_total, y.source_file]));
  }
  function downloadStateCsv() {
    const y = document.getElementById('cr-year').value;
    const header = ['ccn', 'home', 'cost_year', 'direct_care_per_resident_day', 'direct_care_share_of_costs', 'nursing_hours_per_resident_day',
      'pbj_total_nurse_hprd_same_months', 'expenses_per_resident_day', 'management_fees_m12', 'related_party_total', 'operating_margin_nh', 'medicaid_share_of_days'];
    saveCsv(`ct-cost-reports-${y}.csv`, header, stateRows().map(r => [r.ccn, r.facility_name, y, r.direct_care_per_resident_day,
      r.direct_care_share_of_expenses, r.nursing_hours_per_resident_day, r.pbj_total_nurse_hprd, r.expenses_per_resident_day,
      r.management_fee, r.related_party_total_reported, r.operating_margin_nh, r.medicaid_share_of_days]));
  }

  // ------------------------------------------------------------------ init
  function renderSources() {
    document.getElementById('cr-sources').innerHTML = index.sources.map(s => `<li>${s.url ? `<a href="${esc(s.url)}" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}${s.as_of ? `, as of ${esc(s.as_of)}` : ''}. <span class="subtle">${esc(s.note || '')}</span></li>`).join('');
    document.getElementById('cr-method').innerHTML = Object.entries(index.method).map(([k, v]) => `<li><strong>${esc(k.replace(/_/g, ' '))}:</strong> ${esc(v)}</li>`).join('');
    document.getElementById('cr-caveats').innerHTML = index.caveats.map(c => `<li>${esc(c)}</li>`).join('');
    document.getElementById('cr-corrections').innerHTML = esc(index.corrections_notice).replace('hello@danbeem.xyz', '<a href="mailto:hello@danbeem.xyz">hello@danbeem.xyz</a>');
  }

  async function init() {
    const note = document.getElementById('cr-note');
    try {
      index = await getJson(INDEX_PATH);
    } catch (err) {
      note.textContent = `Cost-report records could not be loaded. Details: ${err.message}`;
      note.className = 'notice error';
      return;
    }
    const s = index.summary;
    const years = Object.keys(index.statewide_medians);
    note.textContent = `${s.home_years.toLocaleString('en-US')} cost reports from ${s.homes_with_reports} homes, cost years ${years[0]} to ${years[years.length - 1]}; ${s.validated_home_years.toLocaleString('en-US')} passed every check.`;
    renderSources();
    const search = document.getElementById('cr-search');
    search.disabled = false;
    search.addEventListener('input', renderResults);
    document.getElementById('cr-results').addEventListener('click', e => { const b = e.target.closest('button[data-ccn]'); if (b) choose(b.dataset.ccn, true); });
    document.getElementById('home-view').addEventListener('click', e => {
      const b = e.target.closest('button[data-year]');
      if (!b) return;
      selectedYear = Number(b.dataset.year);
      renderHome();
      const url = new URL(global.location.href);
      url.searchParams.set('year', selectedYear);
      global.history.replaceState(null, '', url);
    });
    const ysel = document.getElementById('cr-year');
    ysel.innerHTML = years.slice().reverse().map(y => `<option value="${y}">${y}</option>`).join('');
    ysel.disabled = false;
    ysel.addEventListener('change', renderState);
    document.querySelector('#cr-state-table thead').addEventListener('click', e => {
      const b = e.target.closest('button[data-sort]');
      if (!b) return;
      stateSort = { key: b.dataset.sort, dir: stateSort.key === b.dataset.sort ? -stateSort.dir : (b.dataset.sort === 'facility_name' ? 1 : -1) };
      renderState();
    });
    document.getElementById('cr-state-rows').addEventListener('click', e => { const b = e.target.closest('button[data-ccn]'); if (b) choose(b.dataset.ccn, true); });
    document.getElementById('cr-state-csv').addEventListener('click', downloadStateCsv);
    renderState();
    const ccn = new URLSearchParams(global.location.search).get('ccn');
    if (ccn && /^\d{6}$/.test(ccn)) choose(ccn, false);
  }

  document.addEventListener('DOMContentLoaded', init);
})(window);
