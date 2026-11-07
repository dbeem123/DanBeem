(function (global) {
  'use strict';

  // Facility Explorer: headline DSS cost-report figures for the selected home. Loaded when the section opens.
  const INDEX_PATH = '/data/ct_nursing_home_cost_reports.json';
  const PAGE = '/staffing/tools/nursing-home-cost-reports.html';
  let promise = null;

  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const money = v => v == null ? '' : (v < 0 ? '-$' : '$') + Math.abs(Math.round(v)).toLocaleString('en-US');
  const money2 = v => v == null ? '' : `$${Number(v).toFixed(2)}`;
  const pct = v => v == null ? '' : `${(v * 100).toFixed(1)}%`;
  const num = v => v == null ? '' : Number(v).toFixed(2);

  function load() {
    if (!promise) {
      promise = (global.DanBeemData ? global.DanBeemData.loadJson(INDEX_PATH) : fetch(INDEX_PATH).then(r => r.json()))
        .catch(err => { promise = null; throw err; });
    }
    return promise;
  }

  function selectedCcn() {
    const select = document.getElementById('facility-select');
    const m = ((select && select.value) || '').match(/(\d{6})$/);
    return m ? m[1] : (new URLSearchParams(global.location.search).get('ccn') || '').trim();
  }

  async function render() {
    const details = document.getElementById('cost-report-details');
    const out = document.getElementById('cost-report-output');
    if (!details || !out || !details.open) return;
    out.setAttribute('aria-busy', 'true');
    try {
      const data = await load();
      const ccn = selectedCcn();
      const f = data.facilities.find(x => x.ccn === ccn);
      const years = f ? Object.entries(f.years) : [];
      if (!years.length) {
        out.innerHTML = '<p class="notice">No DSS cost report is on file for this home. Homes that do not take Medicaid, such as many continuing-care retirement community health centers, do not file one.</p>';
        return;
      }
      const rows = years.slice().reverse().map(([y, r]) => {
        const med = data.statewide_medians[y] || {};
        const ok = r.validated;
        return `<tr><td data-label="Cost year"><a href="${PAGE}?ccn=${esc(ccn)}&year=${esc(y)}">${esc(y)}</a>${ok ? '' : ' <span class="subtle">(check)</span>'}</td>
          <td data-label="Direct care / day">${ok ? money2(r.direct_care_per_resident_day) : ''} <span class="subtle">${ok ? `CT ${money2(med.direct_care_per_resident_day)}` : ''}</span></td>
          <td data-label="Share of costs">${ok ? pct(r.direct_care_share_of_expenses) : ''}</td>
          <td data-label="Nursing hrs / day">${ok ? num(r.nursing_hours_per_resident_day) : ''}${ok && r.pbj_total_nurse_hprd != null ? ` / PBJ ${num(r.pbj_total_nurse_hprd)}` : ''}</td>
          <td data-label="Mgmt fees">${money(r.management_fee)}</td>
          <td data-label="Related parties">${money(r.related_party_total_reported)}</td></tr>`;
      }).join('');
      out.innerHTML = `<div class="table-scroll"><table class="stack admin-of-record">
        <caption>DSS cost reports, most recent first</caption>
        <thead><tr><th scope="col">Cost year</th><th scope="col">Direct care per resident day</th><th scope="col">Direct care share of costs</th><th scope="col">Nursing hours per resident day</th><th scope="col">Management fees</th><th scope="col">Paid to related parties</th></tr></thead>
        <tbody>${rows}</tbody></table></div>
        <p class="microcopy">As reported by the home, before DSS audit. Figures that did not pass the report's own total checks are left blank; open the year for detail. Spending is not a measure of care quality.</p>`;
    } catch (err) {
      out.innerHTML = `<p class="notice error">Cost-report records could not be loaded. Details: ${esc(err.message)}</p>`;
    } finally {
      out.removeAttribute('aria-busy');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const details = document.getElementById('cost-report-details');
    if (!details) return;
    details.addEventListener('toggle', render);
    document.getElementById('facility-select')?.addEventListener('change', render);
  });
})(window);
