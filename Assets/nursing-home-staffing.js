(function(global) {
  'use strict';

  /**
   * @typedef {Object} StaffingMetrics
   * @property {number} totalNurseHprd
   * @property {number} rnHprd
   * @property {number} lpnLvnHprd
   * @property {number} nurseAideHprd
   * @property {number} contractStaffPct
   */

  /**
   * @typedef {Object} StaffingQuarter
   * @property {string} quarter
   * @property {number} totalNurseHprd
   * @property {number} rnHprd
   * @property {number} lpnLvnHprd
   * @property {number} nurseAideHprd
   * @property {number} contractStaffPct
   * @property {number} averageCensus
   */

  /**
   * @typedef {Object} StaffingFacility
   * @property {string} id
   * @property {string} ccn
   * @property {string} name
   * @property {string} city
   * @property {string} state
   * @property {string} quarterReviewed
   * @property {number=} averageCensus
   * @property {number=} caseMixBenchmarkHprd
   * @property {StaffingMetrics} metrics
   * @property {StaffingQuarter[]} quarters
   * @property {{shows:string,suggests:string,cannotProve:string}} interpretation
   */

  const metricDefinitions = [
    {
      key: 'totalNurseHprd',
      label: 'Total nurse HPRD',
      format: formatHprd,
      help: 'Reported RN, LPN/LVN, and nurse aide hours per resident day.'
    },
    {
      key: 'rnHprd',
      label: 'RN HPRD',
      format: formatHprd,
      help: 'Registered nurse hours per resident day.'
    },
    {
      key: 'lpnLvnHprd',
      label: 'LPN/LVN HPRD',
      format: formatHprd,
      help: 'Licensed practical or vocational nurse hours per resident day.'
    },
    {
      key: 'nurseAideHprd',
      label: 'Nurse aide HPRD',
      format: formatHprd,
      help: 'Nurse aide hours per resident day.'
    },
    {
      key: 'contractStaffPct',
      label: 'Contract staff %',
      format: formatPercent,
      help: 'Share of reported nursing hours supplied by contract staff.'
    }
  ];

  let facilities = [];

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatHprd(value) {
    return Number.isFinite(Number(value)) ? Number(value).toFixed(2) : 'Not available';
  }

  function formatPercent(value) {
    return Number.isFinite(Number(value)) ? `${Number(value).toFixed(1)}%` : 'Not available';
  }

  function formatCount(value) {
    return Number.isFinite(Number(value)) ? Number(value).toLocaleString() : 'Not available';
  }

  function getFacilityById(id) {
    return facilities.find(facility => facility.id === id) || facilities[0];
  }

  function populateFacilitySelect() {
    const select = document.getElementById('facility-select');
    select.innerHTML = facilities.map(facility => (
      `<option value="${escapeHtml(facility.id)}">${escapeHtml(facility.name)} - ${escapeHtml(facility.city)}, ${escapeHtml(facility.state)}</option>`
    )).join('');
  }

  function renderFacilitySummary(facility) {
    document.getElementById('facility-summary').innerHTML = `
      <div>
        <div class="eyebrow">Selected Facility</div>
        <h2>${escapeHtml(facility.name)}</h2>
        <p class="subtle">${escapeHtml(facility.city)}, ${escapeHtml(facility.state)}</p>
      </div>
      <dl class="staffing-summary-list">
        <div><dt>CCN</dt><dd>${escapeHtml(facility.ccn)}</dd></div>
        <div><dt>Quarter reviewed</dt><dd>${escapeHtml(facility.quarterReviewed)}</dd></div>
        <div><dt>Average census</dt><dd>${formatCount(facility.averageCensus)}</dd></div>
      </dl>
    `;
  }

  function renderMetricCards(facility) {
    const metricCards = metricDefinitions.map(metric => `
      <article class="staffing-metric card">
        <div class="summary-label">${escapeHtml(metric.label)}</div>
        <strong>${escapeHtml(metric.format(facility.metrics[metric.key]))}</strong>
        <p class="subtle">${escapeHtml(metric.help)}</p>
      </article>
    `);

    if (Number.isFinite(Number(facility.caseMixBenchmarkHprd))) {
      metricCards.push(`
        <article class="staffing-metric card">
          <div class="summary-label">Case-mix benchmark</div>
          <strong>${formatHprd(facility.caseMixBenchmarkHprd)}</strong>
          <p class="subtle">Mock CMS case-mix nursing HPRD comparison value, not a legal minimum.</p>
        </article>
      `);
    }

    document.getElementById('metric-cards').innerHTML = metricCards.join('');
  }

  function renderQuarterlyTable(facility) {
    const output = document.getElementById('quarterly-exhibit');
    const maxHprd = Math.max(...facility.quarters.map(row => row.totalNurseHprd), 1);
    output.innerHTML = `
      <div class="table-scroll" tabindex="0" aria-label="Quarterly staffing comparison table">
        <table>
          <caption>Quarterly comparison for ${escapeHtml(facility.name)}</caption>
          <thead>
            <tr>
              <th scope="col">Quarter</th>
              <th scope="col">Total nurse HPRD</th>
              <th scope="col">RN HPRD</th>
              <th scope="col">Nurse aide HPRD</th>
              <th scope="col">Contract staff</th>
              <th scope="col">Average census</th>
            </tr>
          </thead>
          <tbody>
            ${facility.quarters.map(row => {
              const width = Math.max(8, Math.round((row.totalNurseHprd / maxHprd) * 100));
              return `
                <tr>
                  <th scope="row">${escapeHtml(row.quarter)}</th>
                  <td>
                    <div class="staffing-bar" aria-hidden="true"><span style="width:${width}%"></span></div>
                    <span>${formatHprd(row.totalNurseHprd)}</span>
                  </td>
                  <td>${formatHprd(row.rnHprd)}</td>
                  <td>${formatHprd(row.nurseAideHprd)}</td>
                  <td>${formatPercent(row.contractStaffPct)}</td>
                  <td>${formatCount(row.averageCensus)}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderInterpretation(facility) {
    document.getElementById('interpretation').innerHTML = `
      <article class="card">
        <h3>What this shows</h3>
        <p>${escapeHtml(facility.interpretation.shows)}</p>
      </article>
      <article class="card">
        <h3>What this may suggest</h3>
        <p>${escapeHtml(facility.interpretation.suggests)}</p>
      </article>
      <article class="card">
        <h3>What this cannot prove</h3>
        <p>${escapeHtml(facility.interpretation.cannotProve)}</p>
      </article>
    `;
  }

  function renderFacility(facilityId) {
    const facility = getFacilityById(facilityId);
    renderFacilitySummary(facility);
    renderMetricCards(facility);
    renderQuarterlyTable(facility);
    renderInterpretation(facility);
  }

  async function loadPage() {
    const status = document.getElementById('staffing-load-status');
    const select = document.getElementById('facility-select');

    try {
      if (!global.DanBeemData) throw new Error('Shared data loader did not load.');
      const data = await global.DanBeemData.loadJson('../data/nursing_home_staffing_mock.json');
      facilities = Array.isArray(data.facilities) ? data.facilities : [];
      if (!facilities.length) throw new Error('No mock facilities were found.');

      populateFacilitySelect();
      select.addEventListener('change', event => renderFacility(event.target.value));
      renderFacility(facilities[0].id);
      status.textContent = 'Mock PBJ staffing data loaded for interface review.';
      status.className = 'notice';
    } catch (err) {
      status.textContent = `Staffing explorer data could not be loaded. Details: ${err.message}`;
      status.className = 'notice error';
      select.disabled = true;
    }
  }

  document.addEventListener('DOMContentLoaded', loadPage);
})(window);
