(function(global) {
  'use strict';

  const dataPaths = [
    '../data/nursing_home_staffing_ct.json',
    '../data/nursing_home_staffing_mock.json'
  ];
  const geographyPath = '../data/nursing_home_facility_geography_ct.json';
  const unknownCountyValue = '__unknown__';
  const countyDisclosure = 'County is based on the April 2026 CMS Provider Information snapshot. Facilities without a Provider Information county match appear under Unknown / needs review. County is current context and not historical quarter-specific geography.';

  let dataset = null;
  let geographyDataset = null;
  let geographyByCcn = new Map();
  let facilities = [];
  let latestRows = [];
  let filteredRows = [];
  let sortKey = 'ct_direct_care_total';

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
    return isUsableNumber(value) ? Number(value).toFixed(2) : 'Unavailable';
  }

  function formatCompactHprd(value) {
    return isUsableNumber(value) ? Number(value).toFixed(2) : '-';
  }

  function formatPercent(value) {
    return isUsableNumber(value) ? `${Number(value).toFixed(1)}%` : '-';
  }

  function formatCount(value) {
    return isUsableNumber(value) ? Number(value).toLocaleString() : '0';
  }

  function formatSignedHprd(value) {
    if (!isUsableNumber(value)) return '-';
    const number = Number(value);
    return `${number > 0 ? '+' : ''}${number.toFixed(2)}`;
  }

  function average(values) {
    const usable = values.filter(isUsableNumber).map(Number);
    if (!usable.length) return null;
    return usable.reduce((sum, value) => sum + value, 0) / usable.length;
  }

  function getMetric(row, key) {
    return row?.metrics ? row.metrics[key] : null;
  }

  function getBenchmark(row, key) {
    return row?.benchmarks ? row.benchmarks[key] : null;
  }

  function getBenchmarkDifference(row) {
    const actual = getMetric(row, 'total_nurse_hprd');
    const benchmark = getBenchmark(row, 'case_mix_total_nurse_hprd');
    if (!isUsableNumber(actual) || !isUsableNumber(benchmark)) return null;
    return Number(actual) - Number(benchmark);
  }

  function getLatestQuarter() {
    const reportingQuarter = dataset?.reporting_period?.quarter;
    const quarters = [...new Set((dataset?.facility_quarterly_staffing || []).map(row => row.quarter).filter(Boolean))].sort();
    return reportingQuarter || quarters[quarters.length - 1] || '';
  }

  function normalizeGeography(data) {
    geographyDataset = data;
    geographyByCcn = new Map();
    (data?.facilities || []).forEach(row => {
      if (!row.ccn) return;
      geographyByCcn.set(String(row.ccn).trim(), row);
    });
  }

  function getGeographyForCcn(ccn) {
    return geographyByCcn.get(String(ccn || '').trim()) || null;
  }

  function getCountyName(row) {
    return String(row?.geography?.county_name || '').trim();
  }

  function hasUnknownCounty(row) {
    return !getCountyName(row);
  }

  function getCountyDisplay(row) {
    return getCountyName(row) || 'County unavailable';
  }

  function getGeographyMatchStatus(row) {
    const geography = row?.geography;
    if (!geography) return 'not_in_geography_crosswalk';
    if (getCountyName(row)) return 'county_matched_provider_info';
    if (geography.manual_review_required) return 'county_unavailable_needs_review';
    return 'county_unavailable';
  }

  function normalizeDataset(data) {
    dataset = data;
    const facilityRows = Array.isArray(data.facilities) ? data.facilities : [];
    const quarterlyRows = Array.isArray(data.facility_quarterly_staffing) ? data.facility_quarterly_staffing : [];
    const facilityByCcn = new Map(facilityRows.map(facility => [facility.ccn, facility]));
    const latestQuarter = getLatestQuarter();
    const latestRowByCcn = new Map(quarterlyRows
      .filter(row => row.quarter === latestQuarter && row.ccn)
      .map(row => [row.ccn, row]));

    facilities = facilityRows;
    latestRows = facilityRows
      .map(facility => {
        const row = latestRowByCcn.get(facility.ccn);
        return {
          ...(row || {
            ccn: facility.ccn,
            quarter: latestQuarter,
            quarter_label: dataset?.reporting_period?.label || latestQuarter,
            metrics: {},
            benchmarks: {},
            missing_latest_pbj_row: true
          }),
          facility: facilityByCcn.get(facility.ccn) || facility,
          geography: getGeographyForCcn(facility.ccn)
        };
      })
      .filter(row => row.ccn);
    filteredRows = latestRows.slice();
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

  function renderSourceStatus() {
    const status = document.getElementById('load-status');
    const sourceNames = (dataset?.sources || []).map(source => source.source_dataset_name).filter(Boolean);
    const latestLabel = dataset?.reporting_period?.label || getLatestQuarter() || 'latest quarter';
    status.textContent = `${sourceNames.join(' + ') || 'Connecticut staffing data'} loaded. Latest quarter: ${latestLabel}.`;
    status.className = 'notice';
  }

  function renderSummaryCards() {
    const output = document.getElementById('summary-cards');
    const latestQuarter = getLatestQuarter();
    const latestLabel = dataset?.reporting_period?.label || latestQuarter;
    const missingLatest = latestRows.filter(row => row.missing_latest_pbj_row).length;
    const belowTotal = latestRows.filter(row => getMetric(row, 'ct_total_direct_care_below_minimum_estimate') === true).length;
    const belowLicensed = latestRows.filter(row => getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate') === true).length;
    const benchmarkAvailable = latestRows.filter(row => row.benchmarks?.case_mix_benchmark_available === true).length;
    const withAffiliation = latestRows.filter(row => String(row.facility?.affiliation_entity_name || '').trim()).length;
    const unknownCounty = latestRows.filter(hasUnknownCounty).length;

    document.getElementById('summary-note').textContent =
      `${latestLabel} comparison includes ${formatCount(latestRows.length)} current runtime facilities. ${formatCount(missingLatest)} current facilities do not have a ${latestLabel} PBJ row and are shown with unavailable staffing metrics rather than being treated as zero.`;

    output.innerHTML = `
      <div class="summary-card">
        <span class="summary-label">Facilities with latest PBJ data</span>
        <strong>${formatCount(latestRows.length)}</strong>
        <div class="microcopy">${escapeHtml(latestLabel)}</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Below CT 3.00 direct-care point</span>
        <strong>${formatCount(belowTotal)}</strong>
        <div class="microcopy">PBJ-derived direct-care estimate</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Below CT 0.84 licensed point</span>
        <strong>${formatCount(belowLicensed)}</strong>
        <div class="microcopy">PBJ-derived licensed nursing estimate</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Case-mix benchmark available</span>
        <strong>${formatCount(benchmarkAvailable)}</strong>
        <div class="microcopy">Provider Information context</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">With affiliation entity data</span>
        <strong>${formatCount(withAffiliation)}</strong>
        <div class="microcopy">CMS SNF Enrollment match</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">County unavailable</span>
        <strong>${formatCount(unknownCounty)}</strong>
        <div class="microcopy">Needs review in geography crosswalk</div>
      </div>
    `;
  }

  function uniqueSorted(values) {
    return [...new Set(values.map(value => String(value || '').trim()).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b));
  }

  function populateSelectOptions() {
    const affiliationSelect = document.getElementById('affiliation-filter');
    const ownershipSelect = document.getElementById('ownership-filter');
    const countySelect = document.getElementById('county-filter');
    const affiliations = uniqueSorted(latestRows.map(row => row.facility?.affiliation_entity_name));
    const ownershipTypes = uniqueSorted(latestRows.map(row => row.facility?.ownership_type));
    const counties = uniqueSorted(latestRows.map(getCountyName));

    affiliationSelect.innerHTML = '<option value="all">All affiliations</option>' + affiliations
      .map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
      .join('');
    ownershipSelect.innerHTML = '<option value="all">All ownership types</option>' + ownershipTypes
      .map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
      .join('');
    countySelect.innerHTML = '<option value="all">All counties / all facilities</option>' + counties
      .map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
      .join('') + `<option value="${unknownCountyValue}">Unknown / needs review</option>`;
  }

  function getSortValue(row) {
    if (sortKey === 'name') return String(row.facility?.provider_name || row.ccn || '');
    if (sortKey === 'ct_direct_care_total') return getMetric(row, 'ct_direct_care_total_hprd_estimate');
    if (sortKey === 'ct_licensed') return getMetric(row, 'ct_direct_care_licensed_nurse_hprd_estimate');
    if (sortKey === 'total_nurse') return getMetric(row, 'total_nurse_hprd');
    if (sortKey === 'rn') return getMetric(row, 'rn_hprd');
    if (sortKey === 'contract') return getMetric(row, 'contract_staff_pct');
    if (sortKey === 'benchmark_difference') return getBenchmarkDifference(row);
    return getMetric(row, 'ct_direct_care_total_hprd_estimate');
  }

  function sortRows(rows) {
    return rows.slice().sort((a, b) => {
      if (sortKey === 'name') {
        return String(getSortValue(a)).localeCompare(String(getSortValue(b)));
      }
      const aValue = getSortValue(a);
      const bValue = getSortValue(b);
      const aUsable = isUsableNumber(aValue);
      const bUsable = isUsableNumber(bValue);
      if (!aUsable && !bUsable) return String(a.facility?.provider_name || '').localeCompare(String(b.facility?.provider_name || ''));
      if (!aUsable) return 1;
      if (!bUsable) return -1;
      return Number(aValue) - Number(bValue) || String(a.facility?.provider_name || '').localeCompare(String(b.facility?.provider_name || ''));
    });
  }

  function updateSortButtons() {
    document.querySelectorAll('.sort-button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.sortKey === sortKey));
    });
  }

  function getFilteredSummary(rows) {
    return {
      facilityCount: rows.length,
      belowTotal: rows.filter(row => getMetric(row, 'ct_total_direct_care_below_minimum_estimate') === true).length,
      belowLicensed: rows.filter(row => getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate') === true).length,
      avgCtDirect: average(rows.map(row => getMetric(row, 'ct_direct_care_total_hprd_estimate'))),
      avgCtLicensed: average(rows.map(row => getMetric(row, 'ct_direct_care_licensed_nurse_hprd_estimate'))),
      avgRn: average(rows.map(row => getMetric(row, 'rn_hprd'))),
      avgContract: average(rows.map(row => getMetric(row, 'contract_staff_pct'))),
      benchmarkCount: rows.filter(row => row.benchmarks?.case_mix_benchmark_available === true).length,
      avgBenchmarkDifference: average(rows.map(getBenchmarkDifference))
    };
  }

  function renderFilteredSummary(rows) {
    const output = document.getElementById('filtered-summary-cards');
    if (!output) return;
    const summary = getFilteredSummary(rows);
    output.innerHTML = `
      <div class="summary-card">
        <span class="summary-label">Facilities shown</span>
        <strong>${formatCount(summary.facilityCount)}</strong>
        <div class="microcopy">Current filtered table</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Below CT 3.00 direct-care point</span>
        <strong>${formatCount(summary.belowTotal)}</strong>
        <div class="microcopy">Filtered screening count</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Below CT 0.84 licensed point</span>
        <strong>${formatCount(summary.belowLicensed)}</strong>
        <div class="microcopy">Filtered screening count</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Avg CT direct-care HPRD</span>
        <strong>${formatCompactHprd(summary.avgCtDirect)}</strong>
        <div class="microcopy">Simple facility average</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Avg CT licensed HPRD</span>
        <strong>${formatCompactHprd(summary.avgCtLicensed)}</strong>
        <div class="microcopy">Simple facility average</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Avg RN HPRD</span>
        <strong>${formatCompactHprd(summary.avgRn)}</strong>
        <div class="microcopy">Simple facility average</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Avg contract staff %</span>
        <strong>${formatPercent(summary.avgContract)}</strong>
        <div class="microcopy">Simple facility average</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Benchmark available</span>
        <strong>${formatCount(summary.benchmarkCount)}</strong>
        <div class="microcopy">Case-mix context present</div>
      </div>
      <div class="summary-card">
        <span class="summary-label">Avg actual minus benchmark</span>
        <strong>${formatSignedHprd(summary.avgBenchmarkDifference)}</strong>
        <div class="microcopy">Rows with both values</div>
      </div>
    `;
  }

  function getSelectedOptionText(id) {
    const element = document.getElementById(id);
    return element?.selectedOptions?.[0]?.textContent || '';
  }

  function getActiveFilterSummary() {
    const query = String(document.getElementById('facility-search').value || '').trim();
    const ctFilter = document.getElementById('ct-filter').value;
    const affiliationFilter = document.getElementById('affiliation-filter').value;
    const ownershipFilter = document.getElementById('ownership-filter').value;
    const countyFilter = document.getElementById('county-filter').value;
    const contractFilter = document.getElementById('contract-filter').value;
    const filters = [];

    if (query) filters.push(`Search term: ${query}`);
    if (ctFilter !== 'all') filters.push(`CT filter: ${getSelectedOptionText('ct-filter')}`);
    if (affiliationFilter !== 'all') filters.push(`Affiliation: ${affiliationFilter}`);
    if (ownershipFilter !== 'all') filters.push(`Ownership type: ${ownershipFilter}`);
    if (countyFilter !== 'all') filters.push(`County: ${getSelectedOptionText('county-filter')}`);
    if (contractFilter !== 'all') filters.push(`Contract filter: ${getSelectedOptionText('contract-filter')}`);

    return filters.length ? filters : ['No filters active; full latest-quarter comparison shown.'];
  }

  function getMaterialFilterSummary() {
    return getActiveFilterSummary().filter(item => !item.startsWith('No filters active'));
  }

  function joinWithAnd(items) {
    if (items.length <= 1) return items.join('');
    if (items.length === 2) return `${items[0]} and ${items[1]}`;
    return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`;
  }

  function hideStatewideSummaryFallback() {
    const fallback = document.getElementById('statewide-summary-fallback');
    const textarea = document.getElementById('statewide-summary-text');
    if (fallback) fallback.hidden = true;
    if (textarea) textarea.value = '';
  }

  function showStatewideSummaryFallback(summary) {
    const fallback = document.getElementById('statewide-summary-fallback');
    const textarea = document.getElementById('statewide-summary-text');
    if (!fallback || !textarea) return;
    textarea.value = summary;
    fallback.hidden = false;
    textarea.focus();
    textarea.select();
  }

  function buildStatewideBriefingSummary(rows) {
    if (!rows.length) return '';
    const latestLabel = dataset?.reporting_period?.label || getLatestQuarter() || 'the latest available quarter';
    const summary = getFilteredSummary(rows);
    const filters = getMaterialFilterSummary();
    const filterSentence = filters.length
      ? ` Active filters narrowing the view include ${joinWithAnd(filters)}.`
      : '';
    const benchmarkSentence = isUsableNumber(summary.avgBenchmarkDifference)
      ? ` Average actual-minus-case-mix benchmark is ${formatSignedHprd(summary.avgBenchmarkDifference)} where available.`
      : '';
    const leadingRows = rows.slice(0, Math.min(5, rows.length))
      .map(row => row.facility?.provider_name || row.ccn || 'Unnamed facility');
    const leadingSentence = leadingRows.length
      ? ` Under the current sort, leading rows include ${joinWithAnd(leadingRows)}.`
      : '';
    return `Using CMS PBJ staffing data for ${latestLabel}, this filtered statewide view shows ${formatCount(summary.facilityCount)} Connecticut nursing homes. Within the current view, ${formatCount(summary.belowTotal)} facilities are below the CT 3.00 direct-care comparison point and ${formatCount(summary.belowLicensed)} are below the CT 0.84 licensed comparison point. The displayed facilities average ${formatCompactHprd(summary.avgCtDirect)} CT direct-care HPRD, ${formatCompactHprd(summary.avgRn)} RN HPRD, and ${formatPercent(summary.avgContract)} contract staffing.${benchmarkSentence}${filterSentence}${leadingSentence} These are PBJ-derived screening measures intended to identify patterns and questions for closer review, not formal DPH compliance findings or stand-alone care-quality conclusions.`;
  }

  function renderPrintReportContext(rows) {
    const output = document.getElementById('print-report-context');
    if (!output) return;
    const latestLabel = dataset?.reporting_period?.label || getLatestQuarter();
    const generatedAt = dataset?.generated_at || dataset?.generated_on || dataset?.meta?.generated_on || '';
    const sourceCurrency = global.NursingHomeSourceCurrency?.buildCurrencySummary?.(dataset);
    const summary = getFilteredSummary(rows);
    output.innerHTML = `
      <h1>Connecticut Nursing Home Statewide Staffing Comparison</h1>
      <p><strong>Latest quarter:</strong> ${escapeHtml(latestLabel || 'Unavailable')}</p>
      <p><strong>Generated export timestamp:</strong> ${escapeHtml(generatedAt || 'Not listed in export')}</p>
      ${sourceCurrency ? `<p><strong>Data currency:</strong> ${escapeHtml(sourceCurrency)}</p>` : ''}
      <p><strong>County context:</strong> ${escapeHtml(countyDisclosure)}</p>
      <div class="notice">
        <strong>Active filters:</strong>
        <ul>
          ${getActiveFilterSummary().map(item => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </div>
      <div class="notice">
        <strong>Filtered-view summary:</strong>
        ${formatCount(summary.facilityCount)} facilities shown; ${formatCount(summary.belowTotal)} below the CT 3.00 direct-care comparison point; ${formatCount(summary.belowLicensed)} below the CT 0.84 licensed comparison point; average CT direct-care HPRD ${formatCompactHprd(summary.avgCtDirect)}; average CT licensed HPRD ${formatCompactHprd(summary.avgCtLicensed)}; average RN HPRD ${formatCompactHprd(summary.avgRn)}; average contract staff ${formatPercent(summary.avgContract)}; ${formatCount(summary.benchmarkCount)} with case-mix benchmark context.
      </div>
      <div class="notice warning">
        PBJ staffing metrics are quarterly screening data. CT comparison flags are PBJ-derived estimates, not formal DPH compliance findings. Case-mix benchmark fields are contextual Provider Information comparison points. Staffing data alone do not prove poor care, neglect, harm, or violations. Facility rows should be reviewed in context using the facility explorer.
      </div>
    `;
  }

  function applyFilters() {
    const query = String(document.getElementById('facility-search').value || '').trim().toLowerCase();
    const ctFilter = document.getElementById('ct-filter').value;
    const affiliationFilter = document.getElementById('affiliation-filter').value;
    const ownershipFilter = document.getElementById('ownership-filter').value;
    const countyFilter = document.getElementById('county-filter').value;
    const contractFilter = document.getElementById('contract-filter').value;

    filteredRows = latestRows.filter(row => {
      const facility = row.facility || {};
      const countyName = getCountyName(row);
      const haystack = `${facility.provider_name || ''} ${row.ccn || ''} ${facility.city || ''} ${facility.affiliation_entity_name || ''} ${countyName}`.toLowerCase();
      if (query && !haystack.includes(query)) return false;
      if (ctFilter === 'below-total' && getMetric(row, 'ct_total_direct_care_below_minimum_estimate') !== true) return false;
      if (ctFilter === 'below-licensed' && getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate') !== true) return false;
      if (affiliationFilter !== 'all' && String(facility.affiliation_entity_name || '') !== affiliationFilter) return false;
      if (ownershipFilter !== 'all' && String(facility.ownership_type || '') !== ownershipFilter) return false;
      if (countyFilter === unknownCountyValue && !hasUnknownCounty(row)) return false;
      if (countyFilter !== 'all' && countyFilter !== unknownCountyValue && countyName !== countyFilter) return false;
      if (contractFilter !== 'all') {
        const threshold = Number(contractFilter);
        if (!isUsableNumber(getMetric(row, 'contract_staff_pct')) || Number(getMetric(row, 'contract_staff_pct')) < threshold) return false;
      }
      return true;
    });
    renderTable();
  }

  function renderStatus(value) {
    if (value === true) return '<span class="status-pill warning">Below comparison point</span>';
    if (value === false) return '<span class="status-pill">At/above comparison point</span>';
    return '<span class="subtle-note">Unavailable</span>';
  }

  function renderTable() {
    const output = document.getElementById('facility-table');
    const rows = sortRows(filteredRows);
    const latestLabel = dataset?.reporting_period?.label || getLatestQuarter();
    hideStatewideSummaryFallback();
    renderFilteredSummary(rows);
    renderPrintReportContext(rows);
    document.getElementById('filter-status').textContent = `${formatCount(rows.length)} of ${formatCount(latestRows.length)} current facility rows shown.`;
    document.getElementById('download-statewide-csv').disabled = !rows.length;
    document.getElementById('print-current-view').disabled = !rows.length;
    document.getElementById('copy-statewide-summary').disabled = !rows.length;
    if (!rows.length) {
      output.innerHTML = '<div class="notice warning">No facilities match the current filters.</div>';
      return;
    }
    output.innerHTML = `
      <div class="table-scroll" tabindex="0" aria-label="Statewide facility staffing comparison table">
        <table>
          <caption>Latest-quarter Connecticut facility staffing comparison for ${escapeHtml(latestLabel)}</caption>
          <thead>
            <tr>
              <th scope="col">Facility</th>
              <th scope="col">CCN</th>
              <th scope="col">City</th>
              <th scope="col">County</th>
              <th scope="col">Affiliation entity</th>
              <th scope="col">Total nurse HPRD</th>
              <th scope="col">RN HPRD</th>
              <th scope="col">CT direct-care HPRD estimate</th>
              <th scope="col">Below CT 3.00 status</th>
              <th scope="col">CT licensed HPRD estimate</th>
              <th scope="col">Below CT 0.84 status</th>
              <th scope="col">Contract staff %</th>
              <th scope="col">Case-mix total benchmark</th>
              <th scope="col">Actual minus benchmark</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(row => {
              const facility = row.facility || {};
              return `
                <tr>
                  <th scope="row">${escapeHtml(facility.provider_name || row.ccn || 'Unnamed facility')}</th>
                  <td>${escapeHtml(row.ccn || '-')}</td>
                  <td>${escapeHtml(facility.city || '-')}</td>
                  <td>
                    ${escapeHtml(getCountyDisplay(row))}
                    ${hasUnknownCounty(row) ? '<span class="county-secondary">Needs review</span>' : ''}
                  </td>
                  <td>${escapeHtml(facility.affiliation_entity_name || 'Not listed')}</td>
                  <td>${formatCompactHprd(getMetric(row, 'total_nurse_hprd'))}</td>
                  <td>${formatCompactHprd(getMetric(row, 'rn_hprd'))}</td>
                  <td>${formatCompactHprd(getMetric(row, 'ct_direct_care_total_hprd_estimate'))}</td>
                  <td>${renderStatus(getMetric(row, 'ct_total_direct_care_below_minimum_estimate'))}</td>
                  <td>${formatCompactHprd(getMetric(row, 'ct_direct_care_licensed_nurse_hprd_estimate'))}</td>
                  <td>${renderStatus(getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate'))}</td>
                  <td>${formatPercent(getMetric(row, 'contract_staff_pct'))}</td>
                  <td>${formatCompactHprd(getBenchmark(row, 'case_mix_total_nurse_hprd'))}</td>
                  <td>${formatSignedHprd(getBenchmarkDifference(row))}</td>
                  <td><a class="linkBtn" href="nursing-home-staffing-explorer.html?ccn=${encodeURIComponent(row.ccn || '')}">View facility details</a></td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;
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

  function buildCsv(rows) {
    const headers = [
      'facility_name',
      'ccn',
      'city',
      'county_name',
      'geography_match_status',
      'manual_review_required',
      'affiliation_entity',
      'ownership_type',
      'total_nurse_hprd',
      'rn_hprd',
      'ct_direct_care_total_hprd_estimate',
      'below_ct_3_00_comparison_flag',
      'ct_direct_care_licensed_nurse_hprd_estimate',
      'below_ct_0_84_comparison_flag',
      'contract_staff_pct',
      'case_mix_total_benchmark',
      'actual_minus_case_mix_benchmark',
      'facility_detail_url'
    ];
    const dataRows = sortRows(rows).map(row => {
      const facility = row.facility || {};
      return {
        facility_name: facility.provider_name || '',
        ccn: row.ccn || '',
        city: facility.city || '',
        county_name: getCountyName(row),
        geography_match_status: getGeographyMatchStatus(row),
        manual_review_required: Boolean(row.geography?.manual_review_required),
        affiliation_entity: facility.affiliation_entity_name || '',
        ownership_type: facility.ownership_type || '',
        total_nurse_hprd: csvNumber(getMetric(row, 'total_nurse_hprd')),
        rn_hprd: csvNumber(getMetric(row, 'rn_hprd')),
        ct_direct_care_total_hprd_estimate: csvNumber(getMetric(row, 'ct_direct_care_total_hprd_estimate')),
        below_ct_3_00_comparison_flag: getMetric(row, 'ct_total_direct_care_below_minimum_estimate'),
        ct_direct_care_licensed_nurse_hprd_estimate: csvNumber(getMetric(row, 'ct_direct_care_licensed_nurse_hprd_estimate')),
        below_ct_0_84_comparison_flag: getMetric(row, 'ct_licensed_direct_care_below_minimum_estimate'),
        contract_staff_pct: csvNumber(getMetric(row, 'contract_staff_pct'), 1),
        case_mix_total_benchmark: csvNumber(getBenchmark(row, 'case_mix_total_nurse_hprd')),
        actual_minus_case_mix_benchmark: csvNumber(getBenchmarkDifference(row)),
        facility_detail_url: `tools/nursing-home-staffing-explorer.html?ccn=${row.ccn || ''}`
      };
    });
    return [
      headers.map(quoteCsvCell).join(','),
      ...dataRows.map(row => headers.map(header => quoteCsvCell(row[header])).join(','))
    ].join('\r\n') + '\r\n';
  }

  function handleDownloadCsv() {
    if (!filteredRows.length) return;
    const latestQuarter = getLatestQuarter() || 'latest';
    downloadTextFile(`statewide-staffing-comparison-${latestQuarter.toLowerCase()}-filtered.csv`, buildCsv(filteredRows));
  }

  function resetFilters() {
    document.getElementById('facility-search').value = '';
    document.getElementById('ct-filter').value = 'all';
    document.getElementById('affiliation-filter').value = 'all';
    document.getElementById('ownership-filter').value = 'all';
    document.getElementById('county-filter').value = 'all';
    document.getElementById('contract-filter').value = 'all';
    sortKey = 'ct_direct_care_total';
    updateSortButtons();
    applyFilters();
  }

  function handlePrintCurrentView() {
    if (!filteredRows.length) return;
    renderTable();
    global.print();
  }

  async function handleCopyBriefingSummary() {
    const rows = sortRows(filteredRows);
    const status = document.getElementById('filter-status');
    if (!rows.length) {
      renderTable();
      if (status) status.textContent = 'No facilities match the current filters, so there is no briefing summary to copy.';
      return;
    }
    const summary = buildStatewideBriefingSummary(rows);
    try {
      if (!global.navigator?.clipboard || typeof global.navigator.clipboard.writeText !== 'function') {
        throw new Error('Clipboard API unavailable');
      }
      await global.navigator.clipboard.writeText(summary);
      hideStatewideSummaryFallback();
      if (status) status.textContent = 'Briefing summary copied.';
    } catch (err) {
      showStatewideSummaryFallback(summary);
      if (status) status.textContent = 'Clipboard copy was unavailable; the generated briefing summary is shown below.';
    }
  }

  async function loadPage() {
    const status = document.getElementById('load-status');
    try {
      if (!global.DanBeemData) throw new Error('Shared data loader did not load.');
      const [data, geographyData] = await Promise.all([
        loadFirstAvailableJson(dataPaths),
        global.DanBeemData.loadJson(geographyPath)
      ]);
      normalizeGeography(geographyData);
      normalizeDataset(data);
      if (!latestRows.length) throw new Error('No latest-quarter facility rows were found in the staffing export.');
      renderSourceStatus();
      renderSummaryCards();
      populateSelectOptions();
      ['facility-search', 'ct-filter', 'affiliation-filter', 'ownership-filter', 'county-filter', 'contract-filter'].forEach(id => {
        document.getElementById(id).addEventListener('input', applyFilters);
        document.getElementById(id).addEventListener('change', applyFilters);
      });
      document.querySelectorAll('.sort-button').forEach(button => {
        button.addEventListener('click', () => {
          sortKey = button.dataset.sortKey || 'ct_direct_care_total';
          updateSortButtons();
          renderTable();
        });
      });
      document.getElementById('download-statewide-csv').addEventListener('click', handleDownloadCsv);
      document.getElementById('reset-filters').addEventListener('click', resetFilters);
      document.getElementById('print-current-view').addEventListener('click', handlePrintCurrentView);
      document.getElementById('copy-statewide-summary').addEventListener('click', handleCopyBriefingSummary);
      updateSortButtons();
      renderTable();
    } catch (err) {
      status.textContent = `Statewide staffing comparison could not be loaded. Details: ${err.message}`;
      status.className = 'notice error';
    }
  }

  document.addEventListener('DOMContentLoaded', loadPage);
})(window);
