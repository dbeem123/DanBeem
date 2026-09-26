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
    assert.equal(await page.locator('.danbeem-card').count(), 4);
    assert.equal(await page.locator('a.danbeem-card').count(), 2);
    assert.equal(await page.locator('article.danbeem-card').count(), 2);
    assert.equal(await page.locator('a[href*="glizzy"]').count(), 0);
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').textContent(), 'Skip to projects');

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

    for (const url of ['/', '/staffing/', ...tools.map(route)]) {
      await visit(url);
      for (const width of [360, 390, 768, 1440]) {
        await page.setViewportSize({ width, height: 1000 });
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
    await page.setViewportSize({ width: 720, height: 500 });
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
