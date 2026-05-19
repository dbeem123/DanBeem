(function(global) {
  'use strict';

  const dataPaths = [
    '../data/nursing_home_staffing_ct.json',
    '../data/nursing_home_staffing_mock.json'
  ];

  let dataset = null;
  let facilities = [];
  let quarterlyRows = [];
  let affiliations = [];
  let filteredAffiliations = [];
  let selectedSortKey = 'name';

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function isUsableNumber(value) {
    return value !== null && value !== '' && Number.isFinite(Number(value));
  }

  function formatHprd(value) {
    return isUsableNumber(value) ? Number(value).toFixed(2) : 'Not available';
  }

  function formatCompactHprd(value) {
    return isUsableNumber(value) ? Number(value).toFixed(2) : '-';
  }

  function formatPercent(value) {
    return isUsableNumber(value) ? `${Number(value).toFixed(1)}%` : 'Not available';
  }

  function formatCompactPercent(value) {
    return isUsableNumber(value) ? `${Number(value).toFixed(1)}%` : '-';
  }

  function formatShare(count, denominator) {
    if (!isUsableNumber(count) || !isUsableNumber(denominator) || Number(denominator) <= 0) return 'Not available';
    return `${formatCount(count)} of ${formatCount(denominator)} (${((Number(count) / Number(denominator)) * 100).toFixed(1)}%)`;
  }

  function formatCompactShare(count, denominator) {
    if (!isUsableNumber(count) || !isUsableNumber(denominator) || Number(denominator) <= 0) return '-';
    return `${formatCount(count)}/${formatCount(denominator)} (${((Number(count) / Number(denominator)) * 100).toFixed(0)}%)`;
  }

  function formatCount(value) {
    return isUsableNumber(value) ? Number(value).toLocaleString() : '0';
  }

  function formatSignedHprd(value) {
    if (!isUsableNumber(value)) return '-';
    const number = Number(value);
    const sign = number > 0 ? '+' : '';
    return `${sign}${number.toFixed(2)}`;
  }

  function average(values) {
    const usable = values.filter(isUsableNumber).map(Number);
    if (!usable.length) return null;
    return usable.reduce((sum, value) => sum + value, 0) / usable.length;
  }

  function byQuarter(a, b) {
    return String(a.quarter || '').localeCompare(String(b.quarter || ''));
  }

  function normalizeDataset(data) {
    dataset = data;
    facilities = Array.isArray(data.facilities) ? data.facilities : [];
    quarterlyRows = Array.isArray(data.facility_quarterly_staffing) ? data.facility_quarterly_staffing : [];
    const rowsByCcn = groupRowsByCcn(quarterlyRows);
    const grouped = new Map();

    facilities.forEach(facility => {
      const name = String(facility.affiliation_entity_name || '').trim();
      if (!name) return;
      const id = String(facility.affiliation_entity_id || '').trim();
      const key = name.toLowerCase();
      if (!grouped.has(key)) {
        grouped.set(key, {
          key,
          name,
          affiliationId: id,
          facilities: []
        });
      }
      if (!grouped.get(key).affiliationId && id) {
        grouped.get(key).affiliationId = id;
      }
      grouped.get(key).facilities.push({
        ...facility,
        rows: (rowsByCcn.get(facility.ccn) || []).slice().sort(byQuarter)
      });
    });

    affiliations = [...grouped.values()]
      .map(group => ({
        ...group,
        facilities: group.facilities.sort((a, b) => String(a.provider_name || '').localeCompare(String(b.provider_name || '')))
      }))
      .sort((a, b) => b.facilities.length - a.facilities.length || a.name.localeCompare(b.name));
    filteredAffiliations = affiliations.slice();
  }

  function groupRowsByCcn(rows) {
    const map = new Map();
    rows.forEach(row => {
      if (!row.ccn) return;
      if (!map.has(row.ccn)) map.set(row.ccn, []);
      map.get(row.ccn).push(row);
    });
    return map;
  }

  function getDatasetQuarters() {
    const byKey = new Map();
    quarterlyRows.forEach(row => {
      if (!row.quarter) return;
      byKey.set(row.quarter, row.quarter_label || row.quarter);
    });
    return [...byKey.entries()]
      .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
      .map(([quarter, label]) => ({ quarter, label }));
  }

  function getLatestQuarter() {
    const reportingQuarter = dataset?.reporting_period?.quarter;
    const quarters = getDatasetQuarters();
    return quarters.find(quarter => quarter.quarter === reportingQuarter) || quarters[quarters.length - 1] || null;
  }

  function getGroupByKey(key) {
    return affiliations.find(group => group.key === key) || affiliations[0] || null;
  }

  function getFacilityQuarterRow(facility, quarter) {
    return (facility.rows || []).find(row => row.quarter === quarter) || null;
  }

  function getMetric(row, key) {
    return row?.metrics ? row.metrics[key] : null;
  }

  function getBenchmark(row, key) {
    return row?.benchmarks ? row.benchmarks[key] : null;
  }

  function calculateQuarterAggregate(group, quarter) {
    const rows = group.facilities
      .map(facility => getFacilityQuarterRow(facility, quarter))
      .filter(Boolean);
    const benchmarkRows = rows.filter(row => isUsableNumber(getBenchmark(row, 'case_mix_total_nurse_hprd')));
    const ctTotalRows = rows.filter(row => isUsableNumber(getMetric(row, 'ct_direct_care_total_hprd_estimate')));
    const ctLicensedRows = rows.filter(row => isUsableNumber(getMetric(row, 'ct_direct_care_licensed_nurse_hprd_estimate')));
    const differenceValues = rows
      .map(row => {
        const actual = getMetric(row, 'total_nurse_hprd');
        const benchmark = getBenchmark(row, 'case_mix_total_nurse_hprd');
        if (!isUsableNumber(actual) || !isUsableNumber(benchmark)) return null;
        return Number(actual) - Number(benchmark);
      })
      .filter(isUsableNumber);

    return {
      quarter,
      facilityCount: rows.length,
      missingFacilityCount: Math.max(0, group.facilities.length - rows.length),
      averageTotalHprd: average(rows.map(row => getMetric(row, 'total_nurse_hprd'))),
      averageRnHprd: average(rows.map(row => getMetric(row, 'rn_hprd'))),
      averageContractStaffPct: average(rows.map(row => getMetric(row, 'contract_staff_pct'))),
      averageBenchmarkTotalHprd: average(benchmarkRows.map(row => getBenchmark(row, 'case_mix_total_nurse_hprd'))),
      averageActualMinusBenchmark: average(differenceValues),
      benchmarkCount: benchmarkRows.length,
      averageCtDirectCareTotalHprd: average(ctTotalRows.map(row => getMetric(row, 'ct_direct_care_total_hprd_estimate'))),
      ctTotalComparisonCount: ctTotalRows.length,
      ctTotalBelowCount: ctTotalRows.filter(row => getMetric(row, 'ct_total_direct_care_below_minimum_estimate') === true).length,
      averageCtLicensedDirectCareHprd: average(ctLicensedRows.map(row => getMetric(row, 'ct_direct_care_licensed_nurse_hprd_estimate'))),
      ctLicensedComparisonCount: ctLicensedRows.length,
      ctLicensedBelowCount: ctLicensedRows.filter(row => getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate') === true).length
    };
  }

  function renderDatasetSummary() {
    const output = document.getElementById('dataset-summary');
    const quarters = getDatasetQuarters();
    const facilitiesWithAffiliation = facilities.filter(facility => String(facility.affiliation_entity_name || '').trim()).length;
    const missingAffiliation = Math.max(0, facilities.length - facilitiesWithAffiliation);
    output.innerHTML = `
      <div class="dataset-fact">
        <span class="summary-label">Quarters</span>
        <strong>${escapeHtml(quarters.map(quarter => quarter.label).join(', ') || 'Not available')}</strong>
      </div>
      <div class="dataset-fact">
        <span class="summary-label">CT facilities</span>
        <strong>${formatCount(facilities.length)}</strong>
      </div>
      <div class="dataset-fact">
        <span class="summary-label">With affiliation</span>
        <strong>${formatCount(facilitiesWithAffiliation)}</strong>
        <div class="microcopy">${formatCount(missingAffiliation)} without an affiliation name</div>
      </div>
      <div class="dataset-fact">
        <span class="summary-label">Affiliation entities</span>
        <strong>${formatCount(affiliations.length)}</strong>
      </div>
      <div class="dataset-fact">
        <span class="summary-label">Sources</span>
        <strong>CMS PBJ + Provider Info + SNF Enrollments</strong>
      </div>
    `;
  }

  function renderSourceStatus() {
    const status = document.getElementById('ownership-load-status');
    const sourceNames = (dataset?.sources || []).map(source => source.source_dataset_name).filter(Boolean);
    const reportingLabel = dataset?.reporting_period?.label || 'latest quarter';
    status.textContent = `${sourceNames.join(' + ') || 'Connecticut staffing data'} loaded. Latest quarter: ${reportingLabel}.`;
    status.className = 'notice';
  }

  function getAffiliationLabel(group) {
    return `${group.name} (${group.facilities.length} CT ${group.facilities.length === 1 ? 'facility' : 'facilities'})`;
  }

  function populateAffiliationSelect(list = filteredAffiliations, selectedKey = null) {
    const select = document.getElementById('affiliation-select');
    if (!list.length) {
      select.innerHTML = '<option value="">No affiliation entities match this search</option>';
      select.disabled = true;
      updateFilterStatus(0);
      return;
    }
    select.disabled = false;
    select.innerHTML = list.map(group => (
      `<option value="${escapeHtml(group.key)}">${escapeHtml(getAffiliationLabel(group))}</option>`
    )).join('');
    if (selectedKey && list.some(group => group.key === selectedKey)) {
      select.value = selectedKey;
    }
    updateFilterStatus(list.length);
  }

  function updateFilterStatus(count) {
    const status = document.getElementById('affiliation-filter-status');
    if (!status) return;
    status.textContent = `${count} of ${affiliations.length} affiliation entities shown.`;
  }

  function filterAffiliations() {
    const query = String(document.getElementById('affiliation-filter').value || '').trim().toLowerCase();
    const currentKey = document.getElementById('affiliation-select').value;
    filteredAffiliations = affiliations.filter(group => {
      const haystack = `${group.name} ${group.affiliationId}`.toLowerCase();
      return haystack.includes(query);
    });
    populateAffiliationSelect(filteredAffiliations, currentKey);
    if (filteredAffiliations.length) {
      const next = getGroupByKey(document.getElementById('affiliation-select').value) || filteredAffiliations[0];
      renderGroup(next.key);
    }
  }

  function renderAffiliationSummary(group) {
    const output = document.getElementById('affiliation-summary');
    const linkedFacilities = group.facilities.map(facility => `
      <li>
        <a href="nursing-home-staffing-explorer.html?ccn=${encodeURIComponent(facility.ccn)}">${escapeHtml(facility.provider_name || facility.ccn)}</a>
        <span class="subtle"> - ${escapeHtml(facility.ccn || 'CCN unavailable')} - ${escapeHtml(facility.city || 'City unavailable')}, ${escapeHtml(facility.state || 'CT')}</span>
      </li>
    `).join('');

    output.innerHTML = `
      <h3>${escapeHtml(group.name)}</h3>
      <div class="summary-grid">
        <div class="summary-cell"><dl><dt>CT facilities linked</dt><dd>${formatCount(group.facilities.length)}</dd></dl></div>
        <div class="summary-cell"><dl><dt>Affiliation entity ID</dt><dd>${escapeHtml(group.affiliationId || 'Not available')}</dd></dl></div>
      </div>
      <p class="subtle">Affiliation entity names come from CMS SNF Enrollments. They provide organizational context and may not describe every operational relationship among facilities.</p>
      <ol class="facility-list">${linkedFacilities}</ol>
    `;
  }

  function renderGroupMetricCards(group) {
    const output = document.getElementById('group-metric-cards');
    const latest = getLatestQuarter();
    if (!latest) {
      output.innerHTML = '<div class="notice warning">No quarterly rows are available for this group.</div>';
      return;
    }
    const aggregate = calculateQuarterAggregate(group, latest.quarter);
    const missingNote = aggregate.missingFacilityCount
      ? `${aggregate.missingFacilityCount} linked facility${aggregate.missingFacilityCount === 1 ? ' is' : 'ies are'} missing ${latest.label}.`
      : `All linked facilities have a ${latest.label} PBJ row.`;
    const benchmarkText = isUsableNumber(aggregate.averageBenchmarkTotalHprd)
      ? `${formatHprd(aggregate.averageBenchmarkTotalHprd)} benchmark average; actual minus benchmark ${formatSignedHprd(aggregate.averageActualMinusBenchmark)}.`
      : 'Case-mix benchmark average is not available for this group-quarter.';

    document.getElementById('latest-quarter-note').textContent = `${latest.label} averages use ${aggregate.facilityCount} of ${group.facilities.length} linked facilities. ${missingNote}`;
    output.innerHTML = `
      <article class="metric-card card">
        <div class="summary-label">Average total nurse HPRD</div>
        <strong>${formatHprd(aggregate.averageTotalHprd)}</strong>
        <p class="subtle">Simple average across linked CT facilities with ${escapeHtml(latest.label)} PBJ data.</p>
      </article>
      <article class="metric-card card">
        <div class="summary-label">Average RN HPRD</div>
        <strong>${formatHprd(aggregate.averageRnHprd)}</strong>
        <p class="subtle">Registered nurse HPRD average across the same latest-quarter group.</p>
      </article>
      <article class="metric-card card">
        <div class="summary-label">Average contract staff %</div>
        <strong>${formatPercent(aggregate.averageContractStaffPct)}</strong>
        <p class="subtle">Average reported contract share. This does not measure continuity of care by itself.</p>
      </article>
      <article class="metric-card card">
        <div class="summary-label">Actual vs case-mix benchmark</div>
        <strong>${isUsableNumber(aggregate.averageActualMinusBenchmark) ? formatSignedHprd(aggregate.averageActualMinusBenchmark) : 'Not available'}</strong>
        <p class="subtle">${escapeHtml(benchmarkText)}</p>
      </article>
      <article class="metric-card card">
        <div class="summary-label">Avg CT direct-care total HPRD estimate</div>
        <strong>${formatHprd(aggregate.averageCtDirectCareTotalHprd)}</strong>
        <p class="subtle">${escapeHtml(formatShare(aggregate.ctTotalBelowCount, aggregate.ctTotalComparisonCount))} below the CT 3.00 comparison point. PBJ-derived screening estimate only.</p>
      </article>
      <article class="metric-card card">
        <div class="summary-label">Avg CT licensed direct-care HPRD estimate</div>
        <strong>${formatHprd(aggregate.averageCtLicensedDirectCareHprd)}</strong>
        <p class="subtle">${escapeHtml(formatShare(aggregate.ctLicensedBelowCount, aggregate.ctLicensedComparisonCount))} below the CT 0.84 licensed nursing comparison point. PBJ-derived screening estimate only.</p>
      </article>
    `;
  }

  function renderTrendTable(group) {
    const output = document.getElementById('group-trend');
    const quarters = getDatasetQuarters();
    if (!quarters.length) {
      output.innerHTML = '<div class="notice warning">No quarter sequence is available in the current export.</div>';
      return;
    }
    const rows = quarters.map(quarter => ({
      ...quarter,
      aggregate: calculateQuarterAggregate(group, quarter.quarter)
    }));
    output.innerHTML = `
      <div class="table-scroll" tabindex="0" aria-label="Group staffing trend table">
        <table>
          <caption>Multi-quarter staffing averages for ${escapeHtml(group.name)}</caption>
          <thead>
            <tr>
              <th scope="col">Quarter</th>
              <th scope="col">Facilities with data</th>
              <th scope="col">Average total nurse HPRD</th>
              <th scope="col">Average RN HPRD</th>
              <th scope="col">Average contract staff %</th>
              <th scope="col">Avg CT direct-care total estimate</th>
              <th scope="col">Below CT 3.00 point</th>
              <th scope="col">Avg CT licensed estimate</th>
              <th scope="col">Below CT 0.84 point</th>
              <th scope="col">Average case-mix benchmark</th>
              <th scope="col">Actual minus benchmark</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(row => `
              <tr>
                <th scope="row">${escapeHtml(row.label)}</th>
                <td>${formatCount(row.aggregate.facilityCount)} of ${formatCount(group.facilities.length)}</td>
                <td>${formatCompactHprd(row.aggregate.averageTotalHprd)}</td>
                <td>${formatCompactHprd(row.aggregate.averageRnHprd)}</td>
                <td>${formatCompactPercent(row.aggregate.averageContractStaffPct)}</td>
                <td>${formatCompactHprd(row.aggregate.averageCtDirectCareTotalHprd)}</td>
                <td>${formatCompactShare(row.aggregate.ctTotalBelowCount, row.aggregate.ctTotalComparisonCount)}</td>
                <td>${formatCompactHprd(row.aggregate.averageCtLicensedDirectCareHprd)}</td>
                <td>${formatCompactShare(row.aggregate.ctLicensedBelowCount, row.aggregate.ctLicensedComparisonCount)}</td>
                <td>${formatCompactHprd(row.aggregate.averageBenchmarkTotalHprd)}</td>
                <td>${formatSignedHprd(row.aggregate.averageActualMinusBenchmark)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  function sortFacilityRows(rows) {
    return rows.slice().sort((a, b) => {
      if (selectedSortKey === 'name') {
        return String(a.facility.provider_name || '').localeCompare(String(b.facility.provider_name || ''));
      }
      const aValue = getMetric(a.row, selectedSortKey);
      const bValue = getMetric(b.row, selectedSortKey);
      if (!isUsableNumber(aValue) && !isUsableNumber(bValue)) return 0;
      if (!isUsableNumber(aValue)) return 1;
      if (!isUsableNumber(bValue)) return -1;
      return Number(aValue) - Number(bValue);
    });
  }

  function renderFacilityComparison(group) {
    const output = document.getElementById('facility-comparison');
    const latest = getLatestQuarter();
    if (!latest) {
      output.innerHTML = '<div class="notice warning">No latest quarter is available for facility comparison.</div>';
      return;
    }
    const rows = sortFacilityRows(group.facilities.map(facility => ({
      facility,
      row: getFacilityQuarterRow(facility, latest.quarter)
    })));
    output.innerHTML = `
      <div class="table-scroll" tabindex="0" aria-label="Facility comparison table">
        <table>
          <caption>Linked facility comparison for ${escapeHtml(latest.label)}</caption>
          <thead>
            <tr>
              <th scope="col">Facility</th>
              <th scope="col">CCN</th>
              <th scope="col">City</th>
              <th scope="col">Total nurse HPRD</th>
              <th scope="col">RN HPRD</th>
              <th scope="col">CT direct-care total estimate</th>
              <th scope="col">CT licensed estimate</th>
              <th scope="col">Contract staff %</th>
              <th scope="col">Case-mix total nurse benchmark</th>
              <th scope="col">Actual minus benchmark</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(item => {
              const actual = getMetric(item.row, 'total_nurse_hprd');
              const benchmark = getBenchmark(item.row, 'case_mix_total_nurse_hprd');
              const difference = isUsableNumber(actual) && isUsableNumber(benchmark) ? Number(actual) - Number(benchmark) : null;
              return `
                <tr>
                  <th scope="row"><a href="nursing-home-staffing-explorer.html?ccn=${encodeURIComponent(item.facility.ccn)}">${escapeHtml(item.facility.provider_name || item.facility.ccn)}</a></th>
                  <td>${escapeHtml(item.facility.ccn || '-')}</td>
                  <td>${escapeHtml(item.facility.city || '-')}</td>
                  <td>${item.row ? formatCompactHprd(actual) : 'No PBJ row'}</td>
                  <td>${item.row ? formatCompactHprd(getMetric(item.row, 'rn_hprd')) : '-'}</td>
                  <td>${item.row ? `${formatCompactHprd(getMetric(item.row, 'ct_direct_care_total_hprd_estimate'))}<br><span class="subtle">${getMetric(item.row, 'ct_total_direct_care_below_minimum_estimate') === true ? 'Below CT 3.00 comparison point' : 'At/above CT 3.00 point'}</span>` : '-'}</td>
                  <td>${item.row ? `${formatCompactHprd(getMetric(item.row, 'ct_direct_care_licensed_nurse_hprd_estimate'))}<br><span class="subtle">${getMetric(item.row, 'ct_licensed_direct_care_below_minimum_estimate') === true ? 'Below CT 0.84 comparison point' : 'At/above CT 0.84 point'}</span>` : '-'}</td>
                  <td>${item.row ? formatCompactPercent(getMetric(item.row, 'contract_staff_pct')) : '-'}</td>
                  <td>${item.row ? formatCompactHprd(benchmark) : '-'}</td>
                  <td>${item.row ? formatSignedHprd(difference) : '-'}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderGroup(groupKey) {
    const group = getGroupByKey(groupKey);
    if (!group) return;
    renderAffiliationSummary(group);
    renderGroupMetricCards(group);
    renderTrendTable(group);
    renderFacilityComparison(group);
  }

  function updateSortButtons(activeKey) {
    document.querySelectorAll('.sort-button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.sortKey === activeKey));
    });
  }

  async function loadFirstAvailableJson(paths) {
    const errors = [];
    for (const path of paths) {
      try {
        return await global.DanBeemData.loadJson(path);
      } catch (err) {
        errors.push(`${path}: ${err.message}`);
      }
    }
    throw new Error(errors.join('; '));
  }

  async function loadPage() {
    const status = document.getElementById('ownership-load-status');
    const select = document.getElementById('affiliation-select');
    try {
      if (!global.DanBeemData) throw new Error('Shared data loader did not load.');
      const data = await loadFirstAvailableJson(dataPaths);
      normalizeDataset(data);
      if (!affiliations.length) throw new Error('No affiliation entity names were found in the staffing export.');

      renderDatasetSummary();
      populateAffiliationSelect();
      document.getElementById('affiliation-filter').addEventListener('input', filterAffiliations);
      select.addEventListener('change', event => renderGroup(event.target.value));
      document.querySelectorAll('.sort-button').forEach(button => {
        button.addEventListener('click', () => {
          selectedSortKey = button.dataset.sortKey || 'name';
          updateSortButtons(selectedSortKey);
          renderGroup(select.value);
        });
      });
      renderGroup(affiliations[0].key);
      renderSourceStatus();
    } catch (err) {
      status.textContent = `Ownership explorer data could not be loaded. Details: ${err.message}`;
      status.className = 'notice error';
      select.disabled = true;
    }
  }

  document.addEventListener('DOMContentLoaded', loadPage);
})(window);
