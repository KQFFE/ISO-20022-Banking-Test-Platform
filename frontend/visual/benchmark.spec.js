const { test, expect } = require('@playwright/test');
const postcss = require('postcss');
const tailwindcss = require('tailwindcss');
const pixelmatch = require('pixelmatch');
const { PNG } = require('pngjs');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const cases = require('./cases.json');

const outputDir = path.resolve(__dirname, '../test-results/visual-benchmark');
const threshold = 0.00005;

function hash(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

test('overview baseline and controlled visual changes', async ({ page }, testInfo) => {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.rmSync(path.join(outputDir, 'results.json'), { force: true });
  const css = await postcss([
    tailwindcss({ content: [path.resolve(__dirname, '../src/**/*.{js,jsx}')] }),
  ]).process('@tailwind base; @tailwind components; @tailwind utilities;', { from: undefined });
  const unexpected = [];
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin === 'http://localhost:8000' && url.pathname === '/stats' && route.request().method() === 'GET') {
      await route.fulfill({
        json: { total_transactions: 12, active_flows: 3, executed_transactions: 9 },
        headers: { 'access-control-allow-origin': '*' },
      });
    } else if (url.origin === 'http://localhost:3100') {
      await route.continue();
    } else if (url.href === 'https://cdn.tailwindcss.com/') {
      await route.fulfill({ contentType: 'application/javascript', body: '' });
    } else {
      unexpected.push(`${route.request().method()} ${url.origin}${url.pathname}`);
      await route.abort();
    }
  });

  async function loadOverview() {
    await page.goto('/');
    await page.addStyleTag({ content: css.css });
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
    await expect(page.locator('div').filter({ has: page.getByRole('heading', { name: 'Total Transactions' }) }).getByText('12', { exact: true }).first()).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
  }

  await loadOverview();
  expect(unexpected, 'Unexpected network requests; only local assets and mocked synthetic stats are permitted').toEqual([]);
  const baselinePath = testInfo.snapshotPath('overview.png');
  if (!fs.existsSync(baselinePath) && testInfo.config.updateSnapshots !== 'all') {
    throw new Error('No baseline for this platform. Generate a candidate with --update-snapshots and review it before use.');
  }
  if (fs.existsSync(baselinePath)) {
    const reference = fs.readFileSync(baselinePath);
    const actual = await page.screenshot({ animations: 'disabled' });
    fs.writeFileSync(path.join(outputDir, 'baseline.png'), reference);
    fs.writeFileSync(path.join(outputDir, 'actual-ui.png'), actual);
    fs.writeFileSync(path.join(outputDir, 'results.json'), JSON.stringify({
      threshold,
      baselineSha256: hash(reference),
      results: [{ id: 'actual-ui', expectedChange: null, imageSha256: hash(actual) }],
    }, null, 2));
  }
  await expect(page).toHaveScreenshot('overview.png', {
    animations: 'disabled',
    maxDiffPixelRatio: threshold,
  });
  const baseline = fs.readFileSync(baselinePath);
  const baselinePng = PNG.sync.read(baseline);
  fs.writeFileSync(path.join(outputDir, 'baseline.png'), baseline);
  const actual = await page.screenshot({ animations: 'disabled' });
  fs.writeFileSync(path.join(outputDir, 'actual-ui.png'), actual);
  const results = [{ id: 'actual-ui', expectedChange: null, imageSha256: hash(actual) }];

  for (const item of cases) {
    await loadOverview();
    if (item.id === 'missing-action') {
      await page.getByRole('button', { name: 'Clear History' }).evaluate(el => { el.style.visibility = 'hidden'; });
    } else if (item.id === 'wrong-label') {
      await page.getByRole('heading', { name: 'Active Flows' }).evaluate(el => { el.textContent = 'Inactive Flows'; });
    } else if (item.id === 'shifted-card') {
      await page.getByRole('heading', { name: 'Executed Transactions' }).evaluate(el => { el.parentElement.style.transform = 'translateY(25px)'; });
    } else if (item.id === 'wrong-value') {
      await page.getByRole('heading', { name: 'Total Transactions' }).evaluate(el => { el.nextElementSibling.textContent = '72'; });
    }
    const image = await page.screenshot({ animations: 'disabled' });
    const actualPng = PNG.sync.read(image);
    expect([actualPng.width, actualPng.height]).toEqual([baselinePng.width, baselinePng.height]);
    const diff = new PNG({ width: baselinePng.width, height: baselinePng.height });
    const pixels = pixelmatch(baselinePng.data, actualPng.data, diff.data, diff.width, diff.height, { threshold: 0.2 });
    const ratio = pixels / (diff.width * diff.height);
    fs.writeFileSync(path.join(outputDir, `${item.id}.png`), image);
    fs.writeFileSync(path.join(outputDir, `${item.id}-diff.png`), PNG.sync.write(diff));
    results.push({ id: item.id, expectedChange: item.changed, detected: ratio > threshold, differentPixels: pixels, ratio, imageSha256: hash(image) });
  }
  const counts = {
    truePositive: results.filter(r => r.expectedChange && r.detected).length,
    falseNegative: results.filter(r => r.expectedChange && !r.detected).length,
    trueNegative: results.filter(r => r.expectedChange === false && !r.detected).length,
    falsePositive: results.filter(r => r.expectedChange === false && r.detected).length,
  };
  fs.writeFileSync(path.join(outputDir, 'results.json'), JSON.stringify({
    threshold, baselineSha256: hash(baseline), results, counts,
  }, null, 2));
  console.log('Visual benchmark:', counts);
  expect(unexpected, 'Unexpected network requests; only local assets and mocked synthetic stats are permitted').toEqual([]);
  expect(counts.falseNegative, 'Controlled changes missed by pixel comparison').toBe(0);
  expect(counts.falsePositive, 'Unchanged control incorrectly detected').toBe(0);
});
