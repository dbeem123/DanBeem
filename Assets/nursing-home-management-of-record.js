(function (global) {
  'use strict';

  // Facility Explorer: organizations the selected home reported to CMS with managerial control.
  // The data file is fetched only when the section is opened.
  const DATA_PATH = '/data/ct_nursing_home_management_companies.json';
  const PAGE = '/staffing/tools/nursing-home-management-companies.html';
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  let dataPromise = null;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, ch => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  }

  function fmtDate(iso) {
    if (!iso) return '';
    const [y, m, d] = iso.split('-').map(Number);
    return `${MONTHS[m - 1]} ${d}, ${y}`;
  }

  function load() {
    if (!dataPromise) {
      dataPromise = (global.DanBeemData ? global.DanBeemData.loadJson(DATA_PATH)
        : fetch(DATA_PATH).then(r => r.json())).catch(err => { dataPromise = null; throw err; });
    }
    return dataPromise;
  }

  function selectedCcn() {
    const select = document.getElementById('facility-select');
    const match = ((select && select.value) || '').match(/(\d{6})$/);
    return match ? match[1] : (new URLSearchParams(global.location.search).get('ccn') || '').trim();
  }

  async function render() {
    const details = document.getElementById('management-details');
    const out = document.getElementById('management-output');
    if (!details || !out || !details.open) return;
    out.setAttribute('aria-busy', 'true');
    try {
      const data = await load();
      const entry = data.facilities.find(f => f.ccn === selectedCcn());
      const asOf = fmtDate(data.source_as_of);
      if (!entry) {
        out.innerHTML = `<p class="notice">No organization with operational or managerial control was reported to CMS for this home in the releases from ${esc(fmtDate(data.window.first_release))} to ${esc(asOf)}.</p>`;
        return;
      }
      const rows = entry.management.map(m => {
        const end = m.current ? `Current as of ${asOf}` : `Ended between ${fmtDate(m.end)} and ${fmtDate(m.ended_before)}`;
        return `<tr><td data-label="Organization"><a href="${PAGE}?company=${esc(m.company_id)}">${esc(m.name)}</a></td><td data-label="Start">${esc(fmtDate(m.start))}</td><td data-label="End">${esc(end)}</td></tr>`;
      }).join('');
      out.innerHTML = `<div class="table-scroll"><table class="stack admin-of-record">
          <caption>Organizations reported with managerial control, current first</caption>
          <thead><tr><th scope="col">Organization</th><th scope="col">Start</th><th scope="col">End</th></tr></thead>
          <tbody>${rows}</tbody></table></div>
        <p class="microcopy">From ${esc(data.window.releases)} monthly CMS releases. Operational or managerial control is not the same as ownership. ${esc(data.caveats.find(c => c.includes('performance')) || '')}</p>`;
    } catch (err) {
      out.innerHTML = `<p class="notice error">Management records could not be loaded. Details: ${esc(err.message)}</p>`;
    } finally {
      out.removeAttribute('aria-busy');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const details = document.getElementById('management-details');
    if (!details) return;
    details.addEventListener('toggle', render);
    document.getElementById('facility-select')?.addEventListener('change', render);
  });
})(window);
