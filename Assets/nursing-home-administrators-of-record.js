(function (global) {
  'use strict';

  // Facility Explorer: "Administrators of record" for the selected home. The data file is
  // fetched only when the section is opened, so the explorer's first load stays light.
  const DATA_PATH = '/data/ct_nursing_home_administrators.json';
  const SEARCH = '/staffing/tools/nursing-home-administrator-search.html';
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
    const params = new URLSearchParams(global.location.search);
    const select = document.getElementById('facility-select');
    const fromSelect = ((select && select.value) || '').match(/(\d{6})$/);
    return fromSelect ? fromSelect[1] : (params.get('ccn') || '').trim();
  }

  async function render() {
    const details = document.getElementById('administrators-details');
    const out = document.getElementById('administrators-output');
    if (!details || !out || !details.open) return;
    const ccn = selectedCcn();
    out.setAttribute('aria-busy', 'true');
    try {
      const data = await load();
      const facility = data.facilities.find(f => f.ccn === ccn);
      if (!facility) {
        out.innerHTML = '<p class="notice">This home is not in the Connecticut DPH administrator history used here. The history covers chronic and convalescent nursing homes licensed when the data was downloaded.</p>';
        return;
      }
      const asOf = fmtDate(data.source_as_of);
      const rows = facility.administrators.map(a => {
        const name = a.person_id
          ? `<a href="${SEARCH}?license=${esc(a.license_number)}">${esc(a.name)}</a><div class="subtle">License ${esc(a.license_number)}</div>`
          : `${esc(a.name)}<div class="subtle">No license number recorded</div>`;
        const end = a.end ? fmtDate(a.end) : (a.open ? `Open as of ${asOf}` : 'End not recorded');
        return `<tr><td data-label="Administrator">${name}</td><td data-label="Start">${esc(a.start ? fmtDate(a.start) : 'Start not recorded')}</td><td data-label="End">${esc(end)}</td></tr>`;
      }).join('');
      out.innerHTML = `<p class="subtle">${esc(facility.facility_name)}, DPH license ${esc(facility.facility_license)}. ${facility.administrators.length} administrator records from DPH, as of ${esc(asOf)}.</p>
        <div class="table-scroll"><table class="stack admin-of-record">
          <caption>Administrators of record, most recent first</caption>
          <thead><tr><th scope="col">Administrator</th><th scope="col">Start</th><th scope="col">End</th></tr></thead>
          <tbody>${rows}</tbody></table></div>
        <p class="microcopy">${esc(data.caveats.find(c => c.includes('performance')) || '')} Listing is not an allegation of wrongdoing. ${esc(data.corrections_notice)}</p>`;
    } catch (err) {
      out.innerHTML = `<p class="notice error">Administrator records could not be loaded. Details: ${esc(err.message)}</p>`;
    } finally {
      out.removeAttribute('aria-busy');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const details = document.getElementById('administrators-details');
    if (!details) return;
    details.addEventListener('toggle', render);
    document.getElementById('facility-select')?.addEventListener('change', render);
  });
})(window);
