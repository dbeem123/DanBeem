(function(global) {
  'use strict';

  /**
   * @typedef {Object} StaffingSource
   * @property {string} source_dataset_name
   * @property {string} source_release
   * @property {string} freshness_date
   */

  /**
   * @typedef {Object} FacilityDirectoryRow
   * @property {string} facility_id
   * @property {string} ccn
   * @property {string} provider_name
   * @property {string} city
   * @property {string} state
   */

  /**
   * @typedef {Object} QuarterlyStaffingRow
   * @property {string} ccn
   * @property {string} quarter
   * @property {string} quarter_label
   * @property {number|null} average_resident_census
   * @property {number|null} resident_days
   * @property {{total_nurse_hprd:number|null,rn_hprd:number|null,lpn_lvn_hprd:number|null,nurse_aide_hprd:number|null,contract_staff_pct:number|null}} metrics
   * @property {{case_mix_total_nurse_hprd:number|null,case_mix_benchmark_available:boolean}=} benchmarks
   * @property {{shows:string,suggests:string,cannot_prove:string}=} interpretation
   * @property {{missing_fields:string[],notes:string[]}=} data_quality
   */

  /**
   * @typedef {Object} FacilityViewModel
   * @property {string} id
   * @property {string} ccn
   * @property {string} name
   * @property {string} city
   * @property {string} state
   * @property {string=} address
   * @property {number|null=} certifiedBeds
   * @property {string=} ownershipType
   * @property {number|null=} cmsOverallRating
   * @property {number|null=} cmsHealthInspectionRating
   * @property {number|null=} cmsStaffingRating
   * @property {number|null=} cmsRnStaffingRating
   * @property {number|null=} cmsQmRating
   * @property {number|null=} cmsLongStayQmRating
   * @property {number|null=} cmsShortStayQmRating
   * @property {string=} cmsRatingSource
   * @property {string=} cmsRatingSourceNote
   * @property {Array<Object>=} qualityMeasuresClaims
   * @property {boolean=} providerSourceMatched
   * @property {boolean=} enrollmentSourceMatched
   * @property {string=} enrollmentOrganizationName
   * @property {string=} enrollmentDoingBusinessAsName
   * @property {string=} enrollmentProprietaryNonprofit
   * @property {string=} enrollmentOrganizationTypeStructure
   * @property {string=} affiliationEntityName
   * @property {QuarterlyStaffingRow|null} currentRow
   * @property {QuarterlyStaffingRow[]} historyRows
   */

  const metricDefinitions = [
    {
      key: 'total_nurse_hprd',
      label: 'Total nurse HPRD',
      format: formatHprd,
      help: 'Total reported RN, LPN/LVN, and nurse aide hours divided by resident days for the quarter.'
    },
    {
      key: 'rn_hprd',
      label: 'RN HPRD',
      format: formatHprd,
      help: 'Registered nurse hours per resident day. RN time may include direct care and reported RN administrative categories.'
    },
    {
      key: 'lpn_lvn_hprd',
      label: 'LPN/LVN HPRD',
      format: formatHprd,
      help: 'Licensed practical or vocational nurse hours per resident day.'
    },
    {
      key: 'nurse_aide_hprd',
      label: 'Nurse aide HPRD',
      format: formatHprd,
      help: 'Certified nurse aide, aide trainee, and medication aide hours per resident day.'
    },
    {
      key: 'contract_staff_pct',
      label: 'Contract staff %',
      format: formatPercent,
      help: 'Percent of reported nursing hours supplied by contract staff. This can suggest reliance on agency or temporary staffing, but it does not measure continuity by itself.'
    }
  ];

  let dataset = null;
  /** @type {FacilityViewModel[]} */
  let facilities = [];
  let filteredFacilities = [];
  const dataPaths = [
    '../data/nursing_home_staffing_ct.json',
    '../data/nursing_home_staffing_mock.json'
  ];
  const caseMixBenchmarkExplanation = 'How this comparison is built: the case-mix comparison point value itself is not calculated by this tool. It is imported directly from the CMS Nursing Home Provider Information field "Case-Mix Total Nurse Staffing Hours per Resident per Day." CMS describes that field as case-mix total nurse staffing HPRD combining Aide + LPN + RN. This tool compares the facility\'s PBJ-reported actual total nurse HPRD against that CMS-published comparison point. The actual-minus-benchmark difference and percent-of-benchmark text are calculated by this tool. The comparison point is contextual, not actual staffing, not a legal minimum, and not proof of poor care, neglect, harm, or violations.';

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

  function formatPercent(value) {
    return isUsableNumber(value) ? `${Number(value).toFixed(1)}%` : 'Not available';
  }

  function formatCount(value) {
    return isUsableNumber(value) ? Number(value).toLocaleString() : 'Not available';
  }

  function formatRatingText(value) {
    return isUsableNumber(value) ? `${Number(value).toLocaleString()} of 5` : 'Not available';
  }

  function formatSignedHprd(value) {
    if (!isUsableNumber(value)) return 'not available';
    const number = Number(value);
    const sign = number > 0 ? '+' : '';
    return `${sign}${number.toFixed(2)}`;
  }

  function formatScore(value) {
    return isUsableNumber(value)
      ? Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })
      : 'Not available';
  }

  function formatYesNo(value) {
    if (value === true) return 'Yes';
    if (value === false) return 'No';
    return 'Not available';
  }

  function csvValue(value) {
    if (value === null || value === undefined || value === '') return '';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    return String(value);
  }

  function csvNumber(value) {
    return isUsableNumber(value) ? Number(value).toFixed(2) : '';
  }

  function csvOneDecimal(value) {
    return isUsableNumber(value) ? Number(value).toFixed(1) : '';
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
    return String(value || 'facility')
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 90) || 'facility';
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

  function formatCtComparisonStatus(isBelow, minimum) {
    if (isBelow === true) return `Below CT ${Number(minimum).toFixed(2)} comparison point`;
    if (isBelow === false) return `At or above CT ${Number(minimum).toFixed(2)} comparison point`;
    return 'CT comparison not available';
  }

  function getCtTotalStatus(metrics) {
    const minimum = isUsableNumber(metrics.ct_total_direct_care_minimum_hprd)
      ? Number(metrics.ct_total_direct_care_minimum_hprd)
      : 3.00;
    return formatCtComparisonStatus(metrics.ct_total_direct_care_below_minimum_estimate, minimum)
      .replace('CT 3.00 comparison point', 'CT 3.00 direct-care comparison point');
  }

  function getCtLicensedStatus(metrics) {
    const minimum = isUsableNumber(metrics.ct_licensed_direct_care_minimum_hprd)
      ? Number(metrics.ct_licensed_direct_care_minimum_hprd)
      : 0.84;
    return formatCtComparisonStatus(metrics.ct_licensed_direct_care_below_minimum_estimate, minimum)
      .replace('CT 0.84 comparison point', 'CT 0.84 licensed comparison point');
  }

  function byQuarter(a, b) {
    return String(a.quarter || '').localeCompare(String(b.quarter || ''));
  }

  function getDatasetQuarters() {
    const rows = Array.isArray(dataset?.facility_quarterly_staffing) ? dataset.facility_quarterly_staffing : [];
    const byKey = new Map();
    rows.forEach(row => {
      if (!row.quarter) return;
      byKey.set(row.quarter, row.quarter_label || row.quarter);
    });
    return [...byKey.entries()]
      .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
      .map(([quarter, label]) => ({ quarter, label }));
  }

  function getFacilityById(id) {
    return facilities.find(facility => facility.id === id) || facilities[0];
  }

  function getSelectedFacility() {
    const select = document.getElementById('facility-select');
    const id = select?.value || '';
    return facilities.find(facility => facility.id === id) || null;
  }

  function getFacilityIdFromUrl() {
    const params = new URLSearchParams(global.location.search);
    const ccn = String(params.get('ccn') || '').trim();
    const facilityId = String(params.get('facility') || '').trim();
    if (ccn) {
      const matchedByCcn = facilities.find(facility => facility.ccn === ccn);
      if (matchedByCcn) return matchedByCcn.id;
    }
    if (facilityId && facilities.some(facility => facility.id === facilityId)) {
      return facilityId;
    }
    return facilities[0]?.id || '';
  }

  function getCurrentRow(rows) {
    const reportingQuarter = dataset?.reporting_period?.quarter;
    return rows.find(row => row.quarter === reportingQuarter) || rows[rows.length - 1] || null;
  }

  function normalizeDataset(data) {
    const directoryRows = Array.isArray(data.facilities) ? data.facilities : [];
    const quarterlyRows = Array.isArray(data.facility_quarterly_staffing) ? data.facility_quarterly_staffing : [];

    dataset = data;
    facilities = directoryRows.map(facility => {
      const historyRows = quarterlyRows
        .filter(row => row.ccn === facility.ccn)
        .sort(byQuarter);
      return {
        id: facility.facility_id || facility.ccn,
        ccn: facility.ccn,
        name: facility.provider_name || 'Unnamed facility',
        city: facility.city || 'City unavailable',
        state: facility.state || 'State unavailable',
        address: facility.address || '',
        certifiedBeds: facility.certified_beds,
        ownershipType: facility.ownership_type || '',
        cmsOverallRating: facility.cms_overall_rating,
        cmsHealthInspectionRating: facility.cms_health_inspection_rating,
        cmsStaffingRating: facility.cms_staffing_rating,
        cmsRnStaffingRating: facility.cms_rn_staffing_rating,
        cmsQmRating: facility.cms_qm_rating,
        cmsLongStayQmRating: facility.cms_long_stay_qm_rating,
        cmsShortStayQmRating: facility.cms_short_stay_qm_rating,
        cmsRatingSource: facility.cms_rating_source || '',
        cmsRatingSourceNote: facility.cms_rating_source_note || '',
        qualityMeasuresClaims: Array.isArray(facility.quality_measures_claims) ? facility.quality_measures_claims : [],
        providerSourceMatched: Boolean(facility.provider_source_matched),
        enrollmentSourceMatched: Boolean(facility.enrollment_source_matched),
        enrollmentOrganizationName: facility.enrollment_organization_name || '',
        enrollmentDoingBusinessAsName: facility.enrollment_doing_business_as_name || '',
        enrollmentProprietaryNonprofit: facility.enrollment_proprietary_nonprofit || '',
        enrollmentOrganizationTypeStructure: facility.enrollment_organization_type_structure || '',
        affiliationEntityName: facility.affiliation_entity_name || '',
        affiliationEntityId: facility.affiliation_entity_id || '',
        currentRow: getCurrentRow(historyRows),
        historyRows
      };
    });
    filteredFacilities = facilities.slice();
  }

  function getFacilityOptionLabel(facility) {
    return `${facility.name} - ${facility.city}, ${facility.state} (${facility.ccn})`;
  }

  function populateFacilitySelect(list = filteredFacilities, selectedId = null) {
    const select = document.getElementById('facility-select');
    if (!list.length) {
      select.innerHTML = '<option value="">No facilities match this search</option>';
      select.disabled = true;
      updateFilterStatus(0);
      return;
    }
    select.disabled = false;
    select.innerHTML = list.map(facility => (
      `<option value="${escapeHtml(facility.id)}">${escapeHtml(getFacilityOptionLabel(facility))}</option>`
    )).join('');
    if (selectedId && list.some(facility => facility.id === selectedId)) {
      select.value = selectedId;
    }
    updateFilterStatus(list.length);
  }

  function updateFilterStatus(count) {
    const status = document.getElementById('facility-filter-status');
    if (!status) return;
    status.textContent = `${count} of ${facilities.length} facilities shown.`;
  }

  function filterFacilities() {
    const filterInput = document.getElementById('facility-filter');
    const query = String(filterInput.value || '').trim().toLowerCase();
    const currentId = document.getElementById('facility-select').value;
    filteredFacilities = facilities.filter(facility => {
      const haystack = `${facility.name} ${facility.city} ${facility.state} ${facility.ccn}`.toLowerCase();
      return haystack.includes(query);
    });
    populateFacilitySelect(filteredFacilities, currentId);
    if (filteredFacilities.length) {
      const next = getFacilityById(document.getElementById('facility-select').value) || filteredFacilities[0];
      renderFacility(next.id);
    } else {
      updateReportActions(null);
    }
  }

  function renderSourceStatus() {
    const status = document.getElementById('staffing-load-status');
    const sources = Array.isArray(dataset?.sources) ? dataset.sources : [];
    const sourceNames = sources.map(source => source.source_dataset_name).filter(Boolean);
    const freshnessDates = sources.map(source => source.freshness_date).filter(Boolean);
    const reportingLabel = dataset?.reporting_period?.label || dataset?.reporting_period?.quarter || 'selected quarter';
    const freshness = freshnessDates.length ? ` Freshness date: ${freshnessDates[0]}.` : '';

    status.textContent = `${sourceNames.length ? sourceNames.join(' + ') : 'Staffing data'} loaded for Connecticut ${reportingLabel}.${freshness}`;
    status.className = 'notice';
  }

  function renderDatasetSummary() {
    const output = document.getElementById('dataset-summary');
    if (!output) return;
    const reportingLabel = dataset?.reporting_period?.label || 'Current quarter';
    const quality = dataset?.data_quality || {};
    const source = Array.isArray(dataset?.sources) ? dataset.sources[0] : null;
    output.innerHTML = `
      <div class="dataset-fact">
        <span class="summary-label">State</span>
        <strong>Connecticut</strong>
      </div>
      <div class="dataset-fact">
        <span class="summary-label">Quarter</span>
        <strong>${escapeHtml(reportingLabel)}</strong>
      </div>
      <div class="dataset-fact">
        <span class="summary-label">Facilities</span>
        <strong>${formatCount(quality.facility_count || facilities.length)}</strong>
      </div>
      <div class="dataset-fact">
        <span class="summary-label">Source</span>
        <strong>CMS PBJ</strong>
        <div class="microcopy">${escapeHtml(source?.source_release || 'Static export')}</div>
      </div>
    `;
  }

  function setReportActionStatus(message) {
    const status = document.getElementById('report-action-status');
    if (status) status.textContent = message;
  }

  function updateReportActions(facility) {
    const hasFacility = Boolean(facility);
    ['print-facility-summary', 'download-facility-trend-csv'].forEach(id => {
      const button = document.getElementById(id);
      if (button) button.disabled = !hasFacility;
    });
    setReportActionStatus(hasFacility ? 'Reporting actions use the selected facility.' : 'Select a facility to use reporting actions.');
  }

  function getCareCompareRatingRows(facility) {
    return [
      ['Overall', facility.cmsOverallRating],
      ['Health inspection', facility.cmsHealthInspectionRating],
      ['Staffing', facility.cmsStaffingRating],
      ['Quality measures', facility.cmsQmRating],
      ['Long-stay QM', facility.cmsLongStayQmRating],
      ['Short-stay QM', facility.cmsShortStayQmRating],
      ['RN staffing', facility.cmsRnStaffingRating]
    ].filter(([, value]) => isUsableNumber(value));
  }

  function renderStarRating(value) {
    if (!isUsableNumber(value)) return '';
    const rating = Math.max(0, Math.min(5, Math.round(Number(value))));
    const filled = '★'.repeat(rating);
    const empty = '☆'.repeat(5 - rating);
    return `
      <span class="star-rating" aria-hidden="true">
        <span class="star-filled">${filled}</span><span class="star-empty">${empty}</span>
      </span>
    `;
  }

  function renderCareCompareRatingItems(facility) {
    return getCareCompareRatingRows(facility)
      .map(([label, value]) => `
        <article class="rating-card" aria-label="${escapeHtml(`${label} rating: ${formatRatingText(value)} stars.`)}">
          <div class="summary-label">${escapeHtml(label)}</div>
          <div class="rating-value">${escapeHtml(formatRatingText(value))}</div>
          ${renderStarRating(value)}
          <p class="microcopy">CMS Provider Information rating imported into this tool.</p>
        </article>
      `)
      .join('');
  }

  function renderCareCompareRatingContext(facility) {
    const rows = renderCareCompareRatingItems(facility);
    if (!rows) return '';
    const note = facility.cmsRatingSourceNote || 'CMS Care Compare ratings are contextual summary ratings from Provider Information. They are not calculated by this tool and should be interpreted alongside the staffing metrics and source caveats.';
    return `
      <div class="ownership-context care-compare-context">
        <h3>CMS Care Compare rating context</h3>
        <div class="care-compare-rating-grid">${rows}</div>
        <p class="subtle">${escapeHtml(note)}</p>
      </div>
    `;
  }

  function renderCareCompareRatingSection(facility) {
    const output = document.getElementById('care-compare-context');
    if (!output) return;
    const content = renderCareCompareRatingContext(facility);
    output.innerHTML = content || '<div class="notice warning">CMS Care Compare rating fields are not available for this facility in the current export.</div>';
  }

  function renderQualityMeasureDescription(measure) {
    const footnote = String(measure.footnote_for_score || '').trim();
    return `
      <strong>${escapeHtml(measure.measure_description || measure.measure_code || 'Quality measure')}</strong>
      ${footnote ? `<div class="microcopy">Footnote: ${escapeHtml(footnote)}</div>` : ''}
    `;
  }

  function renderQualityMeasuresClaimsTable(facility, options = {}) {
    const measures = Array.isArray(facility.qualityMeasuresClaims) ? facility.qualityMeasuresClaims : [];
    if (!measures.length) return '';
    const limit = options.limit || measures.length;
    const rows = measures.slice(0, limit).map(measure => `
      <tr>
        <th scope="row">${renderQualityMeasureDescription(measure)}</th>
        <td>${escapeHtml(measure.resident_type || 'Not available')}</td>
        <td>${escapeHtml(formatScore(measure.adjusted_score))}</td>
        <td>${escapeHtml(formatScore(measure.observed_score))}</td>
        <td>${escapeHtml(formatScore(measure.expected_score))}</td>
        <td>${escapeHtml(measure.measure_period || 'Not available')}</td>
        <td>${escapeHtml(formatYesNo(measure.used_in_qm_five_star_rating))}</td>
      </tr>
    `).join('');
    return `
      <div class="table-scroll" tabindex="0" aria-label="CMS claims-based quality measures table">
        <table class="quality-measures-table">
          <thead>
            <tr>
              <th scope="col">Measure</th>
              <th scope="col">Resident type</th>
              <th scope="col">Adjusted</th>
              <th scope="col">Observed</th>
              <th scope="col">Expected</th>
              <th scope="col">Period</th>
              <th scope="col">Used in QM rating</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  }

  function renderQualityMeasuresClaimsContext(facility) {
    const measures = Array.isArray(facility.qualityMeasuresClaims) ? facility.qualityMeasuresClaims : [];
    if (!measures.length) return '';
    const periods = [...new Set(measures.map(measure => measure.measure_period).filter(Boolean))];
    return `
      <div class="ownership-context quality-measures-context">
        <h3>CMS claims-based quality measures</h3>
        <p class="subtle">These facility-level measures are imported from CMS Nursing Home Quality Measures Claims data. They are not calculated by this tool, are not staffing measures, and should be interpreted with measure definitions, footnotes, and measure period context.</p>
        ${periods.length ? `<p class="microcopy">Measure period${periods.length === 1 ? '' : 's'}: ${escapeHtml(periods.join(', '))}</p>` : ''}
        ${renderQualityMeasuresClaimsTable(facility)}
        <p class="subtle">Individual quality measures and summary Care Compare ratings are different CMS fields. Neither replaces PBJ staffing metrics or proves care quality by itself.</p>
      </div>
    `;
  }

  function renderQualityMeasuresClaimsSection(facility) {
    const output = document.getElementById('quality-measures-detail');
    if (!output) return;
    output.innerHTML = renderQualityMeasuresClaimsContext(facility) || '<div class="notice warning">CMS claims-based quality measures are not available for this facility in the current export.</div>';
  }

  function renderOwnershipContextSection(facility) {
    const output = document.getElementById('ownership-detail');
    if (!output) return;
    output.innerHTML = renderOwnershipContext(facility) || '<div class="notice warning">CMS SNF Enrollment ownership / affiliation fields are not available for this facility in the current export.</div>';
  }

  function renderPrintReportContext(facility) {
    const output = document.getElementById('print-report-context');
    if (!output || !facility) return;
    const current = facility.currentRow;
    const metrics = current?.metrics || {};
    const benchmark = current?.benchmarks || {};
    const generatedAt = dataset?.generated_at || 'Not available';
    const quarterLabel = current?.quarter_label || dataset?.reporting_period?.label || 'Not available';
    const benchmarkComparison = getBenchmarkComparison(metrics.total_nurse_hprd, benchmark.case_mix_total_nurse_hprd);
    const ratingRows = renderCareCompareRatingItems(facility);
    const qualityMeasures = Array.isArray(facility.qualityMeasuresClaims) ? facility.qualityMeasuresClaims : [];
    const qualityMeasurePeriods = [...new Set(qualityMeasures.map(measure => measure.measure_period).filter(Boolean))];
    output.innerHTML = `
      <h1>Connecticut Facility Staffing Summary</h1>
      <dl class="staffing-summary-list">
        <div><dt>Facility</dt><dd>${escapeHtml(facility.name)}</dd></div>
        <div><dt>CCN</dt><dd>${escapeHtml(facility.ccn || 'Not available')}</dd></div>
        <div><dt>City/state</dt><dd>${escapeHtml(facility.city)}, ${escapeHtml(facility.state)}</dd></div>
        <div><dt>Latest quarter</dt><dd>${escapeHtml(quarterLabel)}</dd></div>
        <div><dt>Export generated</dt><dd>${escapeHtml(generatedAt)}</dd></div>
      </dl>
      ${ratingRows ? `
        <h2>CMS Care Compare Rating Context</h2>
        <div class="care-compare-rating-grid print-rating-grid">${ratingRows}</div>
      ` : ''}
      ${qualityMeasures.length ? `
        <h2>CMS Claims-Based Quality Measures</h2>
        <div class="notice">
          ${qualityMeasures.length} claims-based quality measure${qualityMeasures.length === 1 ? '' : 's'} imported from CMS Quality Measures Claims${qualityMeasurePeriods.length ? ` for ${escapeHtml(qualityMeasurePeriods.join(', '))}` : ''}. These are contextual CMS measures, not calculated by this staffing tool.
        </div>
        ${renderQualityMeasuresClaimsTable(facility)}
      ` : ''}
      <div class="notice">
        Latest-quarter snapshot: total nurse HPRD ${formatHprd(metrics.total_nurse_hprd)}, RN HPRD ${formatHprd(metrics.rn_hprd)}, LPN/LVN HPRD ${formatHprd(metrics.lpn_lvn_hprd)}, nurse aide HPRD ${formatHprd(metrics.nurse_aide_hprd)}, contract staff ${formatPercent(metrics.contract_staff_pct)}.
        ${benchmarkComparison ? escapeHtml(benchmarkComparison) : 'Case-mix comparison is not available for this facility-quarter.'}
      </div>
      <div class="notice">
        PBJ staffing metrics are screening-level quarterly data. Connecticut direct-care comparison values are PBJ-derived estimates, not formal DPH compliance findings. ${escapeHtml(caseMixBenchmarkExplanation)} Provider Information benchmark timing may not align exactly with every historical PBJ quarter. Staffing data alone do not prove care quality, neglect, harm, or regulatory violations. Ownership and affiliation context is informational and does not itself prove common day-to-day control.
      </div>
    `;
  }

  function renderExhibitHelp() {
    const output = document.getElementById('exhibit-help');
    if (!output) return;
    const quarters = [...new Set((dataset?.facility_quarterly_staffing || []).map(row => row.quarter_label || row.quarter).filter(Boolean))];
    if (quarters.length > 1) {
      output.textContent = `Compare reported staffing across ${quarters.length} quarters in this static export: ${quarters.join(', ')}.`;
    } else if (quarters.length === 1) {
      output.textContent = `This export currently includes ${quarters[0]}. Additional quarters will appear after more PBJ files are added.`;
    }
  }

  function renderFacilitySummary(facility) {
    const current = facility.currentRow;
    const quarterLabel = current?.quarter_label || dataset?.reporting_period?.label || 'Not available';
    const metadataRows = [
      `<div><dt>CCN</dt><dd>${escapeHtml(facility.ccn || 'Not available')}</dd></div>`,
      `<div><dt>Latest quarter</dt><dd>${escapeHtml(quarterLabel)}</dd></div>`
    ];
    if (isUsableNumber(facility.certifiedBeds)) {
      metadataRows.push(`<div><dt>Certified beds</dt><dd>${formatCount(facility.certifiedBeds)}</dd></div>`);
    }
    if (facility.ownershipType) {
      metadataRows.push(`<div><dt>Ownership</dt><dd>${escapeHtml(facility.ownershipType)}</dd></div>`);
    }
    if (facility.affiliationEntityName) {
      metadataRows.push(`<div><dt>Affiliation entity</dt><dd>${escapeHtml(facility.affiliationEntityName)}</dd></div>`);
    }

    document.getElementById('facility-summary').innerHTML = `
      <div class="ltcop-provider-banner">
        <div class="eyebrow">Selected Facility</div>
        <div class="ltcop-provider-heading">
          <h2>${escapeHtml(facility.name)}</h2>
          <p class="subtle">${facility.address ? `${escapeHtml(facility.address)} - ` : ''}${escapeHtml(facility.city)}, ${escapeHtml(facility.state)}</p>
        </div>
        ${renderScreeningIndicators(facility)}
      </div>
      <dl class="staffing-summary-list ltcop-provider-meta">
        ${metadataRows.join('')}
      </dl>
    `;
  }

  function renderScreeningIndicators(facility) {
    const current = facility.currentRow;
    const metrics = current?.metrics || {};
    const benchmark = current?.benchmarks || {};
    const badges = [];
    if (metrics.ct_total_direct_care_below_minimum_estimate === true) {
      badges.push({
        type: 'attention',
        text: 'Below CT 3.00 direct-care comparison point',
        label: 'Screening indicator: latest quarter below CT 3.00 direct-care comparison point.'
      });
    }
    if (metrics.ct_licensed_direct_care_below_minimum_estimate === true) {
      badges.push({
        type: 'attention',
        text: 'Below CT 0.84 licensed comparison point',
        label: 'Screening indicator: latest quarter below CT 0.84 licensed comparison point.'
      });
    }
    const benchmarkValue = benchmark.case_mix_total_nurse_hprd;
    if (isUsableNumber(metrics.total_nurse_hprd) && isUsableNumber(benchmarkValue) && Number(metrics.total_nurse_hprd) < Number(benchmarkValue)) {
      badges.push({
        type: 'context',
        text: 'Actual below case-mix comparison point',
        label: 'Screening indicator: PBJ-reported actual total nurse HPRD is below the CMS case-mix comparison point.'
      });
    }
    const availableRows = facility.historyRows.filter(row => row.metrics);
    const repeatedBelowCount = availableRows.filter(row => row.metrics?.ct_total_direct_care_below_minimum_estimate === true).length;
    if (repeatedBelowCount >= 2) {
      badges.push({
        type: 'attention',
        text: `Repeated pattern: below CT 3.00 in ${repeatedBelowCount} of ${availableRows.length} quarters`,
        label: `Screening indicator: below CT 3.00 direct-care comparison point in ${repeatedBelowCount} of ${availableRows.length} available quarters.`
      });
    }
    if (isUsableNumber(metrics.contract_staff_pct) && Number(metrics.contract_staff_pct) >= 10) {
      badges.push({
        type: 'context',
        text: 'Contract staffing at/above 10% in latest quarter',
        label: 'Descriptive context: contract staffing was at or above 10 percent in the latest quarter.'
      });
    }
    if (!badges.length) {
      badges.push({
        type: 'neutral',
        text: 'No selected screening indicator triggered in latest view',
        label: 'No selected screening indicator triggered in the latest facility view.'
      });
    }
    return `
      <div class="screening-badge-row" aria-label="Selected facility screening indicators">
        ${badges.map(badge => `<span class="screening-badge ${escapeHtml(badge.type)}" aria-label="${escapeHtml(badge.label)}">${escapeHtml(badge.text)}</span>`).join('')}
      </div>
      <p class="screening-note">Screening indicators identify questions for review and are not formal compliance findings.</p>
    `;
  }

  function renderOwnershipContext(facility) {
    const rows = [];
    const affiliationUrl = getAffiliationExplorerUrl(facility);
    if (facility.enrollmentOrganizationName) {
      rows.push(`<div><dt>Legal organization</dt><dd>${escapeHtml(facility.enrollmentOrganizationName)}</dd></div>`);
    }
    if (facility.enrollmentDoingBusinessAsName) {
      rows.push(`<div><dt>DBA name</dt><dd>${escapeHtml(facility.enrollmentDoingBusinessAsName)}</dd></div>`);
    }
    if (facility.affiliationEntityName) {
      rows.push(`<div><dt>Affiliation entity</dt><dd>${escapeHtml(facility.affiliationEntityName)}</dd></div>`);
    }
    const structureParts = [facility.enrollmentProprietaryNonprofit, facility.enrollmentOrganizationTypeStructure].filter(Boolean);
    if (structureParts.length) {
      rows.push(`<div><dt>Enrollment type</dt><dd>${escapeHtml(structureParts.join(' - '))}</dd></div>`);
    }
    if (!rows.length) return '';
    return `
      <div class="ownership-context">
        <h3>Ownership / affiliation context</h3>
        <dl>${rows.join('')}</dl>
        <p class="subtle">Enrollment fields add legal organization and affiliation context; they do not replace Provider Information facility details.</p>
        ${affiliationUrl ? `<p><a class="linkBtn" href="${escapeHtml(affiliationUrl)}">View affiliation staffing summary</a></p>` : ''}
      </div>
    `;
  }

  function getAffiliationExplorerUrl(facility) {
    const affiliationValue = facility.affiliationEntityId || facility.affiliationEntityName;
    if (!affiliationValue) return '';
    return `nursing-home-ownership-staffing-explorer.html?affiliation=${encodeURIComponent(affiliationValue)}`;
  }

  function renderMetricCards(facility) {
    const current = facility.currentRow;
    const metrics = current?.metrics || {};
    const metricCards = metricDefinitions.map(metric => `
      <article class="staffing-metric card">
        <div class="summary-label">${escapeHtml(metric.label)}</div>
        <strong>${escapeHtml(metric.format(metrics[metric.key]))}</strong>
        <p class="subtle">${escapeHtml(metric.help)}</p>
      </article>
    `);
    const benchmark = current?.benchmarks || {};
    if (benchmark.case_mix_benchmark_available) {
      const comparison = getBenchmarkComparison(metrics.total_nurse_hprd, benchmark.case_mix_total_nurse_hprd);
      metricCards.push(`
        <article class="staffing-metric card">
          <div class="summary-label">Case-mix comparison point</div>
          <strong>${formatHprd(benchmark.case_mix_total_nurse_hprd)}</strong>
          <p class="subtle">${escapeHtml(caseMixBenchmarkExplanation)}</p>
          ${comparison ? `<div class="comparison-note">${escapeHtml(comparison)}</div>` : ''}
        </article>
      `);
    }
    metricCards.push(renderCtDirectCareComparison(metrics));

    document.getElementById('metric-cards').innerHTML = metricCards.join('');
    renderBenchmarkExplainer(Boolean(benchmark.case_mix_benchmark_available));
  }

  function renderCtDirectCareComparison(metrics) {
    const totalMinimum = isUsableNumber(metrics.ct_total_direct_care_minimum_hprd)
      ? Number(metrics.ct_total_direct_care_minimum_hprd)
      : 3.00;
    const licensedMinimum = isUsableNumber(metrics.ct_licensed_direct_care_minimum_hprd)
      ? Number(metrics.ct_licensed_direct_care_minimum_hprd)
      : 0.84;
    return `
      <article class="staffing-metric ct-comparison-card card">
        <div>
          <div class="summary-label">Connecticut Direct-Care Staffing Comparison</div>
          <h3>PBJ-derived screening estimate</h3>
          <p class="subtle">Connecticut regulations establish direct-care staffing minimums of 3.00 total HPRD and 0.84 licensed nursing HPRD. This estimate excludes nursing administration / DON-style hours and is not a formal DPH compliance finding.</p>
        </div>
        <div class="ct-comparison-grid">
          <div>
            <div class="summary-label">CT direct-care HPRD estimate</div>
            <strong>${formatHprd(metrics.ct_direct_care_total_hprd_estimate)}</strong>
            <p class="subtle">Comparison to ${totalMinimum.toFixed(2)} HPRD: ${formatSignedHprd(metrics.ct_total_direct_care_difference_from_minimum)}.</p>
            <div class="comparison-note">${escapeHtml(getCtTotalStatus(metrics))}</div>
          </div>
          <div>
            <div class="summary-label">CT licensed HPRD estimate</div>
            <strong>${formatHprd(metrics.ct_direct_care_licensed_nurse_hprd_estimate)}</strong>
            <p class="subtle">Comparison to ${licensedMinimum.toFixed(2)} HPRD: ${formatSignedHprd(metrics.ct_licensed_direct_care_difference_from_minimum)}.</p>
            <div class="comparison-note">${escapeHtml(getCtLicensedStatus(metrics))}</div>
          </div>
        </div>
      </article>
    `;
  }

  function renderBenchmarkExplainer(shouldShow) {
    const output = document.getElementById('benchmark-explainer');
    if (!output) return;
    output.style.display = shouldShow ? 'block' : 'none';
  }

  function getBenchmarkComparison(actualValue, benchmarkValue) {
    if (!isUsableNumber(actualValue) || !isUsableNumber(benchmarkValue) || Number(benchmarkValue) <= 0) {
      return '';
    }
    const actual = Number(actualValue);
    const benchmark = Number(benchmarkValue);
    const difference = actual - benchmark;
    const percent = (actual / benchmark) * 100;
    const direction = difference >= 0 ? 'above' : 'below';
    return `Actual total nurse HPRD is ${formatSignedHprd(difference)} ${direction} this benchmark, or ${percent.toFixed(0)}% of the benchmark.`;
  }

  function renderTrendChart(displayRows) {
    const availableRows = displayRows.filter(displayRow => displayRow.sourceRow);
    if (availableRows.length < 2) return '';
    const totalValues = availableRows
      .map(displayRow => Number(displayRow.sourceRow.metrics?.total_nurse_hprd))
      .filter(Number.isFinite);
    const directValues = availableRows
      .map(displayRow => Number(displayRow.sourceRow.metrics?.ct_direct_care_total_hprd_estimate))
      .filter(Number.isFinite);
    const values = [...totalValues, ...directValues, 3.00].filter(Number.isFinite);
    if (!values.length) return '';
    const width = 760;
    const height = 260;
    const left = 46;
    const right = 22;
    const top = 18;
    const bottom = 52;
    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;
    const maxValue = Math.max(4, Math.ceil(Math.max(...values) * 10) / 10);
    const minValue = 0;
    const xForIndex = index => left + (availableRows.length === 1 ? plotWidth / 2 : (plotWidth * index) / (availableRows.length - 1));
    const yForValue = value => top + plotHeight - ((Number(value) - minValue) / (maxValue - minValue)) * plotHeight;
    const lineForMetric = metricKey => availableRows
      .map((displayRow, index) => {
        const value = displayRow.sourceRow.metrics?.[metricKey];
        if (!isUsableNumber(value)) return null;
        return `${xForIndex(index).toFixed(1)},${yForValue(Number(value)).toFixed(1)}`;
      })
      .filter(Boolean)
      .join(' ');
    const directLine = lineForMetric('ct_direct_care_total_hprd_estimate');
    const totalLine = lineForMetric('total_nurse_hprd');
    const referenceY = yForValue(3.00).toFixed(1);
    const xLabels = availableRows.map((displayRow, index) => `
      <text x="${xForIndex(index).toFixed(1)}" y="${height - 24}" text-anchor="middle">${escapeHtml(displayRow.quarter_label || displayRow.quarter)}</text>
    `).join('');
    return `
      <div class="ltcop-trend-chart" role="img" aria-label="Line chart showing CT direct-care HPRD estimate and total nurse HPRD across available quarters, with a CT 3.00 comparison reference line. Missing quarters are not plotted as zero.">
        <svg viewBox="0 0 ${width} ${height}" focusable="false" aria-hidden="true">
          <line x1="${left}" y1="${referenceY}" x2="${width - right}" y2="${referenceY}" class="chart-line-reference" stroke-width="2"></line>
          ${totalLine ? `<polyline points="${totalLine}" fill="none" class="chart-line-total" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>` : ''}
          ${directLine ? `<polyline points="${directLine}" fill="none" class="chart-line-direct" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>` : ''}
          <line x1="${left}" y1="${top}" x2="${left}" y2="${height - bottom}" stroke="#cbd5e1"></line>
          <line x1="${left}" y1="${height - bottom}" x2="${width - right}" y2="${height - bottom}" stroke="#cbd5e1"></line>
          <text x="${left - 10}" y="${yForValue(maxValue).toFixed(1)}" text-anchor="end">${maxValue.toFixed(1)}</text>
          <text x="${left - 10}" y="${referenceY}" text-anchor="end">3.0</text>
          <text x="${left - 10}" y="${height - bottom}" text-anchor="end">0</text>
          ${xLabels}
        </svg>
        <div class="chart-legend">
          <span class="direct">CT direct-care HPRD estimate</span>
          <span class="total">Total nurse HPRD</span>
          <span>CT 3.00 comparison point</span>
        </div>
        <p class="microcopy">The chart plots only available PBJ facility-quarter rows; missing quarters are not treated as zero.</p>
      </div>
    `;
  }

  function renderQuarterlyTable(facility) {
    const output = document.getElementById('quarterly-exhibit');
    const datasetQuarters = getDatasetQuarters();
    if (!facility.historyRows.length && !datasetQuarters.length) {
      output.innerHTML = '<div class="notice warning">No quarterly history rows are available for this facility in the current static export.</div>';
      return;
    }

    const rowsByQuarter = new Map(facility.historyRows.map(row => [row.quarter, row]));
    const displayRows = datasetQuarters.length
      ? datasetQuarters.map(quarter => ({
          quarter: quarter.quarter,
          quarter_label: quarter.label,
          sourceRow: rowsByQuarter.get(quarter.quarter) || null
        }))
      : facility.historyRows.map(row => ({
          quarter: row.quarter,
          quarter_label: row.quarter_label || row.quarter,
          sourceRow: row
        }));
    const missingCount = displayRows.filter(row => !row.sourceRow).length;
    const hprdValues = facility.historyRows
      .map(row => row.metrics?.total_nurse_hprd)
      .filter(isUsableNumber)
      .map(Number);
    const maxHprd = Math.max(...hprdValues, 1);

    output.innerHTML = `
      ${renderTrendChart(displayRows)}
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
            ${displayRows.map(displayRow => {
              const row = displayRow.sourceRow;
              if (!row) {
                return `
                  <tr class="missing-quarter-row">
                    <th scope="row">${escapeHtml(displayRow.quarter_label || displayRow.quarter || 'Quarter unavailable')}</th>
                    <td colspan="5">No PBJ row available</td>
                  </tr>
                `;
              }
              const totalHprd = row.metrics?.total_nurse_hprd;
              const width = isUsableNumber(totalHprd) ? Math.max(8, Math.round((Number(totalHprd) / maxHprd) * 100)) : 0;
              return `
                <tr>
                  <th scope="row">${escapeHtml(row.quarter_label || row.quarter || 'Quarter unavailable')}</th>
                  <td>
                    ${width ? `<div class="staffing-bar" aria-hidden="true"><span style="width:${width}%"></span></div>` : ''}
                    <span>${formatHprd(totalHprd)}</span>
                  </td>
                  <td>${formatHprd(row.metrics?.rn_hprd)}</td>
                  <td>${formatHprd(row.metrics?.nurse_aide_hprd)}</td>
                  <td>${formatPercent(row.metrics?.contract_staff_pct)}</td>
                  <td>${formatCount(row.average_resident_census)}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
      ${missingCount ? `<div class="notice missing-quarter-note">This facility is missing ${missingCount} quarter${missingCount === 1 ? '' : 's'} in the uploaded PBJ source files. Missing quarters are shown so the trend does not look continuous when a facility-quarter row is absent.</div>` : ''}
    `;
  }

  function getDisplayedQuarterRows(facility) {
    const datasetQuarters = getDatasetQuarters();
    const rowsByQuarter = new Map(facility.historyRows.map(row => [row.quarter, row]));
    return datasetQuarters.length
      ? datasetQuarters.map(quarter => ({
          quarter: quarter.quarter,
          quarter_label: quarter.label,
          sourceRow: rowsByQuarter.get(quarter.quarter) || null
        }))
      : facility.historyRows.map(row => ({
          quarter: row.quarter,
          quarter_label: row.quarter_label || row.quarter,
          sourceRow: row
        }));
  }

  function buildFacilityTrendCsv(facility) {
    const headers = [
      'facility_name',
      'ccn',
      'city',
      'cms_overall_rating',
      'cms_health_inspection_rating',
      'cms_staffing_rating',
      'cms_rn_staffing_rating',
      'cms_qm_rating',
      'cms_long_stay_qm_rating',
      'cms_short_stay_qm_rating',
      'cms_rating_source',
      'quarter',
      'row_status',
      'resident_days',
      'average_resident_census',
      'total_nurse_hprd',
      'rn_hprd',
      'lpn_lvn_hprd',
      'nurse_aide_hprd',
      'contract_staff_pct',
      'case_mix_total_nurse_benchmark',
      'actual_minus_case_mix_benchmark',
      'ct_direct_care_total_hprd_estimate',
      'below_ct_3_00_comparison_flag',
      'ct_direct_care_licensed_nurse_hprd_estimate',
      'below_ct_0_84_comparison_flag',
      'input_daily_row_count',
      'included_daily_row_count',
      'excluded_zero_census_day_count',
      'included_zero_nursing_hours_day_count'
    ];
    const rows = getDisplayedQuarterRows(facility).map(displayRow => {
      const row = displayRow.sourceRow;
      const metrics = row?.metrics || {};
      const benchmark = row?.benchmarks || {};
      const quality = row?.data_quality || {};
      const actual = metrics.total_nurse_hprd;
      const benchmarkValue = benchmark.case_mix_total_nurse_hprd;
      const difference = isUsableNumber(actual) && isUsableNumber(benchmarkValue) ? Number(actual) - Number(benchmarkValue) : null;
      return {
        facility_name: facility.name,
        ccn: facility.ccn || '',
        city: facility.city || '',
        cms_overall_rating: csvValue(facility.cmsOverallRating),
        cms_health_inspection_rating: csvValue(facility.cmsHealthInspectionRating),
        cms_staffing_rating: csvValue(facility.cmsStaffingRating),
        cms_rn_staffing_rating: csvValue(facility.cmsRnStaffingRating),
        cms_qm_rating: csvValue(facility.cmsQmRating),
        cms_long_stay_qm_rating: csvValue(facility.cmsLongStayQmRating),
        cms_short_stay_qm_rating: csvValue(facility.cmsShortStayQmRating),
        cms_rating_source: facility.cmsRatingSource || '',
        quarter: displayRow.quarter || '',
        row_status: row ? 'PBJ row available' : 'No PBJ row available',
        resident_days: row ? csvOneDecimal(row.resident_days) : '',
        average_resident_census: row ? csvOneDecimal(row.average_resident_census) : '',
        total_nurse_hprd: csvNumber(metrics.total_nurse_hprd),
        rn_hprd: csvNumber(metrics.rn_hprd),
        lpn_lvn_hprd: csvNumber(metrics.lpn_lvn_hprd),
        nurse_aide_hprd: csvNumber(metrics.nurse_aide_hprd),
        contract_staff_pct: csvOneDecimal(metrics.contract_staff_pct),
        case_mix_total_nurse_benchmark: csvNumber(benchmarkValue),
        actual_minus_case_mix_benchmark: csvNumber(difference),
        ct_direct_care_total_hprd_estimate: csvNumber(metrics.ct_direct_care_total_hprd_estimate),
        below_ct_3_00_comparison_flag: metrics.ct_total_direct_care_below_minimum_estimate,
        ct_direct_care_licensed_nurse_hprd_estimate: csvNumber(metrics.ct_direct_care_licensed_nurse_hprd_estimate),
        below_ct_0_84_comparison_flag: metrics.ct_licensed_direct_care_below_minimum_estimate,
        input_daily_row_count: row ? quality.input_daily_row_count : '',
        included_daily_row_count: row ? quality.included_daily_row_count : '',
        excluded_zero_census_day_count: row ? quality.excluded_zero_census_day_count : '',
        included_zero_nursing_hours_day_count: row ? quality.included_zero_nursing_hours_day_count : ''
      };
    });
    return buildCsv(headers, rows);
  }

  function getFacilityTrendCsvFilename(facility) {
    const latest = dataset?.reporting_period?.quarter || facility.currentRow?.quarter || 'latest';
    return `facility-staffing-trend-${safeFilenamePart(facility.name)}-${safeFilenamePart(facility.ccn)}-${safeFilenamePart(latest)}.csv`;
  }

  function handlePrintFacilitySummary() {
    const facility = getSelectedFacility();
    if (!facility) {
      setReportActionStatus('Select a valid facility before printing.');
      return;
    }
    renderPrintReportContext(facility);
    global.print();
  }

  function handleDownloadFacilityTrendCsv() {
    const facility = getSelectedFacility();
    if (!facility) {
      setReportActionStatus('Select a valid facility before downloading.');
      return;
    }
    downloadTextFile(getFacilityTrendCsvFilename(facility), buildFacilityTrendCsv(facility));
    setReportActionStatus('Facility five-quarter trend CSV prepared for the selected facility.');
  }

  function renderInterpretation(facility) {
    const interpretation = buildInterpretation(facility);

    document.getElementById('interpretation').innerHTML = `
      <article class="card">
        <h3>What this shows</h3>
        <p>${escapeHtml(interpretation.shows || fallback.shows)}</p>
      </article>
      <article class="card">
        <h3>What this may suggest</h3>
        <p>${escapeHtml(interpretation.suggests || fallback.suggests)}</p>
      </article>
      <article class="card">
        <h3>What this cannot prove</h3>
        <p>${escapeHtml(interpretation.cannot_prove || fallback.cannot_prove)}</p>
      </article>
    `;
  }

  function buildInterpretation(facility) {
    const current = facility.currentRow;
    const metrics = current?.metrics || {};
    const benchmark = current?.benchmarks || {};
    const total = formatHprd(metrics.total_nurse_hprd);
    const rn = formatHprd(metrics.rn_hprd);
    const lpn = formatHprd(metrics.lpn_lvn_hprd);
    const aide = formatHprd(metrics.nurse_aide_hprd);
    const contract = formatPercent(metrics.contract_staff_pct);
    const quarter = current?.quarter_label || dataset?.reporting_period?.label || 'the selected quarter';
    const contractSentence = isUsableNumber(metrics.contract_staff_pct)
      ? `Contract staff accounted for ${contract} of reported nursing hours.`
      : 'Contract staff percentage is not available in this export for the selected facility-quarter.';
    const benchmarkComparison = getBenchmarkComparison(metrics.total_nurse_hprd, benchmark.case_mix_total_nurse_hprd);
    const benchmarkSentence = benchmark.case_mix_benchmark_available && benchmarkComparison
      ? ` The CMS Provider Information case-mix total nurse HPRD comparison point is imported from CMS, not calculated by this tool; the comparison is calculated here: ${benchmarkComparison.toLowerCase()}`
      : benchmark.case_mix_benchmark_available
        ? ' The CMS Provider Information case-mix total nurse HPRD comparison point is available for context, but a total-nurse comparison could not be calculated from the current values.'
        : ' No CMS case-mix benchmark is available in this export for the selected facility-quarter.';
    const ctBelow = [];
    if (metrics.ct_total_direct_care_below_minimum_estimate === true) {
      ctBelow.push('below the CT 3.00 total direct-care comparison point');
    }
    if (metrics.ct_licensed_direct_care_below_minimum_estimate === true) {
      ctBelow.push('below the CT 0.84 licensed comparison point');
    }
    const ctComparisonSentence = ctBelow.length
      ? ` The separate CT direct-care screening estimate is ${ctBelow.join(' and ')}.`
      : isUsableNumber(metrics.ct_direct_care_total_hprd_estimate) || isUsableNumber(metrics.ct_direct_care_licensed_nurse_hprd_estimate)
        ? ' The separate CT direct-care screening estimate is available above and should be read as a comparison indicator, not a compliance finding.'
        : ' The separate CT direct-care screening estimate is not available for this facility-quarter.';

    return {
      shows: `${quarter} PBJ data for ${facility.name} reports ${total} total nurse HPRD: ${rn} RN HPRD, ${lpn} LPN/LVN HPRD, and ${aide} nurse aide HPRD. ${contractSentence}${benchmarkSentence}${ctComparisonSentence}`,
      suggests: 'Use these numbers as screening context for follow-up questions: whether resident experience, call-light response, missed-care concerns, turnover, weekend coverage, acuity changes, or complaint patterns point to a staffing issue worth closer review.',
      cannot_prove: 'This quarterly PBJ snapshot, CT direct-care comparison estimate, and any case-mix comparison cannot prove poor care, harm, neglect, regulatory violations, or staffing on a specific shift. They should be checked against resident accounts, care records when appropriate, survey findings, complaints, and official CMS Care Compare information.'
    };
  }

  function renderFacility(facilityId) {
    const facility = getFacilityById(facilityId);
    if (!facility) return;
    updateReportActions(facility);
    renderPrintReportContext(facility);
    renderFacilitySummary(facility);
    renderCareCompareRatingSection(facility);
    renderOwnershipContextSection(facility);
    renderQualityMeasuresClaimsSection(facility);
    renderMetricCards(facility);
    renderQuarterlyTable(facility);
    renderInterpretation(facility);
  }

  async function loadPage() {
    const status = document.getElementById('staffing-load-status');
    const select = document.getElementById('facility-select');

    try {
      if (!global.DanBeemData) throw new Error('Shared data loader did not load.');
      const data = await loadFirstAvailableJson(dataPaths);
      normalizeDataset(data);
      if (!facilities.length) throw new Error('No facilities were found in the staffing export.');

      renderDatasetSummary();
      renderExhibitHelp();
      const initialFacilityId = getFacilityIdFromUrl();
      populateFacilitySelect(filteredFacilities, initialFacilityId);
      document.getElementById('facility-filter').addEventListener('input', filterFacilities);
      select.addEventListener('change', event => renderFacility(event.target.value));
      document.getElementById('print-facility-summary')?.addEventListener('click', handlePrintFacilitySummary);
      document.getElementById('download-facility-trend-csv')?.addEventListener('click', handleDownloadFacilityTrendCsv);
      renderFacility(initialFacilityId);
      renderSourceStatus();
    } catch (err) {
      status.textContent = `Staffing explorer data could not be loaded. Details: ${err.message}`;
      status.className = 'notice error';
      select.disabled = true;
    }
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

  document.addEventListener('DOMContentLoaded', loadPage);
})(window);
