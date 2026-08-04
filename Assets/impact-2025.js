(function () {
  "use strict";

  const DATA_PATH = "../data/impact-2025.json";
  const numberFormatter = new Intl.NumberFormat("en-US");
  const currencyFormatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  });

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatValue(item) {
    if (item.displayValue) return escapeHtml(item.displayValue);
    return numberFormatter.format(item.value);
  }

  function setHtml(id, html) {
    const node = document.getElementById(id);
    if (node) node.innerHTML = html;
  }

  function setReportLinks(url) {
    document.querySelectorAll("[data-report-link]").forEach((link) => {
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener";
    });
  }

  function renderYearNavigation(years) {
    setHtml("year-navigation", years.map((year) => {
      const current = year.current ? ' aria-current="page"' : "";
      const note = year.current ? "Current" : year.note || "Open dashboard";
      return `<a class="impact-year-link" href="${escapeHtml(year.href)}"${current}><span>${escapeHtml(year.label)}</span><small>${escapeHtml(note)}</small></a>`;
    }).join(""));
  }

  function renderMetrics(metrics) {
    setHtml("primary-metrics", metrics.map((metric) => `
      <article class="impact-metric">
        <strong>${numberFormatter.format(metric.value)}</strong>
        <h3>${escapeHtml(metric.label)}</h3>
        <p>${escapeHtml(metric.description)}</p>
      </article>
    `).join(""));
  }

  function renderComplaints(complaints) {
    document.getElementById("complaints-intro").textContent = complaints.intro;
    setHtml("complaint-categories", complaints.categories.map((category) => `
      <article class="impact-complaint-card">
        <div>
          <h3>${escapeHtml(category.label)}</h3>
          <div class="impact-complaint-total">
            <strong>${numberFormatter.format(category.count)}</strong>
            <span>${category.percent.toFixed(2)}% of ${numberFormatter.format(complaints.totalReceived)} complaints received</span>
          </div>
          <div class="impact-bar-track" aria-hidden="true">
            <span class="impact-bar-fill" style="--bar-width:${category.percent}%"></span>
          </div>
        </div>
        <ul class="impact-detail-list" aria-label="Most frequently reported concerns within ${escapeHtml(category.label)}">
          ${category.details.map((detail) => `<li><span>${escapeHtml(detail.label)}</span><strong>${numberFormatter.format(detail.count)}</strong></li>`).join("")}
        </ul>
      </article>
    `).join(""));
  }

  function renderFacilityAccess(facilityAccess) {
    document.getElementById("facility-access-intro").textContent = facilityAccess.intro;
    setHtml("facility-activity-table", facilityAccess.activity.map((row) => `
      <tr>
        <td data-label="Program activity">${escapeHtml(row.label)}</td>
        <td data-label="All settings">${numberFormatter.format(row.total)}</td>
        <td data-label="Nursing facilities">${numberFormatter.format(row.nursing)}</td>
        <td data-label="Residential care communities">${numberFormatter.format(row.residentialCare)}</td>
      </tr>
    `).join(""));
    document.getElementById("total-visits").textContent = numberFormatter.format(facilityAccess.totalVisits);
    setHtml("setting-capacity", facilityAccess.capacity.map((item) => `
      <div><dt>${escapeHtml(item.label)}</dt><dd>${formatValue(item)}</dd></div>
    `).join(""));
  }

  function renderComparisons(section) {
    document.getElementById("information-intro").textContent = section.intro;
    setHtml("information-comparisons", section.comparisons.map((item) => `
      <article class="impact-comparison-card">
        <h3>${escapeHtml(item.label)}</h3>
        <div class="impact-year-values">
          <div class="impact-year-value">
            <span>${escapeHtml(item.previousYear)}</span>
            <strong>${numberFormatter.format(item.previous)}</strong>
          </div>
          <div class="impact-year-value current">
            <span>${escapeHtml(item.currentYear)}</span>
            <strong>${numberFormatter.format(item.current)}</strong>
          </div>
        </div>
      </article>
    `).join(""));
  }

  function councilCard(title, council) {
    const residentialLabel = council.residentialCare === 1 ? "participation" : "participations";
    return `
      <article class="impact-council-card">
        <div class="impact-big-number">${numberFormatter.format(council.total)}</div>
        <h3>${escapeHtml(title)}</h3>
        <ul class="impact-breakdown">
          <li>${numberFormatter.format(council.nursing)} nursing facility participations</li>
          <li>${numberFormatter.format(council.residentialCare)} residential care community ${residentialLabel}</li>
        </ul>
      </article>
    `;
  }

  function renderEngagement(engagement) {
    const voice = engagement.residentVoice;
    setHtml("engagement-grid", `
      ${councilCard("Resident council participations", engagement.residentCouncils)}
      ${councilCard("Family council participations", engagement.familyCouncils)}
      <article class="impact-voice-card">
        <div class="impact-kicker">Resident voice · ${escapeHtml(voice.date)}</div>
        <h3>${escapeHtml(voice.title)}</h3>
        <span class="impact-voice-theme">Theme: “${escapeHtml(voice.theme)}”</span>
        <p>${escapeHtml(voice.summary)}</p>
      </article>
    `);
  }

  function renderCommunity(section) {
    setHtml("community-metrics", section.metrics.map((metric) => `
      <article class="impact-narrative-card">
        <div class="impact-big-number">${numberFormatter.format(metric.value)}</div>
        <h3>${escapeHtml(metric.label)}</h3>
      </article>
    `).join(""));
    document.getElementById("community-summary").textContent = section.summary;
    document.getElementById("community-coordination").textContent = section.coordination;
  }

  function renderClosures(section) {
    setHtml("closure-metrics", section.metrics.map((metric) => `
      <article class="impact-narrative-card">
        <div class="impact-big-number">${numberFormatter.format(metric.value)}</div>
        <h3>${escapeHtml(metric.label)}</h3>
      </article>
    `).join(""));
    document.getElementById("closures-summary").textContent = section.summary;
  }

  function renderFunding(funding) {
    document.getElementById("funding-total").textContent = funding.totalDisplay;
    const maxAmount = Math.max(...funding.categories.map((category) => category.amount));
    setHtml("funding-categories", funding.categories.map((category) => {
      const width = Math.max(5, (category.amount / maxAmount) * 100);
      const note = category.note ? `<small>${escapeHtml(category.note)}</small>` : "";
      return `
        <div class="impact-funding-row">
          <div><strong>${escapeHtml(category.label)}: ${currencyFormatter.format(category.amount)}</strong>${note}</div>
          <div class="impact-bar-track" aria-hidden="true"><span class="impact-bar-fill" style="--bar-width:${width.toFixed(2)}%"></span></div>
        </div>
      `;
    }).join(""));
    document.getElementById("funding-note").textContent = funding.note;
  }

  function renderHighlights(highlights) {
    setHtml("program-highlights", highlights.map((highlight) => `
      <article class="impact-highlight-card">
        <h3>${escapeHtml(highlight.title)}</h3>
        <p>${escapeHtml(highlight.summary)}</p>
      </article>
    `).join(""));
  }

  function renderReports(library) {
    setHtml("annual-report-cards", library.reports.map((report) => `
      <article class="impact-report-card${report.current ? " current" : ""}">
        <span class="impact-report-status">${escapeHtml(report.status)}</span>
        <h3>${escapeHtml(report.year)}</h3>
        <p>Connecticut Long Term Care Ombudsman Program annual report.</p>
        <div class="impact-report-links">
          <a class="btn" href="${escapeHtml(report.reportUrl)}" target="_blank" rel="noopener">Open ${escapeHtml(report.year)} report (PDF)</a>
          <a class="btn secondary" href="${escapeHtml(report.dashboardUrl)}">${report.current ? "View current dashboard" : "View dashboard"}${report.dashboardNote ? ` · ${escapeHtml(report.dashboardNote)}` : ""}</a>
        </div>
      </article>
    `).join(""));
    const archiveLink = document.getElementById("report-archive-link");
    archiveLink.href = library.archiveUrl;
  }

  function renderSource(source) {
    const sourceLink = document.getElementById("source-link");
    sourceLink.href = source.url;
    sourceLink.textContent = source.note;
  }

  async function initialize() {
    const status = document.getElementById("dashboard-status");
    try {
      if (!window.DanBeemData || typeof window.DanBeemData.loadJson !== "function") {
        throw new Error("Shared data loader is unavailable.");
      }
      const data = await window.DanBeemData.loadJson(DATA_PATH);
      setReportLinks(data.source.url);
      renderYearNavigation(data.dashboardYears);
      renderMetrics(data.primaryMetrics);
      renderComplaints(data.complaints);
      renderFacilityAccess(data.facilityAccess);
      renderComparisons(data.informationEducation);
      renderEngagement(data.engagement);
      renderCommunity(data.communityOmbudsman);
      renderClosures(data.closures);
      renderFunding(data.funding);
      renderHighlights(data.highlights);
      renderReports(data.annualReports);
      renderSource(data.source);
      status.hidden = true;
    } catch (error) {
      console.error("Impact dashboard initialization failed:", error);
      status.classList.add("impact-error");
      status.textContent = "The FFY 2025 dashboard data could not be loaded. Please open the official annual report using the source link below or try again later.";
    }
  }

  document.addEventListener("DOMContentLoaded", initialize);
})();
