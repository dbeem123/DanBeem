(function () {
  'use strict';

  const MONTHS = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
  ];

  function parseSnapshotLabel(value) {
    const text = String(value || '');
    const compact = text.match(/(?:^|[^A-Za-z])(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[_ -]?(20\d{2})\b/i);
    if (compact) {
      const monthPrefix = compact[1].toLowerCase().slice(0, 3);
      const monthIndex = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'].indexOf(monthPrefix);
      return monthIndex >= 0 ? `${MONTHS[monthIndex]} ${compact[2]}` : compact[0];
    }
    const dotted = text.match(/\b(20\d{2})[._-](0?[1-9]|1[0-2])(?:[._-]\d{1,2})?\b/);
    if (dotted) {
      return `${MONTHS[Number(dotted[2]) - 1]} ${dotted[1]}`;
    }
    return '';
  }

  function formatGeneratedDate(value) {
    if (!value) return '';
    const parsed = new Date(String(value).replace(' ', 'T'));
    if (Number.isNaN(parsed.getTime())) return String(value);
    return parsed.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  function sourceByName(dataset, pattern) {
    const regex = pattern instanceof RegExp ? pattern : new RegExp(pattern, 'i');
    return (dataset?.sources || []).find(source => regex.test(source?.source_dataset_name || '')) || null;
  }

  function getSourceSnapshot(dataset, pattern, fallbackLabel) {
    const source = sourceByName(dataset, pattern);
    return parseSnapshotLabel(source?.source_release) || fallbackLabel || '';
  }

  function buildCurrencyParts(dataset) {
    const pbjLabel = dataset?.reporting_period?.label || dataset?.reporting_period?.quarter || 'the latest included quarter';
    const providerSnapshot = getSourceSnapshot(dataset, /Provider Information/i, 'April 2026');
    const qmSnapshot = getSourceSnapshot(dataset, /Quality Measures Claims/i, 'April 2026');
    const snfSnapshot = getSourceSnapshot(dataset, /Skilled Nursing Facility Enrollments|SNF Enrollments/i, 'May 2026');
    const generatedDate = formatGeneratedDate(dataset?.generated_at);
    return {
      pbjLabel,
      providerSnapshot,
      qmSnapshot,
      snfSnapshot,
      generatedDate
    };
  }

  function formatQuarterLabel(quarter) {
    const text = String(quarter || '');
    const match = text.match(/^(20\d{2})Q([1-4])$/);
    return match ? `Q${match[2]} ${match[1]}` : text;
  }

  function buildCurrencySummary(dataset) {
    if (dataset?.dataset_type === 'nursing_home_staffing_history_pbj_only' || dataset?.history_window) {
      const window = dataset?.history_window || {};
      const first = formatQuarterLabel(window.first_quarter || window.quarters?.[0] || '');
      const latest = formatQuarterLabel(window.latest_quarter || window.quarters?.[window.quarters.length - 1] || '');
      const generatedDate = formatGeneratedDate(dataset?.generated_at);
      const generated = generatedDate ? ` Export generated ${generatedDate}.` : '';
      return `Historical CMS PBJ staffing is available from ${first || 'the first included quarter'} through ${latest || 'the latest included quarter'}. Current contextual CMS snapshots, including ratings, quality measures, case-mix comparison points, and affiliation context, are not historical quarter-specific values.${generated}`;
    }
    const parts = buildCurrencyParts(dataset);
    const snapshots = [
      parts.providerSnapshot ? `Provider Information (${parts.providerSnapshot})` : 'Provider Information',
      parts.qmSnapshot ? `Quality Measures Claims (${parts.qmSnapshot})` : 'Quality Measures Claims',
      parts.snfSnapshot ? `SNF Enrollments (${parts.snfSnapshot})` : 'SNF Enrollments'
    ];
    const generated = parts.generatedDate ? ` Export generated ${parts.generatedDate}.` : '';
    return `Staffing data current through CMS PBJ ${parts.pbjLabel}. Contextual CMS snapshots include ${snapshots.join(', ')}.${generated}`;
  }

  function renderCurrencyElement(element, dataset) {
    const summary = buildCurrencySummary(dataset);
    const methodologyHref = element.getAttribute('data-methodology-href') || 'nursing-home-staffing-methodology.html';
    element.classList.add('source-currency-card');
    element.innerHTML = `
      <div class="source-currency-kicker">Data currency</div>
      <p>${escapeHtml(summary)}</p>
      <p class="source-currency-link"><a href="${escapeHtml(methodologyHref)}">About the data and methodology</a></p>
    `;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[character]));
  }

  async function loadDataset(path) {
    const response = await fetch(path, { cache: 'no-store' });
    if (!response.ok) throw new Error(`Could not load ${path}: ${response.status}`);
    return response.json();
  }

  async function renderAllCurrencyElements() {
    const elements = Array.from(document.querySelectorAll('[data-source-currency]'));
    if (!elements.length) return;
    const groups = new Map();
    elements.forEach(element => {
      const path = element.getAttribute('data-source-json') || '../data/nursing_home_staffing_ct.json';
      if (!groups.has(path)) groups.set(path, []);
      groups.get(path).push(element);
    });
    await Promise.all(Array.from(groups.entries()).map(async ([path, groupElements]) => {
      try {
        const dataset = await loadDataset(path);
        groupElements.forEach(element => renderCurrencyElement(element, dataset));
      } catch (error) {
        groupElements.forEach(element => {
          element.classList.add('source-currency-card');
          element.textContent = 'Data currency details could not be loaded. Use the methodology page and source notes for current source context.';
        });
      }
    }));
  }

  window.NursingHomeSourceCurrency = {
    buildCurrencyParts,
    buildCurrencySummary,
    renderAllCurrencyElements
  };

  document.addEventListener('DOMContentLoaded', renderAllCurrencyElements);
}());
