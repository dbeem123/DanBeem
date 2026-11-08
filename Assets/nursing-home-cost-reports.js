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
  let supportSort = { key: 'metric', dir: -1 };
  // Statewide cost explorer: one metric at a time (per resident day). 'cat' marks a category of total costs.
  const METRICS = [
    ['expenses_per_resident_day', 'Total costs', 'Totals'],
    ['direct_care_per_resident_day', 'Nursing care (direct care)', 'Categories', 'nursing'],
    ['dietary_per_resident_day', 'Dietary, all-in', 'Categories', 'dietary'],
    ['housekeeping_per_resident_day', 'Housekeeping, all-in', 'Categories', 'housekeeping'],
    ['laundry_per_resident_day', 'Laundry, all-in', 'Categories', 'laundry'],
    ['other_staff_per_resident_day', 'All other staff and benefits', 'Categories', 'other_staff'],
    ['other_fees_per_resident_day', 'Other professional fees', 'Categories', 'other_fees'],
    ['admin_per_resident_day', 'Administrative and general', 'Categories', 'admin'],
    ['resident_care_per_resident_day', 'Resident care supplies and services', 'Categories', 'resident_care'],
    ['plant_per_resident_day', 'Plant operation and utilities', 'Categories', 'plant'],
    ['property_per_resident_day', 'Building and property', 'Categories', 'property'],
    ['interest_per_resident_day', 'Interest', 'Categories', 'interest'],
    ['insurance_per_resident_day', 'Insurance', 'Categories', 'insurance'],
    ['raw_food_per_resident_day', 'Raw food (homes that buy their own)', 'Details'],
    ['management_fees_per_resident_day', 'Management fees (line m12)', 'Details'],
    ['rent_per_resident_day', 'Rent on leased real property', 'Details'],
    ['rent_or_lease_paid_to_related_parties_per_resident_day', 'Rent or lease paid to related parties', 'Details'],
    ['utilities_per_resident_day', 'Utilities (heat, light and power, water)', 'Details'],
  ];
  const PURCHASING = { home: 'The home', contractor: 'Food-service contractor', unclear: 'Unclear' };

  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const norm = t => String(t || '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  const money = v => v == null ? '' : (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString('en-US');
  const money2 = v => v == null ? '' : (v < 0 ? '-$' : '$') + Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const num = (v, d = 0) => v == null ? '' : Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
  const MONTHS_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const longDate = iso => { const [y, m, d] = String(iso).split('-').map(Number); return `${MONTHS_LONG[m - 1]} ${d}, ${y}`; };
  const partTag = y => y.part_year ? ' <span class="cr-part" title="This filing covers only part of the cost year">part year</span>' : '';
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
        <td data-label="Cost year"><button type="button" data-year="${y.cost_year}">${y.cost_year}</button>${partTag(y)} ${y.checks.validated ? '' : '<span class="cr-flag">check</span>'}</td>
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

  // Food, dietary, housekeeping and laundry per resident day (method in index.method)
  function supportSection(y) {
    const ss = y.support_services;
    if (!ss || !['dietary', 'housekeeping', 'laundry'].some(k => ss[k]) || (y.checks.out_of_range || []).includes('resident days vs beds')) {
      return '<h3>Food and support services</h3><p class="subtle">Not available for this year: the dietary, laundry and housekeeping pages could not be read reliably. Check the original report.</p>';
    }
    const f = ss.food || {}, dt = ss.dietary || {}, hk = ss.housekeeping || {}, la = ss.laundry || {};
    const rawSub = f.purchasing === 'home' ? vsState(f.raw_food_per_resident_day, 'raw_food_per_resident_day', money2)
      : f.purchasing === 'contractor' ? `A food-service company supplies the food (contract services ${pct(f.contract_share, 0)} of food plus contract), so raw food cannot be separated. Compare the all-in dietary cost instead.`
      : 'Raw food could not be separated from the report. Compare the all-in dietary cost instead.';
    const split = d => d.per_resident_day == null ? '' : d.salaries ? `Staff ${money(d.salaries)} + benefits ${money(d.fringe_allocated)} + supplies and contracts ${money(d.non_salary)}`
      : `No staff on the home's own payroll; supplies and contracts ${money(d.non_salary)}`;
    const other = (dt.non_salary || 0) - (f.raw_food || 0) - (f.contract_services || 0);
    const days = y.resident_days.resident_days_total || y.resident_days.days_total_care;
    return `<h3>Food and support services</h3>
      ${ss.flags.length ? `<p class="subtle"><span class="cr-flag">Check against the original</span> Withheld: ${esc(ss.flags.join(', '))}.</p>` : ''}
      <div class="facts">
        ${factCard('Raw food per resident day', f.raw_food_per_resident_day == null ? 'Not separable' : money2(f.raw_food_per_resident_day), rawSub)}
        ${factCard('Dietary, all-in, per resident day', money2(dt.per_resident_day), [split(dt), vsState(dt.per_resident_day, 'dietary_per_resident_day', money2)].filter(Boolean).join('<br>'))}
        ${factCard('Housekeeping per resident day', money2(hk.per_resident_day), [split(hk), vsState(hk.per_resident_day, 'housekeeping_per_resident_day', money2)].filter(Boolean).join('<br>'))}
        ${factCard('Laundry per resident day', money2(la.per_resident_day), [split(la), vsState(la.per_resident_day, 'laundry_per_resident_day', money2)].filter(Boolean).join('<br>'))}
      </div>
      ${f.lines_add_up ? kvTable('Dietary lines (pages 10 and 18, nursing home)', [['Raw food (line 2a1)', money(f.raw_food)], ['Contract dietary services (line 2b)', money(f.contract_services)], ['Supplies and other (lines 2a2, 2a3, 2c)', other ? money(other) : ''], ['Dietary staff salaries (page 10, lines 5a-5c)', money(dt.salaries)], ['Their share of benefits', money(dt.fringe_allocated)], ['Total resident days (page 8)', num(days)], ['Food bought by', esc(PURCHASING[f.purchasing] || '')]]) : ''}
      ${!ss.dietary_staff_on_payroll && f.lines_add_up ? '<p class="subtle">No dietary staff on the home\'s own payroll: the kitchen staff are likely employed by the contractor, whose fee is in contract services.</p>' : ''}
      <details class="cr-more"><summary>How these numbers are calculated</summary><ul>
        ${['raw_food', 'dietary', 'housekeeping', 'laundry', 'support_costs_exclude'].filter(k => index.method[k]).map(k => `<li>${esc(index.method[k])}</li>`).join('')}
      </ul></details>`;
  }

  // Medicare cost reports (CMS) for this home, with Connecticut and national medians for the same fiscal-year end.
  function medicareSection() {
    const rows = detail.medicare_cost_reports || [];
    if (!rows.length) return '<p class="subtle">No Medicare cost reports for this home in the CMS file.</p>';
    const meds = index.medicare_cost_report_medians || {};
    const body = rows.slice().reverse().map(r => {
      const m = meds[r.period_end.slice(0, 4)] || {}, ct = m.CT || {}, us = m.US || {};
      const cmp = (v, k, f) => `${f(v)}<div class="subtle">CT ${f(ct[k])} · US ${f(us[k])}</div>`;
      return `<tr>
        <td data-label="Fiscal year">${esc(fmtDate(r.period_start))} to ${esc(fmtDate(r.period_end))}${r.full_year ? '' : ' <span class="cr-part">part year</span>'}</td>
        <td data-label="Beds" class="cr-num">${num(r.beds)}</td>
        <td data-label="Days" class="cr-num">${num(r.total_days)}</td>
        <td data-label="Operating expense / day" class="cr-num">${cmp(r.operating_expense_per_day, 'operating_expense_per_day', money2)}</td>
        <td data-label="Salaries / day" class="cr-num">${cmp(r.salaries_per_day, 'salaries_per_day', money2)}</td>
        <td data-label="Benefits / day" class="cr-num">${cmp(r.benefits_per_day, 'benefits_per_day', money2)}</td>
        <td data-label="Contract labor / day" class="cr-num">${cmp(r.contract_labor_per_day, 'contract_labor_per_day', money2)}</td>
        <td data-label="Operating margin" class="cr-num">${cmp(r.operating_margin, 'operating_margin', pct)}</td></tr>`;
    }).join('');
    return `<div class="table-scroll"><table class="stack company-table"><caption>Medicare cost reports filed with CMS (whole facility, the home's own fiscal year), with Connecticut and US medians for full-year reports ending the same year</caption>
      <thead><tr><th scope="col">Fiscal year</th><th scope="col">Beds</th><th scope="col">Total days</th><th scope="col">Operating expense per day</th><th scope="col">Salaries per day</th><th scope="col">Benefits (wage-related) per day</th><th scope="col">Contract labor per day</th><th scope="col">Operating margin</th></tr></thead>
      <tbody>${body}</tbody></table></div>
      <details class="cr-more"><summary>How the Medicare figures differ from the DSS report</summary><p>${esc(index.method.medicare_cost_reports || '')}</p></details>`;
  }

  function medicareSameYear(y) {
    const m = y.medicare_cost_report_same_year;
    if (!m) return '';
    const r = (detail.medicare_cost_reports || []).find(x => x.report_id === m.report_id);
    if (!r) return '';
    const d = guarded(y);
    return factCard('Medicare cost report, same months', money2(r.operating_expense_per_day),
      `Operating expense per day for ${esc(fmtDate(r.period_start))} to ${esc(fmtDate(r.period_end))}${m.same_period ? ' (same period)' : ` (${num(m.overlap_days)} days overlap)`}, whole facility. DSS nursing-home costs ${money2(d.expenses_per_resident_day)} per resident day.`);
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
      <h3>Cost year ${y.cost_year} (${longDate(y.period_start || `${y.cost_year - 1}-10-01`)} to ${longDate(y.period_end || `${y.cost_year}-09-30`)})${partTag(y)}</h3>
      ${y.part_year ? `<p class="notice cr-part-note">This filing covers ${y.period_days} days, not a full cost year, usually because the home opened, closed or changed owner. Dollar totals cover only those days; figures per resident day can still be compared. Part-year filings are left out of the statewide medians.</p>` : ''}
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
        ${medicareSameYear(y)}
      </div>
      ${breakdownSection(y)}
      ${supportSection(y)}
      <div class="cr-grid">
        ${kvTable('Resident days (page 8)', [['Certified beds', num(y.capacity.beds_certified)], ['Medicaid (CT)', num(rd.days_medicaid_ct)], ['Medicaid (other states)', num(rd.days_medicaid_other_states)], ['Medicare', num(rd.days_medicare)], ['Private pay', num(rd.days_private)], ['Other payers', num(rd.days_other_payer)], ['Total care days', num(rd.days_total_care)], ['Total resident days', num(days)]])}
        ${kvTable('Nursing salaries and paid hours (page 10)', [['Directors of nursing', s.sal_don == null ? '' : `${money(s.sal_don)} · ${num(h.hrs_don)} h`], ['RN direct care', s.sal_rn_direct == null ? '' : `${money(s.sal_rn_direct)} · ${num(h.hrs_rn_direct)} h`], ['RN administrative', s.sal_rn_admin == null ? '' : `${money(s.sal_rn_admin)} · ${num(h.hrs_rn_admin)} h`], ['LPN direct care', s.sal_lpn_direct == null ? '' : `${money(s.sal_lpn_direct)} · ${num(h.hrs_lpn_direct)} h`], ['LPN administrative', s.sal_lpn_admin == null ? '' : `${money(s.sal_lpn_admin)} · ${num(h.hrs_lpn_admin)} h`], ['Aides and attendants', s.sal_aides == null ? '' : `${money(s.sal_aides)} · ${num(h.hrs_aides)} h`], ['All salaries', s.sal_total == null ? '' : `${money(s.sal_total)} · ${num(h.hrs_total)} h`]])}
        ${kvTable('Owner and administrator pay (page 10)', [['Operators / owners', money(s.sal_owners)], ['Administrator(s)', money(s.sal_administrator)], ['Assistant administrator', money(s.sal_asst_administrator)]])}
        ${kvTable('Agency / nursing pool (page 13)', [['RN', np.pool_rn_direct == null ? '' : `${money(np.pool_rn_direct)} · ${num(np.pool_hrs_rn_direct)} h`], ['RN administrative', money(np.pool_rn_admin)], ['LPN', np.pool_lpn_direct == null ? '' : `${money(np.pool_lpn_direct)} · ${num(np.pool_hrs_lpn_direct)} h`], ['Aides', np.pool_aides == null ? '' : `${money(np.pool_aides)} · ${num(np.pool_hrs_aides)} h`], ['All fees in lieu of salaries', money(np.prof_fees_total)]])}
        ${kvTable('Costs by category (nursing home)', [['Administrative and general', money(ex.ag_total)], ['of which management services (line m12)', money(ex.mgmt_fee_m12)], ['Employee benefits (fringe)', money(y.fringe.fringe_total)], ['Dietary (non-salary, page 18)', money(ex.dietary_total)], ['Laundry (non-salary, page 19)', money(ex.laundry_total)], ['Housekeeping (non-salary, page 20)', money(ex.housekeeping_total)], ['Resident care supplies and services', money(ex.resident_care_total)], ['Maintenance and operating', money(ex.maint_operating_total)], ['Property', money(ex.property_total)], ['Interest', money(ex.interest_total)], ['Insurance', money(ex.insurance_total)], ['Total costs (nursing home)', money(ex.expenses_total_ccnh)], ['Total costs (all levels)', money(ex.expenses_total_all)]])}
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
      ${cmsStatusNote()}
      ${years.length ? `<div class="year-row" role="group" aria-label="Cost year">${years.map(v => `<button type="button" data-year="${v}" aria-pressed="${v === selectedYear}">${v}</button>`).join('')}</div>` : '<div class="notice">No DSS cost report is on file for this home. Homes that do not take Medicaid, such as many continuing-care retirement community health centers, do not file one.</div>'}
      ${years.length ? `<h3>Year by year</h3>${trendTable()}` : ''}
      ${y ? yearDetail(y) : ''}
      <h3>CMS ownership records</h3>${ownersSection()}
      <h3>Changes of ownership</h3>${chowSection()}
      <h3 id="medicare-title">Medicare cost reports (CMS)</h3>${medicareSection()}
      ${years.length ? '<div class="report-actions no-print"><button id="cr-home-csv" class="action-button secondary" type="button">Download every year for this home (CSV)</button></div>' : ''}
      <p class="microcopy">${esc(detail.caveats[0])} ${esc(detail.caveats[2])}</p>`;
    document.getElementById('cr-home-csv')?.addEventListener('click', downloadHomeCsv);
  }

  // A home missing from CMS Provider Information, or whose PBJ staffing stopped, has usually closed or left
  // Medicare and Medicaid. Say what CMS lists rather than asserting a closure.
  function cmsStatusNote() {
    const st = detail.cms_status;
    if (!st) return '';
    const q = v => v ? `Q${v.slice(-1)} ${v.slice(0, 4)}` : '';
    const qIndex = v => v ? Number(v.slice(0, 4)) * 4 + Number(v.slice(-1)) : 0;
    const behind = st.last_pbj_quarter && st.latest_pbj_quarter ? qIndex(st.latest_pbj_quarter) - qIndex(st.last_pbj_quarter) : 0;
    // Still listed by CMS and one quarter behind: a missed submission, not a closure.
    if (st.in_provider_information && behind === 1) {
      return `<p class="notice cr-status-note">No CMS staffing (PBJ) report for ${q(st.latest_pbj_quarter)}${String(st.staffing_footnote) === '23' ? '; CMS footnote 23 says this facility did not submit staffing data' : ''}. Its last PBJ report is for ${q(st.last_pbj_quarter)}.</p>`;
    }
    const stopped = behind >= 1;
    if (st.in_provider_information && !stopped) return '';
    const last = detail.cost_years.length ? detail.cost_years[detail.cost_years.length - 1] : null;
    const parts = [];
    if (!st.in_provider_information) parts.push(`CMS does not list this home in its Provider Information file${st.provider_information_release ? ` (${esc(st.provider_information_release)})` : ''}.`);
    if (stopped) parts.push(`Its last CMS staffing (PBJ) report is for ${q(st.last_pbj_quarter)}; the latest quarter is ${q(st.latest_pbj_quarter)}.`);
    if (last) parts.push(`Its last DSS cost report on file ends ${longDate(last.period_end)}.`);
    parts.push('A home drops off these lists when it closes, changes its CMS number or leaves Medicare and Medicaid.');
    return `<p class="notice cr-status-note">${parts.join(' ')}</p>`;
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
    const parts = rows.filter(r => r.part_year).length;
    document.getElementById('cr-state-summary').textContent = `${rows.length} homes with checked figures for cost year ${y}${parts ? `, ${parts} of them for part of the year (marked; their dollar totals cover fewer days)` : ''}. Statewide median direct care ${money2(med.direct_care_per_resident_day)} per resident day, ${pct(med.direct_care_share_of_expenses)} of costs, from full-year filings.`;
    document.getElementById('cr-state-rows').innerHTML = rows.map(r => `<tr>
      <td data-label="Home"><button type="button" data-ccn="${esc(r.ccn)}">${esc(r.facility_name)}</button>${partTag(r)}</td>
      <td data-label="Direct care / day" class="cr-num"><span class="cr-bar" style="width:${Math.round(60 * (r.direct_care_per_resident_day || 0) / max)}px" aria-hidden="true"></span>${money2(r.direct_care_per_resident_day)}</td>
      <td data-label="Share of costs" class="cr-num">${pct(r.direct_care_share_of_expenses)}</td>
      <td data-label="Nursing hrs / day" class="cr-num">${num(r.nursing_hours_per_resident_day, 2)}${r.pbj_total_nurse_hprd != null ? ` / ${num(r.pbj_total_nurse_hprd, 2)}` : ''}</td>
      <td data-label="Mgmt fees" class="cr-num">${money(r.management_fee)}</td>
      <td data-label="Related parties" class="cr-num">${money(r.related_party_total_reported)}</td>
      <td data-label="Margin" class="cr-num">${pct(r.operating_margin_nh)}</td></tr>`).join('');
  }

  function renderSupport() {
    const y = document.getElementById('cr-year').value;
    const sel = document.getElementById('cr-metric');
    const m = METRICS.find(x => x[0] === sel.value) || METRICS[0];
    const mk = m[0];
    const rows = stateRows().filter(r => r[mk] != null).map(r => Object.assign({}, r, { metric: r[mk] }));
    const { key, dir } = supportSort;
    rows.sort((a, b) => {
      const av = a[key], bv = b[key];
      if (typeof av === 'string' || typeof bv === 'string') return dir * String(av || '').localeCompare(String(bv || ''));
      return dir * ((av == null ? -Infinity : av) - (bv == null ? -Infinity : bv));
    });
    const med = index.statewide_medians[y] || {};
    const isFood = mk === 'raw_food_per_resident_day';
    const max = Math.max(...rows.map(r => r.metric || 0), 1);
    document.getElementById('cr-metric-head').textContent = `${m[1]} per resident day`;
    document.getElementById('cr-food-head').hidden = !isFood;
    const contractors = isFood ? stateRows().filter(r => r.food_purchasing === 'contractor').length : 0;
    document.getElementById('cr-support-summary').textContent = rows.length
      ? `${rows.length} homes for cost year ${y}. Statewide median ${money2(med[mk])} per resident day${m[3] && med[`${m[3]}_share`] != null ? `, ${pct(med[`${m[3]}_share`])} of total costs` : ''}.${isFood ? ` ${contractors} homes have a food-service contractor supply the food, so their raw food cannot be separated (see dietary, all-in).` : ''}`
      : `No figures for ${m[1].toLowerCase()} in cost year ${y}.`;
    document.getElementById('cr-support-rows').innerHTML = rows.map(r => `<tr>
      <td data-label="Home"><button type="button" data-ccn="${esc(r.ccn)}">${esc(r.facility_name)}</button>${partTag(r)}</td>
      <td data-label="Per resident day" class="cr-num"><span class="cr-bar" style="width:${Math.round(60 * Math.max(0, r.metric) / max)}px" aria-hidden="true"></span>${money2(r.metric)}</td>
      <td data-label="Share of costs" class="cr-num">${m[3] && r.expenses_per_resident_day ? pct(r.metric / r.expenses_per_resident_day) : ''}</td>
      <td data-label="Total costs / day" class="cr-num">${money2(r.expenses_per_resident_day)}</td>
      ${isFood ? `<td data-label="Food bought by">${esc(PURCHASING[r.food_purchasing] || '')}</td>` : ''}</tr>`).join('');
    document.getElementById('cr-support-method').innerHTML = ['cost_breakdown', 'raw_food', 'dietary', 'housekeeping', 'laundry', 'related_party_rent', 'support_costs_exclude']
      .filter(k => index.method[k]).map(k => `<li>${esc(index.method[k])}</li>`).join('');
  }

  // Every dollar of the home's costs by category, per resident day, with the statewide median.
  const CATEGORY_DETAILS = { admin: [['management_fees', 'of which management fees (line m12)']],
    plant: [['utilities', 'of which utilities (heat, light and power, water)'], ['equipment_leases', 'of which equipment leases']],
    property: [['rent', 'of which rent on leased real property'], ['depreciation', 'of which depreciation'], ['amortization', 'of which amortization'],
      ['property_taxes', 'of which property taxes'], ['rent_or_lease_paid_to_related_parties', 'of which paid to related parties for rent or lease (page 4)']] };
  const CATEGORY_MEDIAN = { nursing: 'direct_care_per_resident_day', dietary: 'dietary_per_resident_day', housekeeping: 'housekeeping_per_resident_day', laundry: 'laundry_per_resident_day' };
  function breakdownSection(y) {
    const cb = y.cost_breakdown;
    if (!cb) return '';
    if (!cb.adds_up) return `<h3>Where the money goes</h3><p class="subtle">Not shown for this year: the cost categories read from the report add up to ${money(cb.categories_total)}, not the printed total of ${money(cb.printed_total)}. Check the original report.</p>`;
    const labels = Object.fromEntries((index.cost_categories || []).map(c => [c[0], c[1]]));
    const det = cb.details || {};
    const rows = Object.entries(cb.categories).map(([k, v]) => {
      const mkey = CATEGORY_MEDIAN[k] || `${k}_per_resident_day`;
      const sub = (CATEGORY_DETAILS[k] || []).filter(([d]) => det[d]).map(([d, l]) => `<tr class="cr-sub"><th scope="row">${esc(l)}</th><td class="cr-num">${money2(det[d].per_resident_day)}</td><td class="cr-num">${money(det[d].amount)}</td><td></td><td class="cr-num subtle">${money2(stateMedian(selectedYear, `${d}_per_resident_day`))}</td></tr>`).join('');
      return `<tr><th scope="row">${esc(labels[k] || k)}</th><td class="cr-num">${money2(v.per_resident_day)}</td><td class="cr-num">${money(v.amount)}</td><td class="cr-num">${pct(v.share)}</td><td class="cr-num subtle">${money2(stateMedian(selectedYear, mkey))}</td></tr>${sub}`;
    }).join('');
    const days = y.resident_days.resident_days_total || y.resident_days.days_total_care;
    return `<h3>Where the money goes</h3>
      <div class="table-scroll"><table class="cr-breakdown"><caption>Nursing-home costs by category, cost year ${y.cost_year} (${num(days)} resident days)</caption>
      <thead><tr><th scope="col">Category</th><th scope="col">Per resident day</th><th scope="col">Amount</th><th scope="col">Share of costs</th><th scope="col">CT median per day</th></tr></thead>
      <tbody>${rows}<tr class="cr-total"><th scope="row">Total costs (page 27)</th><td class="cr-num">${money2(cb.printed_total / days)}</td><td class="cr-num">${money(cb.printed_total)}</td><td class="cr-num">100%</td><td class="cr-num subtle">${money2(stateMedian(selectedYear, 'expenses_per_resident_day'))}</td></tr></tbody></table></div>
      <details class="cr-more"><summary>How these categories are built</summary><ul>${['cost_breakdown', 'related_party_rent'].filter(k => index.method[k]).map(k => `<li>${esc(index.method[k])}</li>`).join('')}</ul></details>`;
  }

  function renderNational() {
    const meds = index.medicare_cost_report_medians || {};
    const keys = [['operating_expense_per_day', 'Operating expense per day', money2], ['salaries_per_day', 'Salaries per day', money2],
      ['benefits_per_day', 'Benefits per day', money2], ['contract_labor_per_day', 'Contract labor per day', money2],
      ['net_patient_revenue_per_day', 'Net patient revenue per day', money2], ['operating_margin', 'Operating margin', pct],
      ['occupancy', 'Occupancy', pct], ['medicaid_share_of_days', 'Medicaid share of days', pct]];
    const years = Object.keys(meds).filter(y => meds[y].US && meds[y].CT && meds[y].CT.operating_expense_per_day != null).reverse();
    document.getElementById('cr-national-head').innerHTML = `<tr><th scope="col">Fiscal year ending</th>${keys.map(k => `<th scope="col">${esc(k[1])}<br><span class="subtle">CT / US</span></th>`).join('')}</tr>`;
    document.getElementById('cr-national-rows').innerHTML = years.map(y => {
      const ct = meds[y].CT, us = meds[y].US;
      return `<tr><td data-label="Fiscal year ending">${esc(y)}${us.complete && ct.complete ? '' : ' <span class="cr-flag" title="Reports for this year are still being filed">incomplete</span>'}<div class="subtle">${num(ct.reports)} CT · ${num(us.reports)} US</div></td>${keys.map(([k, l, f]) => `<td data-label="${esc(l)} (CT / US)" class="cr-num">${f(ct[k])}<div class="subtle">${f(us[k])}</div></td>`).join('')}</tr>`;
    }).join('');
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
      'net_income_entity', 'total_assets', 'total_liabilities', 'source_file', 'period_start', 'period_end', 'part_year',
      'raw_food', 'raw_food_per_resident_day', 'food_bought_by', 'dietary_contract_services', 'dietary_all_in_per_resident_day',
      'housekeeping_all_in_per_resident_day', 'laundry_all_in_per_resident_day'];
    const sup = y => { const ss = y.support_services || {}, f = ss.food || {};
      return [f.raw_food, f.raw_food_per_resident_day, f.purchasing, f.contract_services, (ss.dietary || {}).per_resident_day,
        (ss.housekeeping || {}).per_resident_day, (ss.laundry || {}).per_resident_day]; };
    saveCsv(`ct-cost-reports-${detail.ccn}.csv`, header, detail.cost_years.map(y => [detail.ccn, detail.facility_name, y.cost_year,
      y.checks.validated ? 'yes' : 'no', y.resident_days.resident_days_total, y.resident_days.days_medicaid_ct, y.resident_days.days_medicare,
      y.resident_days.days_private, y.direct_care.direct_care_total, y.direct_care.direct_salaries, y.direct_care.nursing_pool,
      y.direct_care.direct_fringe_allocated, y.direct_care.direct_care_per_resident_day, y.direct_care.direct_care_share_of_expenses,
      y.direct_care.nursing_hours_reported, y.direct_care.nursing_hours_per_resident_day, (y.pbj_same_period || {}).total_nurse_hprd,
      y.expenses.mgmt_fee_m12, y.related_party_total_reported, y.expenses.expenses_total_ccnh, y.revenue.rev_total,
      y.direct_care.operating_margin_nh, y.balance_sheet.net_income_p36, y.balance_sheet.assets_total, y.balance_sheet.liabilities_total, y.source_file,
      y.period_start, y.period_end, y.part_year ? 'yes' : 'no', ...sup(y)]));
  }
  const EXTRA_STATE_KEYS = ['other_staff_per_resident_day', 'other_fees_per_resident_day', 'admin_per_resident_day',
    'resident_care_per_resident_day', 'plant_per_resident_day', 'property_per_resident_day', 'interest_per_resident_day', 'insurance_per_resident_day',
    'management_fees_per_resident_day', 'rent_per_resident_day', 'rent_or_lease_paid_to_related_parties_per_resident_day', 'utilities_per_resident_day'];
  function downloadStateCsv() {
    const y = document.getElementById('cr-year').value;
    const header = ['ccn', 'home', 'cost_year', 'direct_care_per_resident_day', 'direct_care_share_of_costs', 'nursing_hours_per_resident_day',
      'pbj_total_nurse_hprd_same_months', 'expenses_per_resident_day', 'management_fees_m12', 'related_party_total', 'operating_margin_nh', 'medicaid_share_of_days', 'period_start', 'period_end', 'part_year',
      'raw_food_per_resident_day', 'food_bought_by', 'dietary_all_in_per_resident_day', 'housekeeping_all_in_per_resident_day', 'laundry_all_in_per_resident_day',
      ...EXTRA_STATE_KEYS];
    saveCsv(`ct-cost-reports-${y}.csv`, header, stateRows().map(r => [r.ccn, r.facility_name, y, r.direct_care_per_resident_day,
      r.direct_care_share_of_expenses, r.nursing_hours_per_resident_day, r.pbj_total_nurse_hprd, r.expenses_per_resident_day,
      r.management_fee, r.related_party_total_reported, r.operating_margin_nh, r.medicaid_share_of_days,
      r.period_start, r.period_end, r.part_year ? 'yes' : 'no', r.raw_food_per_resident_day, r.food_purchasing,
      r.dietary_per_resident_day, r.housekeeping_per_resident_day, r.laundry_per_resident_day, ...EXTRA_STATE_KEYS.map(k => r[k])]));
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
    ysel.addEventListener('change', () => { renderState(); renderSupport(); });
    const msel = document.getElementById('cr-metric');
    const groups = [...new Set(METRICS.map(m => m[2]))];
    msel.innerHTML = groups.map(g => `<optgroup label="${esc(g)}">${METRICS.filter(m => m[2] === g).map(m => `<option value="${m[0]}">${esc(m[1])}</option>`).join('')}</optgroup>`).join('');
    msel.value = 'expenses_per_resident_day';
    msel.addEventListener('change', () => { supportSort = { key: 'metric', dir: -1 }; renderSupport(); });
    document.querySelector('#cr-state-table thead').addEventListener('click', e => {
      const b = e.target.closest('button[data-sort]');
      if (!b) return;
      stateSort = { key: b.dataset.sort, dir: stateSort.key === b.dataset.sort ? -stateSort.dir : (b.dataset.sort === 'facility_name' ? 1 : -1) };
      renderState();
    });
    document.getElementById('cr-state-rows').addEventListener('click', e => { const b = e.target.closest('button[data-ccn]'); if (b) choose(b.dataset.ccn, true); });
    document.getElementById('cr-state-csv').addEventListener('click', downloadStateCsv);
    document.querySelector('#cr-support-table thead').addEventListener('click', e => {
      const b = e.target.closest('button[data-sort]');
      if (!b) return;
      supportSort = { key: b.dataset.sort, dir: supportSort.key === b.dataset.sort ? -supportSort.dir : (b.dataset.sort === 'facility_name' ? 1 : -1) };
      renderSupport();
    });
    document.getElementById('cr-support-rows').addEventListener('click', e => { const b = e.target.closest('button[data-ccn]'); if (b) choose(b.dataset.ccn, true); });
    renderState();
    renderSupport();
    renderNational();
    const ccn = new URLSearchParams(global.location.search).get('ccn');
    if (ccn && /^\d{6}$/.test(ccn)) choose(ccn, false);
  }

  document.addEventListener('DOMContentLoaded', init);
})(window);
