(function(global) {
  'use strict';

  const dataPaths = [
    '../data/nursing_home_staffing_history_ct.json'
  ];
  const contextPaths = ['../data/nursing_home_staffing_ct.json'];

  const modeConfig = {
    'ct-total': {
      label: 'Below CT 3.00 direct-care comparison point in multiple quarters',
      shortLabel: 'Below CT 3.00 direct-care point',
      countLabel: 'Quarters below CT 3.00',
      latestMetricLabel: 'Latest CT direct-care HPRD estimate',
      latestStatusLabel: 'Latest CT 3.00 status',
      valueKind: 'hprd',
      sortLatest: 'asc',
      eligible: row => row?.ct_comparison_applicable_for_public_status === true,
      matches: row => row?.ct_total_direct_care_below_comparison_point === true,
      latestValue: row => getMetric(row, 'ct_direct_care_total_hprd_estimate'),
      latestStatus: row => row?.ct_comparison_applicable_for_public_status === true ? statusFromBoolean(row.ct_total_direct_care_below_comparison_point, 'Below CT 3.00', 'At/above CT 3.00') : { text: 'Not applicable for public CT status', warning: false },
      patternMatchText: 'below CT 3.00 direct-care comparison point',
      patternNonMatchText: 'at/above CT 3.00 direct-care comparison point'
    },
    'ct-licensed': {
      label: 'Below CT 0.84 licensed comparison point in multiple quarters',
      shortLabel: 'Below CT 0.84 licensed point',
      countLabel: 'Quarters below CT 0.84',
      latestMetricLabel: 'Latest CT licensed HPRD estimate',
      latestStatusLabel: 'Latest CT 0.84 status',
      valueKind: 'hprd',
      sortLatest: 'asc',
      eligible: row => row?.ct_comparison_applicable_for_public_status === true,
      matches: row => row?.ct_licensed_below_comparison_point === true,
      latestValue: row => getMetric(row, 'ct_direct_care_licensed_nurse_hprd_estimate'),
      latestStatus: row => row?.ct_comparison_applicable_for_public_status === true ? statusFromBoolean(row.ct_licensed_below_comparison_point, 'Below CT 0.84', 'At/above CT 0.84') : { text: 'Not applicable for public CT status', warning: false },
      patternMatchText: 'below CT 0.84 licensed comparison point',
      patternNonMatchText: 'at/above CT 0.84 licensed comparison point'
    },
    'case-mix': {
      label: 'Below CMS case-mix total nurse comparison point in multiple quarters',
      shortLabel: 'Below case-mix comparison point',
      countLabel: 'Quarters below case-mix comparison point',
      latestMetricLabel: 'Latest actual minus case-mix comparison point',
      latestStatusLabel: 'Latest case-mix status',
      valueKind: 'signedHprd',
      sortLatest: 'asc',
      eligible: row => isUsableNumber(getMetric(row, 'total_nurse_hprd')) && isUsableNumber(getMetric(row, 'case_mix_total_nurse_hprd')),
      matches: row => Number(getMetric(row, 'total_nurse_hprd')) < Number(getMetric(row, 'case_mix_total_nurse_hprd')),
      latestValue: row => {
        if (!modeConfig['case-mix'].eligible(row)) return null;
        return Number(getMetric(row, 'total_nurse_hprd')) - Number(getMetric(row, 'case_mix_total_nurse_hprd'));
      },
      latestStatus: row => {
        if (!modeConfig['case-mix'].eligible(row)) return { text: 'Benchmark unavailable', warning: false };
        return modeConfig['case-mix'].matches(row)
          ? { text: 'Below case-mix comparison point', warning: true }
          : { text: 'At/above case-mix comparison point', warning: false };
      },
      patternMatchText: 'below case-mix comparison point',
      patternNonMatchText: 'at/above case-mix comparison point'
    },
    'contract-10': {
      label: 'Contract staff at or above 10% in multiple quarters',
      shortLabel: 'Contract staff at/above 10%',
      countLabel: 'Quarters at/above 10%',
      latestMetricLabel: 'Latest contract staff %',
      latestStatusLabel: 'Latest contract status',
      valueKind: 'percent',
      sortLatest: 'desc',
      eligible: row => isUsableNumber(getMetric(row, 'contract_staff_pct')),
      matches: row => Number(getMetric(row, 'contract_staff_pct')) >= 10,
      latestValue: row => getMetric(row, 'contract_staff_pct'),
      latestStatus: row => statusFromThreshold(getMetric(row, 'contract_staff_pct'), 10, 'At/above 10%', 'Below 10%'),
      patternMatchText: 'contract staff at or above 10%',
      patternNonMatchText: 'contract staff below 10%'
    },
    'contract-20': {
      label: 'Contract staff at or above 20% in multiple quarters',
      shortLabel: 'Contract staff at/above 20%',
      countLabel: 'Quarters at/above 20%',
      latestMetricLabel: 'Latest contract staff %',
      latestStatusLabel: 'Latest contract status',
      valueKind: 'percent',
      sortLatest: 'desc',
      eligible: row => isUsableNumber(getMetric(row, 'contract_staff_pct')),
      matches: row => Number(getMetric(row, 'contract_staff_pct')) >= 20,
      latestValue: row => getMetric(row, 'contract_staff_pct'),
      latestStatus: row => statusFromThreshold(getMetric(row, 'contract_staff_pct'), 20, 'At/above 20%', 'Below 20%'),
      patternMatchText: 'contract staff at or above 20%',
      patternNonMatchText: 'contract staff below 20%'
    }
  };

  let dataset = null;
  let contextDataset = null;
  let facilities = [];
  let quarterlyRows = [];
  let sourceRows = [];
  let allQuarters = [];
  let selectedQuarters = [];
  let facilityRecords = [];
  let evaluatedRecords = [];
  let filteredRecords = [];
  let currentMode = 'ct-total';
  let currentThreshold = 2;
  let currentShareThreshold = 0;

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

  function getMetric(row, key) {
    if (!row) return null;
    if (row.metrics && Object.prototype.hasOwnProperty.call(row.metrics, key)) return row.metrics[key];
    if (row.benchmarks && Object.prototype.hasOwnProperty.call(row.benchmarks, key)) return row.benchmarks[key];
    return null;
  }

  function statusFromBoolean(value, trueText, falseText) {
    if (value === true) return { text: trueText, warning: true };
    if (value === false) return { text: falseText, warning: false };
    return { text: 'Not available', warning: false };
  }

  function statusFromThreshold(value, threshold, trueText, falseText) {
    if (!isUsableNumber(value)) return { text: 'Not available', warning: false };
    return Number(value) >= threshold
      ? { text: trueText, warning: true }
      : { text: falseText, warning: false };
  }

  function formatCount(value) {
    return isUsableNumber(value) ? Number(value).toLocaleString() : '0';
  }

  function formatHprd(value) {
    return isUsableNumber(value) ? Number(value).toFixed(2) : 'Not available';
  }

  function formatPercent(value) {
    return isUsableNumber(value) ? `${Number(value).toFixed(1)}%` : 'Not available';
  }

  function formatSignedHprd(value) {
    if (!isUsableNumber(value)) return 'Not available';
    const number = Number(value);
    return `${number > 0 ? '+' : ''}${number.toFixed(2)}`;
  }

  function formatMetric(value, kind) {
    if (kind === 'percent') return formatPercent(value);
    if (kind === 'signedHprd') return formatSignedHprd(value);
    return formatHprd(value);
  }

  function formatQuarterMarkerLabel(quarter) {
    return String(quarter || '').replace(/^20/, '');
  }

  function average(values) {
    const usable = values.filter(isUsableNumber).map(Number);
    if (!usable.length) return null;
    return usable.reduce((sum, value) => sum + value, 0) / usable.length;
  }

  function uniqueSorted(values) {
    return [...new Set(values.map(value => String(value || '').trim()).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b));
  }

  function quarterSort(a, b) {
    const ay = Number(String(a || '').slice(0, 4));
    const aq = Number(String(a || '').slice(-1));
    const by = Number(String(b || '').slice(0, 4));
    const bq = Number(String(b || '').slice(-1));
    return ay === by ? aq - bq : ay - by;
  }

  function selectedWindowQuarters() {
    const mode = document.getElementById('pattern-window')?.value || 'latest8';
    if (mode === 'latest4') return allQuarters.slice(Math.max(0, allQuarters.length - 4));
    if (mode === 'full') return allQuarters;
    return allQuarters.slice(Math.max(0, allQuarters.length - 8));
  }

  function getFacilityName(record) {
    return record.facility.provider_name || record.ccn || 'Unnamed facility';
  }

  function getAffiliationName(record) {
    return record.facility.affiliation_entity_name || 'No affiliation listed';
  }

  function getOwnershipType(record) {
    return record.facility.ownership_type || 'Not listed';
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
    sourceRows = Array.isArray(data.facility_quarterly_staffing_history)
      ? data.facility_quarterly_staffing_history
      : (Array.isArray(data.facility_quarterly_staffing) ? data.facility_quarterly_staffing : []);
    allQuarters = uniqueSorted(sourceRows.map(row => row.quarter)).sort(quarterSort);
    selectedQuarters = selectedWindowQuarters();
    quarterlyRows = sourceRows.filter(row => selectedQuarters.includes(row.quarter));
    const contextFacilities = Array.isArray(contextDataset?.facilities) ? contextDataset.facilities : [];
    const contextByCcn = new Map(contextFacilities.map(facility => [facility.ccn, facility]));
    const historyFacilityByCcn = new Map((data.facilities || []).map(facility => [facility.ccn, facility]));
    facilities = [...new Set(sourceRows.map(row => row.ccn).filter(Boolean))].map(ccn => {
      const context = contextByCcn.get(ccn) || {};
      const historyFacility = historyFacilityByCcn.get(ccn) || {};
      const firstRow = sourceRows.find(row => row.ccn === ccn) || {};
      return {
        ...historyFacility,
        ...context,
        ccn,
        provider_name: context.provider_name || historyFacility.latest_pbj_provider_name || firstRow.provider_name_from_pbj || ccn,
        city: context.city || historyFacility.latest_pbj_city || firstRow.city_from_pbj || '',
        state: 'CT'
      };
    });

    const facilityByCcn = new Map(facilities.map(facility => [facility.ccn, facility]));
    const rowsByCcn = new Map();
    quarterlyRows.forEach(row => {
      if (!row.ccn) return;
      if (!rowsByCcn.has(row.ccn)) rowsByCcn.set(row.ccn, []);
      rowsByCcn.get(row.ccn).push(row);
    });

    rowsByCcn.forEach(rows => rows.sort((a, b) => String(a.quarter).localeCompare(String(b.quarter))));

    facilityRecords = [...rowsByCcn.entries()].map(([ccn, rows]) => {
      const fallbackFacility = {
        ccn,
        provider_name: rows[0]?.provider_name || ccn,
        city: rows[0]?.city || '',
        state: rows[0]?.state || 'CT'
      };
      const facility = facilityByCcn.get(ccn) || fallbackFacility;
      const rowByQuarter = new Map(rows.map(row => [row.quarter, row]));
      const latestRow = rowByQuarter.get(selectedQuarters[selectedQuarters.length - 1]) || null;
      const completeHistory = selectedQuarters.every(quarter => rowByQuarter.has(quarter));
      return { ccn, facility, rows, rowByQuarter, latestRow, completeHistory };
    }).sort((a, b) => getFacilityName(a).localeCompare(getFacilityName(b)));
  }

  function evaluateRecord(record, mode) {
    const config = modeConfig[mode];
    const eligibleRows = record.rows.filter(row => config.eligible(row));
    const matchingRows = eligibleRows.filter(row => config.matches(row));
    const latestStatus = config.latestStatus(record.latestRow);
    return {
      ...record,
      mode,
      eligibleCount: eligibleRows.length,
      matchCount: matchingRows.length,
      matchingQuarters: matchingRows.map(row => row.quarter),
      matchingQuarterLabels: matchingRows.map(row => row.quarter_label || row.quarter),
      latestMatches: record.latestRow ? config.matches(record.latestRow) : false,
      latestValue: config.latestValue(record.latestRow),
      latestStatusText: latestStatus.text,
      latestStatusWarning: latestStatus.warning
    };
  }

  function buildSummaryCounts() {
    const countsFor = mode => facilityRecords
      .map(record => evaluateRecord(record, mode))
      .filter(record => record.matchCount >= 2).length;
    return {
      total: facilityRecords.length,
      complete: facilityRecords.filter(record => record.completeHistory).length,
      ctTotal: countsFor('ct-total'),
      ctLicensed: countsFor('ct-licensed'),
      caseMix: countsFor('case-mix'),
      contract10: countsFor('contract-10'),
      contract20: countsFor('contract-20')
    };
  }

  function renderSourceStatus() {
    const status = document.getElementById('load-status');
    const sourceNames = (dataset?.sources || []).map(source => source.source_dataset_name).filter(Boolean);
    status.textContent = `${sourceNames.join(' + ') || 'Connecticut staffing data'} loaded. Current data window: ${getQuarterWindowText()}.`;
    status.className = 'notice';
  }

  function getQuarterWindowText() {
    if (!selectedQuarters.length) return 'not available';
    return `${selectedQuarters[0]} through ${selectedQuarters[selectedQuarters.length - 1]}`;
  }

  function renderSummaryCards() {
    const counts = buildSummaryCounts();
    document.getElementById('summary-note').textContent =
      `The current export covers ${getQuarterWindowText()}. Missing facility-quarter rows are not counted as adverse findings.`;
    document.getElementById('summary-cards').innerHTML = `
      <div class="summary-card">
        <span class="summary-label">CT facilities in export</span>
        <strong>${formatCount(counts.total)}</strong>
        <div class="microcopy">At least one PBJ quarter row</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">All quarters available</span>
        <strong>${formatCount(counts.complete)}</strong>
        <div class="microcopy">${formatCount(allQuarters.length)} quarter history</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Below CT 3.00 direct-care point in 2+ quarters</span>
        <strong>${formatCount(counts.ctTotal)}</strong>
        <div class="microcopy">PBJ-derived CT direct-care estimate</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Below CT 0.84 licensed point in 2+ quarters</span>
        <strong>${formatCount(counts.ctLicensed)}</strong>
        <div class="microcopy">PBJ-derived licensed estimate</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Historical case-mix patterns</span>
        <strong>Not available</strong>
        <div class="microcopy">Requires historical CMS benchmark snapshots</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Contract staff 10%+ in 2+ quarters</span>
        <strong>${formatCount(counts.contract10)}</strong>
        <div class="microcopy">Quarterly contract share</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Contract staff 20%+ in 2+ quarters</span>
        <strong>${formatCount(counts.contract20)}</strong>
        <div class="microcopy">Higher contract share screen</div>
      </div>
    `;
  }

  function populateFilters() {
    const affiliationSelect = document.getElementById('affiliation-filter');
    const ownershipSelect = document.getElementById('ownership-filter');
    const affiliations = uniqueSorted(facilityRecords.map(record => record.facility.affiliation_entity_name));
    const ownershipTypes = uniqueSorted(facilityRecords.map(record => record.facility.ownership_type));
    affiliationSelect.innerHTML = '<option value="all">All affiliations</option>' +
      affiliations.map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join('');
    ownershipSelect.innerHTML = '<option value="all">All ownership types</option>' +
      ownershipTypes.map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join('');
  }

  function getActiveFilters() {
    return {
      search: document.getElementById('facility-search').value.trim(),
      affiliation: document.getElementById('affiliation-filter').value,
      ownership: document.getElementById('ownership-filter').value,
      completeHistory: document.getElementById('complete-history-filter').value
    };
  }

  function getActiveFilterSummary() {
    const filters = getActiveFilters();
    const parts = [];
    if (filters.search) parts.push(`Search term: ${filters.search}`);
    if (filters.affiliation !== 'all') parts.push(`Affiliation: ${filters.affiliation}`);
    if (filters.ownership !== 'all') parts.push(`Ownership: ${filters.ownership}`);
    if (filters.completeHistory === 'complete') parts.push('Quarter history: complete available-quarter history only');
    return parts.length ? parts : ['No active filters'];
  }

  function getMaterialFilterSummary() {
    return getActiveFilterSummary().filter(item => item !== 'No active filters');
  }

  function joinWithAnd(items) {
    if (items.length <= 1) return items.join('');
    if (items.length === 2) return `${items[0]} and ${items[1]}`;
    return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`;
  }

  function getThresholdPhrase() {
    return `${currentThreshold} or more quarters and at least ${currentShareThreshold}% of eligible quarters`;
  }

  function getPatternBriefingPhrase() {
    if (currentMode === 'ct-total') return 'below the CT 3.00 direct-care comparison point';
    if (currentMode === 'ct-licensed') return 'below the CT 0.84 licensed comparison point';
    if (currentMode === 'case-mix') return 'below the CMS case-mix total nurse comparison point';
    if (currentMode === 'contract-10') return 'contract staffing at or above 10%';
    if (currentMode === 'contract-20') return 'contract staffing at or above 20%';
    return modeConfig[currentMode]?.shortLabel || 'the selected screening pattern';
  }

  function hidePatternSummaryFallback() {
    const fallback = document.getElementById('pattern-summary-fallback');
    const textarea = document.getElementById('pattern-summary-text');
    if (fallback) fallback.hidden = true;
    if (textarea) textarea.value = '';
  }

  function showPatternSummaryFallback(summary) {
    const fallback = document.getElementById('pattern-summary-fallback');
    const textarea = document.getElementById('pattern-summary-text');
    if (!fallback || !textarea) return;
    textarea.value = summary;
    fallback.hidden = false;
    textarea.focus();
    textarea.select();
  }

  function applyFilters() {
    hidePatternSummaryFallback();
    currentThreshold = Number(document.getElementById('minimum-quarter-threshold').value || 2);
    currentShareThreshold = Number(document.getElementById('minimum-share-threshold')?.value || 0);
    const config = modeConfig[currentMode];
    const filters = getActiveFilters();
    const searchNeedle = filters.search.toLowerCase();

    evaluatedRecords = facilityRecords.map(record => evaluateRecord(record, currentMode));
    filteredRecords = evaluatedRecords
      .filter(record => record.matchCount >= currentThreshold)
      .filter(record => record.eligibleCount > 0 && (record.matchCount / record.eligibleCount) * 100 >= currentShareThreshold)
      .filter(record => {
        if (!searchNeedle) return true;
        const searchable = [
          getFacilityName(record),
          record.ccn,
          record.facility.city,
          record.facility.affiliation_entity_name
        ].join(' ').toLowerCase();
        return searchable.includes(searchNeedle);
      })
      .filter(record => filters.affiliation === 'all' || record.facility.affiliation_entity_name === filters.affiliation)
      .filter(record => filters.ownership === 'all' || record.facility.ownership_type === filters.ownership)
      .filter(record => filters.completeHistory !== 'complete' || record.completeHistory)
      .sort((a, b) => sortRecords(a, b, config));

    renderCurrentSummary();
    renderTable();
    renderPrintContext();
    updateActionState();
  }

  function sortRecords(a, b, config) {
    if (b.matchCount !== a.matchCount) return b.matchCount - a.matchCount;
    if (isUsableNumber(a.latestValue) && isUsableNumber(b.latestValue) && Number(a.latestValue) !== Number(b.latestValue)) {
      return config.sortLatest === 'desc'
        ? Number(b.latestValue) - Number(a.latestValue)
        : Number(a.latestValue) - Number(b.latestValue);
    }
    if (isUsableNumber(a.latestValue) !== isUsableNumber(b.latestValue)) {
      return isUsableNumber(a.latestValue) ? -1 : 1;
    }
    return getFacilityName(a).localeCompare(getFacilityName(b));
  }

  function renderCurrentSummary() {
    const config = modeConfig[currentMode];
    const shown = filteredRecords.length;
    const averageMatchCount = average(filteredRecords.map(record => record.matchCount));
    const latestMatches = filteredRecords.filter(record => record.latestMatches).length;
    const completeHistory = filteredRecords.filter(record => record.completeHistory).length;
    const caseMixExtra = currentMode === 'case-mix'
      ? `<div class="summary-card">
          <span class="summary-label">Benchmark-eligible rows shown</span>
          <strong>${formatCount(filteredRecords.reduce((sum, record) => sum + record.eligibleCount, 0))}</strong>
          <div class="microcopy">Across displayed facilities</div>
        </div>`
      : '';
    document.getElementById('mode-note').textContent =
      `These figures summarize facilities currently shown for "${config.label}" at the ${currentThreshold}+ quarter and ${currentShareThreshold}%+ eligible-quarter threshold.`;
    document.getElementById('current-summary-cards').innerHTML = `
      <div class="summary-card">
        <span class="summary-label">Facilities shown</span>
        <strong>${formatCount(shown)}</strong>
        <div class="microcopy">After selected mode and filters</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Average matching quarters</span>
        <strong>${isUsableNumber(averageMatchCount) ? Number(averageMatchCount).toFixed(1) : 'Not available'}</strong>
        <div class="microcopy">Simple facility average</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Currently matching latest quarter</span>
        <strong>${formatCount(latestMatches)}</strong>
        <div class="microcopy">${escapeHtml(selectedQuarters[selectedQuarters.length - 1] || 'Latest quarter')}</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Complete histories shown</span>
        <strong>${formatCount(completeHistory)}</strong>
        <div class="microcopy">${formatCount(selectedQuarters.length)} quarters in selected window</div>
      </div>
      ${caseMixExtra}
    `;
    document.getElementById('filter-status').textContent = `${formatCount(shown)} facilities shown for ${config.shortLabel} at ${currentThreshold}+ quarters and ${currentShareThreshold}%+ of eligible quarters.`;
  }

  function buildPersistentPatternBriefingSummary() {
    if (!filteredRecords.length) return '';
    const averageMatchCount = average(filteredRecords.map(record => record.matchCount));
    const latestMatches = filteredRecords.filter(record => record.latestMatches).length;
    const filters = getMaterialFilterSummary();
    const filterSentence = filters.length
      ? ` Active filters narrowing the view include ${joinWithAnd(filters)}.`
      : '';
    const leadingRows = filteredRecords.slice(0, Math.min(5, filteredRecords.length))
      .map(record => `${getFacilityName(record)} (${formatCount(record.matchCount)} matching quarters)`);
    const leadingSentence = leadingRows.length
      ? ` Leading rows under the current sort include ${joinWithAnd(leadingRows)}.`
      : '';
    return `Using CMS PBJ staffing data from ${getQuarterWindowText()}, this persistent-pattern view shows ${formatCount(filteredRecords.length)} Connecticut nursing homes that meet the selected screening pattern: ${getPatternBriefingPhrase()} in ${getThresholdPhrase()}.${filterSentence} Facilities in the current view average ${isUsableNumber(averageMatchCount) ? Number(averageMatchCount).toFixed(1) : 'not available'} matching quarters, and ${formatCount(latestMatches)} also match the selected pattern in the latest quarter.${leadingSentence} Missing PBJ rows or benchmark-ineligible quarters are not counted as adverse findings. These are screening patterns intended to support closer review, not formal violations or stand-alone care-quality conclusions.`;
  }

  function renderTable() {
    const config = modeConfig[currentMode];
    const output = document.getElementById('patterns-table');
    if (!filteredRecords.length) {
      output.innerHTML = `
        <div class="notice warning">
          No facilities match the current persistent-pattern mode, threshold, and filters.
        </div>
      `;
      return;
    }

    output.innerHTML = `
      ${renderPatternLegend()}
      <div class="table-scroll">
        <table>
          <caption>${escapeHtml(config.label)}; minimum ${currentThreshold} matching quarter${currentThreshold === 1 ? '' : 's'}.</caption>
          <thead>
            <tr>
              <th scope="col">Facility</th>
              <th scope="col">CCN</th>
              <th scope="col">City</th>
              <th scope="col">Affiliation entity</th>
              <th scope="col">${escapeHtml(config.countLabel)}</th>
              <th scope="col">Matching quarters</th>
              <th scope="col">Quarter pattern</th>
              <th scope="col">${escapeHtml(config.latestStatusLabel)}</th>
              <th scope="col">${escapeHtml(config.latestMetricLabel)}</th>
              <th scope="col">View facility trend</th>
            </tr>
          </thead>
          <tbody>
            ${filteredRecords.map(record => renderTableRow(record, config)).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderPatternLegend() {
    return `
      <div class="pattern-legend" aria-label="Quarter pattern legend">
        <span>Quarter pattern:</span>
        <span><span class="legend-marker match" aria-hidden="true">●</span> Pattern matched</span>
        <span><span class="legend-marker nonmatch" aria-hidden="true">○</span> Pattern not matched</span>
        <span><span class="legend-marker unavailable" aria-hidden="true">–</span> Data unavailable / not eligible</span>
      </div>
    `;
  }

  function renderTableRow(record, config) {
    const countText = currentMode === 'case-mix'
      ? `${formatCount(record.matchCount)} of ${formatCount(record.eligibleCount)} eligible`
      : `${formatCount(record.matchCount)} of ${formatCount(record.rows.length)}`;
    const quarters = record.matchingQuarterLabels.length
      ? record.matchingQuarterLabels.join(', ')
      : 'None';
    return `
      <tr>
        <th scope="row">${escapeHtml(getFacilityName(record))}</th>
        <td>${escapeHtml(record.ccn)}</td>
        <td>${escapeHtml(record.facility.city || 'Not listed')}</td>
        <td>${escapeHtml(getAffiliationName(record))}</td>
        <td>${escapeHtml(countText)}</td>
        <td>${escapeHtml(quarters)}</td>
        <td>${renderQuarterPattern(record, config)}</td>
        <td><span class="status-pill${record.latestStatusWarning ? ' warning' : ''}">${escapeHtml(record.latestStatusText)}</span></td>
        <td>${escapeHtml(formatMetric(record.latestValue, config.valueKind))}</td>
        <td><a href="nursing-home-staffing-explorer.html?ccn=${encodeURIComponent(record.ccn)}">View facility trend</a></td>
      </tr>
    `;
  }

  function renderQuarterPattern(record, config) {
    const markers = selectedQuarters.map(quarter => {
      const row = record.rowByQuarter.get(quarter);
      const state = getQuarterPatternState(row, config);
      const symbol = state.kind === 'match' ? '●' : state.kind === 'nonmatch' ? '○' : '–';
      const ariaLabel = `${quarter}: ${state.label}`;
      return `
        <span class="pattern-marker ${state.kind}" title="${escapeHtml(ariaLabel)}" aria-label="${escapeHtml(ariaLabel)}">
          <span class="marker-symbol" aria-hidden="true">${escapeHtml(symbol)}</span>
          <span class="marker-quarter">${escapeHtml(formatQuarterMarkerLabel(quarter))}</span>
        </span>
      `;
    }).join('');
    return `<div class="quarter-pattern">${markers}</div>`;
  }

  function getQuarterPatternState(row, config) {
    if (!row) return { kind: 'unavailable', label: 'no PBJ row' };
    if (!config.eligible(row)) return { kind: 'unavailable', label: 'no eligible data' };
    if (config.matches(row)) return { kind: 'match', label: config.patternMatchText || 'matched selected pattern' };
    return { kind: 'nonmatch', label: config.patternNonMatchText || 'did not match selected pattern' };
  }

  function renderPrintContext() {
    const config = modeConfig[currentMode];
    const filters = getActiveFilterSummary();
    const sourceCurrency = window.NursingHomeSourceCurrency?.buildCurrencySummary?.(dataset);
    document.getElementById('print-report-context').innerHTML = `
      <h1>Connecticut Nursing Home Persistent Staffing Patterns</h1>
      <p><strong>Quarter window:</strong> ${escapeHtml(getQuarterWindowText())}</p>
      <p><strong>Generated export timestamp:</strong> ${escapeHtml(dataset?.generated_at || 'Not available')}</p>
      ${sourceCurrency ? `<p><strong>Data currency:</strong> ${escapeHtml(sourceCurrency)}</p>` : ''}
      <p><strong>Selected pattern:</strong> ${escapeHtml(config.label)}</p>
      <p><strong>Minimum-quarter threshold:</strong> ${escapeHtml(String(currentThreshold))}+ matching quarters</p>
      <p><strong>Active filters:</strong> ${filters.map(escapeHtml).join('; ')}</p>
      <div class="notice">
        <strong>Disclosure:</strong> This report identifies repeated PBJ staffing screening patterns across the displayed quarter window. Missing facility-quarter rows are not counted as adverse findings. Case-mix patterns use only quarters where CMS comparison points are available. CT comparison patterns are PBJ-derived screening estimates, not formal DPH findings. Contract staffing shares are descriptive indicators and do not independently prove staffing instability, poor care, neglect, harm, or regulatory violations. Use the facility-level Staffing Explorer to review full quarter-by-quarter context.
      </div>
    `;
  }

  function updateActionState() {
    const hasRows = filteredRecords.length > 0;
    document.getElementById('download-pattern-csv').disabled = !hasRows;
    document.getElementById('print-pattern-view').disabled = !hasRows;
    document.getElementById('copy-pattern-summary').disabled = !hasRows;
  }

  function resetFilters() {
    currentMode = 'ct-total';
    document.getElementById('minimum-quarter-threshold').value = '2';
    document.getElementById('facility-search').value = '';
    document.getElementById('affiliation-filter').value = 'all';
    document.getElementById('ownership-filter').value = 'all';
    document.getElementById('complete-history-filter').value = 'all';
    updateModeButtons();
    applyFilters();
  }

  function updateModeButtons() {
    document.querySelectorAll('.mode-button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.mode === currentMode));
    });
  }

  function applyQueryParameters() {
    const params = new URLSearchParams(global.location.search);
    const requestedMode = String(params.get('mode') || '').trim();
    if (requestedMode && modeConfig[requestedMode] && requestedMode !== 'case-mix') {
      currentMode = requestedMode;
    }
    const requestedThreshold = Number(params.get('threshold'));
    if ([2, 3, 4, 5].includes(requestedThreshold)) {
      document.getElementById('minimum-quarter-threshold').value = String(requestedThreshold);
    }
    const requestedAffiliation = String(params.get('affiliation') || '').trim();
    if (requestedAffiliation) {
      const affiliationSelect = document.getElementById('affiliation-filter');
      const matchedOption = [...affiliationSelect.options].find(option => (
        option.value.toLowerCase() === requestedAffiliation.toLowerCase()
      ));
      if (matchedOption) {
        affiliationSelect.value = matchedOption.value;
      }
    }
  }

  function downloadCsv() {
    if (!filteredRecords.length) return;
    const config = modeConfig[currentMode];
    const rows = filteredRecords.map(record => ({
      pattern_mode: config.label,
      minimum_matching_quarters: currentThreshold,
      minimum_share_of_eligible_quarters: currentShareThreshold,
      facility_name: getFacilityName(record),
      ccn: record.ccn,
      city: record.facility.city || '',
      affiliation_entity: record.facility.affiliation_entity_name || '',
      ownership_type: record.facility.ownership_type || '',
      matching_quarter_count: record.matchCount,
      eligible_quarter_count: record.eligibleCount,
      available_quarter_count: record.rows.length,
      complete_selected_window_history: record.completeHistory ? 'yes' : 'no',
      matching_quarters: record.matchingQuarterLabels.join('; '),
      latest_quarter: record.latestRow?.quarter || '',
      latest_status: record.latestStatusText,
      latest_metric_label: config.latestMetricLabel,
      latest_metric_value: isUsableNumber(record.latestValue) ? Number(record.latestValue) : '',
      facility_detail_url: `nursing-home-staffing-explorer.html?ccn=${record.ccn}`
    }));
    const csv = toCsv(rows);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ct-nursing-home-persistent-patterns-${currentMode}-${currentThreshold}-plus.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function handleCopyBriefingSummary() {
    const status = document.getElementById('filter-status');
    if (!filteredRecords.length) {
      updateActionState();
      if (status) status.textContent = 'No facilities match the current persistent-pattern mode, threshold, and filters, so there is no briefing summary to copy.';
      return;
    }
    const summary = buildPersistentPatternBriefingSummary();
    try {
      if (!global.navigator?.clipboard || typeof global.navigator.clipboard.writeText !== 'function') {
        throw new Error('Clipboard API unavailable');
      }
      await global.navigator.clipboard.writeText(summary);
      hidePatternSummaryFallback();
      if (status) status.textContent = 'Briefing summary copied.';
    } catch (err) {
      showPatternSummaryFallback(summary);
      if (status) status.textContent = 'Clipboard copy was unavailable; the generated briefing summary is shown below.';
    }
  }

  function toCsv(rows) {
    if (!rows.length) return '';
    const headers = Object.keys(rows[0]);
    const escapeCsv = value => {
      const text = String(value ?? '');
      if (/[",\n\r]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
      return text;
    };
    return [
      headers.join(','),
      ...rows.map(row => headers.map(header => escapeCsv(row[header])).join(','))
    ].join('\n') + '\n';
  }

  function bindEvents() {
    document.querySelectorAll('.mode-button').forEach(button => {
      button.addEventListener('click', () => {
        currentMode = button.dataset.mode;
        updateModeButtons();
        applyFilters();
      });
    });
    [
      'pattern-window',
      'minimum-quarter-threshold',
      'minimum-share-threshold',
      'facility-search',
      'affiliation-filter',
      'ownership-filter',
      'complete-history-filter'
    ].forEach(id => {
      document.getElementById(id).addEventListener('input', applyFilters);
      document.getElementById(id).addEventListener('change', () => {
        if (id === 'pattern-window') normalizeDataset(dataset);
        applyFilters();
      });
    });
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    document.getElementById('download-pattern-csv').addEventListener('click', downloadCsv);
    document.getElementById('copy-pattern-summary').addEventListener('click', handleCopyBriefingSummary);
    document.getElementById('print-pattern-view').addEventListener('click', () => {
      if (filteredRecords.length) window.print();
    });
  }

  async function init() {
    try {
      try {
        contextDataset = await loadFirstAvailableJson(contextPaths);
      } catch (err) {
        contextDataset = null;
      }
      const data = await loadFirstAvailableJson(dataPaths);
      normalizeDataset(data);
      renderSourceStatus();
      renderSummaryCards();
      populateFilters();
      document.querySelector('[data-mode="case-mix"]')?.setAttribute('disabled', 'disabled');
      document.querySelector('[data-mode="case-mix"]')?.setAttribute('title', 'Historical case-mix comparison patterns require historically aligned CMS benchmark snapshots and are not available in the PBJ history view.');
      bindEvents();
      applyQueryParameters();
      updateModeButtons();
      applyFilters();
    } catch (err) {
      const status = document.getElementById('load-status');
      status.textContent = `Unable to load staffing data: ${err.message}`;
      status.className = 'notice error';
      document.getElementById('filter-status').textContent = 'Persistent-pattern table unavailable.';
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})(window);
