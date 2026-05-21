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
  let statewideSortKey = 'ct_total_below_share';
  let affiliationPatternMode = 'ct-total';
  let affiliationPatternThreshold = 2;
  let currentAffiliationPersistenceRows = [];
  const caseMixBenchmarkExplanation = 'How this comparison is built: the case-mix comparison point value itself is not calculated by this tool. It is imported directly from the CMS Nursing Home Provider Information field "Case-Mix Total Nurse Staffing Hours per Resident per Day." CMS describes that field as case-mix total nurse staffing HPRD combining Aide + LPN + RN. This tool compares PBJ-reported actual total nurse HPRD against that CMS-published comparison point; in affiliation views, it averages available facility comparison points and calculates actual-minus-benchmark group comparisons. These difference values are calculated by this tool. The comparison point is contextual, not actual staffing, not a legal minimum, and not proof of poor care, neglect, harm, or violations.';

  const persistentPatternConfig = {
    'ct-total': {
      label: 'Below CT 3.00 direct-care comparison point',
      countLabel: 'Facilities below CT 3.00 in threshold quarters',
      eligible: row => typeof getMetric(row, 'ct_total_direct_care_below_minimum_estimate') === 'boolean',
      matches: row => getMetric(row, 'ct_total_direct_care_below_minimum_estimate') === true
    },
    'ct-licensed': {
      label: 'Below CT 0.84 licensed comparison point',
      countLabel: 'Facilities below CT 0.84 in threshold quarters',
      eligible: row => typeof getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate') === 'boolean',
      matches: row => getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate') === true
    },
    'case-mix': {
      label: 'Below CMS case-mix total nurse comparison point',
      countLabel: 'Facilities below case-mix comparison point in threshold quarters',
      eligible: row => isUsableNumber(getMetric(row, 'total_nurse_hprd')) && isUsableNumber(getBenchmark(row, 'case_mix_total_nurse_hprd')),
      matches: row => Number(getMetric(row, 'total_nurse_hprd')) < Number(getBenchmark(row, 'case_mix_total_nurse_hprd'))
    },
    'contract-10': {
      label: 'Contract staff at or above 10%',
      countLabel: 'Facilities with contract staff 10%+ in threshold quarters',
      eligible: row => isUsableNumber(getMetric(row, 'contract_staff_pct')),
      matches: row => Number(getMetric(row, 'contract_staff_pct')) >= 10
    },
    'contract-20': {
      label: 'Contract staff at or above 20%',
      countLabel: 'Facilities with contract staff 20%+ in threshold quarters',
      eligible: row => isUsableNumber(getMetric(row, 'contract_staff_pct')),
      matches: row => Number(getMetric(row, 'contract_staff_pct')) >= 20
    }
  };

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

  function shareValue(count, denominator) {
    if (!isUsableNumber(count) || !isUsableNumber(denominator) || Number(denominator) <= 0) return null;
    return Number(count) / Number(denominator);
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

  function csvValue(value) {
    if (value === null || value === undefined || value === '') return '';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    return String(value);
  }

  function csvNumber(value) {
    return isUsableNumber(value) ? Number(value).toFixed(2) : '';
  }

  function csvPercent(value) {
    return isUsableNumber(value) ? Number(value).toFixed(1) : '';
  }

  function csvSharePercent(count, denominator) {
    const share = shareValue(count, denominator);
    return isUsableNumber(share) ? (Number(share) * 100).toFixed(1) : '';
  }

  function quoteCsvCell(value) {
    const text = csvValue(value);
    return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  }

  function buildCsv(headers, rows) {
    return [
      headers.map(quoteCsvCell).join(','),
      ...rows.map(row => headers.map(header => quoteCsvCell(row[header])).join(','))
    ].join('\r\n') + '\r\n';
  }

  function safeFilenamePart(value) {
    return String(value || 'affiliation')
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 80) || 'affiliation';
  }

  function downloadTextFile(filename, content, mimeType = 'text/csv;charset=utf-8') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
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

  function getSelectedGroup() {
    const select = document.getElementById('affiliation-select');
    const key = select?.value || '';
    return affiliations.find(group => group.key === key) || null;
  }

  function getRequestedAffiliationGroup() {
    const params = new URLSearchParams(global.location.search);
    const rawValue = String(params.get('affiliation') || '').trim();
    if (!rawValue) {
      return { group: null, requested: false, matched: false };
    }
    const normalizedValue = rawValue.toLowerCase();
    const matchedById = affiliations.find(group => String(group.affiliationId || '').trim().toLowerCase() === normalizedValue);
    if (matchedById) {
      return { group: matchedById, requested: true, matched: true };
    }
    const matchedByName = affiliations.find(group => group.key === normalizedValue || group.name.toLowerCase() === normalizedValue);
    if (matchedByName) {
      return { group: matchedByName, requested: true, matched: true };
    }
    return { group: null, requested: true, matched: false };
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

  function calculateFiveQuarterAggregate(group) {
    const rows = group.facilities.flatMap(facility => Array.isArray(facility.rows) ? facility.rows : []);
    const ctTotalRows = rows.filter(row => isUsableNumber(getMetric(row, 'ct_direct_care_total_hprd_estimate')));
    const contractRows = rows.filter(row => isUsableNumber(getMetric(row, 'contract_staff_pct')));
    return {
      facilityQuarterCount: rows.length,
      averageCtDirectCareTotalHprd: average(ctTotalRows.map(row => getMetric(row, 'ct_direct_care_total_hprd_estimate'))),
      ctTotalComparisonCount: ctTotalRows.length,
      ctTotalBelowCount: ctTotalRows.filter(row => getMetric(row, 'ct_total_direct_care_below_minimum_estimate') === true).length,
      averageContractStaffPct: average(contractRows.map(row => getMetric(row, 'contract_staff_pct')))
    };
  }

  function evaluateFacilityPersistentPattern(facility, mode = affiliationPatternMode, threshold = affiliationPatternThreshold) {
    const config = persistentPatternConfig[mode] || persistentPatternConfig['ct-total'];
    const rows = Array.isArray(facility.rows) ? facility.rows : [];
    const eligibleRows = rows.filter(row => config.eligible(row));
    const matchingRows = eligibleRows.filter(row => config.matches(row));
    const latest = getLatestQuarter();
    const latestRow = latest ? getFacilityQuarterRow(facility, latest.quarter) : null;
    const latestMatches = latestRow && config.eligible(latestRow) && config.matches(latestRow);
    return {
      facility,
      eligibleCount: eligibleRows.length,
      matchCount: matchingRows.length,
      matchingQuarters: matchingRows.map(row => row.quarter_label || row.quarter),
      meetsThreshold: matchingRows.length >= threshold,
      latestMatches: Boolean(latestMatches)
    };
  }

  function calculateGroupPersistentPattern(group, mode = affiliationPatternMode, threshold = affiliationPatternThreshold) {
    const facilityResults = group.facilities.map(facility => evaluateFacilityPersistentPattern(facility, mode, threshold));
    const matchingFacilities = facilityResults.filter(result => result.meetsThreshold);
    return {
      group,
      facilityResults,
      matchingFacilities,
      matchingFacilityCount: matchingFacilities.length,
      groupFacilityCount: group.facilities.length,
      matchingShare: shareValue(matchingFacilities.length, group.facilities.length),
      latestMatchingFacilityCount: facilityResults.filter(result => result.latestMatches).length
    };
  }

  function buildAffiliationPersistenceRows() {
    return affiliations
      .map(group => calculateGroupPersistentPattern(group))
      .sort(sortAffiliationPersistenceRows);
  }

  function sortAffiliationPersistenceRows(a, b) {
    return compareNullableNumbers(a.matchingShare, b.matchingShare, 'desc')
      || b.matchingFacilityCount - a.matchingFacilityCount
      || b.groupFacilityCount - a.groupFacilityCount
      || a.group.name.localeCompare(b.group.name);
  }

  function buildStatewideRows() {
    const latest = getLatestQuarter();
    if (!latest) return [];
    return affiliations
      .map(group => {
        const latestAggregate = calculateQuarterAggregate(group, latest.quarter);
        const patternAggregate = calculateFiveQuarterAggregate(group);
        return {
          group,
          latest,
          latestAggregate,
          patternAggregate,
          ctTotalBelowShare: shareValue(latestAggregate.ctTotalBelowCount, latestAggregate.ctTotalComparisonCount),
          ctLicensedBelowShare: shareValue(latestAggregate.ctLicensedBelowCount, latestAggregate.ctLicensedComparisonCount),
          patternCtTotalBelowShare: shareValue(patternAggregate.ctTotalBelowCount, patternAggregate.ctTotalComparisonCount)
        };
      })
      .filter(row => row.latestAggregate.facilityCount > 0);
  }

  function compareNullableNumbers(aValue, bValue, direction = 'asc') {
    const aUsable = isUsableNumber(aValue);
    const bUsable = isUsableNumber(bValue);
    if (!aUsable && !bUsable) return 0;
    if (!aUsable) return 1;
    if (!bUsable) return -1;
    return direction === 'desc' ? Number(bValue) - Number(aValue) : Number(aValue) - Number(bValue);
  }

  function sortStatewideRows(rows) {
    return rows.slice().sort((a, b) => {
      if (statewideSortKey === 'name') {
        return a.group.name.localeCompare(b.group.name);
      }
      if (statewideSortKey === 'facility_count') {
        return b.group.facilities.length - a.group.facilities.length || a.group.name.localeCompare(b.group.name);
      }
      if (statewideSortKey === 'average_ct_direct_care_total') {
        return compareNullableNumbers(a.latestAggregate.averageCtDirectCareTotalHprd, b.latestAggregate.averageCtDirectCareTotalHprd, 'asc')
          || b.group.facilities.length - a.group.facilities.length
          || a.group.name.localeCompare(b.group.name);
      }
      if (statewideSortKey === 'average_rn_hprd') {
        return compareNullableNumbers(a.latestAggregate.averageRnHprd, b.latestAggregate.averageRnHprd, 'asc')
          || b.group.facilities.length - a.group.facilities.length
          || a.group.name.localeCompare(b.group.name);
      }
      if (statewideSortKey === 'average_contract_staff_pct') {
        return compareNullableNumbers(a.latestAggregate.averageContractStaffPct, b.latestAggregate.averageContractStaffPct, 'desc')
          || b.group.facilities.length - a.group.facilities.length
          || a.group.name.localeCompare(b.group.name);
      }
      return compareNullableNumbers(a.ctTotalBelowShare, b.ctTotalBelowShare, 'desc')
        || b.group.facilities.length - a.group.facilities.length
        || compareNullableNumbers(a.latestAggregate.averageCtDirectCareTotalHprd, b.latestAggregate.averageCtDirectCareTotalHprd, 'asc')
        || a.group.name.localeCompare(b.group.name);
    });
  }

  function getSmallGroupLabel(group) {
    return group.facilities.length <= 2 ? '<div class="small-group-label">Small CT group</div>' : '';
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

  function renderInvalidAffiliationStatus() {
    const status = document.getElementById('ownership-load-status');
    if (!status) return;
    status.textContent = 'The requested affiliation entity deep link did not match the current export, so the default affiliation view is shown.';
    status.className = 'notice warning';
  }

  function setReportActionStatus(message) {
    const status = document.getElementById('report-action-status');
    if (status) status.textContent = message;
  }

  function updateReportActions(group) {
    const hasGroup = Boolean(group);
    ['print-affiliation-summary', 'download-facility-comparison-csv', 'download-trend-csv'].forEach(id => {
      const button = document.getElementById(id);
      if (button) button.disabled = !hasGroup;
    });
    setReportActionStatus(hasGroup ? 'Reporting actions use the selected affiliation entity.' : 'Select an affiliation entity to use reporting actions.');
  }

  function renderPrintReportContext(group) {
    const output = document.getElementById('print-report-context');
    if (!output || !group) return;
    const latest = getLatestQuarter();
    const latestAggregate = latest ? calculateQuarterAggregate(group, latest.quarter) : null;
    const patternAggregate = calculateFiveQuarterAggregate(group);
    const persistentConfig = persistentPatternConfig[affiliationPatternMode] || persistentPatternConfig['ct-total'];
    const persistentAggregate = calculateGroupPersistentPattern(group);
    const generatedAt = dataset?.generated_at || 'Not available';
    const reportingLabel = dataset?.reporting_period?.label || latest?.label || 'latest quarter';
    output.innerHTML = `
      <h1>Connecticut Affiliation Staffing Summary</h1>
      <div class="summary-grid">
        <div class="summary-cell"><dl><dt>Affiliation entity</dt><dd>${escapeHtml(group.name)}</dd></dl></div>
        <div class="summary-cell"><dl><dt>Affiliation entity ID</dt><dd>${escapeHtml(group.affiliationId || 'Not available')}</dd></dl></div>
        <div class="summary-cell"><dl><dt>Latest quarter</dt><dd>${escapeHtml(reportingLabel)}</dd></dl></div>
        <div class="summary-cell"><dl><dt>CT facilities linked</dt><dd>${formatCount(group.facilities.length)}</dd></dl></div>
        <div class="summary-cell"><dl><dt>Export generated</dt><dd>${escapeHtml(generatedAt)}</dd></dl></div>
      </div>
      ${latestAggregate ? `
        <div class="notice">
          Latest-quarter screening snapshot: average total nurse HPRD ${formatHprd(latestAggregate.averageTotalHprd)};
          average CT direct-care total estimate ${formatHprd(latestAggregate.averageCtDirectCareTotalHprd)};
          ${escapeHtml(formatShare(latestAggregate.ctTotalBelowCount, latestAggregate.ctTotalComparisonCount))} below the CT 3.00 direct-care comparison point;
          ${escapeHtml(formatShare(latestAggregate.ctLicensedBelowCount, latestAggregate.ctLicensedComparisonCount))} below the CT 0.84 licensed comparison point.
          Five-quarter pattern: ${escapeHtml(formatShare(patternAggregate.ctTotalBelowCount, patternAggregate.ctTotalComparisonCount))} facility-quarter rows below the CT 3.00 direct-care comparison point.
          Selected persistent pattern: ${escapeHtml(formatShare(persistentAggregate.matchingFacilityCount, persistentAggregate.groupFacilityCount))} linked facilities meet "${escapeHtml(persistentConfig.label)}" in ${affiliationPatternThreshold}+ quarters.
        </div>
      ` : ''}
      <div class="notice">
        Grouped by CMS SNF Enrollment affiliation entity. Staffing measures are CMS PBJ-derived screening metrics. Connecticut comparison points are screening estimates, not formal DPH compliance findings. ${escapeHtml(caseMixBenchmarkExplanation)} Shared affiliation does not prove identical operations or decision-making across facilities.
      </div>
    `;
  }

  function renderStatewideComparison() {
    const output = document.getElementById('statewide-comparison');
    const patternOutput = document.getElementById('five-quarter-affiliation-summary');
    const latest = getLatestQuarter();
    if (!output || !patternOutput) return;
    if (!latest) {
      output.innerHTML = '<div class="notice warning">No latest quarter is available for statewide affiliation comparison.</div>';
      patternOutput.innerHTML = '';
      return;
    }
    const rows = sortStatewideRows(buildStatewideRows());
    document.getElementById('statewide-ranking-note').textContent =
      `${latest.label} opens with groups that have the highest share of linked facilities below the CT 3.00 direct-care comparison point so potential staffing screening questions are easy to find. Use the sort buttons to change the view, and interpret small CT groups cautiously. Values are simple facility averages.`;
    output.innerHTML = `
      <div class="table-scroll" tabindex="0" aria-label="Statewide affiliation staffing comparison table">
        <table>
          <caption>Connecticut affiliation entity comparison for ${escapeHtml(latest.label)}</caption>
          <thead>
            <tr>
              <th scope="col">Affiliation entity</th>
              <th scope="col">CT facilities in group</th>
              <th scope="col">Facilities with latest PBJ data</th>
              <th scope="col">Avg total nurse HPRD</th>
              <th scope="col">Avg RN HPRD</th>
              <th scope="col">Avg CT direct-care HPRD estimate</th>
              <th scope="col">Below CT 3.00 direct-care comparison point</th>
              <th scope="col">Avg CT licensed estimate</th>
              <th scope="col">Below CT 0.84 licensed comparison point</th>
              <th scope="col">Avg contract staff %</th>
              <th scope="col">Avg case-mix benchmark</th>
              <th scope="col">Actual minus case-mix benchmark</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(item => `
              <tr>
                <th scope="row">
                  <button class="link-button view-group-button" type="button" data-group-key="${escapeHtml(item.group.key)}">${escapeHtml(item.group.name)}</button>
                  ${getSmallGroupLabel(item.group)}
                </th>
                <td>${formatCount(item.group.facilities.length)}</td>
                <td>${formatCount(item.latestAggregate.facilityCount)} of ${formatCount(item.group.facilities.length)}</td>
                <td>${formatCompactHprd(item.latestAggregate.averageTotalHprd)}</td>
                <td>${formatCompactHprd(item.latestAggregate.averageRnHprd)}</td>
                <td>${formatCompactHprd(item.latestAggregate.averageCtDirectCareTotalHprd)}</td>
                <td>${formatCompactShare(item.latestAggregate.ctTotalBelowCount, item.latestAggregate.ctTotalComparisonCount)}</td>
                <td>${formatCompactHprd(item.latestAggregate.averageCtLicensedDirectCareHprd)}</td>
                <td>${formatCompactShare(item.latestAggregate.ctLicensedBelowCount, item.latestAggregate.ctLicensedComparisonCount)}</td>
                <td>${formatCompactPercent(item.latestAggregate.averageContractStaffPct)}</td>
                <td>${formatCompactHprd(item.latestAggregate.averageBenchmarkTotalHprd)}</td>
                <td>${formatSignedHprd(item.latestAggregate.averageActualMinusBenchmark)}</td>
                <td><button class="action-button view-group-button" type="button" data-group-key="${escapeHtml(item.group.key)}">View group</button></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    patternOutput.innerHTML = `
      <div class="table-scroll compact-table" tabindex="0" aria-label="Five-quarter affiliation pattern summary table">
        <table>
          <caption>Five-quarter affiliation pattern summary, 2024Q4 through 2025Q4</caption>
          <thead>
            <tr>
              <th scope="col">Affiliation entity</th>
              <th scope="col">CT facilities</th>
              <th scope="col">Facility-quarter rows</th>
              <th scope="col">5-quarter avg CT direct-care HPRD estimate</th>
              <th scope="col">Below CT 3.00 direct-care comparison point across five quarters</th>
              <th scope="col">5-quarter avg contract staff %</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(item => `
              <tr>
                <th scope="row">${escapeHtml(item.group.name)}${getSmallGroupLabel(item.group)}</th>
                <td>${formatCount(item.group.facilities.length)}</td>
                <td>${formatCount(item.patternAggregate.facilityQuarterCount)}</td>
                <td>${formatCompactHprd(item.patternAggregate.averageCtDirectCareTotalHprd)}</td>
                <td>${formatCompactShare(item.patternAggregate.ctTotalBelowCount, item.patternAggregate.ctTotalComparisonCount)}</td>
                <td>${formatCompactPercent(item.patternAggregate.averageContractStaffPct)}</td>
                <td><button class="action-button view-group-button" type="button" data-group-key="${escapeHtml(item.group.key)}">View group</button></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
    bindViewGroupButtons();
  }

  function renderAffiliationPersistenceComparison() {
    const output = document.getElementById('affiliation-persistence-comparison');
    const note = document.getElementById('affiliation-persistence-note');
    if (!output || !note) return;
    const config = persistentPatternConfig[affiliationPatternMode] || persistentPatternConfig['ct-total'];
    const rows = buildAffiliationPersistenceRows();
    currentAffiliationPersistenceRows = rows;
    hideAffiliationPersistenceSummaryFallback();
    note.textContent = `${config.label}; showing affiliation entities sorted by the share of linked Connecticut facilities meeting the ${affiliationPatternThreshold}+ quarter persistence threshold. Small CT groups remain visible but should be read cautiously.`;
    output.innerHTML = `
      <div class="table-scroll" tabindex="0" aria-label="Affiliation persistent staffing pattern table">
        <table>
          <caption>Affiliation persistence summary: ${escapeHtml(config.label)}, ${affiliationPatternThreshold}+ quarters</caption>
          <thead>
            <tr>
              <th scope="col">Affiliation entity</th>
              <th scope="col">Affiliation ID</th>
              <th scope="col">CT facilities in group</th>
              <th scope="col">${escapeHtml(config.countLabel)}</th>
              <th scope="col">Share of group</th>
              <th scope="col">Matching facilities</th>
              <th scope="col">Latest-quarter matching facilities</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(row => renderAffiliationPersistenceRow(row)).join('')}
          </tbody>
        </table>
      </div>
    `;
    bindViewGroupButtons();
    renderAffiliationPersistencePrintContext();
    updateAffiliationPersistenceActions();
  }

  function renderAffiliationPersistenceRow(row) {
    const matchingLinks = row.matchingFacilities.length
      ? row.matchingFacilities.slice(0, 4).map(result => (
          `<a href="nursing-home-staffing-explorer.html?ccn=${encodeURIComponent(result.facility.ccn)}">${escapeHtml(result.facility.provider_name || result.facility.ccn)}</a>`
        )).join('<br>')
      : '<span class="subtle">None at this threshold</span>';
    const extraCount = row.matchingFacilities.length > 4
      ? `<br><span class="subtle">+ ${formatCount(row.matchingFacilities.length - 4)} more</span>`
      : '';
    const persistentUrl = getPersistentPatternsUrl(row.group);
    return `
      <tr>
        <th scope="row">
          <button class="link-button view-group-button" type="button" data-group-key="${escapeHtml(row.group.key)}">${escapeHtml(row.group.name)}</button>
          ${getSmallGroupLabel(row.group)}
        </th>
        <td><span class="subtle">${escapeHtml(row.group.affiliationId || 'Not available')}</span></td>
        <td>${formatCount(row.groupFacilityCount)}</td>
        <td>${formatCount(row.matchingFacilityCount)}</td>
        <td>${formatCompactPercent(isUsableNumber(row.matchingShare) ? Number(row.matchingShare) * 100 : null)}</td>
        <td>${matchingLinks}${extraCount}</td>
        <td>${formatCount(row.latestMatchingFacilityCount)}</td>
        <td>
          <button class="action-button view-group-button" type="button" data-group-key="${escapeHtml(row.group.key)}">View group</button>
          <br><a href="${escapeHtml(persistentUrl)}">View matching facilities</a>
        </td>
      </tr>
    `;
  }

  function getPersistentPatternsUrl(group) {
    const params = new URLSearchParams({
      mode: affiliationPatternMode,
      threshold: String(affiliationPatternThreshold),
      affiliation: group.name
    });
    return `nursing-home-persistent-staffing-patterns.html?${params.toString()}`;
  }

  function getQuarterWindowText() {
    const quarters = getDatasetQuarters();
    if (!quarters.length) return 'Not available';
    return `${quarters[0].label} through ${quarters[quarters.length - 1].label}`;
  }

  function getThresholdPhrase(threshold = affiliationPatternThreshold) {
    const number = Number(threshold);
    return number >= 5 ? '5' : `${formatCount(number)} or more`;
  }

  function getAffiliationPersistenceBriefingPhrase(mode = affiliationPatternMode, threshold = affiliationPatternThreshold) {
    const thresholdPhrase = getThresholdPhrase(threshold);
    switch (mode) {
      case 'ct-licensed':
        return `below the CT 0.84 licensed comparison point in ${thresholdPhrase} quarters`;
      case 'case-mix':
        return `below the CMS case-mix total nurse comparison point in ${thresholdPhrase} eligible quarters`;
      case 'contract-10':
        return `with contract staffing at or above 10% in ${thresholdPhrase} quarters`;
      case 'contract-20':
        return `with contract staffing at or above 20% in ${thresholdPhrase} quarters`;
      case 'ct-total':
      default:
        return `below the CT 3.00 direct-care comparison point in ${thresholdPhrase} quarters`;
    }
  }

  function joinWithAnd(items) {
    if (items.length <= 1) return items.join('');
    if (items.length === 2) return `${items[0]} and ${items[1]}`;
    return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`;
  }

  function buildAffiliationPersistenceBriefingSummary() {
    const rowCount = currentAffiliationPersistenceRows.length;
    if (!rowCount) return '';
    const topRows = currentAffiliationPersistenceRows.slice(0, Math.min(5, rowCount));
    const leadingEntities = topRows.map(row => (
      `${row.group.name} (${formatCount(row.matchingFacilityCount)}/${formatCount(row.groupFacilityCount)} CT facilities, ${formatCompactPercent(Number(row.matchingShare) * 100)})`
    ));
    const entityNoun = rowCount === 1 ? 'affiliation entity' : 'affiliation entities';
    const appearVerb = rowCount === 1 ? 'appears' : 'appear';
    const leadingNoun = topRows.length === 1 ? 'entity' : 'entities';
    const includeVerb = topRows.length === 1 ? 'includes' : 'include';
    return `Using CMS PBJ staffing data from ${getQuarterWindowText()}, ${formatCount(rowCount)} ${entityNoun} currently ${appearVerb} in the screening view for facilities ${getAffiliationPersistenceBriefingPhrase()}. The leading ${leadingNoun} under the current table sort ${includeVerb} ${joinWithAnd(leadingEntities)}. These are PBJ-derived screening patterns grouped by CMS SNF Enrollment affiliation entity and are intended to identify questions for closer review, not establish legal violations, common operational control, or care-quality conclusions.`;
  }

  function hideAffiliationPersistenceSummaryFallback() {
    const fallback = document.getElementById('affiliation-persistence-summary-fallback');
    const textarea = document.getElementById('affiliation-persistence-summary-text');
    if (fallback) fallback.hidden = true;
    if (textarea) textarea.value = '';
  }

  function showAffiliationPersistenceSummaryFallback(summary) {
    const fallback = document.getElementById('affiliation-persistence-summary-fallback');
    const textarea = document.getElementById('affiliation-persistence-summary-text');
    if (!fallback || !textarea) return;
    textarea.value = summary;
    fallback.hidden = false;
    textarea.focus();
    textarea.select();
  }

  function updateAffiliationPersistenceActions() {
    const hasRows = currentAffiliationPersistenceRows.length > 0;
    ['download-affiliation-persistence-csv', 'print-affiliation-persistence-view', 'copy-affiliation-persistence-summary'].forEach(id => {
      const button = document.getElementById(id);
      if (button) button.disabled = !hasRows;
    });
    if (!hasRows) hideAffiliationPersistenceSummaryFallback();
    const status = document.getElementById('affiliation-persistence-action-status');
    if (status) {
      status.textContent = hasRows
        ? `Reporting actions use ${formatCount(currentAffiliationPersistenceRows.length)} affiliation rows in the current persistence view.`
        : 'No affiliation persistence rows are available to export, print, or summarize.';
    }
  }

  function renderAffiliationPersistencePrintContext() {
    const output = document.getElementById('affiliation-persistence-print-context');
    if (!output) return;
    const config = persistentPatternConfig[affiliationPatternMode] || persistentPatternConfig['ct-total'];
    output.innerHTML = `
      <h1>Connecticut Affiliation Persistent Staffing Screening Patterns</h1>
      <div class="summary-grid">
        <div class="summary-cell"><dl><dt>Pattern mode</dt><dd>${escapeHtml(config.label)}</dd></dl></div>
        <div class="summary-cell"><dl><dt>Minimum quarters</dt><dd>${formatCount(affiliationPatternThreshold)}+</dd></dl></div>
        <div class="summary-cell"><dl><dt>Affiliation rows</dt><dd>${formatCount(currentAffiliationPersistenceRows.length)}</dd></dl></div>
        <div class="summary-cell"><dl><dt>Data window</dt><dd>${escapeHtml(getQuarterWindowText())}</dd></dl></div>
        <div class="summary-cell"><dl><dt>Export generated</dt><dd>${escapeHtml(dataset?.generated_at || 'Not available')}</dd></dl></div>
      </div>
      <div class="notice">
        This view groups Connecticut facilities by CMS SNF Enrollment affiliation entity. Persistent patterns reflect repeated screening indicators across available PBJ quarters. Missing PBJ rows and benchmark-ineligible quarters are not treated as adverse findings. CT comparison patterns are PBJ-derived screening estimates, not formal DPH compliance findings. Shared affiliation does not prove identical day-to-day operations, management decisions, or legal responsibility across facilities. Use the linked persistent-pattern and facility-level tools for drill-down review.
      </div>
    `;
  }

  function buildAffiliationPersistenceCsv() {
    const config = persistentPatternConfig[affiliationPatternMode] || persistentPatternConfig['ct-total'];
    const headers = [
      'pattern_mode',
      'minimum_matching_quarters_threshold',
      'affiliation_entity_name',
      'affiliation_entity_id',
      'ct_facilities_in_affiliation_group',
      'facilities_meeting_selected_persistent_pattern_threshold',
      'share_of_affiliation_facilities_meeting_threshold_pct',
      'latest_quarter_matching_facility_count',
      'matching_facility_names',
      'persistent_patterns_deep_link_url'
    ];
    const rows = currentAffiliationPersistenceRows.map(row => ({
      pattern_mode: config.label,
      minimum_matching_quarters_threshold: `${affiliationPatternThreshold}+`,
      affiliation_entity_name: row.group.name,
      affiliation_entity_id: row.group.affiliationId || '',
      ct_facilities_in_affiliation_group: row.groupFacilityCount,
      facilities_meeting_selected_persistent_pattern_threshold: row.matchingFacilityCount,
      share_of_affiliation_facilities_meeting_threshold_pct: isUsableNumber(row.matchingShare) ? (Number(row.matchingShare) * 100).toFixed(1) : '',
      latest_quarter_matching_facility_count: row.latestMatchingFacilityCount,
      matching_facility_names: row.matchingFacilities.map(result => result.facility.provider_name || result.facility.ccn).join('; '),
      persistent_patterns_deep_link_url: getPersistentPatternsUrl(row.group)
    }));
    return buildCsv(headers, rows);
  }

  function handleDownloadAffiliationPersistenceCsv() {
    if (!currentAffiliationPersistenceRows.length) {
      updateAffiliationPersistenceActions();
      return;
    }
    const filename = `affiliation-persistence-${safeFilenamePart(affiliationPatternMode)}-${affiliationPatternThreshold}-plus.csv`;
    downloadTextFile(filename, buildAffiliationPersistenceCsv());
    const status = document.getElementById('affiliation-persistence-action-status');
    if (status) status.textContent = `Affiliation persistence CSV prepared: ${filename}`;
  }

  function handlePrintAffiliationPersistence() {
    if (!currentAffiliationPersistenceRows.length) {
      updateAffiliationPersistenceActions();
      return;
    }
    renderAffiliationPersistencePrintContext();
    document.body.classList.add('print-affiliation-persistence');
    global.print();
  }

  async function handleCopyAffiliationPersistenceSummary() {
    const status = document.getElementById('affiliation-persistence-action-status');
    if (!currentAffiliationPersistenceRows.length) {
      updateAffiliationPersistenceActions();
      return;
    }
    const summary = buildAffiliationPersistenceBriefingSummary();
    if (!summary) {
      if (status) status.textContent = 'No affiliation persistence rows are available to summarize.';
      return;
    }
    try {
      if (!navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') {
        throw new Error('Clipboard API unavailable');
      }
      await navigator.clipboard.writeText(summary);
      hideAffiliationPersistenceSummaryFallback();
      if (status) status.textContent = 'Briefing summary copied.';
    } catch (err) {
      showAffiliationPersistenceSummaryFallback(summary);
      if (status) status.textContent = 'Clipboard copy was unavailable; the generated briefing summary is shown below.';
    }
  }

  function selectAffiliationGroup(groupKey, shouldScroll = true) {
    const group = getGroupByKey(groupKey);
    const select = document.getElementById('affiliation-select');
    const filter = document.getElementById('affiliation-filter');
    if (!group || !select) return;
    if (filter && filter.value) {
      filter.value = '';
      filteredAffiliations = affiliations.slice();
      populateAffiliationSelect(filteredAffiliations, group.key);
    }
    select.value = group.key;
    renderGroup(group.key);
    if (shouldScroll) {
      document.getElementById('selected-summary-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function bindViewGroupButtons() {
    document.querySelectorAll('.view-group-button').forEach(button => {
      button.addEventListener('click', () => {
        selectAffiliationGroup(button.dataset.groupKey || '', true);
      });
    });
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
      updateReportActions(null);
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
      <p class="subtle">Affiliation entity names come from CMS SNF Enrollments. Select a facility name for facility staffing details. These fields provide organizational context and may not describe every operational relationship among facilities.</p>
      ${renderSelectedPersistenceSummary(group)}
      <ol class="facility-list">${linkedFacilities}</ol>
    `;
  }

  function renderSelectedPersistenceSummary(group) {
    const config = persistentPatternConfig[affiliationPatternMode] || persistentPatternConfig['ct-total'];
    const aggregate = calculateGroupPersistentPattern(group);
    const matching = aggregate.matchingFacilities;
    const matchingList = matching.length
      ? `<ul>${matching.map(result => `
          <li>
            <a href="nursing-home-staffing-explorer.html?ccn=${encodeURIComponent(result.facility.ccn)}">${escapeHtml(result.facility.provider_name || result.facility.ccn)}</a>
            <span class="subtle"> - ${formatCount(result.matchCount)} matching quarter${result.matchCount === 1 ? '' : 's'}${result.matchingQuarters.length ? ` (${escapeHtml(result.matchingQuarters.join(', '))})` : ''}</span>
          </li>
        `).join('')}</ul>`
      : '<p class="subtle">No linked Connecticut facilities meet this persistent-pattern threshold.</p>';
    return `
      <div class="notice">
        <strong>Selected persistent pattern:</strong> ${escapeHtml(config.label)} in ${affiliationPatternThreshold}+ quarters.
        <div class="summary-grid">
          <div class="summary-cell"><dl><dt>Facilities meeting threshold</dt><dd>${formatCount(aggregate.matchingFacilityCount)}</dd></dl></div>
          <div class="summary-cell"><dl><dt>Share of CT group</dt><dd>${formatCompactPercent(isUsableNumber(aggregate.matchingShare) ? Number(aggregate.matchingShare) * 100 : null)}</dd></dl></div>
          <div class="summary-cell"><dl><dt>Latest-quarter matches</dt><dd>${formatCount(aggregate.latestMatchingFacilityCount)}</dd></dl></div>
        </div>
        ${matchingList}
        <p><a href="${escapeHtml(getPersistentPatternsUrl(group))}">View matching facilities in Persistent Staffing Patterns</a></p>
      </div>
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
      ? `${formatHprd(aggregate.averageBenchmarkTotalHprd)} average of available CMS Provider Information case-mix comparison points; actual minus benchmark ${formatSignedHprd(aggregate.averageActualMinusBenchmark)}. The imported facility comparison point values are not calculated by this tool; this tool calculates the group average and actual-minus-benchmark comparison.`
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
        <p class="subtle">${escapeHtml(caseMixBenchmarkExplanation)}</p>
      </article>
      <article class="metric-card card">
        <div class="summary-label">Avg CT direct-care HPRD estimate</div>
        <strong>${formatHprd(aggregate.averageCtDirectCareTotalHprd)}</strong>
        <p class="subtle">${escapeHtml(formatShare(aggregate.ctTotalBelowCount, aggregate.ctTotalComparisonCount))} below the CT 3.00 direct-care comparison point. PBJ-derived screening estimate only.</p>
      </article>
      <article class="metric-card card">
        <div class="summary-label">Avg CT licensed HPRD estimate</div>
        <strong>${formatHprd(aggregate.averageCtLicensedDirectCareHprd)}</strong>
        <p class="subtle">${escapeHtml(formatShare(aggregate.ctLicensedBelowCount, aggregate.ctLicensedComparisonCount))} below the CT 0.84 licensed comparison point. PBJ-derived screening estimate only.</p>
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
              <th scope="col">Avg CT direct-care HPRD estimate</th>
              <th scope="col">Below CT 3.00 direct-care point</th>
              <th scope="col">Avg CT licensed estimate</th>
              <th scope="col">Below CT 0.84 licensed point</th>
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
                  <td>${item.row ? `${formatCompactHprd(getMetric(item.row, 'ct_direct_care_total_hprd_estimate'))}<br><span class="subtle">${getMetric(item.row, 'ct_total_direct_care_below_minimum_estimate') === true ? 'Below CT 3.00 direct-care point' : 'At/above CT 3.00 direct-care point'}</span>` : '-'}</td>
                  <td>${item.row ? `${formatCompactHprd(getMetric(item.row, 'ct_direct_care_licensed_nurse_hprd_estimate'))}<br><span class="subtle">${getMetric(item.row, 'ct_licensed_direct_care_below_minimum_estimate') === true ? 'Below CT 0.84 licensed point' : 'At/above CT 0.84 licensed point'}</span>` : '-'}</td>
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
    updateReportActions(group);
    renderPrintReportContext(group);
    renderAffiliationSummary(group);
    renderGroupMetricCards(group);
    renderTrendTable(group);
    renderFacilityComparison(group);
  }

  function buildFacilityComparisonCsv(group) {
    const latest = getLatestQuarter();
    const headers = [
      'affiliation_entity_name',
      'affiliation_entity_id',
      'facility_name',
      'ccn',
      'city',
      'total_nurse_hprd',
      'rn_hprd',
      'contract_staff_pct',
      'ct_direct_care_total_hprd_estimate',
      'below_ct_3_00_comparison_flag',
      'ct_direct_care_licensed_nurse_hprd_estimate',
      'below_ct_0_84_comparison_flag',
      'case_mix_total_benchmark',
      'actual_minus_case_mix_benchmark'
    ];
    const rows = group.facilities.map(facility => {
      const row = latest ? getFacilityQuarterRow(facility, latest.quarter) : null;
      const actual = getMetric(row, 'total_nurse_hprd');
      const benchmark = getBenchmark(row, 'case_mix_total_nurse_hprd');
      const difference = isUsableNumber(actual) && isUsableNumber(benchmark) ? Number(actual) - Number(benchmark) : null;
      return {
        affiliation_entity_name: group.name,
        affiliation_entity_id: group.affiliationId || '',
        facility_name: facility.provider_name || '',
        ccn: facility.ccn || '',
        city: facility.city || '',
        total_nurse_hprd: csvNumber(actual),
        rn_hprd: csvNumber(getMetric(row, 'rn_hprd')),
        contract_staff_pct: csvPercent(getMetric(row, 'contract_staff_pct')),
        ct_direct_care_total_hprd_estimate: csvNumber(getMetric(row, 'ct_direct_care_total_hprd_estimate')),
        below_ct_3_00_comparison_flag: getMetric(row, 'ct_total_direct_care_below_minimum_estimate'),
        ct_direct_care_licensed_nurse_hprd_estimate: csvNumber(getMetric(row, 'ct_direct_care_licensed_nurse_hprd_estimate')),
        below_ct_0_84_comparison_flag: getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate'),
        case_mix_total_benchmark: csvNumber(benchmark),
        actual_minus_case_mix_benchmark: csvNumber(difference)
      };
    });
    return buildCsv(headers, rows);
  }

  function buildTrendCsv(group) {
    const headers = [
      'affiliation_entity_name',
      'affiliation_entity_id',
      'quarter',
      'facilities_with_pbj_data',
      'ct_facilities_in_group',
      'average_total_nurse_hprd',
      'average_rn_hprd',
      'average_contract_staff_pct',
      'average_ct_direct_care_total_hprd_estimate',
      'below_ct_3_00_count',
      'below_ct_3_00_denominator',
      'below_ct_3_00_share_pct',
      'average_ct_licensed_direct_care_hprd_estimate',
      'below_ct_0_84_count',
      'below_ct_0_84_denominator',
      'below_ct_0_84_share_pct',
      'average_case_mix_total_benchmark',
      'average_actual_minus_case_mix_benchmark'
    ];
    const rows = getDatasetQuarters().map(quarter => {
      const aggregate = calculateQuarterAggregate(group, quarter.quarter);
      return {
        affiliation_entity_name: group.name,
        affiliation_entity_id: group.affiliationId || '',
        quarter: quarter.quarter,
        facilities_with_pbj_data: aggregate.facilityCount,
        ct_facilities_in_group: group.facilities.length,
        average_total_nurse_hprd: csvNumber(aggregate.averageTotalHprd),
        average_rn_hprd: csvNumber(aggregate.averageRnHprd),
        average_contract_staff_pct: csvPercent(aggregate.averageContractStaffPct),
        average_ct_direct_care_total_hprd_estimate: csvNumber(aggregate.averageCtDirectCareTotalHprd),
        below_ct_3_00_count: aggregate.ctTotalBelowCount,
        below_ct_3_00_denominator: aggregate.ctTotalComparisonCount,
        below_ct_3_00_share_pct: csvSharePercent(aggregate.ctTotalBelowCount, aggregate.ctTotalComparisonCount),
        average_ct_licensed_direct_care_hprd_estimate: csvNumber(aggregate.averageCtLicensedDirectCareHprd),
        below_ct_0_84_count: aggregate.ctLicensedBelowCount,
        below_ct_0_84_denominator: aggregate.ctLicensedComparisonCount,
        below_ct_0_84_share_pct: csvSharePercent(aggregate.ctLicensedBelowCount, aggregate.ctLicensedComparisonCount),
        average_case_mix_total_benchmark: csvNumber(aggregate.averageBenchmarkTotalHprd),
        average_actual_minus_case_mix_benchmark: csvNumber(aggregate.averageActualMinusBenchmark)
      };
    });
    return buildCsv(headers, rows);
  }

  function getSelectedCsvFilename(group, kind) {
    const latest = getLatestQuarter();
    const quarter = safeFilenamePart(latest?.quarter || dataset?.reporting_period?.quarter || 'latest');
    return `affiliation-${kind}-${safeFilenamePart(group?.name)}-${quarter}.csv`;
  }

  function handlePrintSummary() {
    const group = getSelectedGroup();
    if (!group) {
      setReportActionStatus('Select a valid affiliation entity before printing.');
      return;
    }
    renderPrintReportContext(group);
    global.print();
  }

  function handleDownloadFacilityCsv() {
    const group = getSelectedGroup();
    if (!group) {
      setReportActionStatus('Select a valid affiliation entity before downloading.');
      return;
    }
    downloadTextFile(getSelectedCsvFilename(group, 'facility-comparison'), buildFacilityComparisonCsv(group));
    setReportActionStatus('Facility comparison CSV prepared for the selected affiliation entity.');
  }

  function handleDownloadTrendCsv() {
    const group = getSelectedGroup();
    if (!group) {
      setReportActionStatus('Select a valid affiliation entity before downloading.');
      return;
    }
    downloadTextFile(getSelectedCsvFilename(group, 'five-quarter-trend'), buildTrendCsv(group));
    setReportActionStatus('Five-quarter trend CSV prepared for the selected affiliation entity.');
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
      renderStatewideComparison();
      renderAffiliationPersistenceComparison();
      populateAffiliationSelect();
      document.getElementById('affiliation-filter').addEventListener('input', filterAffiliations);
      select.addEventListener('change', event => renderGroup(event.target.value));
      document.querySelectorAll('.sort-button').forEach(button => {
        if (!button.dataset.sortKey) return;
        button.addEventListener('click', () => {
          selectedSortKey = button.dataset.sortKey || 'name';
          updateSortButtons(selectedSortKey);
          renderGroup(select.value);
        });
      });
      document.querySelectorAll('.statewide-sort-button').forEach(button => {
        button.addEventListener('click', () => {
          statewideSortKey = button.dataset.statewideSortKey || 'ct_total_below_share';
          updateStatewideSortButtons(statewideSortKey);
          renderStatewideComparison();
        });
      });
      document.querySelectorAll('.affiliation-pattern-mode-button').forEach(button => {
        button.addEventListener('click', () => {
          affiliationPatternMode = button.dataset.affiliationPatternMode || 'ct-total';
          refreshAffiliationPersistenceViews();
        });
      });
      document.getElementById('affiliation-pattern-threshold')?.addEventListener('change', refreshAffiliationPersistenceViews);
      document.getElementById('download-affiliation-persistence-csv')?.addEventListener('click', handleDownloadAffiliationPersistenceCsv);
      document.getElementById('print-affiliation-persistence-view')?.addEventListener('click', handlePrintAffiliationPersistence);
      document.getElementById('copy-affiliation-persistence-summary')?.addEventListener('click', handleCopyAffiliationPersistenceSummary);
      global.addEventListener('afterprint', () => {
        document.body.classList.remove('print-affiliation-persistence');
      });
      document.getElementById('print-affiliation-summary')?.addEventListener('click', handlePrintSummary);
      document.getElementById('download-facility-comparison-csv')?.addEventListener('click', handleDownloadFacilityCsv);
      document.getElementById('download-trend-csv')?.addEventListener('click', handleDownloadTrendCsv);
      renderSourceStatus();
      const requestedAffiliation = getRequestedAffiliationGroup();
      if (requestedAffiliation.matched && requestedAffiliation.group) {
        selectAffiliationGroup(requestedAffiliation.group.key, true);
      } else {
        renderGroup(affiliations[0].key);
        if (requestedAffiliation.requested) {
          renderInvalidAffiliationStatus();
        }
      }
    } catch (err) {
      status.textContent = `Ownership explorer data could not be loaded. Details: ${err.message}`;
      status.className = 'notice error';
      select.disabled = true;
    }
  }

  function updateStatewideSortButtons(activeKey) {
    document.querySelectorAll('.statewide-sort-button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.statewideSortKey === activeKey));
    });
  }

  function updateAffiliationPatternModeButtons(activeMode) {
    document.querySelectorAll('.affiliation-pattern-mode-button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.affiliationPatternMode === activeMode));
    });
  }

  function refreshAffiliationPersistenceViews() {
    affiliationPatternThreshold = Number(document.getElementById('affiliation-pattern-threshold')?.value || 2);
    updateAffiliationPatternModeButtons(affiliationPatternMode);
    renderAffiliationPersistenceComparison();
    const selected = getSelectedGroup();
    if (selected) renderAffiliationSummary(selected);
  }

  document.addEventListener('DOMContentLoaded', loadPage);
})(window);
