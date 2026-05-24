(function () {
  const DATA_URL = "../../data/testing/nursing_home_staffing_history_ct_2017q4_2025q4_preview.json";
  const CT_TOTAL = 3.0;
  const CT_LICENSED = 0.84;
  const FULL_QUARTER_APPLICABLE = "2023Q2";
  const PARTIAL_QUARTER = "2023Q1";

  const state = {
    rows: [],
    quarters: [],
    byCcn: new Map(),
    facilities: [],
    facilityWindow: "latest8",
  };

  const $ = (id) => document.getElementById(id);

  function quarterSort(a, b) {
    const ay = Number(a.slice(0, 4));
    const aq = Number(a.slice(-1));
    const by = Number(b.slice(0, 4));
    const bq = Number(b.slice(-1));
    return ay === by ? aq - bq : ay - by;
  }

  function formatNumber(value, digits = 2) {
    return Number.isFinite(value) ? value.toFixed(digits) : "Not available";
  }

  function formatPct(value) {
    return Number.isFinite(value) ? `${value.toFixed(1)}%` : "Not available";
  }

  function ctApplicability(quarter) {
    if (quarterSort(quarter, FULL_QUARTER_APPLICABLE) >= 0) {
      return "applicable";
    }
    if (quarter === PARTIAL_QUARTER) {
      return "partial";
    }
    return "reference";
  }

  function ctStatus(row, kind) {
    const applicability = ctApplicability(row.quarter);
    const metrics = row.metrics || {};
    const value = kind === "licensed"
      ? metrics.ct_direct_care_licensed_nurse_hprd_estimate
      : metrics.ct_direct_care_total_hprd_estimate;
    const point = kind === "licensed" ? CT_LICENSED : CT_TOTAL;
    if (!Number.isFinite(value)) return "Not available";
    if (applicability === "reference") return `Reference only: ${formatNumber(value)} vs ${formatNumber(point)}`;
    if (applicability === "partial") return `Partial-period context: ${formatNumber(value)} vs ${formatNumber(point)}`;
    return value < point ? `Below ${formatNumber(point)}` : `At/above ${formatNumber(point)}`;
  }

  function selectedWindowQuarters(windowName) {
    if (windowName === "full") return state.quarters;
    const count = windowName === "latest4" ? 4 : 8;
    return state.quarters.slice(Math.max(0, state.quarters.length - count));
  }

  function facilityLabel(facility) {
    return `${facility.name || facility.ccn} (${facility.city || "Unknown city"}, ${facility.ccn})`;
  }

  function metricCard(label, value, note) {
    return `<div class="metric-card"><span>${label}</span><strong>${value}</strong><small>${note || ""}</small></div>`;
  }

  function renderFacilityOptions() {
    const search = $("facility-search").value.trim().toLowerCase();
    const matches = state.facilities
      .filter((facility) => {
        const haystack = `${facility.ccn} ${facility.name || ""} ${facility.city || ""}`.toLowerCase();
        return !search || haystack.includes(search);
      })
      .slice(0, 80);

    $("facility-select").innerHTML = matches
      .map((facility) => `<option value="${facility.ccn}">${facilityLabel(facility)}</option>`)
      .join("");
    renderFacility();
  }

  function renderFacilityChart(rows) {
    const host = $("facility-history-chart");
    if (!rows.length) {
      host.innerHTML = "";
      return;
    }
    const values = rows
      .map((row) => row.metrics && row.metrics.ct_direct_care_total_hprd_estimate)
      .filter(Number.isFinite);
    const max = Math.max(CT_TOTAL, ...values, 1);
    const width = 760;
    const height = 220;
    const pad = 34;
    const xStep = rows.length > 1 ? (width - pad * 2) / (rows.length - 1) : 0;
    const y = (value) => height - pad - (value / max) * (height - pad * 2);
    const points = rows.map((row, index) => {
      const value = row.metrics && row.metrics.ct_direct_care_total_hprd_estimate;
      return Number.isFinite(value) ? `${pad + index * xStep},${y(value)}` : null;
    }).filter(Boolean);
    const refY = y(CT_TOTAL);
    host.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="CT direct-care HPRD trend for selected facility">
        <line x1="${pad}" y1="${refY}" x2="${width - pad}" y2="${refY}" stroke="#b4232a" stroke-dasharray="6 6" />
        <text x="${pad}" y="${Math.max(14, refY - 8)}" fill="#702024">3.00 reference</text>
        <polyline points="${points.join(" ")}" fill="none" stroke="#173761" stroke-width="4" stroke-linejoin="round" stroke-linecap="round" />
      </svg>
    `;
  }

  function renderFacility() {
    const ccn = $("facility-select").value || (state.facilities[0] && state.facilities[0].ccn);
    const rows = (state.byCcn.get(ccn) || []).slice();
    const windowQuarters = selectedWindowQuarters(state.facilityWindow);
    const shown = rows.filter((row) => windowQuarters.includes(row.quarter));
    const latest = rows[rows.length - 1];
    $("facility-window-note").textContent = shown.length
      ? `Showing ${shown[0].quarter} through ${shown[shown.length - 1].quarter}. ${state.facilityWindow === "full" ? "Full PBJ history preview." : "Recent-window preview."}`
      : "No rows are available for the selected facility/window.";
    $("facility-history-summary").innerHTML = latest ? [
      metricCard("Latest quarter", latest.quarter, latest.provider_name_from_pbj || ccn),
      metricCard("Latest CT direct-care HPRD", formatNumber(latest.metrics.ct_direct_care_total_hprd_estimate), ctStatus(latest, "total")),
      metricCard("Latest RN HPRD", formatNumber(latest.metrics.rn_hprd), "PBJ-derived"),
      metricCard("Quarters available", rows.length, "Missing quarters are not treated as zero"),
    ].join("") : "";
    $("facility-history-body").innerHTML = shown.map((row) => `
      <tr>
        <td>${row.quarter}</td>
        <td>${formatNumber(row.metrics.ct_direct_care_total_hprd_estimate)}</td>
        <td>${ctStatus(row, "total")}</td>
        <td>${formatNumber(row.metrics.rn_hprd)}</td>
        <td>${formatNumber(row.metrics.total_nurse_hprd)}</td>
        <td>${formatPct(row.metrics.contract_staff_pct)}</td>
      </tr>
    `).join("");
    renderFacilityChart(shown);
  }

  function syncChangePreset() {
    const preset = $("change-preset").value;
    if (preset !== "custom") {
      const quarters = selectedWindowQuarters(preset === "full" ? "full" : preset);
      $("change-start").value = quarters[0];
      $("change-end").value = quarters[quarters.length - 1];
    }
    renderChange();
  }

  function renderChange() {
    const start = $("change-start").value;
    const end = $("change-end").value;
    const changes = [];
    for (const facility of state.facilities) {
      const rows = state.byCcn.get(facility.ccn) || [];
      const byQuarter = new Map(rows.map((row) => [row.quarter, row]));
      const a = byQuarter.get(start);
      const b = byQuarter.get(end);
      if (!a || !b) continue;
      const av = a.metrics.ct_direct_care_total_hprd_estimate;
      const bv = b.metrics.ct_direct_care_total_hprd_estimate;
      if (!Number.isFinite(av) || !Number.isFinite(bv)) continue;
      changes.push({ facility, start: av, end: bv, change: bv - av });
    }
    changes.sort((a, b) => a.change - b.change);
    $("change-summary").textContent = `${changes.length} facilities have both endpoint quarters (${start} and ${end}). Endpoint changes are descriptive screening context and do not establish cause.`;
    $("change-body").innerHTML = changes.slice(0, 12).map((row) => `
      <tr>
        <td>${facilityLabel(row.facility)}</td>
        <td>${formatNumber(row.start)}</td>
        <td>${formatNumber(row.end)}</td>
        <td>${formatNumber(row.change)}</td>
      </tr>
    `).join("");
  }

  function patternMatches(row, mode) {
    const metrics = row.metrics || {};
    if (mode === "belowTotal") {
      return ctApplicability(row.quarter) === "applicable"
        && metrics.ct_total_direct_care_below_minimum_estimate === true;
    }
    if (mode === "belowLicensed") {
      return ctApplicability(row.quarter) === "applicable"
        && metrics.ct_licensed_direct_care_below_minimum_estimate === true;
    }
    if (mode === "contract10") return (metrics.contract_staff_pct || 0) >= 10;
    if (mode === "contract20") return (metrics.contract_staff_pct || 0) >= 20;
    return false;
  }

  function eligibleForPattern(row, mode) {
    if (mode === "belowTotal" || mode === "belowLicensed") return ctApplicability(row.quarter) === "applicable";
    return true;
  }

  function renderPatterns() {
    const windowQuarters = selectedWindowQuarters($("pattern-window").value);
    const mode = $("pattern-mode").value;
    const minCount = Number($("pattern-min-count").value || 1);
    const minShare = Number($("pattern-min-share").value || 0) / 100;
    let eligibleFacilities = 0;
    let matchingFacilities = 0;
    for (const facility of state.facilities) {
      const rows = (state.byCcn.get(facility.ccn) || []).filter((row) => windowQuarters.includes(row.quarter));
      const eligibleRows = rows.filter((row) => eligibleForPattern(row, mode));
      if (!eligibleRows.length) continue;
      eligibleFacilities += 1;
      const matches = eligibleRows.filter((row) => patternMatches(row, mode)).length;
      const share = matches / eligibleRows.length;
      if (matches >= minCount && share >= minShare) matchingFacilities += 1;
    }
    $("pattern-summary").textContent = `${matchingFacilities} of ${eligibleFacilities} eligible facilities match the selected preview rule in ${windowQuarters[0]}-${windowQuarters[windowQuarters.length - 1]}. Denominators exclude missing and non-applicable quarters.`;
  }

  async function init() {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`Unable to load ${DATA_URL}`);
    const data = await response.json();
    state.rows = data.facility_quarterly_staffing_history || [];
    state.quarters = Array.from(new Set(state.rows.map((row) => row.quarter))).sort(quarterSort);
    for (const row of state.rows) {
      if (!state.byCcn.has(row.ccn)) state.byCcn.set(row.ccn, []);
      state.byCcn.get(row.ccn).push(row);
    }
    for (const rows of state.byCcn.values()) rows.sort((a, b) => quarterSort(a.quarter, b.quarter));
    state.facilities = Array.from(state.byCcn.entries()).map(([ccn, rows]) => {
      const latest = rows[rows.length - 1];
      return { ccn, name: latest.provider_name_from_pbj, city: latest.city_from_pbj };
    }).sort((a, b) => facilityLabel(a).localeCompare(facilityLabel(b)));

    const quarterOptions = state.quarters.map((q) => `<option value="${q}">${q}</option>`).join("");
    $("change-start").innerHTML = quarterOptions;
    $("change-end").innerHTML = quarterOptions;
    $("preview-status").textContent = `Loaded ${state.rows.length.toLocaleString()} PBJ facility-quarter rows across ${state.quarters.length} quarters.`;
    renderFacilityOptions();
    syncChangePreset();
    renderPatterns();
  }

  document.addEventListener("DOMContentLoaded", () => {
    $("facility-search").addEventListener("input", renderFacilityOptions);
    $("facility-select").addEventListener("change", renderFacility);
    $("show-latest-8").addEventListener("click", () => { state.facilityWindow = "latest8"; renderFacility(); });
    $("show-full-history").addEventListener("click", () => { state.facilityWindow = "full"; renderFacility(); });
    $("change-preset").addEventListener("change", syncChangePreset);
    $("change-start").addEventListener("change", () => { $("change-preset").value = "custom"; renderChange(); });
    $("change-end").addEventListener("change", () => { $("change-preset").value = "custom"; renderChange(); });
    $("pattern-window").addEventListener("change", renderPatterns);
    $("pattern-mode").addEventListener("change", renderPatterns);
    $("pattern-min-count").addEventListener("input", renderPatterns);
    $("pattern-min-share").addEventListener("input", renderPatterns);
    init().catch((error) => {
      $("preview-status").textContent = `Preview failed to load: ${error.message}`;
    });
  });
}());
