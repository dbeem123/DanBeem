// Run against a repository-root static server; requires Playwright and Edge.
// node scripts/test_website_presentation.js http://127.0.0.1:8765
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');
const base = process.argv[2] || 'http://127.0.0.1:8765';
const route = (name) => `/staffing/tools/nursing-home-${name}.html`;
const tools = ['staffing-explorer', 'statewide-staffing-comparison', 'staffing-change-over-time',
  'persistent-staffing-patterns', 'ownership-staffing-explorer', 'staffing-methodology'];
const screenshots = path.join(os.tmpdir(), 'danbeem-redesign-qa');
const root = path.resolve(__dirname, '..');

async function main() {
  const current = JSON.parse(fs.readFileSync(path.join(root, 'data/nursing_home_staffing_ct.json')));
  const history = JSON.parse(fs.readFileSync(path.join(root, 'data/nursing_home_staffing_history_ct.json')));
  assert.equal(current.reporting_period.quarter, '2026Q1');
  assert.equal(current.facilities.length, 196);
  const latest = new Set(current.facility_quarterly_staffing.filter(r => r.quarter === '2026Q1').map(r => r.ccn));
  assert.equal(latest.size, 190);
  assert.equal(current.facilities.filter(f => !latest.has(f.ccn)).length, 6);
  const quarters = [...new Set(history.facility_quarterly_staffing_history.map(r => r.quarter))].sort();
  assert.equal(quarters.length, 34);
  assert.equal(quarters[0], '2017Q4');
  assert.equal(quarters.at(-1), '2026Q1');
  console.log('PASS production invariants: 196 / 190 / 6; 34 quarters');

  fs.mkdirSync(screenshots, { recursive: true });
  const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge' });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    const errors = [];
    const missing = [];
    const requests = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', r => requests.push(r.url()));
    page.on('response', r => { if (r.url().startsWith(base) && r.status() >= 400 && !r.url().endsWith('/favicon.ico')) missing.push(r.url()); });
    // Some browsers (seen in Edge 156 on Windows) report the new innerWidth before
    // viewport-dependent styles are applied. Wait two animation frames after a resize
    // so measurements see the settled layout.
    async function resize(viewport) {
      await page.setViewportSize(viewport);
      await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    }
    async function visit(url) {
      const response = await page.goto(base + url);
      assert.equal(response.status(), 200, url);
      await page.waitForLoadState('networkidle');
    }
    async function csv(button) {
      const event = page.waitForEvent('download');
      await page.locator(button).click();
      const download = await event;
      const stream = await download.createReadStream();
      const chunks = [];
      for await (const chunk of stream) chunks.push(chunk);
      assert.equal(await download.failure(), null);
      return Buffer.concat(chunks).toString('utf8');
    }

    await visit('/');
    assert.equal(await page.locator('.project-card').count(), 4);
    assert.equal(await page.locator('a.feature-strip[href="/legislation/"]').count(), 1);
    assert.equal(await page.locator('.main-nav a[href="/legislation/"]').count(), 1);
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').textContent(), 'Skip to content');
    console.log('PASS homepage cards, legislative tracker links, skip link');

    await visit(route('staffing-explorer') + '?ccn=075442');
    assert.equal(await page.locator('#facility-select').inputValue(), current.facilities.find(f => f.ccn === '075442').facility_id);
    assert.ok(!requests.some(u => u.includes('nursing_home_staffing_history_ct.json')), 'history must stay lazy');
    await page.locator('#facility-filter').fill('075442');
    assert.equal(await page.locator('#facility-select option').count(), 1);
    await page.locator('.dossier-guide a[href="#ratings-title"]').click();
    assert.equal(await page.locator('#ratings-title').evaluate(e => e.parentElement.open), true);
    await page.locator('.dossier-guide a[href="#historical-pbj-title"]').click();
    await page.locator('#load-historical-pbj').click();
    await page.locator('#history-full:not([disabled])').waitFor();
    await page.locator('#history-full').click();
    assert.equal(await page.locator('#history-full').getAttribute('aria-pressed'), 'true');
    assert.match(await page.locator('#historical-pbj-output').innerText(), /2017|2018/);
    assert.match(await csv('#download-history-csv'), /2026Q1/);
    await page.locator('#history-latest-8').click();
    assert.equal(await page.locator('#history-latest-8').getAttribute('aria-pressed'), 'true');
    const before = await page.locator('main details').evaluateAll(es => es.map(e => e.open));
    await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
    assert.equal(await page.locator('main details:not([open])').count(), 0);
    await page.emulateMedia({ media: 'print' });
    assert.ok(await page.locator('#care-compare-context').isVisible());
    await page.emulateMedia({ media: 'screen' });
    await page.evaluate(() => window.dispatchEvent(new Event('afterprint')));
    assert.deepEqual(await page.locator('main details').evaluateAll(es => es.map(e => e.open)), before);
    await page.locator('.dossier-guide a[href="#survey-enforcement-title"]').click();
    await page.locator('[data-survey-detail-action="toggle"]').click();
    await page.locator('#survey-enforcement-details-heading').waitFor();
    assert.ok(await page.locator('#survey-enforcement-details-area').isVisible());
    await page.locator('[data-survey-detail-action="toggle"]').click();
    assert.ok(await page.locator('#survey-enforcement-details-area').isHidden());
    console.log('PASS facility search, disclosure anchors, lazy history, windows, CSV, print restoration');

    await visit(route('statewide-staffing-comparison'));
    const allRows = await page.locator('tbody tr').count();
    assert.equal(allRows, 196);
    await page.locator('#county-filter').selectOption({ index: 1 });
    assert.ok(await page.locator('tbody tr').count() < allRows);
    await page.locator('#facility-search').fill('075442');
    assert.ok(await page.locator('tbody tr').count() <= 1);
    await page.locator('#ownership-filter').selectOption({ index: 1 });
    await page.locator('#ct-filter').selectOption('below-total');
    await page.locator('#contract-filter').selectOption('10');
    await page.locator('#reset-filters').click();
    assert.equal(await page.locator('#county-filter').inputValue(), 'all');
    assert.equal(await page.locator('tbody tr').count(), allRows);
    await page.locator('#county-filter').selectOption('__unknown__');
    assert.equal(await page.locator('tbody tr').count(), 5);
    await page.locator('#reset-filters').click();
    await page.locator('[data-sort-key="name"]').click();
    assert.equal(await page.locator('[data-sort-key="name"]').getAttribute('aria-pressed'), 'true');
    const exported = await csv('#download-statewide-csv');
    for (const column of ['county_name', 'geography_match_status', 'manual_review_required']) assert.ok(exported.includes(column));
    console.log('PASS statewide county/search/combined filters/reset/sort/CSV');

    await visit(route('staffing-change-over-time'));
    assert.equal(await page.locator('#window-preset').inputValue(), 'latest8');
    await page.locator('#window-preset').selectOption('full');
    assert.equal(await page.locator('#start-quarter').inputValue(), '2017Q4');
    await page.locator('#window-preset').selectOption('custom');
    await page.locator('#start-quarter').selectOption('2025Q4');
    assert.equal(await page.locator('#end-quarter').inputValue(), '2026Q1');
    assert.match(await csv('#download-change-csv'), /2026Q1/);
    await visit(route('persistent-staffing-patterns'));
    for (const value of ['latest4', 'latest8', 'full']) {
      await page.locator('#pattern-window').selectOption(value);
      assert.equal(await page.locator('#pattern-window').inputValue(), value);
      assert.ok((await page.locator('#mode-note').innerText()).length > 20);
    }
    await visit(route('ownership-staffing-explorer'));
    await page.locator('#affiliation-select').selectOption({ index: 1 });
    assert.ok((await page.locator('#affiliation-summary').innerText()).length > 20);
    console.log('PASS change/custom windows, persistent windows, affiliation selection');

    await visit(route('ct-staffing-rules'));
    await page.locator('#snapshot-cards .summary-card').first().waitFor();
    assert.match(await page.locator('#snapshot-cards').innerText(), /36/);
    assert.match(await page.locator('#scenario-table').innerText(), /120 of 190/);
    assert.equal(await page.locator('#trend-chart svg').count(), 1);
    assert.equal(await page.locator('#legislation-table tbody tr').count(), 3);
    console.log('PASS Connecticut rules and context: 36 below 3.00, 120 of 190 below 3.60 scenario, trend chart');

    const admins = JSON.parse(fs.readFileSync(path.join(root, 'data/ct_nursing_home_administrators.json')));
    const sample = admins.people.find(p => p.license_number === '1750');
    assert.ok(sample && sample.roles.length === 3, 'fixture administrator 1750 has 3 roles');
    await visit(route('administrator-search'));
    await page.locator('#admin-query:not([disabled])').waitFor();
    assert.match(await page.locator('#search-note').innerText(), new RegExp(`${admins.summary.people} administrators`));
    await page.locator('#admin-query').fill('wagner');
    assert.ok(await page.locator('#admin-results button').count() >= 1);
    await page.locator('#admin-results button[data-person="nha-1750"]').click();
    assert.equal(new URL(page.url()).search, '?license=1750');
    assert.equal(await page.locator('#person-name').innerText(), sample.name);
    assert.equal(await page.locator('#person-view .tenure li').count(), 3);
    assert.equal(await page.locator('#person-view table.stack tbody tr').count(), 3);
    assert.match(await page.locator('#person-view table.stack').innerText(), /Q4 2017 to Q2 2018 \(3 quarters\)/);
    assert.match(await page.locator('#person-view table.stack').innerText(), /Before CMS staffing data begins/);
    assert.equal(await page.locator('#person-view a[href*="nursing-home-staffing-explorer.html?ccn="]').count(), 3);
    const adminCsv = await csv('#admin-csv');
    assert.match(adminCsv.split('\n')[0], /^administrator,license_number,license_status/);
    assert.equal(adminCsv.trim().split('\n').length, 4);
    const pageText = await page.locator('main').innerText();
    assert.ok(!/\b0[6-9]\d{3}\b/.test(pageText), 'no ZIP codes on the administrator page');
    assert.match(pageText, /not a measure of the administrator's performance/);
    assert.match(pageText, /Listing is not an allegation of wrongdoing/);
    assert.match(await page.locator('#admin-corrections').innerText(), /hello@danbeem\.xyz/);
    assert.match(await page.locator('#admin-coverage').innerText(), /BICKFORD HEALTH CARE CENTER/);
    await page.goto('about:blank');
    await visit(route('administrator-search') + '?license=1327');
    await page.locator('#person-name').waitFor();
    assert.match(await page.locator('#person-view').innerText(), /License number\s*1327/i);
    await page.locator('#admin-query').fill('');
    await page.locator('#admin-query').fill('1750');
    await page.locator('#admin-search-form button[type="submit"]').click();
    assert.equal(await page.locator('#person-name').innerText(), sample.name);
    console.log('PASS administrator search: name and license search, deep link, timeline, tenure staffing, CSV, caveats, no ZIPs');

    requests.length = 0;
    await visit(route('staffing-explorer') + '?ccn=075279');
    assert.ok(!requests.some(u => u.includes('ct_nursing_home_administrators.json')), 'administrator data stays lazy');
    await page.locator('.dossier-guide a[href="#administrators-title"]').click();
    await page.locator('table.admin-of-record tbody tr').first().waitFor();
    const home = admins.facilities.find(f => f.ccn === '075279');
    assert.equal(await page.locator('table.admin-of-record tbody tr').count(), home.administrators.length);
    const firstLinked = home.administrators.find(a => a.person_id);
    assert.equal(await page.locator(`table.admin-of-record a[href$="?license=${firstLinked.license_number}"]`).count() >= 1, true);
    console.log('PASS Facility Explorer administrators of record: lazy load, rows, links to the search');

    const mgmt = JSON.parse(fs.readFileSync(path.join(root, 'data/ct_nursing_home_management_companies.json')));
    const nhca = mgmt.companies.find(c => c.id === 'mc-national-health-care-associates-inc');
    assert.ok(nhca && nhca.homes.length >= 1, 'fixture company present');
    await visit(route('management-companies'));
    await page.locator('#mc-filter:not([disabled])').waitFor();
    assert.equal(await page.locator('#mc-rows tr').count(), mgmt.companies.length);
    await page.locator('#mc-current').check();
    assert.equal(await page.locator('#mc-rows tr').count(), mgmt.companies.filter(c => c.homes_current > 0).length);
    await page.locator('#mc-filter').fill('national health');
    assert.equal(await page.locator('#mc-rows tr').count(), 1);
    await page.locator('#mc-rows button[data-company="mc-national-health-care-associates-inc"]').click();
    assert.equal(new URL(page.url()).search, '?company=mc-national-health-care-associates-inc');
    assert.equal(await page.locator('#company-view .tenure li').count(), nhca.homes.length);
    assert.equal(await page.locator('#company-view table.stack tbody tr').count(), nhca.homes.length);
    assert.match(await page.locator('#company-view').innerText(), /000033/);
    assert.ok(await page.locator(`#company-view a[href^="${route('administrator-search')}?license="]`).count() >= 1);
    const mgmtCsv = await csv('#mc-csv');
    assert.equal(mgmtCsv.trim().split('\n').length, nhca.homes.length + 1);
    const mgmtText = await page.locator('main').innerText();
    assert.match(mgmtText, /not the same as ownership/);
    assert.match(mgmtText, /not a measure of the management company's performance/);
    assert.ok(!/\b0[6-9]\d{3}\b/.test(mgmtText), 'no ZIP codes on the management page');
    await page.goto('about:blank');
    await visit(route('management-companies') + '?company=mc-the-geer-corporation');
    await page.locator('#company-name').waitFor();
    assert.match(await page.locator('#company-view').innerText(), /no CMS ownership record/);
    console.log('PASS management companies: list, current filter, search, company view, administrators links, CSV, DPH-only company');

    requests.length = 0;
    await visit(route('staffing-explorer') + '?ccn=075355');
    assert.ok(!requests.some(u => u.includes('ct_nursing_home_management_companies.json')), 'management data stays lazy');
    await page.locator('.dossier-guide a[href="#management-title"]').click();
    await page.locator('#management-output tbody tr').first().waitFor();
    const mgmtHome = mgmt.facilities.find(f => f.ccn === '075355');
    assert.equal(await page.locator('#management-output tbody tr').count(), mgmtHome.management.length);
    console.log('PASS Facility Explorer management companies: lazy load, rows, links');

    await visit('/legislation/');
    await page.locator('#topics .topic').first().waitFor();
    assert.equal(await page.locator('#topics .topic').count(), 9);
    assert.ok(await page.locator('#past-bills tbody tr').count() >= 30);
    await page.locator('#past-outcome').selectOption('failed');
    assert.ok(await page.locator('#past-bills tbody tr').count() >= 5);
    assert.ok(await page.locator('#past-bills .thread-chip').count() >= 3, '"Part of" chips in past sessions');
    assert.match(await page.locator('#topic-staffing_workforce').innerText(), /36/);
    assert.match(await csv('#download-csv'), /SB 1279/);
    console.log('PASS legislative tracker: topics, stats, filters, CSV');

    // Topic browser: one panel at a time, click and keyboard, deep links.
    assert.equal(await page.locator('#topic-nav [role="tab"]').count(), 9);
    assert.equal(await page.locator('#topics .topic:visible').count(), 1);
    await page.locator('#tab-discharge_rights').click();
    assert.equal(await page.locator('#tab-discharge_rights').getAttribute('aria-selected'), 'true');
    assert.ok(await page.locator('#topic-discharge_rights').isVisible());
    assert.equal(new URL(page.url()).hash, '#topic-discharge_rights');
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#tab-closures_capacity').getAttribute('aria-selected'), 'true');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'tab-closures_capacity');
    await page.keyboard.press('Home');
    assert.equal(await page.locator('#tab-staffing_workforce').getAttribute('aria-selected'), 'true');
    await page.goto('about:blank'); // a fresh load, not a same-document hash change
    await visit('/legislation/#topic-community_settings');
    await page.locator('#topics .topic').first().waitFor({ state: 'attached' });
    assert.equal(await page.locator('#tab-community_settings').getAttribute('aria-selected'), 'true');
    assert.ok(await page.locator('#topic-community_settings').isVisible());
    assert.match(await page.locator('#topic-community_settings').innerText(), /Background before 2021[\s\S]*2012/i);
    await page.locator('#tab-staffing_workforce').click();
    const staffingHistory = page.locator('#topic-staffing_workforce .history-list li');
    assert.ok(await staffingHistory.count() > 6, 'staffing history lists more than 6 bills');
    await page.locator('#hist-enacted-staffing_workforce').check();
    assert.equal(await page.locator('#topic-staffing_workforce .history-list .outline-pill').count(), 0);
    assert.equal(await page.locator('#topic-staffing_workforce .compare-table tbody tr').count(), 3);
    assert.match(await page.locator('#compare-staffing-approaches').innerText(), /Minimum spending on direct care[\s\S]*SB 328/);
    console.log('PASS topic browser: tabs, arrow keys, deep link, background, history over 6, staffing comparison');

    // Act reference table: filters and CSV.
    await page.locator('#acts-details > summary').click();
    const allActs = await page.locator('#acts-table tbody tr').count();
    assert.ok(allActs >= 50, `acts listed: ${allActs}`);
    await page.locator('#acts-year').selectOption('2021');
    const acts2021 = await page.locator('#acts-table tbody tr').count();
    assert.ok(acts2021 > 0 && acts2021 < allActs);
    await page.locator('#acts-search').fill('21-185');
    assert.equal(await page.locator('#acts-table tbody tr').count(), 1);
    assert.match(await csv('#acts-csv'), /PA 21-185/);
    await page.locator('#acts-search').fill('');
    await page.locator('#acts-year').selectOption('all');
    console.log('PASS act reference: filters, search, CSV');

    // Storylines: timeline, data strip, copy text, deep link.
    assert.equal(await page.locator('#threads .thread').count(), 12);
    assert.match(await page.locator('#thread-cfc-and-waivers').innerText(), /Final budget keeps CFC as a state plan option/);
    assert.ok(await page.locator('#thread-staffing-floor .thread-event').count() >= 8);
    assert.equal(await page.locator('#thread-staffing-floor .data-strip svg polyline').count(), 1);
    assert.ok(await page.locator('#thread-staffing-floor .thread-event.not-enacted').count() >= 2);
    await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: base });
    await page.locator('#thread-staffing-floor [data-copy-thread]').click();
    const copied = await page.evaluate(() => navigator.clipboard.readText());
    assert.match(copied, /^Raising the staffing floor/);
    assert.match(copied, /2021-10-01 — PA 21-185/);
    assert.ok(copied.includes('Listing is not a position of the Long Term Care Ombudsman Program.'));
    await page.locator('#bill-search').fill('room size');
    assert.match(await page.locator('#current-bills').innerText(), /Room size and capacity/);
    await page.locator('#bill-search').fill('');
    console.log('PASS storylines: 12 cards, timeline, data strip, copy text, search');

    // Testimony builder: renders, placeholder with zero positions, cap of 5 stats, download, no storage.
    const storageBefore = await page.evaluate(() => JSON.stringify(Object.entries(localStorage)));
    await page.locator('#builder-start').selectOption('thread:staffing-floor');
    let draft = await page.locator('#builder-output').inputValue();
    assert.match(draft, /^Storyline: Raising the staffing floor/);
    assert.ok(draft.includes('[No approved Program position for this topic. Add one only with State Ombudsman approval.]'));
    assert.match(draft, /Draft generated from danbeem\.xyz research data on .+\. Verify before submitting\.$/);
    const statBoxes = page.locator('#builder-stats input');
    for (let i = 0; i < await statBoxes.count(); i += 1) if (!(await statBoxes.nth(i).isDisabled())) await statBoxes.nth(i).check();
    assert.equal(await page.locator('#builder-stats input:checked').count(), 5);
    draft = await page.locator('#builder-output').inputValue();
    assert.equal((draft.match(/^- .*\(Q\d \d{4}|^- .*\(FFY/gm) || []).length, 5);
    const dl = page.waitForEvent('download');
    await page.locator('#builder-download').click();
    const file = await dl;
    assert.match(file.suggestedFilename(), /^testimony-draft-\d{4}-\d{2}-\d{2}\.txt$/);
    assert.equal(await page.evaluate(() => JSON.stringify(Object.entries(localStorage))), storageBefore);
    console.log('PASS testimony builder: placeholder, five-stat cap, download, nothing stored');

    await page.goto('about:blank');
    await visit('/legislation/#thread-paying-for-care');
    await page.locator('#thread-paying-for-care').waitFor();
    assert.ok(await page.locator('#thread-paying-for-care').isVisible());

    await visit('/legislation/2026/');
    await page.locator('#bill-lists tbody tr').first().waitFor();
    assert.equal(await page.locator('#bill-lists tbody tr').count(), 131);
    await page.locator('#f-status').selectOption('signed');
    assert.equal(await page.locator('#bill-lists tbody tr').count(), 20);
    await page.locator('#f-status').selectOption('all');
    await page.locator('#f-list').selectOption('2');
    assert.equal(await page.locator('#bill-lists tbody tr').count(), 20);
    assert.match(await csv('#download-csv'), /PA 26-103/);
    await page.locator('#f-list').selectOption('all');
    assert.ok(await page.locator('#bill-lists .thread-chip').count() >= 5, '"Part of" chips on 2026 bills');
    assert.equal(await page.locator('#bill-lists a.thread-chip[href="/legislation/#thread-ownership-transparency"]').count() >= 1, true);
    await page.locator('#f-search').fill('financial transparency');
    assert.ok(await page.locator('#bill-lists tbody tr').count() >= 1, 'search matches storyline titles');
    await page.locator('#f-search').fill('');
    console.log('PASS 2026 session tracker: 131 bills, filters, CSV, storyline chips and search');

    await visit('/legislation/2027/');
    await page.locator('#bill-lists .empty').waitFor();
    assert.equal(await page.locator('#bill-lists tbody tr').count(), 0);
    assert.match(await page.locator('#bill-lists').innerText(), /January 6, 2027/);
    assert.match(await page.locator('#summary-note').innerText(), /Pre-session/);
    assert.doesNotMatch(await page.locator('#summary-note').innerText(), /ended without becoming law/);
    assert.match(await page.locator('#report-pill').innerText(), /2027 Session/);
    console.log('PASS 2027 session tracker: pre-session empty state');

    for (const url of ['/', '/staffing/', ...tools.map(route), route('ct-staffing-rules'), route('administrator-search') + '?license=2143', route('management-companies') + '?company=mc-athena-health-care-associates-inc', '/legislation/', '/legislation/2026/', '/legislation/2027/']) {
      await visit(url);
      for (const width of [360, 390, 768, 1440]) {
        await resize({ width, height: 1000 });
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `overflow ${url} at ${width}`);
        if (url.startsWith('/staffing/') && width < 900) {
          const toggle = page.locator('.staffing-nav-toggle');
          await toggle.click();
          assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
          await toggle.press('Escape');
          assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
        }
        await page.screenshot({ path: path.join(screenshots, `${url.replace(/[^a-z0-9]/gi, '_')}-${width}.png`) });
      }
      const links = await page.locator('a[href^="/staffing/"], link[rel="stylesheet"], script[src], img[src]').evaluateAll(es => es.map(e => e.getAttribute('href') || e.getAttribute('src')));
      for (const link of new Set(links.filter(u => u && u.startsWith('/')))) {
        assert.ok((await context.request.get(base + link.split('#')[0])).ok(), `resource ${link}`);
      }
    }
    // A half-width viewport exercises the reflow expected at 200% desktop zoom.
    await resize({ width: 720, height: 500 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    for (const name of tools) {
      await visit('/tools/nursing-home-' + name + '.html?ccn=075442#source-note-title');
      assert.equal(new URL(page.url()).pathname, route(name));
      assert.equal(new URL(page.url()).search, '?ccn=075442');
      assert.equal(new URL(page.url()).hash, '#source-note-title');
    }
    for (const url of ['/birds/', '/privacy/', '/terms/', '/dashboards/impact-2024.html', '/dashboards/impact-2025.html']) {
      assert.ok((await context.request.get(base + url)).ok(), url);
    }
    const noJs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
    const fallback = await noJs.newPage();
    await fallback.goto(base + '/staffing/');
    assert.ok(await fallback.locator('.ltcop-suite-nav a').first().isVisible());
    await fallback.goto(base + '/tools/nursing-home-staffing-explorer.html');
    await fallback.waitForURL(base + route('staffing-explorer'));
    const legacyHtml = await (await context.request.get(base + '/tools/nursing-home-staffing-explorer.html')).text();
    assert.ok(legacyHtml.includes('<a href="' + route('staffing-explorer') + '">'));
    await noJs.close();
    assert.deepEqual(errors, [], 'browser exceptions');
    assert.deepEqual(missing, [], 'missing resources');
    console.log('PASS responsive layouts, navigation, routes, resources, no-JS fallbacks; no browser errors');
    console.log('Screenshots: ' + screenshots);
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
