(function(global) {
  'use strict';

  const dataPaths = [
    '../data/nursing_home_staffing_ct.json',
    '../data/nursing_home_staffing_mock.json'
  ];

  const modeConfig = {
    'direct-decline': {
      label: 'Largest decline in CT direct-care HPRD',
      metricLabel: 'CT direct-care HPRD estimate',
      earliestHeader: 'Earliest CT direct-care HPRD',
      latestHeader: 'Latest CT direct-care HPRD',
      changeHeader: 'Change in CT direct-care HPRD',
      metricKey: 'directChange',
      rowFilter: record => isUsableNumber(record.directChange) && record.directChange < 0,
      sortDirection: 'asc'
    },
    'direct-improvement': {
      label: 'Largest improvement in CT direct-care HPRD',
      metricLabel: 'CT direct-care HPRD estimate',
      earliestHeader: 'Earliest CT direct-care HPRD',
      latestHeader: 'Latest CT direct-care HPRD',
      changeHeader: 'Change in CT direct-care HPRD',
      metricKey: 'directChange',
      rowFilter: record => isUsableNumber(record.directChange) && record.directChange > 0,
      sortDirection: 'desc'
    },
    'crossed-below': {
      label: 'Crossed below CT 3.00 direct-care comparison point',
      metricLabel: 'CT direct-care HPRD estimate',
      earliestHeader: 'Earliest CT direct-care HPRD',
      latestHeader: 'Latest CT direct-care HPRD',
      changeHeader: 'Change in CT direct-care HPRD',
      metricKey: 'directChange',
      rowFilter: record => record.crossedBelowTotal,
      sortDirection: 'asc'
    },
    'crossed-above': {
      label: 'Crossed above CT 3.00 direct-care comparison point',
      metricLabel: 'CT direct-care HPRD estimate',
      earliestHeader: 'Earliest CT direct-care HPRD',
      latestHeader: 'Latest CT direct-care HPRD',
      changeHeader: 'Change in CT direct-care HPRD',
      metricKey: 'directChange',
      rowFilter: record => record.crossedAboveTotal,
      sortDirection: 'desc'
    },
    'contract-increase': {
      label: 'Largest increase in contract staff %',
      metricLabel: 'Contract staff %',
      earliestHeader: 'Earliest contract staff %',
      latestHeader: 'Latest contract staff %',
      changeHeader: 'Change in contract staff %',
      metricKey: 'contractChange',
      rowFilter: record => isUsableNumber(record.contractChange) && record.contractChange > 0,
      sortDirection: 'desc',
      formatter: 'percent'
    },
    'rn-decrease': {
      label: 'Largest decrease in RN HPRD',
      metricLabel: 'RN HPRD',
      earliestHeader: 'Earliest RN HPRD',
      latestHeader: 'Latest RN HPRD',
      changeHeader: 'Change in RN HPRD',
      metricKey: 'rnChange',
      rowFilter: record => isUsableNumber(record.rnChange) && record.rnChange < 0,
      sortDirection: 'asc'
    }
  };

  let dataset = null;
  let facilities = [];
  let changeRecords = [];
  let filteredRecords = [];
  let allQuarters = [];
  let earliestQuarter = '';
  let latestQuarter = '';
  let currentMode = 'direct-decline';
  let summaryCounts = {};

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

  function formatCount(value) {
    return isUsableNumber(value) ? Number(value).toLocaleString() : '0';
  }

  function formatHprd(value) {
    return isUsableNumber(value) ? Number(value).toFixed(2) : '-';
  }

  function formatPercent(value) {
    return isUsableNumber(value) ? `${Number(value).toFixed(1)}%` : '-';
  }

  function formatSigned(value, formatter) {
    if (!isUsableNumber(value)) return '-';
    const number = Number(value);
    const sign = number > 0 ? '+' : '';
    if (formatter === 'percent') return `${sign}${number.toFixed(1)} pts`;
    return `${sign}${number.toFixed(2)}`;
  }

  function average(values) {
    const usable = values.filter(isUsableNumber).map(Number);
    if (!usable.length) return null;
    return usable.reduce((sum, value) => sum + value, 0) / usable.length;
  }

  function getMetric(row, key) {
    return row?.metrics ? row.metrics[key] : null;
  }

  function getFacilityName(record) {
    return record.facility?.provider_name || record.ccn || 'Unnamed facility';
  }

  function uniqueSorted(values) {
    return [...new Set(values.map(value => String(value || '').trim()).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b));
  }

  function getRowValue(record, metricKind, point) {
    if (metricKind === 'contract') return getMetric(record[point], 'contract_staff_pct');
    if (metricKind === 'rn') return getMetric(record[point], 'rn_hprd');
    return getMetric(record[point], 'ct_direct_care_total_hprd_estimate');
  }

  function getModeMetricKind(mode) {
    if (mode === 'contract-increase') return 'contract';
    if (mode === 'rn-decrease') return 'rn';
    return 'direct';
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

  function normalizeDataset(data) {
    dataset = data;
    facilities = Array.isArray(data.facilities) ? data.facilities : [];
    const quarterlyRows = Array.isArray(data.facility_quarterly_staffing) ? data.facility_quarterly_staffing : [];
    allQuarters = uniqueSorted(quarterlyRows.map(row => row.quarter));
    earliestQuarter = allQuarters[0] || '';
    latestQuarter = allQuarters[allQuarters.length - 1] || '';

    const facilityByCcn = new Map(facilities.map(facility => [facility.ccn, facility]));
    const rowsByCcnQuarter = new Map(quarterlyRows.map(row => [`${row.ccn}:${row.quarter}`, row]));

    changeRecords = facilities.map(facility => {
      const earliest = rowsByCcnQuarter.get(`${facility.ccn}:${earliestQuarter}`) || null;
      const latest = rowsByCcnQuarter.get(`${facility.ccn}:${latestQuarter}`) || null;
      if (!earliest || !latest) {
        return null;
      }
      const directEarly = getMetric(earliest, 'ct_direct_care_total_hprd_estimate');
      const directLatest = getMetric(latest, 'ct_direct_care_total_hprd_estimate');
      const contractEarly = getMetric(earliest, 'contract_staff_pct');
      const contractLatest = getMetric(latest, 'contract_staff_pct');
      const rnEarly = getMetric(earliest, 'rn_hprd');
      const rnLatest = getMetric(latest, 'rn_hprd');
      const earlyBelow = getMetric(earliest, 'ct_total_direct_care_below_minimum_estimate');
      const latestBelow = getMetric(latest, 'ct_total_direct_care_below_minimum_estimate');
      return {
        ccn: facility.ccn,
        facility: facilityByCcn.get(facility.ccn) || facility,
        earliest,
        latest,
        directChange: isUsableNumber(directEarly) && isUsableNumber(directLatest) ? Number(directLatest) - Number(directEarly) : null,
        contractChange: isUsableNumber(contractEarly) && isUsableNumber(contractLatest) ? Number(contractLatest) - Number(contractEarly) : null,
        rnChange: isUsableNumber(rnEarly) && isUsableNumber(rnLatest) ? Number(rnLatest) - Number(rnEarly) : null,
        crossedBelowTotal: earlyBelow === false && latestBelow === true,
        crossedAboveTotal: earlyBelow === true && latestBelow === false
      };
    }).filter(Boolean);

    filteredRecords = changeRecords.slice();
    summaryCounts = {
      included: changeRecords.length,
      incomplete: Math.max(0, facilities.length - changeRecords.length),
      directDeclines: changeRecords.filter(record => isUsableNumber(record.directChange) && record.directChange < 0).length,
      directImprovements: changeRecords.filter(record => isUsableNumber(record.directChange) && record.directChange > 0).length,
      crossedBelow: changeRecords.filter(record => record.crossedBelowTotal).length,
      crossedAbove: changeRecords.filter(record => record.crossedAboveTotal).length,
      contractIncreases: changeRecords.filter(record => isUsableNumber(record.contractChange) && record.contractChange > 0).length,
      rnDecreases: changeRecords.filter(record => isUsableNumber(record.rnChange) && record.rnChange < 0).length
    };
  }

  function renderSourceStatus() {
    const status = document.getElementById('load-status');
    const sourceNames = (dataset?.sources || []).map(source => source.source_dataset_name).filter(Boolean);
    status.textContent = `${sourceNames.join(' + ') || 'Connecticut staffing data'} loaded. Change window: ${earliestQuarter || 'earliest'} to ${latestQuarter || 'latest'}.`;
    status.className = 'notice';
  }

  function renderSummaryCards() {
    const output = document.getElementById('summary-cards');
    document.getElementById('summary-note').textContent =
      `Primary change tables compare facilities with both ${earliestQuarter} and ${latestQuarter} PBJ rows. Facilities missing either endpoint are counted separately and are not zero-filled.`;
    output.innerHTML = `
      <div class="summary-card">
        <span class="summary-label">Both endpoint quarters</span>
        <strong>${formatCount(summaryCounts.included)}</strong>
        <div class="microcopy">${escapeHtml(earliestQuarter)} to ${escapeHtml(latestQuarter)}</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Missing endpoint data</span>
        <strong>${formatCount(summaryCounts.incomplete)}</strong>
        <div class="microcopy">Excluded from primary change tables</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">CT direct-care decline</span>
        <strong>${formatCount(summaryCounts.directDeclines)}</strong>
        <div class="microcopy">Earliest to latest</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">CT direct-care increase</span>
        <strong>${formatCount(summaryCounts.directImprovements)}</strong>
        <div class="microcopy">Earliest to latest</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Crossed below CT 3.00</span>
        <strong>${formatCount(summaryCounts.crossedBelow)}</strong>
        <div class="microcopy">At/above to below</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Crossed above CT 3.00</span>
        <strong>${formatCount(summaryCounts.crossedAbove)}</strong>
        <div class="microcopy">Below to at/above</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Contract staff % increased</span>
        <strong>${formatCount(summaryCounts.contractIncreases)}</strong>
        <div class="microcopy">Endpoint comparison</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">RN HPRD decreased</span>
        <strong>${formatCount(summaryCounts.rnDecreases)}</strong>
        <div class="microcopy">Endpoint comparison</div>
      </div>
    `;
  }

  function populateSelectOptions() {
    const affiliationSelect = document.getElementById('affiliation-filter');
    const ownershipSelect = document.getElementById('ownership-filter');
    const affiliations = uniqueSorted(changeRecords.map(record => record.facility?.affiliation_entity_name));
    const ownershipTypes = uniqueSorted(changeRecords.map(record => record.facility?.ownership_type));

    affiliationSelect.innerHTML = '<option value="all">All affiliations</option>' + affiliations
      .map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
      .join('');
    ownershipSelect.innerHTML = '<option value="all">All ownership types</option>' + ownershipTypes
      .map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
      .join('');
  }

  function updateModeButtons() {
    document.querySelectorAll('.mode-button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.mode === currentMode));
    });
  }

  function baseRowsForMode() {
    const config = modeConfig[currentMode] || modeConfig['direct-decline'];
    return changeRecords.filter(config.rowFilter);
  }

  function sortRecords(rows) {
    const config = modeConfig[currentMode] || modeConfig['direct-decline'];
    const direction = config.sortDirection === 'desc' ? -1 : 1;
    return rows.slice().sort((a, b) => {
      const aValue = a[config.metricKey];
      const bValue = b[config.metricKey];
      const aUsable = isUsableNumber(aValue);
      const bUsable = isUsableNumber(bValue);
      if (!aUsable && !bUsable) return getFacilityName(a).localeCompare(getFacilityName(b));
      if (!aUsable) return 1;
      if (!bUsable) return -1;
      return (Number(aValue) - Number(bValue)) * direction || getFacilityName(a).localeCompare(getFacilityName(b));
    });
  }

  function applyFilters() {
    const query = String(document.getElementById('facility-search').value || '').trim().toLowerCase();
    const affiliationFilter = document.getElementById('affiliation-filter').value;
    const ownershipFilter = document.getElementById('ownership-filter').value;
    const affiliationPresence = document.getElementById('affiliation-presence-filter').value;
    filteredRecords = baseRowsForMode().filter(record => {
      const facility = record.facility || {};
      const haystack = `${facility.provider_name || ''} ${record.ccn || ''} ${facility.city || ''} ${facility.affiliation_entity_name || ''}`.toLowerCase();
      if (query && !haystack.includes(query)) return false;
      if (affiliationFilter !== 'all' && String(facility.affiliation_entity_name || '') !== affiliationFilter) return false;
      if (ownershipFilter !== 'all' && String(facility.ownership_type || '') !== ownershipFilter) return false;
      if (affiliationPresence === 'with-affiliation' && !String(facility.affiliation_entity_name || '').trim()) return false;
      return true;
    });
    renderCurrentView();
  }

  function renderStatus(value) {
    if (value === true) return '<span class="status-pill warning">Below comparison point</span>';
    if (value === false) return '<span class="status-pill">At/above comparison point</span>';
    return '<span class="subtle-note">Unavailable</span>';
  }

  function metricFormatter(config) {
    return config.formatter === 'percent' ? formatPercent : formatHprd;
  }

  function getSelectedOptionText(id) {
    const element = document.getElementById(id);
    return element?.selectedOptions?.[0]?.textContent || '';
  }

  function getActiveFilterSummary() {
    const query = String(document.getElementById('facility-search').value || '').trim();
    const affiliationFilter = document.getElementById('affiliation-filter').value;
    const ownershipFilter = document.getElementById('ownership-filter').value;
    const affiliationPresence = document.getElementById('affiliation-presence-filter').value;
    const filters = [];

    if (query) filters.push(`Search term: ${query}`);
    if (affiliationFilter !== 'all') filters.push(`Affiliation entity: ${affiliationFilter}`);
    if (ownershipFilter !== 'all') filters.push(`Ownership type: ${ownershipFilter}`);
    if (affiliationPresence !== 'all') filters.push(`Affiliation data: ${getSelectedOptionText('affiliation-presence-filter')}`);

    return filters.length ? filters : ['No filters active; full selected change mode shown.'];
  }

  function getMaterialFilterSummary() {
    return getActiveFilterSummary().filter(item => !item.startsWith('No filters active'));
  }

  function joinWithAnd(items) {
    if (items.length <= 1) return items.join('');
    if (items.length === 2) return `${items[0]} and ${items[1]}`;
    return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`;
  }

  function hideChangeSummaryFallback() {
    const fallback = document.getElementById('change-summary-fallback');
    const textarea = document.getElementById('change-summary-text');
    if (fallback) fallback.hidden = true;
    if (textarea) textarea.value = '';
  }

  function showChangeSummaryFallback(summary) {
    const fallback = document.getElementById('change-summary-fallback');
    const textarea = document.getElementById('change-summary-text');
    if (!fallback || !textarea) return;
    textarea.value = summary;
    fallback.hidden = false;
    textarea.focus();
    textarea.select();
  }

  function getCurrentSummary(rows) {
    const config = modeConfig[currentMode] || modeConfig['direct-decline'];
    return {
      rowsShown: rows.length,
      averageChange: average(rows.map(record => record[config.metricKey])),
      crossingShown: rows.filter(record => record.crossedBelowTotal || record.crossedAboveTotal).length
    };
  }

  function buildChangeBriefingSummary(rows) {
    if (!rows.length) return '';
    const config = modeConfig[currentMode] || modeConfig['direct-decline'];
    const summary = getCurrentSummary(rows);
    const filters = getMaterialFilterSummary();
    const filterSentence = filters.length
      ? ` Active filters narrowing the view include ${joinWithAnd(filters)}.`
      : '';
    const averageSentence = currentMode === 'crossed-below' || currentMode === 'crossed-above'
      ? ' The current rows are facilities that crossed the CT 3.00 direct-care comparison point between the endpoint quarters.'
      : ` The current filtered set has an average change of ${formatSigned(summary.averageChange, config.formatter)} in ${config.metricLabel}.`;
    const leadingRows = rows.slice(0, Math.min(5, rows.length))
      .map(record => `${getFacilityName(record)} (${formatSigned(record[config.metricKey], config.formatter)})`);
    const leadingSentence = leadingRows.length
      ? ` The leading facilities under the current sort include ${joinWithAnd(leadingRows)}.`
      : '';
    return `Using CMS PBJ staffing data from ${earliestQuarter || 'the earliest available quarter'} through ${latestQuarter || 'the latest available quarter'}, this change-over-time view shows ${formatCount(rows.length)} Connecticut nursing homes under the selected mode: ${config.label}.${filterSentence}${averageSentence}${leadingSentence} These figures describe changes in PBJ-reported staffing screening measures and do not explain why staffing changed or establish legal or care-quality conclusions.`;
  }

  function renderPrintReportContext(rows) {
    const output = document.getElementById('print-report-context');
    if (!output) return;
    const config = modeConfig[currentMode] || modeConfig['direct-decline'];
    const generatedAt = dataset?.generated_at || dataset?.generated_on || dataset?.meta?.generated_on || '';
    const summary = getCurrentSummary(rows);
    output.innerHTML = `
      <h1>Connecticut Nursing Home Staffing Change Over Time</h1>
      <p><strong>Comparison window:</strong> ${escapeHtml(earliestQuarter || 'Unavailable')} to ${escapeHtml(latestQuarter || 'Unavailable')}</p>
      <p><strong>Generated export timestamp:</strong> ${escapeHtml(generatedAt || 'Not listed in export')}</p>
      <p><strong>Selected change mode:</strong> ${escapeHtml(config.label)}</p>
      <div class="notice">
        <strong>Active filters:</strong>
        <ul>
          ${getActiveFilterSummary().map(item => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </div>
      <div class="notice">
        <strong>Current-view summary:</strong>
        ${formatCount(summary.rowsShown)} rows shown; average change ${formatSigned(summary.averageChange, config.formatter)}; ${formatCount(summary.crossingShown)} CT 3.00 direct-care comparison point crossings shown.
      </div>
      <div class="notice warning">
        This report compares available PBJ staffing rows across the displayed quarter window. Missing endpoint quarter rows are excluded from endpoint-to-endpoint change tables. Changes reflect PBJ-reported staffing measures and do not explain why staffing changed. CT comparison point crossings are PBJ-derived screening indicators, not formal DPH compliance findings. Staffing changes alone do not prove poor care, neglect, harm, or regulatory violations. Use the facility-level Staffing Explorer to review the full five-quarter context for any individual nursing home.
      </div>
    `;
  }

  function renderCurrentSummary(rows) {
    const output = document.getElementById('current-summary-cards');
    const config = modeConfig[currentMode] || modeConfig['direct-decline'];
    const summary = getCurrentSummary(rows);
    document.getElementById('mode-note').textContent =
      `${config.label}. These figures summarize the rows currently shown after search and filters.`;
    output.innerHTML = `
      <div class="summary-card">
        <span class="summary-label">Rows shown</span>
        <strong>${formatCount(summary.rowsShown)}</strong>
        <div class="microcopy">Selected mode and filters</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Average change</span>
        <strong>${formatSigned(summary.averageChange, config.formatter)}</strong>
        <div class="microcopy">${escapeHtml(config.metricLabel)}</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Threshold crossings shown</span>
        <strong>${formatCount(summary.crossingShown)}</strong>
        <div class="microcopy">CT 3.00 direct-care comparison point</div>
      </div>
    `;
  }

  function renderChangeTable(rows) {
    const output = document.getElementById('change-table');
    const config = modeConfig[currentMode] || modeConfig['direct-decline'];
    const metricKind = getModeMetricKind(currentMode);
    const formatMetric = metricFormatter(config);
    hideChangeSummaryFallback();
    document.getElementById('filter-status').textContent =
      `${formatCount(rows.length)} rows shown for "${config.label}".`;
    document.getElementById('download-change-csv').disabled = !rows.length;
    document.getElementById('print-change-view').disabled = !rows.length;
    document.getElementById('copy-change-summary').disabled = !rows.length;
    if (!rows.length) {
      output.innerHTML = '<div class="notice warning">No facilities match the selected change mode and filters.</div>';
      return;
    }
    output.innerHTML = `
      <div class="table-scroll" tabindex="0" aria-label="Statewide staffing change table">
        <table>
          <caption>${escapeHtml(config.label)} from ${escapeHtml(earliestQuarter)} to ${escapeHtml(latestQuarter)}</caption>
          <thead>
            <tr>
              <th scope="col">Facility</th>
              <th scope="col">CCN</th>
              <th scope="col">City</th>
              <th scope="col">Affiliation entity</th>
              <th scope="col">${escapeHtml(config.earliestHeader)}</th>
              <th scope="col">${escapeHtml(config.latestHeader)}</th>
              <th scope="col">${escapeHtml(config.changeHeader)}</th>
              <th scope="col">${escapeHtml(earliestQuarter)} CT 3.00 status</th>
              <th scope="col">${escapeHtml(latestQuarter)} CT 3.00 status</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(record => {
              const facility = record.facility || {};
              const changeValue = record[config.metricKey];
              const changeClass = isUsableNumber(changeValue) && Number(changeValue) < 0 ? 'negative' : 'positive';
              return `
                <tr>
                  <th scope="row">${escapeHtml(getFacilityName(record))}</th>
                  <td>${escapeHtml(record.ccn || '-')}</td>
                  <td>${escapeHtml(facility.city || '-')}</td>
                  <td>${escapeHtml(facility.affiliation_entity_name || 'Not listed')}</td>
                  <td>${formatMetric(getRowValue(record, metricKind, 'earliest'))}</td>
                  <td>${formatMetric(getRowValue(record, metricKind, 'latest'))}</td>
                  <td class="${changeClass}">${formatSigned(changeValue, config.formatter)}</td>
                  <td>${renderStatus(getMetric(record.earliest, 'ct_total_direct_care_below_minimum_estimate'))}</td>
                  <td>${renderStatus(getMetric(record.latest, 'ct_total_direct_care_below_minimum_estimate'))}</td>
                  <td><a class="linkBtn" href="nursing-home-staffing-explorer.html?ccn=${encodeURIComponent(record.ccn || '')}">View facility trend</a></td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderCurrentView() {
    const rows = sortRecords(filteredRecords);
    renderPrintReportContext(rows);
    renderCurrentSummary(rows);
    renderChangeTable(rows);
  }

  function csvValue(value) {
    if (value === null || value === undefined || value === '') return '';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    return String(value);
  }

  function csvNumber(value, digits = 2) {
    return isUsableNumber(value) ? Number(value).toFixed(digits) : '';
  }

  function quoteCsvCell(value) {
    const text = csvValue(value);
    return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }

  function downloadTextFile(filename, content) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function safeSlug(value) {
    return String(value || 'change-view').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'change-view';
  }

  function buildCsv(rows) {
    const config = modeConfig[currentMode] || modeConfig['direct-decline'];
    const metricKind = getModeMetricKind(currentMode);
    const headers = [
      'mode',
      'facility_name',
      'ccn',
      'city',
      'affiliation_entity',
      'ownership_type',
      'earliest_quarter',
      'latest_quarter',
      'earliest_value',
      'latest_value',
      'change_amount',
      'earliest_below_ct_3_00_comparison_flag',
      'latest_below_ct_3_00_comparison_flag',
      'facility_detail_url'
    ];
    const dataRows = sortRecords(rows).map(record => {
      const facility = record.facility || {};
      const valueDigits = config.formatter === 'percent' ? 1 : 2;
      return {
        mode: config.label,
        facility_name: getFacilityName(record),
        ccn: record.ccn || '',
        city: facility.city || '',
        affiliation_entity: facility.affiliation_entity_name || '',
        ownership_type: facility.ownership_type || '',
        earliest_quarter: earliestQuarter,
        latest_quarter: latestQuarter,
        earliest_value: csvNumber(getRowValue(record, metricKind, 'earliest'), valueDigits),
        latest_value: csvNumber(getRowValue(record, metricKind, 'latest'), valueDigits),
        change_amount: csvNumber(record[config.metricKey], valueDigits),
        earliest_below_ct_3_00_comparison_flag: getMetric(record.earliest, 'ct_total_direct_care_below_minimum_estimate'),
        latest_below_ct_3_00_comparison_flag: getMetric(record.latest, 'ct_total_direct_care_below_minimum_estimate'),
        facility_detail_url: `tools/nursing-home-staffing-explorer.html?ccn=${record.ccn || ''}`
      };
    });
    return [
      headers.map(quoteCsvCell).join(','),
      ...dataRows.map(row => headers.map(header => quoteCsvCell(row[header])).join(','))
    ].join('\r\n') + '\r\n';
  }

  function handleDownloadCsv() {
    if (!filteredRecords.length) return;
    const filename = `staffing-change-${safeSlug(currentMode)}-${safeSlug(earliestQuarter)}-to-${safeSlug(latestQuarter)}.csv`;
    downloadTextFile(filename, buildCsv(filteredRecords));
  }

  function handlePrintCurrentView() {
    if (!filteredRecords.length) return;
    renderCurrentView();
    global.print();
  }

  async function handleCopyBriefingSummary() {
    const rows = sortRecords(filteredRecords);
    const status = document.getElementById('filter-status');
    if (!rows.length) {
      renderCurrentView();
      if (status) status.textContent = 'No facilities match the selected change mode and filters, so there is no briefing summary to copy.';
      return;
    }
    const summary = buildChangeBriefingSummary(rows);
    try {
      if (!global.navigator?.clipboard || typeof global.navigator.clipboard.writeText !== 'function') {
        throw new Error('Clipboard API unavailable');
      }
      await global.navigator.clipboard.writeText(summary);
      hideChangeSummaryFallback();
      if (status) status.textContent = 'Briefing summary copied.';
    } catch (err) {
      showChangeSummaryFallback(summary);
      if (status) status.textContent = 'Clipboard copy was unavailable; the generated briefing summary is shown below.';
    }
  }

  function resetFilters() {
    document.getElementById('facility-search').value = '';
    document.getElementById('affiliation-filter').value = 'all';
    document.getElementById('ownership-filter').value = 'all';
    document.getElementById('affiliation-presence-filter').value = 'all';
    currentMode = 'direct-decline';
    updateModeButtons();
    applyFilters();
  }

  async function loadPage() {
    const status = document.getElementById('load-status');
    try {
      if (!global.DanBeemData) throw new Error('Shared data loader did not load.');
      const data = await loadFirstAvailableJson(dataPaths);
      normalizeDataset(data);
      if (!earliestQuarter || !latestQuarter || earliestQuarter === latestQuarter) {
        throw new Error('At least two PBJ quarters are required for change-over-time comparison.');
      }
      renderSourceStatus();
      renderSummaryCards();
      populateSelectOptions();
      ['facility-search', 'affiliation-filter', 'ownership-filter', 'affiliation-presence-filter'].forEach(id => {
        document.getElementById(id).addEventListener('input', applyFilters);
        document.getElementById(id).addEventListener('change', applyFilters);
      });
      document.querySelectorAll('.mode-button').forEach(button => {
        button.addEventListener('click', () => {
          currentMode = button.dataset.mode || 'direct-decline';
          updateModeButtons();
          applyFilters();
        });
      });
      document.getElementById('download-change-csv').addEventListener('click', handleDownloadCsv);
      document.getElementById('print-change-view').addEventListener('click', handlePrintCurrentView);
      document.getElementById('copy-change-summary').addEventListener('click', handleCopyBriefingSummary);
      document.getElementById('reset-filters').addEventListener('click', resetFilters);
      updateModeButtons();
      applyFilters();
    } catch (err) {
      status.textContent = `Staffing change-over-time explorer could not be loaded. Details: ${err.message}`;
      status.className = 'notice error';
    }
  }

  document.addEventListener('DOMContentLoaded', loadPage);
})(window);
